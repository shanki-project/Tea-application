<div align="center">

# 🍵 SHANKIS TEA

### _Steeped in Silence_ — a luxury tea e-commerce experience

Dawn to wake · Dusk to unwind · Night to rest

<br/>

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=for-the-badge&logo=mysql&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)
![JWT](https://img.shields.io/badge/Auth-JWT%20%2B%20bcrypt-000000?style=for-the-badge&logo=jsonwebtokens&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)

</div>

---

## 🎬 The Story

<div align="center">

<video src="public/tea-story-final.mp4" controls muted loop playsinline width="80%"></video>

_If the video doesn't play inline, ▶️ **[click here to watch `tea-story-final.mp4`](public/tea-story-final.mp4)**._
_(Inline playback works in VS Code's Markdown preview and most local viewers.)_

</div>

---

## 🫖 The Collection

<div align="center">
<table>
  <tr>
    <td align="center" width="33%">
      <img src="public/dawn-product.png" width="170" alt="Dawn" /><br/>
      <b>DAWN</b><br/>
      <sub>Morning Clarity · Green tea</sub><br/>
      <sub>Tulsi · Rose · Cardamom</sub><br/>
      <b>₹890</b>
    </td>
    <td align="center" width="33%">
      <img src="public/dusk-product.png" width="170" alt="Dusk" /><br/>
      <b>DUSK</b> <sub>★ Bestseller</sub><br/>
      <sub>Evening Unwind · Black tea</sub><br/>
      <sub>Chamomile · Rose · Cardamom</sub><br/>
      <b>₹950</b>
    </td>
    <td align="center" width="33%">
      <img src="public/night-product.png" width="170" alt="Night" /><br/>
      <b>NIGHT</b><br/>
      <sub>Deep Rest · White tea</sub><br/>
      <sub>Ashwagandha · Rose · Lavender</sub><br/>
      <b>₹1,050</b>
    </td>
  </tr>
</table>

<sub>…plus 17 more blends across Green, Black, White, Oolong & Herbal categories (20 total).</sub>

</div>

---

## ✨ What it is

A full-stack tea store with **role-based access control (RBAC)**. A single Python
service serves the REST **API** _and_ the **website** — so there is just one thing to
deploy. Payment is **simulated** (no real gateway, no money moves).

| | Feature |
|---|---|
| 🛍️ | **Storefront** — 20 blends, search & category filter, product detail + reviews |
| 🔐 | **Auth** — JWT login/signup, bcrypt passwords, password reset & change |
| 👥 | **RBAC** — Super Admin · Admin/Staff · Customer · Guest |
| 🛒 | **Cart & Checkout** — persisted per user, mock "Processing → Paid → Confirmed" flow |
| 📦 | **Orders** — status workflow (Placed → Packed → Shipped → Delivered), cancel + auto-restock |
| ⭐ | **Reviews** — write/edit/delete on purchased products only |
| 📊 | **Admin dashboard** — product CRUD, inventory, **sales analytics with charts**, CSV export |
| 🖼️ | **Image uploads** — admins upload product photos (persisted to a volume) |
| 📝 | **Audit log** — every admin action recorded (Super Admin only) |

---

## 🧱 Tech stack

<div align="center">

| Layer | Technology |
|-------|-----------|
| **Backend** | FastAPI (Python 3.12), Gunicorn + Uvicorn workers |
| **Database** | MySQL 8 · InnoDB · utf8mb4 |
| **ORM / Migrations** | SQLAlchemy 2.0 + PyMySQL · Alembic |
| **Auth** | JWT (python-jose) · bcrypt (passlib) |
| **Frontend** | HTML / CSS / vanilla JS · Chart.js (admin) |
| **Packaging** | Docker + docker-compose |
| **Payment** | Mock / simulated (fake transaction id) |

</div>

---

## 🎭 Roles & permissions

| Role | Can do |
|------|--------|
| **👑 Super Admin** | Everything — manage admin/staff accounts, all users & orders, analytics, audit log |
| **🛠️ Admin / Staff** | Product CRUD, inventory/stock, order status, image uploads |
| **🙋 Customer** | Browse, cart, checkout, order history & tracking, reviews |
| **👤 Guest** | Browse only — restricted actions redirect to login |

---

## 🚀 Quick start (Docker)

> Requires Docker Desktop. MySQL runs in a container — nothing else to install.

```bash
cp .env.example .env          # then edit the secrets
docker compose up -d --build
docker compose exec backend python -m scripts.seed   # first run only
```

<div align="center">

| | URL |
|---|---|
| 🌐 **Landing (new design)** | http://localhost:8000/home.html |
| 🛍️ **Shop** | http://localhost:8000/shop.html |
| 📚 **API docs (Swagger)** | http://localhost:8000/api/docs |
| ❤️ **Health** | http://localhost:8000/api/health |

</div>

**Default Super Admin** → `superadmin@shankistea.com` / `ChangeMe123!` _(change after first login)_

---

## 💻 Run locally (without Docker)

<details>
<summary><b>Click to expand — local Python + MySQL setup</b></summary>

<br/>

**1. Install MySQL Community Server** (free) and create the DB:
```sql
CREATE DATABASE shankistea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'shankis'@'localhost' IDENTIFIED BY 'your-password';
GRANT ALL PRIVILEGES ON shankistea.* TO 'shankis'@'localhost';
FLUSH PRIVILEGES;
```

**2. Configure** — in `.env` set `MYSQL_HOST=localhost` and matching `MYSQL_*` values.

**3. Install, migrate, seed, run:**
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate   ·   macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
alembic upgrade head          # create all tables
python -m scripts.seed        # Super Admin + 20 products
uvicorn app.main:app --reload # http://localhost:8000
```

</details>

---

## 🗂️ Project structure

```
shankis-tea/
├── backend/
│   ├── app/
│   │   ├── main.py        FastAPI entry — API at /api + website at /
│   │   ├── core/          config · database · security (JWT/bcrypt)
│   │   ├── models/        SQLAlchemy tables
│   │   ├── schemas/       Pydantic request/response models
│   │   ├── crud/          data-access functions
│   │   ├── services/      business logic (auth · checkout · audit)
│   │   └── api/routes/    auth · users · products · cart · orders ·
│   │                        reviews · dashboard · uploads · health
│   ├── alembic/           database migrations
│   ├── scripts/           start.sh (entrypoint) · seed.py
│   └── tests/             pytest (runs on SQLite)
├── public/                website + product images + tea video
├── docker-compose.yml     backend + MySQL
├── .env.example
├── DEPLOYMENT.docx        ← full deploy & ops guide (Word)
└── README.md              ← you are here
```

---

## 🧪 Tests & lint

```bash
cd backend
pytest          # integration tests on in-memory SQLite (no MySQL needed)
ruff check .    # lint
```

---

## 📖 Full deployment & operations guide

For production deployment, architecture deep-dive, environment variables, reverse-proxy
/ TLS, backups, scaling, and a troubleshooting runbook, see:

> 📄 **[DEPLOYMENT.docx](DEPLOYMENT.docx)** (Word) — or the markdown source **[DEPLOYMENT.md](DEPLOYMENT.md)**

---

<div align="center">
<sub>© 2026 Shankis Tea — Rooted in the hills. · Payment is simulated for demo purposes.</sub>
</div>
