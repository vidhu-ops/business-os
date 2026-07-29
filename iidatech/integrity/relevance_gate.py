"""Adaptive relevance gating for IIDATECH evidence retrieval (PR1-A).

Implements:
  - Evidence density estimation (high / medium / sparse)
  - Adaptive relevance floor resolution (sparse markets get lowered floors)
  - Market relevance scoring (composed signal)
  - Tri-state retrieval eligibility (eligible / unknown / rejected)

The effective relevance floor is:
    effective_floor = max(base_floor - sparsity_bonus, min_floor)

Final retrieval eligibility requires:
    corpus == real_evidence
    AND source_trust_tier <= section_allowed_max_tier
    AND claim_trust_score >= claim_trust_floor
    AND market_relevance_score >= effective_relevance_floor
    AND not synthetic
    AND not route_only
    AND metadata_completeness checks pass

Unknown status = soft context only; never investor citation.

All functions are pure. No Streamlit. No app.py imports. No side effects.

Feature flags (applied by caller):
    IIDATECH_RELEVANCE_GATING
    IIDATECH_RELEVANCE_FLOOR_DEFAULT     (default 0.42)
    IIDATECH_RELEVANCE_FLOOR_NICHE       (default 0.50)
    IIDATECH_RELEVANCE_FLOOR_CITATION    (default 0.45)
    IIDATECH_RELEVANCE_FLOOR_MIN_SPARSE  (default 0.30)
    IIDATECH_RELEVANCE_FLOOR_HARD_NUMERIC (default 0.50)
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Density bands
# ---------------------------------------------------------------------------

DENSITY_HIGH = "high"
DENSITY_MEDIUM = "medium"
DENSITY_SPARSE = "sparse"

# Thresholds for candidate record counts
_DENSITY_HIGH_THRESHOLD = 30
_DENSITY_SPARSE_THRESHOLD = 8

# ---------------------------------------------------------------------------
# Base relevance floors per retrieval path
# ---------------------------------------------------------------------------

# Defaults — callers should read from env and pass in; these are fallbacks
FLOOR_DEFAULT = 0.42
FLOOR_NICHE = 0.50
FLOOR_CITATION_LEDGER = 0.45
FLOOR_HARD_NUMERIC = 0.50

FLOOR_MIN_GENERAL = 0.28      # absolute minimum for general retrieval
FLOOR_MIN_CITATION = 0.36     # absolute minimum for citation ledger
FLOOR_MIN_HARD_NUMERIC = 0.40 # absolute minimum for hard numeric claims

# Sparsity bonus applied when density == sparse
_SPARSITY_BONUS = 0.10
# Partial bonus for medium density
_MEDIUM_BONUS = 0.04

# ---------------------------------------------------------------------------
# Section-level allowed trust tier ceilings
# ---------------------------------------------------------------------------

# Maps lowercased section title substrings to (max_trust_tier, relevance_floor)
_SECTION_TIER_CEILINGS: list[tuple[str, int, float]] = [
    ("market size", 2, 0.50),
    ("valuation", 2, 0.50),
    ("financial forecast", 2, 0.50),
    ("executive summary", 2, 0.45),
    ("tam", 2, 0.50),
    ("sam", 2, 0.50),
    ("som", 2, 0.50),
    ("regulatory", 2, 0.42),
    ("compliance", 2, 0.42),
    ("competitive", 3, 0.42),
    ("pricing", 3, 0.42),
    ("technology landscape", 3, 0.40),
    ("technology", 3, 0.40),
    ("consumer", 3, 0.38),
    ("go-to-market", 3, 0.38),
    ("gtm", 3, 0.38),
    ("market entry", 3, 0.38),
]

_DEFAULT_SECTION_MAX_TIER = 3
_DEFAULT_SECTION_FLOOR = 0.42

# ---------------------------------------------------------------------------
# Market relevance domain / topic tokens
# ---------------------------------------------------------------------------

# Niche domain indicators that raise the floor
_NICHE_DOMAIN_TOKENS: frozenset[str] = frozenset({
    "dental", "ophthalmology", "dermatology", "orthopaedic", "veterinary",
    "tier 2", "tier 3", "tier2", "tier3", "rural", "semi-urban",
    "micro saas", "vertical saas", "niche", "specialty",
    "b2b saas", "enterprise saas",
})

# Generic denominator tokens that reduce relevance (macro stats)
_GENERIC_DENOMINATOR_TOKENS: frozenset[str] = frozenset({
    "total population", "internet users", "smartphone users",
    "gdp per capita", "total gdp", "all industries",
    "entire economy", "global market",
})


def _text_for_record(record: dict[str, Any]) -> str:
    parts = [
        record.get("title", ""),
        record.get("metric_name", ""),
        record.get("description", ""),
        record.get("source", ""),
        record.get("tags", ""),
        record.get("domains", ""),
    ]
    cleaned = []
    for p in parts:
        if isinstance(p, list):
            cleaned.append(" ".join(str(x) for x in p))
        elif p:
            cleaned.append(str(p))
    return " ".join(cleaned).lower()


# ---------------------------------------------------------------------------
# Density estimation
# ---------------------------------------------------------------------------


def estimate_evidence_density(
    candidate_count: int,
    vector_candidate_count: int = 0,
    section_specific_count: int = 0,
) -> dict[str, Any]:
    """Estimate evidence density for a topic/section query.

    candidate_count: raw records passing corpus/tier filters
    vector_candidate_count: records from vector search (weighted 0.5)
    section_specific_count: records with strong section-type match
    """
    weighted_total = (
        candidate_count
        + int(vector_candidate_count * 0.5)
        + int(section_specific_count * 1.5)
    )

    if weighted_total >= _DENSITY_HIGH_THRESHOLD:
        band = DENSITY_HIGH
    elif weighted_total <= _DENSITY_SPARSE_THRESHOLD:
        band = DENSITY_SPARSE
    else:
        band = DENSITY_MEDIUM

    return {
        "density_band": band,
        "weighted_total": weighted_total,
        "raw_candidate_count": candidate_count,
        "vector_candidate_count": vector_candidate_count,
        "section_specific_count": section_specific_count,
    }


# ---------------------------------------------------------------------------
# Effective floor resolution
# ---------------------------------------------------------------------------


def resolve_effective_relevance_floor(
    base_floor: float,
    density_band: str,
    min_floor: float = FLOOR_MIN_GENERAL,
    is_hard_numeric: bool = False,
    is_citation_ledger: bool = False,
) -> dict[str, Any]:
    """Compute the effective relevance floor given density and context.

    Sparse markets receive a sparsity_bonus reduction.
    Hard numeric and citation ledger paths enforce higher minimums.
    """
    if density_band == DENSITY_SPARSE:
        sparsity_bonus = _SPARSITY_BONUS
    elif density_band == DENSITY_MEDIUM:
        sparsity_bonus = _MEDIUM_BONUS
    else:
        sparsity_bonus = 0.0

    if is_hard_numeric:
        effective_min = max(min_floor, FLOOR_MIN_HARD_NUMERIC)
    elif is_citation_ledger:
        effective_min = max(min_floor, FLOOR_MIN_CITATION)
    else:
        effective_min = min_floor

    effective_floor = max(base_floor - sparsity_bonus, effective_min)

    return {
        "base_floor": base_floor,
        "effective_floor": round(effective_floor, 3),
        "density_band": density_band,
        "sparsity_bonus_applied": round(sparsity_bonus, 3),
        "min_floor": effective_min,
    }


# ---------------------------------------------------------------------------
# Market relevance score
# ---------------------------------------------------------------------------


def compute_market_relevance_score(
    record: dict[str, Any],
    *,
    topic: str = "",
    industry: str = "",
    target: str = "",
    section: str = "",
    domain: str = "",
    domain_confidence: float | None = None,
    niche_match_score: float | None = None,
    topic_token_overlap: float | None = None,
    section_claim_fit: float | None = None,
    academic_relevance_subscore: float | None = None,
) -> float:
    """Compute a market relevance score [0.0, 1.0] for a record.

    Uses a weighted blend of sub-signals. Callers may pass pre-computed
    sub-scores from existing app.py helpers (record_domain_confidence,
    source_precision_check, etc.) or leave as None to use fallbacks.

    This function does NOT replace existing scoring — it composes signals
    that already exist in the retrieval path.
    """
    text = _text_for_record(record)

    # Sub-signal 1: domain confidence (from record_domain_confidence or fallback)
    if domain_confidence is not None:
        sig_domain = _clamp01(float(domain_confidence))
    else:
        sig_domain = _clamp01(_lexical_domain_confidence(record, domain, industry))

    # Sub-signal 2: niche match
    if niche_match_score is not None:
        sig_niche = _clamp01(float(niche_match_score))
    else:
        sig_niche = _clamp01(_lexical_niche_match(record, industry, target))

    # Sub-signal 3: topic token overlap
    if topic_token_overlap is not None:
        sig_topic = _clamp01(float(topic_token_overlap))
    else:
        sig_topic = _clamp01(_lexical_topic_overlap(text, topic, industry))

    # Sub-signal 4: section claim fit (0.5 default — neutral)
    sig_section = _clamp01(float(section_claim_fit) if section_claim_fit is not None else 0.50)

    # Sub-signal 5: academic relevance
    sig_academic = _clamp01(
        float(academic_relevance_subscore) if academic_relevance_subscore is not None else 1.0
    )

    # Generic denominator penalty
    generic_penalty = 1.0
    if any(token in text for token in _GENERIC_DENOMINATOR_TOKENS):
        if not any(kw in text for kw in (topic.lower(), industry.lower(), target.lower()) if kw):
            generic_penalty = 0.60

    # Weighted blend
    score = (
        sig_domain * 0.30
        + sig_niche * 0.25
        + sig_topic * 0.25
        + sig_section * 0.10
        + sig_academic * 0.10
    ) * generic_penalty

    return round(min(max(score, 0.0), 1.0), 3)


def _clamp01(value: float) -> float:
    return min(max(value, 0.0), 1.0)


def _lexical_domain_confidence(
    record: dict[str, Any], domain: str, industry: str
) -> float:
    text = _text_for_record(record)
    kws = [kw.lower().strip() for kw in (domain, industry) if kw]
    if not kws:
        return 0.50
    hits = sum(1 for kw in kws if kw in text)
    return round(min(hits / len(kws), 1.0), 3)


def _lexical_niche_match(
    record: dict[str, Any], industry: str, target: str
) -> float:
    text = _text_for_record(record)
    terms = [t.lower().strip() for t in (industry, target) if t]
    if not terms:
        return 0.50

    niche_hit = any(token in text for token in _NICHE_DOMAIN_TOKENS)
    term_hits = sum(1 for t in terms if t in text)
    base = min(term_hits / max(len(terms), 1), 1.0)

    if niche_hit:
        base = min(base + 0.15, 1.0)
    return round(base, 3)


def _lexical_topic_overlap(text: str, topic: str, industry: str) -> float:
    if not topic and not industry:
        return 0.50
    tokens = set((topic + " " + industry).lower().split())
    tokens = {t for t in tokens if len(t) >= 4}
    if not tokens:
        return 0.50
    hits = sum(1 for t in tokens if t in text)
    return round(min(hits / len(tokens), 1.0), 3)


# ---------------------------------------------------------------------------
# Section tier ceiling lookup
# ---------------------------------------------------------------------------


def section_allowed_max_tier(section_title: str, funding_ready_mode: bool = False) -> int:
    """Return the maximum allowed trust tier for a section."""
    lower = section_title.lower()
    for fragment, max_tier, _ in _SECTION_TIER_CEILINGS:
        if fragment in lower:
            return max_tier
    return _DEFAULT_SECTION_MAX_TIER


def section_relevance_floor(section_title: str) -> float:
    """Return the base relevance floor for a section."""
    lower = section_title.lower()
    for fragment, _, floor in _SECTION_TIER_CEILINGS:
        if fragment in lower:
            return floor
    return _DEFAULT_SECTION_FLOOR


# ---------------------------------------------------------------------------
# Tri-state eligibility
# ---------------------------------------------------------------------------

ELIGIBILITY_ELIGIBLE = "eligible"
ELIGIBILITY_UNKNOWN = "unknown"
ELIGIBILITY_REJECTED = "rejected"


def resolve_tri_state_eligibility(
    record: dict[str, Any],
    *,
    trust_tier: int,
    final_claim_trust: float,
    market_relevance_score: float,
    effective_relevance_floor: float,
    section_max_tier: int,
    claim_trust_floor: float,
    citation_admissible: bool = True,
) -> dict[str, Any]:
    """Compute tri-state retrieval eligibility.

    Returns:
        status: eligible | unknown | rejected
        reasoning_allowed (bool)
        citation_allowed (bool)
        reason_codes (list[str])
        effective_relevance_floor (float)
        market_relevance_score (float)
        final_claim_trust (float)
    """
    reason_codes: list[str] = []
    family = str(
        record.get("source_family") or record.get("source_type") or record.get("family") or ""
    ).lower()
    evidence_namespace = str(record.get("evidence_namespace") or "").lower()

    # Hard rejects
    if family in ("synthetic_model", "financial_model_bank", "route_only"):
        return _make_result(
            ELIGIBILITY_REJECTED,
            reason_codes=["synthetic_or_route_only"],
            relevance_floor=effective_relevance_floor,
            relevance_score=market_relevance_score,
            claim_trust=final_claim_trust,
            citation_admissible=citation_admissible,
        )

    if evidence_namespace == "synthetic":
        return _make_result(
            ELIGIBILITY_REJECTED,
            reason_codes=["synthetic_namespace"],
            relevance_floor=effective_relevance_floor,
            relevance_score=market_relevance_score,
            claim_trust=final_claim_trust,
            citation_admissible=citation_admissible,
        )

    # Unknown / incomplete metadata checks
    unknown_reasons: list[str] = []
    if not record.get("url") and not record.get("source_url"):
        unknown_reasons.append("missing_url")
    if not record.get("year") and not record.get("publication_year") and not record.get("data_year"):
        unknown_reasons.append("missing_year")
    geo = record.get("geography") or record.get("region") or record.get("market_geography")
    if not geo:
        unknown_reasons.append("missing_geography")
    if record.get("metric_extraction_partial"):
        unknown_reasons.append("partial_metric_extraction")

    # Trust tier gate
    if trust_tier > section_max_tier:
        reason_codes.append(f"tier_{trust_tier}_exceeds_max_{section_max_tier}")
        return _make_result(
            ELIGIBILITY_REJECTED,
            reason_codes=reason_codes,
            relevance_floor=effective_relevance_floor,
            relevance_score=market_relevance_score,
            claim_trust=final_claim_trust,
            citation_admissible=citation_admissible,
        )

    # Claim trust gate
    if final_claim_trust < claim_trust_floor:
        reason_codes.append(f"claim_trust_{final_claim_trust:.2f}_below_floor_{claim_trust_floor}")
        return _make_result(
            ELIGIBILITY_REJECTED,
            reason_codes=reason_codes,
            relevance_floor=effective_relevance_floor,
            relevance_score=market_relevance_score,
            claim_trust=final_claim_trust,
            citation_admissible=citation_admissible,
        )

    # Relevance gate
    if market_relevance_score < effective_relevance_floor:
        reason_codes.append(
            f"relevance_{market_relevance_score:.2f}_below_floor_{effective_relevance_floor:.2f}"
        )
        return _make_result(
            ELIGIBILITY_REJECTED,
            reason_codes=reason_codes,
            relevance_floor=effective_relevance_floor,
            relevance_score=market_relevance_score,
            claim_trust=final_claim_trust,
            citation_admissible=citation_admissible,
        )

    # Passed all hard gates — but unknown metadata → downgrade to unknown
    if unknown_reasons:
        return _make_result(
            ELIGIBILITY_UNKNOWN,
            reason_codes=unknown_reasons,
            relevance_floor=effective_relevance_floor,
            relevance_score=market_relevance_score,
            claim_trust=final_claim_trust,
            citation_admissible=citation_admissible,
        )

    return _make_result(
        ELIGIBILITY_ELIGIBLE,
        reason_codes=[],
        relevance_floor=effective_relevance_floor,
        relevance_score=market_relevance_score,
        claim_trust=final_claim_trust,
        citation_admissible=citation_admissible,
    )


def _make_result(
    status: str,
    *,
    reason_codes: list[str],
    relevance_floor: float,
    relevance_score: float,
    claim_trust: float,
    citation_admissible: bool,
) -> dict[str, Any]:
    reasoning_allowed = status in (ELIGIBILITY_ELIGIBLE, ELIGIBILITY_UNKNOWN)
    citation_allowed = (
        status == ELIGIBILITY_ELIGIBLE
        and citation_admissible
    )
    return {
        "status": status,
        "reasoning_allowed": reasoning_allowed,
        "citation_allowed": citation_allowed,
        "reason_codes": reason_codes,
        "effective_relevance_floor": relevance_floor,
        "market_relevance_score": relevance_score,
        "final_claim_trust": claim_trust,
    }