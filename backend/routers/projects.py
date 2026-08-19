from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.founder_scope import assess_topic_scope
from backend.services.demo_service import block_demo_mutation, block_workspace_mutation, is_demo_user
from backend.services import org_memory as om
from backend.services.workspaces import (
    build_project_payload,
    list_workspaces_for_user,
    load_workspace,
    require_workspace_access,
    save_workspace,
    update_workspace_intake,
)

router = APIRouter(prefix="/projects", tags=["projects"])


class CreateProjectBody(BaseModel):
    idea: str = Field(min_length=3)
    industry: str = Field(min_length=2)
    country: str = Field(min_length=2)
    workflow: str = "Understand your market"
    areas: str = ""
    mode: str = "new"  # new | existing


class UpdateIntakeBody(BaseModel):
    idea: str = Field(min_length=3)
    industry: str = Field(min_length=2)
    country: str = Field(min_length=2)
    areas: str = ""


@router.get("")
def get_projects(email: str = Depends(get_current_user)) -> dict:
    return {"projects": list_workspaces_for_user(email, limit=50), "is_demo": is_demo_user(email)}


@router.post("")
def create_project(body: CreateProjectBody, email: str = Depends(get_current_user)) -> dict:
    block_demo_mutation(email, action="create projects")
    mode = "existing" if str(body.mode or "").strip().lower() == "existing" else "new"
    scope = assess_topic_scope(body.idea, body.industry, body.country)
    payload = build_project_payload(
        body.idea.strip(),
        body.country.strip(),
        body.industry.strip(),
        body.workflow,
        scope,
        owner_email=email,
    )
    payload["areas"] = body.areas.strip()
    bp = payload.get("business_profile") if isinstance(payload.get("business_profile"), dict) else om.empty_workspace_profile(mode=mode)
    bp["mode"] = mode
    payload["business_profile"] = bp
    if mode == "existing":
        payload["business_builder_is_existing"] = True
        payload["business_plan_mode"] = "existing"
        payload = om.advance_execution_loop(payload, phase="gauge", event="Existing business project created — GAUGE next")
    else:
        payload = om.advance_execution_loop(payload, phase="intake", event="New project created — org memory onboarding next")
    path = save_workspace(payload)
    if not path:
        raise HTTPException(status_code=500, detail="Could not save project")
    payload["path"] = str(path)
    return {
        "project": payload,
        "scope": scope,
        "next": {
            "onboarding": f"/app/onboarding?project={payload['workspace_id']}",
            "gauge": f"/app/audit?project={payload['workspace_id']}" if mode == "existing" else None,
            "mentor": f"/app/mentor?project={payload['workspace_id']}",
        },
    }


@router.get("/{workspace_id}")
def get_project(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    payload = require_workspace_access(email, workspace_id)
    return {"project": payload}


@router.patch("/{workspace_id}/intake")
def patch_intake(workspace_id: str, body: UpdateIntakeBody, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, workspace, action="edit projects")
    scope = assess_topic_scope(body.idea, body.industry, body.country)
    workspace = update_workspace_intake(
        workspace_id,
        idea=body.idea,
        industry=body.industry,
        country=body.country,
        areas=body.areas,
        scope_assessment=scope,
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project": workspace, "scope": scope}