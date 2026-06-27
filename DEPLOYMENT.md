# Shankis Tea — Deploy, Run & Operate Guide

One document for everyone: **DevOps** (deploy & operate), **developers** (run & change
the code), and anyone who needs to understand **how the application actually runs**.

- App: a tea e-commerce store with role-based access control (RBAC).
- Backend: **Python / FastAPI** serving a REST API **and** the static website.
- Database: **MySQL 8** (InnoDB).
- Packaging: **Docker + docker-compose** (one backend container + one MySQL container).

> TL;DR for DevOps: `cp .env.example .env` → edit secrets → `docker compose up -d --build`
> → `docker compose exec backend python -m scripts.seed`. App on port **8000**. Put a
> TLS reverse proxy in front. Persistent state lives in two volumes: `db_data`, `uploads_data`.

---

## 1. What this application is

A single deployable service that does three things on one port (**8000**):

| Path | Served | Purpose |
|------|--------|---------|
| `/api/*` | FastAPI JSON API | All business logic (auth, products, cart, orders, admin) |
| `/api/docs` | Swagger UI | Interactive API documentation |
| `/uploads/*` | Uploaded files | Product images uploaded by admins |
| `/` and everything else | Static files from `public/` | The website (landing, shop, login, cart, checkout, account, admin dashboard) |

Because the API and the website ship in the **same container**, there is only one thing
to deploy. No separate frontend build/host is required.

### Roles (RBAC)
- **Super Admin** — full access: manage admin/staff accounts, all users & orders, audit log, analytics.
- **Admin / Staff** — product CRUD, inventory/stock, order status, image uploads.
- **Customer** — browse, cart, checkout (mock payment), order history, reviews.
- **Guest** — browse only; restricted actions redirect to login.

---

## 2. How the code runs (architecture)

### 2.1 Runtime topology

```
                       ┌─────────────────────────────────────────────┐
   Browser  ──HTTP──▶  │  backend container  (port 8000)             │
                       │                                             │
                       │   Gunicorn  ──manages──▶  Uvicorn workers   │
                       │                              │              │
                       │                         FastAPI app         │
                       │            /api → routers → services → CRUD  │
                       │            /    → static files (public/)     │
                       │            /uploads → uploaded images        │
                       └───────────────────────│─────────────────────┘
                                                │ SQLAlchemy + PyMySQL
                                                ▼
                       ┌─────────────────────────────────────────────┐
                       │  db container  MySQL 8  (internal port 3306) │
                       │  data persisted in the `db_data` volume      │
                       └─────────────────────────────────────────────┘
```

- **Gunicorn** is the production process manager; it runs **N Uvicorn workers**
  (`WEB_CONCURRENCY`, default 2) each running the async FastAPI app.
- The backend reaches MySQL over the private docker network using hostname **`db`**
  (not via the host). The host port mapping (`3307`) is only for optional external tools.

### 2.2 Container startup sequence

The container entrypoint is [`backend/scripts/start.sh`](backend/scripts/start.sh):

1. `alembic upgrade head` — applies any pending DB migrations (creates tables on first run).
2. `gunicorn app.main:app` with Uvicorn workers — starts serving.

`docker-compose` makes the backend **wait for MySQL to be healthy** (`depends_on:
condition: service_healthy`) before it starts, so migrations don't run against a DB
that isn't ready.

### 2.3 Request flow (example: a customer checks out)

```
POST /api/orders/checkout
  → CORS middleware
  → JWT auth dependency (get_current_user) → must be role "customer"
  → route handler (app/api/routes/orders.py)
  → service (app/services/checkout.py): validate stock, generate fake TXN id,
       create order + items, decrement stock, clear cart  (one DB transaction)
  → response (order + fake_transaction_id)
```

> Payment is **mocked** — there is no real gateway. The frontend simulates the
> "Processing…" delay; the backend stores a fake `TXN-…` transaction id. Swap
> `app/services/checkout.py` for a real integration when going live.

