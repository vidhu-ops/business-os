"""Guarded confidence model — replaces inflated report confidence."""
from __future__ import annotations

from typing import Any

from iidatech.validation.hallucination_firewall import competitor_recall_from_payload, hallucination_score


def _extract_evidence_count(payload: dict[str, Any]) -> int:
    ri = payload.get("research_intelligence") if isinstance(payload.get("research_intelligence"), dict) else {}
    if ri.get("evidence_count") is not None:
        return int(ri["evidence_count"])
    diligence = payload.get("diligence_pack") if isinstance(payload.get("diligence_pack"), dict) else {}
    ledger = diligence.get("citation_ledger")
    if isinstance(ledger, list) and ledger:
        return len(ledger)
    return 0


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _source_quality(payload: dict[str, Any]) -> float:
    diligence = _as_dict(payload.get("diligence_pack"))
    ledger = diligence.get("citation_ledger")
    ledger_n = len(ledger) if isinstance(ledger, list) else 0
    ri = _as_dict(payload.get("research_intelligence"))
    tier = _as_dict(ri.get("source_quality"))
    tier_score = float(tier.get("score") or tier.get("avg_trust") or 0)
    if tier_score > 1:
        tier_score = tier_score / 100.0
    if ledger_n >= 8:
        base = 0.9
    elif ledger_n >= 4:
        base = 0.7
    elif ledger_n >= 1:
        base = 0.45
    else:
        base = 0.2
    return round(min(1.0, max(base, tier_score)), 4)


def _evidence_coverage(payload: dict[str, Any]) -> float:
    count = _extract_evidence_count(payload)
    return round(min(1.0, count / 12.0), 4)


def _numeric_verification(payload: dict[str, Any]) -> float:
    ri = _as_dict(payload.get("research_intelligence"))
    fin = _as_dict(ri.get("financial_truth"))
    tam = _as_dict(fin.get("tam"))
    ue = _as_dict(fin.get("unit_economics"))
    score = 0.0
    if tam.get("computed"):
        score += 0.35
    if ue and not str(ue.get("status", "")).startswith("VALIDATION"):
        score += 0.35
    comp = _as_dict(ri.get("competitor_map"))
    if int(comp.get("competitor_count") or 0) > 0 and competitor_recall_from_payload(payload) > 0:
        score += 0.3
    return round(min(1.0, score), 4)


def compute_guarded_confidence(
    payload: dict[str, Any],
    *,
    integrity: dict[str, Any] | None = None,
    firewall: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    integrity = integrity or {}
    firewall = firewall or {}

    source_q = _source_quality(payload)
    evidence = _evidence_coverage(payload)
    numeric = _numeric_verification(payload)
    hall_pen = hallucination_score(payload)

    score = round(
        100.0
        * (
            0.35 * source_q
            + 0.25 * evidence
            + 0.20 * numeric
            + 0.20 * hall_pen
        ),
        1,
    )

    caps: list[dict[str, Any]] = []
    if not integrity.get("ok", True) or integrity.get("payload_corruption_error"):
        caps.append({"cap": 10, "reason": "payload_corrupted"})
        score = min(score, 10)
    hall_n = int(firewall.get("hallucination_count") or 0)
    if hall_n > 3:
        caps.append({"cap": 30, "reason": f"hallucinations_{hall_n}"})
        score = min(score, 30)
    if competitor_recall_from_payload(payload) <= 0:
        caps.append({"cap": 25, "reason": "zero_verified_competitors"})
        score = min(score, 25)

    audit = _as_dict(payload.get("final_report_audit"))
    honesty = _as_dict(audit.get("honesty_audit"))
    if honesty.get("honesty_enforced"):
        try:
            honest_10 = float(honesty.get("honest_score") or 0)
        except (TypeError, ValueError):
            honest_10 = 0.0
        cap_100 = round(honest_10 * 10, 1)
        caps.append({"cap": cap_100, "reason": "honesty_audit"})
        score = min(score, cap_100)

    try:
        from iidatech.validation.consumer_trust import withheld_market_metrics

        withheld = withheld_market_metrics(payload)
    except Exception:
        withheld = []
    if withheld:
        caps.append({"cap": 35, "reason": f"withheld_{'_'.join(m.lower() for m in withheld)}"})
        score = min(score, 35)

    if audit.get("funding_ready") is False:
        caps.append({"cap": 30, "reason": "funding_gate_failed"})
        score = min(score, 30)

    grade = "high" if score >= 75 else "medium" if score >= 50 else "low"
    if score <= 10:
        grade = "blocked"

    return {
        "score": score,
        "grade": grade,
        "components": {
            "source_quality": source_q,
            "evidence_coverage": evidence,
            "numeric_verification": numeric,
            "hallucination_penalty": hall_pen,
        },
        "caps_applied": caps,
    }