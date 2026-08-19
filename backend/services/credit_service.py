from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from backend.auth import load_users, save_users
from backend.services.account_service import ensure_account
from backend.services.pricing_catalog import (
    credit_cost_for_action,
    credit_costs_map,
    credit_labels_map,
    get_plan,
    is_unlimited_plan,
    RESEARCH_TIERS,
    signup_credits_for_plan,
)

CREDIT_COSTS: dict[str, int] = credit_costs_map()
CREDIT_LABELS: dict[str, str] = credit_labels_map()


def is_unlimited(email: str) -> bool:
    record = ensure_account(email)
    return is_unlimited_plan(str(record.get("plan") or "starter"))


def get_balance(email: str) -> dict[str, Any]:
    record = ensure_account(email)
    unlimited = is_unlimited(email)
    remaining = record.get("credits_remaining")
    total = record.get("credits_total")
    plan = get_plan(str(record.get("plan") or "starter"))
    return {
        "credits_remaining": None if unlimited else remaining,
        "credits_total": None if unlimited else total,
        "is_unlimited": unlimited,
        "plan": record.get("plan", "starter"),
        "plan_display_name": plan.get("display_name"),
        "plan_stage": plan.get("stage"),
        "billing_model": plan.get("billing_model"),
        "entitlements": plan.get("entitlements"),
        "costs": dict(CREDIT_COSTS),
        "labels": dict(CREDIT_LABELS),
        "research_tiers": [
            {"section_count": count, "credits": tier["credits"], "label": tier["label"]}
            for count, tier in sorted(RESEARCH_TIERS.items())
        ],
    }


def _week_key() -> str:
    return datetime.now(timezone.utc).strftime("%G-W%V")


def office_week_credit_cost(*, mode: str, departments: list[str]) -> tuple[str, int]:
    if mode == "full_office":
        return "full_office_week", CREDIT_COSTS["full_office_week"]
    depts = [d for d in departments if str(d).strip()]
    count = max(1, len(depts))
    return "department_week", CREDIT_COSTS["department_week"] * count


def office_week_already_paid(workspace: dict[str, Any], *, mode: str, departments: list[str]) -> bool:
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    passes = os2.get("credit_pass") if isinstance(os2.get("credit_pass"), dict) else {}
    week = _week_key()
    if mode == "full_office":
        return passes.get("full_office_week") == week
    depts = sorted({str(d).strip() for d in departments if str(d).strip()})
    if not depts:
        depts = ["default"]
    dept_passes = passes.get("departments") if isinstance(passes.get("departments"), dict) else {}
    return all(dept_passes.get(d) == week for d in depts)


def mark_office_week_paid(workspace: dict[str, Any], *, mode: str, departments: list[str]) -> None:
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    passes = dict(os2.get("credit_pass") or {})
    week = _week_key()
    if mode == "full_office":
        passes["full_office_week"] = week
    else:
        dept_passes = dict(passes.get("departments") or {})
        depts = [str(d).strip() for d in departments if str(d).strip()] or ["default"]
        for d in depts:
            dept_passes[d] = week
        passes["departments"] = dept_passes
    os2["credit_pass"] = passes
    workspace["employee_os"] = os2


def spend_credits(
    email: str,
    action: str,
    *,
    quantity: int = 1,
    section_count: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if is_unlimited(email):
        return {"charged": 0, "credits_remaining": None, "is_unlimited": True, "action": action}

    try:
        unit = credit_cost_for_action(action, section_count=section_count)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    amount = max(1, int(quantity)) * int(unit)
    users = load_users()
    key = email.strip().lower()
    record = ensure_account(key)
    remaining = int(record.get("credits_remaining") or 0)
    if remaining < amount:
        raise HTTPException(
            status_code=402,
            detail={
                "message": f"Not enough credits. This action needs {amount}; you have {remaining}.",
                "required": amount,
                "remaining": remaining,
                "action": action,
                "upgrade_href": "/pricing",
            },
        )
    record["credits_remaining"] = remaining - amount
    ledger = list(record.get("credit_ledger") or [])
    ledger.insert(
        0,
        {
            "action": action,
            "amount": amount,
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "meta": metadata or {},
        },
    )
    record["credit_ledger"] = ledger[:50]
    users[key] = record
    save_users(users)
    return {
        "charged": amount,
        "credits_remaining": record["credits_remaining"],
        "is_unlimited": False,
        "action": action,
    }


def charge_office_week(email: str, workspace: dict[str, Any], *, mode: str, departments: list[str]) -> dict[str, Any]:
    if office_week_already_paid(workspace, mode=mode, departments=departments):
        return {"charged": 0, "already_paid": True, **get_balance(email)}
    action, _ = office_week_credit_cost(mode=mode, departments=departments)
    qty = 1
    if action == "department_week":
        depts = [d for d in departments if str(d).strip()]
        qty = max(1, len(depts))
    result = spend_credits(email, action, quantity=qty, metadata={"mode": mode, "departments": departments})
    mark_office_week_paid(workspace, mode=mode, departments=departments)
    return result


def charge_employee_work(
    email: str | None,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Charge 1 credit for one Employee OS work unit. No-op when email missing."""
    if not email or not str(email).strip():
        return None
    from backend.services.demo_service import is_demo_user

    key = str(email).strip().lower()
    if is_demo_user(key):
        return {"charged": 0, "is_demo": True, "action": "employee_work"}
    return spend_credits(key, "employee_work", metadata=metadata or {})


def ensure_can_spend(email: str | None, action: str = "employee_work", *, quantity: int = 1) -> None:
    """Raise 402 early when the account cannot afford the action."""
    if not email or not str(email).strip():
        return
    key = str(email).strip().lower()
    from backend.services.demo_service import is_demo_user

    if is_demo_user(key) or is_unlimited(key):
        return
    try:
        unit = credit_cost_for_action(action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    amount = max(1, int(quantity)) * int(unit)
    record = ensure_account(key)
    remaining = int(record.get("credits_remaining") or 0)
    if remaining < amount:
        raise HTTPException(
            status_code=402,
            detail={
                "message": f"Not enough credits. This action needs {amount}; you have {remaining}.",
                "required": amount,
                "remaining": remaining,
                "action": action,
                "upgrade_href": "/pricing",
            },
        )


def charge_mentor_turn(
    email: str | None,
    *,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Charge 1 credit for one Mentor chat turn. No-op when email missing."""
    if not email or not str(email).strip():
        return None
    from backend.services.demo_service import is_demo_user

    key = str(email).strip().lower()
    if is_demo_user(key):
        return {"charged": 0, "is_demo": True, "action": "mentor"}
    return spend_credits(key, "mentor", metadata=metadata or {})


def add_credits(email: str, amount: int, *, reason: str = "purchase", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    users = load_users()
    key = email.strip().lower()
    record = ensure_account(key)
    if is_unlimited(key):
        return {"added": 0, "credits_remaining": None, "is_unlimited": True}
    added = max(0, int(amount))
    remaining = int(record.get("credits_remaining") or 0) + added
    total = int(record.get("credits_total") or 0) + added
    record["credits_remaining"] = remaining
    record["credits_total"] = total
    ledger = list(record.get("credit_ledger") or [])
    ledger.insert(
        0,
        {
            "action": reason,
            "amount": -added,
            "at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "meta": metadata or {},
        },
    )
    record["credit_ledger"] = ledger[:50]
    users[key] = record
    save_users(users)
    return {"added": added, "credits_remaining": remaining, "is_unlimited": False}
