from __future__ import annotations

from awg_client import AwgClient, AwgError

from app.core.config import settings


class AwgService:
    def __init__(self) -> None:
        self.client = AwgClient(
            base_url=settings.awg_api_base_url,
            token=settings.awg_api_token,
            timeout=settings.awg_timeout_seconds,
        )

    async def create_client(self, awg_client_id: str) -> None:
        await self.client.create_client(awg_client_id)

    async def get_configuration(self, awg_client_id: str) -> str:
        return await self.client.get_configuration(awg_client_id)

    async def revoke_client(self, awg_client_id: str) -> None:
        await self.client.delete_client(awg_client_id)


__all__ = ["AwgError", "AwgService"]

