from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import (
    EmailVerifyRequest,
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirm,
    PasswordResetRequest,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.services import auth_service
from app.services.email_service import EmailService

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, request: Request, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.register(session, payload.email, payload.phone_number, payload.password, request)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.login(session, payload.email, payload.password, request)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, request: Request, session: AsyncSession = Depends(get_db)) -> TokenResponse:
    return await auth_service.refresh(session, payload.refresh_token, request)


@router.post("/logout", response_model=MessageResponse)
async def logout(payload: LogoutRequest, session: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.logout(session, payload.refresh_token)
    return MessageResponse(message="logged out")


@router.post("/email/verify", response_model=MessageResponse)
async def verify_email(payload: EmailVerifyRequest, session: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.verify_email(session, payload.token)
    return MessageResponse(message="email verified")


@router.get("/email/verify", response_model=MessageResponse)
async def verify_email_link(token: str, session: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.verify_email(session, token)
    return MessageResponse(message="email verified")


@router.post("/password-reset/request", response_model=MessageResponse)
async def request_password_reset(payload: PasswordResetRequest, session: AsyncSession = Depends(get_db)) -> MessageResponse:
    user, token = await auth_service.create_password_reset_token(session, payload.email)
    if user and token:
        try:
            await EmailService().send_password_reset_email(user.email, token)
        except Exception:
            logger.exception("Password reset email delivery failed")
    return MessageResponse(message="password reset requested")


@router.post("/password-reset/confirm", response_model=MessageResponse)
async def confirm_password_reset(payload: PasswordResetConfirm, session: AsyncSession = Depends(get_db)) -> MessageResponse:
    await auth_service.reset_password(session, payload.token, payload.password)
    return MessageResponse(message="password reset complete")
