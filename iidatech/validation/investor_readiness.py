"""Investor-ready verdict for research reports (no Claude 10/10 required)."""
from __future__ import annotations

import re
from typing import Any

INVESTOR_READY_SECTION_AVG = 7.0
INVESTOR_READY_SECTION_MIN = 5.5
INVESTOR_READY_REPORT_SCORE = 7.0


def _num(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "queued"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def merge_eval_scores(report: dict, eval_scores: dict | None) -> dict:
    """Merge checkpoint/payload quality_scores with in-run eval_scores."""
    merged: dict = {}
    for source in (report.get("quality_scores"), eval_scores):
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            if isinstance(value, dict):
                merged[key] = value
    return merged


def _collect_numeric_section_scores(eval_scores: dict) -> list[float]:
    numeric_scores: list[float] = []
    for ev in (eval_scores or {}).values():
        if not isinstance(ev, dict):
            continue
        score = ev.get("overall_score")
        if isinstance(score, (int, float)):
            numeric_scores.append(float(score))
    return numeric_scores


def assess_investor_readiness(
    report: dict,
    eval_scores: dict,
    local_audit: dict,
    *,
    section_avg_target: float = INVESTOR_READY_SECTION_AVG,
    section_min_target: float = INVESTOR_READY_SECTION_MIN,
    report_score_target: float = INVESTOR_READY_REPORT_SCORE,
) -> dict:
    merged_scores = merge_eval_scores(report, eval_scores)
    numeric_scores = _collect_numeric_section_scores(merged_scores)

    avg_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0.0
    min_score = min(numeric_scores) if numeric_scores else 0.0
    market_score = _num(local_audit.get("market_style_score"), avg_score)
    honesty_audit = local_audit.get("honesty_audit") if isinstance(local_audit.get("honesty_audit"), dict) else {}
    honest_score = _num(honesty_audit.get("honest_score"), market_score)
    honesty_enforced = bool(honesty_audit.get("honesty_enforced"))
    caps_applied = [c for c in (honesty_audit.get("caps_applied") or []) if isinstance(c, dict)]

    if numeric_scores:
        raw_blended = round(max(market_score, avg_score), 1)
        effective_report_score = min(raw_blended, honest_score) if honesty_enforced else raw_blended
    else:
        effective_report_score = honest_score if honesty_enforced else market_score

    diligence = report.get("diligence_pack") if isinstance(report.get("diligence_pack"), dict) else {}
    live_count = int(diligence.get("live_competitor_count") or 0)
    if live_count < 2:
        serp = diligence.get("serp_intelligence") or diligence.get("live_serp") or {}
        if isinstance(serp, dict):
            competitors = serp.get("competitors") or serp.get("live_competitors") or []
            if isinstance(competitors, list):
                live_count = max(live_count, len(competitors))

    citation = diligence.get("citation_ledger") or []
    source_count = len(citation) if isinstance(citation, list) else 0

    gaps: list[str] = []
    warnings: list[str] = []
    if numeric_scores and avg_score < section_avg_target:
        gaps.append(f"Average section score {avg_score:.1f}/10 is below {section_avg_target}/10 investor bar.")
    if numeric_scores and min_score < section_min_target:
        gaps.append(f"Weakest section {min_score:.1f}/10 is below {section_min_target}/10 floor.")
    if not numeric_scores:
        gaps.append(
            "Section quality was not scored — enable section scoring or re-run the report "
            "(Quality gate scores sections even when auto-redo is off)."
        )
    elif effective_report_score < report_score_target:
        gaps.append(
            f"Blended report quality {effective_report_score:.1f}/10 is below {report_score_target}/10."
        )
    if live_count < 2 and source_count < 6:
        gaps.append(
            "Need at least 2 live competitors (SERP) or 6 cited sources — add SERPAPI_KEY to `.env` "
            "and keep Auto-research enabled."
        )

    if any(c.get("reason") == "placeholder_or_nan_markers" for c in caps_applied):
        gaps.append(
            "Report still contains placeholder or withheld numeric tokens — customer export blocked until removed."
        )
    if honesty_enforced and honest_score < section_avg_target:
        gaps.append(
            f"Honesty-capped quality {honest_score:.1f}/10 is below {section_avg_target}/10 "
            f"(placeholders, TAM, pricing, or buyer-validation gaps)."
        )

    for gap in (local_audit.get("critical_gaps") or []):
        if not isinstance(gap, str):
            continue
        low = gap.lower()
        if "wrong-domain" in low:
            if gap not in gaps:
                gaps.append(gap)
        elif any(t in low for t in ("withheld", "funding readiness", "strict verification", "tam", "sam", "som")):
            if gap not in warnings:
                warnings.append(gap)

    investor_ready = not gaps
    investor_score = round(
        min(effective_report_score, honest_score) if honesty_enforced else effective_report_score,
        1,
    )

    return {
        "investor_ready": investor_ready,
        "investor_ready_score": investor_score,
        "honest_score": round(honest_score, 1) if honesty_enforced else None,
        "honesty_enforced": honesty_enforced,
        "section_average": round(avg_score, 1) if numeric_scores else None,
        "section_minimum": round(min_score, 1) if numeric_scores else None,
        "market_style_score": market_score,
        "effective_report_score": effective_report_score,
        "live_competitor_count": live_count,
        "cited_source_count": source_count,
        "gaps": gaps,
        "notes": (
            ["No blocking investor gaps detected by deterministic gate."]
            if investor_ready
            else []
        ),
        "warnings": warnings,
        "verdict": (
            "Investor-ready research brief"
            if investor_ready
            else "Research scaffold — close gaps before investor circulation"
        ),
        "policy": (
            "Investor-ready = section quality ~7/10 + evidence depth, capped by honesty audit "
            "(placeholders, TAM, pricing, buyer proof). Funding tier is separate."
        ),
    }
