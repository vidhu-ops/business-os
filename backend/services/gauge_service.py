from __future__ import annotations

from typing import Any

from backend.services.plan_builder import build_business_plan
from backend.services.workspace_context import workspace_report_context
from iidatech.services.existing_business_profile import (
    PLAN_PURPOSE_OPTIONS,
    profile_to_planning_idea,
    validate_existing_business_profile,
)
from iidatech.services.gauge_audit import gauge_audit_prompt_section, merge_gauge_audit_into_profile, run_gauge_audit
from iidatech.services.gauge_intake import GAUGE_BUSINESS_TYPES, GAUGE_CHECKLISTS, gauge_checklist_prompt_lines, gauge_checklist_summary, gauge_type_label
from iidatech.llm.text_request import llm_text_request


def gauge_metadata() -> dict[str, Any]:
    return {
        "business_types": GAUGE_BUSINESS_TYPES,
        "checklists": GAUGE_CHECKLISTS,
        "plan_purpose_options": PLAN_PURPOSE_OPTIONS,
        "step_labels": ["Business", "Checklist", "Data", "Forward", "Report"],
    }


def _clean(value: Any, *, limit: int = 4000) -> str:
    import re

    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]


def _num(value: Any) -> str:
    import re

    text = _clean(value, limit=80)
    if not text:
        return ""
    digits = re.sub(r"[^\d.\-]", "", text.replace(",", ""))
    return digits or text


def profile_from_draft(draft: dict[str, Any]) -> dict[str, Any]:
    gauge_type = _clean(draft.get("gauge_type") or "other")
    checklist_state = (draft.get("checklists") or {}).get(gauge_type) or {}
    months = _num(draft.get("months_in_operation"))
    years = ""
    if months:
        try:
            years = str(round(float(months) / 12, 1))
        except (TypeError, ValueError):
            years = months
    monthly_rev = _num(draft.get("monthly_revenue"))
    monthly_cost = _num(draft.get("monthly_costs"))
    team_size = _num(draft.get("team_size"))
    industry = _clean(draft.get("industry")) or gauge_type_label(gauge_type)
    geography = _clean(draft.get("geography"))
    company_name = _clean(draft.get("company_name"))
    website = _clean(draft.get("website"))
    public_links = _clean(draft.get("public_links"), limit=2000)
    competitors = _clean(draft.get("competitors"), limit=2000)
    gauge_notes = _clean(draft.get("gauge_notes"), limit=12000)
    description = _clean(draft.get("description"), limit=8000)
    if not description and company_name:
        description = f"{gauge_type_label(gauge_type)} business operating as {company_name}."
    annual = ""
    if monthly_rev:
        try:
            annual = str(round(float(monthly_rev) * 12, 2))
        except (TypeError, ValueError):
            annual = ""
    plan_forward = draft.get("plan_forward") if isinstance(draft.get("plan_forward"), dict) else {}
    return {
        "business_stage": "existing",
        "gauge_business_type": gauge_type,
        "gauge_business_type_label": gauge_type_label(gauge_type),
        "company_name": company_name,
        "website": website,
        "public_links": public_links,
        "business_description": description,
        "industry": industry,
        "geography": geography,
        "months_in_operation": months,
        "years_operating": years,
        "currency": _clean(draft.get("currency") or "USD"),
        "monthly_revenue": monthly_rev,
        "monthly_costs": monthly_cost,
        "annual_revenue": annual,
        "monthly_opex": monthly_cost,
        "active_customers": _num(draft.get("active_customers")),
        "customer_churn_pct": _num(draft.get("churn_pct")),
        "employees_ft": team_size,
        "main_competitors": competitors,
        "gauge_notes": gauge_notes,
        "plan_purpose": _clean(draft.get("plan_purpose")),
        "target_revenue_year_3": _num(draft.get("target_revenue_y3")),
        "funding_amount_needed": _num(draft.get("funding_needed")),
        "growth_goal_12_24m": _clean(draft.get("growth_goal"), limit=2000),
        "gauge_checklist_state": checklist_state,
        "gauge_checklist_summary": gauge_checklist_summary(gauge_type, checklist_state),
        "gauge_checklist_prompt": gauge_checklist_prompt_lines(gauge_type, checklist_state),
        "plan_forward": {
            "biggest_bottleneck": _clean(plan_forward.get("biggest_bottleneck"), limit=2000),
            "priority_12_months": _clean(plan_forward.get("priority_12_months"), limit=2000),
            "success_12_months": _clean(plan_forward.get("success_12_months"), limit=2000),
            "willing_to_invest": _clean(plan_forward.get("willing_to_invest"), limit=2000),
            "stop_doing": _clean(plan_forward.get("stop_doing"), limit=2000),
            "why_customers_choose": _clean(plan_forward.get("why_customers_choose"), limit=2000),
            "why_customers_leave": _clean(plan_forward.get("why_customers_leave"), limit=2000),
            "competitive_threat": _clean(plan_forward.get("competitive_threat"), limit=2000),
        },
        "intake_source": "existing_company_plan_forward",
    }


def _text_request(prompt: str, system: str, max_tokens: int = 2048, temperature: float = 0.1) -> tuple[str, str]:
    try:
        return llm_text_request(prompt, system, max_tokens=max_tokens, temperature=temperature)
    except Exception:
        return "", "fallback"


def run_audit_for_profile(profile: dict[str, Any]) -> dict[str, Any]:
    has_identity = bool(str(profile.get("company_name") or "").strip() or str(profile.get("website") or "").strip())
    return run_gauge_audit(profile, _text_request, include_market_search=has_identity)


def build_forward_plan(workspace: dict[str, Any], profile_with_audit: dict[str, Any]) -> dict[str, Any]:
    idea = profile_to_planning_idea(profile_with_audit)
    workspace = dict(workspace)
    workspace["idea"] = idea
    workspace["industry"] = str(profile_with_audit.get("industry") or workspace.get("industry") or "General")
    workspace["country"] = str(profile_with_audit.get("geography") or workspace.get("country") or "Global")
    workspace["application_purpose"] = str(profile_with_audit.get("plan_purpose") or "Internal strategy")
    workspace["business_builder_is_existing"] = True
    workspace["existing_business_profile"] = profile_with_audit
    ctx = workspace_report_context(workspace)
    ctx["existing_business_profile"] = profile_with_audit
    audit = profile_with_audit.get("gauge_audit") if isinstance(profile_with_audit.get("gauge_audit"), dict) else {}
    ctx["gauge_audit_prompt"] = gauge_audit_prompt_section(audit)
    workspace["_report_context_override"] = ctx
    result = build_business_plan(workspace)
    if result.get("success"):
        result["gauge_audit"] = audit
        result["plan_forward_profile"] = profile_with_audit
        result["idea"] = idea
    return result


def validate_draft(draft: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    profile = profile_from_draft(draft)
    return validate_existing_business_profile(profile), profile
