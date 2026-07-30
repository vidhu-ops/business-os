"""Demo mode: view-only sample workspace, no mutations."""

from __future__ import annotations

from fastapi import HTTPException

DEMO_EMAIL = "demo@local"
DEMO_WORKSPACE_ID = "demo_readonly"


def is_demo_user(email: str) -> bool:
    return str(email or "").strip().lower() == DEMO_EMAIL


def is_readonly_workspace(workspace: dict | None) -> bool:
    if not workspace or not isinstance(workspace, dict):
        return False
    ws_id = str(workspace.get("workspace_id") or "").strip()
    return bool(workspace.get("demo_readonly")) or ws_id == DEMO_WORKSPACE_ID


def block_demo_mutation(email: str, *, action: str = "change") -> None:
    if is_demo_user(email):
        raise HTTPException(
            status_code=403,
            detail={
                "message": f"Demo mode is view-only — you cannot {action}. Sign up for a free account to create projects.",
                "signup_href": "/login?mode=register",
                "demo": True,
            },
        )


def block_workspace_mutation(email: str, workspace: dict | None, *, action: str = "change") -> None:
    block_demo_mutation(email, action=action)
    if is_readonly_workspace(workspace):
        raise HTTPException(
            status_code=403,
            detail={
                "message": f"This sample workspace is read-only — you cannot {action}. Sign up to create your own projects.",
                "signup_href": "/login?mode=register",
                "demo": True,
            },
        )


def demo_workspace_row() -> dict:
    return {
        "workspace_id": DEMO_WORKSPACE_ID,
        "idea": "CRM automation for SMBs (sample)",
        "country": "India",
        "industry": "SaaS / B2B Software",
        "current_path": "Understand your market",
        "updated_at": "2026-03-01T08:30:00Z",
        "path": f"opportunity_workspaces/{DEMO_WORKSPACE_ID}/workspace.json",
        "has_report": True,
        "has_plan": True,
        "demo_readonly": True,
    }