### 2.4 Backend layer structure (separation of concerns)

```
app/
  main.py            FastAPI app: mounts API (/api), uploads (/uploads), static (/)
  core/
    config.py        all settings from env vars (.env)
    database.py      SQLAlchemy engine, session, Base
    security.py      JWT encode/decode, bcrypt hashing
  models/            SQLAlchemy ORM tables (users, products, orders, …)
  schemas/           Pydantic request/response models (the API contract)
  crud/              data-access functions (the only place that touches the ORM)
  services/          business logic (auth, checkout, audit)
  api/
    deps.py          shared dependencies: get_db, get_current_user, require_* (RBAC)
    router.py        aggregates all feature routers under /api
    routes/          one file per feature: auth, users, products, cart, orders,
                     reviews, dashboard, uploads, health
```

Rule of thumb when adding a feature: **model → schema → crud → (service) → route → migration.**

### 2.5 Database schema (tables)

`users`, `roles`, `products`, `cart_items`, `orders`, `order_items`, `reviews`,
`audit_logs` — all **InnoDB / utf8mb4**, with foreign keys, indexes on `email`/`slug`,
and a rating check constraint. Defined as SQLAlchemy models in `backend/app/models/`
and created by the Alembic migration
[`backend/alembic/versions/0001_initial_schema.py`](backend/alembic/versions/0001_initial_schema.py).

---

## 3. Repository layout

```
shankis-tea/
├── backend/
│   ├── app/                  FastAPI application (see §2.4)
│   ├── alembic/              database migrations
│   ├── scripts/
│   │   ├── start.sh          container entrypoint (migrate → serve)
│   │   └── seed.py           creates Super Admin + Dawn/Dusk/Night products
│   ├── tests/                pytest suite (runs on SQLite, no MySQL needed)
│   ├── requirements.txt      runtime dependencies (pinned)
│   ├── requirements-dev.txt  + test/lint dependencies
│   ├── Dockerfile            backend image (non-root, healthcheck)
│   └── alembic.ini
├── public/                   the website (HTML/CSS/JS) + product images + video
├── docker-compose.yml        backend + MySQL stack
├── .env.example              copy to .env and fill in
├── README.md                 quick start
└── DEPLOYMENT.md             ← this file
```

---

## 4. Configuration (environment variables)

All configuration comes from environment variables, loaded from a `.env` file at the
repo root (see [`.env.example`](.env.example)). **Never commit the real `.env`.**

| Variable | Used by | Default | Notes |
|----------|---------|---------|-------|
| `ENVIRONMENT` | app | `production` (compose) | `development` / `staging` / `production` |
| `DEBUG` | app | `false` | `true` echoes SQL + verbose errors — never in prod |
| `SECRET_KEY` | auth | — | **Set a strong value.** `openssl rand -hex 32` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | auth | `1440` | JWT lifetime (24h) |
| `CORS_ORIGINS` | app | `*` | Comma-separated origins in prod (e.g. `https://shankistea.com`) |
| `BACKEND_PORT` | compose | `8000` | Host port for the app |
| `WEB_CONCURRENCY` | gunicorn | `2` | Worker processes; rule of thumb `2 × vCPU + 1` |
| `MYSQL_HOST` | backend | `db` (compose) | `db` in Docker; `localhost` for local-venv runs |
| `MYSQL_PORT` | backend | `3306` | Internal DB port |
| `MYSQL_DB` | both | `shankistea` | Database name |
| `MYSQL_USER` | both | `shankis` | App DB user |
| `MYSQL_PASSWORD` | both | — | **Set a strong value** |
| `MYSQL_ROOT_PASSWORD` | db | — | **Set a strong value** |
| `MYSQL_HOST_PORT` | compose | `3307` | Host port to reach MySQL from outside (optional) |
| `UPLOAD_DIR` | backend | `/app/uploads` | Where product images are written (a volume) |
| `DATABASE_URL` | backend | — | Optional full SQLAlchemy URL; overrides the `MYSQL_*` fields |
| `SUPERADMIN_EMAIL` / `_PASSWORD` / `_NAME` | seed | see `.env.example` | First Super Admin created by the seed script |

