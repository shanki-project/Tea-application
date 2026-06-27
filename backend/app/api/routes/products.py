from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_admin
from app.api.serializers import product_read
from app.crud import product as product_crud
from app.models.user import User
from app.schemas.product import (
    ProductCreate,
    ProductRead,
    ProductUpdate,
    StockUpdate,
)
from app.services.audit import log_action

router = APIRouter()


# ----- Public -----
@router.get("", response_model=list[ProductRead])
def list_products(
    q: str | None = Query(default=None, description="Search name/description"),
    category: str | None = None,
    ingredient: str | None = None,
    db: Session = Depends(get_db),
):
    products = product_crud.search(db, q=q, category=category, ingredient=ingredient)
    return [product_read(p) for p in products]


@router.get("/{slug}", response_model=ProductRead)
def get_product(slug: str, db: Session = Depends(get_db)):
    product = product_crud.get_by_slug(db, slug)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    return product_read(product)


# ----- Admin / Staff -----
@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = product_crud.create(db, payload, admin_id=admin.id)
    log_action(
        db, admin_id=admin.id, action="create_product",
        target_table="products", target_id=product.id,
    )
    db.commit()
    return product_read(product)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = product_crud.get(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    product = product_crud.update(db, product, payload)
    log_action(
        db, admin_id=admin.id, action="update_product",
        target_table="products", target_id=product.id,
    )
    db.commit()
    return product_read(product)


@router.patch("/{product_id}/stock", response_model=ProductRead)
def update_stock(
    product_id: int,
    payload: StockUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = product_crud.get(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    product.stock_qty = payload.stock_qty
    log_action(
        db, admin_id=admin.id, action="update_stock",
        target_table="products", target_id=product.id,
    )
    db.commit()
    return product_read(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    product = product_crud.get(db, product_id)
    if not product:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    product_crud.delete(db, product)
    log_action(
        db, admin_id=admin.id, action="delete_product",
        target_table="products", target_id=product_id,
    )
    db.commit()
