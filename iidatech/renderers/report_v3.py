"""IIDATECH V3 customer report renderer — decision-first export from full report payload."""
from __future__ import annotations

from typing import Any

from iidatech.renderers.report_v3_enhancements import build_execution_calendar, build_risk_heatmap
from iidatech.renderers.report_v3_truth import (
    TruthContext,
    compute_report_truth_confidence,
    grounding_known,
    metric,
    metric_display,
)
from iidatech.validation.competitor_evidence import (
    DEFAULT_COMPETITOR_EVIDENCE_GAPS,
    competitor_evidence_gap_markdown,
    filter_verified_competitor_matrix,
    filter_verified_pricing_rows,
    is_synthetic_competitor_name,
)
from iidatech.report_modes import (
    MODE_LABELS,
    REPORT_MODE_BUSINESS_BUILDER,
    REPORT_MODE_INVESTOR_MEMO,
    REPORT_MODE_RESEARCH,
    filter_v3_report_object,
    infer_report_mode,
    mode_allows_section,
)

_VALIDATION = "VALIDATION REQUIRED"
_SCHEMA_VERSION = "iidatech_report_v3"

_CUSTOMER_VERDICT = {
    "STRONG_YES": "BUILD",
    "CONDITIONAL_YES": "BUILD WITH CONDITIONS",
    "MAYBE": "BUILD WITH CONDITIONS",
    "NO": "DO NOT BUILD",
    "BUILD": "BUILD",
    "AVOID": "DO NOT BUILD",
}

_RISK_CATEGORIES = ("market", "pricing", "operational", "demand", "financial")


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


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


def _num(v: Any) -> float | None:
    if v in (None, ""):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def _market_size_block(ctx: TruthContext, fin: dict) -> dict[str, Any]:
    structured = ctx.structured
    qmodel = ctx.qmodel
    fin_analysis = _as_dict(structured.get("financial_analysis"))
    blueprint_mo = _as_dict(ctx.blueprint.get("market_opportunity"))
    headline = _as_dict(qmodel.get("headline"))

    def _pick_block(block: dict, *keys: str) -> Any:
        for k in keys:
            if block.get(k) not in (None, "", "WITHHELD"):
                return block.get(k)
        return None

    def _size_metric(key: str, headline_key: str, brain_key: str) -> dict[str, Any]:
        brain_block = _as_dict(fin.get(brain_key))
        struct_block = _as_dict(fin_analysis.get(brain_key))
        candidates = [
            (_pick_block(brain_block, "value", brain_key), "research_intelligence", str(brain_block.get("confidence") or "high"), "validated" if brain_block.get("computed") else "estimated"),
            (_pick_block(struct_block, "value", brain_key), "structured_research_report", "medium", "estimated"),
            (blueprint_mo.get(brain_key), "business_blueprint", "medium", "estimated"),
            (headline.get(headline_key) or headline.get(f"{brain_key}_base"), "quantitative_model", "high" if headline.get(f"{brain_key}_base_fmt") and "WITHHELD" not in str(headline.get(f"{brain_key}_base_fmt")).upper() else "medium", "validated"),
            (qmodel.get(brain_key), "quantitative_model", "medium", "estimated"),
        ]
        m = ctx.resolve(candidates)
        n = _num(m.get("value"))
        if n is not None:
            m = {**m, "display": _fmt_money(n)}
        return m

    tam_m = _size_metric("tam", "tam_base", "tam")
    sam_m = _size_metric("sam", "sam_base", "sam")
    som_m = _size_metric("som", "som_base", "som")
    return {
        "tam": tam_m,
        "sam": sam_m,
        "som": som_m,
        "denominator_notes": metric(
            _pick_block(_as_dict(fin.get("tam")), "denominator", "method") or headline.get("methodology"),
            source="research_intelligence",
            confidence="medium",
            validation_state="estimated" if _pick_block(_as_dict(fin.get("tam")), "denominator") else "validation_required",
        ),
        "invalid_business_model": bool(fin.get("invalid_business_model")),
        "invalid_reasons": fin.get("invalid_business_model_reasons") or [],
    }


def _brain(payload: dict) -> dict:
    ri = payload.get("research_intelligence")
    if isinstance(ri, dict) and ri:
        return ri
    diligence = _as_dict(payload.get("diligence_pack"))
    return _as_dict(diligence.get("research_intelligence"))


def _map_customer_verdict(raw: str) -> str:
    key = str(raw or "MAYBE").upper().replace(" ", "_")
    return _CUSTOMER_VERDICT.get(key, "BUILD WITH CONDITIONS")


