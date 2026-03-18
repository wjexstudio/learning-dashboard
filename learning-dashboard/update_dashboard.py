"""
LEARNING Dashboard Auto-Updater
================================
Fetches all Blog articles from the LEARNING Notion database,
compares with previous snapshot, regenerates index.html if changed.

Run by GitHub Actions at 10:00 and 20:00 Bangkok time daily.
Requires env var: NOTION_TOKEN
"""

import os, json, hashlib, sys

# Load .env file if present (for local/Cowork runs)
_env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())
from datetime import datetime, timezone
from collections import Counter

NOTION_TOKEN  = os.environ.get("NOTION_TOKEN", "")
DATABASE_ID   = "fc475f415ec2828298e4013a334aa66b"  # LEARNING Articles database
SNAPSHOT_FILE = os.path.join(os.path.dirname(__file__), ".snapshot.json")
OUTPUT_HTML   = os.path.join(os.path.dirname(__file__), "index.html")

# ── Notion REST helpers ──────────────────────────────────────────
def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }

def fetch_all_pages():
    import urllib.request, urllib.error
    url     = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    results = []
    cursor  = None
    while True:
        body = {
            "page_size": 100,
            "filter": {"property": "Type", "select": {"equals": "Blog"}}
        }
        if cursor:
            body["start_cursor"] = cursor
        req = urllib.request.Request(
            url, data=json.dumps(body).encode(), headers=notion_headers(), method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read())
        except urllib.error.HTTPError as e:
            print(f"[ERROR] Notion API: {e.code} {e.reason}")
            sys.exit(1)
        results.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return results

def extract_article(page):
    props = page.get("properties", {})
    def txt(k):
        f = "title" if k == "Title" else "rich_text"
        return "".join(t.get("plain_text","") for t in props.get(k,{}).get(f,[]))
    def sel(k):  return (props.get(k,{}).get("select") or {}).get("name","")
    def multi(k): return [t.get("name","") for t in props.get(k,{}).get("multi_select",[])]
    def date(k):  return ((props.get(k,{}).get("date") or {}).get("start",""))
    return {
        "id":          page["id"],
        "title":       txt("Title"),
        "status":      sel("Status"),
        "category":    sel("Categories"),
        "tags":        multi("Tags"),
        "hashtags":    multi("Hashtags"),
        "slug":        txt("Slug"),
        "description": txt("Description"),
        "pub_date":    date("Published Date"),
        "created":     page.get("created_time","")[:10],
        "edited":      page.get("last_edited_time","")[:10],
    }

# ── Change detection ─────────────────────────────────────────────
def fingerprint(articles):
    s = json.dumps(sorted([a["id"] + a["edited"] + a["status"] for a in articles]))
    return hashlib.md5(s.encode()).hexdigest()

def load_snapshot():
    try:
        with open(SNAPSHOT_FILE) as f:
            return json.load(f)
    except Exception:
        return {"hash": "", "generated_at": ""}

def save_snapshot(h):
    with open(SNAPSHOT_FILE, "w") as f:
        json.dump({"hash": h, "generated_at": datetime.now(timezone.utc).isoformat()}, f)

