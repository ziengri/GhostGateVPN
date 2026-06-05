import uuid
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from app.api.deps import require_roles
from app.db.models import User, UserRole, VpnConfig, VpnConfigStatus
from app.services.vpn_service import can_read_config


@pytest.mark.asyncio
async def test_role_dependency_accepts_only_configured_roles() -> None:
    admin = User(email="admin@example.com", phone_number="+70000000001", password_hash="x", role=UserRole.admin)
    user = User(email="user@example.com", phone_number="+70000000002", password_hash="x", role=UserRole.user)
    dependency = require_roles(UserRole.admin)

    assert await dependency(admin) is admin
    with pytest.raises(HTTPException) as exc:
        await dependency(user)
    assert exc.value.status_code == 403


def test_config_read_access_contract() -> None:
    owner_id = uuid.uuid4()
    other_id = uuid.uuid4()
    config = VpnConfig(
        user_id=owner_id,
        awg_client_id="awg-1",
        status=VpnConfigStatus.active,
        starts_at=datetime.now(UTC),
        expires_at=datetime.now(UTC),
    )
    owner = User(id=owner_id, email="owner@example.com", phone_number="+70000000003", password_hash="x", role=UserRole.user)
    other_user = User(id=other_id, email="other@example.com", phone_number="+70000000004", password_hash="x", role=UserRole.user)
    support = User(id=uuid.uuid4(), email="support@example.com", phone_number="+70000000005", password_hash="x", role=UserRole.support)
    admin = User(id=uuid.uuid4(), email="admin@example.com", phone_number="+70000000006", password_hash="x", role=UserRole.admin)

    assert can_read_config(owner, config)
    assert can_read_config(support, config)
    assert can_read_config(admin, config)
    assert not can_read_config(other_user, config)
