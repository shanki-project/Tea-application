from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.cart import CartItem


def list_for_user(db: Session, user_id: int) -> list[CartItem]:
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(joinedload(CartItem.product))
        .order_by(CartItem.id)
    )
    return list(db.scalars(stmt).all())


def get_item(db: Session, user_id: int, item_id: int) -> CartItem | None:
    return db.scalar(
        select(CartItem).where(CartItem.id == item_id, CartItem.user_id == user_id)
    )


def get_by_product(db: Session, user_id: int, product_id: int) -> CartItem | None:
    return db.scalar(
        select(CartItem).where(
            CartItem.user_id == user_id, CartItem.product_id == product_id
        )
    )


def add(db: Session, user_id: int, product_id: int, quantity: int) -> CartItem:
    existing = get_by_product(db, user_id, product_id)
    if existing:
        existing.quantity += quantity
        db.flush()
        return existing
    item = CartItem(user_id=user_id, product_id=product_id, quantity=quantity)
    db.add(item)
    db.flush()
    return item


def set_quantity(db: Session, item: CartItem, quantity: int) -> CartItem:
    item.quantity = quantity
    db.flush()
    return item


def remove(db: Session, item: CartItem) -> None:
    db.delete(item)
    db.flush()


def clear(db: Session, user_id: int) -> None:
    for item in list_for_user(db, user_id):
        db.delete(item)
    db.flush()
