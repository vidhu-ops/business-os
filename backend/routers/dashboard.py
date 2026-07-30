from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import get_current_user, load_users
from backend.services.account_service import (
    build_activity,
    ensure_account,
    get_plan_snapshot,
    list_recent_files,
)
from backend.services.audit_service import audit_status
from backend.services.demo_service import is_demo_user
from backend.services.workspaces import list_workspaces_for_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(email: str = Depends(get_current_user)) -> dict:
    users = load_users()
    record = ensure_account(email, users.get(email, {}).get("name"))
    projects = list_workspaces_for_user(email, limit=50)
    files = list_recent_files(limit=8)
    reports_ready = sum(1 for p in projects if p.get("has_report"))
    plans_ready = sum(1 for p in projects if p.get("has_plan"))
    plan = get_plan_snapshot(record)
    credits_total = record.get("credits_total") or 0
    credits_remaining = record.get("credits_remaining")
    credits_used = None
    if credits_remaining is not None and credits_total:
        credits_used = max(0, int(credits_total) - int(credits_remaining))

    return {
        "user": {
            "email": email,
            "name": record.get("name") or email.split("@")[0],
            "member_since": record.get("created_at", ""),
        },
        "plan": plan,
        "stats": {
            "projects": len(projects),
            "reports_ready": reports_ready,
            "plans_ready": plans_ready,
            "saved_files": len(files),
            "credits_remaining": credits_remaining,
            "credits_used": credits_used,
        },
        "projects": projects[:8],
        "recent_files": files,
        "recent_activity": build_activity(projects, files),
        "audit": audit_status(email),
        "is_demo": is_demo_user(email),
    }
