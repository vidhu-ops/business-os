"""Pre-section synthesis intelligence assembly.



Extracted from app.run_report_generation so headless workers, API routes,

and Streamlit share one orchestration path for diligence + research brain wiring.

"""

from __future__ import annotations



import os

from typing import Any





def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}





def stamp_diligence_run_metadata(
    diligence_pack: dict[str, Any],
    *,
    source_readiness: dict[str, Any] | None = None,
    application_pack: dict[str, Any] | None = None,
    claude_full_report_rescue: bool = False,
    funding_ready_report_mode: bool = False,
    enable_claude_section_audit: bool = False,
    enable_final_audit: bool = False,
    cloud_llm_configured: bool = False,

) -> dict[str, Any]:
    pack = dict(diligence_pack or {})
    readiness = _as_dict(source_readiness)
    pack["source_readiness_preflight"] = readiness
    pack["markets_report_gate"] = readiness.get("markets_report_gate", {})
    pack["competitor_intelligence_gate"] = readiness.get("competitor_intelligence_gate", {})
    pack["application_readiness_pack"] = _as_dict(application_pack)
    pack["claude_full_report_rescue"] = bool(claude_full_report_rescue)
    existing_fr = _as_dict(pack.get("funding_ready_report_mode"))
    funding_requested = bool(
        funding_ready_report_mode
        or existing_fr.get("requested")
        or existing_fr.get("enabled")
    )
    pack["funding_ready_report_mode"] = {
        "requested": funding_requested,
        "enabled": funding_requested,
        "rule": (
            "Every generated report is audited for funding readiness. If the evidence does not support "
            "funding-ready use, the report must present a repair-ready funding diligence view with visible "
            "evidence gaps, formulas, and blocked claims instead of claiming investment-grade status."
        ),
        "claude_section_audit": bool(enable_claude_section_audit and cloud_llm_configured),
        "claude_final_audit": bool(enable_final_audit and cloud_llm_configured),
    }
    return pack







def apply_funding_ready_confidence_gate(
    pack: dict[str, Any],
    research_intelligence: dict[str, Any],
) -> dict[str, Any]:
    """Gate funding-ready mode on evidence-grounded real_confidence > 7.0."""
    pack = dict(pack or {})
    fr = dict(pack.get("funding_ready_report_mode") or {})
    requested = bool(fr.get("requested", fr.get("enabled", False)))
    fr["requested"] = requested

    rc = _as_dict(research_intelligence.get("real_confidence"))
    score = float(rc.get("score") or 0.0)
    threshold = float(rc.get("funding_ready_threshold") or 7.0)
    fr["real_confidence_score"] = score
    fr["real_confidence_components"] = rc.get("components") or {}

    if requested:
        fr["enabled"] = score > threshold
        if not fr["enabled"]:
            fr["blocked_reason"] = (
                "funding-ready mode requires real_confidence > "
                + str(threshold)
                + "; got "
                + format(score, ".1f")
            )
    else:
        fr["enabled"] = False

    pack["funding_ready_report_mode"] = fr
    return pack