# ── HTML Generator ───────────────────────────────────────────────
def generate_html(articles, generated_at):
    total     = len(articles)
    published = sum(1 for a in articles if a["status"] == "Published")
    draft     = sum(1 for a in articles if a["status"] == "Draft")
    no_slug   = sum(1 for a in articles if not a["slug"])
    no_desc   = sum(1 for a in articles if not a["description"])
    no_cat    = sum(1 for a in articles if not a["category"])
    no_date   = sum(1 for a in articles if not a["pub_date"])
    no_tags   = sum(1 for a in articles if not a["tags"])

    cat_counts   = Counter(a["category"] or "ไม่ระบุ" for a in articles)
    tag_counts   = Counter(t for a in articles for t in a["tags"])
    hash_counts  = Counter(h for a in articles for h in a["hashtags"])
    month_counts = Counter(a["created"][:7] for a in articles if a["created"])
    months_sorted = sorted(month_counts.keys())

    publish_rate = round(published / total * 100) if total else 0
    meta_score   = round((1 - (no_cat + no_slug + no_desc + no_date) / (total * 4)) * 100) if total else 0
    overall      = round(publish_rate * 0.4 + meta_score * 0.6)
    score_color  = "#6adfb8" if overall >= 70 else ("#ffc96a" if overall >= 50 else "#ff6a9b")

    # Tags progress bars
    tag_bar = ""
    top_tags = tag_counts.most_common(6)
    max_t = top_tags[0][1] if top_tags else 1
    for tag, cnt in top_tags:
        pct = int(cnt / max_t * 100)
        tag_bar += f'<div class="pr"><div class="pl"><span>{tag}</span><span>{cnt}</span></div><div class="pb"><div class="pf" style="width:{pct}%;background:#7c6aff"></div></div></div>'

    # Hashtag pills
    ALL_HASH = ["#WJEXS","#AgentSkills","#ClaudeCowork","#Manifest","#Writing","#Gemini",
                "#Line","#N8N","#NewFeature","#Automation","#GoogleAIStudio","#NanoBanana2",
                "#OnePersonBusiness","#Bookreview","#Study","#Solopreneur","#DigitalProduct",
                "#PersonalBranding","#ClaudeCode","#CLI","#Agent","#Productivity"]
    used_pills = "".join(
        f'<div class="tp">{h} <span class="tc">{hash_counts[h]}</span></div>'
        for h in ALL_HASH if hash_counts.get(h, 0) > 0
    )
    zero_pills = "".join(
        f'<div class="tp">{h} <span class="tz">0</span></div>'
        for h in ALL_HASH if hash_counts.get(h, 0) == 0
    )

    # Article rows
    def sbadge(s):
        cls = "bp" if s == "Published" else "bd"
        return f'<span class="b {cls}">{s or "—"}</span>'
    def cbadge(c):
        m = {"Technology":"bt","Business":"bb","Work Life":"bw","Design":"bds"}
        return f'<span class="b {m.get(c,"bn")}">{c or "—"}</span>'
    def warn(a):
        issues = [x for x,v in [("Slug",a["slug"]),("Desc",a["description"]),("Cat",a["category"]),("Date",a["pub_date"])] if not v]
        if not issues: return '<span style="color:#6adfb8;font-size:.73rem">✅</span>'
        col = "#ff6a9b" if len(issues) >= 3 else "#ffc96a"
        return f'<span style="color:{col};font-size:.73rem">⚠️ {", ".join(issues)}</span>'

    rows = ""
    for i, a in enumerate(articles, 1):
        tags_html = " ".join(f'<span class="b bai" style="font-size:.68rem">{t}</span>' for t in a["tags"][:2])
        slug_disp = (a["slug"][:20]+"…") if len(a["slug"]) > 20 else (a["slug"] or '<span style="color:#ff6a9b">ไม่มี!</span>')
        rows += f"""<tr>
          <td style="color:#7b82a8">{i}</td>
          <td class="tc2"><strong>{a['title'] or '(ไม่มีชื่อ)'}</strong></td>
          <td>{sbadge(a['status'])}</td>
          <td>{cbadge(a['category'])}</td>
          <td>{tags_html or '<span style="color:#7b82a8">—</span>'}</td>
          <td style="font-size:.76rem;color:#7b82a8">{a['pub_date'] or '—'}</td>
          <td style="font-size:.76rem;color:#7b82a8">{slug_disp}</td>
          <td>{warn(a)}</td></tr>"""

    cat_labels = json.dumps(list(cat_counts.keys()))
    cat_data   = json.dumps(list(cat_counts.values()))
    ml = json.dumps(months_sorted)
    md = json.dumps([month_counts[m] for m in months_sorted])
    has_data   = json.dumps([total-no_slug, total-no_desc, total-no_cat, total-no_date])
    miss_data  = json.dumps([no_slug, no_desc, no_cat, no_date])

    return f"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>LEARNING Dashboard</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
