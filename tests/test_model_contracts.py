from app.db.base import Base
from app.db.models import Plan, UserRole, VpnConfigStatus


def test_vpn_configs_do_not_store_config_body_or_keys() -> None:
    columns = set(Base.metadata.tables["vpn_configs"].columns.keys())

    assert {"awg_client_id", "status", "starts_at", "expires_at"}.issubset(columns)
    assert "config_body" not in columns
    assert "configuration" not in columns
    assert "private_key" not in columns
    assert "public_key" not in columns
    assert "preshared_key" not in columns


def test_required_tables_are_mapped() -> None:
    assert {
        "users",
        "refresh_tokens",
        "plans",
        "subscriptions",
        "vpn_configs",
        "vpn_config_events",
        "email_verification_tokens",
        "password_reset_tokens",
    }.issubset(Base.metadata.tables.keys())


def test_required_enum_values_exist() -> None:
    assert {item.value for item in UserRole} == {"user", "admin", "support"}
    assert {item.value for item in VpnConfigStatus} == {"active", "pending_revoke", "expired", "revoked", "failed"}


def test_trial_plan_model_contract() -> None:
    plan = Plan(code="trial", name="Trial 14 days", duration_days=14, max_configs=1, price_amount=0, currency="RUB")
    assert plan.code == "trial"
    assert plan.duration_days == 14
    assert plan.max_configs == 1

