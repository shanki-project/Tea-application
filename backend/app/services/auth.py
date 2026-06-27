"""Authentication service: credential checks and signup."""

from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.crud import user as user_crud
from app.models.enums import UserRole
from app.models.user import User


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = user_crud.get_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def signup_customer(db: Session, *, name: str, email: str, password: str) -> User:
    return user_crud.create(
        db, name=name, email=email, password=password, role=UserRole.customer
    )
