"""Product reviews. Customers may review only products they have purchased,
and may edit/delete only their own reviews (Super Admin may delete any)."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.crud import order as order_crud
from app.crud import product as product_crud
from app.crud import review as review_crud
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.review import ReviewCreate, ReviewRead, ReviewUpdate

router = APIRouter()


def _to_read(review) -> ReviewRead:
    return ReviewRead(
        id=review.id,
        user_id=review.user_id,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
        user_name=review.user.name if review.user else None,
    )


@router.get("/products/{product_id}/reviews", response_model=list[ReviewRead])
def list_reviews(product_id: int, db: Session = Depends(get_db)):
    return [_to_read(r) for r in review_crud.list_for_product(db, product_id)]


@router.post(
    "/products/{product_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
)
def create_review(
    product_id: int,
    payload: ReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.customer:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Only customers can review.")
    if not product_crud.get(db, product_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found.")
    if not order_crud.has_purchased(db, current_user.id, product_id):
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "You can only review products you have purchased.",
        )
    if review_crud.get_user_review(db, current_user.id, product_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "You already reviewed this product. Edit your existing review instead.",
        )
    review = review_crud.create(
        db,
        user_id=current_user.id,
        product_id=product_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    db.commit()
    db.refresh(review)
    return _to_read(review)


@router.put("/reviews/{review_id}", response_model=ReviewRead)
def update_review(
    review_id: int,
    payload: ReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = review_crud.get(db, review_id)
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found.")
    if review.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own review.")
    data = payload.model_dump(exclude_unset=True)
    if "rating" in data and data["rating"] is not None:
        review.rating = data["rating"]
    if "comment" in data:
        review.comment = data["comment"]
    db.commit()
    db.refresh(review)
    return _to_read(review)


@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    review = review_crud.get(db, review_id)
    if not review:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Review not found.")
    if review.user_id != current_user.id and current_user.role != UserRole.super_admin:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Not allowed.")
    review_crud.delete(db, review)
    db.commit()
