"""V3 render guard — integrity + hallucination firewall before customer output."""
from __future__ import annotations

from typing import Any

from iidatech.validation.confidence_model import compute_guarded_confidence
from iidatech.validation.hallucination_firewall import (
    detect_hallucinations,
    sanitize_hallucinated_fields,
)
from iidatech.validation.payload_guard import (
    export_integrity_trace,
    stamp_payload_identity,
    validate_payload_integrity,
)

BLOCKED_HEADER = "REPORT BLOCKED — INSUFFICIENT VERIFIED DATA"


from iidatech.report_modes import filter_payload_by_mode, stamp_report_mode
from iidatech.validation.competitor_evidence import DEFAULT_COMPETITOR_EVIDENCE_GAPS


def _missing_evidence_list(payload: dict[str, Any], firewall: dict[str, Any]) -> list[str]:
    missing = list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
    codes = {i.get("code") for i in firewall.get("issues") or []}
    if not codes & {"fake_competitor", "generic_competitor_label", "unverified_competitor", "missing_pricing", "synthetic_pricing_source"}:
        missing = [m for m in missing if m != "competitor names" and m != "pricing pages"]
    if not codes & {"circular_icp", "circular_icp_topic"}:
        if "buyer interviews / ICP validation" not in missing:
            pass
    if codes & {"synthetic_tam"}:
        if "TAM denominator inputs" not in missing:
            missing.append("TAM denominator inputs")
    if codes & {"impossible_cac", "impossible_arpu", "suspicious_payback", "suspicious_ltv_cac"}:
        if "unit economics with cited sources" not in missing:
            missing.append("unit economics with cited sources")
    return missing


def render_blocked_markdown(
    *,
    topic: str,
    integrity: dict[str, Any],
    firewall: dict[str, Any],
    missing: list[str],
) -> str:
    lines = [
        f"# {BLOCKED_HEADER}",
        "",
        f"**Topic:** {topic or 'unknown'}",
        "",
        "This report was blocked because verified research data failed integrity or hallucination checks.",
        "",
        "## Missing / unverified evidence",
        "",
    ]
    for item in missing:
        lines.append(f"- {item}")
    violations = integrity.get("violations") or []
    if violations:
        lines.append("")
        lines.append("## Payload integrity violations")
        lines.append("")
        for v in violations:
            lines.append(f"- {v}")
    critical = firewall.get("critical") or []
    if critical:
        lines.append("")
        lines.append("## Hallucination firewall (critical)")
        lines.append("")
        for issue in critical[:12]:
            lines.append(f"- `{issue.get('code')}`: {issue.get('detail')}")
    lines.append("")
    lines.append("_No fabricated competitors, pricing, or unit economics are shown._")
    return "\n".join(lines)


def _firewall_hard_block(firewall: dict[str, Any]) -> bool:
    hard = int(firewall.get("hard_critical_count") or 0)
    if hard > 0:
        return True
    critical = firewall.get("critical") or []
    return any(i.get("code") in {"fake_competitor", "generic_competitor_label", "circular_icp", "circular_icp_topic",
        "impossible_cac", "impossible_arpu", "suspicious_payback", "suspicious_ltv_cac", "manual_preview_synthetic"}
        for i in critical if isinstance(i, dict))


