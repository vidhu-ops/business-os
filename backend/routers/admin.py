from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.auth import load_users, require_admin_email
from backend.services.account_service import get_plan_snapshot
from backend.services.audit_service import audit_status
from backend.services.credit_service import add_credits
from backend.services.workspaces import list_workspaces_for_user

router = APIRouter(prefix="/admin", tags=["admin"])


class AdminCreditsBody(BaseModel):
    email: str = Field(min_length=3)
    amount: int = Field(default=1_000_000, ge=1, le=10_000_000)
    reason: str = "admin_grant"


def _ledger_summary(record: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = record.get("credit_ledger")
    if not isinstance(ledger, list):
        return []
    rows: list[dict[str, Any]] = []
    # Ledger is newest-first; take the first 8 recent entries.
    for item in ledger[:8]:
        if not isinstance(item, dict):
            continue
        amount = item.get("amount")
        try:
            amount_n = int(amount) if amount is not None else 0
        except (TypeError, ValueError):
            amount_n = 0
        rows.append(
            {
                "action": str(item.get("action") or ""),
                "amount": amount_n,
                # Positive amount = spend; negative = grant/refund
                "direction": "spend" if amount_n > 0 else "grant" if amount_n < 0 else "zero",
                "at": str(item.get("at") or ""),
            }
        )
    return rows


def _usage_row(email: str, record: dict[str, Any]) -> dict[str, Any]:
    plan = get_plan_snapshot(record)
    projects = list_workspaces_for_user(email, limit=50)
    reports = sum(1 for p in projects if p.get("has_report"))
    plans = sum(1 for p in projects if p.get("has_plan"))
    audit = audit_status(email)
    remaining = plan.get("credits_remaining")
    total = plan.get("credits_total")
    used = None
    if isinstance(remaining, int) and isinstance(total, int):
        used = max(0, total - remaining)
    updated_ats = [str(p.get("updated_at") or "") for p in projects if p.get("updated_at")]
    ledger = _ledger_summary(record)
    last_ledger = ledger[0]["at"] if ledger else ""
    last_activity = max([*updated_ats, last_ledger, str(record.get("created_at") or "")], default="")
    return {
        "email": email,
        "name": str(record.get("name") or email.split("@")[0]),
        "joined_at": str(record.get("created_at") or ""),
        "plan_id": plan.get("id"),
        "plan_name": plan.get("display_name") or plan.get("name"),
        "credits_remaining": remaining,
        "credits_total": total,
        "credits_used": used,
        "is_unlimited": bool(plan.get("is_unlimited")),
        "projects": len(projects),
        "reports_ready": reports,
        "plans_ready": plans,
        "free_audit_used": int(audit.get("free_audit_used") or 0),
        "free_audit_granted": int(audit.get("free_audit_granted") or 0),
        "last_activity_at": last_activity,
        "recent_actions": ledger,
        "project_ideas": [str(p.get("idea") or p.get("workspace_id") or "") for p in projects[:5]],
        "analytics_visitor_id": str(record.get("analytics_visitor_id") or ""),
        "signup_attribution": record.get("signup_attribution") if isinstance(record.get("signup_attribution"), dict) else None,
    }


@router.get("/users")
def list_crm_users(
    q: str = Query(""),
    _: str = Depends(require_admin_email),
) -> dict:
    needle = (q or "").strip().lower()
    users = load_users()
    rows: list[dict[str, Any]] = []
    for email, record in users.items():
        if not isinstance(record, dict):
            continue
        if email == "demo@local":
            continue
        if needle and needle not in email.lower() and needle not in str(record.get("name") or "").lower():
            continue
        rows.append(_usage_row(email, record))
    rows.sort(key=lambda row: str(row.get("joined_at") or ""), reverse=True)
    return {
        "users": rows,
        "total": len(rows),
        "totals": {
            "users": len(rows),
            "projects": sum(int(r.get("projects") or 0) for r in rows),
            "credits_remaining": sum(
                int(r["credits_remaining"]) for r in rows if isinstance(r.get("credits_remaining"), int)
            ),
        },
    }

@router.post("/credits")
def grant_credits(body: AdminCreditsBody, admin: str = Depends(require_admin_email)) -> dict:
    key = body.email.strip().lower()
    users = load_users()
    if key not in users:
        raise HTTPException(status_code=404, detail="User not found")
    result = add_credits(key, int(body.amount), reason=body.reason, metadata={"granted_by": admin})
    return {"success": True, "email": key, **result}