def _top_three(items: list[Any], *, field: str | None = None) -> list[str]:
    out: list[str] = []
    for item in items:
        if len(out) >= 3:
            break
        if isinstance(item, str) and item.strip():
            out.append(item.strip()[:240])
        elif isinstance(item, dict):
            val = item.get(field) if field else None
            if val is None:
                val = item.get("reason") or item.get("rationale") or item.get("category")
            if val:
                out.append(str(val).strip()[:240])
    while len(out) < 3:
        out.append(_VALIDATION)
    return out[:3]


def _confidence_0_100(payload: dict, brain: dict, investment: dict, audit: dict) -> int:
    for src in (
        brain.get("confidence_score"),
        _as_dict(investment.get("scorecard")).get("confidence_score"),
        audit.get("confidence_score"),
        payload.get("report_confidence"),
    ):
        n = _num(src)
        if n is not None:
            if n <= 10:
                return int(max(0, min(100, round(n * 10))))
            return int(max(0, min(100, round(n))))
    return 0


def _funding_ready(payload: dict, diligence: dict, audit: dict) -> bool | str:
    for pack in (
        _as_dict(diligence.get("funding_readiness_pack")),
        _as_dict(audit.get("funding_readiness_pack")),
        audit,
    ):
        if "funding_ready" in pack:
            return bool(pack.get("funding_ready"))
    fr = payload.get("funding_ready")
    if fr is not None:
        return bool(fr)
    return _VALIDATION


def _build_executive_verdict(payload: dict, brain: dict, investment: dict, audit: dict) -> dict[str, Any]:
    raw = investment.get("verdict") or investment.get("investment_verdict") or "MAYBE"
    scorecard = _as_dict(investment.get("scorecard"))
    rationale = _as_list(investment.get("rationale"))
    risks = _as_list(investment.get("risks"))
    for_src = rationale or _as_list(brain.get("strategic_recommendations", {}).get("moat_strategy") if isinstance(brain.get("strategic_recommendations"), dict) else [])
    against_src = risks or _as_list(brain.get("risk_flags"))

    return {
        "decision": _map_customer_verdict(str(raw)),
        "source_verdict": str(raw).upper(),
        "confidence_score": _confidence_0_100(payload, brain, investment, audit),
        "attractiveness": _text(scorecard.get("market_attractiveness") or investment.get("investment_score")),
        "risk": _text(scorecard.get("competition_intensity") or (against_src[0] if against_src else None)),
        "funding_ready": _funding_ready(payload, _as_dict(payload.get("diligence_pack")), audit),
        "reasons_for": _top_three(for_src if isinstance(for_src, list) else []),
        "reasons_against": _top_three(against_src if isinstance(against_src, list) else []),
        "investment_score": investment.get("investment_score"),
    }


def _icps(payload: dict, cust: dict, diligence: dict) -> list[dict[str, Any]]:
    profiles: list[dict[str, Any]] = []
    survey = _as_dict(diligence.get("survey_interview_findings"))
    for row in _as_list(survey.get("icp_profiles")) + _as_list(survey.get("buyer_profiles")):
        if isinstance(row, dict):
            profiles.append(row)
    for row in _as_list(cust.get("icp_profiles")) + _as_list(cust.get("buyer_personas")):
        if isinstance(row, dict):
            profiles.append(row)

    segments = _as_list(cust.get("segments"))
    for row in segments:
        if isinstance(row, dict):
            profiles.append(row)
        elif isinstance(row, str) and row.strip():
            profiles.append({"name": row.strip()})

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for p in profiles:
        name = str(p.get("name") or p.get("named_buyer_profile") or p.get("segment") or "").lower()
        if name and name in seen:
            continue
        if name:
            seen.add(name)
        deduped.append(
            {
                "name": _text(p.get("name") or p.get("named_buyer_profile") or p.get("segment")),
                "pain": _text(p.get("pain") or p.get("primary_pain")),
                "trigger": _text(p.get("buyer_trigger") or p.get("trigger")),
                "wtp": _text(p.get("willingness_to_pay") or p.get("wtp")),
                "decision_maker": _text(p.get("decision_maker")),
            }
        )
        if len(deduped) >= 3:
            break
    if not deduped:
        desires = _as_list(cust.get("top_desires"))
        for i, pain in enumerate(_as_list(cust.get("top_pains"))[:3]):
            if not isinstance(pain, dict):
                continue
            desire = desires[i] if i < len(desires) and isinstance(desires[i], dict) else {}
            deduped.append(
                {
                    "name": f"ICP {i + 1}: {str(pain.get('category') or 'segment').title()} buyer",
                    "pain": _text(pain.get("sample") or pain.get("category")),
                    "trigger": _text(desire.get("desired_outcome")),
                    "wtp": _VALIDATION,
                    "decision_maker": _VALIDATION,
                }
            )
    while len(deduped) < 3:
        deduped.append({"name": _VALIDATION, "pain": _VALIDATION, "trigger": _VALIDATION, "wtp": _VALIDATION, "decision_maker": _VALIDATION})
    return deduped[:3]


