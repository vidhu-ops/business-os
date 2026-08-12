from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from backend.auth import get_current_user, load_users
from backend.services.account_service import ensure_account, get_plan_snapshot
from backend.services.demo_service import is_demo_user
from backend.services.iida_guide_service import build_proactive_tip, heuristic_reply, try_llm_reply

router = APIRouter(prefix="/iida", tags=["iida"])


class GuideContext(BaseModel):
    path: str = "/app/dashboard"
    screen_summary: str | None = None
    project_id: str | None = None


class GuideChatBody(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    path: str = "/app/dashboard"
    screen_summary: str | None = None
    project_id: str | None = None
    prefer_llm: bool = True


def _profile(email: str) -> dict[str, Any]:
    users = load_users()
    record = ensure_account(email, users.get(email, {}).get("name"))
    plan = get_plan_snapshot(record)
    return {
        "name": record.get("name") or email.split("@")[0],
        "email": email,
        "plan_name": (plan or {}).get("name") if isinstance(plan, dict) else None,
        "credits_remaining": record.get("credits_remaining"),
        "is_demo": is_demo_user(email),
    }


@router.get("/tip")
def get_tip(path: str = "/app/dashboard", screen_summary: str | None = None, email: str = Depends(get_current_user)) -> dict:
    profile = _profile(email)
    return build_proactive_tip(
        path=path,
        user_name=str(profile["name"]),
        email=email,
        plan_name=profile.get("plan_name"),
        credits_remaining=profile.get("credits_remaining") if isinstance(profile.get("credits_remaining"), int) else None,
        screen_summary=screen_summary,
        is_demo=bool(profile.get("is_demo")),
    )


@router.post("/chat")
def post_chat(body: GuideChatBody, email: str = Depends(get_current_user)) -> dict:
    profile = _profile(email)
    kwargs = dict(
        message=body.message,
        path=body.path,
        user_name=str(profile["name"]),
        email=email,
        plan_name=profile.get("plan_name"),
        credits_remaining=profile.get("credits_remaining") if isinstance(profile.get("credits_remaining"), int) else None,
        screen_summary=body.screen_summary,
        is_demo=bool(profile.get("is_demo")),
        project_id=body.project_id,
    )
    if body.prefer_llm:
        llm = try_llm_reply(**kwargs)
        if llm:
            return llm
    return heuristic_reply(**kwargs)
