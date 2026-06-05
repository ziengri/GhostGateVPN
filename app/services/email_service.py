from __future__ import annotations

from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings


class EmailService:
    async def send_email(self, to_email: str, subject: str, body: str) -> None:
        if not settings.smtp_enabled:
            return
        message = EmailMessage()
        message["From"] = f"{settings.smtp_from_name} <{settings.smtp_from_email}>"
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=settings.smtp_password,
            start_tls=settings.smtp_use_tls,
            use_tls=settings.smtp_use_ssl,
        )

    async def send_verify_email(self, to_email: str, token: str) -> None:
        link = f"{settings.app_public_url}/verify-email?token={token}"
        await self.send_email(to_email, "Verify your email", f"Verify your email: {link}")

    async def send_password_reset_email(self, to_email: str, token: str) -> None:
        await self.send_email(to_email, "Password reset", f"Use this token to reset your password: {token}")

    async def send_trial_started_email(self, to_email: str) -> None:
        await self.send_email(to_email, "Trial started", "Your 14 day VPN trial has started.")

    async def send_config_created_email(self, to_email: str) -> None:
        await self.send_email(to_email, "VPN config created", "Your VPN config is ready.")
