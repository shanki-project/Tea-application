"""SQLAlchemy ORM models.

Every model is imported here so Alembic autogenerate and `Base.metadata` see the
full schema.
"""

from app.core.database import Base  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.cart import CartItem  # noqa: F401
from app.models.enums import OrderStatus, UserRole  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.user import User  # noqa: F401

__all__ = [
    "Base",
    "AuditLog",
    "CartItem",
    "Order",
    "OrderItem",
    "OrderStatus",
    "Product",
    "Review",
    "Role",
    "User",
    "UserRole",
]
