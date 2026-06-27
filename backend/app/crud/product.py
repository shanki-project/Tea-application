from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.utils import slugify
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate


def get(db: Session, product_id: int) -> Product | None:
    return db.get(Product, product_id)


def get_by_slug(db: Session, slug: str) -> Product | None:
    return db.scalar(select(Product).where(Product.slug == slug))


def _unique_slug(db: Session, base: str) -> str:
    slug = base
    i = 2
    while db.scalar(select(Product.id).where(Product.slug == slug)) is not None:
        slug = f"{base}-{i}"
        i += 1
    return slug


def search(
    db: Session,
    *,
    q: str | None = None,
    category: str | None = None,
    ingredient: str | None = None,
) -> list[Product]:
    stmt = select(Product).order_by(Product.created_at.desc())
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Product.name.ilike(like), Product.description.ilike(like)))
    if category:
        stmt = stmt.where(Product.category == category)
    if ingredient:
        stmt = stmt.where(Product.ingredients.ilike(f"%{ingredient}%"))
    return list(db.scalars(stmt).all())


def create(db: Session, data: ProductCreate, *, admin_id: int | None) -> Product:
    base_slug = slugify(data.slug or data.name)
    product = Product(
        name=data.name,
        slug=_unique_slug(db, base_slug),
        description=data.description,
        ingredients=data.ingredients,
        price=data.price,
        stock_qty=data.stock_qty,
        image_url=data.image_url,
        category=data.category,
        created_by_admin_id=admin_id,
    )
    db.add(product)
    db.flush()
    return product


def update(db: Session, product: Product, data: ProductUpdate) -> Product:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.flush()
    return product


def delete(db: Session, product: Product) -> None:
    db.delete(product)
    db.flush()
