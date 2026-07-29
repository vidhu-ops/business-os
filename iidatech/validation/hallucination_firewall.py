"""Hallucination firewall — detect and reject fabricated report fields."""
from __future__ import annotations

import copy
import re
from typing import Any

from iidatech.validation.competitor_evidence import (
    DEFAULT_COMPETITOR_EVIDENCE_GAPS,
    has_live_competitor_evidence,
    has_live_pricing_evidence,
    is_live_serp_evidence_row,
    is_synthetic_competitor_name,
    is_verified_competitor_row,
    is_verified_pricing_row,
)

_VALIDATION = "VALIDATION REQUIRED"
_FAKE_COMPETITOR = re.compile(r"^competitor\s*[#:]?\s*\d+\b", re.I)
_GENERIC_ICP = re.compile(r"^(primary buyer|workflow buyer|named buyer|generic buyer|icp\s*\d+)", re.I)
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
    }
)


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _is_india(payload: dict[str, Any]) -> bool:
    geo = _norm(payload.get("geography") or payload.get("target"))
    return "india" in geo or geo in {"in", "ind"}


def _is_saas_context(payload: dict[str, Any]) -> bool:
    blob = _norm(
        " ".join(
            [
                str(payload.get("industry") or ""),
                str(payload.get("topic") or ""),
                str(payload.get("routed_domain") or ""),
            ]
        )
    )
    return any(tok in blob for tok in ("saas", "software", "b2b", "crm", "automation"))


