from dataclasses import dataclass
from typing import Any

import httpx


class AwgError(RuntimeError):
    pass


@dataclass
class AwgClient:
    base_url: str
    token: str
    timeout: float = 20.0

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self.token}"}

    async def create_client(self, client_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.post(
                "/api/clients",
                headers={**self.headers, "Content-Type": "application/json"},
                json={"id": client_id},
            )
        if response.status_code >= 400:
            raise AwgError(f"AWG create client failed: {response.status_code} {response.text}")
        return response.json() if response.content else {"id": client_id}

    async def get_configuration(self, client_id: str) -> str:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(f"/api/clients/{client_id}/configuration", headers=self.headers)
        if response.status_code >= 400:
            raise AwgError(f"AWG get configuration failed: {response.status_code} {response.text}")
        return response.text

    async def delete_client(self, client_id: str) -> None:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.delete(f"/api/clients/{client_id}", headers=self.headers)
        if response.status_code >= 400:
            raise AwgError(f"AWG delete client failed: {response.status_code} {response.text}")

    async def list_clients(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get("/api/clients", headers=self.headers)
        if response.status_code >= 400:
            raise AwgError(f"AWG list clients failed: {response.status_code} {response.text}")
        data = response.json()
        return data if isinstance(data, list) else data.get("clients", [])

    async def get_stats(self, client_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout) as client:
            response = await client.get(f"/api/clients/{client_id}/stats", headers=self.headers)
        if response.status_code >= 400:
            raise AwgError(f"AWG get stats failed: {response.status_code} {response.text}")
        return response.json()
