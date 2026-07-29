"""Single consumer-trust gate — aligns badges, V3 render, and audit."""
from __future__ import annotations

from typing import Any

_CLAIM_KEYS = {"tam": "TAM", "sam": "SAM", "som": "SOM"}


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def strict_metric_withheld(payload: dict[str, Any], metric_key: str) -> bool:
    """True when strict_verification_pack marks a market metric as not verified."""
    diligence = _as_dict(payload.get("diligence_pack"))
    strict = _as_dict(diligence.get("strict_verification_pack"))
    gates = _as_dict(strict.get("claim_gates"))
    if not gates:
        return False
    gate_name = _CLAIM_KEYS.get(str(metric_key).lower(), str(metric_key).upper())
    gate = _as_dict(gates.get(gate_name))
    if not gate:
        return False
    return str(gate.get("status", "")).lower() != "verified"


def withheld_market_metrics(payload: dict[str, Any]) -> list[str]:
    return [key.upper() for key in _CLAIM_KEYS if strict_metric_withheld(payload, key)]


def consumer_trust_block_reasons(payload: dict[str, Any]) -> list[str]:
    """Reasons to block polished customer V3 (show repair scaffold instead)."""
    payload = payload if isinstance(payload, dict) else {}
    reasons: list[str] = []
    audit = _as_dict(payload.get("final_report_audit"))
    honesty = _as_dict(audit.get("honesty_audit"))

    try:
        from iidatech.validation.financial_validator import detect_placeholders

        placeholders = detect_placeholders(payload)
    except Exception:
        placeholders = {"has_placeholders": False}

    fin = _as_dict(honesty.get("financial_validation"))
    ph = _as_dict(fin.get("placeholders"))
    if placeholders.get("has_placeholders") or ph.get("has_placeholders"):
        reasons.append("placeholder_tokens_in_report")

    caps = [c for c in (honesty.get("caps_applied") or []) if isinstance(c, dict)]
    if any(c.get("reason") == "placeholder_or_nan_markers" for c in caps):
        reasons.append("honesty_cap_placeholders")

    if audit.get("investor_ready") is False:
        reasons.append("investor_readiness_failed")

    withheld = withheld_market_metrics(payload)
    if withheld and audit.get("funding_ready") is False:
        reasons.append(f"withheld_market_metrics:{','.join(withheld)}")

    if honesty.get("honesty_enforced"):
        try:
            honest = float(honesty.get("honest_score") or 0)
        except (TypeError, ValueError):
            honest = 0.0
        if honest < 5.0:
            reasons.append("honesty_score_below_5")

    return list(dict.fromkeys(reasons))


def consumer_trust_blocked(payload: dict[str, Any]) -> bool:
    return bool(consumer_trust_block_reasons(payload))


def capped_display_score(
    section_avg: float | None,
    market_score: float,
    honesty_audit: dict[str, Any] | None,
) -> float:
    """One headline score for UI — min(section, market, honesty cap)."""
    honesty_audit = honesty_audit if isinstance(honesty_audit, dict) else {}
    scores: list[float] = []
    if isinstance(section_avg, (int, float)):
        scores.append(float(section_avg))
    if isinstance(market_score, (int, float)):
        scores.append(float(market_score))
    if honesty_audit.get("honesty_enforced"):
        try:
            scores.append(float(honesty_audit.get("honest_score") or 0))
        except (TypeError, ValueError):
            pass
    if not scores:
        return 0.0
    return round(min(scores), 1)
