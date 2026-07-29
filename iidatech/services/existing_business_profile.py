"""Existing operating business intake for business builder (GAUGE-aligned)."""

from __future__ import annotations



import json

import re

from typing import Any



from iidatech.services.gauge_intake import (

    collect_gauge_checklist_state,

    gauge_checklist_prompt_lines,

    gauge_checklist_summary,

    gauge_type_label,

)



BUSINESS_STAGE_NEW = "new"

BUSINESS_STAGE_EXISTING = "existing"



PLAN_PURPOSE_OPTIONS = [

    "Growth / expansion plan",

    "Bank loan / MSME loan",

    "Investor fundraising",

    "Visa / immigration",

    "Grant application",

    "Internal strategy",

    "Other",

]





def _clean(value: Any, *, limit: int = 4000) -> str:

    return re.sub(r"\s+", " ", str(value or "")).strip()[:limit]





def _num(value: Any) -> str:

    text = _clean(value, limit=80)

    if not text:

        return ""

    digits = re.sub(r"[^\d.\-]", "", text.replace(",", ""))

    return digits or text





def collect_existing_business_profile(st: Any) -> dict[str, Any]:

    gauge_type = _clean(st.session_state.get("existing_biz_gauge_type") or "other")

    checklist_state = collect_gauge_checklist_state(st, gauge_type)

    months = _num(st.session_state.get("existing_biz_months_in_operation"))

    years = ""

    if months:

        try:

            years = str(round(float(months) / 12, 1))

        except (TypeError, ValueError):

            years = months

    monthly_rev = _num(st.session_state.get("existing_biz_monthly_revenue"))

    monthly_cost = _num(st.session_state.get("existing_biz_monthly_costs"))

    team_size = _num(st.session_state.get("existing_biz_team_size"))

    industry = _clean(st.session_state.get("existing_biz_industry")) or gauge_type_label(gauge_type)

    geography = _clean(st.session_state.get("existing_biz_geography"))

    company_name = _clean(st.session_state.get("existing_biz_company_name"))

    website = _clean(st.session_state.get("existing_biz_website"))

    public_links = _clean(st.session_state.get("existing_biz_public_links"), limit=2000)

    competitors = _clean(st.session_state.get("existing_biz_competitors"), limit=2000)

    gauge_notes = _clean(st.session_state.get("existing_biz_gauge_notes"), limit=12000)

    description = _clean(st.session_state.get("existing_biz_description"), limit=8000)

    if not description and company_name:

        description = f"{gauge_type_label(gauge_type)} business operating as {company_name}."

    annual = ""

    if monthly_rev:

        try:

            annual = str(round(float(monthly_rev) * 12, 2))

        except (TypeError, ValueError):

            annual = ""

    return {

        "business_stage": BUSINESS_STAGE_EXISTING,

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

        "currency": _clean(st.session_state.get("existing_biz_currency") or "USD"),

        "monthly_revenue": monthly_rev,

        "monthly_costs": monthly_cost,

        "annual_revenue": annual,

        "monthly_opex": monthly_cost,

        "active_customers": _num(st.session_state.get("existing_biz_active_customers")),

        "customer_churn_pct": _num(st.session_state.get("existing_biz_churn_pct")),

        "employees_ft": team_size,

        "main_competitors": competitors,

        "gauge_notes": gauge_notes,

        "plan_purpose": _clean(st.session_state.get("existing_biz_plan_purpose")),

        "target_revenue_year_3": _num(st.session_state.get("existing_biz_target_revenue_y3")),

        "funding_amount_needed": _num(st.session_state.get("existing_biz_funding_needed")),

        "growth_goal_12_24m": _clean(st.session_state.get("existing_biz_growth_goal"), limit=2000),

        "gauge_checklist_state": checklist_state,

        "gauge_checklist_summary": gauge_checklist_summary(gauge_type, checklist_state),

        "gauge_checklist_prompt": gauge_checklist_prompt_lines(gauge_type, checklist_state),

    }





def validate_existing_business_profile(profile: dict[str, Any]) -> list[str]:

    errors: list[str] = []

    if not profile.get("gauge_business_type"):

        errors.append("Select what kind of business this is (Step 1).")

    if not profile.get("company_name"):

        errors.append("Enter your company name (Step 3).")

    if not profile.get("geography"):

        errors.append("Enter your primary market / geography (Step 3).")

    has_signal = any(

        profile.get(key)

        for key in (

            "monthly_revenue",

            "monthly_costs",

            "active_customers",

            "gauge_notes",

            "website",

        )

    )

    if not has_signal:

        errors.append("Add at least one metric, website, or notes in Step 3 so the plan can ground on real data.")

    return errors





def profile_to_planning_idea(profile: dict[str, Any]) -> str:

    company = profile.get("company_name") or "Existing business"

    desc = profile.get("business_description") or ""

    biz_type = profile.get("gauge_business_type_label") or profile.get("industry") or "business"

    parts = [

        f"{company}: {desc}".strip(": "),

        f"{biz_type} — operating business ({profile.get('months_in_operation') or profile.get('years_operating') or 'unknown'} months/years in market).",

    ]

    currency = profile.get("currency") or "USD"

    if profile.get("monthly_revenue"):

        parts.append(f"Monthly revenue: {currency} {profile['monthly_revenue']}.")

    elif profile.get("annual_revenue"):

        parts.append(f"Annual revenue: {currency} {profile['annual_revenue']}.")

    if profile.get("monthly_costs"):

        parts.append(f"Monthly costs: {currency} {profile['monthly_costs']}.")

    if profile.get("active_customers"):

        parts.append(f"Active customers: {profile['active_customers']}.")

    if profile.get("customer_churn_pct"):

        parts.append(f"Monthly churn: {profile['customer_churn_pct']}%.")

    if profile.get("employees_ft"):

        parts.append(f"Team size: {profile['employees_ft']}.")

    if profile.get("growth_goal_12_24m"):

        parts.append(f"Growth goal: {profile['growth_goal_12_24m']}.")

    if profile.get("plan_purpose"):

        parts.append(f"Plan purpose: {profile['plan_purpose']}.")

    return " ".join(p for p in parts if p)





