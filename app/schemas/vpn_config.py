from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.db.models.vpn_config import VpnConfigStatus


class VpnConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    subscription_id: UUID | None
    awg_client_id: str
    status: VpnConfigStatus
    starts_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    created_at: datetime
    last_sync_at: datetime | None