def guard_v3_render(payload: dict[str, Any]) -> dict[str, Any]:
    from iidatech.renderers.report_v3 import render_v3_report_markdown

    payload = payload if isinstance(payload, dict) else {}
    stamp_payload_identity(payload, source=payload.get("_identity_source") or "pipeline")
    topic = str(payload.get("topic") or (payload.get("_identity_snapshot") or {}).get("topic") or "")
    mode = stamp_report_mode(
        payload,
        user_query=topic,
        selected_mode=payload.get("report_mode"),
        workflow_choice=str(payload.get("workflow_choice") or ""),
    )
    payload = filter_payload_by_mode(payload, mode)

    snapshot = payload.get("_identity_snapshot") or {}
    integrity = validate_payload_integrity(payload, snapshot)
    firewall = detect_hallucinations(payload)
    export_integrity_trace(payload, integrity)

    topic = str(payload.get("topic") or snapshot.get("topic") or "")
    try:
        from iidatech.validation.consumer_trust import consumer_trust_block_reasons
    except ImportError:
        def consumer_trust_block_reasons(_payload: dict[str, Any]) -> list[str]:
            return []

    trust_reasons = consumer_trust_block_reasons(payload)
    blocked = (not integrity.get("ok", True)) or _firewall_hard_block(firewall) or bool(trust_reasons)

    if blocked:
        missing = _missing_evidence_list(payload, firewall)
        for reason in trust_reasons:
            label = reason.replace("_", " ")
            if label not in missing:
                missing.append(label)
        audit = payload.get("final_report_audit") if isinstance(payload.get("final_report_audit"), dict) else {}
        honesty = audit.get("honesty_audit") if isinstance(audit.get("honesty_audit"), dict) else {}
        if honesty.get("honesty_enforced"):
            missing.append(
                f"Honesty-capped quality: {honesty.get('honest_score', 'n/a')}/10 "
                f"(caps: {', '.join(str(c.get('reason')) for c in (honesty.get('caps_applied') or []) if isinstance(c, dict))})"
            )
        markdown = render_blocked_markdown(topic=topic, integrity=integrity, firewall=firewall, missing=missing)
        confidence = compute_guarded_confidence(payload, integrity=integrity, firewall=firewall)
        payload["report_confidence"] = confidence
        payload["v3_render_blocked"] = True
        payload["hallucination_firewall"] = firewall
        return {
            "blocked": True,
            "v3": None,
            "markdown": markdown,
            "integrity": integrity,
            "firewall": firewall,
            "confidence": confidence,
            "trace": payload.get("integrity_trace"),
        }

    clean = sanitize_hallucinated_fields(payload)
    clean_firewall = detect_hallucinations(clean)
    from iidatech.core.report_compiler import compile_for_mode, validate_canonical_report
    from iidatech.core.truth_arbiter import (
        build_canonical_truth_object,
        should_block_customer_report,
    )
    from iidatech.core.truth_arbiter import adapt_arbiter_truth_for_compiler

    canonical_truth = build_canonical_truth_object(clean)
    arbiter_blocked, arbiter_reasons = should_block_customer_report(
        canonical_truth, firewall=clean_firewall, integrity=integrity
    )
    canonical = adapt_arbiter_truth_for_compiler(canonical_truth)
    validate_canonical_report(canonical)
    clean["canonical_truth"] = canonical_truth
    clean["canonical_report"] = canonical

    if _firewall_hard_block(clean_firewall) or arbiter_blocked or consumer_trust_block_reasons(clean):
        missing = _missing_evidence_list(clean, clean_firewall)
        for r in arbiter_reasons:
            if r not in missing:
                missing.append(r)
        for reason in consumer_trust_block_reasons(clean):
            label = reason.replace("_", " ")
            if label not in missing:
                missing.append(label)
        markdown = render_blocked_markdown(topic=topic, integrity=integrity, firewall=clean_firewall, missing=missing)
        confidence = compute_guarded_confidence(clean, integrity=integrity, firewall=clean_firewall)
        clean["report_confidence"] = confidence
        clean["v3_render_blocked"] = True
        return {
            "blocked": True,
            "v3": None,
            "markdown": markdown,
            "integrity": integrity,
            "firewall": clean_firewall,
            "confidence": confidence,
            "trace": clean.get("integrity_trace"),
        }

    mode = stamp_report_mode(
        clean,
        user_query=topic,
        selected_mode=clean.get("report_mode"),
        workflow_choice=str(clean.get("workflow_choice") or ""),
    )
    v3 = compile_for_mode(canonical, mode)
    confidence = compute_guarded_confidence(clean, integrity=integrity, firewall=clean_firewall)
    clean["report_confidence"] = confidence
    if isinstance(v3, dict):
        v3["report_truth_confidence"] = confidence
        v3["guarded_confidence"] = confidence
    markdown = render_v3_report_markdown(v3)
    clean["v3_render_blocked"] = False
    clean["hallucination_firewall"] = clean_firewall
    return {
        "blocked": False,
        "v3": v3,
        "markdown": markdown,
        "integrity": integrity,
        "firewall": clean_firewall,
        "confidence": confidence,
        "trace": clean.get("integrity_trace"),
        "payload": clean,
    }


def apply_v3_guard_to_payload(payload: dict[str, Any]) -> dict[str, Any]:
    result = guard_v3_render(payload)
    if isinstance(result.get("payload"), dict):
        payload.update(result["payload"])
    payload["report_v3"] = result.get("v3")
    payload["report_v3_markdown"] = result.get("markdown") or ""
    payload["v3_guard"] = {
        "blocked": result.get("blocked"),
        "confidence": result.get("confidence"),
        "firewall": result.get("firewall"),
        "integrity": result.get("integrity"),
    }
    return result