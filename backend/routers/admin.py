from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
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


def _parse_dt(raw: object) -> datetime | None:
    s = str(raw or "").strip()
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def _ledger_summary(record: dict[str, Any]) -> list[dict[str, Any]]:
    ledger = record.get("credit_ledger")
    if not isinstance(ledger, list):
        return []
    rows: list[dict[str, Any]] = []
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
    flags = record.get("legacy_flags") if isinstance(record.get("legacy_flags"), dict) else {}
    source = str(record.get("source") or ("legacy_iidatech_users_xlsx" if flags else "signup"))
    return {
        "email": email,
        "name": str(record.get("name") or record.get("username") or email.split("@")[0]),
        "username": str(record.get("username") or ""),
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
        "source": source,
        "imported_at": str(record.get("imported_at") or ""),
        "is_subscriber": bool(flags.get("is_subscriber")),
        "ai_create_access_paid": bool(flags.get("ai_create_access_paid")),
        "financial_tools_access_paid": bool(flags.get("financial_tools_access_paid")),
        "event_management_access_paid": bool(flags.get("event_management_access_paid")),
        "legacy_flags": {
            "ai_create_expiry": flags.get("ai_create_expiry"),
            "financial_tools_expiry": flags.get("financial_tools_expiry"),
            "event_management_expiry": flags.get("event_management_expiry"),
            "subscription_expiry": flags.get("subscription_expiry"),
            "pm_access_expiry": flags.get("pm_access_expiry"),
            "legacy_id": flags.get("legacy_id"),
        }
        if flags
        else None,
    }


def _build_account_analytics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    d30 = now - timedelta(days=30)
    d7 = now - timedelta(days=7)
    month_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    plan_counts: Counter[str] = Counter()
    signed_7 = signed_30 = with_projects = zero_credits = legacy_import = paid_any = credits_used_sum = active_30 = 0

    for r in rows:
        joined = _parse_dt(r.get("joined_at"))
        if joined:
            if joined.tzinfo is None:
                joined = joined.replace(tzinfo=timezone.utc)
            month_counts[joined.strftime("%Y-%m")] += 1
            if joined >= d7:
                signed_7 += 1
            if joined >= d30:
                signed_30 += 1
        last = _parse_dt(r.get("last_activity_at"))
        if last:
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            if last >= d30:
                active_30 += 1
        if int(r.get("projects") or 0) > 0:
            with_projects += 1
        rem = r.get("credits_remaining")
        if isinstance(rem, int) and rem <= 0 and not r.get("is_unlimited"):
            zero_credits += 1
        used = r.get("credits_used")
        if isinstance(used, int):
            credits_used_sum += used
        src = str(r.get("source") or "signup")
        source_counts[src] += 1
        if "legacy" in src:
            legacy_import += 1
        plan_counts[str(r.get("plan_name") or r.get("plan_id") or "unknown")] += 1
        if (
            r.get("is_subscriber")
            or r.get("ai_create_access_paid")
            or r.get("financial_tools_access_paid")
            or r.get("event_management_access_paid")
        ):
            paid_any += 1

    return {
        "signups_7d": signed_7,
        "signups_30d": signed_30,
        "active_30d": active_30,
        "with_projects": with_projects,
        "zero_credits": zero_credits,
        "legacy_import": legacy_import,
        "paid_legacy_flags": paid_any,
        "credits_used": credits_used_sum,
        "signups_by_month": [
            {"month": m, "count": month_counts[m]} for m in sorted(month_counts.keys(), reverse=True)[:12]
        ],
        "by_source": [{"source": k, "count": v} for k, v in source_counts.most_common()],
        "by_plan": [{"plan": k, "count": v} for k, v in plan_counts.most_common()],
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
        hay = " ".join(
            [
                email,
                str(record.get("name") or ""),
                str(record.get("username") or ""),
                str(record.get("source") or ""),
            ]
        ).lower()
        if needle and needle not in hay:
            continue
        rows.append(_usage_row(email, record))
    rows.sort(key=lambda row: str(row.get("joined_at") or ""), reverse=True)
    analytics = _build_account_analytics(rows)
    return {
        "users": rows,
        "total": len(rows),
        "totals": {
            "users": len(rows),
            "projects": sum(int(r.get("projects") or 0) for r in rows),
            "credits_remaining": sum(
                int(r["credits_remaining"]) for r in rows if isinstance(r.get("credits_remaining"), int)
            ),
            "credits_used": analytics["credits_used"],
            "signups_30d": analytics["signups_30d"],
            "active_30d": analytics["active_30d"],
            "with_projects": analytics["with_projects"],
            "zero_credits": analytics["zero_credits"],
            "legacy_import": analytics["legacy_import"],
            "paid_legacy_flags": analytics["paid_legacy_flags"],
        },
        "analytics": analytics,
    }


@router.post("/credits")
def grant_credits(body: AdminCreditsBody, admin: str = Depends(require_admin_email)) -> dict:
    key = body.email.strip().lower()
    users = load_users()
    if key not in users:
        raise HTTPException(status_code=404, detail="User not found")
    result = add_credits(key, int(body.amount), reason=body.reason, metadata={"granted_by": admin})
    return {"success": True, "email": key, **result}
