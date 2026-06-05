from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.jwt import create_access_token
from app.core.security import hash_password, hash_token, new_opaque_token, verify_password
from app.db.models import EmailVerificationToken, PasswordResetToken, Plan, RefreshToken, Subscription, SubscriptionStatus, User, UserRole
from app.schemas.auth import TokenResponse
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


async def _create_refresh_token(session: AsyncSession, user: User, request: Request | None = None) -> str:
    token = new_opaque_token()
    item = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=datetime.now(UTC) + timedelta(days=settings.jwt_refresh_token_expire_days),
        user_agent=request.headers.get("user-agent") if request else None,
        ip_address=request.client.host if request and request.client else None,
    )
    session.add(item)
    return token


async def _token_response(session: AsyncSession, user: User, request: Request | None = None) -> TokenResponse:
    refresh_token = await _create_refresh_token(session, user, request)
    access_token = create_access_token(user.id, user.role.value)
    await session.flush()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, user=user)


async def register(session: AsyncSession, email: str, phone_number: str, password: str, request: Request) -> TokenResponse:
    email = _normalize_email(email)
    existing = await session.scalar(select(User).where(User.email == email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")
    plan = await session.scalar(select(Plan).where(Plan.code == "trial", Plan.is_active.is_(True)))
    if not plan:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="trial plan is not configured")
    user = User(email=email, phone_number=phone_number, password_hash=hash_password(password), role=UserRole.user)
    session.add(user)
    await session.flush()
    now = datetime.now(UTC)
    session.add(Subscription(user_id=user.id, plan_id=plan.id, status=SubscriptionStatus.trial, starts_at=now, expires_at=now + timedelta(days=plan.duration_days)))
    response = await _token_response(session, user, request)
    verify_token = new_opaque_token()
    session.add(EmailVerificationToken(user_id=user.id, token_hash=hash_token(verify_token), expires_at=now + timedelta(hours=24)))
    await session.commit()
    try:
        email_service = EmailService()
        await email_service.send_verify_email(user.email, verify_token)
        await email_service.send_trial_started_email(user.email)
    except Exception:
        logger.exception("Registration email delivery failed")
    return response


async def login(session: AsyncSession, email: str, password: str, request: Request) -> TokenResponse:
    user = await session.scalar(select(User).where(User.email == _normalize_email(email)))
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user blocked")
    user.last_login_at = datetime.now(UTC)
    response = await _token_response(session, user, request)
    await session.commit()
    return response


async def refresh(session: AsyncSession, refresh_token: str, request: Request) -> TokenResponse:
    now = datetime.now(UTC)
    item = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    if not item or item.revoked_at or item.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid refresh token")
    user = await session.get(User, item.user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="user blocked")
    item.revoked_at = now
    response = await _token_response(session, user, request)
    await session.commit()
    return response


async def logout(session: AsyncSession, refresh_token: str) -> None:
    item = await session.scalar(select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token)))
    if item and not item.revoked_at:
        item.revoked_at = datetime.now(UTC)
        await session.commit()


async def create_email_verification_token(session: AsyncSession, user: User) -> str:
    token = new_opaque_token()
    session.add(EmailVerificationToken(user_id=user.id, token_hash=hash_token(token), expires_at=datetime.now(UTC) + timedelta(hours=24)))
    await session.commit()
    return token


async def verify_email(session: AsyncSession, token: str) -> None:
    now = datetime.now(UTC)
    item = await session.scalar(select(EmailVerificationToken).where(EmailVerificationToken.token_hash == hash_token(token)))
    if not item or item.used_at or item.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid verification token")
    user = await session.get(User, item.user_id)
    if user:
        user.is_email_verified = True
    item.used_at = now
    await session.commit()


async def create_password_reset_token(session: AsyncSession, email: str) -> tuple[User | None, str | None]:
    user = await session.scalar(select(User).where(User.email == _normalize_email(email)))
    if not user:
        return None, None
    token = new_opaque_token()
    session.add(PasswordResetToken(user_id=user.id, token_hash=hash_token(token), expires_at=datetime.now(UTC) + timedelta(hours=1)))
    await session.commit()
    return user, token


async def reset_password(session: AsyncSession, token: str, password: str) -> None:
    now = datetime.now(UTC)
    item = await session.scalar(select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(token)))
    if not item or item.used_at or item.expires_at <= now:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid reset token")
    user = await session.get(User, item.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid reset token")
    user.password_hash = hash_password(password)
    item.used_at = now
    await session.commit()
