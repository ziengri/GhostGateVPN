import pytest

from app.core.config import settings
from app.services.email_service import EmailService


@pytest.mark.asyncio
async def test_email_service_noops_when_smtp_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fail_send(*args, **kwargs) -> None:
        raise AssertionError("SMTP send should not be called when SMTP is disabled")

    monkeypatch.setattr(settings, "smtp_enabled", False)
    monkeypatch.setattr("app.services.email_service.aiosmtplib.send", fail_send)

    await EmailService().send_password_reset_email("user@example.com", "token")