def run_research_brain_layer(
    *,
    topic: str,
    industry: str,
    geography: str,
    horizon: str,
    topic_brief: dict[str, Any],
    diligence_pack: dict[str, Any],
    strict_market_model: dict[str, Any],
    completeness: dict[str, Any],

) -> dict[str, Any]:
    pack = dict(diligence_pack or {})
    brief = dict(topic_brief or {})
    structured_research_report: dict[str, Any] = {}
    research_intelligence: dict[str, Any] = {}
    try:
        from iidatech.agents.research_brain import (
            apply_research_brain_to_report,
            attach_real_confidence,
            polish_research_brain_cheap,
            run_research_brain,
        )
        brain_ctx = {
            "topic": topic,
            "industry": industry,
            "geography": geography,
            "horizon": horizon,
            "quantitative_model": strict_market_model,
            "topic_intelligence_brief": brief,
            "diligence_pack": pack,
            "evidence_completeness": completeness,
            "serp_intelligence": pack.get("serp_intelligence") if isinstance(pack.get("serp_intelligence"), dict) else {},
        }
        research_intelligence = run_research_brain(
            topic,
            industry,
            geography,
            brain_ctx,
            evidence_records=pack.get("citation_ledger") if isinstance(pack.get("citation_ledger"), list) else None,
        )
        if not research_intelligence.get("polish_attempted"):
            polish_enabled = bool(str(os.getenv("OPENAI_API_KEY") or "").strip())
            research_intelligence = polish_research_brain_cheap(research_intelligence, enabled=polish_enabled)
        attach_real_confidence(
            research_intelligence,
            research_intelligence.get("_evidence_rows"),
        )
        merged = apply_research_brain_to_report(brain_ctx, research_intelligence)
        brief = merged.get("topic_intelligence_brief", brief)
        pack = merged.get("diligence_pack", pack)
        pack["research_intelligence"] = research_intelligence
        structured_research_report = merged.get("structured_research_report") or (
            (research_intelligence.get("structured_report") or {}).get("payload")
        )
        if structured_research_report:
            pack["structured_research_report"] = structured_research_report
        pack = apply_funding_ready_confidence_gate(pack, research_intelligence)
    except Exception as exc:
        pack["research_intelligence"] = {"error": str(exc)[:240], "engine": "research_brain_primary"}
        pack["report_degraded"] = True
        pack["degradation_reason"] = str(exc)[:240]
        pack["report_degrade_reason"] = pack["degradation_reason"]
        research_intelligence = pack["research_intelligence"]
    return {
        "topic_brief": brief,
        "diligence_pack": pack,
        "research_intelligence": research_intelligence,
        "structured_research_report": structured_research_report,
        "report_degraded": bool(pack.get("report_degraded")),
        "degradation_reason": pack.get("degradation_reason") or pack.get("report_degrade_reason"),
        "report_degrade_reason": pack.get("report_degrade_reason") or pack.get("degradation_reason"),
    }





def assemble_intelligence_context(
    *,
    topic: str,
    industry: str,
    geography: str,
    horizon: str,
    topic_brief: dict[str, Any],
    diligence_pack: dict[str, Any],
    strict_market_model: dict[str, Any],
    completeness: dict[str, Any],
    source_readiness: dict[str, Any] | None = None,
    application_pack: dict[str, Any] | None = None,
    claude_full_report_rescue: bool = False,
    funding_ready_report_mode: bool = False,
    enable_claude_section_audit: bool = False,
    enable_final_audit: bool = False,
    cloud_llm_configured: bool = False,

) -> dict[str, Any]:
    pack = stamp_diligence_run_metadata(
        diligence_pack,
        source_readiness=source_readiness,
        application_pack=application_pack,
        claude_full_report_rescue=claude_full_report_rescue,
        funding_ready_report_mode=funding_ready_report_mode,
        enable_claude_section_audit=enable_claude_section_audit,
        enable_final_audit=enable_final_audit,
        cloud_llm_configured=cloud_llm_configured,
    )
    brain = run_research_brain_layer(
        topic=topic,
        industry=industry,
        geography=geography,
        horizon=horizon,
        topic_brief=topic_brief,
        diligence_pack=pack,
        strict_market_model=strict_market_model,
        completeness=completeness,
    )
    pack = apply_funding_ready_confidence_gate(
        brain["diligence_pack"],
        brain.get("research_intelligence") or {},
    )
    brain["diligence_pack"] = pack
    return {
        "topic_brief": brain["topic_brief"],
        "diligence_pack": brain["diligence_pack"],
        "strict_market_model": strict_market_model,
        "research_intelligence": brain["research_intelligence"],
        "structured_research_report": brain["structured_research_report"],
        "report_degraded": bool(brain.get("report_degraded") or brain["diligence_pack"].get("report_degraded")),
        "degradation_reason": (
            brain.get("degradation_reason")
            or brain["diligence_pack"].get("degradation_reason")
            or brain.get("report_degrade_reason")
            or brain["diligence_pack"].get("report_degrade_reason")
        ),
        "report_degrade_reason": brain.get("report_degrade_reason") or brain["diligence_pack"].get("report_degrade_reason"),
    }


