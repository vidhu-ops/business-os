"""IIDATECH Failure Trace Engine - diagnostic-only post-report analysis."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

FAILURE_TRACE_DIR = Path(__file__).resolve().parents[2] / "qa_outputs" / "failure_traces"
SCORE_THRESHOLD = 8.0


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _dig(payload: dict, *keys: str, default: Any = None) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
    return cur if cur is not None else default


def report_id_from_payload(payload: dict[str, Any]) -> str:
    topic = str(payload.get("topic") or payload.get("query") or "report")
    geo = str(payload.get("geography") or payload.get("target") or "global")
    base = re.sub(r"[^a-z0-9]+", "_", f"{topic}_{geo}".lower()).strip("_")[:72]
    digest = hashlib.md5(json.dumps({"t": topic, "g": geo}, sort_keys=True).encode()).hexdigest()[:8]
    return f"{base}_{digest}" if base else digest


def _readiness_counts(payload: dict[str, Any]) -> dict[str, int]:
    diligence = _as_dict(payload.get("diligence_pack"))
    readiness = _as_dict(diligence.get("readiness"))
    counts = _as_dict(readiness.get("record_counts"))
    if counts:
        return {k: int(v or 0) for k, v in counts.items()}
    dep = _dig(payload, "final_report_audit", "local_audit_baseline", "dependability_pipeline")
    dep = _as_dict(dep)
    ev = _as_dict(dep.get("evidence_summary"))
    by_type = _as_dict(ev.get("by_type"))
    return {
        "direct_records": int(by_type.get("direct", 0) or 0),
        "proxy_records": int(by_type.get("proxy", 0) or 0),
        "anecdotal_records": int(by_type.get("anecdotal", 0) or 0),
        "named_competitor_operator_records": 0,
        "strict_buyer_validation_records": 0,
        "direct_pricing_unit_cost_records": 0,
    }


def analyze_retrieval_failures(payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    missing: list[str] = []
    layer_hits = 0
    counts = _readiness_counts(payload)
    named_comp = int(counts.get("named_competitor_operator_records", 0) or 0)
    buyer = int(counts.get("strict_buyer_validation_records", 0) or 0)
    pricing = int(counts.get("direct_pricing_unit_cost_records", 0) or 0)
    direct = int(counts.get("direct_records", 0) or 0)
    proxy = int(counts.get("proxy_records", 0) or 0)
    anecdotal = int(counts.get("anecdotal_records", 0) or 0)
    if named_comp < 3:
        layer_hits += 2
        reasons.append(f"Insufficient named competitor evidence ({named_comp}/3 minimum)")
        missing.append("named competitor records (3+ required)")
    if pricing < 2:
        layer_hits += 2
        reasons.append(f"Insufficient direct pricing evidence ({pricing}/2 minimum)")
        missing.append("official or direct pricing pages")
    if buyer < 2:
        layer_hits += 2
        reasons.append(f"Insufficient buyer validation evidence ({buyer}/2 minimum)")
        missing.append("buyer interviews, reviews, or practitioner validation")
    total_classified = max(1, direct + proxy + anecdotal)
    off_topic_ratio = (proxy + anecdotal) / total_classified
    if off_topic_ratio > 0.55:
        layer_hits += 1
        reasons.append(f"High proxy/anecdotal evidence ratio ({off_topic_ratio:.0%})")
        missing.append("topic-matched direct sources")
    diligence = _as_dict(payload.get("diligence_pack"))
    competitors = diligence.get("competitive_benchmark") or []
    if isinstance(competitors, list) and len(competitors) < 2:
        layer_hits += 1
        reasons.append("Competitive benchmark pack is thin or empty")
        missing.append("competitive_benchmark rows with named operators")
    bank_trace = _as_dict(payload.get("evidence_bank_trace"))
    if bank_trace and int(bank_trace.get("bank_hits", 0) or 0) == 0:
        layer_hits += 1
        reasons.append("Competitor bank returned zero hits for this topic")
        missing.append("evidence bank competitor rows for domain")
    return {"layer": "retrieval", "reasons": reasons, "missing_evidence": missing, "weight": layer_hits}


def diligence_bottom_up(payload: dict[str, Any]) -> bool:
    diligence = _as_dict(payload.get("diligence_pack"))
    calc = diligence.get("bottom_up_market_calculation")
    if isinstance(calc, dict) and calc.get("status") not in {None, "", "template_estimated"}:
        return True
    return bool(calc)


def analyze_financial_failures(payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    missing: list[str] = []
    layer_hits = 0
    model = _as_dict(payload.get("quantitative_model"))
    headline = _as_dict(model.get("headline"))
    ue = _as_dict(payload.get("unit_economics_grounding"))
    conf = _as_dict(payload.get("report_confidence"))
    unknowns = ue.get("financial_unknowns") or conf.get("financial_unknowns") or []
    if isinstance(unknowns, dict):
        unknowns = list(unknowns.keys())
    unknown_blob = " ".join(str(u).lower() for u in unknowns) if isinstance(unknowns, list) else str(unknowns).lower()
    tam = _safe_float(headline.get("tam_base") or headline.get("tam") or model.get("tam"), -1)
    tam_fmt = str(headline.get("tam_base_fmt") or "")
    if tam <= 0 or tam_fmt in {"", "$0", "0", "Not validated", "WITHHELD"}:
        layer_hits += 2
        reasons.append("Missing or zero TAM denominator")
        missing.append("verified TAM / addressable buyer count")
    for key, label in (("cac", "CAC"), ("ltv", "LTV"), ("churn", "churn"), ("gross_margin", "gross margin"), ("margin", "margin")):
        if key in unknown_blob or label.lower() in unknown_blob:
            layer_hits += 1
            reasons.append(f"Missing {label}")
            missing.append(label)
    if not diligence_bottom_up(payload):
        layer_hits += 1
        reasons.append("Bottom-up market calculation missing or template-only")
        missing.append("bottom-up TAM/SAM/SOM with sourced inputs")
    funding = _as_dict(_dig(payload, "diligence_pack", "funding_readiness_pack"))
    if funding and not funding.get("funding_ready"):
        layer_hits += 1
        for gap in (funding.get("must_fix_to_be_funding_ready") or [])[:3]:
            if isinstance(gap, str):
                reasons.append(gap[:200])
    return {"layer": "financial_model", "reasons": reasons, "missing_evidence": missing, "weight": layer_hits}


def analyze_synthesis_failures(payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    missing: list[str] = []
    layer_hits = 0
    weak_sections: list[str] = []
    audit = _as_dict(payload.get("final_report_audit"))
    for gap in (audit.get("critical_gaps") or [])[:8]:
        if isinstance(gap, str):
            reasons.append(gap[:220])
            layer_hits += 1
    local = _as_dict(audit.get("local_audit_baseline"))
    dep = _as_dict(local.get("dependability_pipeline"))
    consistency = _as_dict(dep.get("consistency"))
    for issue in (consistency.get("issues") or [])[:5]:
        if isinstance(issue, str):
            reasons.append(f"Consistency: {issue[:180]}")
            layer_hits += 1
    strict = _as_dict(_dig(payload, "diligence_pack", "strict_verification_pack"))
    withheld = int(_dig(strict, "counts", "withheld_numeric_records") or 0)
    if withheld:
        layer_hits += 1
        reasons.append(f"{withheld} numeric claims withheld (unsupported by evidence)")
        missing.append("verified numeric claims for withheld figures")
    sections = _as_dict(payload.get("sections"))
    section_blob = json.dumps(sections, ensure_ascii=False).lower()
    if "unsupported numeric claim removed" in section_blob or "source-gated estimate withheld" in section_blob:
        layer_hits += 1
        reasons.append("Sections contain withheld or stripped unsupported numerics")
    if "[placeholder]" in section_blob or "[x%]" in section_blob:
        layer_hits += 1
        reasons.append("Placeholder tokens remain in section output")
    eval_scores = _as_dict(payload.get("eval_scores"))
    for sec_id, ev in eval_scores.items():
        if isinstance(ev, dict) and isinstance(ev.get("overall_score"), (int, float)) and float(ev.get("overall_score")) < 8.0:
            weak_sections.append(str(ev.get("section") or sec_id))
            layer_hits += 1
    if weak_sections:
        reasons.append("Weak sections below 8/10: " + ", ".join(weak_sections[:6]))
    citation_ledger = _dig(payload, "diligence_pack", "citation_ledger") or []
    if isinstance(citation_ledger, list) and citation_ledger:
        low_grade = sum(1 for row in citation_ledger if isinstance(row, dict) and str(row.get("source_label", "")).upper() in {"UNVERIFIED", "C", "D"})
        if low_grade > len(citation_ledger) * 0.6:
            layer_hits += 1
            reasons.append(f"Weak citation grade dominates ledger ({low_grade}/{len(citation_ledger)} unverified/low)")
            missing.append("grade-A/B citations for investor use")
    return {"layer": "synthesis", "reasons": reasons, "missing_evidence": missing, "weak_sections": weak_sections, "weight": layer_hits}


def analyze_business_plan_failures(payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    missing: list[str] = []
    layer_hits = 0
    plan = _as_dict(payload.get("business_build_plan") or payload.get("execution_blueprint"))
    if not plan:
        return {"layer": "business_layer", "reasons": [], "missing_evidence": [], "weight": 0}
    gtm = _as_dict(plan.get("go_to_market") or plan.get("gtm"))
    gtm_blob = json.dumps(gtm, ensure_ascii=False).lower()
    if not gtm or len(gtm_blob) < 80:
        layer_hits += 1
        reasons.append("GTM section missing or generic")
        missing.append("specific GTM channels, ICP, and proof metric")
    elif not any(tok in gtm_blob for tok in ("channel", "icp", "pilot", "geo", "city", "segment")):
        layer_hits += 1
        reasons.append("GTM lacks channel/ICP/geo specificity")
        missing.append("named geography and buyer segment in GTM")
    tasks = plan.get("employee_execution_system") or plan.get("execution_tasks") or []
    task_count = 0
    if isinstance(tasks, dict):
        for emp in tasks.get("tasks_by_employee") or []:
            if isinstance(emp, dict):
                task_count += len(emp.get("tasks") or [])
    elif isinstance(tasks, list):
        task_count = len(tasks)
    if task_count < 5:
        layer_hits += 1
        reasons.append(f"Execution task coverage thin ({task_count} tasks)")
        missing.append("actionable execution tasks by role")
    ue = _as_dict(plan.get("unit_economics"))
    if not ue or not any(ue.get(k) for k in ("cac", "ltv", "payback", "gross_margin", "contribution_margin")):
        layer_hits += 1
        reasons.append("Business plan unit economics not grounded")
        missing.append("sourced CAC/LTV/margin in business plan")
    return {"layer": "business_layer", "reasons": reasons, "missing_evidence": missing, "weight": layer_hits}


def _selection_failures(payload: dict[str, Any]) -> dict[str, Any]:
    reasons: list[str] = []
    missing: list[str] = []
    layer_hits = 0
    completeness = _as_dict(payload.get("evidence_completeness"))
    score = _safe_float(completeness.get("score"), 0)
    if score and score < 60:
        layer_hits += 2
        reasons.append(f"Evidence completeness score low ({score}/100)")
        missing.append("higher completeness across pricing, competitor, buyer families")
    conf = _as_dict(payload.get("report_confidence"))
    if str(conf.get("research_confidence", "")).lower() == "low":
        layer_hits += 1
        reasons.append("Research confidence rated Low")
        missing.append("additional direct research sources")
    harvest = _as_dict(payload.get("auto_research_harvest") or payload.get("harvest_result"))
    trace = _as_dict(harvest.get("evidence_bank_trace") or payload.get("evidence_bank_trace"))
    if trace:
        total_hits = sum(int(trace.get(k, 0) or 0) for k in ("bank_hits", "serp_competitor_hits", "exact_search_hits", "exa_hits", "tavily_hits"))
        if total_hits == 0:
            layer_hits += 2
            reasons.append("All live retrieval layers returned zero hits")
            missing.append("successful Exa/Tavily/Serp retrieval pass")
    return {"layer": "selection", "reasons": reasons, "missing_evidence": missing, "weight": layer_hits}


def _pick_bottleneck(layer_results: list[dict[str, Any]]) -> str:
    if not layer_results:
        return "retrieval"
    best = max(layer_results, key=lambda r: int(r.get("weight") or 0))
    if int(best.get("weight") or 0) == 0:
        return "synthesis"
    return str(best.get("layer") or "synthesis")


def _recommended_fix(bottleneck: str, missing: list[str]) -> str:
    fixes = {
        "retrieval": "Run targeted harvest: competitor bank + Serp discovery + pricing-page exact search before re-synthesis.",
        "selection": "Tighten evidence ranking filters and raise minimum direct-record threshold per section family.",
        "synthesis": "Re-run weak sections with compressed high-trust evidence only; strip unsupported numerics.",
        "financial_model": "Populate bottom-up model with sourced buyer count, ACV, and churn; gate TAM until verified.",
        "business_layer": "Regenerate business blueprint after financial and competitor gaps are closed.",
    }
    base = fixes.get(bottleneck, "Review failure trace and close top missing evidence items.")
    if missing:
        return f"{base} Priority gaps: {'; '.join(missing[:4])}."
    return base


def build_failure_trace(report_payload: dict[str, Any]) -> dict[str, Any]:
    payload = report_payload if isinstance(report_payload, dict) else {}
    audit = _as_dict(payload.get("final_report_audit"))
    report_score = _safe_float(audit.get("market_style_score") or payload.get("production_score") or payload.get("score"), 0.0)
    funding_ready = bool(audit.get("funding_ready") if audit.get("funding_ready") is not None else payload.get("funding_ready", False))
    investor_ready = bool(
        audit.get("investor_ready")
        if audit.get("investor_ready") is not None
        else payload.get("investor_ready", False)
    )
    analyzers = [analyze_retrieval_failures(payload), _selection_failures(payload), analyze_synthesis_failures(payload), analyze_financial_failures(payload), analyze_business_plan_failures(payload)]
    failure_reasons: list[str] = []
    missing_evidence: list[str] = []
    weak_sections: list[str] = []
    layer_scores: dict[str, int] = {}
    for result in analyzers:
        layer = str(result.get("layer") or "unknown")
        layer_scores[layer] = int(result.get("weight") or 0)
        for r in result.get("reasons") or []:
            if isinstance(r, str) and r not in failure_reasons:
                failure_reasons.append(r)
        for m in result.get("missing_evidence") or []:
            if isinstance(m, str) and m not in missing_evidence:
                missing_evidence.append(m)
        for w in result.get("weak_sections") or []:
            if isinstance(w, str) and w not in weak_sections:
                weak_sections.append(w)
    bottleneck = _pick_bottleneck(analyzers)
    return {
        "report_id": report_id_from_payload(payload),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topic": payload.get("topic"),
        "geography": payload.get("geography") or payload.get("target"),
        "report_score": round(report_score, 2),
        "funding_ready": funding_ready,
        "investor_ready": investor_ready,
        "failure_reasons": failure_reasons[:30],
        "missing_evidence": missing_evidence[:20],
        "weak_sections": weak_sections[:15],
        "bottleneck_layer": bottleneck,
        "layer_scores": layer_scores,
        "recommended_fix": _recommended_fix(bottleneck, missing_evidence),
        "top_failure_reasons": failure_reasons[:5],
    }


def export_failure_trace(trace: dict[str, Any], *, report_id: str | None = None) -> Path:
    rid = report_id or str(trace.get("report_id") or "unknown_report")
    FAILURE_TRACE_DIR.mkdir(parents=True, exist_ok=True)
    path = FAILURE_TRACE_DIR / f"{rid}.json"
    path.write_text(json.dumps(trace, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def aggregate_failure_causes_from_summaries(summaries: list[dict[str, Any]], *, top_n: int = 5) -> list[tuple[str, int]]:
    counts: dict[str, int] = {}
    for row in summaries:
        payload = {"topic": row.get("topic"), "geography": row.get("target") or row.get("geography"), "funding_ready": row.get("funding_ready"), "score": row.get("score") or row.get("production_score"), "final_report_audit": row.get("audit") or {}, "diligence_pack": row.get("diligence_pack") or {}, "report_confidence": row.get("report_confidence") or {}}
        trace = build_failure_trace(payload)
        for reason in trace.get("failure_reasons") or []:
            key = reason[:80]
            counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:top_n]