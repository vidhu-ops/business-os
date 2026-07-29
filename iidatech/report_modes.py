"""Explicit IIDATECH customer report modes — strict section gating by product intent."""
from __future__ import annotations

import copy
import re
from typing import Any

REPORT_MODE_RESEARCH = "research"
REPORT_MODE_BUSINESS_BUILDER = "business_builder"
REPORT_MODE_INVESTOR_MEMO = "investor_memo"

VALID_REPORT_MODES = frozenset(
    {
        REPORT_MODE_RESEARCH,
        REPORT_MODE_BUSINESS_BUILDER,
        REPORT_MODE_INVESTOR_MEMO,
    }
)

MODE_LABELS: dict[str, str] = {
    REPORT_MODE_RESEARCH: "Research Report",
    REPORT_MODE_BUSINESS_BUILDER: "Business Builder",
    REPORT_MODE_INVESTOR_MEMO: "Investor Memo",
}

_WORKFLOW_TO_MODE: dict[str, str] = {
    "Understand your market": REPORT_MODE_RESEARCH,
    "Research a market": REPORT_MODE_RESEARCH,
    "Turn idea into business plan": REPORT_MODE_BUSINESS_BUILDER,
    "Run business execution": REPORT_MODE_BUSINESS_BUILDER,
}

_INVESTOR_QUERY_HINTS = (
    "investor",
    "investment",
    "funding",
    "venture",
    "diligence",
    "investable",
    "cap table",
    "series a",
    "seed round",
)
_BUILDER_QUERY_HINTS = (
    "business plan",
    "launch plan",
    "go-to-market",
    "go to market",
    "gtm",
    "execution plan",
    "90 day",
    "90-day",
    "hiring plan",
)

# V3 object top-level section keys
_RESEARCH_V3_SECTIONS = frozenset(
    {
        "schema_version",
        "topic",
        "industry",
        "geography",
        "report_mode",
        "market_truth",
        "customer_truth",
        "competitor_truth",
        "pricing_truth",
        "report_truth_confidence",
        "data_provenance",
        "truth_policy",
    }
)

_BUSINESS_BUILDER_V3_SECTIONS = _RESEARCH_V3_SECTIONS | frozenset(
    {
        "go_to_market",
        "execution_plan",
        "execution_calendar",
        "risk_map",
    }
)

_INVESTOR_V3_SECTIONS = _RESEARCH_V3_SECTIONS | frozenset(
    {
        "unit_economics",
        "risk_map",
        "risk_heatmap",
        "investment_verdict",
        "executive_verdict",
        "go_to_market",
    }
)

_PAYLOAD_STRIP_BY_MODE: dict[str, frozenset[str]] = {
    REPORT_MODE_RESEARCH: frozenset(
        {
            "business_blueprint",
            "execution_blueprint",
            "boardroom_strategist",
            "investment_decision",
            "employee_os",
            "hiring_plan",
        }
    ),
    REPORT_MODE_BUSINESS_BUILDER: frozenset(
        {
            "boardroom_strategist",
            "investment_decision",
            "employee_os",
        }
    ),
    REPORT_MODE_INVESTOR_MEMO: frozenset(
        {
            "execution_blueprint",
            "employee_os",
            "business_plan",
        }
    ),
}


def normalize_report_mode(value: Any) -> str | None:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "research": REPORT_MODE_RESEARCH,
        "research_report": REPORT_MODE_RESEARCH,
        "market_research": REPORT_MODE_RESEARCH,
        "business_builder": REPORT_MODE_BUSINESS_BUILDER,
        "business_plan": REPORT_MODE_BUSINESS_BUILDER,
        "builder": REPORT_MODE_BUSINESS_BUILDER,
        "investor_memo": REPORT_MODE_INVESTOR_MEMO,
        "investor": REPORT_MODE_INVESTOR_MEMO,
        "investment_memo": REPORT_MODE_INVESTOR_MEMO,
        "funding": REPORT_MODE_INVESTOR_MEMO,
    }
    if raw in VALID_REPORT_MODES:
        return raw
    return aliases.get(raw)


