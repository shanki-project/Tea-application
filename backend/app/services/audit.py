"""Audit logging for admin actions."""

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    admin_id: int | None,
    action: str,
    target_table: str | None = None,
    target_id: int | None = None,
) -> AuditLog:
    entry = AuditLog(
        admin_id=admin_id,
        action=action,
        target_table=target_table,
        target_id=target_id,
    )
    db.add(entry)
    db.flush()
    return entry
