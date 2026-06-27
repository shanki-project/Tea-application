from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.audit_log import AuditLog


def list_all(db: Session, limit: int = 200) -> list[AuditLog]:
    stmt = (
        select(AuditLog)
        .options(joinedload(AuditLog.admin))
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    return list(db.scalars(stmt).all())
