"""Database engine, session factory, and the declarative Base.

Uses SQLAlchemy 2.0 (sync) with PyMySQL. DB-touching endpoints are declared as
plain `def` so FastAPI runs them in a threadpool — keeping sync DB calls safe.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.sqlalchemy_database_uri,
    pool_pre_ping=True,   # transparently recycle stale connections
    pool_recycle=3600,    # MySQL drops idle connections after wait_timeout
    echo=settings.DEBUG,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def get_db() -> Generator:
    """FastAPI dependency that yields a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