---

## 5. Developer guide — run & change the code

You have two options. Most developers use **Docker** for parity with production.

### Option A — Docker (recommended)

```bash
cp .env.example .env          # then edit secrets
docker compose up -d --build  # build + start backend and MySQL
docker compose exec backend python -m scripts.seed   # first run only
```
Open http://localhost:8000 — API docs at http://localhost:8000/api/docs.

Day-to-day:
```bash
docker compose up -d --build   # rebuild after changing backend or frontend code
docker compose logs -f backend # tail logs
docker compose down            # stop (keeps data)
```

> The frontend and backend are **baked into the image at build time**, so after editing
> any file under `backend/` or `public/`, run `docker compose up -d --build` to see it.

### Option B — Local Python + local MySQL (fastest inner loop)

Gives you `uvicorn --reload` hot-reloading. Requires a local MySQL.

1. **Install MySQL Community Server** (free): https://dev.mysql.com/downloads/ —
   Windows installer, `brew install mysql` (macOS), or `apt install mysql-server` (Linux).

2. **Create the database & user** (`mysql -u root -p`):
   ```sql
   CREATE DATABASE shankistea CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'shankis'@'localhost' IDENTIFIED BY 'your-password';
   GRANT ALL PRIVILEGES ON shankistea.* TO 'shankis'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. **Point `.env` at it:** set `MYSQL_HOST=localhost` and the matching `MYSQL_*` values.

4. **Install, migrate, seed, run:**
   ```bash
   cd backend
   python -m venv .venv
   # Windows:  .venv\Scripts\activate     macOS/Linux:  source .venv/bin/activate
   pip install -r requirements-dev.txt
   alembic upgrade head            # create tables
   python -m scripts.seed          # Super Admin + 3 products
   uvicorn app.main:app --reload   # http://localhost:8000
   ```

> ⚠️ Don't run Docker and the local server at the same time — both use port 8000.

### Tests & linting
```bash
cd backend
pytest          # integration tests run on in-memory SQLite (no MySQL needed)
ruff check .    # lint
ruff format .   # auto-format
```

### Database migrations (when you change a model)
```bash
cd backend
alembic revision --autogenerate -m "add wishlist table"   # generate
alembic upgrade head                                       # apply
alembic downgrade -1                                       # roll back one
```
In Docker, migrations run **automatically** on container start. To run one manually:
`docker compose exec backend alembic upgrade head`.

### Default login after seeding
`superadmin@shankistea.com` / `ChangeMe123!` — **change this after first login.**

---

## 6. DevOps deployment guide

### 6.1 Prerequisites on the host
- Docker Engine + the Docker Compose plugin (`docker compose version`).
- A reverse proxy for TLS (Nginx, Caddy, Traefik, or a cloud load balancer).
- Outbound network access to pull base images (`python:3.12-slim`, `mysql:8.4`).

### 6.2 First deployment
```bash
git clone <repo> && cd shankis-tea
cp .env.example .env
#  Edit .env — REQUIRED before going live:
#    SECRET_KEY            = openssl rand -hex 32
#    MYSQL_PASSWORD        = strong value
#    MYSQL_ROOT_PASSWORD   = strong value
#    SUPERADMIN_PASSWORD   = strong value
#    ENVIRONMENT=production    DEBUG=false
#    CORS_ORIGINS=https://yourdomain.com
docker compose up -d --build
docker compose exec backend python -m scripts.seed     # one time, creates Super Admin
docker compose ps                                      # both should be "healthy"
curl -fsS http://localhost:8000/api/health             # {"status":"ok",...}
```

### 6.3 What ships & how it's hardened
The backend image ([`backend/Dockerfile`](backend/Dockerfile)):
- Based on `python:3.12-slim`; installs pinned deps from `requirements.txt`.
- Copies `backend/` and `public/` into the image; sets `STATIC_DIR`, `UPLOAD_DIR`.
- Runs as a **non-root user** (`appuser`).
- Has a built-in **HEALTHCHECK** hitting `/api/health`.
- Entrypoint runs migrations then Gunicorn/Uvicorn.

### 6.4 Reverse proxy / TLS (required for production)
Terminate TLS at a proxy and forward to the backend on `8000`. Example Nginx:
```nginx
server {
  listen 443 ssl http2;
  server_name shankistea.com;
  ssl_certificate     /etc/letsencrypt/live/shankistea.com/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/shankistea.com/privkey.pem;

  client_max_body_size 6m;            # allow product image uploads (max 5 MB)

  location / {
    proxy_pass         http://127.0.0.1:8000;
    proxy_set_header   Host $host;
    proxy_set_header   X-Real-IP $remote_addr;
    proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto $scheme;
  }
}
```
Then set `CORS_ORIGINS=https://shankistea.com` in `.env` and restart the backend.

