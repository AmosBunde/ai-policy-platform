"""User management routes."""
import uuid as uuid_mod

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.orm import User
from shared.models.schemas import UserResponse, UserRole
from shared.utils.database import get_db
from src.middleware.auth import get_current_user, require_role

router = APIRouter()


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, max_length=255)
    organization: str | None = Field(None, max_length=255)
    role: UserRole | None = None
    is_active: bool | None = None


def _user_to_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization=user.organization,
        is_active=user.is_active,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user profile."""
    return _user_to_response(current_user)


@router.get("/", response_model=list[UserResponse])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: User = require_role(["admin"]),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)."""
    offset = (max(1, min(page, 1000)) - 1) * min(max(page_size, 1), 100)
    limit = min(max(page_size, 1), 100)
    result = await db.execute(
        select(User).offset(offset).limit(limit).order_by(User.created_at.desc())
    )
    users = result.scalars().all()
    return [_user_to_response(u) for u in users]


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update user (admin only, or self for own profile)."""
    try:
        target_id = uuid_mod.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

    # Non-admin users can only update themselves
    is_self = current_user.id == target_id
    is_admin = current_user.role == "admin"

    if not is_admin and not is_self:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    result = await db.execute(select(User).where(User.id == target_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Prevent privilege escalation: non-admins cannot change roles
    if update.role is not None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change user roles",
        )

    # Prevent non-admins from changing is_active
    if update.is_active is not None and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can change active status",
        )

    if update.full_name is not None:
        user.full_name = update.full_name
    if update.organization is not None:
        user.organization = update.organization
    if update.role is not None and is_admin:
        user.role = update.role.value if hasattr(update.role, "value") else update.role
    if update.is_active is not None and is_admin:
        user.is_active = update.is_active

    await db.flush()
    await db.refresh(user)

    return _user_to_response(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    current_user: User = require_role(["admin"]),
    db: AsyncSession = Depends(get_db),
):
    """Soft-delete user (admin only, cannot delete self)."""
    try:
        target_id = uuid_mod.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")

    if current_user.id == target_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    result = await db.execute(select(User).where(User.id == target_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = False
    await db.flush()
