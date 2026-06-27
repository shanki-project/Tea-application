# ASSAM TEA

Luxury tea storefront. **Python (FastAPI) backend** serving a REST API **and** the
static frontend, backed by **MySQL**. Containerized with Docker for deployment.

> The Python backend replaces the previous Node/Express static server.

---

## Project structure

```
assamtea/
├── backend/                    # Python / FastAPI application
│   ├── app/
│   │   ├── main.py             # FastAPI entry: mounts API + static frontend
│   │   ├── core/
│   │   │   ├── config.py       # Settings from env vars (.env)
│   │   │   └── database.py     # SQLAlchemy engine, session, Base
│   │   ├── api/
│   │   │   ├── router.py       # Aggregates all feature routers
│   │   │   ├── deps.py         # Shared dependencies (DB session, auth, ...)
│   │   │   └── routes/         # One module per feature (health.py, ...)
│   │   ├── models/             # SQLAlchemy ORM models  (DB tables)
│   │   ├── schemas/            # Pydantic schemas        (API contract)
│   │   ├── crud/               # Data-access functions
│   │   └── services/           # Business logic
│   ├── alembic/                # Database migrations
│   ├── alembic.ini
│   ├── tests/                  # pytest suite
│   ├── scripts/start.sh        # Container entrypoint (migrate + serve)
│   ├── requirements.txt        # Runtime deps (pinned)
│   ├── requirements-dev.txt    # + test/lint deps
│   ├── pyproject.toml          # ruff + pytest config
│   └── Dockerfile
├── public/                     # Static frontend (index.html, images, video)
├── docker-compose.yml          # backend + MySQL stack
├── .env.example                # Copy to .env and fill in
├── .dockerignore
└── .gitignore
```

**Where features go** (next iteration): a feature = a model in `models/`, schemas in
`schemas/`, data access in `crud/`, optional logic in `services/`, and a router in
`api/routes/` wired into `api/router.py`. Then generate a migration.

---

## Run with Docker (recommended)

```bash
cp .env.example .env          # then edit passwords
docker compose up --build
```

- Website:  http://localhost:8000
- API docs (Swagger): http://localhost:8000/api/docs
- Health:   http://localhost:8000/api/health

Migrations run automatically on container start (`alembic upgrade head`).

## Run locally without Docker

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

# Point at a reachable MySQL (set MYSQL_HOST=localhost in ../.env)
alembic upgrade head
uvicorn app.main:app --reload
```

App: http://localhost:8000

## Tests & lint

```bash
cd backend
pytest
ruff check .
```

## Database migrations

```bash
cd backend
alembic revision --autogenerate -m "add products table"   # after adding a model
alembic upgrade head
```

---

## Configuration

All config comes from environment variables (see `.env.example`). Key ones:

| Variable | Purpose |
|---|---|
| `ENVIRONMENT` | `development` / `staging` / `production` |
| `DEBUG` | SQL echo + verbose errors |
| `CORS_ORIGINS` | Comma-separated allowed origins (`*` only for dev) |
| `MYSQL_*` | Database host/port/name/credentials |
| `DATABASE_URL` | Optional full SQLAlchemy URL (overrides `MYSQL_*`) |
| `WEB_CONCURRENCY` | Gunicorn worker count |

## Notes for deployment (DevOps)

- The container is self-contained: it serves the API and the static site on port `8000`.
- It runs as a non-root user and exposes `GET /api/health` (liveness) and
  `GET /api/health/db` (readiness) for probes; a Docker `HEALTHCHECK` is built in.
- Secrets must be injected via environment / secret manager — never bake `.env` into the image.
- Put a reverse proxy (Nginx/ALB) in front for TLS termination.
