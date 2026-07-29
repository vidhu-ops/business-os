"""Financial claim validation and missing-field detection."""
from __future__ import annotations

import re
from typing import Any


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _has_positive_number(value: Any) -> bool:
    if value in (None, "", 0, "0", "$0", "WITHHELD"):
        return False
    try:
        return float(str(value).replace(",", "").replace("$", "").replace("₹", "")) > 0
    except ValueError:
        return bool(re.search(r"\d{2,}", str(value)))


def assess_tam_inputs(report: dict[str, Any]) -> dict[str, Any]:
    model = _as_dict(report.get("quantitative_model"))
    headline = _as_dict(model.get("headline"))
    diligence = _as_dict(report.get("diligence_pack"))
    bottom_up = _as_dict(diligence.get("bottom_up_market_calculation"))
    missing = []
    buyer_count = bottom_up.get("buyer_count") or model.get("buyer_count") or headline.get("buyer_count")
    avg_ticket = bottom_up.get("avg_ticket") or model.get("avg_ticket") or headline.get("avg_acv")
    frequency = bottom_up.get("purchase_frequency") or model.get("purchase_frequency")
    tam_result = _as_dict(bottom_up.get("tam_result"))
    tam = (
        headline.get("tam_base")
        or model.get("tam")
        or headline.get("tam_base_fmt")
        or bottom_up.get("tam")
        or tam_result.get("tam")
        or tam_result.get("tam_usd")
    )
    if not _has_positive_number(buyer_count):
        missing.append("buyer_count")
    if not _has_positive_number(avg_ticket):
        missing.append("avg_ticket")
    if not frequency:
        missing.append("purchase_frequency")
    if not _has_positive_number(tam):
        missing.append("tam_denominator")
    return {
        "complete": not missing,
        "missing": missing,
        "buyer_count": buyer_count,
        "avg_ticket": avg_ticket,
        "purchase_frequency": frequency,
        "tam": tam,
    }


def assess_unit_economics(report: dict[str, Any]) -> dict[str, Any]:
    ue = _as_dict(report.get("unit_economics_grounding"))
    conf = _as_dict(report.get("report_confidence"))
    unknowns = ue.get("financial_unknowns") or conf.get("financial_unknowns") or []
    if isinstance(unknowns, dict):
        unknowns = list(unknowns.keys())
    unknown_blob = " ".join(str(u).lower() for u in unknowns) if isinstance(unknowns, list) else str(unknowns).lower()
    missing = []
    for key, label in (("cac", "CAC"), ("ltv", "LTV"), ("margin", "margin"), ("payback", "payback_period")):
        val = ue.get(key) or ue.get(label.lower())
        if not _has_positive_number(val) or key in unknown_blob or label.lower() in unknown_blob:
            missing.append(label if label != "margin" else "margin")
    if "payback" in unknown_blob:
        missing.append("payback_period")
    return {"complete": not missing, "missing": list(dict.fromkeys(missing)), "unknowns": unknowns}


def assess_buyer_validation(report: dict[str, Any]) -> dict[str, Any]:
    diligence = _as_dict(report.get("diligence_pack"))
    readiness = _as_dict(diligence.get("readiness"))
    counts = _as_dict(readiness.get("record_counts"))
    if not counts:
        counts = _as_dict(_as_dict(diligence.get("source_readiness_preflight")).get("record_counts"))
    buyer = int(counts.get("strict_buyer_validation_records", 0) or 0)
    return {"complete": buyer >= 2, "buyer_validation_count": buyer, "missing": [] if buyer >= 2 else ["buyer_validation"]}


def assess_pricing_evidence(report: dict[str, Any]) -> dict[str, Any]:
    from iidatech.validation.pricing_validator import filter_valid_pricing_rows

    diligence = _as_dict(report.get("diligence_pack"))
    readiness = _as_dict(diligence.get("readiness"))
    counts = _as_dict(readiness.get("record_counts"))
    if not counts:
        counts = _as_dict(_as_dict(diligence.get("source_readiness_preflight")).get("record_counts"))
    pricing = int(counts.get("direct_pricing_unit_cost_records", 0) or 0)
    pack = _as_dict(diligence.get("pricing_intelligence_pack"))
    domain = str(pack.get("domain") or diligence.get("domain") or "default")
    sourced = pack.get("sourced_pricing_records") or []
    if not isinstance(sourced, list):
        sourced = []
    validated = filter_valid_pricing_rows(sourced, domain=domain)
    valid_count = int(validated.get("valid_count") or 0)
    ok = valid_count >= 2 or pricing >= 2
    return {
        "complete": ok,
        "pricing_record_count": pricing,
        "validated_pricing_count": valid_count,
        "rejected_pricing_count": int(validated.get("rejected_count") or 0),
        "missing": [] if ok else ["validated_pricing"],
    }


def detect_placeholders(report: dict[str, Any]) -> dict[str, Any]:
    parts: list[str] = []
    sections = report.get("sections")
    if isinstance(sections, dict):
        parts.append(str(sections))
    elif isinstance(sections, list):
        parts.append(str(sections))
    for key in ("report_v3_markdown", "report_markdown", "market_by_market_report"):
        if report.get(key):
            parts.append(str(report.get(key)))
    blob = " ".join(parts).lower()
    markers = (
        "[placeholder]",
        "[x%]",
        "[estimated",
        "low confidence",
        "source-gated estimate withheld",
        "[unsupported numeric claim removed]",
        "masked value",
        "template_estimated",
        "not investor citable",
    )
    hits = [m for m in markers if m in blob]
    if re.search(r"\bnan\b", blob) or '"nan"' in blob or ": nan" in blob:
        hits.append("nan")
    soft_validation = "validation required" in blob and "[estimated" in blob
    if soft_validation:
        hits.append("validation_required_with_estimated")
    return {"has_placeholders": bool(hits), "markers": hits}


def build_financial_validation_summary(report: dict[str, Any]) -> dict[str, Any]:
    tam = assess_tam_inputs(report)
    ue = assess_unit_economics(report)
    buyer = assess_buyer_validation(report)
    pricing = assess_pricing_evidence(report)
    placeholders = detect_placeholders(report)
    return {
        "tam": tam,
        "unit_economics": ue,
        "buyer_validation": buyer,
        "pricing": pricing,
        "placeholders": placeholders,
    }