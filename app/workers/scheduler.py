from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import settings
from app.workers.jobs import expire_subscriptions, retry_pending_revoke, revoke_expired_configs

scheduler = AsyncIOScheduler(timezone="UTC")


def start_scheduler() -> None:
    if not settings.scheduler_enabled or scheduler.running:
        return
    scheduler.add_job(revoke_expired_configs, "interval", minutes=2, id="revoke_expired_configs", replace_existing=True)
    scheduler.add_job(retry_pending_revoke, "interval", minutes=2, id="retry_pending_revoke", replace_existing=True)
    scheduler.add_job(expire_subscriptions, "interval", minutes=10, id="expire_subscriptions", replace_existing=True)
    scheduler.start()


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)

