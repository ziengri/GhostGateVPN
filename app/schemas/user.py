from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.db.models.user import UserRole


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    role: UserRole
    tgid: int | None
    is_active: bool
    is_email_verified: bool
    created_at: datetime


class AdminUserPatch(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None
    tgid: int | None = None