def profile_to_structured_summary(profile: dict[str, Any]) -> dict[str, Any]:

    annual = profile.get("annual_revenue")

    monthly = profile.get("monthly_revenue")

    if not annual and monthly:

        try:

            annual = str(round(float(monthly) * 12, 2))

        except (TypeError, ValueError):

            pass

    return {

        "business_stage": BUSINESS_STAGE_EXISTING,

        "gauge_business_type": profile.get("gauge_business_type"),

        "gauge_business_type_label": profile.get("gauge_business_type_label"),

        "company_identity": {

            "company_name": profile.get("company_name"),

            "website": profile.get("website"),

            "public_links": profile.get("public_links"),

        },

        "months_in_operation": profile.get("months_in_operation"),

        "years_operating": profile.get("years_operating"),

        "currency": profile.get("currency") or "USD",

        "reported_actuals": {

            "annual_revenue": annual,

            "monthly_revenue": monthly,

            "monthly_costs": profile.get("monthly_costs"),

            "monthly_opex": profile.get("monthly_opex"),

            "active_customers": profile.get("active_customers"),

            "customer_churn_pct": profile.get("customer_churn_pct"),

            "employees_ft": profile.get("employees_ft"),

            "target_revenue_year_3": profile.get("target_revenue_year_3"),

            "funding_amount_needed": profile.get("funding_amount_needed"),

        },

        "gauge_checklist": profile.get("gauge_checklist_summary") or {},

        "go_to_market_actuals": {

            "main_competitors": profile.get("main_competitors"),

        },

        "strategic_context": {

            "growth_goal_12_24m": profile.get("growth_goal_12_24m"),

            "plan_purpose": profile.get("plan_purpose"),

            "gauge_notes_excerpt": (profile.get("gauge_notes") or "")[:1200],

        },

    }





def profile_to_evidence_item(profile: dict[str, Any]) -> dict[str, Any]:

    summary = profile_to_structured_summary(profile)

    narrative = profile_to_planning_idea(profile)

    body = (

        f"{narrative}\n\n"

        f"Business type: {profile.get('gauge_business_type_label')}\n\n"

        f"GAUGE checklist (has / missing):\n{profile.get('gauge_checklist_prompt') or ''}\n\n"

        f"Company identity: website={profile.get('website') or 'n/a'}; links={profile.get('public_links') or 'n/a'}\n\n"

        f"Notes / pasted data:\n{(profile.get('gauge_notes') or '')[:8000]}\n\n"

        f"Structured operating metrics (founder-reported):\n"

        f"{json.dumps(summary, indent=2, ensure_ascii=False)}"

    )

    return {

        "name": f"existing_business_profile_{profile.get('company_name', 'company')}",

        "kind": "existing_business_intake",

        "mime": "application/json",

        "bytes": len(body.encode("utf-8")),

        "text": body[:16000],

        "notes": ["existing operating business intake", "use reported metrics as financial baseline"],

        "structured_profile": summary,

    }





def existing_business_prompt_section(profile: dict[str, Any] | None) -> str:

    if not profile or profile.get("business_stage") != BUSINESS_STAGE_EXISTING:

        return ""

    from iidatech.services.gauge_audit import gauge_audit_prompt_section



    summary = profile_to_structured_summary(profile)

    audit_section = gauge_audit_prompt_section(profile.get("gauge_audit"))

    forward = profile.get("plan_forward") or {}

    forward_block = ""

    if forward:

        forward_block = (

            "FORWARD PLAN INTENT (founder stated):\n"

            + "\n".join(f"- {k.replace('_', ' ')}: {v}" for k, v in forward.items() if v)

            + "\n\n"

        )

    return (

        "EXISTING OPERATING BUSINESS MODE — GAUGE health instrument intake (mandatory):\n"

        "- This is NOT a greenfield startup idea. The company already operates with reported actuals.\n"

        "- Use the GAUGE checklist Has/Missing signals to prioritize gaps in financial_model, operations, GTM, and hiring_plan.\n"

        "- Ground financial_model, founder_financial_breakdown, and startup_budget in monthly revenue/costs and customer metrics below.\n"

        "- Project forward from current revenue, costs, headcount, and customer base — do not ignore founder numbers.\n"

        "- first_90_day_plan must close the highest-impact Missing checklist items while pursuing the stated growth goal.\n"

        "- If website or public links are provided, use them for company context; if identity is thin, label assumptions clearly.\n"

        "- competitor sections must use named competitors from intake when provided.\n\n"

        f"{audit_section}"

        f"{forward_block}"

        f"Business type: {profile.get('gauge_business_type_label')}\n\n"

        f"CHECKLIST (what the owner says is / isn't in place):\n{profile.get('gauge_checklist_prompt') or 'none'}\n\n"

        f"Founder-reported operating business profile:\n{json.dumps(summary, indent=2, ensure_ascii=False)[:12000]}\n\n"

    )





def merge_existing_profile_evidence(

    evidence_items: list[dict] | None,

    profile: dict[str, Any] | None,

) -> list[dict]:

    items = list(evidence_items or [])

    if not profile or profile.get("business_stage") != BUSINESS_STAGE_EXISTING:

        return items

    item = profile_to_evidence_item(profile)

    return [item] + [x for x in items if x.get("kind") != "existing_business_intake"]

