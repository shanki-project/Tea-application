from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    description: str | None = None
    ingredients: str | None = None
    price: Decimal = Field(ge=0)
    stock_qty: int = Field(ge=0, default=0)
    image_url: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=80)


class ProductCreate(ProductBase):
    slug: str | None = Field(default=None, max_length=180)  # auto-generated if omitted


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    ingredients: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    stock_qty: int | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    category: str | None = Field(default=None, max_length=80)


class StockUpdate(BaseModel):
    stock_qty: int = Field(ge=0)


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    created_by_admin_id: int | None = None
    created_at: datetime
    is_low_stock: bool = False