def _ranked_pains(cust: dict, structured: dict) -> list[dict[str, Any]]:
    cust_analysis = _as_dict(structured.get("customer_analysis"))
    pains = _as_list(cust.get("top_pains")) or _as_list(cust.get("buyer_pain_clusters")) or _as_list(cust_analysis.get("top_pains"))
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
        elif isinstance(p, str):
            ranked.append({"rank": i, "category": _VALIDATION, "evidence": p[:240]})
    return ranked or [{"rank": 1, "category": _VALIDATION, "evidence": _VALIDATION}]


def _build_customer_truth(payload: dict, brain: dict, structured: dict) -> dict[str, Any]:
    cust = _as_dict(brain.get("customer_truth"))
    diligence = _as_dict(payload.get("diligence_pack"))
    cust_analysis = _as_dict(structured.get("customer_analysis"))
    wtp = cust.get("wtp_distribution") or cust_analysis.get("wtp_distribution") or cust.get("willingness_to_pay_signals")
    objections = (
        _as_list(cust.get("dominant_objections"))
        or _as_list(cust_analysis.get("dominant_objections"))
        or _as_list(cust.get("objections"))
    )
    return {
        "icps": _icps(payload, cust, diligence),
        "ranked_pains": _ranked_pains(cust, structured),
        "wtp": wtp if wtp not in (None, "", {}) else _VALIDATION,
        "objections": objections[:8] or [_VALIDATION],
    }


def _competitor_matrix(comp: dict, structured: dict) -> list[dict[str, Any]]:
    comp_analysis = _as_dict(structured.get("competitor_analysis"))
    raw = _as_list(comp.get("competitor_matrix")) or _as_list(comp_analysis.get("matrix"))
    matrix = filter_verified_competitor_matrix(raw)
    rows: list[dict[str, Any]] = []
    for row in matrix[:12]:
        price_raw = row.get("pricing") or row.get("price_band") or row.get("price")
        price_disp = _fmt_money(price_raw) if _num(price_raw) is not None else _text(price_raw)
        trust = _num(row.get("trust_score"))
        strength = _text(row.get("strength") or row.get("strengths"))
        weakness = _text(row.get("weakness") or row.get("gaps"))
        if strength == _VALIDATION and trust is not None:
            strength = "Strong evidence anchor" if trust >= 0.85 else "Credible competitor" if trust >= 0.7 else _VALIDATION
        if weakness == _VALIDATION and trust is not None and trust < 0.7:
            weakness = "Low trust tier / weak differentiation proof"
        name = _text(row.get("name") or row.get("competitor"))
        if is_synthetic_competitor_name(name):
            continue
        rows.append(
            {
                "name": name,
                "positioning": _text(row.get("positioning") or row.get("segment") or row.get("plan")),
                "pricing": price_disp,
                "strength": strength,
                "weakness": weakness,
                "gap": _text((comp.get("feature_gap") or [""])[0] if isinstance(comp.get("feature_gap"), list) else comp.get("feature_gap")),
            }
        )
    return rows


def _pricing_table(comp: dict, diligence: dict) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    raw_rows: list[dict[str, Any]] = []
    for row in _as_list(comp.get("validated_pricing")) + _as_list(comp.get("pricing_rows")) + _as_list(comp.get("competitor_matrix")):
        if isinstance(row, dict):
            raw_rows.append(row)
    pack = _as_dict(diligence.get("pricing_intelligence_pack"))
    for row in _as_list(pack.get("rows")) + _as_list(pack.get("sourced_pricing_records")):
        if isinstance(row, dict):
            raw_rows.append(row)
    for row in filter_verified_pricing_rows(raw_rows):
        rows.append(
            {
                "competitor": _text(row.get("name") or row.get("competitor") or row.get("competitor_archetypes")),
                "package": _text(row.get("package") or row.get("plan") or row.get("tier")),
                "price": _fmt_money(row.get("price") or row.get("price_band")) if _num(row.get("price") or row.get("price_band")) is not None else _text(row.get("estimated_price_band") or row.get("price") or row.get("price_band")),
                "source": _text(row.get("source") or row.get("url") or row.get("source_url")),
            }
        )
    return rows[:15]


