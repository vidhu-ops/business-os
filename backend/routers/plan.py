from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.credit_service import spend_credits
from backend.services.demo_service import block_workspace_mutation
from backend.services.plan_builder import build_business_plan
from backend.services.workspaces import load_workspace, require_workspace_access, save_workspace, update_workspace_intake

router = APIRouter(prefix="/plan", tags=["plan"])


class PlanRunBody(BaseModel):
    workspace_id: str
    use_research: bool = True


class PlanModeBody(BaseModel):
    company_mode: str | None = Field(default=None, description="new | existing | null")


class PlanIntakeBody(BaseModel):
    idea: str = ""
    industry: str = ""
    country: str = "Global"
    areas: str = ""
    pasted_research: str = ""
    use_research: bool = True
    application_mode: bool = False
    application_purpose: str = "General market research"


class GaugeDraftBody(BaseModel):
    draft: dict = Field(default_factory=dict)


@router.get("/gauge/metadata")
def gauge_metadata(_: str = Depends(get_current_user)) -> dict:
    from backend.services.gauge_service import gauge_metadata as meta

    return meta()


@router.get("/{workspace_id}")
def get_plan(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, workspace_id)
    plan = workspace.get("business_plan") if isinstance(workspace.get("business_plan"), dict) else {}
    intake = workspace.get("plan_intake") if isinstance(workspace.get("plan_intake"), dict) else {}
    research = workspace.get("research_report") if isinstance(workspace.get("research_report"), dict) else {}
    has_research = bool(research.get("available") and (research.get("report_markdown") or research.get("markdown")))
    gauge_forward = workspace.get("gauge_forward_plan") if isinstance(workspace.get("gauge_forward_plan"), dict) else {}
    return {
        "plan": plan,
        "gauge_forward_plan": gauge_forward,
        "has_research": has_research,
        "company_mode": workspace.get("business_plan_mode"),
        "intake": {
            "idea": intake.get("idea") or workspace.get("idea", ""),
            "industry": intake.get("industry") or workspace.get("industry", ""),
            "country": intake.get("country") or workspace.get("country", "Global"),
            "areas": intake.get("areas") or workspace.get("areas", ""),
            "pasted_research": intake.get("pasted_research", ""),
            "use_research": intake.get("use_research", True),
            "application_mode": intake.get("application_mode", False),
            "application_purpose": intake.get("application_purpose", "General market research"),
        },
    }


@router.patch("/{workspace_id}/mode")
def set_plan_mode(workspace_id: str, body: PlanModeBody, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, workspace, action="edit plans")
    mode = body.company_mode
    if mode not in {None, "new", "existing"}:
        raise HTTPException(status_code=400, detail="company_mode must be new, existing, or null")
    workspace["business_plan_mode"] = mode
    if mode == "new":
        workspace["business_builder_is_existing"] = False
    elif mode == "existing":
        workspace["business_builder_is_existing"] = True
    save_workspace(workspace)
    return {"company_mode": mode}


@router.patch("/{workspace_id}/intake")
def save_plan_intake(workspace_id: str, body: PlanIntakeBody, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, workspace, action="edit plans")
    workspace = update_workspace_intake(
        workspace_id,
        idea=body.idea or str(workspace.get("idea") or ""),
        industry=body.industry or str(workspace.get("industry") or ""),
        country=body.country or str(workspace.get("country") or "Global"),
        areas=body.areas,
    )
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    workspace["plan_intake"] = {
        "idea": body.idea,
        "industry": body.industry,
        "country": body.country,
        "areas": body.areas,
        "pasted_research": body.pasted_research,
        "use_research": body.use_research,
        "application_mode": body.application_mode,
        "application_purpose": body.application_purpose,
    }
    workspace["application_purpose"] = body.application_purpose
    save_workspace(workspace)
    return {"intake": workspace["plan_intake"]}


