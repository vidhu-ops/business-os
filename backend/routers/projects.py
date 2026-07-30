from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.founder_scope import assess_topic_scope
from backend.services.demo_service import block_demo_mutation, block_workspace_mutation, is_demo_user
from backend.services.workspaces import (
    build_project_payload,
    list_workspaces_for_user,
    load_workspace,
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
    path = save_workspace(payload)
    if not path:
        raise HTTPException(status_code=500, detail="Could not save project")
    payload["path"] = str(path)
    return {"project": payload, "scope": scope}


@router.get("/{workspace_id}")
def get_project(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    payload = load_workspace(workspace_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"project": payload}


@router.patch("/{workspace_id}/intake")
def patch_intake(workspace_id: str, body: UpdateIntakeBody, email: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
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
