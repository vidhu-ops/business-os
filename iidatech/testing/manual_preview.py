"""Manual preview mode — near-zero LLM cost product simulation without synthetic competitors."""
from __future__ import annotations

import hashlib
import json
import os
from typing import Any, Callable

from iidatech.validation.competitor_evidence import DEFAULT_COMPETITOR_EVIDENCE_GAPS

_PREVIEW_ENV = "IIDATECH_MANUAL_PREVIEW"
_PATCHED = False
_VALIDATION = "VALIDATION REQUIRED"


def is_manual_preview() -> bool:
    return os.getenv(_PREVIEW_ENV, "0").strip().lower() in {"1", "true", "yes", "on"}


def enable_manual_preview() -> None:
    os.environ[_PREVIEW_ENV] = "1"


def disable_manual_preview() -> None:
    os.environ.pop(_PREVIEW_ENV, None)


def _seed(case_id: str) -> int:
    return int(hashlib.md5(case_id.encode("utf-8")).hexdigest()[:8], 16)


def _topic_hash(topic: str) -> int:
    return int(hashlib.md5(topic.encode("utf-8")).hexdigest()[:8], 16)


def build_preview_research_brain(case: dict[str, Any], *, domain: str = "") -> dict[str, Any]:
    """Deterministic research_intelligence block for preview runs — no invented competitors or pricing."""
    sid = case.get("case_id") or case.get("topic", "case")
    h = _seed(str(sid))
    topic = str(case.get("topic") or "Market opportunity")
    industry = str(case.get("industry") or "General")
    score = 5.5 + (h % 30) / 10.0
    gaps = list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
    return {
        "confidence_score": round(score * 10),
        "competitor_map": {
            "competitor_count": 0,
            "market_leaders": [],
            "competitor_matrix": [],
            "validated_pricing": [],
            "pricing_rows": [],
            "pricing_bands": {},
            "market_gaps": gaps,
            "evidence_gap": True,
        },
        "customer_truth": {
            "top_pains": [{"category": "workflow", "frequency": 0, "sample": _VALIDATION}],
            "top_desires": [],
            "wtp_distribution": {},
        },
        "financial_truth": {
            "tam": {"status": _VALIDATION, "withheld_reason": "preview — no verified market denominator"},
            "sam": {"status": _VALIDATION, "withheld_reason": "preview — no verified market denominator"},
            "som": {"status": _VALIDATION, "withheld_reason": "preview — no verified market denominator"},
            "unit_economics": {"status": _VALIDATION, "withheld_reason": "preview — no cited unit economics"},
        },
        "strategic_recommendations": {
            "best_wedge": _VALIDATION,
            "launch_strategy": [_VALIDATION],
            "first_revenue_path": [_VALIDATION],
            "positioning": {"statement": _VALIDATION},
        },
        "risk_flags": ["Insufficient verified competitor evidence for preview"],
        "evidence_count": 0,
        "missing_evidence": gaps,
        "domain": domain,
        "preview_mode": "evidence_gap_only",
    }


def build_preview_report_payload(case: dict[str, Any], *, domain: str = "", routed_confidence: float = 0.0) -> dict[str, Any]:
    """Full report payload for preview harness without premium LLM calls or synthetic competitors."""
    from iidatech.validation.payload_guard import stamp_payload_identity

    brain = build_preview_research_brain(case, domain=domain)
    h = _seed(str(case.get("case_id", case.get("topic", ""))))
    score = 5.0 + (h % 25) / 10.0
    topic = str(case.get("topic") or "")
    geography = str(case.get("geography") or "Global")
    industry = str(case.get("industry") or "General")
    boardroom = mock_boardroom_verdict({"topic": topic, "research_intelligence": brain}, None)
    audit = mock_claude_audit({"topic": topic, "research_intelligence": brain}, None)
    payload = {
        "topic": topic,
        "industry": industry,
        "target": geography,
        "geography": geography,
        "routed_domain": domain,
        "routing_confidence": routed_confidence,
        "research_intelligence": brain,
        "structured_research_report": {"market_truth": {"topic": topic, "industry": industry}},
        "investment_decision": {
            "verdict": boardroom.get("investment_verdict", "CONDITIONAL_YES"),
            "investment_score": score,
            "scorecard": {"market_attractiveness": score, "competition_intensity": 6.0, "confidence_score": score},
            "rationale": boardroom.get("rationale", ["Preview mode — evidence gaps only"]),
            "risks": boardroom.get("key_risks", ["Missing verified competitor evidence"]),
        },
        "final_report_audit": audit,
        "boardroom_strategist": boardroom,
        "diligence_pack": {
            "competitive_benchmark": [],
            "pricing_intelligence_pack": {"rows": []},
            "citation_ledger": [],
            "readiness": {
                "record_counts": {
                    "named_competitor_operator_records": 0,
                    "direct_pricing_unit_cost_records": 0,
                }
            },
        },
        "quantitative_model": {},
        "report_confidence": {"score": score, "financial_unknowns": list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)},
        "manual_preview": True,
        "evidence_gap_only": True,
    }
    stamp_payload_identity(payload, source="user")
    return payload


