from fastapi.testclient import TestClient

from app.main import app


def test_health_and_openapi_routes() -> None:
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
        schema = client.get("/openapi.json").json()

    paths = schema["paths"]
    for path in [
        "/auth/register",
        "/auth/login",
        "/auth/refresh",
        "/auth/logout",
        "/auth/email/verify",
        "/auth/password-reset/request",
        "/auth/password-reset/confirm",
        "/me",
        "/plans",
        "/subscriptions/current",
        "/vpn/configs",
        "/vpn/configs/create-and-download",
        "/vpn/configs/{config_id}/download",
        "/vpn/configs/{config_id}/revoke",
        "/admin/users",
        "/admin/configs",
        "/admin/subscriptions",
    ]:
        assert path in paths
    assert "get" in paths["/auth/email/verify"]
    assert "post" in paths["/auth/email/verify"]
    assert "post" in paths["/vpn/configs/create-and-download"]
