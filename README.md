# Shankis Tea — Full-Stack E-Commerce with RBAC

A minimalist, ritualistic tea brand store (Dawn / Dusk / Night blends) with a
**Python FastAPI** backend, **MySQL** database, **JWT auth**, **role-based access
control**, and a **mock checkout** (no real payment gateway). The existing
static landing page is kept as the brand entry point; the shop, cart, checkout,
account, and admin pages are wired to the REST API.

> Everything here is free to run locally — MySQL Community Edition, no paid
> services, no external payment provider.

---

## Tech stack

| Layer    | Choice |
|----------|--------|
| Backend  | FastAPI (Python 3.12+) |
| Database | MySQL 8 (InnoDB, utf8mb4) |
| ORM      | SQLAlchemy 2.0 + PyMySQL |
| Auth     | JWT (python-jose) + bcrypt (passlib) |
| Migrations | Alembic |
| Frontend | Static HTML/CSS/vanilla JS calling the REST API |
| Payment  | Mock/simulated only — fake transaction id, no gateway |

## Roles (RBAC)

| Role | Can do |
|------|--------|
| **Super Admin** | Everything: manage admin/staff accounts (create/promote/demote/deactivate/delete), view all users & orders, view audit logs |
| **Admin / Staff** | Product CRUD, inventory/stock, view & advance order status. Cannot manage admins or see audit logs |
| **Customer** | Browse, cart, checkout (mock payment), order history & tracking, review purchased products |
| **Guest** | Browse products only; restricted actions redirect to login/signup |

---

## Project structure

```
shankis-tea/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI entry: API at /api + serves frontend at /
│   │   ├── core/               config, database, security (JWT/bcrypt), utils
│   │   ├── models/             SQLAlchemy models (users, roles, products, cart,
│   │   │                         orders, order_items, reviews, audit_logs)
│   │   ├── schemas/            Pydantic request/response models
│   │   ├── crud/               data-access functions
│   │   ├── services/           auth, checkout (mock payment), audit logging
│   │   └── api/
│   │       ├── deps.py         get_current_user + RBAC guards
│   │       ├── router.py       aggregates routers
│   │       └── routes/         auth, users, products, cart, orders, reviews, dashboard
│   ├── alembic/                migrations (0001_initial_schema.py creates all tables)
│   ├── scripts/
│   │   ├── seed.py             Super Admin + Dawn/Dusk/Night products + roles
│   │   └── start.sh            container entrypoint (migrate → serve)
│   ├── tests/                  pytest
│   ├── requirements.txt
│   └── Dockerfile
├── public/                     frontend: index.html (landing) + shop/login/signup/
│                                 cart/checkout/account/admin + css/ + js/
├── docker-compose.yml          backend + MySQL
├── .env.example
└── README.md
```

---

## Option A — Run with Docker (easiest)

Requires Docker Desktop. MySQL runs in a container, so you don't install it.

```bash
cp .env.example .env            # edit passwords + SECRET_KEY
docker compose up --build
# migrations run automatically on startup; then seed once:
docker compose exec backend python -m scripts.seed
```

Open **http://localhost:8000** — API docs at **/api/docs**.

---

## Option B — Run locally with MySQL Community Server (free)

### 1. Install MySQL Community Server (free)
- **Windows:** download the **MySQL Community Server** + **MySQL Installer** from
  https://dev.mysql.com/downloads/installer/ → install "Server only" (or full),
  set a root password during setup.
- **macOS:** `brew install mysql && brew services start mysql`
- **Ubuntu/Debian:** `sudo apt install mysql-server && sudo systemctl start mysql`

Verify it's running: `mysql --version`.

### 2. Create the database and a user
Open a MySQL shell (`mysql -u root -p`) and run:

```sql
CREATE DATABASE shankistea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'shankis'@'localhost' IDENTIFIED BY 'change-me-strong-password';
GRANT ALL PRIVILEGES ON shankistea.* TO 'shankis'@'localhost';
FLUSH PRIVILEGES;
```

