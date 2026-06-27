"""Helpers to turn ORM objects into response schemas where extra computed
fields (e.g. is_low_stock) are needed."""

from app.core.config import settings
from app.models.product import Product
from app.schemas.product import ProductRead


def product_read(p: Product) -> ProductRead:
    return ProductRead(
        id=p.id,
        name=p.name,
        slug=p.slug,
        description=p.description,
        ingredients=p.ingredients,
        price=p.price,
        stock_qty=p.stock_qty,
        image_url=p.image_url,
        category=p.category,
        created_by_admin_id=p.created_by_admin_id,
        created_at=p.created_at,
        is_low_stock=p.stock_qty <= settings.LOW_STOCK_THRESHOLD,
    )
