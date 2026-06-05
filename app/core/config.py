from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "GhostGateVPN"
    app_env: str = "local"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_public_url: str = "http://localhost:8000"
    app_secret_key: str = Field(default="change-me-super-secret")
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://host.docker.internal:5173"

    database_url: str = "postgresql+asyncpg://vpn_user:vpn_password@localhost:5432/vpn_service"

    jwt_access_token_expire_minutes: int = 120
    jwt_refresh_token_expire_days: int = 30
    jwt_algorithm: str = "HS256"

    awg_api_base_url: str = "http://host.docker.internal:7777"
    awg_api_token: str = "change-me-awg-token"
    awg_timeout_seconds: float = 10.0

    smtp_host: str = "smtp.example.com"
    smtp_port: int = 587
    smtp_username: str = "your-smtp-user"
    smtp_password: str = "your-smtp-password"
    smtp_from_email: str = "no-reply@example.com"
    smtp_from_name: str = "VPN Service"
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_enabled: bool = False

    scheduler_enabled: bool = True


settings = Settings()


def get_cors_origins() -> list[str]:
    return [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
