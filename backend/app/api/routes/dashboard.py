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
from app.models.enums import OrderStatus, UserRole
from app.models.order import Order, OrderItem
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


@router.get("/analytics")
def analytics(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Sales metrics for the admin charts. Revenue excludes cancelled orders."""
    valid = Order.status != OrderStatus.cancelled

    revenue = float(
        db.scalar(select(func.coalesce(func.sum(Order.total_amount), 0)).where(valid)) or 0
    )
    order_total = db.scalar(select(func.count(Order.id))) or 0

    # Orders grouped by status
    by_status_rows = db.execute(
        select(Order.status, func.count(Order.id)).group_by(Order.status)
    ).all()
    by_status = {s.value if hasattr(s, "value") else str(s): c for s, c in by_status_rows}

    # Top products by quantity sold (valid orders only)
    top_rows = db.execute(
        select(
            Product.name,
            func.sum(OrderItem.quantity).label("qty"),
            func.sum(OrderItem.quantity * OrderItem.price_at_purchase).label("revenue"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(valid)
        .group_by(Product.id, Product.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(5)
    ).all()
    top_products = [
        {"name": name, "qty": int(qty or 0), "revenue": float(rev or 0)}
        for name, qty, rev in top_rows
    ]

    # Revenue per day (valid orders)
    day_rows = db.execute(
        select(
            func.date(Order.created_at).label("day"),
            func.sum(Order.total_amount).label("revenue"),
        )
        .where(valid)
        .group_by(func.date(Order.created_at))
        .order_by(func.date(Order.created_at))
    ).all()
    revenue_by_day = [
        {"day": str(day), "revenue": float(rev or 0)} for day, rev in day_rows
    ]

    low_stock = db.scalar(
        select(func.count(Product.id)).where(
            Product.stock_qty <= settings.LOW_STOCK_THRESHOLD
        )
    )

    return {
        "revenue": revenue,
        "order_total": order_total,
        "by_status": by_status,
        "top_products": top_products,
        "revenue_by_day": revenue_by_day,
        "low_stock_count": low_stock,
    }


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
