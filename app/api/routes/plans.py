from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Plan
from app.db.session import get_db
from app.schemas.plan import PlanRead

router = APIRouter(prefix="/plans", tags=["plans"])


@router.get("", response_model=list[PlanRead])
async def list_plans(session: AsyncSession = Depends(get_db)) -> list[Plan]:
    return list((await session.scalars(select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.created_at))).all())