### 6.5 Health & readiness probes
- **Liveness:** `GET /api/health` → `200` if the process is up.
- **Readiness:** `GET /api/health/db` → `200` if MySQL is reachable.

Use these for load-balancer health checks / Kubernetes probes.

### 6.6 Persistent state (back this up!)
Two named volumes hold everything stateful:

| Volume | Holds | Backup |
|--------|-------|--------|
| `db_data` | the entire MySQL database | logical dump (below) or volume snapshot |
| `uploads_data` | uploaded product images | volume snapshot / file copy |

**Database backup:**
```bash
docker compose exec db sh -c \
  'exec mysqldump -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' > backup-$(date +%F).sql
```
**Restore:**
```bash
docker compose exec -T db sh -c \
  'exec mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' < backup-2026-06-27.sql
```

### 6.7 Updating to a new version (zero-ish downtime)
```bash
git pull
docker compose up -d --build        # rebuild image; migrations auto-run on start
docker compose ps                   # confirm healthy
```
Migrations are forward-only on startup. For risky migrations, back up `db_data` first.

### 6.8 Scaling
- Vertical: raise `WEB_CONCURRENCY` (≈ `2 × vCPU + 1`).
- Horizontal: run multiple backend replicas behind the proxy. They are stateless
  **except** for `uploads_data` — for multi-host you must move uploads to shared
  storage (NFS/S3-style) or a managed object store, and point all replicas at it.
- The app is fine against a managed MySQL (RDS/Cloud SQL): set `DATABASE_URL` or the
  `MYSQL_*` vars to the managed instance and drop the `db` service from compose.

---

## 7. Operations runbook

### Common commands
```bash
docker compose ps                       # status
docker compose logs -f backend          # tail backend logs
docker compose logs db                  # MySQL logs
docker compose restart backend          # restart app only
docker compose exec backend bash        # shell into the backend container
docker compose exec backend python -m scripts.seed   # (re)seed (idempotent)
docker compose down                     # stop, keep data
docker compose down -v                  # stop and DELETE all data (db + uploads)
```

### Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `bind: address already in use` on **3306** | A local MySQL already uses 3306 | Default host map is `3307`; or set `MYSQL_HOST_PORT` in `.env` |
| Backend keeps restarting at boot | DB not ready / wrong creds | Check `docker compose logs db`; verify `MYSQL_*` in `.env` |
| `Can't connect to MySQL 'db'` | DB still starting | Compose waits for healthy; if it persists, check the db healthcheck/logs |
| Image upload returns **500 / permission denied** | `uploads_data` volume owned by root | Image creates `/app/uploads` as `appuser`; if it predates that, recreate the volume: `docker compose rm -f backend && docker volume rm <proj>_uploads_data && docker compose up -d --build` |
| Verbose SQL in logs | `DEBUG=true` | Set `DEBUG=false` and `docker compose up -d` |
| 401 on every API call | Missing/expired JWT | Re-login; check `SECRET_KEY` hasn't changed between restarts |
| CORS error in browser | `CORS_ORIGINS` doesn't include the site origin | Set it to your domain and restart backend |

