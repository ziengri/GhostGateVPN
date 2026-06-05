from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.schemas.subscription import SubscriptionRead
from app.services.vpn_service import get_active_subscription

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.get("/current", response_model=SubscriptionRead)
async def current_subscription(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)):
    subscription = await get_active_subscription(session, user.id)
    if not subscription:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="subscription not found")
    return subscription

