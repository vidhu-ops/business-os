from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.auth import load_users, save_users
from backend.config import settings
from backend.services.founder_files import is_founder_visible_file
from backend.services.pricing_catalog import get_plan, is_unlimited_plan, normalize_plan_id, signup_credits_for_plan


def ensure_account(email: str, name: str | None = None) -> dict[str, Any]:
    users = load_users()
    key = email.strip().lower()
    if key not in users:
        credits = signup_credits_for_plan("starter")
        users[key] = {
            "email": key,
            "name": (name or key.split("@")[0]).strip(),
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "plan": "starter",
            "credits_remaining": credits,
            "credits_total": credits,
        }
        save_users(users)
    elif name and not users[key].get("name"):
        users[key]["name"] = name.strip()
        save_users(users)
    return users[key]


def get_plan_snapshot(record: dict[str, Any]) -> dict[str, Any]:
    plan_id = normalize_plan_id(str(record.get("plan") or "starter"))
    catalog = get_plan(plan_id)
    unlimited = is_unlimited_plan(plan_id)
    credits_total = record.get("credits_total")
    credits_remaining = record.get("credits_remaining")
    if unlimited:
        credits_total = None
        credits_remaining = None
    checkout_href = f"/checkout?plan={plan_id}" if catalog.get("billable") else "/pricing"
    return {
        "id": plan_id,
        "name": catalog.get("display_name") or catalog.get("id"),
        "display_name": catalog.get("display_name"),
        "stage": catalog.get("stage"),
        "user_type": catalog.get("user_type"),
        "billing_model": catalog.get("billing_model"),
        "price_label": catalog.get("price_label"),
        "period": catalog.get("period", ""),
        "tagline": (catalog.get("perks") or [""])[0],
        "upgrade_href": checkout_href,
        "entitlements": catalog.get("entitlements"),
        "credits_total": credits_total,
        "credits_remaining": credits_remaining,
        "is_unlimited": unlimited,
    }


def activate_plan(email: str, plan_id: str) -> dict[str, Any]:
    users = load_users()
    key = email.strip().lower()
    record = ensure_account(key)
    plan = normalize_plan_id(plan_id)
    record["plan"] = plan
    if is_unlimited_plan(plan):
        record["credits_total"] = None
        record["credits_remaining"] = None
        record["plan_activated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    users[key] = record
    save_users(users)
    return record


def list_recent_files(limit: int = 8) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = settings.outputs_root
    if not root.exists():
        return rows
    allowed = {".md", ".json", ".csv", ".pdf", ".docx", ".xlsx", ".html", ".jsonl"}
    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in allowed
        and "__pycache__" not in path.parts
        and is_founder_visible_file(path)
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for path in files[:limit]:
        stat = path.stat()
        rows.append(
            {
                "name": path.name,
                "folder": path.parent.name,
                "type": path.suffix.lower().lstrip("."),
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "path": str(path.relative_to(settings.app_root)).replace("\\", "/"),
            }
        )
    return rows


def build_activity(projects: list[dict[str, Any]], files: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for project in projects[:5]:
        title = str(project.get("idea") or project.get("workspace_id") or "Project")
        detail = f"{project.get('industry', '')} · {project.get('country', '')}".strip(" ·")
        items.append(
            {
                "type": "project",
                "title": title[:80],
                "detail": detail or "Workspace updated",
                "at": str(project.get("updated_at") or ""),
            }
        )
    for file_row in files[:3]:
        items.append(
            {
                "type": "file",
                "title": str(file_row.get("name") or "File"),
                "detail": str(file_row.get("folder") or "export"),
                "at": str(file_row.get("modified") or ""),
            }
        )
    return items[:10]
