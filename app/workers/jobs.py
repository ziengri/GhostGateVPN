from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy import select

from app.db.models import Subscription, SubscriptionStatus, VpnConfig, VpnConfigStatus
from app.db.session import AsyncSessionLocal
from app.services.awg_service import AwgError, AwgService
from app.services.vpn_service import log_config_event, now_utc, revoke_config

logger = logging.getLogger(__name__)


async def revoke_expired_configs() -> None:
    async with AsyncSessionLocal() as session:
        configs = (
            await session.scalars(select(VpnConfig).where(VpnConfig.status == VpnConfigStatus.active, VpnConfig.expires_at <= now_utc()).limit(100))
        ).all()
        for config in configs:
            try:
                await revoke_config(session, config, expired=True, awg_service=AwgService())
            except Exception:
                logger.exception("Expired config revoke job failed for config_id=%s", config.id)
                continue


async def retry_pending_revoke() -> None:
    async with AsyncSessionLocal() as session:
        configs = (await session.scalars(select(VpnConfig).where(VpnConfig.status == VpnConfigStatus.pending_revoke).limit(100))).all()
        awg = AwgService()
        for config in configs:
            try:
                await awg.revoke_client(config.awg_client_id)
            except AwgError as exc:
                logger.warning("Pending revoke retry failed for config_id=%s", config.id)
                await log_config_event(session, config, config.user_id, "revoke_failed", str(exc), {"error": str(exc)})
                await session.commit()
                continue
            config.status = VpnConfigStatus.expired if config.expires_at <= datetime.now(UTC) else VpnConfigStatus.revoked
            config.revoked_at = now_utc()
            await log_config_event(session, config, config.user_id, "expired" if config.status == VpnConfigStatus.expired else "revoked")
            await session.commit()


async def expire_subscriptions() -> None:
    async with AsyncSessionLocal() as session:
        subscriptions = (
            await session.scalars(
                select(Subscription)
                .where(Subscription.status.in_([SubscriptionStatus.active, SubscriptionStatus.trial]), Subscription.expires_at <= now_utc())
                .limit(100)
            )
        ).all()
        for subscription in subscriptions:
            subscription.status = SubscriptionStatus.expired
            configs = (
                await session.scalars(
                    select(VpnConfig).where(VpnConfig.subscription_id == subscription.id, VpnConfig.status == VpnConfigStatus.active)
                )
            ).all()
            for config in configs:
                config.status = VpnConfigStatus.pending_revoke
                await log_config_event(session, config, config.user_id, "subscription_expired")
            await session.commit()
