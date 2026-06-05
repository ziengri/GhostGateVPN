from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_staff_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.user import AdminUserPatch, UserRead

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


@router.get("", response_model=list[UserRead])
async def list_users(_: User = Depends(get_staff_user), session: AsyncSession = Depends(get_db)) -> list[User]:
    return list((await session.scalars(select(User).order_by(User.created_at.desc()).limit(100))).all())


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: UUID, _: User = Depends(get_staff_user), session: AsyncSession = Depends(get_db)) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
async def patch_user(user_id: UUID, payload: AdminUserPatch, _: User = Depends(get_admin_user), session: AsyncSession = Depends(get_db)) -> User:
    user = await session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(user, key, value)
    await session.commit()
    await session.refresh(user)
    return user

