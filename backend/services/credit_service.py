from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from backend.auth import load_users, save_users
from backend.services.account_service import ensure_account

CREDIT_COSTS: dict[str, int] = {
    "research": 5,
    "business_plan": 5,
    "department_week": 10,
    "full_office_week": 50,
    "automation_build": 8,
    "automation_run": 8,
}

CREDIT_LABELS: dict[str, str] = {
    "research": "Market research report",
    "business_plan": "Business plan generation",
    "department_week": "Employee OS — one department (1 week)",
    "full_office_week": "Employee OS — full office (1 week)",
    "automation_build": "Automation workflow build",
    "automation_run": "Automation step run",
}


def is_unlimited(email: str) -> bool:
    record = ensure_account(email)
    return str(record.get("plan") or "starter").lower() == "growth"


def get_balance(email: str) -> dict[str, Any]:
    record = ensure_account(email)
    unlimited = is_unlimited(email)
    remaining = record.get("credits_remaining")
    total = record.get("credits_total")
    return {
        "credits_remaining": None if unlimited else remaining,
        "credits_total": None if unlimited else total,
        "is_unlimited": unlimited,
        "plan": record.get("plan", "starter"),
        "costs": dict(CREDIT_COSTS),
        "labels": dict(CREDIT_LABELS),
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
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if is_unlimited(email):
        return {"charged": 0, "credits_remaining": None, "is_unlimited": True, "action": action}

    unit = CREDIT_COSTS.get(action)
    if unit is None:
        raise HTTPException(status_code=400, detail=f"Unknown credit action: {action}")
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
