from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt

from app.core.config import settings


def create_access_token(user_id: UUID, role: str, expires_delta: timedelta | None = None) -> str:
    expires = datetime.now(UTC) + (expires_delta or timedelta(minutes=settings.jwt_access_token_expire_minutes))
    payload = {"sub": str(user_id), "role": role, "type": "access", "exp": expires}
    return jwt.encode(payload, settings.app_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(token, settings.app_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid access token") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise ValueError("Invalid access token")
    return payload

