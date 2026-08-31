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
from backend.routers import admin, analytics, audit, auth_routes, automation, canva, credits, dashboard, deliverables, files, health, iida_guide, mentor, oauth, org_memory, os2, partners, payments, plan, pricing, projects, research, team

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
app.include_router(mentor.router, prefix="/api/v1")
app.include_router(org_memory.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(analytics.public_router, prefix="/api/v1")
app.include_router(analytics.admin_router, prefix="/api/v1")
app.include_router(analytics.leads_router, prefix="/api/v1")


def _bootstrap_admin_credits() -> None:
    """Ensure ADMIN_EMAIL accounts have at least ADMIN_GRANT_CREDITS (default 1_000_000)."""
    import os

    from backend.auth import admin_emails
    from backend.services.credit_service import add_credits
    from backend.services.user_store import load_users

    target = int(os.getenv("ADMIN_GRANT_CREDITS") or "1000000")
    if target <= 0:
        return
    users = load_users()
    for email in admin_emails():
        rec = users.get(email) if isinstance(users, dict) else None
        if not isinstance(rec, dict):
            continue
        remaining = rec.get("credits_remaining")
        if remaining is None:
            continue  # unlimited
        rem = int(remaining or 0)
        if rem >= target:
            continue
        add_credits(email, target - rem, reason="admin_bootstrap", metadata={"target": target})


try:
    _bootstrap_admin_credits()
except Exception:
    pass

try:
    from backend.services.legacy_user_seed import ensure_legacy_users_seeded

    _legacy_seed_result = ensure_legacy_users_seeded()
    print(f"[startup] legacy_user_seed={_legacy_seed_result}", flush=True)
except Exception as exc:
    print(f"[startup] legacy_user_seed failed: {exc}", flush=True)
