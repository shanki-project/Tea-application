from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.product import ProductRead


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(ge=1, default=1)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=1)


class CartItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    product: ProductRead
    line_total: Decimal = Decimal("0.00")


class CartRead(BaseModel):
    items: list[CartItemRead]
    total: Decimal
    item_count: int