---

## 8. Security checklist (before going live)

- [ ] `SECRET_KEY` set to a strong random value (and stable across restarts).
- [ ] `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD`, `SUPERADMIN_PASSWORD` changed from defaults.
- [ ] `ENVIRONMENT=production`, `DEBUG=false`.
- [ ] `CORS_ORIGINS` restricted to your real domain(s) — not `*`.
- [ ] TLS terminated at a reverse proxy; HTTP redirects to HTTPS.
- [ ] `.env` is **not** committed and not baked into the image (it isn't by default).
- [ ] Super Admin password changed after the first login.
- [ ] `db_data` and `uploads_data` are included in your backup routine.
- [ ] Do **not** expose MySQL's host port publicly (remove the `db` `ports:` mapping in prod).

Built-in protections: passwords hashed with **bcrypt**; JWT auth on protected routes;
**RBAC** enforced server-side; admin actions written to an **audit log**; order-status
transitions and stock changes validated on the server; SQL via SQLAlchemy (parameterized).

---

## 9. API reference (summary)

Full interactive docs: **`/api/docs`**. Auth = send `Authorization: Bearer <token>`.

```
POST   /api/auth/signup              register (Customer)            public
POST   /api/auth/login               JWT login                      public
GET    /api/auth/me                  current user                   auth
POST   /api/auth/change-password     change password                auth
POST   /api/auth/password-reset/*    request / confirm reset        public
GET    /api/products                 list/search/filter             public
GET    /api/products/{slug}          product detail                 public
POST|PUT|DELETE /api/products[...]   product CRUD                   admin+
PATCH  /api/products/{id}/stock      set stock                      admin+
POST   /api/uploads                  upload product image           admin+
GET    /api/cart                     view cart                      customer
POST   /api/cart/items               add to cart                    customer
POST   /api/orders/checkout          mock-payment checkout          customer
GET    /api/orders                   my order history               customer
POST   /api/orders/{id}/cancel       cancel own order (+restock)    customer
PATCH  /api/orders/{id}/status       advance order status           admin+
GET|POST /api/products/{id}/reviews  list / write review            public / customer
GET    /api/reviews/mine             my reviews                     customer
PUT|DELETE /api/reviews/{id}         edit / delete own review       customer
GET    /api/users                    all users                      super admin
POST   /api/users/admins             create admin/staff             super admin
PATCH  /api/users/{id}/role          promote / demote               super admin
GET    /api/dashboard/summary        role-aware KPIs                auth
GET    /api/dashboard/orders         all orders (+customer info)    admin+
GET    /api/dashboard/inventory      stock list                     admin+
GET    /api/dashboard/analytics      sales metrics for charts       admin+
GET    /api/dashboard/audit-logs     audit log                      super admin
GET    /api/health  /api/health/db   liveness / readiness           public
```

---

## 10. Quick reference card

| I want to… | Command |
|------------|---------|
| Start everything (Docker) | `docker compose up -d --build` |
| Seed first Super Admin + products | `docker compose exec backend python -m scripts.seed` |
| See logs | `docker compose logs -f backend` |
| Stop (keep data) | `docker compose down` |
| Wipe everything | `docker compose down -v` |
| Run a migration | `docker compose exec backend alembic upgrade head` |
| Back up the DB | see §6.6 |
| Run locally with reload | `uvicorn app.main:app --reload` (see §5 Option B) |
| Run tests | `cd backend && pytest` |
| App URL | http://localhost:8000  · docs `/api/docs` |
