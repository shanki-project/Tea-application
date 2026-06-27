"""FastAPI application entry point.

- Registers the API under `settings.API_PREFIX` (default `/api`).
- Serves the static frontend (public/) at `/`, so a single container serves
  both the API and the website.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    docs_url=f"{settings.API_PREFIX}/docs",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API routes (must be registered BEFORE the catch-all static mount) ---
app.include_router(api_router, prefix=settings.API_PREFIX)


# --- Static frontend ---
# `html=True` makes StaticFiles serve index.html at "/" and handle client-side
# routing fallbacks. Mounted last so it doesn't shadow the API.
_static_dir = Path(settings.STATIC_DIR)
if _static_dir.is_dir():
    app.mount("/", StaticFiles(directory=str(_static_dir), html=True), name="static")
