from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from backend.auth import load_users, save_users
from backend.config import settings

PLAN_CATALOG: dict[str, dict[str, Any]] = {
    "starter": {
        "id": "starter",
        "name": "Starter",
        "price_label": "Free",
        "period": "",
        "credits_total": 30,
        "tagline": "Validate ideas with real research output.",
        "upgrade_href": "/pricing",
    },
    "growth": {
        "id": "growth",
        "name": "Growth",
        "price_label": "₹4,999",
        "period": "/ month",
        "credits_total": None,
        "tagline": "Unlimited research and Employee OS for growing teams.",
        "upgrade_href": "/pricing",
    },
    "scale": {
        "id": "scale",
        "name": "Scale",
        "price_label": "Custom",
        "period": "",
        "credits_total": None,
        "tagline": "Multi-workspace, SLA, and white-label deliverables.",
        "upgrade_href": "/pricing",
    },
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_account(email: str, name: str | None = None) -> dict[str, Any]:
    users = load_users()
    record = users.get(email)
    if not record:
        record = {
            "email": email,
            "name": name or email.split("@")[0],
            "password_hash": "",
            "created_at": _now_iso(),
            "plan": "starter",
            "credits_remaining": 30,
            "credits_total": 30,
        }
        users[email] = record
        save_users(users)
        return record

    changed = False
    if name and not record.get("name"):
        record["name"] = name
        changed = True
    if not record.get("created_at"):
        record["created_at"] = _now_iso()
        changed = True
    if not record.get("plan"):
        record["plan"] = "starter"
        changed = True
    if record.get("credits_remaining") is None:
        record["credits_remaining"] = 30
        changed = True
    if record.get("credits_total") is None:
        record["credits_total"] = 30
        changed = True
    if changed:
        users[email] = record
        save_users(users)
    return record


def get_plan_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    plan_id = str(record.get("plan") or "starter")
    catalog = PLAN_CATALOG.get(plan_id, PLAN_CATALOG["starter"])
    credits_remaining = record.get("credits_remaining")
    credits_total = record.get("credits_total")
    if plan_id in {"growth", "scale"}:
        credits_remaining = None
        credits_total = None
    return {
        **catalog,
        "credits_remaining": credits_remaining,
        "credits_total": credits_total,
        "is_unlimited": plan_id in {"growth", "scale"},
    }


def list_recent_files(limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = settings.outputs_root
    if not root.exists():
        return rows
    allowed = {".md", ".json", ".csv", ".pdf", ".docx", ".xlsx", ".html", ".jsonl"}
    files = [
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in allowed and "__pycache__" not in path.parts
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for path in files[:limit]:
        stat = path.stat()
        rows.append(
            {
                "name": path.name,
                "folder": path.parent.name,
                "type": path.suffix.lower().lstrip("."),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "path": str(path.relative_to(settings.app_root)).replace("\\", "/"),
            }
        )
    return rows


def build_activity(projects: list[dict[str, Any]], files: list[dict[str, Any]]) -> list[dict[str, str]]:
    activity: list[dict[str, str]] = []
    for project in projects[:6]:
        label = str(project.get("idea") or "Project").strip() or "Project"
        when = str(project.get("updated_at") or "")
        kind = "report" if project.get("has_report") else "plan" if project.get("has_plan") else "project"
        title = {
            "report": "Market report ready",
            "plan": "Business plan updated",
            "project": "Project updated",
        }[kind]
        activity.append(
            {
                "type": kind,
                "title": title,
                "detail": f"{label[:80]} · {project.get('country', '')}".strip(" ·"),
                "at": when,
            }
        )
    for file_row in files[:4]:
        activity.append(
            {
                "type": "file",
                "title": "File saved",
                "detail": str(file_row.get("name") or "Deliverable"),
                "at": str(file_row.get("modified") or ""),
            }
        )
    return activity[:10]
