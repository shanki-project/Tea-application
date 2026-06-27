"""Shared FastAPI dependencies.

Re-exported here so routes import from a stable location regardless of where the
underlying implementation lives. Add auth/current-user dependencies here later.
"""

from app.core.database import get_db

__all__ = ["get_db"]