### 3. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` and set (for a local install):
```
MYSQL_HOST=localhost
MYSQL_DB=shankistea
MYSQL_USER=shankis
MYSQL_PASSWORD=change-me-strong-password
SECRET_KEY=<output of: openssl rand -hex 32>
```

### 4. Create a virtual environment and install dependencies
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 5. Run migrations (creates all tables)
```bash
alembic upgrade head
```

### 6. Seed the Super Admin + the 3 products
```bash
python -m scripts.seed
```
This prints the Super Admin login (default `superadmin@shankistea.com` /
`ChangeMe123!` — **change it after first login**).

### 7. Start the server
```bash
uvicorn app.main:app --reload
```

Open **http://localhost:8000**. Interactive API docs: **/api/docs**.

---

## Using the app

- **Landing page** (`/`) → click **Shop**.
- **Sign up** as a customer, add blends to cart, **Checkout** → pick a payment
  method → watch the simulated *Processing → Payment Successful → Order Confirmed*
  flow (a fake `TXN-...` id is stored).
- **Account** → order history with a status tracker; review products you've bought.
- **Super Admin** → log in with the seeded account → **Dashboard**:
  manage products, advance order status, create Admin/Staff accounts, change roles,
  activate/deactivate/delete users, and view the **audit log**.
- Create an **Admin/Staff** account from the Super Admin dashboard to see the
  reduced-permission view (products + orders only).

## Key API endpoints (full list at `/api/docs`)

```
POST   /api/auth/signup            register (Customer)         public
POST   /api/auth/login             JWT login                   public
GET    /api/auth/me                current user                auth
POST   /api/auth/password-reset/request | /confirm            public
GET    /api/products               list/search/filter          public
POST   /api/products               create product              admin+
PUT    /api/products/{id}          update product              admin+
PATCH  /api/products/{id}/stock    set stock                   admin+
DELETE /api/products/{id}          delete product              admin+
GET    /api/cart                   view cart                   customer
POST   /api/cart/items             add to cart                 customer
POST   /api/auth/change-password   change password (logged in) auth
POST   /api/orders/checkout        mock-payment checkout       customer
GET    /api/orders                 my order history            customer
POST   /api/orders/{id}/cancel     cancel own order (+restock) customer
PATCH  /api/orders/{id}/status     advance order status        admin+
GET    /api/products/{pid}/reviews list reviews                public
POST   /api/products/{pid}/reviews review purchased product    customer
GET    /api/reviews/mine           my reviews                  customer
PUT    /api/reviews/{id}           edit own review             customer
DELETE /api/reviews/{id}           delete own review           customer
POST   /api/uploads                upload product image        admin+
GET    /api/users                  all users                   super admin
POST   /api/users/admins           create admin/staff          super admin
PATCH  /api/users/{id}/role        promote/demote              super admin
GET    /api/dashboard/orders       all orders (+customer info) admin+
GET    /api/dashboard/analytics    sales metrics for charts    admin+
GET    /api/dashboard/audit-logs   audit log                   super admin
```

## Tests & lint
```bash
cd backend
pytest
ruff check .
```

## Notes for DevOps / deployment
- Single deployable container serves both the API and the static frontend on port 8000.
- Runs as a non-root user; `HEALTHCHECK` + `/api/health` (liveness) and
  `/api/health/db` (readiness) probes included.
- All secrets via environment (`SECRET_KEY`, DB creds) — never bake `.env` into the image.
- Order-status transitions are enforced server-side (Placed → Packed → Shipped → Delivered).
- Stock auto-decrements on checkout; products at/below `LOW_STOCK_THRESHOLD` (default 10)
  are flagged for admins.
- The mock payment is intentional — replace `app/services/checkout.py` with a real
  gateway integration when you go live.
- **Uploaded product images** are written to `UPLOAD_DIR` (default `/app/uploads` in
  Docker) and served at `/uploads/<file>`. The `uploads_data` named volume persists
  them across rebuilds; the image creates the directory owned by the non-root app
  user so the volume inherits write permission. Cancelling an order restocks its items.
