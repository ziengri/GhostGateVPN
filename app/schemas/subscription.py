from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.subscription import SubscriptionStatus


class SubscriptionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    plan_id: UUID
    status: SubscriptionStatus
    starts_at: datetime
    expires_at: datetime
    created_at: datetime


class AdminSubscriptionPatch(BaseModel):
    status: SubscriptionStatus | None = None
    expires_at: datetime | None = None