def _unit_economics_table(ctx: TruthContext, fin: dict) -> list[dict[str, Any]]:
    fin_analysis = _as_dict(ctx.structured.get("financial_analysis"))
    ue_fin = _as_dict(fin.get("unit_economics"))
    ue_struct = _as_dict(fin_analysis.get("unit_economics"))
    ue_bp = _as_dict(ctx.blueprint.get("unit_economics"))

    def row(label: str, key: str, *, bp_key: str | None = None, money: bool = False) -> dict[str, Any]:
        gkey = bp_key or key
        candidates = [
            (ue_fin.get(key), "research_intelligence", str(_as_dict(fin).get("confidence") or "high"), "estimated"),
            (ue_struct.get(key), "structured_research_report", "medium", "estimated"),
            (ue_bp.get(gkey), "business_blueprint", str(ue_bp.get("assumption_level") or "medium"), "estimated"),
            (grounding_known(ctx, key), "unit_economics_grounding", "benchmark-derived", "estimated"),
        ]
        m = ctx.resolve(candidates)
        n = _num(m.get("value"))
        if money and n is not None:
            m = {**m, "display": _fmt_money(n)}
        elif n is not None:
            m = {**m, "display": str(n)}
        return {"metric": label, **m}

    return [
        row("CAC", "cac", money=True),
        row("LTV", "ltv", money=True),
        row("ARPU / monthly", "arpu", bp_key="arpu", money=True),
        row("Gross margin %", "margin", bp_key="gross_margin_pct"),
        row("Payback (months)", "payback_months"),
        row("LTV:CAC", "ltv_cac_ratio"),
    ]


def _gtm_channels(strat: dict, diligence: dict, payload: dict) -> list[dict[str, Any]]:
    channels: list[dict[str, Any]] = []
    for row in _as_list(strat.get("gtm_channels")) + _as_list(strat.get("channels")):
        if isinstance(row, dict):
            channels.append(
                {
                    "channel": _text(row.get("channel") or row.get("name")),
                    "difficulty": _text(row.get("difficulty")),
                    "cac": _text(row.get("cac")),
                    "speed": _text(row.get("speed") or row.get("time_to_results")),
                    "roi": _text(row.get("roi") or row.get("expected_roi")),
                }
            )
    gtm_pack = _as_dict(diligence.get("go_to_market_pack"))
    for row in _as_list(gtm_pack.get("channels")):
        if isinstance(row, dict):
            channels.append(
                {
                    "channel": _text(row.get("channel") or row.get("name")),
                    "difficulty": _text(row.get("difficulty")),
                    "cac": _text(row.get("cac")),
                    "speed": _text(row.get("speed")),
                    "roi": _text(row.get("roi")),
                }
            )
    if not channels:
        for name in _as_list(strat.get("launch_strategy")) + _as_list(strat.get("gtm")):
            if isinstance(name, str) and name.strip():
                channels.append(
                    {
                        "channel": name.strip()[:160],
                        "difficulty": _VALIDATION,
                        "cac": _VALIDATION,
                        "speed": _VALIDATION,
                        "roi": _VALIDATION,
                    }
                )
    blueprint = payload.get("business_blueprint") or payload.get("execution_blueprint")
    if not channels and isinstance(blueprint, dict):
        gtm = _as_dict(blueprint.get("go_to_market"))
        for name in _as_list(gtm.get("acquisition_channels")):
            channels.append({"channel": _text(name), "difficulty": _VALIDATION, "cac": _VALIDATION, "speed": _VALIDATION, "roi": _VALIDATION})
    return channels[:10] or [
        {"channel": _VALIDATION, "difficulty": _VALIDATION, "cac": _VALIDATION, "speed": _VALIDATION, "roi": _VALIDATION}
    ]


def _phase_block(source: dict | list | None, *, default_actions: list[str]) -> dict[str, Any]:
    if isinstance(source, dict):
        return {
            "actions": _as_list(source.get("actions")) or _as_list(source.get("tasks")) or default_actions,
            "milestones": _as_list(source.get("milestones")) or _as_list(source.get("deliverables")) or [_VALIDATION],
            "kpi": _text(source.get("kpi") or (source.get("kpis") or [_VALIDATION])[0] if isinstance(source.get("kpis"), list) and source.get("kpis") else None),
            "budget": _text(source.get("budget") or source.get("budget_estimate")),
        }
    if isinstance(source, list):
        actions = [str(x.get("task") or x)[:200] for x in source if isinstance(x, (dict, str))][:8]
        return {
            "actions": actions or default_actions,
            "milestones": [_VALIDATION],
            "kpi": _VALIDATION,
            "budget": _VALIDATION,
        }
    return {"actions": default_actions, "milestones": [_VALIDATION], "kpi": _VALIDATION, "budget": _VALIDATION}


