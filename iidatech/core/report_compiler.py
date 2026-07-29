"""Canonical report compiler -- single source of truth for customer-facing IIDATECH output."""
from __future__ import annotations

import re
from typing import Any

from iidatech.core.numeric_engine import SECTION_BLOCKED, SECTION_PARTIAL, SECTION_VALID, build_numeric_truth
from iidatech.report_modes import (
    REPORT_MODE_BUSINESS_BUILDER,
    REPORT_MODE_INVESTOR_MEMO,
    REPORT_MODE_RESEARCH,
    filter_v3_report_object,
    infer_report_mode,
)
from iidatech.renderers.report_v3_enhancements import build_execution_calendar, build_risk_heatmap
from iidatech.renderers.report_v3_truth import compute_report_truth_confidence, metric
from iidatech.validation.competitor_evidence import (
    DEFAULT_COMPETITOR_EVIDENCE_GAPS,
    filter_verified_competitor_matrix,
    filter_verified_pricing_rows,
    is_synthetic_competitor_name,
    is_verified_pricing_row,
)

_VALIDATION = "VALIDATION REQUIRED"
_SCHEMA_VERSION = "iidatech_report_v3"
_GENERIC_ICP = re.compile(r"^(primary buyer|workflow buyer|named buyer|generic buyer|icp\s*[#:]?\s*\d+)", re.I)
_RISK_CATEGORIES = ("market", "pricing", "operational", "demand", "financial")

_CUSTOMER_VERDICT = {
    "STRONG_YES": "BUILD",
    "CONDITIONAL_YES": "BUILD WITH CONDITIONS",
    "MAYBE": "BUILD WITH CONDITIONS",
    "NO": "DO NOT BUILD",
    "BUILD": "BUILD",
    "AVOID": "DO NOT BUILD",
}


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


def _fmt_money(v: Any) -> str:
    if v in (None, "", "WITHHELD"):
        return _VALIDATION
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        s = str(v).strip()
        return s if s else _VALIDATION


def _text(v: Any) -> str:
    if v in (None, ""):
        return _VALIDATION
    return str(v).strip()


def _brain(payload: dict) -> dict:
    ri = payload.get("research_intelligence")
    if isinstance(ri, dict) and ri:
        return ri
    return _as_dict(_as_dict(payload.get("diligence_pack")).get("research_intelligence"))


def _is_generic_icp(name: str) -> bool:
    n = str(name or "").strip()
    if not n or n == _VALIDATION:
        return True
    if _GENERIC_ICP.match(n):
        return True
    if re.match(r"^icp\s+\d+\s*:", n, re.I):
        return True
    return False


def _section_status(has_valid: bool, has_partial: bool) -> str:
    if has_valid:
        return SECTION_VALID if not has_partial else SECTION_PARTIAL
    return SECTION_BLOCKED


def _metric_from_numeric(nm: dict[str, Any] | None) -> dict[str, Any]:
    if not nm:
        return metric(None, source="numeric_engine", validation_state="validation_required")
    val = nm.get("value")
    if isinstance(val, dict):
        val = val.get("value")
    if nm.get("withheld") or val in (None, "", "WITHHELD"):
        return metric(
            None,
            source=str(nm.get("source") or "strict_verification_pack"),
            confidence="low",
            validation_state="withheld",
        )
    verified = bool(nm.get("verified"))
    state = "validated" if verified else "estimated"
    return metric(
        val,
        source=str(nm.get("source") or "numeric_engine"),
        confidence=str(nm.get("confidence") or "medium"),
        validation_state=state,
        display=_fmt_money(val) if _num(val) is not None and str(nm.get("key")) in {"tam", "sam", "som", "cac", "ltv", "arpu"} else None,
    )


def _identity_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    market = _as_dict(brain.get("market_truth"))
    snapshot = _as_dict(payload.get("_identity_snapshot"))
    mode = infer_report_mode(
        str(payload.get("topic") or snapshot.get("topic") or ""),
        payload.get("report_mode"),
        workflow_choice=str(payload.get("workflow_choice") or ""),
    )
    return {
        "topic": str(payload.get("topic") or snapshot.get("topic") or market.get("topic") or ""),
        "industry": str(payload.get("industry") or snapshot.get("industry") or market.get("industry") or ""),
        "geography": str(
            payload.get("target")
            or payload.get("geography")
            or payload.get("report_geography")
            or snapshot.get("geography")
            or market.get("geography")
            or ""
        ),
        "report_mode": mode,
    }


