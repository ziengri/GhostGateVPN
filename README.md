# GhostGateVPN Backend

FastAPI backend for issuing AmneziaWG configs through an external awg-server.

## Local setup

```powershell
uv sync
Copy-Item .env.example .env
```

For local non-Docker runs, set `DATABASE_URL` to a reachable PostgreSQL database, for example:

```env
DATABASE_URL=postgresql+asyncpg://vpn_user:vpn_password@localhost:5432/vpn_service
```

Run migrations:

```powershell
uv run alembic upgrade head
```

Start the API:

```powershell
uv run uvicorn app.main:app --reload
```

OpenAPI is available at `http://localhost:8000/docs`.

SMTP is disabled by default for local development. Set `SMTP_ENABLED=true` after configuring real SMTP credentials.

Email verification links use:

```text
GET /auth/email/verify?token=...
```

The JSON API variant is also available:

```text
POST /auth/email/verify
```

## Docker Compose

awg-server is intentionally outside Compose. On Linux, Compose uses:

```yaml
extra_hosts:
  - "host.docker.internal:host-gateway"
```

Use this AWG URL inside `.env`:

```env
AWG_API_BASE_URL=http://host.docker.internal:7777
```

Start services:

```powershell
docker compose up --build
```

The backend container applies Alembic migrations before starting Uvicorn.

Frontend runs from a separate Compose file inside `frontend/`, so it can be deployed on another server:

```powershell
cd frontend
Copy-Item .env.example .env
docker compose up --build -d
```

Set `API_BASE_URL` in `frontend/.env` to the public backend URL, for example `https://api.example.com`.

## Security notes

The database stores only `awg_client_id`, status and validity dates for VPN configs. It must not store `.conf` bodies or private/public/preshared keys. Download requests fetch config bodies from awg-server on demand.
