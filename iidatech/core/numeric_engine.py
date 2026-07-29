"""Numeric truth engine -- sole owner of TAM/SAM/SOM/CAC/LTV for customer-facing output."""
from __future__ import annotations

from typing import Any

SECTION_BLOCKED = "BLOCKED"
SECTION_PARTIAL = "PARTIAL"
SECTION_VALID = "VALID"

_SYNTHETIC_SOURCES = frozenset(
    {
        "",
        "preview",
        "synthetic",
        "manual_preview",
        "preview-mock",
        "preview band",
        "estimated",
        "unverified",
        "benchmark",
        "financial_benchmark_bank",
        "business_blueprint",
    }
)

_SIZE_KEYS = ("tam", "sam", "som")
_UNIT_KEYS = (
    ("cac", "cac"),
    ("ltv", "ltv"),
    ("arpu", "arpu"),
    ("gross_margin", "margin"),
    ("payback_months", "payback_months"),
    ("burn_multiple", "burn_multiple"),
)


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _num(v: Any) -> float | None:
    if v in (None, "", "WITHHELD"):
        return None
    if isinstance(v, dict):
        v = v.get("value") or v.get("display")
    try:
        return float(str(v).replace(",", "").replace("$", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def _source_ok(source: Any) -> bool:
    return str(source or "").strip().lower() not in _SYNTHETIC_SOURCES


def _block_verified(raw: dict, key: str) -> dict[str, Any] | None:
    if not raw:
        return None
    val = raw.get("value")
    if val is None:
        val = raw.get(key)
    if val in (None, "", "WITHHELD"):
        return None
    if not (raw.get("evidence_backed") or raw.get("computed") or raw.get("validated")):
        return None
    source = raw.get("source") or "research_intelligence"
    if not _source_ok(source):
        return None
    n = _num(val)
    if n is None:
        return None
    return {
        "key": key,
        "value": n,
        "source": str(source),
        "owner": "numeric_engine",
        "evidence_backed": bool(raw.get("evidence_backed")),
        "computed": bool(raw.get("computed")),
        "confidence": str(raw.get("confidence") or ("high" if raw.get("computed") else "medium")),
    }


def _qmodel_size(qmodel: dict, key: str) -> dict[str, Any] | None:
    headline = _as_dict(qmodel.get("headline"))
    base_key = f"{key}_base"
    val = headline.get(base_key) or qmodel.get(key)
    if val in (None, "", "WITHHELD"):
        return None
    fmt = str(headline.get(f"{base_key}_fmt") or "")
    if "WITHHELD" in fmt.upper() or "VALIDATION" in fmt.upper():
        return None
    n = _num(val)
    if n is None:
        return None
    if not qmodel.get("evidence_backed") and not headline.get("methodology"):
        return None
    return {
        "key": key,
        "value": n,
        "source": "quantitative_model",
        "owner": "numeric_engine",
        "evidence_backed": bool(qmodel.get("evidence_backed")),
        "computed": True,
        "confidence": "high",
    }


def _grounding_metric(grounding: dict, key: str, alt: str | None = None) -> dict[str, Any] | None:
    block = _as_dict(grounding.get(key) if key in grounding else grounding.get(alt or key))
    if block:
        m = _block_verified(block, key)
        if m:
            m["source"] = "unit_economics_grounding"
            return m
    direct = grounding.get(key) if key in grounding else grounding.get(alt or key)
    if direct in (None, "", "WITHHELD"):
        return None
    if not grounding.get("evidence_backed") and not _source_ok(grounding.get("source")):
        return None
    n = _num(direct)
    if n is None:
        return None
    return {
        "key": key,
        "value": n,
        "source": str(grounding.get("source") or "unit_economics_grounding"),
        "owner": "numeric_engine",
        "evidence_backed": bool(grounding.get("evidence_backed")),
        "computed": False,
        "confidence": "medium",
    }


def _section_status(metrics: dict[str, Any], required: tuple[str, ...]) -> str:
    present = [k for k in required if k in metrics and metrics[k]]
    if not present:
        return SECTION_BLOCKED
    if len(present) < len(required):
        return SECTION_PARTIAL
    return SECTION_VALID


def build_numeric_truth(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Extract verified numeric metrics from payload (read-only aggregation)."""
    payload = payload if isinstance(payload, dict) else {}
    brain = _as_dict(payload.get("research_intelligence"))
    if not brain:
        brain = _as_dict(_as_dict(payload.get("diligence_pack")).get("research_intelligence"))
    fin = _as_dict(brain.get("financial_truth"))
    grounding = _as_dict(payload.get("unit_economics_grounding"))
    qmodel = _as_dict(payload.get("quantitative_model"))

    metrics: dict[str, Any] = {}
    missing: list[str] = []

    for key in _SIZE_KEYS:
        m = _block_verified(_as_dict(fin.get(key)), key)
        if not m:
            m = _qmodel_size(qmodel, key)
        if m:
            metrics[key] = m
        else:
            missing.append(f"{key.upper()} with cited denominator")

    ue = _as_dict(fin.get("unit_economics"))
    for out_key, src_key in _UNIT_KEYS:
        m = _block_verified(ue, src_key) if ue else None
        if not m and grounding:
            m = _grounding_metric(grounding, out_key, src_key)
        if m:
            metrics[out_key] = m
        elif out_key in ("cac", "ltv"):
            missing.append(f"{out_key.upper()} with cited sources")

    size_status = _section_status(metrics, ("tam",))
    unit_status = _section_status(metrics, ("cac", "ltv"))
    if size_status == SECTION_BLOCKED and unit_status == SECTION_BLOCKED:
        status = SECTION_BLOCKED
    elif size_status == SECTION_VALID and unit_status in {SECTION_VALID, SECTION_PARTIAL}:
        status = SECTION_VALID
    elif metrics:
        status = SECTION_PARTIAL
    else:
        status = SECTION_BLOCKED

    return {
        "status": status,
        "owner": "numeric_engine",
        "metrics": metrics,
        "missing_evidence": missing,
        "impossible_economics": _as_list(fin.get("impossible_economics")),
        "invalid_business_model": bool(fin.get("invalid_business_model")),
        "invalid_reasons": _as_list(fin.get("invalid_business_model_reasons")),
        "financial_unknowns": _as_list(grounding.get("financial_unknowns")),
    }
