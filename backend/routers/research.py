from __future__ import annotations

import threading
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.founder_scope import assess_topic_scope, country_choices
from backend.services.os2_service import merged_keys_for_workspace
from backend.services.workspaces import load_workspace, save_workspace, update_workspace_intake
from iidatech.evidence_bank.perplexity_client import perplexity_enabled
from iidatech.execution.session_api_keys import session_api_keys
from iidatech.services.perplexity_report_engine import format_market_geography
from iidatech.services.report_section_plans import SIMPLE_SECTION_COUNTS, budget_for_sections, section_titles
from iidatech.services.client_report_view import sanitize_research_result
from iidatech.services.simple_perplexity_report import generate_simple_perplexity_report, simple_report_budget_usd

router = APIRouter(prefix="/research", tags=["research"])

_RESEARCH_SETUP_HINT = (
    "Research is not configured yet. An administrator can enable it in server environment settings."
)


def _perplexity_ready(workspace_id: str | None = None) -> bool:
    if workspace_id:
        if merged_keys_for_workspace(workspace_id).get("perplexity"):
            return True
    return perplexity_enabled()


class ResearchRunBody(BaseModel):
    workspace_id: str
    section_count: int = Field(default=8, ge=3, le=25)
    idea: str | None = None
    industry: str | None = None
    country: str | None = None
    areas: str | None = None


class ScopePreviewBody(BaseModel):
    idea: str = ""
    industry: str = ""
    country: str = "Global"
    areas: str = ""


def _persist_research(workspace: dict, result: dict, section_count: int) -> None:
    topic = str(workspace.get("idea") or "").strip()
    geography = str(workspace.get("country") or "Global").strip()
    client = sanitize_research_result(result)
    markdown = str(client.get("report_markdown") or client.get("markdown") or "")
    workspace["research_report"] = {
        "available": bool(result.get("success")),
        "pipeline": "simple",
        "topic": topic,
        "geography": geography,
        "section_count": section_count,
        "report_markdown": markdown,
        "markdown": markdown,
        "warnings": client.get("warnings") or [],
        "full_result": client,
    }
    save_workspace(workspace)


def _workspace_intake_payload(workspace: dict) -> dict:
    areas = str(workspace.get("areas") or "").strip()
    geography = str(workspace.get("country") or "Global").strip()
    scope = workspace.get("scope_assessment") if isinstance(workspace.get("scope_assessment"), dict) else {}
    return {
        "idea": workspace.get("idea", ""),
        "industry": workspace.get("industry", ""),
        "country": geography,
        "areas": areas,
        "market_label": format_market_geography(geography, areas),
        "scope_ok": bool(scope.get("ok", True)),
        "scope_issues": list(scope.get("issues") or []),
        "scope_suggestions": list(scope.get("suggestions") or []),
    }


def _research_job(workspace: dict) -> dict:
    job = workspace.get("research_job")
    return job if isinstance(job, dict) else {}


