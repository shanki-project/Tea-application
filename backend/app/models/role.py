from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Role(Base):
    """Reference catalog of roles (Super Admin, Admin, Customer).

    The authoritative role for access control lives on `users.role`; this table
    exists as a lookup/catalog per the schema spec.
    """

    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