def _diligence(payload: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(payload.get("diligence_pack"))


def _has_evidence(payload: dict[str, Any], key: str) -> bool:
    ri = _as_dict(payload.get("research_intelligence"))
    diligence = _diligence(payload)
    ledger = _as_list(diligence.get("citation_ledger"))
    if int(diligence.get("live_competitor_count") or 0) >= 3:
        return True
    serp = _as_dict(payload.get("serp_intelligence") or diligence.get("serp_intelligence"))
    if len(_as_list(serp.get("structured_records"))) >= 5:
        return True
    if key == "unit_economics":
        ue = _as_dict(_as_dict(ri.get("financial_truth")).get("unit_economics"))
        return bool(ue.get("evidence_backed") or ue.get("source") or len(ledger) >= 3)
    return len(ledger) >= 2 or int(ri.get("evidence_count") or 0) >= 3


def _iter_competitor_names(payload: dict[str, Any]) -> list[str]:
    names: list[str] = []
    ri = _as_dict(payload.get("research_intelligence"))
    comp = _as_dict(ri.get("competitor_map"))
    names.extend(str(x) for x in _as_list(comp.get("market_leaders")))
    for row in _as_list(comp.get("competitor_matrix")):
        if isinstance(row, dict):
            names.append(str(row.get("name") or row.get("competitor") or ""))
    diligence = _diligence(payload)
    for row in _as_list(_as_dict(diligence.get("competitor_intelligence_pack")).get("competitors")):
        if isinstance(row, dict):
            names.append(str(row.get("name") or ""))
    for row in _as_list(diligence.get("competitive_benchmark")):
        if isinstance(row, dict):
            names.append(
                str(row.get("name") or row.get("competitor_archetypes") or row.get("competitor") or "")
            )
    serp = _as_dict(payload.get("serp_intelligence") or diligence.get("serp_intelligence"))
    for row in _as_list(serp.get("structured_records")):
        if isinstance(row, dict):
            names.append(str(row.get("name") or row.get("company_name") or ""))
    return [n for n in names if n.strip()]


def _iter_icp_names(payload: dict[str, Any]) -> list[str]:
    names: list[str] = []
    ri = _as_dict(payload.get("research_intelligence"))
    cust = _as_dict(ri.get("customer_truth"))
    for row in _as_list(cust.get("icp_profiles")) + _as_list(cust.get("buyer_personas")):
        if isinstance(row, dict):
            names.append(str(row.get("name") or row.get("named_buyer_profile") or row.get("segment") or ""))
    for pain in _as_list(cust.get("top_pains")):
        if isinstance(pain, dict):
            names.append(str(pain.get("category") or pain.get("sample") or ""))
    return [n for n in names if n.strip()]


def _iter_pricing_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ri = _as_dict(payload.get("research_intelligence"))
    comp = _as_dict(ri.get("competitor_map"))
    rows.extend(r for r in _as_list(comp.get("pricing_rows")) if isinstance(r, dict))
    diligence = _diligence(payload)
    pack = _as_dict(diligence.get("pricing_intelligence_pack"))
    rows.extend(r for r in _as_list(pack.get("rows")) if isinstance(r, dict))
    rows.extend(r for r in _as_list(pack.get("sourced_pricing_records")) if isinstance(r, dict))
    return rows


def _iter_competitor_rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    ri = _as_dict(payload.get("research_intelligence"))
    comp = _as_dict(ri.get("competitor_map"))
    rows.extend(r for r in _as_list(comp.get("competitor_matrix")) if isinstance(r, dict))
    diligence = _diligence(payload)
    rows.extend(r for r in _as_list(diligence.get("competitive_benchmark")) if isinstance(r, dict))
    rows.extend(
        r for r in _as_list(_as_dict(diligence.get("competitor_intelligence_pack")).get("competitors"))
        if isinstance(r, dict)
    )
    return rows


_HARD_CRITICAL_CODES = frozenset(
    {
        "fake_competitor",
        "generic_competitor_label",
        "circular_icp",
        "circular_icp_topic",
        "impossible_cac",
        "impossible_arpu",
        "suspicious_payback",
        "suspicious_ltv_cac",
        "manual_preview_synthetic",
    }
)


def _apply_tam_pricing_gap_policy(payload: dict[str, Any], issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Downgrade TAM/pricing gaps to warnings when live SERP evidence exists."""
    live_comp = has_live_competitor_evidence(payload)
    live_price = has_live_pricing_evidence(payload)
    adjusted: list[dict[str, Any]] = []
    for issue in issues:
        code = str(issue.get("code") or "")
        if code == "unverified_competitor" and live_comp:
            continue
        if code in {"missing_pricing", "synthetic_pricing_source"} and (live_price or live_comp):
            adjusted.append({**issue, "severity": "warning"})
            continue
        if code in {"synthetic_tam", "estimated_tam"}:
            adjusted.append({**issue, "severity": "warning"})
            continue
        adjusted.append(issue)
    return adjusted


def detect_hallucinations(report_payload: dict[str, Any]) -> dict[str, Any]:
    payload = report_payload if isinstance(report_payload, dict) else {}
    issues: list[dict[str, Any]] = []

    ri_comp = _as_dict(_as_dict(payload.get("research_intelligence")).get("competitor_map"))
    for name in _iter_competitor_names(payload):
        if is_synthetic_competitor_name(name) or _FAKE_COMPETITOR.search(name.strip()):
            issues.append(
                {
                    "code": "fake_competitor",
                    "severity": "critical",
                    "field": "competitor_map",
                    "detail": name,
                }
            )
        if _norm(name) in {"competitor", "market leader", "generic competitor", "placeholder competitor"}:
            issues.append(
                {
                    "code": "generic_competitor_label",
                    "severity": "critical",
                    "field": "competitor_map",
                    "detail": name,
                }
            )

    for row in _iter_competitor_rows(payload):
        if not isinstance(row, dict):
            continue
        if row.get("competitor_archetypes") and not row.get("name") and not row.get("url") and not is_live_serp_evidence_row(row):
            continue
        if is_live_serp_evidence_row(row):
            continue
        if not is_verified_competitor_row(row):
            name = str(row.get("name") or row.get("competitor") or row.get("competitor_archetypes") or "")
            if name.strip():
                issues.append(
                    {
                        "code": "unverified_competitor",
                        "severity": "critical",
                        "field": "competitive_benchmark",
                        "detail": name,
                    }
                )

    topic = _norm(payload.get("topic") or payload.get("idea"))
    for icp in _iter_icp_names(payload):
        icp_norm = _norm(icp)
        if _GENERIC_ICP.search(icp.strip()):
            issues.append({"code": "circular_icp", "severity": "critical", "field": "customer_truth", "detail": icp})
        elif topic and len(topic) > 8 and topic in icp_norm:
            issues.append({"code": "circular_icp_topic", "severity": "critical", "field": "customer_truth", "detail": icp})

    ri = _as_dict(payload.get("research_intelligence"))
    ue = _as_dict(_as_dict(ri.get("financial_truth")).get("unit_economics"))
    cac = ue.get("cac")
    ltv = ue.get("ltv")
    arpu = ue.get("arpu") or ue.get("avg_revenue") or ue.get("monthly_revenue")
    payback = ue.get("payback_months")
    try:
        cac_f = float(cac) if cac is not None else None
    except (TypeError, ValueError):
        cac_f = None
    try:
        arpu_f = float(arpu) if arpu is not None else None
    except (TypeError, ValueError):
        arpu_f = None
    try:
        payback_f = float(payback) if payback is not None else None
    except (TypeError, ValueError):
        payback_f = None
    try:
        ltv_f = float(ltv) if ltv is not None else None
    except (TypeError, ValueError):
        ltv_f = None

    india_saas = _is_india(payload) and _is_saas_context(payload)
    if india_saas and cac_f is not None and cac_f < 50:
        issues.append({"code": "impossible_cac", "severity": "critical", "field": "unit_economics", "detail": f"cac={cac_f}"})
    if india_saas and arpu_f is not None and arpu_f < 100:
        issues.append({"code": "impossible_arpu", "severity": "critical", "field": "unit_economics", "detail": f"arpu={arpu_f}"})
    if payback_f is not None and payback_f < 2 and not _has_evidence(payload, "unit_economics"):
        issues.append(
            {
                "code": "suspicious_payback",
                "severity": "critical",
                "field": "unit_economics",
                "detail": f"payback_months={payback_f}",
            }
        )
    if cac_f and ltv_f and cac_f > 0 and (ltv_f / cac_f) > 10 and not _has_evidence(payload, "unit_economics"):
        issues.append(
            {
                "code": "suspicious_ltv_cac",
                "severity": "critical",
                "field": "unit_economics",
                "detail": f"ltv_cac={ltv_f / cac_f:.1f}",
            }
        )

    for row in _iter_pricing_rows(payload):
        if is_verified_pricing_row(row):
            continue
        band = str(row.get("estimated_price_band") or row.get("price_band") or row.get("price") or row.get("package") or "")
        source = _norm(row.get("source") or row.get("what_to_verify") or row.get("url"))
        if _VALIDATION in band or _norm(band) == _norm(_VALIDATION):
            issues.append({"code": "missing_pricing", "severity": "critical", "field": "pricing", "detail": band or "blank"})
        else:
            issues.append({"code": "synthetic_pricing_source", "severity": "critical", "field": "pricing", "detail": source or band or "blank"})

    fin = _as_dict(ri.get("financial_truth"))
    for key in ("tam", "sam", "som"):
        block = _as_dict(fin.get(key))
        if block.get("value") not in (None, "", 0) and not block.get("evidence_backed") and block.get("status") != _VALIDATION:
            if block.get("computed"):
                issues.append(
                    {
                        "code": "estimated_tam",
                        "severity": "warning",
                        "field": key,
                        "detail": str(block.get("value")),
                    }
                )
            else:
                issues.append({"code": "synthetic_tam", "severity": "critical", "field": key, "detail": str(block.get("value"))})

    if payload.get("manual_preview") and any(
        is_synthetic_competitor_name(n) for n in _iter_competitor_names(payload)
    ):
        issues.append({"code": "manual_preview_synthetic", "severity": "critical", "field": "payload", "detail": "preview data"})

    issues = _apply_tam_pricing_gap_policy(payload, issues)
    critical = [i for i in issues if i.get("severity") == "critical"]
    warnings = [i for i in issues if i.get("severity") != "critical"]
    return {
        "issues": issues,
        "critical_count": len(critical),
        "warning_count": len(warnings),
        "hallucination_count": len(issues),
        "critical": critical,
        "warnings": warnings,
        "hard_critical_count": len([i for i in critical if i.get("code") in _HARD_CRITICAL_CODES]),
    }


def sanitize_hallucinated_fields(report_payload: dict[str, Any]) -> dict[str, Any]:
    payload = copy.deepcopy(report_payload if isinstance(report_payload, dict) else {})
    detection = detect_hallucinations(payload)
    codes = {i.get("code") for i in detection.get("issues") or []}

    if codes & {"fake_competitor", "generic_competitor_label", "manual_preview_synthetic", "unverified_competitor"}:
        ri = _as_dict(payload.get("research_intelligence"))
        comp = _as_dict(ri.get("competitor_map"))
        comp["market_leaders"] = []
        comp["competitor_matrix"] = []
        comp["competitor_count"] = 0
        comp["validated_pricing"] = []
        comp["pricing_rows"] = []
        comp["pricing_bands"] = {}
        comp["evidence_gap"] = True
        comp["market_gaps"] = list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
        ri["competitor_map"] = comp
        ri["missing_evidence"] = list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
        payload["research_intelligence"] = ri
        diligence = _as_dict(payload.get("diligence_pack"))
        diligence["competitive_benchmark"] = []
        pack = _as_dict(diligence.get("pricing_intelligence_pack"))
        pack["rows"] = []
        diligence["pricing_intelligence_pack"] = pack
        payload["diligence_pack"] = diligence

    if codes & {"impossible_cac", "impossible_arpu", "suspicious_payback", "suspicious_ltv_cac"}:
        ri = _as_dict(payload.get("research_intelligence"))
        fin = _as_dict(ri.get("financial_truth"))
        fin["unit_economics"] = {"status": _VALIDATION, "withheld_reason": "failed_unit_economics_firewall"}
        ri["financial_truth"] = fin
        payload["research_intelligence"] = ri

    if codes & {"missing_pricing", "synthetic_pricing_source", "synthetic_tam"}:
        ri = _as_dict(payload.get("research_intelligence"))
        fin = _as_dict(ri.get("financial_truth"))
        for key in ("tam", "sam", "som"):
            if key in codes or "synthetic_tam" in codes:
                fin[key] = {"status": _VALIDATION, "withheld_reason": "failed_hallucination_firewall"}
        payload["quantitative_model"] = {}
        ri["financial_truth"] = fin
        payload["research_intelligence"] = ri

    if codes & {"missing_pricing", "synthetic_pricing_source"}:
        diligence = _as_dict(payload.get("diligence_pack"))
        pack = _as_dict(diligence.get("pricing_intelligence_pack"))
        pack["rows"] = []
        diligence["pricing_intelligence_pack"] = pack
        payload["diligence_pack"] = diligence

    if codes & {"circular_icp", "circular_icp_topic"}:
        ri = _as_dict(payload.get("research_intelligence"))
        cust = _as_dict(ri.get("customer_truth"))
        cust["icp_profiles"] = []
        cust["buyer_personas"] = []
        ri["customer_truth"] = cust
        payload["research_intelligence"] = ri

    payload["hallucination_sanitized"] = True
    payload["hallucination_firewall"] = detection
    return payload


def hallucination_score(report_payload: dict[str, Any]) -> float:
    detection = detect_hallucinations(report_payload)
    count = int(detection.get("hallucination_count") or 0)
    if count <= 0:
        return 1.0
    return round(max(0.0, 1.0 - (count / 8.0)), 4)


def competitor_recall_from_payload(report_payload: dict[str, Any]) -> float:
    names = _iter_competitor_names(report_payload)
    if not names:
        return 0.0
    real = [n for n in names if not is_synthetic_competitor_name(n) and _norm(n) not in {"competitor", "market leader"}]
    return round(len(real) / len(names), 4)