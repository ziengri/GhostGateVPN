from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan, Subscription, SubscriptionStatus, User, UserRole, VpnConfig, VpnConfigEvent, VpnConfigStatus
from app.services.awg_service import AwgError, AwgService


def now_utc() -> datetime:
    return datetime.now(UTC)


async def log_config_event(
    session: AsyncSession,
    config: VpnConfig | None,
    user_id: uuid.UUID | None,
    event_type: str,
    message: str | None = None,
    metadata: dict | None = None,
) -> None:
    session.add(VpnConfigEvent(config_id=config.id if config else None, user_id=user_id, event_type=event_type, message=message, event_metadata=metadata))


def can_read_config(user: User, config: VpnConfig) -> bool:
    return user.role in {UserRole.admin, UserRole.support} or config.user_id == user.id


async def get_active_subscription(session: AsyncSession, user_id: uuid.UUID) -> Subscription | None:
    return await session.scalar(
        select(Subscription)
        .where(Subscription.user_id == user_id, Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.trial]))
        .order_by(Subscription.expires_at.desc())
    )


async def create_config(session: AsyncSession, user: User, awg_service: AwgService | None = None) -> VpnConfig:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user blocked")
    subscription = await get_active_subscription(session, user.id)
    if not subscription or subscription.expires_at <= now_utc():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="subscription expired")
    plan = await session.get(Plan, subscription.plan_id)
    if not plan:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="subscription plan is missing")
    active_count = await session.scalar(
        select(func.count(VpnConfig.id)).where(VpnConfig.user_id == user.id, VpnConfig.status == VpnConfigStatus.active)
    )
    if int(active_count or 0) >= plan.max_configs:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="config limit exceeded")

    awg_client_id = str(uuid.uuid4())
    awg_service = awg_service or AwgService()
    try:
        await awg_service.create_client(awg_client_id)
    except AwgError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="awg-server unavailable") from exc
    config = VpnConfig(
        user_id=user.id,
        subscription_id=subscription.id,
        awg_client_id=awg_client_id,
        status=VpnConfigStatus.active,
        starts_at=now_utc(),
        expires_at=subscription.expires_at,
        last_sync_at=now_utc(),
    )
    session.add(config)
    await session.flush()
    await log_config_event(session, config, user.id, "created")
    await log_config_event(session, config, user.id, "awg_created")
    await session.commit()
    await session.refresh(config)
    return config


async def get_config_for_user(session: AsyncSession, config_id: uuid.UUID, user: User) -> VpnConfig:
    config = await session.get(VpnConfig, config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="config not found")
    if not can_read_config(user, config):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return config


async def download_config(session: AsyncSession, config_id: uuid.UUID, user: User, awg_service: AwgService | None = None) -> str:
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user blocked")
    config = await get_config_for_user(session, config_id, user)
    if config.status != VpnConfigStatus.active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="config not active")
    if config.expires_at <= now_utc():
        config.status = VpnConfigStatus.pending_revoke
        await log_config_event(session, config, config.user_id, "pending_revoke", "download rejected because config is expired")
        await session.commit()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="config expired")
    awg_service = awg_service or AwgService()
    try:
        body = await awg_service.get_configuration(config.awg_client_id)
    except AwgError as exc:
        await log_config_event(session, config, config.user_id, "sync_failed", str(exc))
        await session.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="awg-server unavailable") from exc
    await log_config_event(session, config, config.user_id, "downloaded")
    await session.commit()
    return body


async def revoke_config(
    session: AsyncSession,
    config: VpnConfig,
    actor: User | None = None,
    *,
    expired: bool = False,
    awg_service: AwgService | None = None,
) -> VpnConfig:
    if config.status in {VpnConfigStatus.revoked, VpnConfigStatus.expired}:
        return config
    config.status = VpnConfigStatus.pending_revoke
    await log_config_event(session, config, config.user_id, "pending_revoke")
    await session.flush()
    awg_service = awg_service or AwgService()
    try:
        await awg_service.revoke_client(config.awg_client_id)
    except AwgError as exc:
        await log_config_event(session, config, config.user_id, "revoke_failed", str(exc), {"error": str(exc), "actor_id": str(actor.id) if actor else None})
        await session.commit()
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="awg-server unavailable") from exc
    config.status = VpnConfigStatus.expired if expired or config.expires_at <= now_utc() else VpnConfigStatus.revoked
    config.revoked_at = now_utc()
    config.last_sync_at = now_utc()
    await log_config_event(session, config, config.user_id, "expired" if config.status == VpnConfigStatus.expired else "revoked")
    await session.commit()
    await session.refresh(config)
    return config

