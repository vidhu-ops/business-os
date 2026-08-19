from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.demo_service import block_demo_mutation, block_workspace_mutation, is_demo_user
from backend.services import org_memory as om
from backend.services.workspaces import list_workspaces_for_user, load_workspace, require_workspace_access, save_workspace

router = APIRouter(prefix="/org-memory", tags=["org-memory"])


class ProfileBody(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)
    mode: str | None = None
    save_to_account: bool = True
    onboarding_complete: bool | None = None


class IntegrationBody(BaseModel):
    integration_id: str
    connected: bool = True
    url: str = ""
    credential: str = ""
    notes: str = ""
    save_to_account: bool = True
    workspace_id: str | None = None


class GoalProgressBody(BaseModel):
    goal_id: str
    current: str = ""
    progress_pct: int | None = None
    status: str | None = None


class LoopBody(BaseModel):
    workspace_id: str
    phase: str | None = None
    event: str | None = None
    approval_request: str | None = None
    approval_detail: str | None = None
    resolve_approval_id: str | None = None
    adjustment: str | None = None


@router.get("/catalog")
def get_catalog(_: str = Depends(get_current_user)) -> dict:
    return om.catalog()


@router.get("/account")
def get_account_org(email: str = Depends(get_current_user)) -> dict:
    org = om.load_account_org(email)
    return {
        "org": org,
        "completeness": om.profile_completeness(org.get("business_profile") or {}),
        "catalog": om.catalog(),
        "is_demo": is_demo_user(email),
    }


@router.patch("/account/profile")
def patch_account_profile(body: ProfileBody, email: str = Depends(get_current_user)) -> dict:
    block_demo_mutation(email, action="edit org memory")
    payload: dict[str, Any] = {"business_profile": body.answers}
    if body.onboarding_complete is not None:
        payload["onboarding_complete"] = body.onboarding_complete
    org = om.save_account_org(email, payload)
    om.sync_goals_from_profile(email, org.get("business_profile") or {})
    return {"org": om.load_account_org(email), "completeness": om.profile_completeness(org.get("business_profile") or {})}


@router.post("/account/integrations")
def upsert_account_integration(body: IntegrationBody, email: str = Depends(get_current_user)) -> dict:
    block_demo_mutation(email, action="connect integrations")
    row = {
        "connected": body.connected,
        "url": body.url.strip(),
        "notes": body.notes.strip(),
    }
    if body.credential.strip():
        row["credential"] = body.credential.strip()
    if body.save_to_account:
        om.save_account_org(email, {"integrations": {body.integration_id: row}})
    if body.workspace_id:
        ws = require_workspace_access(email, body.workspace_id)
        if not ws:
            raise HTTPException(status_code=404, detail="Project not found")
        block_workspace_mutation(email, ws, action="connect integrations")
        ints = ws.get("integrations") if isinstance(ws.get("integrations"), dict) else {}
        ints[body.integration_id] = {**row, "from_account": body.save_to_account}
        ws["integrations"] = ints
        # Mirror known OAuth providers into report oauth store when credential pasted
        catalog_row = next((c for c in om.INTEGRATION_CATALOG if c["id"] == body.integration_id), None)
        oauth_provider = (catalog_row or {}).get("oauth_provider")
        if oauth_provider and body.credential.strip():
            try:
                from backend.services.workspace_context import workspace_report_id
                from iidatech.integrations.oauth_store import set_connection

                rid = workspace_report_id(ws)
                set_connection(rid, oauth_provider, {"access_token": body.credential.strip(), "connected": True})
            except Exception:
                pass
        save_workspace(ws)
    return {
        "org": om.load_account_org(email),
        "integrations": om.effective_integrations(
            load_workspace(body.workspace_id) if body.workspace_id else None, email
        ),
    }


@router.get("/projects/{workspace_id}")
def get_project_org(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    ws = require_workspace_access(email, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Project not found")
    profile = om.effective_business_profile(ws, email)
    return {
        "workspace_id": workspace_id,
        "business_profile": ws.get("business_profile") or om.empty_workspace_profile(),
        "effective_profile": profile,
        "completeness": om.profile_completeness(profile),
        "integrations": om.effective_integrations(ws, email),
        "account": om.load_account_org(email),
        "execution_loop": om.execution_loop_snapshot(ws, email),
        "catalog": om.catalog(),
        "has_gauge": bool(ws.get("gauge_audit") or ws.get("existing_business_profile")),
        "mode": str((ws.get("business_profile") or {}).get("mode") or ("existing" if ws.get("business_builder_is_existing") else "new")),
    }


@router.patch("/projects/{workspace_id}/profile")
def patch_project_profile(workspace_id: str, body: ProfileBody, email: str = Depends(get_current_user)) -> dict:
    ws = require_workspace_access(email, workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, ws, action="edit org memory")
    ws = om.apply_profile_to_workspace(
        ws,
        body.answers,
        mode=body.mode,
        complete=body.onboarding_complete,
    )
    if body.save_to_account:
        om.save_account_org(
            email,
            {
                "business_profile": body.answers,
                "onboarding_complete": bool(body.onboarding_complete) if body.onboarding_complete is not None else None,
            },
        )
        om.sync_goals_from_profile(email, om.effective_business_profile(ws, email))
    if body.onboarding_complete:
        ws = om.advance_execution_loop(ws, phase="research" if body.mode != "existing" else "gauge", event="Onboarding profile completed")
    save_workspace(ws)
    return {
        "workspace_id": workspace_id,
        "business_profile": ws.get("business_profile"),
        "effective_profile": om.effective_business_profile(ws, email),
        "execution_loop": om.execution_loop_snapshot(ws, email),
    }


@router.post("/goals/progress")
def post_goal_progress(body: GoalProgressBody, email: str = Depends(get_current_user)) -> dict:
    block_demo_mutation(email, action="update goals")
    try:
        out = om.update_goal_progress(
            email,
            body.goal_id,
            current=body.current,
            progress_pct=body.progress_pct,
            status=body.status,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return out


@router.post("/loop")
def post_loop(body: LoopBody, email: str = Depends(get_current_user)) -> dict:
    ws = require_workspace_access(email, body.workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, ws, action="update execution loop")
    approval = None
    if body.approval_request or body.resolve_approval_id or body.adjustment:
        approval = {
            "request": body.approval_request,
            "detail": body.approval_detail,
            "resolve_id": body.resolve_approval_id,
            "adjustment": body.adjustment,
        }
    ws = om.advance_execution_loop(ws, phase=body.phase, event=body.event, approval=approval)
    save_workspace(ws)
    return {"execution_loop": om.execution_loop_snapshot(ws, email), "workspace_id": body.workspace_id}


@router.get("/bootstrap")
def bootstrap(email: str = Depends(get_current_user)) -> dict:
    org = om.load_account_org(email)
    projects = list_workspaces_for_user(email, limit=20)
    return {
        "org": org,
        "completeness": om.profile_completeness(org.get("business_profile") or {}),
        "catalog": om.catalog(),
        "projects": projects,
        "needs_onboarding": not bool(org.get("onboarding_complete")) and om.profile_completeness(org.get("business_profile") or {})["pct"] < 40,
    }