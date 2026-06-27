from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    admin_id: int | None = None
    action: str
    target_table: str | None = None
    target_id: int | None = None
    timestamp: datetime
    admin_name: str | None = None
