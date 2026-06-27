from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_super_admin
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import AdminCreate, ProfileUpdate, RoleUpdate, UserRead
from app.services.audit import log_action

router = APIRouter()


# ----- Profile (any authenticated user) -----
@router.get("/me", response_model=UserRead)
def get_my_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.patch("/me", response_model=UserRead)
def update_my_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        current_user.name = data["name"]
    if "address" in data:
        current_user.address = data["address"]
    db.commit()
    db.refresh(current_user)
    return current_user


# ----- Super Admin: account management -----
@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db), _: User = Depends(require_super_admin)
):
    return user_crud.list_all(db)


@router.post("/admins", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_admin(
    payload: AdminCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    if user_crud.get_by_email(db, payload.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email already in use.")
    user = user_crud.create(
        db,
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role=payload.role,
    )
    log_action(
        db, admin_id=admin.id, action=f"create_user:{payload.role.value}",
        target_table="users", target_id=user.id,
    )
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/role", response_model=UserRead)
def update_role(
    user_id: int,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot change your own role.")
    target = user_crud.get(db, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    target.role = payload.role
    log_action(
        db, admin_id=admin.id, action=f"set_role:{payload.role.value}",
        target_table="users", target_id=user_id,
    )
    db.commit()
    db.refresh(target)
    return target


@router.patch("/{user_id}/deactivate", response_model=UserRead)
def deactivate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot deactivate yourself.")
    target = user_crud.get(db, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    target.is_active = False
    log_action(
        db, admin_id=admin.id, action="deactivate_user",
        target_table="users", target_id=user_id,
    )
    db.commit()
    db.refresh(target)
    return target


@router.patch("/{user_id}/activate", response_model=UserRead)
def activate_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    target = user_crud.get(db, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    target.is_active = True
    log_action(
        db, admin_id=admin.id, action="activate_user",
        target_table="users", target_id=user_id,
    )
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_super_admin),
):
    if user_id == admin.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete yourself.")
    target = user_crud.get(db, user_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    db.delete(target)
    log_action(
        db, admin_id=admin.id, action="delete_user",
        target_table="users", target_id=user_id,
    )
    db.commit()
