# CLAUDE.md — LEARNING Dashboard Project

โปรเจกต์นี้เป็น content dashboard สำหรับติดตามบทความ Blog ใน Notion database ของ LEARNING
Auto-deploy ผ่าน GitHub Pages และมี AI-assisted content workflow ผ่าน Claude Cowork

---

## โครงสร้างโปรเจกต์

```
learning-dashboard/
├── index.html              ← Dashboard (auto-generated, ห้ามแก้มือ)
├── update_dashboard.py     ← Script sync Notion → HTML
├── .snapshot.json          ← Hash เก็บ state ล่าสุด (auto-generated)
├── .env                    ← NOTION_TOKEN (local only, ไม่ขึ้น Git)
├── .gitignore
└── .github/workflows/
    ├── update-dashboard.yml  ← GitHub Actions: รัน update_dashboard.py อัตโนมัติ
    └── deploy-pages.yml      ← GitHub Actions: deploy index.html → GitHub Pages
```

---

## Notion Database

- **Database ID:** `fc475f415ec2828298e4013a334aa66b`
- **Filter:** Type = "Blog"
- **Properties ที่ใช้:**

| Property | Type | ความหมาย |
|---|---|---|
| Title | title | ชื่อบทความ |
| Status | select | Published / Draft |
| Categories | select | หมวดหมู่หลัก |
| Tags | multi_select | แท็กเนื้อหา |
| Hashtags | multi_select | แท็ก social |
| Slug | rich_text | URL slug |
| Description | rich_text | คำอธิบายย่อ |
| Published Date | date | วันที่เผยแพร่ |
| last_edited_time | auto | วันที่แก้ไขล่าสุด (ใช้ตรวจ workflow) |

---

## Task 1 — Dashboard Sync (GitHub Actions)

**ไม่ต้องใช้ AI** — ให้ GitHub Actions จัดการอัตโนมัติ

- รันทุกวัน 10:00 และ 20:00 (Bangkok time)
- รัน `update_dashboard.py` → regenerate `index.html` → deploy GitHub Pages
- **ไม่ต้อง** สร้าง Cowork scheduled task สำหรับงานนี้

---

## Task 2 — AI Content Review (Claude Cowork Scheduled Task)

**ใช้ AI** — รันผ่าน Cowork วันละ 1 ครั้ง เช้าหรือเที่ยง

### Prompt สำหรับ Cowork Scheduled Task:

```
ตรวจสอบ LEARNING Notion database และทำตามขั้นตอนต่อไปนี้:

**ขั้นตอนที่ 1 — ตรวจบทความใหม่และที่แก้ไขล่าสุด**
ใช้ Notion MCP (notion-fetch) ดึงบทความ Type=Blog ทั้งหมด
กรองเฉพาะบทความที่:
- last_edited_time ภายใน 24 ชั่วโมงที่ผ่านมา (บทความที่กำลังเขียน)
- Status = "Draft" และ created_time ภายใน 7 วัน (บทความใหม่)

**ขั้นตอนที่ 2 — วิเคราะห์แต่ละบทความ**
สำหรับแต่ละบทความที่พบ ให้ตรวจสอบ:
- Properties ที่ยังไม่ครบ (Slug, Description, Categories, Tags, Published Date)
- เนื้อหาในหน้า Notion ว่าเขียนถึงไหนแล้ว มีส่วนไหนขาดหายไปบ้าง
- โครงสร้างบทความ: มี Intro / Body / Conclusion หรือไม่

**ขั้นตอนที่ 3 — วิเคราะห์ลักษณะการเขียน (Writing Style Analysis)**
อ่านเนื้อหาในบทความที่มีข้อความเกิน 100 คำ แล้ววิเคราะห์ใน 5 มิติ:

1. **น้ำเสียง (Tone):** เป็นทางการ / กึ่งทางการ / ลำลอง / สอน / เล่าเรื่อง
2. **โครงสร้างประโยค:** ความยาว, การตัดประโยค, การใช้ bullet vs ย่อหน้า
3. **การเว้นวรรค:** เว้นบรรทัดระหว่าง section อย่างไร, ความหนาแน่นของข้อความ
4. **การเน้นข้อความ:** ใช้ bold/italic/เครื่องหมายอะไร เน้นส่วนไหนบ้าง
5. **คำและสำนวนเฉพาะตัว:** คำที่ใช้บ่อย, สำนวนซ้ำ, วิธีอธิบายแนวคิด

จากนั้น:
- เปรียบเทียบกับ `writing-style.md` ที่มีอยู่ (ถ้ามี) ว่ามีอะไรเปลี่ยนไปหรือสอดคล้องกัน
- สรุปสิ่งที่สังเกตเห็นในรูปแบบ **"ฉันสังเกตเห็นว่าคุณ..."** พร้อมยกตัวอย่างจากบทความจริง
- ถามว่า **"ต้องการให้บันทึก/อัปเดต writing style นี้ไหมครับ?"** ก่อนบันทึกทุกครั้ง
- เมื่อได้รับอนุมัติ ให้ update ไฟล์ `writing-style.md` ในโปรเจกต์

**ขั้นตอนที่ 4 — แนะนำและเติมเนื้อหา**
สำหรับบทความที่ยังไม่เสร็จ:
- แนะนำโครงสร้างบทความที่เหมาะสมกับหัวข้อ
- ใช้ WebSearch หาข้อมูลจากแหล่งที่น่าเชื่อถือ
  (official docs, งานวิจัย, บทความวิชาการ, เว็บไซต์ผู้เชี่ยวชาญ)
- ใช้ WebFetch อ่านเนื้อหาแหล่งที่มาก่อน summarize
- **เขียน draft โดยเลียนแบบ writing style จาก `writing-style.md`** (ถ้ามี)
- แสดงผลให้ผู้ใช้ review ก่อน อย่าเขียนลง Notion โดยตรง

**ขั้นตอนที่ 5 — รอการอนุมัติ**
สรุปรายการเปลี่ยนแปลงทั้งหมดและถามว่า:
"ต้องการให้บันทึกการเปลี่ยนแปลงเหล่านี้ลง Notion ไหมครับ? (ใช่ / ไม่ใช่ / แก้ไขก่อน)"

**ขั้นตอนที่ 6 — บันทึกและอัปเดต Dashboard (เมื่อได้รับอนุมัติเท่านั้น)**
- ใช้ Notion MCP (notion-update-page) เขียนเนื้อหาที่อนุมัติแล้วลง Notion
- รัน update_dashboard.py เพื่อ regenerate index.html
- รัน git add, git commit, git push เพื่อ deploy
```

