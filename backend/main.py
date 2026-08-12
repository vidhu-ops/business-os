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
from backend.routers import admin, audit, auth_routes, automation, canva, credits, dashboard, deliverables, files, health, iida_guide, oauth, os2, partners, payments, plan, pricing, projects, research, team

app = FastAPI(
    title="IIDATECH API",
    version="1.0.0",
    description="Production API for IIDATECH founder product",
)


@app.get("/")
def root() -> dict:
    return {
        "service": "iidatech-api",
        "message": "This URL is the API only. Open the web app service for the UI.",
        "health": "/api/v1/health",
        "docs": "/docs",
    }


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://[\w.-]+\.(vercel\.app|onrender\.com|replit\.dev|repl\.co|w\.repl\.co|kirk\.replit\.dev)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1")
app.include_router(auth_routes.router, prefix="/api/v1")
app.include_router(projects.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(research.router, prefix="/api/v1")
app.include_router(plan.router, prefix="/api/v1")
app.include_router(team.router, prefix="/api/v1")
app.include_router(os2.router, prefix="/api/v1")
app.include_router(automation.router, prefix="/api/v1")
app.include_router(deliverables.router, prefix="/api/v1")
app.include_router(oauth.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")
app.include_router(partners.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(pricing.router, prefix="/api/v1")
app.include_router(canva.router, prefix="/api/v1")
app.include_router(credits.router, prefix="/api/v1")
app.include_router(iida_guide.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
