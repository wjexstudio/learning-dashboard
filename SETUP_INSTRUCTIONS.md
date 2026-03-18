# 🚀 วิธี Setup LEARNING Dashboard ออนไลน์

## ขั้นตอนที่ 1 — สร้าง GitHub Repo (2 นาที)

1. ไปที่ https://github.com/new
2. ตั้งชื่อ repo: `learning-dashboard`
3. เลือก **Public**
4. **อย่า** tick "Add README" — ปล่อยว่างไว้
5. คลิก **Create repository**
6. Copy URL repo เช่น `https://github.com/wjexstudio/learning-dashboard`

---

## ขั้นตอนที่ 2 — Push โค้ดขึ้น GitHub (3 นาที)

โฟลเดอร์โปรเจคอยู่ที่ **โฟลเดอร์ LEARNING** ของคุณ → `learning-dashboard/`

เปิด Terminal บนเครื่องของคุณ แล้วรัน (แทน `YOUR_USERNAME` ด้วย GitHub username ของคุณ):

```bash
cd "path/to/your/LEARNING/learning-dashboard"

git init
git add .
git commit -m "feat: LEARNING Dashboard — auto-update via GitHub Actions"
git remote add origin https://github.com/YOUR_USERNAME/learning-dashboard.git
git branch -M main
git push -u origin main
```

> ⚠️ ถ้า Terminal ถาม password ให้ใส่ GitHub Personal Access Token แทน password
> สร้าง token ที่: https://github.com/settings/tokens/new → เลือก scopes: `repo` + `workflow`

**หรือถ้าใช้ GitHub Desktop:** ลาก folder `learning-dashboard` ไปใส่ GitHub Desktop แล้วกด Publish repository

---

## ขั้นตอนที่ 3 — เพิ่ม NOTION_TOKEN เป็น Secret (1 นาที)

1. ไปที่ repo → **Settings → Secrets and variables → Actions**
2. คลิก **New repository secret**
3. Name: `NOTION_TOKEN`
4. Value: Notion integration token ของคุณ (เริ่มด้วย `secret_...`)
5. คลิก **Add secret**

> หา Notion token ได้ที่: https://www.notion.so/my-integrations

---

## ขั้นตอนที่ 4 — เปิด GitHub Pages (1 นาที)

1. ไปที่ repo → **Settings → Pages**
2. Source: เลือก **GitHub Actions**
3. คลิก **Save**

---

## ขั้นตอนที่ 5 — Run ครั้งแรก (Manual)

1. ไปที่ repo → **Actions → Update LEARNING Dashboard**
2. คลิก **Run workflow** → **Run workflow**
3. รอ ~30 วินาที
4. Dashboard จะอยู่ที่: `https://YOUR_USERNAME.github.io/learning-dashboard/`

---

## Embed ใน Notion

1. เปิด Notion page ที่ต้องการ
2. พิมพ์ `/embed`
3. ใส่ URL: `https://YOUR_USERNAME.github.io/learning-dashboard/`
4. กด Enter → Dashboard จะแสดงอยู่ใน Notion เลย!

---

## การทำงานอัตโนมัติ

Dashboard จะอัปเดตอัตโนมัติ:
- ⏰ **ทุกวัน 10:00 น.** (Bangkok time)
- ⏰ **ทุกวัน 20:00 น.** (Bangkok time)
- ✅ ถ้าไม่มีการเปลี่ยนแปลงใน Notion → ข้ามไป ไม่ deploy ใหม่
- ✅ ถ้ามีการเปลี่ยนแปลง → generate HTML ใหม่ → deploy ใน ~1 นาที

---

## ไฟล์ในโปรเจค

| ไฟล์ | หน้าที่ |
|------|---------|
| `update_dashboard.py` | Script หลัก — ดึง Notion → generate HTML |
| `index.html` | Dashboard HTML (auto-generated) |
| `.snapshot.json` | เก็บ hash ของข้อมูลล่าสุด (เช็ค change detection) |
| `.github/workflows/update-dashboard.yml` | GitHub Actions — รัน script ตาม schedule |
| `.github/workflows/deploy-pages.yml` | GitHub Actions — deploy ขึ้น Pages |
