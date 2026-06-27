"""Shared FastAPI dependencies: DB session, current user, and RBAC guards."""

from collections.abc import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.crud import user as user_crud
from app.models.enums import UserRole
from app.models.user import User

# tokenUrl is informational (Swagger "Authorize"); login also accepts JSON.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    if not token:
        raise CREDENTIALS_EXC
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise CREDENTIALS_EXC
    sub = payload.get("sub")
    if sub is None:
        raise CREDENTIALS_EXC
    user = user_crud.get(db, int(sub))
    if user is None or not user.is_active:
        raise CREDENTIALS_EXC
    return user


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    """Dependency factory: allow only the given roles."""

    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )
        return current_user

    return checker


# Convenience guards
require_super_admin = require_roles(UserRole.super_admin)
require_admin = require_roles(UserRole.super_admin, UserRole.admin)  # Admin/Staff+
require_customer = require_roles(UserRole.customer)

__all__ = [
    "get_db",
    "get_current_user",
    "require_roles",
    "require_super_admin",
    "require_admin",
    "require_customer",
]