:root{{--bg:#0f1117;--s:#1a1d27;--s2:#222635;--br:#2e3248;--a:#7c6aff;--a2:#ff6a9b;--a3:#6adfb8;--a4:#ffc96a;--t:#e8eaf6;--tm:#7b82a8;--r:13px}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--t);font-family:'Segoe UI','Noto Sans Thai',sans-serif;font-size:14px;line-height:1.6}}
.topbar{{background:#16192a;border-bottom:1px solid var(--br);padding:16px 24px;display:flex;align-items:center;justify-content:space-between}}
.topbar h1{{font-size:1.1rem;font-weight:700}}.topbar h1 em{{color:var(--a);font-style:normal}}
.upd{{font-size:.73rem;color:var(--tm)}}
.main{{max-width:1280px;margin:0 auto;padding:20px 16px 50px}}
.kg{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:20px}}
.kc{{background:var(--s);border:1px solid var(--br);border-radius:var(--r);padding:16px 14px;position:relative;overflow:hidden}}
.kc::before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--ac,var(--a))}}
.kl{{font-size:.68rem;color:var(--tm);text-transform:uppercase;letter-spacing:.08em;margin-bottom:5px}}
.kv{{font-size:1.8rem;font-weight:800;color:var(--ac,var(--a))}}.ks{{font-size:.68rem;color:var(--tm);margin-top:2px}}
.st{{font-size:.78rem;font-weight:700;color:var(--tm);text-transform:uppercase;letter-spacing:.1em;margin:20px 0 10px;display:flex;align-items:center;gap:8px}}
.st::after{{content:'';flex:1;height:1px;background:var(--br)}}
.g3{{display:grid;grid-template-columns:1.1fr 1fr 1fr;gap:16px;margin-bottom:16px}}
.g2{{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:16px}}
.cd{{background:var(--s);border:1px solid var(--br);border-radius:var(--r);padding:18px}}
.cd h3{{font-size:.73rem;color:var(--tm);margin-bottom:12px;font-weight:600;text-transform:uppercase;letter-spacing:.06em}}
.cw{{position:relative;height:210px}}
.at{{width:100%;border-collapse:collapse;font-size:.78rem}}
.at th{{text-align:left;padding:8px 10px;color:var(--tm);font-size:.66rem;text-transform:uppercase;letter-spacing:.07em;border-bottom:1px solid var(--br);background:var(--s2)}}
.at td{{padding:8px 10px;border-bottom:1px solid #1e2133;vertical-align:middle}}
.at tr:hover td{{background:var(--s2)}}.at tr:last-child td{{border-bottom:none}}
.tc2{{max-width:240px}}
.b{{display:inline-block;padding:1px 7px;border-radius:99px;font-size:.67rem;font-weight:600;white-space:nowrap}}
.bp{{background:rgba(106,223,184,.15);color:#6adfb8}}.bd{{background:rgba(255,201,106,.15);color:#ffc96a}}
.bt{{background:rgba(124,106,255,.15);color:#7c6aff}}.bb{{background:rgba(255,201,106,.15);color:#ffc96a}}
.bw{{background:rgba(255,106,155,.15);color:#ff6a9b}}.bds{{background:rgba(106,223,184,.12);color:#6adfb8}}
.bn{{background:rgba(123,130,168,.1);color:#7b82a8}}.bai{{background:rgba(176,160,255,.12);color:#b0a0ff}}
.pr{{margin-bottom:9px}}.pl{{display:flex;justify-content:space-between;font-size:.76rem;margin-bottom:3px}}
.pl span:last-child{{color:var(--tm)}}.pb{{height:6px;background:var(--s2);border-radius:99px;overflow:hidden}}
.pf{{height:100%;border-radius:99px}}
.tl{{display:flex;flex-wrap:wrap;gap:5px;margin-top:5px}}
.tp{{background:var(--s2);border:1px solid var(--br);border-radius:99px;padding:1px 9px;font-size:.71rem;color:var(--tm);display:flex;align-items:center;gap:4px}}
.tc{{background:var(--a);color:#fff;border-radius:99px;padding:0 5px;font-size:.63rem;font-weight:700}}
.tz{{background:var(--s);color:var(--tm);border:1px solid var(--br);border-radius:99px;padding:0 5px;font-size:.63rem}}
.sc{{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center}}
.sb{{font-size:3rem;font-weight:900;line-height:1;margin:14px 0}}
.sv{{max-height:460px;overflow-y:auto}}
.sv::-webkit-scrollbar{{width:4px}}.sv::-webkit-scrollbar-thumb{{background:var(--br);border-radius:99px}}
@media(max-width:900px){{.kg{{grid-template-columns:repeat(3,1fr)}}.g2,.g3{{grid-template-columns:1fr}}}}
</style>
</head>
<body>
<div class="topbar">
  <h1>📚 <em>LEARNING</em> — Content Dashboard</h1>
  <div class="upd">อัปเดตอัตโนมัติ · {generated_at}</div>
</div>
<div class="main">

<div class="kg">
  <div class="kc" style="--ac:#7c6aff"><div class="kl">บทความทั้งหมด</div><div class="kv">{total}</div><div class="ks">Blog posts</div></div>
  <div class="kc" style="--ac:#6adfb8"><div class="kl">Published</div><div class="kv">{published}</div><div class="ks">{publish_rate}% ของทั้งหมด</div></div>
  <div class="kc" style="--ac:#ffc96a"><div class="kl">Draft</div><div class="kv">{draft}</div><div class="ks">ยังไม่เผยแพร่</div></div>
  <div class="kc" style="--ac:#ff6a9b"><div class="kl">ขาด Metadata</div><div class="kv">{no_slug+no_desc+no_cat+no_date}</div><div class="ks">รายการที่ต้องแก้</div></div>
  <div class="kc" style="--ac:{score_color}"><div class="kl">Content Score</div><div class="kv">{overall}</div><div class="ks">/ 100 คะแนนรวม</div></div>
</div>

<div class="st">📊 ภาพรวม</div>
<div class="g3">
  <div class="cd"><h3>Categories</h3><div class="cw"><canvas id="catC"></canvas></div></div>
  <div class="cd"><h3>สถานะบทความ</h3><div class="cw"><canvas id="statusC"></canvas></div></div>
  <div class="cd"><h3>Tags ที่ใช้บ่อย</h3>{tag_bar}</div>
</div>

<div class="g2">
  <div class="cd"><h3>Timeline การสร้างบทความ</h3><div class="cw"><canvas id="timeC"></canvas></div></div>
  <div class="cd">
    <h3>Hashtags</h3>
    <div style="font-size:.68rem;color:#6adfb8;margin-bottom:5px;font-weight:700">✅ ใช้งานแล้ว</div>
    <div class="tl" style="margin-bottom:10px">{used_pills}</div>
    <div style="font-size:.68rem;color:#ff6a9b;margin-bottom:5px;font-weight:700">⚠️ ยังไม่มีบทความ</div>
    <div class="tl">{zero_pills}</div>
  </div>
</div>

<div class="st">📝 รายการบทความทั้งหมด ({total} บทความ)</div>
<div class="cd" style="padding:0;overflow:hidden">
  <div class="sv">
  <table class="at">
    <thead><tr><th>#</th><th>ชื่อบทความ</th><th>Status</th><th>Category</th><th>Tags</th><th>Published</th><th>Slug</th><th>Metadata</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  </div>
</div>

<div class="st">📋 Metadata Health</div>
<div class="g2">
  <div class="cd"><h3>ความครบถ้วน Metadata</h3><div class="cw"><canvas id="metaC"></canvas></div></div>
  <div class="cd sc">
    <h3>Overall Content Score</h3>
    <div class="sb" style="color:{score_color}">{overall}</div>
    <div style="font-size:.78rem;color:#7b82a8">Publish Rate ({publish_rate}%) × 40% + Metadata ({meta_score}%) × 60%</div>
    <div style="margin-top:12px;font-size:.75rem;color:#7b82a8;line-height:2">
      📅 ขาด Published Date: <strong style="color:#ffc96a">{no_date}</strong> บทความ<br>
      🔗 ขาด Slug: <strong style="color:#ff6a9b">{no_slug}</strong> บทความ<br>
      📁 ขาด Category: <strong style="color:#ff6a9b">{no_cat}</strong> บทความ<br>
      📝 ขาด Description: <strong style="color:#ffc96a">{no_desc}</strong> บทความ
    </div>
  </div>
</div>

</div>
<script>
const G={{grid:'rgba(255,255,255,.06)',tick:'#7b82a8',leg:'#e8eaf6'}};
Chart.defaults.color=G.tick; Chart.defaults.borderColor=G.grid;
new Chart(document.getElementById('catC'),{{type:'bar',data:{{labels:{cat_labels},datasets:[{{label:'บทความ',data:{cat_data},backgroundColor:['rgba(124,106,255,.75)','rgba(255,201,106,.75)','rgba(255,106,155,.7)','rgba(106,223,184,.7)','rgba(123,130,168,.5)'],borderRadius:6,borderWidth:0}}]}},options:{{indexAxis:'y',plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{color:G.grid}},ticks:{{color:G.tick,stepSize:1}}}},y:{{grid:{{display:false}},ticks:{{color:G.tick,font:{{size:10}}}}}}}}  }}}});
new Chart(document.getElementById('statusC'),{{type:'doughnut',data:{{labels:['Published ({published})','Draft ({draft})'],datasets:[{{data:[{published},{draft}],backgroundColor:['rgba(106,223,184,.85)','rgba(255,201,106,.8)'],borderColor:['#1a1d27'],borderWidth:3,hoverOffset:6}}]}},options:{{cutout:'68%',plugins:{{legend:{{position:'bottom',labels:{{color:G.leg,padding:10,font:{{size:11}}}}}}}}  }}}});
new Chart(document.getElementById('timeC'),{{type:'bar',data:{{labels:{ml},datasets:[{{label:'บทความ',data:{md},backgroundColor:'rgba(124,106,255,.7)',borderRadius:5,borderWidth:0}}]}},options:{{plugins:{{legend:{{display:false}}}},scales:{{x:{{grid:{{display:false}},ticks:{{color:G.tick}}}},y:{{grid:{{color:G.grid}},ticks:{{color:G.tick,stepSize:1}}}}}}  }}}});
new Chart(document.getElementById('metaC'),{{type:'bar',data:{{labels:['มี Slug','มี Description','มี Category','มี Published Date'],datasets:[{{label:'มีข้อมูล',data:{has_data},backgroundColor:'rgba(124,106,255,.7)',borderRadius:5,borderWidth:0}},{{label:'ขาด',data:{miss_data},backgroundColor:'rgba(255,106,155,.55)',borderRadius:5,borderWidth:0}}]}},options:{{indexAxis:'y',plugins:{{legend:{{position:'bottom',labels:{{color:G.leg,padding:8}}}}}},scales:{{x:{{stacked:true,max:{total},grid:{{color:G.grid}},ticks:{{color:G.tick,stepSize:1}}}},y:{{stacked:true,grid:{{display:false}},ticks:{{color:G.tick,font:{{size:10}}}}}}}}  }}}});
</script>
</body>
</html>"""

# ── Main ─────────────────────────────────────────────────────────
def main():
    now = datetime.now(timezone.utc)
    print(f"[{now.isoformat()}] LEARNING Dashboard updater starting...")

    if not NOTION_TOKEN:
        print("[ERROR] NOTION_TOKEN environment variable is not set.")
        sys.exit(1)

    print("Fetching articles from Notion...")
    raw   = fetch_all_pages()
    arts  = [extract_article(p) for p in raw]
    print(f"  → {len(arts)} articles found.")

    new_hash = fingerprint(arts)
    snap     = load_snapshot()

    if snap["hash"] == new_hash:
        print("No changes detected — skipping update.")
        return

    print(f"  Changes detected → regenerating dashboard...")
    gen_at = now.strftime("%d/%m/%Y %H:%M UTC")
    html   = generate_html(arts, gen_at)

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    save_snapshot(new_hash)

    total     = len(arts)
    published = sum(1 for a in arts if a["status"] == "Published")
    draft     = total - published
    missing   = sum(1 for a in arts if not a["slug"] or not a["description"] or not a["category"] or not a["pub_date"])
    print(f"  ✓ Dashboard updated: {total} articles ({published} Published / {draft} Draft), {missing} with missing metadata.")

if __name__ == "__main__":
    main()
