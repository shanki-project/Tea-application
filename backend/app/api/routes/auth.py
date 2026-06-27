from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_token,
    hash_password,
)
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    SignupRequest,
    Token,
)
from app.schemas.user import UserRead
from app.services import auth as auth_service

router = APIRouter()


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    user = auth_service.signup_customer(
        db, name=payload.name, email=payload.email, password=payload.password
    )
    db.commit()
    return Token(access_token=create_access_token(user.id, {"role": user.role.value}))


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = auth_service.authenticate(db, payload.email, payload.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    return Token(access_token=create_access_token(user.id, {"role": user.role.value}))


@router.get("/me", response_model=UserRead)
def me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/password-reset/request")
def password_reset_request(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """Issue a reset token.

    With no email service configured, the token is returned directly so the flow
    is testable end-to-end. In production this would be emailed, not returned.
    """
    user = user_crud.get_by_email(db, payload.email)
    if not user:
        # Don't reveal whether the email exists.
        return {"message": "If that email exists, a reset link has been sent."}
    token = create_password_reset_token(user.id)
    return {
        "message": "Password reset token generated.",
        "reset_token": token,
    }


@router.post("/password-reset/confirm")
def password_reset_confirm(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    data = decode_token(payload.token)
    if not data or data.get("type") != "reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )
    user = user_crud.get(db, int(data["sub"]))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found."
        )
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated. You can now log in."}
