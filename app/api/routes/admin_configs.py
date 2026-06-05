from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_user, get_staff_user
from app.db.models import User, VpnConfig
from app.db.session import get_db
from app.schemas.vpn_config import VpnConfigRead
from app.services.vpn_service import revoke_config

router = APIRouter(prefix="/admin/configs", tags=["admin-configs"])


@router.get("", response_model=list[VpnConfigRead])
async def list_configs(_: User = Depends(get_staff_user), session: AsyncSession = Depends(get_db)) -> list[VpnConfig]:
    return list((await session.scalars(select(VpnConfig).order_by(VpnConfig.created_at.desc()).limit(100))).all())


@router.get("/{config_id}", response_model=VpnConfigRead)
async def get_config(config_id: UUID, _: User = Depends(get_staff_user), session: AsyncSession = Depends(get_db)) -> VpnConfig:
    config = await session.get(VpnConfig, config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="config not found")
    return config


@router.post("/{config_id}/revoke", response_model=VpnConfigRead)
async def admin_revoke_config(config_id: UUID, admin: User = Depends(get_admin_user), session: AsyncSession = Depends(get_db)) -> VpnConfig:
    config = await session.get(VpnConfig, config_id)
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="config not found")
    return await revoke_config(session, config, actor=admin)

