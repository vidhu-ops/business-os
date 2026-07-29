"""Pass 0 - business context with Data Truth Layer enrichment."""
from __future__ import annotations
import copy
from typing import Any

def _as_dict(v):
    return v if isinstance(v, dict) else {}

def _as_list(v):
    return v if isinstance(v, list) else []

def _compact_sections(sections, max_chars=12000):
    if not isinstance(sections, dict):
        return {}
    out, used = {}, 0
    for key, payload in sections.items():
        if used >= max_chars:
            break
        if isinstance(payload, dict):
            text = str(payload.get("content") or payload.get("markdown") or payload.get("text") or "")[:2000]
            out[str(key)] = {"title": payload.get("title") or key, "summary": text[:1200]}
            used += len(text)
    return out

def _extract_pricing_anchor(diligence, quantitative):
    anchors = []
    pack = _as_dict(diligence.get("pricing_intelligence_pack"))
    for row in _as_list(pack.get("packages") or pack.get("pricing_rows") or pack.get("rows")):
        if isinstance(row, dict):
            anchors.append({"package": row.get("package"), "price_band": row.get("estimated_price_band") or row.get("price_band"), "source_status": row.get("what_to_verify", "verify"), "evidence_tier": row.get("evidence_tier", "estimated")})
    ue = _as_dict(quantitative.get("unit_economics") or quantitative.get("unit_economics_grounding"))
    if ue:
        anchors.append({"package": "unit_economics_from_report", "price_band": ue.get("arpu") or ue.get("acv"), "source_status": ue.get("source_note", "report"), "evidence_tier": ue.get("evidence_tier", "derived")})
    return anchors[:20]

def _extract_competitor_map(diligence, boardroom, competitor_intel):
    rows = []
    for comp in _as_list(_as_dict(competitor_intel).get("competitors")):
        if isinstance(comp, dict) and comp.get("name"):
            rows.append({"name": comp.get("name"), "pricing": comp.get("pricing"), "strengths": _as_list(comp.get("strengths")), "weaknesses": _as_list(comp.get("weaknesses")), "gaps": [comp.get("market_gap")] if comp.get("market_gap") else [], "source": "competitor_intelligence_agent"})
    if rows:
        return rows[:25]
    for row in _as_list(diligence.get("competitive_benchmark")):
        if isinstance(row, dict):
            rows.append({"name": row.get("competitor_archetypes") or row.get("segment"), "pricing": row.get("benchmark_metrics"), "strengths": [str(row.get("benchmark_metrics", ""))[:120]], "weaknesses": [str(row.get("source_need", ""))[:120]], "gaps": [str(row.get("source_need", ""))[:120]], "source": "diligence_pack.competitive_benchmark"})
    return rows[:25]

def _extract_risks(audit, boardroom, investment):
    risks = []
    for source, payload in (("final_report_audit", audit), ("boardroom_strategist", boardroom), ("investment_decision", investment)):
        if not isinstance(payload, dict):
            continue
        for key in ("critical_gaps", "fatal_flaws", "risks", "blocking_issues", "red_flags"):
            for item in _as_list(payload.get(key)):
                risks.append({"source": source, "risk": str(item.get("finding") if isinstance(item, dict) else item)[:500]})
        verdict = payload.get("executive_verdict") or payload.get("verdict")
        if isinstance(verdict, str) and len(verdict) > 20:
            risks.append({"source": source, "risk": verdict[:500]})
    return risks[:30]

def _citation_records(report_context):
    diligence = _as_dict(report_context.get("diligence_pack"))
    ledger = diligence.get("citation_ledger")
    if isinstance(ledger, list):
        return ledger
    if isinstance(ledger, dict):
        return _as_list(ledger.get("sources"))
    return []

def _infer_domain(idea, industry):
    text = f"{idea} {industry}".lower()
    if any(x in text for x in ("crm", "saas", "b2b", "software")):
        return "crm_automation"
    if any(x in text for x in ("skincare", "d2c", "ecommerce", "retail")):
        return "ecommerce_retail"
    if any(x in text for x in ("automotive", "garage", "repair")):
        return "automotive"
    if any(x in text for x in ("health", "clinic", "dental")):
        return "healthcare"
    return "general"

def build_business_context_object(idea, industry, geography, report_context, evidence_items, *, domain: str = ""):
    report_context = copy.deepcopy(report_context) if isinstance(report_context, dict) else {}
    diligence = _as_dict(report_context.get("diligence_pack"))
    quantitative = _as_dict(report_context.get("quantitative_model"))
    sections = report_context.get("sections") or {}
    boardroom = _as_dict(report_context.get("boardroom_strategist"))
    investment = _as_dict(report_context.get("investment_decision"))
    audit = _as_dict(report_context.get("final_report_audit"))
    brief = _as_dict(report_context.get("topic_intelligence_brief"))
    domain = domain or _infer_domain(idea, industry)
    citation_records = _citation_records(report_context)

    truth_summary = {}
    competitor_intel = {}
    financial_benchmark_pack = {}
    interview_pack = {}
    try:
        from iidatech.retrieval.source_trust import summarize_truth_quality, apply_truth_weighting
        truth_summary = summarize_truth_quality(apply_truth_weighting(citation_records + list(evidence_items or [])))
    except Exception:
        pass
    try:
        from iidatech.services.competitor_intelligence import build_competitor_intelligence
        competitor_intel = build_competitor_intelligence(citation_records + list(evidence_items or []), diligence_pack=diligence)
    except Exception:
        pass
    try:
        from iidatech.data.financial_benchmark_bank import build_benchmark_financial_pack
        currency = "INR" if "india" in str(geography).lower() else "USD"
        financial_benchmark_pack = build_benchmark_financial_pack(domain, currency=currency)
    except Exception:
        pass
    try:
        from iidatech.services.interview_agent import build_interview_questionnaire
        interview_pack = build_interview_questionnaire(domain)
    except Exception:
        pass

    market_truth = {
        "idea": idea, "industry": industry, "geography": geography,
        "tam": quantitative.get("tam") or quantitative.get("TAM"),
        "sam": quantitative.get("sam") or quantitative.get("SAM"),
        "som": quantitative.get("som") or quantitative.get("SOM"),
        "cagr": quantitative.get("cagr") or quantitative.get("CAGR"),
        "bottom_up": _as_dict(report_context.get("bottom_up_market_model")),
        "topic_intelligence": brief,
        "unit_economics_grounding": report_context.get("unit_economics_grounding"),
        "financial_benchmark_pack": financial_benchmark_pack,
    }

    completeness = _as_dict(report_context.get("evidence_completeness"))
    return {
        "meta": {"idea": idea, "industry": industry, "geography": geography, "domain": domain},
        "market_truth": market_truth,
        "competitor_map": _extract_competitor_map(diligence, boardroom, competitor_intel),
        "competitor_intelligence": competitor_intel,
        "pricing_anchor": _extract_pricing_anchor(diligence, quantitative),
        "boardroom_verdict": boardroom,
        "investment_decision": investment,
        "audit_findings": audit,
        "market_sections": _compact_sections(sections),
        "diligence": diligence,
        "risks": _extract_risks(audit, boardroom, investment),
        "evidence_quality": {
            "evidence_completeness_score": completeness.get("score"),
            "citation_ledger_count": len(citation_records),
            "uploaded_evidence_count": len(evidence_items or []),
            "source_truth_summary": truth_summary,
        },
        "interview_readiness": interview_pack,
        "raw_report_keys": sorted(report_context.keys()) if report_context else [],
    }