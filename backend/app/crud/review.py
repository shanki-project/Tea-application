from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.review import Review


def list_for_product(db: Session, product_id: int) -> list[Review]:
    stmt = (
        select(Review)
        .where(Review.product_id == product_id)
        .options(joinedload(Review.user))
        .order_by(Review.created_at.desc())
    )
    return list(db.scalars(stmt).all())


def get(db: Session, review_id: int) -> Review | None:
    return db.get(Review, review_id)


def get_user_review(db: Session, user_id: int, product_id: int) -> Review | None:
    return db.scalar(
        select(Review).where(
            Review.user_id == user_id, Review.product_id == product_id
        )
    )


def create(
    db: Session, *, user_id: int, product_id: int, rating: int, comment: str | None
) -> Review:
    review = Review(
        user_id=user_id, product_id=product_id, rating=rating, comment=comment
    )
    db.add(review)
    db.flush()
    return review


def delete(db: Session, review: Review) -> None:
    db.delete(review)
    db.flush()