def mock_boardroom_verdict(report_payload: dict[str, Any] | None, report_v3: dict[str, Any] | None) -> dict[str, Any]:
    payload = report_payload or {}
    v3 = report_v3 or {}
    brain = payload.get("research_intelligence") or {}
    topic = str(payload.get("topic") or v3.get("topic") or "this market")
    comp_n = int((brain.get("competitor_map") or {}).get("competitor_count") or 0)
    verdict = "validate_before_scale" if comp_n < 3 else "proceed_with_validation"
    return {
        "investment_verdict": verdict,
        "market_timing": f"Evidence refresh required for {topic} before investor-grade competitor claims",
        "strategic_wedge": _VALIDATION,
        "rationale": [
            "Preview mode — competitor names withheld until verified",
            "Pricing anchors withheld until vendor pages are cited",
            "Run live retrieval before scaling GTM claims",
        ],
        "key_risks": list(brain.get("risk_flags") or ["Missing verified competitor evidence"]),
        "founder_actions": ["Run competitor discovery", "Capture pricing page URLs", "Collect review sources"],
        "analyst_mode": "boardroom_strategist_preview",
    }


def mock_claude_audit(report_payload: dict[str, Any] | None, report_v3: dict[str, Any] | None) -> dict[str, Any]:
    payload = report_payload or {}
    brain = payload.get("research_intelligence") or {}
    h = _topic_hash(str(payload.get("topic") or ""))
    base = 4.8 + (h % 15) / 10.0
    comp_n = int((brain.get("competitor_map") or {}).get("competitor_count") or 0)
    if comp_n < 3:
        base -= 1.5
    return {
        "market_style_score": round(min(7.0, max(3.5, base)), 1),
        "funding_ready": False,
        "audit_mode": "manual_preview",
        "strengths": ["Preview harness active", "No synthetic competitors injected"],
        "gaps": list(DEFAULT_COMPETITOR_EVIDENCE_GAPS),
    }


def mock_employee_response(employee_profile: dict[str, Any], context: dict[str, Any] | None = None) -> str:
    ctx = context or {}
    role = str(employee_profile.get("role") or "Team Member")
    style = str(employee_profile.get("communication_style") or "")
    tasks = len((ctx.get("assigned_tasks") or []))
    topic = str((ctx.get("report_context") or {}).get("topic") or "the plan")
    templates = {
        "Research Analyst": f"Evidence check on {topic}: need verified competitor names and pricing pages before we scale. Open tasks: {tasks}.",
        "Growth Marketer": f"Hold paid scale for {topic} until competitor/pricing evidence is verified. Tasks: {tasks}.",
        "Sales Lead": f"Do not publish competitor battlecards for {topic} until named vendors are verified. Tasks: {tasks}.",
        "COO": f"Clearing blockers first — {tasks} active tasks. Weekly cadence scheduled.",
        "Finance Manager": f"Unit economics withheld for {topic} until cited sources exist.",
        "Founder": f"Top priority today: verify competitor evidence for {topic}.",
    }
    msg = templates.get(role, f"Supporting {topic}. Tasks in queue: {tasks}.")
    if style:
        msg += f" ({style.split(',')[0]})"
    return msg


def apply_app_llm_mocks(app: Any, cost_tracker: Any | None = None) -> None:
    """Patch expensive app LLM entry points when manual preview is enabled."""
    global _PATCHED
    if not is_manual_preview() or _PATCHED:
        return

    def _bump(provider: str = "anthropic") -> None:
        if cost_tracker is not None:
            cost_tracker.record_preview_call(provider, 0.0)

    if hasattr(app, "run_boardroom_strategist"):
        orig_boardroom: Callable[..., Any] = app.run_boardroom_strategist

        def _boardroom(*args: Any, **kwargs: Any) -> dict[str, Any]:
            _bump("anthropic")
            payload = kwargs.get("report_payload") or (args[0] if args else {})
            return mock_boardroom_verdict(payload if isinstance(payload, dict) else {}, None)

        app.run_boardroom_strategist = _boardroom  # type: ignore[method-assign]

    if hasattr(app, "run_anthropic_section_audit"):
        def _audit(*args: Any, **kwargs: Any) -> dict[str, Any]:
            _bump("anthropic")
            payload = kwargs.get("report_payload") or kwargs.get("payload") or {}
            return mock_claude_audit(payload if isinstance(payload, dict) else {}, None)

        app.run_anthropic_section_audit = _audit  # type: ignore[method-assign]

    if hasattr(app, "anthropic_text_request"):
        orig_anthropic: Callable[..., Any] = app.anthropic_text_request

        def _anthropic(prompt: str, *args: Any, **kwargs: Any) -> tuple[str, str]:
            _bump("anthropic")
            low = str(prompt or "").lower()
            if "boardroom" in low or "investment verdict" in low:
                return json.dumps(mock_boardroom_verdict({}, None)), "preview-mock"
            if "audit" in low or "score" in low:
                return json.dumps(mock_claude_audit({}, None)), "preview-mock"
            return mock_employee_response({"role": "Research Analyst", "communication_style": "concise"}, {}), "preview-mock"

        app.anthropic_text_request = _anthropic  # type: ignore[method-assign]

    _PATCHED = True
