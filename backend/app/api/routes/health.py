"""Health / readiness endpoints used by Docker, load balancers, and DevOps."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.config import settings

router = APIRouter()


@router.get("/health", summary="Liveness probe")
def health() -> dict:
    """Cheap check that the process is up. No external dependencies touched."""
    return {"status": "ok", "service": settings.PROJECT_NAME, "env": settings.ENVIRONMENT}


@router.get("/health/db", summary="Readiness probe (database)")
def health_db(db: Session = Depends(get_db)) -> dict:
    """Verifies the database is reachable."""
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "reachable"}
