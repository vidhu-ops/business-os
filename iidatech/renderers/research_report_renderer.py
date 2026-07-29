"""Structured research report renderer — answers 10 funding diligence questions."""
from __future__ import annotations

from typing import Any

_VALIDATION = "VALIDATION REQUIRED"

_FUNDING_QUESTIONS = [
    "Is the market large enough (TAM/SAM/SOM with denominators)?",
    "Who are the credible competitors and how crowded is the market?",
    "What pricing bands exist and where is the wedge?",
    "What do buyers pain about and what do they want?",
    "Will buyers pay — what is WTP evidence?",
    "Are unit economics viable (CAC, LTV, margin, payback)?",
    "Is the business model structurally valid (COGS vs price)?",
    "What is the best wedge and positioning?",
    "What is the fastest path to first revenue?",
    "What moat or defensibility is evidence-backed?",
]


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _fmt_money(v: Any) -> str:
    if v in (None, "", "WITHHELD"):
        return _VALIDATION
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def _answer_funding_questions(
    topic: str,
    industry: str,
    geography: str,
    comp: dict,
    cust: dict,
    fin: dict,
    strat: dict,
) -> list[dict[str, str]]:
    tam = _as_dict(fin.get("tam"))
    sam = _as_dict(fin.get("sam"))
    som = _as_dict(fin.get("som"))
    ue = _as_dict(fin.get("unit_economics"))

    answers = [
        {
            "question": _FUNDING_QUESTIONS[0],
            "answer": (
                f"TAM {_fmt_money(tam.get('value') or tam.get('tam'))}; "
                f"SAM {_fmt_money(sam.get('value'))}; SOM {_fmt_money(som.get('value'))}"
                if tam.get("computed") or tam.get("value")
                else _VALIDATION
            ),
        },
        {
            "question": _FUNDING_QUESTIONS[1],
            "answer": (
                f"{comp.get('competitor_count', 0)} competitors; leaders: {', '.join(comp.get('market_leaders') or []) or _VALIDATION}"
            ),
        },
        {
            "question": _FUNDING_QUESTIONS[2],
            "answer": (
                f"Low {_fmt_money(comp.get('low_cost_pricing'))}; "
                f"Avg {_fmt_money(comp.get('avg_pricing'))}; "
                f"Premium {_fmt_money(comp.get('premium_pricing'))}"
                if comp.get("avg_pricing") is not None
                else _VALIDATION
            ),
        },
        {
            "question": _FUNDING_QUESTIONS[3],
            "answer": (
                "; ".join(
                    f"{p.get('category')}: {p.get('sample', '')[:80]}"
                    for p in (cust.get("top_pains") or [])[:3]
                )
                or _VALIDATION
            ),
        },
        {
            "question": _FUNDING_QUESTIONS[4],
            "answer": str(cust.get("wtp_distribution") or _VALIDATION),
        },
        {
            "question": _FUNDING_QUESTIONS[5],
            "answer": (
                f"CAC {_fmt_money(ue.get('cac'))}; LTV {_fmt_money(ue.get('ltv'))}; "
                f"Margin {ue.get('margin') or _VALIDATION}%; Payback {ue.get('payback_months') or _VALIDATION} mo"
            ),
        },
        {
            "question": _FUNDING_QUESTIONS[6],
            "answer": (
                "Invalid: " + "; ".join(fin.get("invalid_business_model_reasons") or ["none"])
                if fin.get("invalid_business_model")
                else "Structurally plausible from dataset COGS vs pricing anchors"
            ),
        },
        {
            "question": _FUNDING_QUESTIONS[7],
            "answer": str(strat.get("best_wedge") or strat.get("wedge") or _VALIDATION),
        },
        {
            "question": _FUNDING_QUESTIONS[8],
            "answer": "; ".join(strat.get("first_revenue_path") or strat.get("fast_revenue_path") or [_VALIDATION]),
        },
        {
            "question": _FUNDING_QUESTIONS[9],
            "answer": "; ".join(strat.get("moat_strategy") or [_VALIDATION]),
        },
    ]
    return answers


def render_structured_research_report(
    topic: str,
    industry: str,
    geography: str,
    brain_output: dict[str, Any],
) -> dict[str, Any]:
    """Render funding-grade structured report from research brain output."""
    comp = _as_dict(brain_output.get("competitor_map"))
    cust = _as_dict(brain_output.get("customer_truth"))
    fin = _as_dict(brain_output.get("financial_truth"))
    strat = _as_dict(brain_output.get("strategic_recommendations"))
    market = _as_dict(brain_output.get("market_truth"))

    funding_answers = _answer_funding_questions(topic, industry, geography, comp, cust, fin, strat)

    executive_summary = {
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "vertical": market.get("vertical"),
        "headline": (
            f"Dataset-grounded diligence for {topic} in {geography} ({industry}). "
            f"Confidence {brain_output.get('confidence_score', 0)}/100."
        ),
        "funding_question_answers": funding_answers,
    }

    tam = _as_dict(fin.get("tam"))
    financial_analysis = {
        "tam": tam,
        "sam": _as_dict(fin.get("sam")),
        "som": _as_dict(fin.get("som")),
        "unit_economics": _as_dict(fin.get("unit_economics")),
        "invalid_business_model": fin.get("invalid_business_model", False),
        "notes": _VALIDATION if not tam.get("computed") and not tam.get("value") else "Computed from denominators",
    }

    return {
        "executive_summary": executive_summary,
        "market_truth": market,
        "competitor_analysis": {
            "matrix": comp.get("competitor_matrix") or [],
            "pricing_bands": comp.get("pricing_bands") or {},
            "market_leaders": comp.get("market_leaders") or [],
            "weak_competitors": comp.get("weak_competitors") or [],
            "market_gaps": comp.get("market_gaps") or [],
            "feature_gap": comp.get("feature_gap") or [],
        },
        "customer_analysis": {
            "top_pains": cust.get("top_pains") or [],
            "top_desires": cust.get("top_desires") or [],
            "wtp_distribution": cust.get("wtp_distribution") or {},
            "dominant_objections": cust.get("dominant_objections") or [],
        },
        "financial_analysis": financial_analysis,
        "strategic_recommendations": {
            "best_wedge": strat.get("best_wedge") or strat.get("wedge"),
            "positioning": strat.get("positioning") or {},
            "launch_strategy": strat.get("launch_strategy") or strat.get("gtm") or [],
            "first_revenue_path": strat.get("first_revenue_path") or strat.get("fast_revenue_path") or [],
            "moat_strategy": strat.get("moat_strategy") or [],
        },
        "risks": brain_output.get("risk_flags") or [],
        "missing_evidence": brain_output.get("missing_evidence") or [],
        "confidence_score": brain_output.get("confidence_score", 0),
        "funding_questions": _FUNDING_QUESTIONS,
    }