def _competitor_truth_from_brain(payload: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    comp = _as_dict(brain.get("competitor_map"))
    structured = _as_dict(payload.get("structured_research_report"))
    raw_matrix = _as_list(comp.get("competitor_matrix")) or _as_list(
        _as_dict(structured.get("competitor_analysis")).get("matrix")
    )
    matrix = filter_verified_competitor_matrix(raw_matrix)
    rows: list[dict[str, Any]] = []
    for row in matrix[:12]:
        name = _text(row.get("name") or row.get("competitor"))
        if is_synthetic_competitor_name(name):
            continue
        price_raw = row.get("pricing") or row.get("price_band") or row.get("price")
        rows.append(
            {
                "name": name,
                "positioning": _text(row.get("positioning") or row.get("segment") or row.get("plan")),
                "pricing": _fmt_money(price_raw) if _num(price_raw) is not None else _text(price_raw),
                "source": row.get("source"),
                "trust_score": row.get("trust_score"),
            }
        )
    status = SECTION_VALID if rows else SECTION_BLOCKED
    return {
        "status": status,
        "owner": "research_brain",
        "competitor_count": len(rows),
        "market_leaders": [
            n for n in _as_list(comp.get("market_leaders"))[:5] if not is_synthetic_competitor_name(n)
        ],
        "matrix": rows,
        "feature_gaps": _as_list(comp.get("feature_gap"))[:6],
        "market_gaps": _as_list(comp.get("market_gaps"))[:6],
        "missing_evidence": list(DEFAULT_COMPETITOR_EVIDENCE_GAPS) if not rows else [],
    }


def _pricing_truth_from_brain(payload: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    comp = _as_dict(brain.get("competitor_map"))
    diligence = _as_dict(payload.get("diligence_pack"))
    strat = _as_dict(brain.get("strategic_recommendations"))
    rows: list[dict[str, Any]] = []
    for row in filter_verified_pricing_rows(_as_list(comp.get("competitor_matrix"))):
        rows.append(
            {
                "competitor": _text(row.get("name") or row.get("competitor")),
                "plan": _text(row.get("plan") or row.get("segment")),
                "price": _fmt_money(row.get("price") or row.get("pricing") or row.get("price_band")),
                "source": row.get("source"),
            }
        )
    for row in _as_list(diligence.get("competitive_benchmark")):
        if isinstance(row, dict) and is_verified_pricing_row(row):
            rows.append(
                {
                    "competitor": _text(row.get("competitor") or row.get("competitor_archetypes")),
                    "plan": _text(row.get("plan") or row.get("tier")),
                    "price": _text(row.get("price_band") or row.get("pricing")),
                    "source": row.get("source"),
                }
            )
    bands = comp.get("pricing_bands") if isinstance(comp.get("pricing_bands"), dict) else {}
    has_bands = bool(bands) and any(_num(v) is not None for v in bands.values())
    status = SECTION_VALID if rows else (SECTION_PARTIAL if has_bands else SECTION_BLOCKED)
    return {
        "status": status,
        "owner": "research_brain",
        "bands": bands if has_bands else {},
        "competitor_pricing_table": rows,
        "wedge": _text(strat.get("best_wedge") or strat.get("wedge")),
        "missing_evidence": [] if rows else ["pricing pages"],
    }


def _customer_truth_from_brain(payload: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    cust = _as_dict(brain.get("customer_truth"))
    diligence = _as_dict(payload.get("diligence_pack"))
    structured = _as_dict(payload.get("structured_research_report"))
    survey = _as_dict(diligence.get("survey_interview_findings"))

    profiles: list[dict[str, Any]] = []
    for row in (
        _as_list(survey.get("icp_profiles"))
        + _as_list(survey.get("buyer_profiles"))
        + _as_list(cust.get("icp_profiles"))
        + _as_list(cust.get("buyer_personas"))
        + _as_list(cust.get("segments"))
    ):
        if isinstance(row, dict):
            profiles.append(row)
        elif isinstance(row, str) and row.strip():
            profiles.append({"name": row.strip()})

    icps: list[dict[str, Any]] = []
    seen: set[str] = set()
    for p in profiles:
        name = str(p.get("name") or p.get("named_buyer_profile") or p.get("segment") or "").strip()
        if not name or _is_generic_icp(name):
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        icps.append(
            {
                "name": name,
                "pain": _text(p.get("pain") or p.get("primary_pain")),
                "trigger": _text(p.get("buyer_trigger") or p.get("trigger")),
                "wtp": _text(p.get("willingness_to_pay") or p.get("wtp")),
                "decision_maker": _text(p.get("decision_maker")),
            }
        )
        if len(icps) >= 3:
            break

    pains = _as_list(cust.get("top_pains")) or _as_list(
        _as_dict(structured.get("customer_analysis")).get("top_pains")
    )
    ranked: list[dict[str, Any]] = []
    for i, p in enumerate(pains[:8], start=1):
        if isinstance(p, dict):
            ranked.append(
                {
                    "rank": i,
                    "category": _text(p.get("category") or p.get("theme")),
                    "evidence": _text(p.get("sample") or p.get("evidence") or p.get("pain")),
                }
            )

    wtp = cust.get("wtp_distribution") or _as_dict(structured.get("customer_analysis")).get("wtp_distribution")
    objections = _as_list(cust.get("dominant_objections")) or _as_list(cust.get("objections"))

    has_icp = bool(icps)
    has_pains = bool(ranked)
    status = _section_status(has_icp or has_pains, has_icp and not has_pains)
    if not has_icp and not has_pains:
        status = SECTION_BLOCKED

    return {
        "status": status,
        "owner": "research_brain",
        "icps": icps,
        "ranked_pains": ranked,
        "wtp": wtp if wtp not in (None, "", {}) else None,
        "objections": objections[:8],
        "missing_evidence": [] if has_icp else ["buyer interviews / ICP validation"],
    }


def _market_truth_from_brain(payload: dict[str, Any], numeric: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    market = _as_dict(brain.get("market_truth"))
    comp = _as_dict(brain.get("competitor_map"))
    qmodel = _as_dict(payload.get("quantitative_model"))
    nm = _as_dict(numeric.get("metrics"))
    sizes = {k: _metric_from_numeric(nm.get(k)) for k in ("tam", "sam", "som")}
    has_size = any(_num(s.get("value")) is not None for s in sizes.values())
    gaps = _as_list(comp.get("market_gaps"))[:6]
    status = numeric.get("status") if has_size else SECTION_BLOCKED
    return {
        "status": status,
        "owner": "research_brain",
        "vertical": market.get("vertical") or payload.get("industry"),
        "market_sizes": sizes,
        "growth": market.get("cagr") or qmodel.get("cagr"),
        "gaps": gaps,
        "observations": _as_list(brain.get("missing_evidence"))[:8],
        "missing_evidence": _as_list(numeric.get("missing_evidence")),
    }


def _investment_truth_from_boardroom(payload: dict[str, Any]) -> dict[str, Any]:
    investment = _as_dict(payload.get("investment_decision"))
    audit = _as_dict(payload.get("final_report_audit"))
    brain = _brain(payload)
    raw = investment.get("verdict") or investment.get("investment_verdict") or ""
    scorecard = _as_dict(investment.get("scorecard"))
    has_verdict = bool(str(raw).strip())
    status = SECTION_VALID if has_verdict else SECTION_BLOCKED
    key = str(raw or "MAYBE").upper().replace(" ", "_")
    return {
        "status": status,
        "owner": "boardroom",
        "verdict": str(raw).upper() if raw else "",
        "customer_decision": _CUSTOMER_VERDICT.get(key, "BUILD WITH CONDITIONS") if has_verdict else _VALIDATION,
        "investment_score": investment.get("investment_score"),
        "rationale": _as_list(investment.get("rationale")),
        "risks": _as_list(investment.get("risks")) or _as_list(brain.get("risk_flags")),
        "audit_score": audit.get("market_style_score") or audit.get("report_score"),
        "funding_ready": audit.get("funding_ready"),
        "confidence_score": brain.get("confidence_score") or scorecard.get("confidence_score"),
    }


def _risk_truth_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    investment = _as_dict(payload.get("investment_decision"))
    audit = _as_dict(payload.get("final_report_audit"))
    by_cat: dict[str, Any] = {}
    for item in _as_list(brain.get("risk_flags")) + _as_list(investment.get("risks")):
        if isinstance(item, dict):
            cat = str(item.get("category") or "market").lower()
            by_cat.setdefault(cat, item)
        elif isinstance(item, str) and item.strip():
            by_cat.setdefault("market", {"probability": "medium", "impact": item.strip()[:200], "mitigation": _VALIDATION})
    structured: list[dict[str, Any]] = []
    for cat in _RISK_CATEGORIES:
        row = by_cat.get(cat, {})
        structured.append(
            {
                "category": cat,
                "probability": _text(row.get("probability") if isinstance(row, dict) else None),
                "impact": _text(row.get("impact") if isinstance(row, dict) else row),
                "mitigation": _text(row.get("mitigation") if isinstance(row, dict) else None),
            }
        )
    status = SECTION_VALID if structured else SECTION_BLOCKED
    return {"status": status, "owner": "boardroom", "risk_map": structured, "audit": audit}


def _gtm_truth_from_engine(payload: dict[str, Any], canonical_interim: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    strat = _as_dict(brain.get("strategic_recommendations"))
    plan = payload.get("business_plan") if isinstance(payload.get("business_plan"), dict) else {}
    v3_stub = {
        "topic": canonical_interim.get("identity", {}).get("topic"),
        "unit_economics": {
            "table": _unit_table_from_numeric(_as_dict(canonical_interim.get("numeric_truth")))
        },
        "go_to_market": {
            "channels": _as_list(strat.get("launch_strategy")),
            "positioning": _as_dict(strat.get("positioning")),
        },
    }
    try:
        from iidatech.services.gtm_engine import build_gtm_channel_economics, build_gtm_engine

        gtm_eng = build_gtm_engine(v3_stub, plan)
        channel_econ = build_gtm_channel_economics({**v3_stub, "go_to_market": {"gtm_engine": gtm_eng}})
        status = SECTION_VALID if _as_list(gtm_eng.get("acquisition_channels")) else SECTION_BLOCKED
        return {
            "status": status,
            "owner": "gtm_engine",
            "vertical": gtm_eng.get("vertical"),
            "acquisition_channels": _as_list(gtm_eng.get("acquisition_channels")),
            "recommended_launch_sequence": _as_list(gtm_eng.get("recommended_launch_sequence")),
            "first_channel": gtm_eng.get("first_channel"),
            "scale_channel": gtm_eng.get("scale_channel"),
            "channel_economics": channel_econ,
            "positioning": _as_dict(strat.get("positioning")),
            "launch_strategy": _as_list(strat.get("launch_strategy")) or _as_list(strat.get("gtm")),
            "moat": _as_list(strat.get("moat_strategy"))[:5],
        }
    except Exception:
        return {
            "status": SECTION_BLOCKED,
            "owner": "gtm_engine",
            "missing_evidence": ["GTM channel validation"],
        }


def _unit_table_from_numeric(numeric: dict[str, Any]) -> list[dict[str, Any]]:
    nm = _as_dict(numeric.get("metrics"))
    rows: list[dict[str, Any]] = []
    labels = {
        "cac": "CAC",
        "ltv": "LTV",
        "arpu": "ARPU",
        "gross_margin": "Gross margin",
        "payback_months": "Payback (months)",
        "burn_multiple": "Burn multiple",
    }
    for key, label in labels.items():
        m = nm.get(key)
        if not m:
            continue
        rows.append({"metric": label, **_metric_from_numeric(m)})
    return rows


def _execution_truth_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    brain = _brain(payload)
    strat = _as_dict(brain.get("strategic_recommendations"))
    diligence = _as_dict(payload.get("diligence_pack"))
    blueprint = payload.get("execution_blueprint") if isinstance(payload.get("execution_blueprint"), dict) else {}
    if not blueprint:
        blueprint = _as_dict(diligence.get("execution_blueprint"))
    first_rev = _as_list(strat.get("first_revenue_path")) or _as_list(strat.get("fast_revenue_path"))
    launch = _as_list(strat.get("launch_strategy")) or _as_list(strat.get("gtm"))
    has = bool(first_rev or launch or blueprint)
    status = SECTION_VALID if has else SECTION_BLOCKED
    return {
        "status": status,
        "owner": "gtm_engine",
        "first_revenue_path": first_rev,
        "launch_strategy": launch,
        "blueprint": blueprint,
    }


def _execution_plan_block(canonical: dict[str, Any]) -> dict[str, Any]:
    ex = _as_dict(canonical.get("execution_truth"))
    if ex.get("status") == SECTION_BLOCKED:
        blocked = {"actions": [_VALIDATION], "milestones": [_VALIDATION], "kpi": _VALIDATION, "budget": _VALIDATION}
        return {
            "day_1_7": blocked,
            "week_2_4": blocked,
            "month_2_3": blocked,
            "month_3_6": blocked,
            "first_revenue_path": [_VALIDATION],
            "status": SECTION_BLOCKED,
        }
    blueprint = _as_dict(ex.get("blueprint"))
    p0 = _as_dict(blueprint.get("phase_0_validation"))
    day_actions = [str(t.get("task") or t)[:200] for t in _as_list(p0.get("daily_tasks")) if isinstance(t, dict)]
    return {
        "day_1_7": {"actions": day_actions or _as_list(ex.get("launch_strategy"))[:3] or [_VALIDATION], "milestones": [_VALIDATION], "kpi": _VALIDATION, "budget": _VALIDATION},
        "week_2_4": {"actions": [_VALIDATION], "milestones": [_VALIDATION], "kpi": _VALIDATION, "budget": _VALIDATION},
        "month_2_3": {"actions": [_VALIDATION], "milestones": [_VALIDATION], "kpi": _VALIDATION, "budget": _VALIDATION},
        "month_3_6": {"actions": [_VALIDATION], "milestones": [_VALIDATION], "kpi": _VALIDATION, "budget": _VALIDATION},
        "first_revenue_path": ex.get("first_revenue_path") or [_VALIDATION],
        "status": ex.get("status"),
    }


def build_canonical_report(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Assemble canonical truth via Truth Arbiter (sole customer-facing writer)."""
    from iidatech.core.truth_arbiter import adapt_arbiter_truth_for_compiler, build_canonical_truth_object

    payload = payload if isinstance(payload, dict) else {}
    truth = build_canonical_truth_object(payload)
    return adapt_arbiter_truth_for_compiler(truth)


def validate_canonical_report(report: dict[str, Any] | None) -> dict[str, Any]:
    """Validate canonical report; annotate metadata with violations."""
    report = report if isinstance(report, dict) else {}
    violations: list[str] = []
    identity = _as_dict(report.get("identity"))
    if not str(identity.get("topic") or "").strip():
        violations.append("missing_topic")

    comp = _as_dict(report.get("competitor_truth"))
    for row in _as_list(comp.get("matrix")):
        if isinstance(row, dict) and is_synthetic_competitor_name(row.get("name")):
            violations.append("synthetic_competitor_in_canonical")

    cust = _as_dict(report.get("customer_truth"))
    for icp in _as_list(cust.get("icps")):
        if isinstance(icp, dict) and _is_generic_icp(icp.get("name")):
            violations.append("generic_icp_in_canonical")

    meta = _as_dict(report.get("metadata"))
    meta["validation_ok"] = not violations
    meta["violations"] = violations
    report["metadata"] = meta
    return {"ok": not violations, "violations": violations, "report": report}


def _executive_from_investment(inv: dict[str, Any]) -> dict[str, Any]:
    return {
        "decision": inv.get("customer_decision") or _VALIDATION,
        "source_verdict": inv.get("verdict") or _VALIDATION,
        "confidence_score": _num(inv.get("confidence_score")) or 0,
        "investment_score": inv.get("investment_score"),
        "funding_ready": inv.get("funding_ready") if inv.get("funding_ready") is not None else _VALIDATION,
        "reasons_for": (inv.get("rationale") or [])[:3] or [_VALIDATION],
        "reasons_against": (inv.get("risks") or [])[:3] or [_VALIDATION],
    }


def _compile_v3_base(canonical: dict[str, Any]) -> dict[str, Any]:
    identity = _as_dict(canonical.get("identity"))
    market = _as_dict(canonical.get("market_truth"))
    comp = _as_dict(canonical.get("competitor_truth"))
    price = _as_dict(canonical.get("pricing_truth"))
    cust = _as_dict(canonical.get("customer_truth"))
    numeric = _as_dict(canonical.get("numeric_truth"))
    gtm = _as_dict(canonical.get("gtm_truth"))
    risk = _as_dict(canonical.get("risk_truth"))
    inv = _as_dict(canonical.get("investment_truth"))
    meta = _as_dict(canonical.get("metadata"))

    competitor_truth = {
        "competitor_count": comp.get("competitor_count", 0),
        "market_leaders": comp.get("market_leaders") or [],
        "matrix": comp.get("matrix") or [],
        "feature_gaps": comp.get("feature_gaps") or list(DEFAULT_COMPETITOR_EVIDENCE_GAPS),
        "status": comp.get("status"),
        "missing_evidence": comp.get("missing_evidence") or [],
    }
    if comp.get("status") == SECTION_BLOCKED:
        competitor_truth["status"] = "evidence_gap"

    customer_truth = {
        "icps": cust.get("icps") or [],
        "ranked_pains": cust.get("ranked_pains") or [],
        "wtp": cust.get("wtp") if cust.get("wtp") not in (None, "", {}) else _VALIDATION,
        "objections": cust.get("objections") or ([_VALIDATION] if cust.get("status") == SECTION_BLOCKED else []),
        "status": cust.get("status"),
        "missing_evidence": cust.get("missing_evidence") or [],
    }

    gtm_channels = []
    for c in _as_list(gtm.get("acquisition_channels")):
        if not isinstance(c, dict):
            continue
        gtm_channels.append(
            {
                "channel": c.get("channel"),
                "difficulty": c.get("difficulty"),
                "expected_cac": c.get("expected_cac"),
                "cac": f"${float(c['expected_cac']):,.0f}" if isinstance(c.get("expected_cac"), (int, float)) else _VALIDATION,
                "conversion_rate": c.get("conversion_rate"),
                "sales_cycle_days": c.get("sales_cycle_days"),
                "roi_score": c.get("roi_score"),
            }
        )

    raw_sizes = _as_dict(market.get("market_sizes"))
    formatted_sizes = {
        k: _metric_from_numeric(raw_sizes.get(k) if isinstance(raw_sizes.get(k), dict) else None)
        for k in ("tam", "sam", "som")
    }

    result: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "topic": identity.get("topic"),
        "industry": identity.get("industry"),
        "geography": identity.get("geography"),
        "report_mode": identity.get("report_mode"),
        "canonical": True,
        "market_truth": {
            "vertical": market.get("vertical"),
            "market_sizes": formatted_sizes,
            "growth": market.get("growth") or _VALIDATION,
            "gaps": market.get("gaps") or ([_VALIDATION] if market.get("status") == SECTION_BLOCKED else []),
            "missing_evidence": market.get("missing_evidence") or [],
            "status": market.get("status"),
        },
        "customer_truth": customer_truth,
        "competitor_truth": competitor_truth,
        "pricing_truth": {
            "bands": price.get("bands") or {},
            "competitor_pricing_table": price.get("competitor_pricing_table") or [],
            "wedge": price.get("wedge") or _VALIDATION,
            "status": price.get("status"),
            "missing_evidence": price.get("missing_evidence") or [],
        },
        "unit_economics": {
            "table": _unit_table_from_numeric(numeric),
            "impossible_economics": numeric.get("impossible_economics") or [],
            "financial_unknowns": numeric.get("financial_unknowns") or [],
            "status": numeric.get("status"),
            "missing_evidence": numeric.get("missing_evidence") or [],
        },
        "go_to_market": {
            "channels": gtm_channels,
            "positioning": gtm.get("positioning") or {},
            "launch_strategy": gtm.get("launch_strategy") or [_VALIDATION],
            "moat": gtm.get("moat") or [_VALIDATION],
            "gtm_engine": gtm,
            "vertical": gtm.get("vertical"),
            "recommended_launch_sequence": gtm.get("recommended_launch_sequence"),
            "first_channel": gtm.get("first_channel"),
            "scale_channel": gtm.get("scale_channel"),
            "channel_economics": gtm.get("channel_economics"),
            "status": gtm.get("status"),
        },
        "execution_plan": _execution_plan_block(canonical),
        "risk_map": risk.get("risk_map") or [],
        "investment_verdict": {
            "verdict": inv.get("customer_decision") or _VALIDATION,
            "source_verdict": inv.get("verdict") or _VALIDATION,
            "investment_score": inv.get("investment_score"),
            "rationale": inv.get("rationale") or [_VALIDATION],
            "risks": inv.get("risks") or [_VALIDATION],
            "audit_score": inv.get("audit_score"),
            "funding_ready": inv.get("funding_ready"),
            "status": inv.get("status"),
        },
        "executive_verdict": _executive_from_investment(inv),
        "report_truth_confidence": {
            "overall": meta.get("confidence", 0),
            "v2_prose_dependency_pct": 0,
            "blocked_sections": meta.get("blocked_sections") or [],
            "missing_evidence": meta.get("missing_evidence") or [],
        },
        "truth_policy": {
            "source": "canonical_compiler",
            "conflict_rule": "single_owner_sections",
            "v2_sections": "appendix_only",
        },
    }
    result["execution_calendar"] = build_execution_calendar(result)
    result["risk_heatmap"] = build_risk_heatmap(result.get("risk_map"))
    return result


def compile_customer_report(canonical: dict[str, Any] | None) -> dict[str, Any]:
    """Research-mode customer report from canonical truth."""
    canonical = canonical if isinstance(canonical, dict) else {}
    mode = str(_as_dict(canonical.get("identity")).get("report_mode") or REPORT_MODE_RESEARCH)
    if mode != REPORT_MODE_RESEARCH:
        mode = REPORT_MODE_RESEARCH
    obj = _compile_v3_base(canonical)
    obj["report_mode"] = REPORT_MODE_RESEARCH
    return filter_v3_report_object(obj, REPORT_MODE_RESEARCH)


def compile_investor_report(canonical: dict[str, Any] | None) -> dict[str, Any]:
    """Investor memo from canonical truth."""
    canonical = canonical if isinstance(canonical, dict) else {}
    obj = _compile_v3_base(canonical)
    obj["report_mode"] = REPORT_MODE_INVESTOR_MEMO
    return filter_v3_report_object(obj, REPORT_MODE_INVESTOR_MEMO)


def compile_execution_report(canonical: dict[str, Any] | None) -> dict[str, Any]:
    """Business builder / execution report from canonical truth."""
    canonical = canonical if isinstance(canonical, dict) else {}
    obj = _compile_v3_base(canonical)
    obj["report_mode"] = REPORT_MODE_BUSINESS_BUILDER
    return filter_v3_report_object(obj, REPORT_MODE_BUSINESS_BUILDER)


def compile_for_mode(canonical: dict[str, Any] | None, mode: str | None = None) -> dict[str, Any]:
    canonical = canonical if isinstance(canonical, dict) else {}
    resolved = mode or _as_dict(canonical.get("identity")).get("report_mode") or REPORT_MODE_RESEARCH
    if resolved == REPORT_MODE_INVESTOR_MEMO:
        return compile_investor_report(canonical)
    if resolved == REPORT_MODE_BUSINESS_BUILDER:
        return compile_execution_report(canonical)
    return compile_customer_report(canonical)
