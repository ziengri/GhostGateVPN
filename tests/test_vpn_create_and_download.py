import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.models import User, UserRole, VpnConfig, VpnConfigStatus
from app.db.session import get_db
from app.main import app
from app.services import vpn_service


class DummySession:
    pass


@pytest.mark.asyncio
async def test_create_and_download_reuses_existing_active_config(monkeypatch: pytest.MonkeyPatch) -> None:
    user = User(id=uuid.uuid4(), email="user@example.com", password_hash="x", role=UserRole.user, is_active=True)
    config = VpnConfig(
        id=uuid.uuid4(),
        user_id=user.id,
        awg_client_id="awg-existing",
        status=VpnConfigStatus.active,
        starts_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    async def fake_get_reusable_active_config(session: DummySession, user_id: uuid.UUID) -> VpnConfig:
        assert user_id == user.id
        return config

    async def fake_create_config(*args, **kwargs) -> VpnConfig:
        raise AssertionError("create_config should not be called when an active config exists")

    async def fake_download_config_body(session: DummySession, existing_config: VpnConfig, awg_service=None) -> str:
        assert existing_config is config
        return "wg-config"

    monkeypatch.setattr(vpn_service, "get_reusable_active_config", fake_get_reusable_active_config)
    monkeypatch.setattr(vpn_service, "create_config", fake_create_config)
    monkeypatch.setattr(vpn_service, "download_config_body", fake_download_config_body)

    result_config, body = await vpn_service.create_and_download_config(DummySession(), user)

    assert result_config is config
    assert body == "wg-config"


@pytest.mark.asyncio
async def test_create_and_download_creates_when_no_active_config(monkeypatch: pytest.MonkeyPatch) -> None:
    user = User(id=uuid.uuid4(), email="user@example.com", password_hash="x", role=UserRole.user, is_active=True)
    created_config = VpnConfig(
        id=uuid.uuid4(),
        user_id=user.id,
        awg_client_id="awg-new",
        status=VpnConfigStatus.active,
        starts_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    async def fake_get_reusable_active_config(session: DummySession, user_id: uuid.UUID) -> None:
        assert user_id == user.id
        return None

    async def fake_create_config(session: DummySession, existing_user: User, awg_service=None) -> VpnConfig:
        assert existing_user is user
        return created_config

    async def fake_download_config_body(session: DummySession, existing_config: VpnConfig, awg_service=None) -> str:
        assert existing_config is created_config
        return "wg-config"

    monkeypatch.setattr(vpn_service, "get_reusable_active_config", fake_get_reusable_active_config)
    monkeypatch.setattr(vpn_service, "create_config", fake_create_config)
    monkeypatch.setattr(vpn_service, "download_config_body", fake_download_config_body)

    result_config, body = await vpn_service.create_and_download_config(DummySession(), user)

    assert result_config is created_config
    assert body == "wg-config"


@pytest.mark.asyncio
async def test_create_and_download_rejects_blocked_user() -> None:
    user = User(id=uuid.uuid4(), email="blocked@example.com", password_hash="x", role=UserRole.user, is_active=False)

    with pytest.raises(HTTPException) as exc:
        await vpn_service.create_and_download_config(DummySession(), user)

    assert exc.value.status_code == 403
    assert exc.value.detail == "user blocked"


def test_create_and_download_route_returns_attachment(monkeypatch: pytest.MonkeyPatch) -> None:
    user = User(id=uuid.uuid4(), email="user@example.com", password_hash="x", role=UserRole.user, is_active=True)
    config = VpnConfig(
        id=uuid.uuid4(),
        user_id=user.id,
        awg_client_id="awg-route",
        status=VpnConfigStatus.active,
        starts_at=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )

    async def fake_create_and_download_config(session: DummySession, existing_user: User, awg_service=None) -> tuple[VpnConfig, str]:
        assert existing_user is user
        return config, "wg-route-body"

    async def fake_get_db():
        yield DummySession()

    app.dependency_overrides[get_current_user] = lambda: user
    monkeypatch.setattr(vpn_service, "create_and_download_config", fake_create_and_download_config)

    app.dependency_overrides[get_db] = fake_get_db
    try:
        with TestClient(app) as client:
            response = client.post("/vpn/configs/create-and-download")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.text == "wg-route-body"
    assert response.headers["content-type"].startswith("application/x-wireguard-profile")
    assert response.headers["content-disposition"] == f'attachment; filename="ghostgate-{config.id}.conf"'