def _run_research_background(
    workspace_id: str,
    section_count: int,
    topic: str,
    industry: str,
    geography: str,
    areas: str,
) -> None:
    try:
        keys = merged_keys_for_workspace(workspace_id)
        with session_api_keys(keys):
            result = generate_simple_perplexity_report(
                topic,
                industry=industry,
                geography=geography,
                areas=areas,
                section_count=section_count,
            )
        workspace = load_workspace(workspace_id)
        if not workspace:
            return
        if result.get("success"):
            _persist_research(workspace, result, section_count)
            workspace = load_workspace(workspace_id) or workspace
            workspace["research_job"] = {
                "status": "completed",
                "section_count": section_count,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        else:
            workspace["research_job"] = {
                "status": "failed",
                "error": str(result.get("error") or "Report failed"),
                "section_count": section_count,
                "finished_at": datetime.now(timezone.utc).isoformat(),
            }
        save_workspace(workspace)
    except Exception as exc:
        workspace = load_workspace(workspace_id)
        if not workspace:
            return
        workspace["research_job"] = {
            "status": "failed",
            "error": str(exc),
            "section_count": section_count,
            "finished_at": datetime.now(timezone.utc).isoformat(),
        }
        save_workspace(workspace)


@router.get("/options")
def research_options(
    workspace_id: str | None = None,
    _: str = Depends(get_current_user),
) -> dict:
    ready = _perplexity_ready(workspace_id)
    options = []
    for count in SIMPLE_SECTION_COUNTS:
        options.append(
            {
                "section_count": count,
                "titles": section_titles(count),
            }
        )
    return {
        "research_ready": ready,
        "setup_hint": None if ready else _RESEARCH_SETUP_HINT,
        "section_counts": list(SIMPLE_SECTION_COUNTS),
        "countries": country_choices(),
        "options": options,
    }


@router.post("/scope")
def preview_scope(body: ScopePreviewBody, _: str = Depends(get_current_user)) -> dict:
    scope = assess_topic_scope(body.idea, body.industry, body.country)
    return {
        "scope": scope,
        "market_label": format_market_geography(body.country, body.areas.strip()),
    }


@router.get("/{workspace_id}")
def get_research(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    research = workspace.get("research_report") if isinstance(workspace.get("research_report"), dict) else {}
    if research:
        research = dict(research)
        full = research.get("full_result")
        if isinstance(full, dict):
            research["full_result"] = sanitize_research_result(full)
        elif research.get("report_markdown") or research.get("markdown"):
            research = {**research, **sanitize_research_result(research)}
    return {
        "research": research,
        "job": _research_job(workspace),
        "intake": _workspace_intake_payload(workspace),
    }


@router.post("/run")
def run_research(body: ResearchRunBody, _: str = Depends(get_current_user)) -> dict:
    if not _perplexity_ready(body.workspace_id):
        raise HTTPException(status_code=503, detail=_RESEARCH_SETUP_HINT)
    workspace = load_workspace(body.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")

    job = _research_job(workspace)
    if job.get("status") == "running":
        raise HTTPException(status_code=409, detail="Report generation already in progress")

    if body.idea is not None:
        scope = assess_topic_scope(
            body.idea or "",
            body.industry or workspace.get("industry") or "",
            body.country or workspace.get("country") or "Global",
        )
        workspace = update_workspace_intake(
            body.workspace_id,
            idea=body.idea or "",
            industry=body.industry or str(workspace.get("industry") or ""),
            country=body.country or str(workspace.get("country") or "Global"),
            areas=body.areas if body.areas is not None else str(workspace.get("areas") or ""),
            scope_assessment=scope,
        )
        if not workspace:
            raise HTTPException(status_code=404, detail="Project not found")

    topic = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "").strip()
    geography = str(workspace.get("country") or "Global").strip()
    areas = str(workspace.get("areas") or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Project is missing a topic")

    scope = workspace.get("scope_assessment") if isinstance(workspace.get("scope_assessment"), dict) else {}
    if not scope:
        scope = assess_topic_scope(topic, industry, geography)
        workspace["scope_assessment"] = scope
        save_workspace(workspace)
    if not scope.get("ok"):
        raise HTTPException(status_code=400, detail={"issues": scope.get("issues", [])})

    if body.section_count not in SIMPLE_SECTION_COUNTS:
        raise HTTPException(status_code=400, detail="Invalid section count")

    workspace["research_job"] = {
        "status": "running",
        "section_count": body.section_count,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    save_workspace(workspace)

    thread = threading.Thread(
        target=_run_research_background,
        args=(body.workspace_id, body.section_count, topic, industry, geography, areas),
        daemon=True,
    )
    thread.start()

    return {
        "success": False,
        "status": "running",
        "message": "Report generation started. This usually takes several minutes.",
        "section_count": body.section_count,
    }
