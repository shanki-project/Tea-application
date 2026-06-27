from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrderStatus


class CheckoutRequest(BaseModel):
    shipping_address: str = Field(min_length=5)
    payment_method: str = Field(default="card", max_length=40)


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    price_at_purchase: Decimal
    product_name: str | None = None


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    total_amount: Decimal
    status: OrderStatus
    fake_transaction_id: str | None = None
    shipping_address: str | None = None
    created_at: datetime
    items: list[OrderItemRead] = []
    customer_name: str | None = None
    customer_email: str | None = None


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class CheckoutResult(BaseModel):
    """Returned by the dummy-payment checkout endpoint."""

    order: OrderRead
    payment_status: str = "successful"
    fake_transaction_id: str
    message: str = "Payment successful. Your order has been placed."
