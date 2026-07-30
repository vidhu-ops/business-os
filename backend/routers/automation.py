from __future__ import annotations

import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.automation_setup import automation_setup_requirements
from backend.services.credit_service import spend_credits
from backend.services.demo_service import DEMO_WORKSPACE_ID, block_workspace_mutation, is_demo_user
from backend.services.workspace_context import workspace_report_context
from backend.services.workspaces import load_workspace, save_workspace
from iidatech.execution.agent_queue import (
    ensure_automation_team,
    init_queue_from_spec,
    load_queue,
    process_next_queue_item,
)
from iidatech.execution.automation_steps import AUTOMATION_STEP_CATALOG, automation_report_id, build_spec_from_steps
from iidatech.execution.os2_api_keys import merge_api_keys

router = APIRouter(prefix="/automation", tags=["automation"])


class AutoBuildBody(BaseModel):
    workspace_id: str
    step_ids: list[str] = Field(min_length=1)
    name: str = "My company workflow"


class AutoRunBody(BaseModel):
    workspace_id: str
    auto_approve_external: bool = False


def _automation_id(workspace: dict) -> str:
    return automation_report_id(str(workspace.get("idea") or ""), str(workspace.get("country") or "Global"))


def _finalize_spec(spec: dict, name: str) -> dict:
    import hashlib

    rid = f"auto-{int(time.time() * 1000)}-{hashlib.sha1(name.encode('utf-8', errors='ignore')).hexdigest()[:8]}"
    spec["id"] = rid
    spec["name"] = name
    spec["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    spec["status"] = "Ready to run with agents"
    return spec


@router.get("/steps")
def list_steps(_: str = Depends(get_current_user)) -> dict:
    return {"steps": AUTOMATION_STEP_CATALOG}


@router.get("/{workspace_id}")
def automation_status(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    report_id = _automation_id(workspace)
    auto = workspace.get("automation") if isinstance(workspace.get("automation"), dict) else {}
    if is_demo_user(email) and workspace_id == DEMO_WORKSPACE_ID and auto.get("demo_queue"):
        queue = auto["demo_queue"]
    else:
        queue = load_queue(report_id)
    return {
        "automation": auto,
        "report_id": report_id,
        "queue": queue,
        "steps_catalog": AUTOMATION_STEP_CATALOG,
        "is_demo_sample": bool(auto.get("demo_sample")),
    }


@router.post("/build")
def build_automation(body: AutoBuildBody, email: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(body.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, workspace, action="build automations")
    credit = spend_credits(email, "automation_build", metadata={"workspace_id": body.workspace_id, "steps": body.step_ids})
    idea = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or "Global").strip()
    report_id = _automation_id(workspace)

    spec = build_spec_from_steps(
        body.step_ids,
        idea=idea,
        industry=industry,
        geography=geography,
        name=body.name,
    )
    spec = _finalize_spec(spec, body.name)
    ensure_automation_team(report_id, topic=idea, industry=industry, geography=geography)
    queue = init_queue_from_spec(report_id, spec)

    auto = workspace.get("automation") if isinstance(workspace.get("automation"), dict) else {}
    auto["available"] = True
    auto["active_spec"] = spec
    auto["report_id"] = report_id
    workspace["automation"] = auto
    save_workspace(workspace)
    setup = automation_setup_requirements(body.step_ids, report_id, workspace_id=body.workspace_id)
    return {
        "success": True,
        "spec": spec,
        "queue": queue,
        "setup_requirements": setup,
        "credit": credit,
    }


@router.post("/run-next")
def run_next_step(body: AutoRunBody, email: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(body.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, workspace, action="run automations")
    credit = spend_credits(email, "automation_run", metadata={"workspace_id": body.workspace_id})
    idea = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or "Global").strip()
    report_id = _automation_id(workspace)
    api_keys = merge_api_keys()
    report_context = workspace_report_context(workspace)

    ensure_automation_team(report_id, topic=idea, industry=industry, geography=geography)
    outcome = process_next_queue_item(
        report_id,
        idea=idea,
        industry=industry,
        geography=geography,
        api_keys=api_keys,
        report_context=report_context,
        auto_approve_external=body.auto_approve_external,
    )
    queue = load_queue(report_id)
    auto = workspace.get("automation") if isinstance(workspace.get("automation"), dict) else {}
    log = list(auto.get("log") or [])
    if outcome.get("item"):
        log.insert(0, outcome)
    auto["log"] = log[:30]
    auto["last_run"] = outcome
    workspace["automation"] = auto
    save_workspace(workspace)
    auto_spec = auto.get("active_spec") if isinstance(auto.get("active_spec"), dict) else {}
    step_ids = [str(s.get("id") or "") for s in (auto_spec.get("picked_steps") or []) if isinstance(s, dict)]
    setup = automation_setup_requirements(step_ids, report_id, workspace_id=body.workspace_id) if step_ids else []
    return {
        "success": bool(outcome.get("success", True)),
        "outcome": outcome,
        "queue": queue,
        "setup_requirements": setup,
        "credit": credit,
    }