def _build_execution_plan(ctx: TruthContext, strat: dict) -> dict[str, Any]:
    payload = ctx.payload
    diligence = ctx.diligence
    blueprint = ctx.blueprint if ctx.blueprint else {}
    if not blueprint:
        blueprint = payload.get("execution_blueprint") if isinstance(payload.get("execution_blueprint"), dict) else {}
    if not blueprint:
        blueprint = _as_dict(diligence.get("execution_blueprint"))
    plan = _as_dict(payload.get("execution_plan")) or _as_dict(strat.get("execution_plan"))
    ctx.provenance.record("business_blueprint" if ctx.blueprint else "research_intelligence")

    p0 = _as_dict(blueprint.get("phase_0_validation"))
    p1 = _as_dict(blueprint.get("phase_1_mvp"))
    p2 = _as_dict(blueprint.get("phase_2_pilot_revenue"))
    p3 = _as_dict(blueprint.get("phase_3_growth"))

    day_tasks = _as_list(p0.get("daily_tasks"))
    day_actions = [str(t.get("task") or t)[:200] for t in day_tasks if isinstance(t, dict)]

    return {
        "day_1_7": _phase_block(plan.get("day_1_7") or {"actions": day_actions, "milestones": ["validation gate"], "kpi": "ICP + pilot metric confirmed", "budget": _VALIDATION}, default_actions=day_actions or [_VALIDATION]),
        "week_2_4": _phase_block(plan.get("week_2_4") or p1, default_actions=[_VALIDATION]),
        "month_2_3": _phase_block(plan.get("month_2_3") or p2, default_actions=[_VALIDATION]),
        "month_3_6": _phase_block(plan.get("month_3_6") or p3, default_actions=[_VALIDATION]),
        "first_revenue_path": _as_list(strat.get("first_revenue_path")) or _as_list(strat.get("fast_revenue_path")) or [_VALIDATION],
    }


def _risk_row(category: str, probability: Any, impact: Any, mitigation: Any) -> dict[str, str]:
    return {
        "category": category,
        "probability": _text(probability) if probability not in (None, "") else _VALIDATION,
        "impact": _text(impact) if impact not in (None, "") else _VALIDATION,
        "mitigation": _text(mitigation) if mitigation not in (None, "") else _VALIDATION,
    }


def _build_risk_map(brain: dict, investment: dict, audit: dict) -> list[dict[str, str]]:
    structured: list[dict[str, str]] = []
    flags = _as_list(brain.get("risk_flags"))
    inv_risks = _as_list(investment.get("risks"))
    audit_risks = _as_list(audit.get("risks")) + _as_list(audit.get("risk_items"))

    by_cat: dict[str, dict[str, Any]] = {}
    for item in flags + inv_risks + audit_risks:
        if isinstance(item, dict):
            cat = str(item.get("category") or item.get("type") or "market").lower()
            if cat not in _RISK_CATEGORIES:
                cat = "market"
            by_cat.setdefault(cat, item)
        elif isinstance(item, str) and item.strip():
            by_cat.setdefault("market", {"probability": _VALIDATION, "impact": item.strip()[:200], "mitigation": _VALIDATION})

    fin = _as_dict(brain.get("financial_truth"))
    comp = _as_dict(brain.get("competitor_map"))
    if fin.get("invalid_business_model"):
        by_cat.setdefault("financial", {"probability": "high", "impact": "; ".join(_as_list(fin.get("invalid_business_model_reasons"))), "mitigation": "Re-model COGS vs price"})
    if int(comp.get("competitor_count") or 0) >= 8:
        by_cat.setdefault("market", {"probability": "medium", "impact": "crowded competitor set", "mitigation": "narrow wedge and ICP"})

    for cat in _RISK_CATEGORIES:
        row = by_cat.get(cat, {})
        structured.append(
            _risk_row(
                cat,
                row.get("probability") if isinstance(row, dict) else None,
                row.get("impact") if isinstance(row, dict) else (row if isinstance(row, str) else None),
                row.get("mitigation") if isinstance(row, dict) else None,
            )
        )
    return structured