def infer_report_mode(
    user_query: str,
    selected_mode: str | None = None,
    *,
    workflow_choice: str | None = None,
) -> str:
    normalized = normalize_report_mode(selected_mode)
    if normalized:
        return normalized
    if workflow_choice and workflow_choice in _WORKFLOW_TO_MODE:
        return _WORKFLOW_TO_MODE[workflow_choice]
    q = re.sub(r"\s+", " ", str(user_query or "").strip().lower())
    if any(hint in q for hint in _INVESTOR_QUERY_HINTS):
        return REPORT_MODE_INVESTOR_MEMO
    if any(hint in q for hint in _BUILDER_QUERY_HINTS):
        return REPORT_MODE_BUSINESS_BUILDER
    return REPORT_MODE_RESEARCH


def allowed_sections_for_mode(mode: str) -> frozenset[str]:
    normalized = normalize_report_mode(mode) or REPORT_MODE_RESEARCH
    if normalized == REPORT_MODE_BUSINESS_BUILDER:
        return _BUSINESS_BUILDER_V3_SECTIONS
    if normalized == REPORT_MODE_INVESTOR_MEMO:
        return _INVESTOR_V3_SECTIONS
    return _RESEARCH_V3_SECTIONS


def _slim_gtm_for_investor(gtm: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(gtm, dict):
        return {}
    return {
        "moat": gtm.get("moat"),
        "positioning": gtm.get("positioning"),
        "vertical": gtm.get("vertical"),
    }


def filter_v3_report_object(report_object: dict[str, Any], mode: str) -> dict[str, Any]:
    obj = copy.deepcopy(report_object if isinstance(report_object, dict) else {})
    allowed = allowed_sections_for_mode(mode)
    filtered = {k: v for k, v in obj.items() if k in allowed}
    filtered["report_mode"] = normalize_report_mode(mode) or REPORT_MODE_RESEARCH
    if filtered["report_mode"] == REPORT_MODE_INVESTOR_MEMO and "go_to_market" in filtered:
        filtered["go_to_market"] = _slim_gtm_for_investor(filtered.get("go_to_market") or {})
    return filtered


def filter_payload_by_mode(payload: dict[str, Any], mode: str) -> dict[str, Any]:
    out = copy.deepcopy(payload if isinstance(payload, dict) else {})
    normalized = normalize_report_mode(mode) or REPORT_MODE_RESEARCH
    out["report_mode"] = normalized
    for key in _PAYLOAD_STRIP_BY_MODE.get(normalized, frozenset()):
        out.pop(key, None)

    if normalized == REPORT_MODE_RESEARCH:
        diligence = out.get("diligence_pack")
        if isinstance(diligence, dict):
            diligence.pop("funding_readiness_pack", None)
        bp = out.get("business_blueprint")
        if isinstance(bp, dict):
            bp.pop("hiring_plan", None)
            bp.pop("funding_plan", None)
            bp.pop("go_to_market", None)
            out["business_blueprint"] = bp

    if normalized == REPORT_MODE_BUSINESS_BUILDER:
        out.pop("final_report_audit", None)
        inv = out.get("investment_decision")
        if isinstance(inv, dict):
            inv.pop("investment_score", None)
            inv.pop("verdict", None)
            out["investment_decision"] = inv

    if normalized == REPORT_MODE_INVESTOR_MEMO:
        out.pop("execution_plan", None)
        bp = out.get("business_blueprint")
        if isinstance(bp, dict):
            bp.pop("hiring_plan", None)
            bp.pop("execution_tasks", None)
            out["business_blueprint"] = bp

    return out


def stamp_report_mode(payload: dict[str, Any], *, user_query: str = "", selected_mode: str | None = None, workflow_choice: str | None = None) -> str:
    mode = infer_report_mode(user_query, selected_mode, workflow_choice=workflow_choice)
    payload["report_mode"] = mode
    return mode


def mode_allows_section(mode: str, section_key: str) -> bool:
    return section_key in allowed_sections_for_mode(mode)