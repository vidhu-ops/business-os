from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user, load_users
from backend.services.credit_service import charge_mentor_turn
from backend.services.demo_service import is_demo_user
from backend.services.mentor_service import build_project_brief, mentor_reply, opening_message
from backend.services.workspaces import list_workspaces_for_user, load_workspace, require_workspace_access

router = APIRouter(prefix="/mentor", tags=["mentor"])


class MentorChatBody(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    workspace_id: str | None = None
    history: list[dict[str, str]] = Field(default_factory=list)


def _pick_workspace(email: str, workspace_id: str | None) -> dict[str, Any] | None:
    if workspace_id:
        ws = require_workspace_access(email, workspace_id)
        return ws
    projects = list_workspaces_for_user(email, limit=20)
    if not projects:
        return None
    ranked = sorted(
        projects,
        key=lambda p: (1 if p.get("has_report") else 0) + (1 if p.get("has_plan") else 0),
        reverse=True,
    )
    wid = str(ranked[0].get("workspace_id") or "")
    return load_workspace(wid) if wid else None


def _profile(email: str) -> dict[str, Any]:
    users = load_users()
    rec = users.get(email.strip().lower()) if isinstance(users, dict) else None
    if not isinstance(rec, dict):
        return {"name": email.split("@")[0], "email": email}
    return {"name": str(rec.get("name") or email.split("@")[0]), "email": email}


@router.get("/bootstrap")
def mentor_bootstrap(workspace_id: str | None = None, email: str = Depends(get_current_user)) -> dict:
    profile = _profile(email)
    workspace = _pick_workspace(email, workspace_id)
    brief = build_project_brief(workspace)
    wid = str((workspace or {}).get("workspace_id") or workspace_id or "")
    return {
        "assistant": "Mentor",
        "workspace_id": wid or None,
        "brief": brief,
        "opening": opening_message(user_name=profile["name"], email=email, brief=brief),
        "is_demo": is_demo_user(email),
        "projects": [
            {
                "workspace_id": p.get("workspace_id"),
                "idea": p.get("idea"),
                "industry": p.get("industry"),
                "country": p.get("country"),
                "has_report": bool(p.get("has_report")),
                "has_plan": bool(p.get("has_plan")),
            }
            for p in list_workspaces_for_user(email, limit=30)
        ],
    }


@router.post("/chat")
def mentor_chat(body: MentorChatBody, email: str = Depends(get_current_user)) -> dict:
    profile = _profile(email)
    workspace = _pick_workspace(email, body.workspace_id)
    if body.workspace_id and not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    brief = build_project_brief(workspace)
    credit = charge_mentor_turn(
        email,
        metadata={"workspace_id": body.workspace_id or "", "via": "mentor_chat"},
    )
    result = mentor_reply(
        message=body.message,
        user_name=profile["name"],
        email=email,
        brief=brief,
        history=body.history,
        workspace_id=body.workspace_id or str((workspace or {}).get("workspace_id") or "") or None,
    )
    result["workspace_id"] = str((workspace or {}).get("workspace_id") or body.workspace_id or "") or None
    if credit is not None:
        result["credit"] = credit
    return result
