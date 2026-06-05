from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlanRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    duration_days: int
    max_configs: int
    price_amount: int
    currency: str
    is_active: bool
    created_at: datetime

