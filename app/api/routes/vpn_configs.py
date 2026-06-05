from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models import User, VpnConfig
from app.db.session import get_db
from app.schemas.vpn_config import VpnConfigRead
from app.services import vpn_service

router = APIRouter(prefix="/vpn/configs", tags=["vpn"])


@router.get("", response_model=list[VpnConfigRead])
async def list_configs(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> list[VpnConfig]:
    return list((await session.scalars(select(VpnConfig).where(VpnConfig.user_id == user.id).order_by(VpnConfig.created_at.desc()))).all())


@router.post("", response_model=VpnConfigRead)
async def create_config(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> VpnConfig:
    return await vpn_service.create_config(session, user)


@router.get("/{config_id}", response_model=VpnConfigRead)
async def get_config(config_id: UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> VpnConfig:
    return await vpn_service.get_config_for_user(session, config_id, user)


@router.get("/{config_id}/download")
async def download_config(config_id: UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> Response:
    body = await vpn_service.download_config(session, config_id, user)
    return Response(
        content=body,
        media_type="application/x-wireguard-profile",
        headers={"Content-Disposition": f'attachment; filename="ghostgate-{config_id}.conf"'},
    )


@router.post("/{config_id}/revoke", response_model=VpnConfigRead)
async def revoke_config(config_id: UUID, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_db)) -> VpnConfig:
    config = await vpn_service.get_config_for_user(session, config_id, user)
    if config.user_id != user.id:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return await vpn_service.revoke_config(session, config, actor=user)

