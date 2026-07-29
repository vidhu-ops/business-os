"""IIDATECH validation layer: source, pricing, financial, scoring honesty."""
from iidatech.validation.financial_validator import (
    assess_buyer_validation,
    assess_pricing_evidence,
    assess_tam_inputs,
    assess_unit_economics,
    build_financial_validation_summary,
    detect_placeholders,
)
from iidatech.validation.pricing_validator import filter_valid_pricing_rows, validate_pricing_row
from iidatech.validation.scoring_honesty import apply_honesty_score_caps
from iidatech.validation.source_validator import (
    audit_citation_ledger,
    classify_source_tier,
    filter_records_for_claim,
    tier_allows_claim,
    validate_record_for_claim,
)
from iidatech.validation.confidence_model import compute_guarded_confidence
from iidatech.validation.hallucination_firewall import (
    detect_hallucinations,
    hallucination_score,
    sanitize_hallucinated_fields,
)
from iidatech.validation.payload_guard import (
    assert_topic_not_overwritten,
    export_integrity_trace,
    snapshot_payload_identity,
    stamp_payload_identity,
    validate_payload_integrity,
)

__all__ = [
    "apply_honesty_score_caps",
    "assess_buyer_validation",
    "assess_pricing_evidence",
    "assess_tam_inputs",
    "assess_unit_economics",
    "audit_citation_ledger",
    "build_financial_validation_summary",
    "classify_source_tier",
    "detect_placeholders",
    "filter_records_for_claim",
    "filter_valid_pricing_rows",
    "tier_allows_claim",
    "validate_pricing_row",
    "validate_record_for_claim",
    "assert_topic_not_overwritten",
    "apply_v3_guard_to_payload",
    "compute_guarded_confidence",
    "detect_hallucinations",
    "export_integrity_trace",
    "guard_v3_render",
    "hallucination_score",
    "sanitize_hallucinated_fields",
    "snapshot_payload_identity",
    "stamp_payload_identity",
    "validate_payload_integrity",
]


def apply_v3_guard_to_payload(payload):  # noqa: ANN001
    from iidatech.validation.v3_render_guard import apply_v3_guard_to_payload as _fn

    return _fn(payload)


def guard_v3_render(payload):  # noqa: ANN001
    from iidatech.validation.v3_render_guard import guard_v3_render as _fn

    return _fn(payload)


__all__ += ["apply_v3_guard_to_payload", "guard_v3_render"]