---

## Tools และ Skills ที่ต้องใช้

### Cowork Task 2 ต้องการ:

| Tool / Skill | ใช้สำหรับ |
|---|---|
| **Notion MCP** (`notion-fetch`) | ดึงบทความและเนื้อหาจาก Notion |
| **Notion MCP** (`notion-update-page`) | เขียนเนื้อหากลับลง Notion หลัง approve |
| **Notion MCP** (`notion-search`) | ค้นหาบทความที่เกี่ยวข้อง |
| **WebSearch** | หาข้อมูลจากแหล่งภายนอกตามเนื้อหาบทความ |
| **WebFetch** | อ่านและ summarize เนื้อหาจาก URL ที่หามาได้ |
| **Bash** (`python update_dashboard.py`) | Regenerate index.html หลังอัปเดต Notion |
| **Bash** (`git commit`, `git push`) | Deploy Dashboard ขึ้น GitHub Pages |
| **Read/Write** (`writing-style.md`) | อ่านและอัปเดต writing style profile ของผู้เขียน |

### GitHub Actions (อัตโนมัติ ไม่ต้องทำเอง):

| Workflow | ทำอะไร |
|---|---|
| `update-dashboard.yml` | รัน update_dashboard.py ทุกวัน 10:00 และ 20:00 |
| `deploy-pages.yml` | Deploy index.html → GitHub Pages |

---

## กฎสำคัญ

1. **ห้ามแก้ `index.html` มือ** — ให้รัน `update_dashboard.py` เสมอ
2. **Writing style analysis ต้องขออนุมัติก่อนบันทึกทุกครั้ง** — แสดงสิ่งที่สังเกตเห็นก่อนเสมอ พร้อมยกตัวอย่างจากบทความจริง
3. **ห้ามเขียนลง Notion โดยไม่ผ่าน review** — ต้องรอ approve ก่อนทุกครั้ง
4. **ห้าม commit `.env`** — NOTION_TOKEN ต้องอยู่ใน `.env` เท่านั้น (ดู .gitignore)
5. **แหล่งข้อมูลที่เชื่อถือได้:** official documentation, peer-reviewed papers, เว็บไซต์องค์กร/สถาบัน ห้ามใช้ blog ทั่วไปที่ไม่มี author credibility
6. **ภาษา:** บทความใช้ภาษาไทยเป็นหลัก เติมเนื้อหาเป็นภาษาไทยเสมอ

---

## Environment Variables

| Variable | ที่เก็บ | ใช้สำหรับ |
|---|---|---|
| `NOTION_TOKEN` | `.env` (local) / GitHub Secret | Notion API authentication |

---

## Dashboard URL

GitHub Pages: `https://wjexstudio.github.io/learning-dashboard`
