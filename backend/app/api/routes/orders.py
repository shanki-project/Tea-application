from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_admin, require_customer
from app.crud import order as order_crud
from app.models.enums import ORDER_STATUS_FLOW, OrderStatus, UserRole
from app.models.order import Order
from app.models.user import User
from app.schemas.order import (
    CheckoutRequest,
    CheckoutResult,
    OrderRead,
    OrderStatusUpdate,
)
from app.services.audit import log_action
from app.services.checkout import place_order

router = APIRouter()


def _to_read(order: Order) -> OrderRead:
    return OrderRead(
        id=order.id,
        user_id=order.user_id,
        total_amount=order.total_amount,
        status=order.status,
        fake_transaction_id=order.fake_transaction_id,
        shipping_address=order.shipping_address,
        created_at=order.created_at,
        customer_name=order.user.name if order.user else None,
        customer_email=order.user.email if order.user else None,
        items=[
            {
                "id": i.id,
                "product_id": i.product_id,
                "quantity": i.quantity,
                "price_at_purchase": i.price_at_purchase,
                "product_name": i.product.name if i.product else None,
            }
            for i in order.items
        ],
    )


def _restock(order: Order) -> None:
    """Return items to inventory (used when an order is cancelled)."""
    for item in order.items:
        if item.product is not None:
            item.product.stock_qty += item.quantity


@router.post("/checkout", response_model=CheckoutResult, status_code=status.HTTP_201_CREATED)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
):
    """Dummy-payment checkout: builds an order from the cart and decrements stock."""
    order = place_order(
        db,
        user_id=user.id,
        shipping_address=payload.shipping_address,
        payment_method=payload.payment_method,
    )
    db.commit()
    db.refresh(order)
    return CheckoutResult(
        order=_to_read(order),
        fake_transaction_id=order.fake_transaction_id,
    )


@router.get("", response_model=list[OrderRead])
def my_orders(db: Session = Depends(get_db), user: User = Depends(require_customer)):
    return [_to_read(o) for o in order_crud.list_for_user(db, user.id)]


@router.get("/{order_id}", response_model=OrderRead)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    order = order_crud.get(db, order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    is_staff = user.role in (UserRole.admin, UserRole.super_admin)
    if order.user_id != user.id and not is_staff:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed.")
    return _to_read(order)


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Admin/Staff move an order through Placed → Packed → Shipped → Delivered."""
    order = order_crud.get(db, order_id)
    if not order:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    allowed = ORDER_STATUS_FLOW.get(order.status, [])
    if payload.status != order.status and payload.status not in allowed:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Cannot move order from {order.status.value} to {payload.status.value}.",
        )
    if payload.status == OrderStatus.cancelled and order.status != OrderStatus.cancelled:
        _restock(order)
    order.status = payload.status
    log_action(
        db, admin_id=admin.id, action=f"order_status:{payload.status.value}",
        target_table="orders", target_id=order.id,
    )
    db.commit()
    db.refresh(order)
    return _to_read(order)


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_my_order(
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_customer),
):
    """A customer cancels their own order while it is still Placed or Packed.
    Cancelled orders return their items to stock."""
    order = order_crud.get(db, order_id)
    if not order or order.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found.")
    if order.status not in (OrderStatus.placed, OrderStatus.packed):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"An order that is {order.status.value} can no longer be cancelled.",
        )
    _restock(order)
    order.status = OrderStatus.cancelled
    db.commit()
    db.refresh(order)
    return _to_read(order)
