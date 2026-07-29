"""Primary deterministic research intelligence engine for IIDATECH reports."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from iidatech.agents.brain_dataset_analysts import (
    competitor_analyst_from_datasets,
    customer_analyst_from_datasets,
    financial_analyst_from_datasets,
    strategy_analyst_from_datasets,
)
from iidatech.proprietary_data.loader import load_proprietary_context
from iidatech.validation.financial_validator import (
    assess_tam_inputs,
    assess_unit_economics,
    build_financial_validation_summary,
)
from iidatech.validation.pricing_validator import filter_valid_pricing_rows
from iidatech.evidence_bank.bank_store import dedupe_competitor_rows
from iidatech.validation.competitor_evidence import is_synthetic_competitor_name
from iidatech.validation.source_validator import classify_source_tier, validate_record_for_claim

_TOKEN_RE = re.compile(r"[a-z]{4,}")
_WTP_RE = re.compile(r"(willing to pay|would pay|pay \$|budget|price sensitive|too expensive|worth it)", re.I)
_PAIN_RE = re.compile(r"(pain|friction|complain|hate|broken|slow|expensive|confus|limitation|churn)", re.I)


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(str(text or "").lower()))


def _overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _records_from_report(report: dict[str, Any], evidence_records: list[dict] | None) -> list[dict]:
    rows = list(evidence_records or [])
    if rows:
        return [r for r in rows if isinstance(r, dict)]
    diligence = _as_dict(report.get("diligence_pack"))
    serp_block = _as_dict(report.get("serp_intelligence")) or _as_dict(diligence.get("serp_intelligence"))
    serp_rows = _as_list(diligence.get("serp_brain_records"))
    if not serp_rows and serp_block:
        try:
            from iidatech.services.serp_payload_bridge import structured_to_brain_records, resolve_report_domain

            domain = resolve_report_domain(
                str(report.get("topic") or ""),
                str(report.get("industry") or ""),
                str(report.get("geography") or report.get("target") or "Global"),
                domain=diligence.get("domain"),
            )
            serp_rows = structured_to_brain_records(
                _as_list(serp_block.get("structured_records")),
                _as_list(serp_block.get("entities")),
                domain=domain,
                geography=str(report.get("geography") or report.get("target") or "Global"),
            )
        except Exception:
            serp_rows = []
    ledger = _as_list(diligence.get("citation_ledger"))
    benchmark = _as_list(diligence.get("competitive_benchmark"))
    sourced = _as_list(_as_dict(diligence.get("pricing_intelligence_pack")).get("sourced_pricing_records"))
    merged = [r for r in serp_rows + ledger + benchmark + sourced if isinstance(r, dict)]
    try:
        from iidatech.services.serp_payload_bridge import resolve_report_domain
        from iidatech.validation.competitor_relevance import filter_records_for_narrative_synthesis

        domain = resolve_report_domain(
            str(report.get("topic") or ""),
            str(report.get("industry") or ""),
            str(report.get("geography") or report.get("target") or "Global"),
            domain=diligence.get("domain"),
        )
        merged = filter_records_for_narrative_synthesis(
            merged,
            topic=str(report.get("topic") or ""),
            industry=str(report.get("industry") or ""),
            domain=domain,
        )
    except Exception:
        pass
    return merged


def _merge_competitor(dataset: dict[str, Any], legacy: dict[str, Any]) -> dict[str, Any]:
    matrix = list(dataset.get("competitor_matrix") or [])
    seen = {str(r.get("name", "")).lower() for r in matrix}
    for row in legacy.get("competitor_matrix") or []:
        name = str(row.get("name") or "").lower()
        if name and name not in seen:
            matrix.append(row)
            seen.add(name)
    out = dict(dataset)
    out["competitor_matrix"] = matrix[:15]
    out["competitor_count"] = max(int(dataset.get("competitor_count") or 0), len(matrix))
    out["validated_pricing"] = legacy.get("validated_pricing") or []
    gaps = list(dict.fromkeys((dataset.get("market_gaps") or []) + (legacy.get("market_gaps") or [])))
    out["market_gaps"] = gaps[:8]
    if legacy.get("confidence") == "high" or dataset.get("confidence") == "high":
        out["confidence"] = "high"
    return out


def _merge_customer(dataset: dict[str, Any], legacy: dict[str, Any]) -> dict[str, Any]:
    out = dict(dataset)
    clusters = list(dataset.get("pain_clusters") or dataset.get("top_pains") or [])
    legacy_clusters = legacy.get("buyer_pain_clusters") or []
    if len(legacy_clusters) > len(clusters):
        clusters = legacy_clusters
    out["buyer_pain_clusters"] = clusters
    out["strict_buyer_validation_count"] = legacy.get("strict_buyer_validation_count", 0)
    out["willingness_to_pay_signals"] = legacy.get("willingness_to_pay_signals") or []
    if legacy.get("confidence") == "high" or dataset.get("confidence") == "high":
        out["confidence"] = "high"
    elif clusters:
        out["confidence"] = out.get("confidence") or "medium"
    return out


def _merge_financial(dataset: dict[str, Any], legacy: dict[str, Any]) -> dict[str, Any]:
    out = dict(dataset)
    if not dataset.get("tam", {}).get("computed") and legacy.get("tam", {}).get("computed"):
        out["tam"] = legacy["tam"]
    out["unit_economics"] = {
        **(_as_dict(legacy.get("unit_economics"))),
        **(_as_dict(dataset.get("unit_economics"))),
    }
    out["impossible_economics"] = list(
        dict.fromkeys((dataset.get("impossible_economics") or []) + (legacy.get("impossible_economics") or []))
    )
    out["validation"] = legacy.get("validation")
    if dataset.get("confidence") == "high" or legacy.get("confidence") == "high":
        out["confidence"] = "high"
    return out


def _merge_strategy(dataset: dict[str, Any], legacy: dict[str, Any]) -> dict[str, Any]:
    out = dict(dataset)
    if not dataset.get("best_wedge"):
        out["best_wedge"] = legacy.get("wedge")
    out["wedge"] = out.get("best_wedge") or legacy.get("wedge")
    out["gtm"] = dataset.get("launch_strategy") or legacy.get("gtm") or []
    out["fast_revenue_path"] = dataset.get("first_revenue_path") or legacy.get("fast_revenue_path") or []
    return out


def competitor_analyst(
    *,
    topic: str,
    industry: str,
    geography: str,
    report: dict[str, Any],
    records: list[dict],
) -> dict[str, Any]:
    diligence = _as_dict(report.get("diligence_pack"))
    pack = _as_dict(diligence.get("competitor_intelligence_pack"))
    domain = str(pack.get("domain") or diligence.get("domain") or "default")
    matrix: list[dict[str, Any]] = []
    seen: set[str] = set()

    try:
        from iidatech.evidence_bank.google_competitor_discovery import is_valid_competitor_display_name
    except ImportError:
        def is_valid_competitor_display_name(name: str) -> bool:
            return bool(name and len(name) > 2)

    for name in _as_list(diligence.get("live_competitor_names")):
        clean = str(name or "").strip()
        if not clean or clean.lower() in seen:
            continue
        if is_synthetic_competitor_name(clean) or not is_valid_competitor_display_name(clean):
            continue
        seen.add(clean.lower())
        matrix.append({
            "name": clean[:80],
            "segment": "direct",
            "pricing_signal": None,
            "source": "live_serp_discovery",
            "verification_status": "live_serp",
            "discovery_source": "serp_intelligence",
            "tier": 2,
        })

    for row in _as_list(pack.get("competitors")) + _as_list(_as_dict(report.get("topic_intelligence_brief")).get("named_competitors")):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("company") or "").strip()
        if not name or name.lower() in seen:
            continue
        if is_synthetic_competitor_name(name) or not is_valid_competitor_display_name(name):
            continue
        seen.add(name.lower())
        matrix.append({
            "name": name[:80],
            "segment": row.get("segment") or row.get("archetype") or "unknown",
            "pricing_signal": row.get("pricing") or row.get("price_band"),
            "source": row.get("url") or row.get("source"),
            "tier": classify_source_tier(row),
        })

    for row in records:
        rtype = str(row.get("record_type") or row.get("claim_type") or "").lower()
        family = str(row.get("source_family") or "").lower()
        if rtype != "competitor" and "competitor" not in family:
            continue
        name = str(row.get("title") or row.get("publisher") or "").strip()[:80]
        if not name or name.lower() in seen:
            continue
        if is_synthetic_competitor_name(name) or not is_valid_competitor_display_name(name):
            continue
        seen.add(name.lower())
        matrix.append({
            "name": name,
            "segment": row.get("segment") or "direct",
            "pricing_signal": row.get("metric_value") or row.get("monthly_price"),
            "source": row.get("url"),
            "tier": classify_source_tier(row),
        })

    pricing_pack = _as_dict(diligence.get("pricing_intelligence_pack"))
    sourced = _as_list(pricing_pack.get("sourced_pricing_records"))
    validated = filter_valid_pricing_rows(sourced, domain=domain)
    pricing_extracts = []
    for row in validated.get("valid") or []:
        pv = _as_dict(row.get("_pricing_validation"))
        pricing_extracts.append({
            "plan": pv.get("plan_name") or row.get("plan_name"),
            "amount": pv.get("amount"),
            "tier": pv.get("tier"),
            "source": row.get("url"),
        })

    gaps = _as_list(pack.get("market_gaps"))
    verified_matrix = _as_list(diligence.get("verified_competitor_pricing_matrix"))
    for row in verified_matrix:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("competitor") or "").strip()
        if not name or name.lower() in seen:
            continue
        if is_synthetic_competitor_name(name) or not is_valid_competitor_display_name(name):
            continue
        seen.add(name.lower())
        matrix.append({
            "name": name[:80],
            "segment": row.get("segment") or "direct",
            "pricing_signal": row.get("pricing") or row.get("price"),
            "pricing": row.get("pricing") or row.get("price"),
            "source": row.get("source") or row.get("url"),
            "verification_status": row.get("verification_status") or "verified_pricing_page",
            "tier": 1,
        })

    if len(matrix) < 3:
        gaps = list(dict.fromkeys(gaps + ["Need 3+ named competitors with tier-1/2 sources"]))
    if len(pricing_extracts) < 2:
        gaps = list(dict.fromkeys(gaps + ["Need 2+ validated official pricing anchors"]))

    return {
        "competitor_matrix": matrix[:12],
        "competitor_count": len(matrix),
        "validated_pricing": pricing_extracts[:8],
        "market_gaps": gaps[:6],
        "confidence": "high" if len(matrix) >= 3 and len(pricing_extracts) >= 2 else "low",
    }


def customer_analyst(
    *,
    topic: str,
    industry: str,
    geography: str,
    report: dict[str, Any],
    records: list[dict],
) -> dict[str, Any]:
    diligence = _as_dict(report.get("diligence_pack"))
    brief = _as_dict(report.get("topic_intelligence_brief"))
    readiness = _as_dict(diligence.get("readiness"))
    counts = _as_dict(readiness.get("record_counts"))
    buyer_count = int(counts.get("strict_buyer_validation_records", 0) or 0)

    pains: list[str] = []
    for src in (
        _as_list(brief.get("buyer_pains")),
        _as_list(_as_dict(diligence.get("survey_interview_findings")).get("findings")),
    ):
        for item in src:
            if isinstance(item, str) and item.strip():
                pains.append(item.strip()[:240])
            elif isinstance(item, dict):
                text = str(item.get("pain") or item.get("signal") or item.get("title") or "")
                if text.strip():
                    pains.append(text.strip()[:240])

    for row in records:
        family = str(row.get("source_family") or "").lower()
        rtype = str(row.get("record_type") or row.get("claim_type") or "").lower()
        if rtype in {"buyer_pain", "buyer_voice", "buyer_signal"} or family in {"reddit_practitioner", "youtube_transcript"}:
            text = str(row.get("text") or row.get("title") or row.get("metric_value") or "")
            if _PAIN_RE.search(text):
                pains.append(text.strip()[:240])

    clusters: list[dict[str, Any]] = []
    assigned: set[int] = set()
    for i, pain in enumerate(pains):
        if i in assigned:
            continue
        cluster_tokens = _tokens(pain)
        members = [pain]
        assigned.add(i)
        for j, other in enumerate(pains):
            if j in assigned:
                continue
            if _overlap(cluster_tokens, _tokens(other)) >= 0.35:
                members.append(other)
                assigned.add(j)
        clusters.append({
            "theme": members[0][:80],
            "count": len(members),
            "samples": members[:3],
        })
    clusters.sort(key=lambda c: c["count"], reverse=True)

    wtp_signals = []
    for row in records:
        blob = " ".join(str(row.get(k) or "") for k in ("text", "title", "metric_value"))
        if _WTP_RE.search(blob):
            wtp_signals.append({
                "signal": blob[:180],
                "source": row.get("url"),
                "tier": classify_source_tier(row),
            })

    return {
        "buyer_pain_clusters": clusters[:8],
        "strict_buyer_validation_count": buyer_count,
        "willingness_to_pay_signals": wtp_signals[:6],
        "confidence": "high" if buyer_count >= 2 and clusters else "low",
    }


def financial_analyst(
    *,
    topic: str,
    industry: str,
    geography: str,
    report: dict[str, Any],
    records: list[dict],
) -> dict[str, Any]:
    validation = build_financial_validation_summary(report)
    tam = assess_tam_inputs(report)
    ue = assess_unit_economics(report)
    ue_data = _as_dict(report.get("unit_economics_grounding"))

    tam_output: dict[str, Any] = {"computed": False, "reason": "missing_denominators"}
    if tam["complete"]:
        try:
            buyers = float(str(tam["buyer_count"]).replace(",", "").replace("$", ""))
            ticket = float(str(tam["avg_ticket"]).replace(",", "").replace("$", ""))
            freq_raw = tam.get("purchase_frequency")
            freq = float(str(freq_raw).replace(",", "")) if freq_raw not in (None, "") else 1.0
            tam_value = buyers * ticket * freq
            tam_output = {
                "computed": True,
                "tam": round(tam_value, 2),
                "formula": "buyer_count * avg_ticket * purchase_frequency",
                "inputs": {"buyer_count": buyers, "avg_ticket": ticket, "purchase_frequency": freq},
            }
        except (TypeError, ValueError):
            tam_output = {"computed": False, "reason": "non_numeric_denominators"}

    def _num(key: str) -> float | None:
        val = ue_data.get(key) or ue_data.get(key.upper())
        if val in (None, "", "WITHHELD"):
            return None
        try:
            return float(str(val).replace(",", "").replace("$", ""))
        except ValueError:
            return None

    cac, ltv, margin, payback = _num("cac"), _num("ltv"), _num("margin"), _num("payback")
    unit_econ = {
        "cac": cac,
        "ltv": ltv,
        "margin": margin,
        "payback_months": payback,
        "complete": ue["complete"],
        "missing": ue.get("missing") or [],
    }

    impossible: list[str] = []
    if cac is not None and ltv is not None and ltv < cac:
        impossible.append("LTV below CAC")
    if margin is not None and margin < 0:
        impossible.append("negative_margin")
    if margin is not None and margin > 0.95:
        impossible.append("margin_unrealistically_high")
    if payback is not None and payback > 36:
        impossible.append("payback_exceeds_36_months")
    tam_inputs = _as_dict(tam_output.get("inputs"))
    if tam_output.get("computed") and tam_inputs.get("avg_ticket") and tam_output.get("tam", 0) < tam_inputs["avg_ticket"]:
        impossible.append("tam_smaller_than_unit_ticket")

    return {
        "tam": tam_output,
        "unit_economics": unit_econ,
        "impossible_economics": impossible,
        "validation": validation,
        "confidence": "high" if tam_output.get("computed") and ue["complete"] and not impossible else "low",
    }


def strategy_analyst(
    *,
    topic: str,
    industry: str,
    geography: str,
    report: dict[str, Any],
    competitor: dict[str, Any],
    customer: dict[str, Any],
    financial: dict[str, Any],
) -> dict[str, Any]:
    brief = _as_dict(report.get("topic_intelligence_brief"))
    wedge = brief.get("Narrow scope") or brief.get("Topic interpretation") or topic
    top_pain = (customer.get("buyer_pain_clusters") or [{}])[0].get("theme") if customer.get("buyer_pain_clusters") else ""
    comp_count = int(competitor.get("competitor_count") or 0)

    if comp_count >= 5:
        wedge_rec = f"Vertical niche within {wedge}: target underserved SMB segment with {top_pain or 'workflow pain'}"
    elif comp_count >= 2:
        wedge_rec = f"Differentiated workflow wedge: {wedge} focused on {top_pain or 'integration pain'}"
    else:
        wedge_rec = f"Category-creation wedge: define {wedge} narrowly before scaling GTM"

    gtm = [
        "Land with 5-10 design-partner SMBs from practitioner channels (Reddit, G2 reviews, founder communities)",
        "Publish pricing comparison using validated tier-1/2 pricing pages only",
        "Pilot paid implementation sprint before self-serve PLG if ACV < $3k",
    ]
    if geography and geography.lower() not in {"global", "worldwide", ""}:
        gtm.insert(0, f"Geo-first launch in {geography} with local compliance and pricing currency")

    fast_revenue = []
    if financial.get("tam", {}).get("computed"):
        fast_revenue.append("Services-led implementation ($2k-$15k) while product matures")
    fast_revenue.append("Agency/MSP channel resale with monthly retainer")
    if customer.get("willingness_to_pay_signals"):
        fast_revenue.append("Anchor pricing to validated competitor plans with 10-20% undercut or premium support")

    return {
        "wedge": wedge_rec,
        "gtm": gtm[:5],
        "fast_revenue_path": fast_revenue[:4],
        "confidence": "medium" if top_pain else "low",
    }


def _build_market_truth(
    topic: str,
    industry: str,
    geography: str,
    competitor: dict[str, Any],
    customer: dict[str, Any],
    financial: dict[str, Any],
    proprietary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "vertical": (proprietary or {}).get("vertical"),
        "competitor_density": competitor.get("competitor_count", 0),
        "validated_pricing_count": len(competitor.get("validated_pricing") or []),
        "buyer_cluster_count": len(customer.get("buyer_pain_clusters") or customer.get("top_pains") or []),
        "tam_computed": bool(_as_dict(financial.get("tam")).get("computed")),
        "unit_economics_complete": _as_dict(financial.get("unit_economics")).get("complete", False),
        "proprietary_dataset_priority": True,
    }


def _build_missing_evidence(
    competitor: dict[str, Any],
    customer: dict[str, Any],
    financial: dict[str, Any],
) -> list[str]:
    missing: list[str] = []
    if int(competitor.get("competitor_count") or 0) < 3:
        missing.append("named_competitors_3plus")
    if len(competitor.get("validated_pricing") or []) < 2 and not competitor.get("pricing_bands"):
        missing.append("validated_pricing_2plus")
    if int(customer.get("strict_buyer_validation_count") or 0) < 2 and not customer.get("top_pains"):
        missing.append("buyer_validation_2plus")
    tam = _as_dict(financial.get("tam"))
    if not tam.get("computed"):
        missing.append("tam_denominators")
    ue = _as_dict(financial.get("unit_economics"))
    for field in ue.get("missing") or []:
        missing.append(str(field).lower())
    if financial.get("invalid_business_model"):
        missing.append("invalid_business_model")
    return list(dict.fromkeys(missing))[:12]


def _build_risk_flags(financial: dict[str, Any], competitor: dict[str, Any]) -> list[str]:
    flags = list(financial.get("impossible_economics") or [])
    flags.extend(financial.get("invalid_business_model_reasons") or [])
    for gap in competitor.get("market_gaps") or []:
        if isinstance(gap, str):
            flags.append(gap[:120])
    if financial.get("confidence") == "low":
        flags.append("financial_truth_incomplete")
    return list(dict.fromkeys(flags))[:10]


def _compute_confidence_score(
    competitor: dict[str, Any],
    customer: dict[str, Any],
    financial: dict[str, Any],
    strategy: dict[str, Any],
) -> float:
    score = 20.0
    if competitor.get("confidence") == "high":
        score += 25
    elif int(competitor.get("competitor_count") or 0) >= 1:
        score += 10
    if customer.get("confidence") == "high":
        score += 20
    elif customer.get("buyer_pain_clusters") or customer.get("top_pains"):
        score += 8
    if financial.get("confidence") == "high":
        score += 25
    elif _as_dict(financial.get("tam")).get("computed"):
        score += 10
    if strategy.get("confidence") == "medium":
        score += 10
    return round(min(100.0, score), 1)


_EXACT_PRICE_RE = re.compile(
    r"\$\s*\d[\d,]*(?:\.\d{1,2})?(?:\s*/\s*(?:mo|month|user|seat|yr|year))?"
    r"|[\u20b9\u20ac\u00a3]\s*\d[\d,]*(?:\.\d{1,2})?(?:\s*/\s*(?:mo|month|user|seat|yr|year))?"
    r"|\b(?:rs|inr)\s*\.?\s*\d[\d,]*(?:\.\d{1,2})?"
    r"|\d[\d,]*(?:\.\d{1,2})?\s*(?:inr|rs\.?)\b"
    r"|(?:starting\s+at|from)\s+(?:[\u20b9$]|(?:rs|inr)\s*\.?\s*)?\s*\d[\d,]*",
    re.I,
)
_VAGUE_RANGE_RE = re.compile(
    r"\$\s*\d[\d,]*\s*[-–—]\s*\$?\s*\d|\$\s*\d[\d,]*\s+to\s+\$?\s*\d"
    r"|[\u20b9]\s*\d[\d,]*\s*[-–—]\s*[\u20b9]?\s*\d"
    r"|[\u20b9]\s*\d[\d,]*\s+to\s+[\u20b9]?\s*\d"
    r"|\b(?:rs|inr)\s*\.?\s*\d[\d,]*\s*[-–—]\s*(?:rs|inr)?\s*\.?\s*\d"
    r"|\d[\d,]*\s*[-–—]\s*\d[\d,]*\s*(?:inr|rs\.?)\b",
    re.I,
)
_CONTACT_PRICING_RE = re.compile(
    r"contact\s+(?:for|us)|request\s+(?:a\s+)?quote|call\s+for\s+pricing|"
    r"custom\s+pricing|pricing\s+upon\s+request|enterprise\s+only",
    re.I,
)
_VAGUE_PRICING_RE = re.compile(r"\bvaries\b|\brange\b|\bstarting\s+(?:at|from)\b|\bfrom\s+\$\d", re.I)
_REAL_CONFIDENCE_WEIGHTS = {
    "verified_ratio": 3.5,
    "specificity_score": 2.5,
    "completeness_score": 2.5,
    "polish_success": 1.5,
}
_FUNDING_READY_CONFIDENCE_THRESHOLD = 7.0


def _shorten_vendor_display_name(name: str) -> str:
    text = str(name or "").strip()
    if len(text) <= 45:
        return text
    stop = {
        "dental", "practice", "management", "software", "clinic", "cloud", "platform",
        "automation", "suite", "system", "solutions", "services",
    }
    words = text.split()
    brand: list[str] = []
    for word in words:
        if word.lower() in stop:
            break
        brand.append(word)
        if len(brand) >= 3:
            break
    return " ".join(brand) if brand else words[0]


def _normalize_competitor_row(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    if not str(out.get("name") or "").strip():
        out["name"] = str(out.get("competitor") or out.get("vendor") or out.get("company_name") or "").strip()
    name = _shorten_vendor_display_name(str(out.get("name") or "").strip())
    for suffix in (" CRM", " Software", " Platform", " Suite", " Cloud"):
        if name.lower().endswith(suffix.lower()):
            out["name"] = name[: -len(suffix)].strip()
            break
    if not str(out.get("pricing") or "").strip():
        price_val = out.get("price") or out.get("pricing_signal")
        if price_val is not None and str(price_val).strip():
            out["pricing"] = str(price_val).strip()
    return out


def _serp_structured_records_from_brain(brain: dict[str, Any]) -> list[dict[str, Any]]:
    serp = _as_dict(brain.get("_serp_intelligence")) or _as_dict(brain.get("serp_intelligence"))
    rows: list[dict[str, Any]] = []
    for row in _as_list(serp.get("structured_records")):
        if not isinstance(row, dict):
            continue
        record_type = str(row.get("record_type") or "").lower()
        if record_type not in {"competitor", "pricing", "vendor", "company"}:
            continue
        name = str(row.get("name") or row.get("competitor") or "").strip()
        if not name or is_synthetic_competitor_name(name):
            continue
        rows.append(_normalize_competitor_row(row))
    for ent in _as_list(serp.get("entities")):
        if not isinstance(ent, dict):
            continue
        name = str(ent.get("company_name") or ent.get("name") or "").strip()
        if not name or is_synthetic_competitor_name(name):
            continue
        rows.append(
            _normalize_competitor_row(
                {
                    **ent,
                    "name": name,
                    "record_type": "competitor",
                }
            )
        )
    return rows


def _is_perplexity_sourced(row: dict[str, Any]) -> bool:
    fields = (
        row.get("source_engine"),
        row.get("source_type"),
        row.get("discovered_via"),
        row.get("source_family"),
        row.get("verification_status"),
        row.get("source"),
    )
    blob = " ".join(str(f or "") for f in fields).lower()
    return "perplexity" in blob


def _has_parseable_price(row: dict[str, Any]) -> bool:
    """True when the row carries a non-empty price that parses as a concrete figure."""
    for key in ("price", "pricing", "pricing_signal", "monthly_price"):
        val = row.get(key)
        if val is None:
            continue
        if isinstance(val, (int, float)) and float(val) > 0:
            return True
        text = str(val).strip()
        if not text or text.lower() in {"unknown", "n/a", "not available"}:
            continue
        if _EXACT_PRICE_RE.search(text):
            return True
    blob = _extract_pricing_text(row)
    if not blob or blob.lower() in {"unknown", "n/a", "not available"}:
        return False
    return bool(_EXACT_PRICE_RE.search(blob))


def _row_verified_for_confidence(
    row: dict[str, Any],
    *,
    topic: str = "",
    industry: str = "",
    domain: str = "",
) -> bool:
    if _has_unresolved_pricing_discrepancy(row):
        return False
    if not _has_parseable_price(row):
        return False
    if str(topic or "").strip():
        try:
            from iidatech.validation.relevance_gate import is_record_relevant_to_report

            if not is_record_relevant_to_report(row, topic, industry, domain)[0]:
                return False
        except Exception:
            pass
    if _is_perplexity_sourced(row):
        return True
    status = str(row.get("verification_status") or "").lower()
    return status in {"firecrawl_verified", "perplexity_live"}


def _has_unresolved_pricing_discrepancy(row: dict[str, Any]) -> bool:
    flag = row.get("pricing_discrepancy")
    if flag is True or str(flag).lower() in {"true", "1", "yes"}:
        return True
    return str(row.get("verification_status") or "").lower() == "pricing_discrepancy"


def _extract_pricing_text(row: dict[str, Any]) -> str:
    for key in (
        "pricing",
        "pricing_signal",
        "price",
        "estimated_price_band",
        "price_band",
        "monthly_price",
        "metric_value",
    ):
        val = row.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def _row_has_public_pricing_url(row: dict[str, Any]) -> bool:
    for key in ("official_url", "url", "source_url", "pricing_url"):
        url = str(row.get(key) or "").strip()
        if url.startswith("http"):
            return True
    return False


def _pricing_specificity_score(row: dict[str, Any]) -> float:
    text = _extract_pricing_text(row)
    low = text.lower()
    if not text or low in {"unknown", "n/a", "not available"}:
        return 0.35
    if _CONTACT_PRICING_RE.search(text):
        return 0.75
    if _EXACT_PRICE_RE.search(text) and not _VAGUE_RANGE_RE.search(text):
        return 1.0
    if _VAGUE_RANGE_RE.search(text) or _VAGUE_PRICING_RE.search(text):
        if _row_has_public_pricing_url(row):
            return 0.35
        return 0.55
    if _EXACT_PRICE_RE.search(text):
        return 0.85
    return 0.5


def _is_competitor_evidence_row(row: dict[str, Any]) -> bool:
    name = str(row.get("name") or row.get("competitor") or row.get("vendor") or "").strip()
    if not name or is_synthetic_competitor_name(name):
        return False
    record_type = str(row.get("record_type") or row.get("entity_type") or "").lower()
    if record_type in {"competitor", "pricing", "vendor", "company"}:
        return True
    if _extract_pricing_text(row):
        return True
    return _is_perplexity_sourced(row)


def _collect_competitor_rows(brain: dict[str, Any], evidence_rows: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    """Merge proprietary matrix rows with live Perplexity structured_records by company name."""
    del evidence_rows  # scoring uses matrix + serp only; citation ledger rows inflate the denominator
    raw: list[dict[str, Any]] = []
    for row in _as_list(_as_dict(brain.get("competitor_map")).get("competitor_matrix")):
        if isinstance(row, dict):
            raw.append(_normalize_competitor_row(row))
    raw.extend(_serp_structured_records_from_brain(brain))
    return dedupe_competitor_rows(raw)


def _brain_completeness_ratio(brain: dict[str, Any]) -> float:
    checks: list[bool] = []
    mt = _as_dict(brain.get("market_truth"))
    checks.append(bool(str(mt.get("topic") or "").strip()))
    checks.append(bool(mt.get("tam_computed")))
    checks.append(int(mt.get("competitor_density") or 0) > 0)

    comp = _as_dict(brain.get("competitor_map"))
    checks.append(int(comp.get("competitor_count") or 0) > 0)
    checks.append(bool(comp.get("competitor_matrix")))

    cust = _as_dict(brain.get("customer_truth"))
    checks.append(bool(cust.get("buyer_pain_clusters") or cust.get("top_pains")))

    fin = _as_dict(brain.get("financial_truth"))
    tam = _as_dict(fin.get("tam"))
    checks.append(bool(tam.get("computed")))
    ue = _as_dict(fin.get("unit_economics"))
    checks.append(bool(ue.get("complete") or ue.get("gross_margin") is not None))

    strat = _as_dict(brain.get("strategic_recommendations"))
    checks.append(bool(strat.get("wedge")))
    checks.append(bool(strat.get("gtm")))

    checks.append(isinstance(brain.get("missing_evidence"), list))
    checks.append(brain.get("confidence_score") is not None)

    if not checks:
        return 0.0
    return sum(1 for ok in checks if ok) / len(checks)


def _polish_success_ratio(brain: dict[str, Any]) -> float:
    if brain.get("polish_error"):
        return 0.0
    if not brain.get("polish_attempted"):
        return 0.0
    narrative = brain.get("analyst_narrative")
    if isinstance(narrative, dict):
        filled = [v for v in narrative.values() if str(v or "").strip()]
        if len(filled) >= 2:
            return 1.0
        if filled:
            return 0.6
    return 0.0


def compute_real_confidence(brain: dict[str, Any], evidence_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Evidence-grounded 0-10 confidence from competitor verification, pricing specificity, completeness, and polish."""
    topic = str(brain.get("topic") or "")
    industry = str(brain.get("industry") or "")
    domain = str(brain.get("domain") or "")
    rows = _collect_competitor_rows(brain, evidence_rows)
    if rows:
        verified = sum(
            1
            for row in rows
            if _row_verified_for_confidence(
                row, topic=topic, industry=industry, domain=domain
            )
        )
        verified_ratio = verified / len(rows)
        specificity_score = sum(_pricing_specificity_score(row) for row in rows) / len(rows)
    else:
        verified_ratio = 0.0
        specificity_score = 0.0

    completeness_score = _brain_completeness_ratio(brain)
    polish_success = _polish_success_ratio(brain)

    components = {
        "verified_ratio": round(verified_ratio, 3),
        "specificity_score": round(specificity_score, 3),
        "completeness_score": round(completeness_score, 3),
        "polish_success": round(polish_success, 3),
        "competitor_row_count": len(rows),
    }
    score = sum(components[key] * weight for key, weight in _REAL_CONFIDENCE_WEIGHTS.items())
    score = round(min(10.0, max(0.0, score)), 1)

    return {
        "score": score,
        "components": components,
        "funding_ready_threshold": _FUNDING_READY_CONFIDENCE_THRESHOLD,
        "funding_ready_eligible": score > _FUNDING_READY_CONFIDENCE_THRESHOLD,
    }


