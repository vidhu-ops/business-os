"""Honest score caps so internal scoring correlates with external audit."""
from __future__ import annotations

from typing import Any

from iidatech.validation.financial_validator import build_financial_validation_summary

SCORE_CAPS = {
    "missing_pricing": 5.0,
    "missing_tam": 6.0,
    "missing_buyer_validation": 5.0,
    "missing_cac_ltv": 4.0,
    "placeholders": 2.0,
}


def apply_honesty_score_caps(report: dict[str, Any], base_score: float) -> dict[str, Any]:
    summary = build_financial_validation_summary(report)
    caps_applied: list[dict[str, Any]] = []
    score = float(base_score or 0)

    if not summary["pricing"]["complete"]:
        caps_applied.append({"cap": SCORE_CAPS["missing_pricing"], "reason": "missing_validated_pricing"})
        score = min(score, SCORE_CAPS["missing_pricing"])
    if not summary["tam"]["complete"]:
        caps_applied.append({"cap": SCORE_CAPS["missing_tam"], "reason": "missing_tam_denominator_inputs"})
        score = min(score, SCORE_CAPS["missing_tam"])
    if not summary["buyer_validation"]["complete"]:
        caps_applied.append({"cap": SCORE_CAPS["missing_buyer_validation"], "reason": "missing_buyer_validation"})
        score = min(score, SCORE_CAPS["missing_buyer_validation"])
    if not summary["unit_economics"]["complete"]:
        caps_applied.append({"cap": SCORE_CAPS["missing_cac_ltv"], "reason": "missing_cac_ltv_margin_payback"})
        score = min(score, SCORE_CAPS["missing_cac_ltv"])
    if summary["placeholders"]["has_placeholders"]:
        caps_applied.append({"cap": SCORE_CAPS["placeholders"], "reason": "placeholder_or_nan_markers"})
        score = min(score, SCORE_CAPS["placeholders"])

    return {
        "honest_score": round(score, 1),
        "base_score": round(float(base_score or 0), 1),
        "caps_applied": caps_applied,
        "financial_validation": summary,
        "honesty_enforced": bool(caps_applied),
    }