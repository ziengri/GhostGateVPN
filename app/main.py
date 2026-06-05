from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import admin_configs, admin_subscriptions, admin_users, auth, me, plans, subscriptions, vpn_configs
from app.core.config import get_cors_origins, settings
from app.workers.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(me.router)
app.include_router(plans.router)
app.include_router(subscriptions.router)
app.include_router(vpn_configs.router)
app.include_router(admin_users.router)
app.include_router(admin_configs.router)
app.include_router(admin_subscriptions.router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
