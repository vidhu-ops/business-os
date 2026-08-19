from __future__ import annotations

import hashlib
from typing import Any


def workspace_report_id(workspace: dict[str, Any]) -> str:
    topic = str(workspace.get("idea") or "").strip()
    geo = str(workspace.get("country") or "Global").strip()
    raw = f"{topic}|{geo}".strip().lower()
    return f"os2_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


def simple_research_to_report_context(result: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(result, dict) or not result.get("success"):
        return {}
    markdown = str(result.get("report_markdown") or result.get("markdown") or "")
    comp_truth: dict[str, Any] = {}
    try:
        from iidatech.services.perplexity_report_engine import competitor_truth_from_report

        comp_truth = competitor_truth_from_report(result)
    except Exception:
        pass
    return {
        "topic": result.get("topic"),
        "industry": result.get("industry"),
        "geography": result.get("geography"),
        "country": result.get("geography"),
        "areas": result.get("areas") or "",
        "market_label": result.get("market_label") or result.get("geography"),
        "source": "iidatech_market_research",
        "report_markdown": markdown[:12000],
        "evidence_gaps": list(result.get("evidence_gaps") or []),
        "competitor_truth": comp_truth,
        "report_v3": result,
        "topic_intelligence_brief": {
            "source": "iidatech_market_research",
            "report_excerpt": markdown[:12000],
        },
    }


def workspace_report_context(workspace: dict[str, Any]) -> dict[str, Any]:
    idea = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or "Global").strip()
    areas = str(workspace.get("areas") or "").strip()
    try:
        from iidatech.services.perplexity_report_engine import format_market_geography

        market_label = format_market_geography(geography, areas)
    except Exception:
        market_label = geography

    ctx: dict[str, Any] = {
        "topic": idea,
        "idea": idea,
        "industry": industry,
        "geography": geography,
        "country": geography,
        "areas": areas,
        "market_label": market_label,
    }

    research = workspace.get("research_report") if isinstance(workspace.get("research_report"), dict) else {}
    full = research.get("full_result") if isinstance(research.get("full_result"), dict) else {}
    if full.get("success"):
        ctx.update(simple_research_to_report_context(full))
    elif research.get("available"):
        md = str(research.get("report_markdown") or research.get("markdown") or "")
        if md:
            ctx["report_markdown"] = md[:12000]
            ctx["source"] = "iidatech_market_research"

    plan = workspace.get("business_plan") if isinstance(workspace.get("business_plan"), dict) else {}
    if isinstance(plan.get("plan_json"), dict) and plan["plan_json"]:
        ctx["business_plan"] = plan["plan_json"]

    # Organizational memory — research, plan, and agents all see this context.
    try:
        from backend.services import org_memory as om

        profile = om.effective_business_profile(workspace)
        ctx["business_profile"] = profile
        ctx["org_memory_prompt"] = om.profile_prompt_block(profile)
        ctx["integrations"] = om.effective_integrations(workspace)
        ebp = workspace.get("existing_business_profile")
        if isinstance(ebp, dict) and ebp:
            ctx["existing_business_profile"] = ebp
        owner = str(workspace.get("owner_email") or "")
        loop = om.execution_loop_snapshot(workspace, owner)
        ctx["execution_loop"] = {
            "phase": loop.get("phase"),
            "goal_progress_avg": loop.get("goal_progress_avg"),
            "goals": loop.get("goals") or [],
            "pending_approvals": loop.get("pending_approvals") or [],
        }
    except Exception:
        pass

    return ctx