"""Source integrity helpers for IIDATECH."""

from iidatech.integrity.rescue_numeric_guard import (
    apply_rescue_funding_strict_redaction,
    build_rescue_guard_status,
    build_rescue_numeric_allowlist,
    build_rescue_strict_allowlist,
)
from iidatech.integrity.source_trust_tier import (
    TIER_HARD_TRUSTED,
    TIER_SOFT_TRUSTED,
    TIER_CONTEXT_ONLY,
    TIER_BLOCKED,
    academic_hard_science_score,
    academic_market_relevance_score,
    classify_academic_subject,
    classify_academic_tier,
    classify_source_trust_tier,
    source_trust_tier,
)
from iidatech.integrity.evidence_namespace import (
    REAL_EVIDENCE_NAMESPACE,
    SYNTHETIC_MODEL_NAMESPACE,
    evidence_namespace_for_record,
    namespace_permissions,
    namespace_schema_fields,
    is_synthetic_namespace,
)
from iidatech.integrity.claim_trust import (
    CLAIM_CLASS_AUDITED_FINANCIAL,
    CLAIM_CLASS_GOVERNMENT_STAT,
    CLAIM_CLASS_ANALYST_ESTIMATE,
    CLAIM_CLASS_MARKETING_TAM,
    CLAIM_CLASS_SYNTHETIC,
    CLAIM_TRUST_FLOOR_HARD_NUMERIC,
    CLAIM_TRUST_FLOOR_CITATION_LEDGER,
    classify_claim_class,
    compute_extraction_confidence,
    claim_trust_score,
)
from iidatech.integrity.relevance_gate import (
    DENSITY_HIGH,
    DENSITY_MEDIUM,
    DENSITY_SPARSE,
    ELIGIBILITY_ELIGIBLE,
    ELIGIBILITY_UNKNOWN,
    ELIGIBILITY_REJECTED,
    estimate_evidence_density,
    resolve_effective_relevance_floor,
    compute_market_relevance_score,
    section_allowed_max_tier,
    section_relevance_floor,
    resolve_tri_state_eligibility,
)
from iidatech.integrity.citation_gate import (
    reasoning_allowed,
    citation_admissible,
    compute_citation_admissibility,
)
from iidatech.integrity.provenance_ledger import (
    build_source_claim,
    build_formula_claim,
    compute_derived_confidence,
)

__all__ = [
    # rescue numeric guard (P0.3)
    "apply_rescue_funding_strict_redaction",
    "build_rescue_guard_status",
    "build_rescue_numeric_allowlist",
    "build_rescue_strict_allowlist",
    # source trust tiers (PR1-A)
    "TIER_HARD_TRUSTED",
    "TIER_SOFT_TRUSTED",
    "TIER_CONTEXT_ONLY",
    "TIER_BLOCKED",
    "academic_hard_science_score",
    "academic_market_relevance_score",
    "classify_academic_subject",
    "classify_academic_tier",
    "classify_source_trust_tier",
    "source_trust_tier",
    # evidence namespace (PR1-B)
    "REAL_EVIDENCE_NAMESPACE",
    "SYNTHETIC_MODEL_NAMESPACE",
    "evidence_namespace_for_record",
    "namespace_permissions",
    "namespace_schema_fields",
    "is_synthetic_namespace",
    # claim trust (PR1-A)
    "CLAIM_CLASS_AUDITED_FINANCIAL",
    "CLAIM_CLASS_GOVERNMENT_STAT",
    "CLAIM_CLASS_ANALYST_ESTIMATE",
    "CLAIM_CLASS_MARKETING_TAM",
    "CLAIM_CLASS_SYNTHETIC",
    "CLAIM_TRUST_FLOOR_HARD_NUMERIC",
    "CLAIM_TRUST_FLOOR_CITATION_LEDGER",
    "classify_claim_class",
    "compute_extraction_confidence",
    "claim_trust_score",
    # relevance gating (PR1-A)
    "DENSITY_HIGH",
    "DENSITY_MEDIUM",
    "DENSITY_SPARSE",
    "ELIGIBILITY_ELIGIBLE",
    "ELIGIBILITY_UNKNOWN",
    "ELIGIBILITY_REJECTED",
    "estimate_evidence_density",
    "resolve_effective_relevance_floor",
    "compute_market_relevance_score",
    "section_allowed_max_tier",
    "section_relevance_floor",
    "resolve_tri_state_eligibility",
    # citation gate (PR1-A)
    "reasoning_allowed",
    "citation_admissible",
    "compute_citation_admissibility",
    # provenance ledger (PR1-C)
    "build_source_claim",
    "build_formula_claim",
    "compute_derived_confidence",
]