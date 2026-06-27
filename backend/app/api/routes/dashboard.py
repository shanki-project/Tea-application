"""Role-aware dashboard endpoints for Admin/Staff and Super Admin."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin, require_super_admin
from app.api.routes.orders import _to_read as order_to_read
from app.api.serializers import product_read
from app.core.config import settings
from app.crud import audit_log as audit_crud
from app.crud import order as order_crud
from app.crud import product as product_crud
from app.models.enums import UserRole
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.audit import AuditLogRead
from app.schemas.order import OrderRead
from app.schemas.product import ProductRead

router = APIRouter()


@router.get("/summary")
def summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """High-level counts tailored to the caller's role."""
    data: dict = {"role": user.role.value}
    if user.role in (UserRole.admin, UserRole.super_admin):
        data["product_count"] = db.scalar(select(func.count(Product.id)))
        data["order_count"] = db.scalar(select(func.count(Order.id)))
        data["low_stock_count"] = db.scalar(
            select(func.count(Product.id)).where(
                Product.stock_qty <= settings.LOW_STOCK_THRESHOLD
            )
        )
    if user.role == UserRole.super_admin:
        data["user_count"] = db.scalar(select(func.count(User.id)))
        data["revenue"] = float(
            db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0))) or 0
        )
    if user.role == UserRole.customer:
        data["my_order_count"] = len(order_crud.list_for_user(db, user.id))
    return data


# ----- Admin/Staff -----
@router.get("/orders", response_model=list[OrderRead])
def all_orders(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [order_to_read(o) for o in order_crud.list_all(db)]


@router.get("/inventory", response_model=list[ProductRead])
def inventory(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return [product_read(p) for p in product_crud.search(db)]


# ----- Super Admin -----
@router.get("/audit-logs", response_model=list[AuditLogRead])
def audit_logs(db: Session = Depends(get_db), _: User = Depends(require_super_admin)):
    rows = audit_crud.list_all(db)
    return [
        AuditLogRead(
            id=r.id,
            admin_id=r.admin_id,
            action=r.action,
            target_table=r.target_table,
            target_id=r.target_id,
            timestamp=r.timestamp,
            admin_name=r.admin.name if r.admin else None,
        )
        for r in rows
    ]