def attach_real_confidence(brain: dict[str, Any], evidence_rows: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Compute and attach real_confidence + honest_score alias on brain."""
    rc = compute_real_confidence(brain, evidence_rows)
    brain["real_confidence"] = rc
    brain["honest_score"] = rc["score"]
    return brain


def run_research_brain(
    topic: str,
    industry: str,
    geography: str,
    report: dict[str, Any],
    *,
    evidence_records: list[dict] | None = None,
) -> dict[str, Any]:
    """Primary Python-first research intelligence layer. No mandatory LLM calls."""
    report = _as_dict(report)
    diligence = _as_dict(report.get("diligence_pack"))
    domain = diligence.get("domain")

    proprietary = load_proprietary_context(topic, industry, geography, domain=domain)
    records = _records_from_report(report, evidence_records)
    ctx = {
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "report": report,
        "proprietary": proprietary,
        "records": records,
    }

    ds_comp = competitor_analyst_from_datasets(ctx)
    ds_cust = customer_analyst_from_datasets(ctx)
    ds_fin = financial_analyst_from_datasets(ctx)
    ds_strat = strategy_analyst_from_datasets(ctx, ds_comp, ds_cust, ds_fin)

    legacy_comp = competitor_analyst(topic=topic, industry=industry, geography=geography, report=report, records=records)
    legacy_cust = customer_analyst(topic=topic, industry=industry, geography=geography, report=report, records=records)
    legacy_fin = financial_analyst(topic=topic, industry=industry, geography=geography, report=report, records=records)

    competitor = _merge_competitor(ds_comp, legacy_comp)
    customer = _merge_customer(ds_cust, legacy_cust)
    financial = _merge_financial(ds_fin, legacy_fin)
    strategy = _merge_strategy(
        ds_strat,
        strategy_analyst(
            topic=topic,
            industry=industry,
            geography=geography,
            report=report,
            competitor=competitor,
            customer=customer,
            financial=financial,
        ),
    )

    missing = _build_missing_evidence(competitor, customer, financial)
    risk_flags = _build_risk_flags(financial, competitor)
    confidence = _compute_confidence_score(competitor, customer, financial, strategy)

    serp_block = _as_dict(report.get("serp_intelligence")) or _as_dict(diligence.get("serp_intelligence"))

    brain = {
        "topic": topic,
        "industry": industry,
        "domain": str(domain or ""),
        "market_truth": _build_market_truth(topic, industry, geography, competitor, customer, financial, proprietary),
        "competitor_map": competitor,
        "customer_truth": customer,
        "financial_truth": financial,
        "strategic_recommendations": strategy,
        "risk_flags": risk_flags,
        "missing_evidence": missing,
        "confidence_score": confidence,
        "evidence_count": len(records) + len(competitor.get("competitor_matrix") or []),
        "serp_structured_count": len(_as_list(serp_block.get("structured_records"))),
        "_serp_intelligence": serp_block,
        "proprietary_context": {
            "vertical": proprietary.get("vertical"),
            "rows": {
                "competitor_pricing": len(proprietary.get("competitor_pricing") or []),
                "buyer_voice": len(proprietary.get("buyer_voice") or []),
                "supplier_costs": len(proprietary.get("supplier_costs") or []),
                "benchmarks": len(proprietary.get("benchmarks") or []),
            },
        },
        "structured_report": {
            "renderer": "iidatech.renderers.research_report_renderer.render_structured_research_report",
            "ready": True,
        },
        "engine": "research_brain_primary",
        "llm_calls_required": False,
    }

    try:
        from iidatech.renderers.research_report_renderer import render_structured_research_report

        brain["structured_report"]["payload"] = render_structured_research_report(
            topic, industry, geography, brain
        )
    except Exception as exc:
        brain["structured_report"]["ready"] = False
        brain["structured_report"]["error"] = str(exc)[:200]

    brain["_evidence_rows"] = records
    if str(os.getenv("OPENAI_API_KEY") or "").strip():
        brain = polish_research_brain_cheap(brain, enabled=True)
    attach_real_confidence(brain, records)
    return brain


def apply_research_brain_to_report(report: dict[str, Any], brain: dict[str, Any]) -> dict[str, Any]:
    """Merge research brain output into report payload for synthesis and export."""
    out = dict(report)
    out["research_intelligence"] = brain
    brief = dict(_as_dict(out.get("topic_intelligence_brief")))
    brief["research_brain_market_truth"] = brain.get("market_truth")
    brief["strategic_wedge"] = _as_dict(brain.get("strategic_recommendations")).get("wedge")
    out["topic_intelligence_brief"] = brief
    diligence = dict(_as_dict(out.get("diligence_pack")))
    diligence["research_intelligence"] = brain
    comp_pack = dict(_as_dict(diligence.get("competitor_intelligence_pack")))
    comp_map = _as_dict(brain.get("competitor_map"))
    if comp_map.get("competitor_matrix"):
        comp_pack["competitors"] = comp_map["competitor_matrix"]
        comp_pack["market_gaps"] = comp_map.get("market_gaps") or []
    diligence["competitor_intelligence_pack"] = comp_pack
    out["diligence_pack"] = diligence
    if brain.get("structured_report", {}).get("payload"):
        out["structured_research_report"] = brain["structured_report"]["payload"]
    return out


_POLISH_SYSTEM = (
    "You are an institutional equity research analyst. "
    "Write 3-5 sentences of plain English using ONLY facts present in the JSON payload. "
    "Do not invent numbers, company names, market sizes, or claims that are not in the input. "
    "If evidence is thin or missing, state that explicitly instead of guessing."
)

_POLISH_SECTIONS: tuple[tuple[str, str], ...] = (
    ("market_truth", "Market truth"),
    ("competitor_map", "Competitive landscape"),
    ("customer_truth", "Customer and buyer truth"),
    ("financial_truth", "Financial truth and unit economics"),
    ("strategic_recommendations", "Strategic recommendations"),
)


def _json_blob(value: Any, *, limit: int = 12000) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)[:limit]
    except TypeError:
        return str(value)[:limit]


def polish_research_brain_cheap(brain: dict[str, Any], *, enabled: bool = False) -> dict[str, Any]:
    """Optional cheap-LLM narrative polish; preserves structured brain fields."""
    if not enabled:
        return brain

    from iidatech.services.llm_client import generate_narrative, llm_last_error

    out = dict(brain)
    out["polish_attempted"] = True
    narratives: dict[str, str] = {}
    errors: list[str] = []

    for key, label in _POLISH_SECTIONS:
        payload = out.get(key)
        if not payload:
            continue
        prompt = f"Section: {label}\n\nStructured data (JSON):\n{_json_blob(payload)}"
        text = generate_narrative(prompt, _POLISH_SYSTEM)
        if text:
            narratives[key] = text.strip()
        else:
            errors.append(f"{key}:{llm_last_error() or 'empty_response'}")

    evidence_payload = {
        "missing_evidence": out.get("missing_evidence") or [],
        "confidence_score": out.get("confidence_score"),
    }
    if evidence_payload["missing_evidence"] or evidence_payload["confidence_score"] is not None:
        prompt = (
            "Section: Evidence quality and gaps\n\nStructured data (JSON):\n"
            f"{_json_blob(evidence_payload)}"
        )
        text = generate_narrative(prompt, _POLISH_SYSTEM)
        if text:
            narratives["evidence_quality"] = text.strip()
        else:
            errors.append(f"evidence_quality:{llm_last_error() or 'empty_response'}")

    if narratives:
        out["analyst_narrative"] = narratives

    if errors:
        out["polish_error"] = "; ".join(errors)[:240]
        out["report_degraded"] = True
        out["degradation_reason"] = out["polish_error"]
        out["report_degrade_reason"] = out["polish_error"]

    attach_real_confidence(out, out.get("_evidence_rows"))
    return out


def write_premium_memo(brain: dict[str, Any], *, enabled: bool = False) -> dict[str, Any]:
    """Optional single premium memo call; skipped unless explicitly enabled."""
    if not enabled:
        return {"skipped": True, "reason": "premium_memo_disabled"}
    return {"skipped": True, "reason": "premium_memo_not_configured_in_primary_brain"}


def run_research_brain_fallback(
    topic: str,
    industry: str,
    geography: str,
    report: dict[str, Any],
) -> dict[str, Any]:
    """Backward-compatible alias."""
    brain = run_research_brain(topic, industry, geography, report)
    return {
        **brain,
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "recommended_actions": [
            f"Close gap: {gap}" for gap in brain.get("missing_evidence", [])[:6]
        ],
        "audit": {
            "honest_score": (brain.get("real_confidence") or {}).get("score")
            or max(1.0, brain.get("confidence_score", 0) / 10),
            "investor_ready": not brain.get("missing_evidence"),
            "real_confidence": brain.get("real_confidence"),
        },
    }