@router.post("/run")
def run_plan(body: PlanRunBody, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, body.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    block_workspace_mutation(email, workspace, action="generate business plans")
    credit = spend_credits(email, "business_plan", metadata={"workspace_id": body.workspace_id})
    intake = workspace.get("plan_intake") if isinstance(workspace.get("plan_intake"), dict) else {}
    if intake.get("idea"):
        workspace["idea"] = intake["idea"]
    if intake.get("industry"):
        workspace["industry"] = intake["industry"]
    if intake.get("country"):
        workspace["country"] = intake["country"]
    if not body.use_research:
        rr = workspace.get("research_report")
        if isinstance(rr, dict):
            workspace["research_report"] = {"available": False}
    result = build_business_plan(workspace)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error") or "Plan generation failed")
    workspace["business_plan"] = {
        "available": True,
        "markdown": result.get("markdown", ""),
        "report_markdown": result.get("report_markdown", ""),
        "plan_json": result.get("plan_json"),
        "founder_readable_plan": result.get("founder_readable_plan"),
        "grounded_in_research": result.get("grounded_in_research", False),
    }
    save_workspace(workspace)
    return {**result, "credit": credit}


@router.delete("/{workspace_id}/gauge")
def reset_gauge(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, workspace_id)
    block_workspace_mutation(email, workspace, action="reset audits")
    for key in ("gauge_intake", "gauge_audit", "existing_business_profile"):
        workspace.pop(key, None)
    save_workspace(workspace)
    return {"ok": True, "step": 1}


@router.get("/{workspace_id}/gauge")
def get_gauge(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, workspace_id)
    draft = workspace.get("gauge_intake") if isinstance(workspace.get("gauge_intake"), dict) else {}
    audit = workspace.get("gauge_audit") if isinstance(workspace.get("gauge_audit"), dict) else None
    return {"draft": draft, "audit": audit, "step": int(draft.get("step") or 1)}


@router.patch("/{workspace_id}/gauge")
def save_gauge_draft(workspace_id: str, body: GaugeDraftBody, email: str = Depends(get_current_user)) -> dict:
    workspace = require_workspace_access(email, workspace_id)
    block_workspace_mutation(email, workspace, action="edit audits")
    workspace["gauge_intake"] = body.draft
    step = int(body.draft.get("step") or 1)
    if step < 5:
        workspace.pop("gauge_audit", None)
        workspace.pop("existing_business_profile", None)
    save_workspace(workspace)
    return {"draft": body.draft}


@router.post("/{workspace_id}/gauge/audit")
def run_gauge_audit_endpoint(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    from backend.services.audit_service import consume_free_audit, require_free_audit_or_existing, save_audit_record
    from backend.services.gauge_service import profile_from_draft, run_audit_for_profile, validate_draft

    workspace = require_workspace_access(email, workspace_id)
    block_workspace_mutation(email, workspace, action="run company audits")
    draft = workspace.get("gauge_intake") if isinstance(workspace.get("gauge_intake"), dict) else {}
    errors, profile = validate_draft(draft)
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    existing_audit = workspace.get("gauge_audit") if isinstance(workspace.get("gauge_audit"), dict) else None
    first_run = not (existing_audit and existing_audit.get("overall_score") is not None)
    if first_run:
        require_free_audit_or_existing(email, workspace=workspace)

    audit = run_audit_for_profile(profile)
    from iidatech.services.gauge_audit import merge_gauge_audit_into_profile

    profile_with_audit = merge_gauge_audit_into_profile(profile, audit)
    workspace["gauge_audit"] = audit
    workspace["existing_business_profile"] = profile_with_audit
    workspace["gauge_intake"] = {**draft, "step": 5}
    save_workspace(workspace)

    if first_run:
        consume_free_audit(email)
        company_name = str(profile.get("company_name") or workspace.get("idea") or "Company")
        save_audit_record(email, company_name=company_name, payload=audit)

    return {"audit": audit, "profile": profile_with_audit}


@router.post("/{workspace_id}/gauge/build-plan")
def build_gauge_plan(workspace_id: str, email: str = Depends(get_current_user)) -> dict:
    from backend.services.gauge_service import build_forward_plan, profile_from_draft, validate_draft
    from iidatech.services.gauge_audit import merge_gauge_audit_into_profile

    workspace = require_workspace_access(email, workspace_id)
    block_workspace_mutation(email, workspace, action="build plans")
    draft = workspace.get("gauge_intake") if isinstance(workspace.get("gauge_intake"), dict) else {}
    errors, profile = validate_draft(draft)
    if errors:
        raise HTTPException(status_code=400, detail=errors)
    audit = workspace.get("gauge_audit")
    if not isinstance(audit, dict):
        raise HTTPException(status_code=400, detail="Run GAUGE audit first")
    profile_with_audit = merge_gauge_audit_into_profile(profile, audit)
    result = build_forward_plan(workspace, profile_with_audit)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error") or "Plan generation failed")
    workspace = load_workspace(workspace_id) or workspace
    workspace["business_plan"] = {
        "available": True,
        "markdown": result.get("markdown", ""),
        "report_markdown": result.get("report_markdown", ""),
        "plan_json": result.get("plan_json"),
        "founder_readable_plan": result.get("founder_readable_plan"),
        "grounded_in_research": result.get("grounded_in_research", False),
        "gauge_audit": audit,
        "plan_forward_profile": profile_with_audit,
    }
    workspace["idea"] = result.get("idea") or workspace.get("idea")
    save_workspace(workspace)
    return result
