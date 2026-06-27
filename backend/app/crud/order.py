from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order, OrderItem


def _with_items(stmt):
    return stmt.options(selectinload(Order.items).joinedload(OrderItem.product))


def get(db: Session, order_id: int) -> Order | None:
    return db.scalar(_with_items(select(Order).where(Order.id == order_id)))


def list_for_user(db: Session, user_id: int) -> list[Order]:
    stmt = _with_items(
        select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc())
    )
    return list(db.scalars(stmt).unique().all())


def list_all(db: Session) -> list[Order]:
    stmt = _with_items(select(Order).order_by(Order.created_at.desc()))
    return list(db.scalars(stmt).unique().all())


def has_purchased(db: Session, user_id: int, product_id: int) -> bool:
    """True if the user has an order that contains this product."""
    stmt = (
        select(OrderItem.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.user_id == user_id, OrderItem.product_id == product_id)
        .limit(1)
    )
    return db.scalar(stmt) is not None
