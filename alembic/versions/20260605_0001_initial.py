from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260605_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE TYPE user_role AS ENUM ('user', 'admin', 'support')")
    op.execute("CREATE TYPE vpn_config_status AS ENUM ('active', 'pending_revoke', 'expired', 'revoked', 'failed')")
    op.execute("CREATE TYPE subscription_status AS ENUM ('active', 'expired', 'cancelled', 'trial')")
    user_role = postgresql.ENUM("user", "admin", "support", name="user_role", create_type=False)
    vpn_config_status = postgresql.ENUM(
        "active", "pending_revoke", "expired", "revoked", "failed", name="vpn_config_status", create_type=False
    )
    subscription_status = postgresql.ENUM("active", "expired", "cancelled", "trial", name="subscription_status", create_type=False)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", user_role, nullable=False, server_default="user"),
        sa.Column("tgid", sa.BigInteger(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)
    op.create_index("idx_users_tgid", "users", ["tgid"], unique=True, postgresql_where=sa.text("tgid IS NOT NULL"))

    op.create_table(
        "plans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("max_configs", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price_amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.Text(), nullable=False, server_default="RUB"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    op.create_index("idx_refresh_tokens_token_hash", "refresh_tokens", ["token_hash"])
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    op.create_table(
        "subscriptions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("plans.id"), nullable=False),
        sa.Column("status", subscription_status, nullable=False, server_default="trial"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_subscriptions_user_id", "subscriptions", ["user_id"])
    op.create_index("idx_subscriptions_status", "subscriptions", ["status"])
    op.create_index("idx_subscriptions_expires_at", "subscriptions", ["expires_at"])
    op.create_index(
        "idx_one_active_subscription_per_user",
        "subscriptions",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("status IN ('active', 'trial')"),
    )

    op.create_table(
        "vpn_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subscription_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True),
        sa.Column("awg_client_id", sa.Text(), nullable=False, unique=True),
        sa.Column("status", vpn_config_status, nullable=False, server_default="active"),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("last_sync_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_vpn_configs_user_id", "vpn_configs", ["user_id"])
    op.create_index("idx_vpn_configs_subscription_id", "vpn_configs", ["subscription_id"])
    op.create_index("idx_vpn_configs_status", "vpn_configs", ["status"])
    op.create_index("idx_vpn_configs_expires_at", "vpn_configs", ["expires_at"])
    op.create_index("idx_vpn_configs_awg_client_id", "vpn_configs", ["awg_client_id"])
    op.create_index("idx_vpn_configs_active_expiring", "vpn_configs", ["expires_at"], postgresql_where=sa.text("status = 'active'"))

    op.create_table(
        "vpn_config_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("config_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("vpn_configs.id", ondelete="CASCADE"), nullable=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_vpn_config_events_config_id", "vpn_config_events", ["config_id"])
    op.create_index("idx_vpn_config_events_user_id", "vpn_config_events", ["user_id"])
    op.create_index("idx_vpn_config_events_event_type", "vpn_config_events", ["event_type"])
    op.create_index("idx_vpn_config_events_created_at", "vpn_config_events", ["created_at"])

    for table_name in ("email_verification_tokens", "password_reset_tokens"):
        op.create_table(
            table_name,
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
            sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
            sa.Column("token_hash", sa.Text(), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        )
        op.create_index(f"idx_{table_name}_user_id", table_name, ["user_id"])
        op.create_index(f"idx_{table_name}_token_hash", table_name, ["token_hash"])

    op.execute(
        """
        INSERT INTO plans (code, name, duration_days, max_configs, price_amount, currency, is_active)
        VALUES ('trial', 'Trial 14 days', 14, 1, 0, 'RUB', TRUE)
        ON CONFLICT (code) DO NOTHING
        """
    )


def downgrade() -> None:
    for table_name in ("password_reset_tokens", "email_verification_tokens"):
        op.drop_index(f"idx_{table_name}_token_hash", table_name=table_name)
        op.drop_index(f"idx_{table_name}_user_id", table_name=table_name)
        op.drop_table(table_name)
    op.drop_index("idx_vpn_config_events_created_at", table_name="vpn_config_events")
    op.drop_index("idx_vpn_config_events_event_type", table_name="vpn_config_events")
    op.drop_index("idx_vpn_config_events_user_id", table_name="vpn_config_events")
    op.drop_index("idx_vpn_config_events_config_id", table_name="vpn_config_events")
    op.drop_table("vpn_config_events")
    op.drop_index("idx_vpn_configs_active_expiring", table_name="vpn_configs")
    op.drop_index("idx_vpn_configs_awg_client_id", table_name="vpn_configs")
    op.drop_index("idx_vpn_configs_expires_at", table_name="vpn_configs")
    op.drop_index("idx_vpn_configs_status", table_name="vpn_configs")
    op.drop_index("idx_vpn_configs_subscription_id", table_name="vpn_configs")
    op.drop_index("idx_vpn_configs_user_id", table_name="vpn_configs")
    op.drop_table("vpn_configs")
    op.drop_index("idx_one_active_subscription_per_user", table_name="subscriptions")
    op.drop_index("idx_subscriptions_expires_at", table_name="subscriptions")
    op.drop_index("idx_subscriptions_status", table_name="subscriptions")
    op.drop_index("idx_subscriptions_user_id", table_name="subscriptions")
    op.drop_table("subscriptions")
    op.drop_index("idx_refresh_tokens_expires_at", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_token_hash", table_name="refresh_tokens")
    op.drop_index("idx_refresh_tokens_user_id", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
    op.drop_table("plans")
    op.drop_index("idx_users_tgid", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_table("users")
    postgresql.ENUM(name="subscription_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="vpn_config_status").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="user_role").drop(op.get_bind(), checkfirst=True)
