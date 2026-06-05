from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_staff_user
from app.db.models import Subscription, User, VpnConfig, VpnConfigStatus
from app.db.session import get_db
from app.schemas.subscription import AdminSubscriptionPatch, SubscriptionRead
from app.services.vpn_service import log_config_event, now_utc

router = APIRouter(prefix="/admin/subscriptions", tags=["admin-subscriptions"])


@router.get("", response_model=list[SubscriptionRead])
async def list_subscriptions(_: User = Depends(get_staff_user), session: AsyncSession = Depends(get_db)) -> list[Subscription]:
    return list((await session.scalars(select(Subscription).order_by(Subscription.created_at.desc()).limit(100))).all())


@router.patch("/{subscription_id}", response_model=SubscriptionRead)
async def patch_subscription(
    subscription_id: UUID,
    payload: AdminSubscriptionPatch,
    _: User = Depends(get_admin_user),
    session: AsyncSession = Depends(get_db),
) -> Subscription:
    subscription = await session.get(Subscription, subscription_id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(subscription, key, value)
    if payload.expires_at and payload.expires_at <= now_utc():
        configs = (
            await session.scalars(select(VpnConfig).where(VpnConfig.subscription_id == subscription.id, VpnConfig.status == VpnConfigStatus.active))
        ).all()
        for config in configs:
            config.status = VpnConfigStatus.pending_revoke
            await log_config_event(session, config, config.user_id, "subscription_expired")
    await session.commit()
    await session.refresh(subscription)
    return subscription

