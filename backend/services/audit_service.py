"""Free company audit credits (one per signup) stored on user JSON records."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from backend.auth import load_users, save_users
from backend.config import settings
from backend.services.account_service import ensure_account

FREE_AUDIT_ON_SIGNUP = 1


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ensure_audit_fields(record: dict[str, Any]) -> None:
    record.setdefault("free_audit_granted", 0)
    record.setdefault("free_audit_used", 0)


def grant_signup_free_audit(record: dict[str, Any]) -> None:
    _ensure_audit_fields(record)
    record["free_audit_granted"] = FREE_AUDIT_ON_SIGNUP
    record["free_audit_used"] = 0


def free_audit_available(email: str) -> bool:
    record = ensure_account(email)
    _ensure_audit_fields(record)
    granted = int(record.get("free_audit_granted") or 0)
    used = int(record.get("free_audit_used") or 0)
    return granted > used


def consume_free_audit(email: str) -> bool:
    if not free_audit_available(email):
        return False
    users = load_users()
    key = email.strip().lower()
    record = users.get(key) or ensure_account(key)
    _ensure_audit_fields(record)
    granted = int(record.get("free_audit_granted") or 0)
    used = int(record.get("free_audit_used") or 0)
    if granted <= used:
        return False
    record["free_audit_used"] = used + 1
    users[key] = record
    save_users(users)
    return True


def audit_status(email: str) -> dict[str, Any]:
    record = ensure_account(email)
    _ensure_audit_fields(record)
    granted = int(record.get("free_audit_granted") or 0)
    used = int(record.get("free_audit_used") or 0)
    return {
        "free_audit_granted": granted,
        "free_audit_used": used,
        "free_audit_available": granted > used,
    }


def require_free_audit_or_existing(email: str, *, workspace: dict[str, Any]) -> None:
    existing = workspace.get("gauge_audit")
    if isinstance(existing, dict) and existing.get("overall_score") is not None:
        return
    if free_audit_available(email):
        return
    raise HTTPException(
        status_code=402,
        detail={
            "message": "Your free company audit has been used. Upgrade for more audits.",
            "upgrade_href": "/pricing",
        },
    )


def save_audit_record(email: str, *, company_name: str, payload: dict[str, Any]) -> str:
    audit_id = "audit_" + uuid.uuid4().hex[:12]
    out = settings.app_root / "business_build_outputs" / "audits"
    out.mkdir(parents=True, exist_ok=True)
    path = out / (audit_id + ".json")
    path.write_text(
        json.dumps(
            {
                "audit_id": audit_id,
                "email": email.strip().lower(),
                "company_name": company_name,
                "created_at": _now_iso(),
                "payload": payload,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    users = load_users()
    key = email.strip().lower()
    record = users.get(key) or ensure_account(key)
    history = list(record.get("audit_history") or [])
    history.insert(0, {"audit_id": audit_id, "company_name": company_name, "created_at": _now_iso()})
    record["audit_history"] = history[:20]
    users[key] = record
    save_users(users)
    return audit_id