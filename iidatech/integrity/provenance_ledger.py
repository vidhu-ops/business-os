"""Provenance ledger for derived financial claims (PR1-C Phase A)."""

from __future__ import annotations

import uuid
from typing import Any

_FORMULA_FACTORS: dict[str, float] = {
    "tam_bottom_up": 0.90,
    "sam_filter": 0.85,
    "som_capture": 0.80,
    "forecast_growth": 0.75,
}


def build_source_claim(
    metric_name: str,
    value: Any,
    unit: str,
    confidence: float,
    source_record_ids: list[str],
    claim_id: str | None = None,
) -> dict:
    """Build a provenance entry for a directly sourced claim."""
    return {
        "id": claim_id or str(uuid.uuid4()),
        "source_type": "source_record",
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "confidence": float(confidence),
        "source_record_ids": list(source_record_ids),
    }


def build_formula_claim(
    metric_name: str,
    value: Any,
    unit: str,
    derived_from_claim_ids: list[str],
    formula_expression: str,
    formula_inputs: dict[str, Any],
    formula_type: str,
    confidence: float | None = None,
    claim_id: str | None = None,
) -> dict:
    """Build a provenance entry for a claim derived via a formula."""
    return {
        "id": claim_id or str(uuid.uuid4()),
        "source_type": "derived_formula",
        "metric_name": metric_name,
        "value": value,
        "unit": unit,
        "derived_from_claim_ids": list(derived_from_claim_ids),
        "formula_expression": formula_expression,
        "formula_inputs": dict(formula_inputs),
        "formula_type": formula_type,
        "confidence": float(confidence) if confidence is not None else None,
    }


def compute_derived_confidence(
    input_confidences: list[float],
    formula_type: str,
) -> float:
    """Return derived confidence = min(input_confidences) * formula_factor."""
    if not input_confidences:
        return 0.0
    factor = _FORMULA_FACTORS.get(formula_type, 0.80)
    return round(min(input_confidences) * factor, 4)