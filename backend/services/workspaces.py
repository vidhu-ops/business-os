from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import settings


def safe_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", (value or "").strip())
    return cleaned.strip("._") or "project"


def workspace_slug(topic: str, country: str, industry: str) -> str:
    return safe_filename(f"{topic}_{country}_{industry}")[:110] or "opportunity"


def workspace_dir(topic: str, country: str, industry: str) -> Path:
    path = settings.workspaces_root / workspace_slug(topic, country, industry)
    path.mkdir(parents=True, exist_ok=True)
    return path


def assess_topic_scope(topic: str, industry: str, target: str) -> dict[str, Any]:
    tokens = [t for t in re.split(r"\W+", (topic or "").lower()) if len(t) > 2]
    issues: list[str] = []
    if len(tokens) < 3:
        issues.append("Topic has too few specific words.")
    if not (industry or "").strip():
        issues.append("Industry is required.")
    if not (target or "").strip():
        issues.append("Market / country is required.")
    return {
        "ok": not issues,
        "issues": issues,
        "token_count": len(tokens),
    }


def build_project_payload(
    topic: str,
    country: str,
    industry: str,
    workflow_choice: str = "Understand your market",
    scope_assessment: dict | None = None,
    *,
    owner_email: str | None = None,
) -> dict[str, Any]:
    workspace_path = workspace_dir(topic, country, industry)
    payload: dict[str, Any] = {
        "workspace_id": workspace_slug(topic, country, industry),
        "workspace_dir": str(workspace_path),
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "idea": topic,
        "country": country,
        "industry": industry,
        "current_path": workflow_choice,
        "scope_assessment": scope_assessment or assess_topic_scope(topic, industry, country),
        "areas": "",
        "research_report": {"available": False},
        "business_plan": {"available": False},
        "employee_os": {"available": False, "runs": []},
        "automation": {"available": False, "log": []},
    }
    if owner_email:
        payload["owner_email"] = owner_email.strip().lower()
    return payload


def save_workspace(payload: dict[str, Any]) -> Path | None:
    if payload.get("demo_readonly"):
        return None
    try:
        path = Path(payload["workspace_dir"]) / "workspace.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        return path
    except Exception:
        return None


def _workspace_row(payload: dict[str, Any], path: Path) -> dict[str, Any]:
    return {
        "workspace_id": payload.get("workspace_id", path.parent.name),
        "idea": payload.get("idea", ""),
        "country": payload.get("country", ""),
        "industry": payload.get("industry", ""),
        "current_path": payload.get("current_path", ""),
        "updated_at": payload.get("updated_at", ""),
        "path": str(path),
        "has_report": bool((payload.get("research_report") or {}).get("available")),
        "has_plan": bool((payload.get("business_plan") or {}).get("available")),
        "demo_readonly": bool(payload.get("demo_readonly")),
    }


def list_workspaces(limit: int = 50) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = settings.workspaces_root
    if not root.exists():
        return rows
    for path in root.glob("*/workspace.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        rows.append(_workspace_row(payload, path))
    rows.sort(key=lambda row: str(row.get("updated_at", "")), reverse=True)
    return rows[:limit]


def list_workspaces_for_user(email: str, limit: int = 50) -> list[dict[str, Any]]:
    from backend.services.demo_service import DEMO_WORKSPACE_ID, demo_workspace_row, is_demo_user

    if is_demo_user(email):
        if load_workspace(DEMO_WORKSPACE_ID):
            return [demo_workspace_row()]
        return []

    key = email.strip().lower()
    rows: list[dict[str, Any]] = []
    root = settings.workspaces_root
    if not root.exists():
        return rows
    for path in root.glob("*/workspace.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        ws_id = str(payload.get("workspace_id", path.parent.name))
        if ws_id == DEMO_WORKSPACE_ID or payload.get("demo_readonly"):
            continue
        owner = str(payload.get("owner_email") or "").strip().lower()
        if owner and owner != key:
            continue
        if not owner:
            continue
        rows.append(_workspace_row(payload, path))
    rows.sort(key=lambda row: str(row.get("updated_at", "")), reverse=True)
    return rows[:limit]


def load_workspace(workspace_id: str) -> dict[str, Any] | None:
    path = settings.workspaces_root / workspace_id / "workspace.json"
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else None
    except Exception:
        return None


def audit_workspace_id_for_user(email: str) -> str:
    key = email.strip().lower().replace("@", "_at_")
    return safe_filename(f"audit_{key}")[:110] or "audit_workspace"


def ensure_audit_workspace(email: str) -> dict[str, Any]:
    """Get or create a dedicated GAUGE audit workspace for this user (no manual project step)."""
    from backend.services.demo_service import DEMO_WORKSPACE_ID, is_demo_user

    if is_demo_user(email):
        demo = load_workspace(DEMO_WORKSPACE_ID)
        if demo:
            return demo

    key = email.strip().lower()
    ws_id = audit_workspace_id_for_user(key)
    existing = load_workspace(ws_id)
    if existing:
        owner = str(existing.get("owner_email") or "").lower()
        if not owner or owner == key:
            if not owner:
                existing["owner_email"] = key
                save_workspace(existing)
            return existing

    root = settings.workspaces_root / ws_id
    root.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    payload: dict[str, Any] = {
        "workspace_id": ws_id,
        "workspace_dir": str(root),
        "owner_email": key,
        "is_audit_workspace": True,
        "idea": "Company audit",
        "country": "Global",
        "industry": "Existing company",
        "current_path": "Company audit (GAUGE)",
        "updated_at": now,
        "scope_assessment": {"ok": True, "issues": []},
        "areas": "",
        "research_report": {"available": False},
        "business_plan": {"available": False},
        "business_plan_mode": "existing",
        "business_builder_is_existing": True,
        "gauge_intake": {"step": 1, "gauge_type": "other"},
        "employee_os": {"available": False, "runs": []},
        "automation": {"available": False, "log": []},
    }
    save_workspace(payload)
    return payload


def user_owns_workspace(email: str, workspace: dict[str, Any]) -> bool:
    from backend.services.demo_service import DEMO_WORKSPACE_ID, is_demo_user

    if workspace.get("demo_readonly") or str(workspace.get("workspace_id")) == DEMO_WORKSPACE_ID:
        return is_demo_user(email)
    owner = str(workspace.get("owner_email") or "").strip().lower()
    if not owner:
        return False
    return owner == email.strip().lower()


def require_workspace_access(email: str, workspace_id: str) -> dict[str, Any]:
    from fastapi import HTTPException

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    if not user_owns_workspace(email, workspace):
        raise HTTPException(status_code=404, detail="Project not found")
    return workspace


def update_workspace_intake(
    workspace_id: str,
    *,
    idea: str,
    industry: str,
    country: str,
    areas: str = "",
    scope_assessment: dict | None = None,
) -> dict[str, Any] | None:
    workspace = load_workspace(workspace_id)
    if not workspace:
        return None
    workspace["idea"] = idea.strip()
    workspace["industry"] = industry.strip()
    workspace["country"] = country.strip()
    workspace["areas"] = areas.strip()
    workspace["scope_assessment"] = scope_assessment or assess_topic_scope(idea, industry, country)
    workspace["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    save_workspace(workspace)
    return workspace
