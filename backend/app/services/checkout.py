"""Checkout with a mock/dummy payment flow (no real gateway).

The frontend simulates the "Processing Payment..." delay; the backend performs the
real work: validate stock, generate a fake transaction id, create the order and its
items, decrement stock, and clear the cart — all in one transaction.
"""

import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.crud import cart as cart_crud
from app.models.enums import OrderStatus
from app.models.order import Order, OrderItem


def _fake_transaction_id() -> str:
    return "TXN-" + uuid.uuid4().hex[:16].upper()


def place_order(
    db: Session, *, user_id: int, shipping_address: str, payment_method: str
) -> Order:
    items = cart_crud.list_for_user(db, user_id)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Your cart is empty."
        )

    # Validate stock before charging.
    for item in items:
        product = item.product
        if product is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A product in your cart no longer exists.",
            )
        if item.quantity > product.stock_qty:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient stock for '{product.name}'. "
                f"Only {product.stock_qty} left.",
            )

    total = Decimal("0.00")
    order = Order(
        user_id=user_id,
        total_amount=Decimal("0.00"),
        status=OrderStatus.placed,
        fake_transaction_id=_fake_transaction_id(),
        shipping_address=shipping_address,
    )
    db.add(order)
    db.flush()  # assign order.id

    for item in items:
        product = item.product
        line_total = Decimal(product.price) * item.quantity
        total += line_total
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=item.quantity,
                price_at_purchase=product.price,
            )
        )
        product.stock_qty -= item.quantity  # auto-decrement stock

    order.total_amount = total
    cart_crud.clear(db, user_id)
    db.flush()
    return order
