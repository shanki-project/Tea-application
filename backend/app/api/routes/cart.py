"""Cart endpoints — Customers only, persisted per user in the DB."""

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_customer
from app.api.serializers import product_read
from app.crud import cart as cart_crud
from app.crud import product as product_crud
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartRead

router = APIRouter()


def _build_cart(db: Session, user_id: int) -> CartRead:
    items = cart_crud.list_for_user(db, user_id)
    out = []
    total = Decimal("0.00")
    count = 0
    for it in items:
        line = Decimal(it.product.price) * it.quantity
        total += line
        count += it.quantity
        out.append(
            {
                "id": it.id,
                "product_id": it.product_id,
                "quantity": it.quantity,
                "product": product_read(it.product),
                "line_total": line,
            }
        )
    return CartRead(items=out, total=total, item_count=count)


@router.get("", response_model=CartRead)
def get_cart(db: Session = Depends(get_db), user: User = Depends(require_customer)):
    return _build_cart(db, user.id)


@router.post("/items", response_model=CartRead, status_code=status.HTTP_201_CREATED)
def add_item(
    payload: CartItemAdd,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
):
    product = product_crud.get(db, payload.product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    if payload.quantity > product.stock_qty:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Only {product.stock_qty} in stock."
        )
    cart_crud.add(db, user.id, payload.product_id, payload.quantity)
    db.commit()
    return _build_cart(db, user.id)


@router.patch("/items/{item_id}", response_model=CartRead)
def update_item(
    item_id: int,
    payload: CartItemUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
):
    item = cart_crud.get_item(db, user.id, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cart item not found.")
    if payload.quantity > item.product.stock_qty:
        raise HTTPException(
            status.HTTP_409_CONFLICT, f"Only {item.product.stock_qty} in stock."
        )
    cart_crud.set_quantity(db, item, payload.quantity)
    db.commit()
    return _build_cart(db, user.id)


@router.delete("/items/{item_id}", response_model=CartRead)
def remove_item(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
):
    item = cart_crud.get_item(db, user.id, item_id)
    if not item:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cart item not found.")
    cart_crud.remove(db, item)
    db.commit()
    return _build_cart(db, user.id)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(db: Session = Depends(get_db), user: User = Depends(require_customer)):
    cart_crud.clear(db, user.id)
    db.commit()