def build_v3_report_object(full_report_payload: dict[str, Any] | None) -> dict[str, Any]:
    """Build V3 presentation object via canonical compiler (single source of truth)."""
    from iidatech.core.report_compiler import build_canonical_report, compile_for_mode, validate_canonical_report

    payload = full_report_payload if isinstance(full_report_payload, dict) else {}
    canonical = build_canonical_report(payload)
    validate_canonical_report(canonical)
    mode = infer_report_mode(
        str(payload.get("topic") or ""),
        payload.get("report_mode"),
        workflow_choice=str(payload.get("workflow_choice") or ""),
    )
    return compile_for_mode(canonical, mode)


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return ""
    line = "| " + " | ".join(headers) + " |"
    sep = "| " + " | ".join("---" for _ in headers) + " |"
    body = "\n".join("| " + " | ".join(str(c).replace("|", "/") for c in row) + " |" for row in rows)
    return "\n".join([line, sep, body])


def render_v3_report_markdown(report_object: dict[str, Any] | None) -> str:
    """Render V3 report object as decision-first markdown (mode-gated sections only)."""
    obj = report_object if isinstance(report_object, dict) else {}
    mode = str(obj.get("report_mode") or REPORT_MODE_RESEARCH)
    mode_label = MODE_LABELS.get(mode, mode)
    ev = _as_dict(obj.get("executive_verdict"))
    mt = _as_dict(obj.get("market_truth"))
    sizes = _as_dict(mt.get("market_sizes"))
    cust = _as_dict(obj.get("customer_truth"))
    comp = _as_dict(obj.get("competitor_truth"))
    price = _as_dict(obj.get("pricing_truth"))
    ue = _as_dict(obj.get("unit_economics"))
    gtm = _as_dict(obj.get("go_to_market"))
    plan = _as_dict(obj.get("execution_plan"))
    inv = _as_dict(obj.get("investment_verdict"))

    topic = _text(obj.get("topic"))
    industry = _text(obj.get("industry"))
    geography = _text(obj.get("geography"))

    rtc = _as_dict(obj.get("report_truth_confidence"))
    lines: list[str] = [
        f"# IIDATECH V3 Report: {topic}",
        "",
        f"**Report mode:** {mode_label}",
        f"**Geography:** {geography} | **Industry:** {industry} | **Schema:** {obj.get('schema_version', _SCHEMA_VERSION)}",
        f"**Truth confidence:** {rtc.get('score', _VALIDATION)}/100 ({rtc.get('grade', _VALIDATION)}) | **Structured sources:** {rtc.get('structured_source_pct', _VALIDATION)}% | **V2 prose dependency:** {rtc.get('v2_prose_dependency_pct', 0)}%",
        "",
    ]

    if mode_allows_section(mode, "executive_verdict") and mode == REPORT_MODE_INVESTOR_MEMO:
        lines.extend(
            [
                "## Executive decision",
                "",
                f"**Verdict:** {ev.get('decision', _VALIDATION)}",
                f"**Confidence:** {ev.get('confidence_score', 0)}/100 | **Funding ready:** {ev.get('funding_ready', _VALIDATION)}",
                f"**Attractiveness:** {ev.get('attractiveness', _VALIDATION)} | **Risk signal:** {ev.get('risk', _VALIDATION)}",
                "",
                "**Top reasons to build**",
            ]
        )
        for r in _as_list(ev.get("reasons_for")):
            lines.append(f"- {r}")
        lines.append("")
        lines.append("**Top reasons to pause**")
        for r in _as_list(ev.get("reasons_against")):
            lines.append(f"- {r}")
        lines.append("")

    if mode_allows_section(mode, "market_truth"):
        lines.extend(
            [
                "## Market truth",
                "",
                _md_table(
                    ["Measure", "Value"],
                    [["TAM", sizes.get("tam", _VALIDATION)], ["SAM", sizes.get("sam", _VALIDATION)], ["SOM", sizes.get("som", _VALIDATION)]],
                ),
                "",
                f"Growth / CAGR: {mt.get('growth', _VALIDATION)}",
                "",
            ]
        )
        missing = _as_list(mt.get("missing_evidence"))
        if missing:
            lines.append("**Missing evidence:**")
            for item in missing:
                lines.append(f"- {item}")
            lines.append("")

    if mode_allows_section(mode, "unit_economics"):
        ue_rows = [[r.get("metric", ""), metric_display(r), r.get("source", ""), r.get("validation_state", "")] for r in _as_list(ue.get("table")) if isinstance(r, dict)]
        lines.extend(["## Unit economics", "", _md_table(["Metric", "Value", "Source", "State"], ue_rows), ""])

    if mode_allows_section(mode, "pricing_truth"):
        price_rows = [
            [r.get("competitor", ""), r.get("package", ""), r.get("price", ""), r.get("source", "")]
            for r in _as_list(price.get("competitor_pricing_table"))
            if isinstance(r, dict)
        ]
        lines.extend(["## Pricing truth", ""])
        if price_rows:
            lines.append(_md_table(["Competitor", "Package", "Price", "Source"], price_rows))
        else:
            lines.append(competitor_evidence_gap_markdown(_as_list(comp.get("missing_evidence")) or list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)))
        lines.append("")

    if mode_allows_section(mode, "customer_truth"):
        icp_rows = [
            [i.get("name", ""), i.get("pain", ""), i.get("trigger", ""), i.get("wtp", "")]
            for i in _as_list(cust.get("icps"))
            if isinstance(i, dict)
        ]
        lines.extend(["## Customer truth", "", "### ICPs (top 3)", "", _md_table(["ICP", "Pain", "Trigger", "WTP"], icp_rows), ""])
        pain_rows = [[str(p.get("rank", "")), p.get("category", ""), p.get("evidence", "")] for p in _as_list(cust.get("ranked_pains")) if isinstance(p, dict)]
        lines.extend(["### Ranked pains", "", _md_table(["Rank", "Category", "Evidence"], pain_rows), ""])
        lines.append(f"**WTP summary:** {cust.get('wtp', _VALIDATION)}")
        lines.append("")
        lines.append("**Objections**")
        for o in _as_list(cust.get("objections")):
            lines.append(f"- {o}")
        lines.append("")

    if mode_allows_section(mode, "competitor_truth"):
        matrix_rows = [
            [r.get("name", ""), r.get("positioning", ""), r.get("pricing", ""), r.get("strength", ""), r.get("weakness", "")]
            for r in _as_list(comp.get("matrix"))
            if isinstance(r, dict)
        ]
        lines.extend(["## Competitor truth", ""])
        if matrix_rows:
            lines.append(_md_table(["Name", "Positioning", "Pricing", "Strength", "Weakness"], matrix_rows))
        else:
            gaps = _as_list(comp.get("missing_evidence")) or list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
            lines.append(competitor_evidence_gap_markdown(gaps))
        lines.append("")

    if mode == REPORT_MODE_INVESTOR_MEMO and mode_allows_section(mode, "go_to_market"):
        moat = _as_list(gtm.get("moat"))
        if moat:
            lines.extend(["## Moat", ""])
            for m in moat:
                lines.append(f"- {m}")
            lines.append("")

    if mode == REPORT_MODE_BUSINESS_BUILDER and mode_allows_section(mode, "go_to_market"):
        ch_rows = []
        for c in _as_list(gtm.get("channels")):
            if not isinstance(c, dict):
                continue
            conv = c.get("conversion_rate")
            conv_disp = f"{float(conv) * 100:.1f}%" if isinstance(conv, (int, float)) else str(conv or "")
            cac_disp = c.get("cac")
            if c.get("expected_cac") is not None and cac_disp in (None, "", _VALIDATION):
                cac_disp = f"${float(c['expected_cac']):,.0f}"
            ch_rows.append([
                c.get("channel", ""),
                c.get("difficulty", ""),
                str(cac_disp or ""),
                conv_disp,
                str(c.get("sales_cycle_days", c.get("speed", ""))),
                str(c.get("roi_score", c.get("roi", ""))),
            ])
        launch_seq = ", ".join(str(x) for x in _as_list(gtm.get("recommended_launch_sequence"))[:4]) or _VALIDATION
        econ_rows = []
        for c in _as_list(gtm.get("channel_economics")):
            if not isinstance(c, dict):
                continue
            conv = c.get("conversion_rate")
            conv_disp = f"{float(conv)*100:.1f}%" if isinstance(conv, (int, float)) else str(conv or _VALIDATION)
            econ_rows.append([str(c.get("channel", _VALIDATION)), str(c.get("expected_cac", _VALIDATION)), str(c.get("expected_leads_per_month", _VALIDATION)), conv_disp, str(c.get("sales_cycle_days", _VALIDATION)), str(c.get("roi_score", _VALIDATION))])
        lines.extend([
            "## Go-to-market",
            f"**Vertical:** {gtm.get('vertical', _VALIDATION)} | **First:** {gtm.get('first_channel', _VALIDATION)} | **Scale:** {gtm.get('scale_channel', _VALIDATION)}",
            f"**Launch sequence:** {launch_seq}",
            "",
            _md_table(["Channel", "Difficulty", "CAC", "Conv %", "Cycle", "ROI"], ch_rows),
            "",
            "### Channel economics",
            _md_table(["Channel", "Exp. CAC", "Leads/mo", "Conv %", "Cycle (d)", "ROI"], econ_rows) if econ_rows else "",
            "",
        ])

    if mode == REPORT_MODE_BUSINESS_BUILDER and mode_allows_section(mode, "execution_plan"):
        for phase_key, title in (
            ("day_1_7", "Days 1–7"),
            ("week_2_4", "Weeks 2–4"),
            ("month_2_3", "Months 2–3"),
            ("month_3_6", "Months 3–6"),
        ):
            block = _as_dict(plan.get(phase_key))
            lines.append(f"### Execution — {title}")
            lines.append(f"- KPI: {block.get('kpi', _VALIDATION)} | Budget: {block.get('budget', _VALIDATION)}")
            lines.append("- Actions:")
            for a in _as_list(block.get("actions")):
                lines.append(f"  - {a}")
            lines.append("")

    if mode == REPORT_MODE_BUSINESS_BUILDER and mode_allows_section(mode, "execution_calendar"):
        cal = _as_dict(obj.get("execution_calendar"))
        cal_order = [("week_1", "Week 1"), ("week_2", "Week 2"), ("week_3", "Week 3"), ("month_2", "Month 2"), ("month_3", "Month 3"), ("month_6", "Month 6")]
        for key, title in cal_order:
            block = _as_dict(cal.get(key))
            if not block:
                continue
            lines.extend([f"### Execution calendar — {title}", ""])
            lines.append(f"**Focus:** {_text(block.get('focus'))}")
            lines.append(f"**KPI:** {_text(block.get('kpi'))}")
            if block.get("budget") and block.get("budget") != _VALIDATION:
                lines.append(f"**Budget:** {block.get('budget')}")
            lines.append("")
            lines.append("**Actions:**")
            for a in _as_list(block.get("actions")):
                lines.append(f"- {a}")
            lines.append("")
            lines.append("**Milestones:**")
            for m in _as_list(block.get("milestones")):
                lines.append(f"- {m}")
            lines.append("")
        y1 = _as_list(cal.get("year_1_milestones"))
        if y1:
            lines.extend(["### Year 1 milestones", ""])
            for m in y1:
                lines.append(f"- {m}")
            lines.append("")

    if mode_allows_section(mode, "risk_heatmap") and mode == REPORT_MODE_INVESTOR_MEMO:
        heat_rows = [[str(r.get("risk", _VALIDATION)), str(r.get("severity", _VALIDATION)), f"{float(r.get('probability', 0)):.0%}" if r.get("probability") is not None else _VALIDATION, str(r.get("mitigation", _VALIDATION))] for r in _as_list(obj.get("risk_heatmap")) if isinstance(r, dict)]
        lines.extend(["### Risk heatmap", "", _md_table(["Risk", "Severity", "Probability", "Mitigation"], heat_rows), ""])

    if mode_allows_section(mode, "risk_map"):
        risk_rows = [[r.get("category", ""), r.get("probability", ""), r.get("impact", ""), r.get("mitigation", "")] for r in _as_list(obj.get("risk_map")) if isinstance(r, dict)]
        lines.extend(["## Risk map", "", _md_table(["Category", "Probability", "Impact", "Mitigation"], risk_rows), ""])

    if mode_allows_section(mode, "investment_verdict"):
        lines.extend(
            [
                "## Investment verdict",
                "",
                f"**Decision:** {inv.get('verdict', _VALIDATION)} (source: {inv.get('source_verdict', _VALIDATION)})",
                f"**Investment score:** {inv.get('investment_score', _VALIDATION)}/10 | **Audit score:** {inv.get('audit_score', _VALIDATION)}",
                "",
            ]
        )
        lines.append("**Rationale**")
        for r in _as_list(inv.get("rationale")):
            lines.append(f"- {r}")
        lines.append("")
        lines.append("**Residual risks**")
        for r in _as_list(inv.get("risks")):
            lines.append(f"- {r}")
        lines.append("")

    if mode_allows_section(mode, "report_truth_confidence"):
        prov = _as_dict(obj.get("data_provenance"))
        lines.extend(["## Source quality", ""])
        lines.append(f"- Truth confidence grade: {rtc.get('grade', _VALIDATION)}")
        lines.append(f"- Structured source coverage: {rtc.get('structured_source_pct', _VALIDATION)}%")
        if prov:
            lines.append(f"- Provenance records: {prov.get('record_count', _VALIDATION)}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"
