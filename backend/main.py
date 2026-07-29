from __future__ import annotations

import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from iidatech.env_bootstrap import ensure_env_loaded

ensure_env_loaded()

from backend.config import settings
from backend.routers import auth_routes, automation, deliverables, files, health, oauth, os2, plan, projects, research, team

app = FastAPI(
    title="IIDATECH API",
    version="1.0.0",
    description="Production API for IIDATECH founder product",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://[\w.-]+\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")
app.include_router(plan.router, prefix="/api/v1")
app.include_router(team.router, prefix="/api/v1")
app.include_router(os2.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
app.include_router(deliverables.router, prefix="/api/v1")
app.include_router(oauth.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
