from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UuidPkMixin


class VpnConfigStatus(str, enum.Enum):
    active = "active"
    pending_revoke = "pending_revoke"
    expired = "expired"
    revoked = "revoked"
    failed = "failed"


class VpnConfig(UuidPkMixin, TimestampMixin, Base):
    __tablename__ = "vpn_configs"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("subscriptions.id", ondelete="SET NULL"), index=True, nullable=True
    )
    awg_client_id: Mapped[str] = mapped_column(Text, unique=True, index=True, nullable=False)
    status: Mapped[VpnConfigStatus] = mapped_column(
        Enum(VpnConfigStatus, name="vpn_config_status"), default=VpnConfigStatus.active, index=True, nullable=False
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="vpn_configs")
    subscription = relationship("Subscription", back_populates="vpn_configs")
    events = relationship("VpnConfigEvent", back_populates="config")

