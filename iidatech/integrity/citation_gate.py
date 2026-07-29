"""Citation admissibility gate for IIDATECH (PR1-A).

Separates two distinct permissions:

    reasoning_allowed   -- evidence may inform report reasoning and context
    citation_allowed    -- evidence may appear as a named citation in
                           investor-grade reports

A source may be useful for reasoning but inadmissible for citation.
Examples:
    Reddit post          -> reasoning yes, citation no
    Vendor blog          -> reasoning yes, citation no (hard metrics)
    Government dataset   -> yes / yes
    Synthetic model      -> neither (planning only)

Citation admissibility is separate from relevance and trust tier eligibility.
It must be combined with tri-state eligibility from relevance_gate.py:

    final_citation_allowed =
        eligibility_status == ELIGIBLE
        AND citation_admissible(record, claim_context)
        AND final_claim_trust >= CLAIM_TRUST_FLOOR_CITATION_LEDGER

All functions are pure. No Streamlit. No app.py imports. No side effects.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Source families: reasoning and citation permissions
# ---------------------------------------------------------------------------

# (reasoning_allowed, citation_allowed)
_FAMILY_PERMISSIONS: dict[str, tuple[bool, bool]] = {
    # Tier 1 - full permissions
    "government": (True, True),
    "government_statistics": (True, True),
    "central_bank": (True, True),
    "international_organization": (True, True),
    "regulatory_body": (True, True),
    "company_filing": (True, True),
    "official_statistic": (True, True),
    "census": (True, True),
    "national_health_authority": (True, True),
    # Tier 2 - reasoning + conditional citation (caller checks claim trust floor)
    "analyst_report": (True, True),
    "market_research": (True, True),
    "industry_survey": (True, True),
    "trade_association": (True, True),
    "ngo_report": (True, True),
    "benchmark_report": (True, True),
    "professional_survey": (True, True),
    "clinical_study": (True, True),
    "conference_proceeding": (True, True),
    # Tier 3 - reasoning allowed, citation generally no
    "vendor_documentation": (True, False),
    "product_documentation": (True, False),
    "company_blog": (True, False),
    "industry_news": (True, False),
    "approved_press": (True, False),
    "trade_press": (True, False),
    "financial_news": (True, False),
    "academic_preprint": (True, False),
    "thesis": (True, False),
    "technical_whitepaper": (True, False),
    # Academic research - citation allowed only for Tier 1 academic (checked below)
    "academic_research": (True, None),   # None = depends on academic tier
    "peer_reviewed_journal": (True, True),
    "research_paper": (True, None),
    "academic": (True, None),
    # Qualitative-only sources: customer pain, complaints, PMF and workflow signals.
    # Numeric claims and investor citations remain blocked elsewhere.
    "social_media": (True, False),
    "forum": (True, False),
    "reddit": (True, False),
    # Tier 4 - blocked
    "public_web": (False, False),
    "scraped_html": (False, False),
    "seo_content": (False, False),
    "news_aggregator": (False, False),
    "synthetic_model": (False, False),
    "financial_model_bank": (False, False),
    "route_only": (False, False),
    "unknown": (False, False),
}

# Claim classes that are never investor-citable
_NON_CITABLE_CLAIM_CLASSES: frozenset[str] = frozenset({
    "promotional_claim",
    "synthetic_model_output",
})

# Claim classes admissible for citation when source tier allows it
_CITABLE_CLAIM_CLASSES: frozenset[str] = frozenset({
    "audited_financial",
    "government_stat",
    "regulatory_fact",
    "survey_estimate",
    "analyst_estimate",
})

# Minimum claim trust score required for citation
_CITATION_CLAIM_TRUST_MINIMUM = 0.65

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _source_family(record: dict[str, Any]) -> str:
    return str(
        record.get("source_family")
        or record.get("source_type")
        or record.get("family")
        or "unknown"
    ).lower()


def _claim_class(claim_context: dict[str, Any] | None) -> str | None:
    if not claim_context:
        return None
    return claim_context.get("claim_class") or claim_context.get("claim_type")


# ---------------------------------------------------------------------------
# Core permission functions
# ---------------------------------------------------------------------------


def reasoning_allowed(
    record: dict[str, Any],
    claim_context: dict[str, Any] | None = None,
) -> bool:
    """Return True if this record may inform report reasoning or context.

    Reasoning is allowed for all sources except hard-blocked families
    (public_web, scraped_html, social_media, synthetic, etc.).
    """
    family = _source_family(record)

    if family in _FAMILY_PERMISSIONS:
        allowed, _ = _FAMILY_PERMISSIONS[family]
        # None is used for academic — reasoning always allowed for academic
        return bool(allowed) if allowed is not None else True

    # Default: block unknown families
    return False


def citation_admissible(
    record: dict[str, Any],
    claim_context: dict[str, Any] | None = None,
) -> bool:
    """Return True if this record+claim may appear in an investor-grade citation.

    Combines:
      - Source family admissibility
      - Academic trust tier (for academic families)
      - Claim class admissibility
      - Minimum claim trust threshold (if provided in claim_context)

    Does NOT check relevance or trust tier ceiling — that is handled
    by resolve_tri_state_eligibility() in relevance_gate.py.
    """
    family = _source_family(record)

    # Hard blocks
    if family in _FAMILY_PERMISSIONS:
        _, citable = _FAMILY_PERMISSIONS[family]
        if citable is False:
            return False
        if citable is True:
            pass  # proceed to claim-level checks
        # citable is None: academic family — check trust_tier on record
        if citable is None:
            trust_tier = record.get("trust_tier")
            if trust_tier is None or int(trust_tier) > 1:
                return False
    else:
        # Unknown family: not citable
        return False

    # Claim class check
    claim_cls = _claim_class(claim_context)
    if claim_cls is not None:
        if claim_cls in _NON_CITABLE_CLAIM_CLASSES:
            return False
        if claim_cls not in _CITABLE_CLAIM_CLASSES:
            # marketing_tam and unknown are not investor-citable
            return False

    # Final claim trust threshold (if caller provides it in claim_context)
    if claim_context:
        final_trust = claim_context.get("final_claim_trust")
        if final_trust is not None and float(final_trust) < _CITATION_CLAIM_TRUST_MINIMUM:
            return False

    return True


# ---------------------------------------------------------------------------
# Structured admissibility result
# ---------------------------------------------------------------------------


def compute_citation_admissibility(
    record: dict[str, Any],
    claim_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a structured citation admissibility result.

    Returns:
        reasoning_allowed (bool)
        citation_admissible (bool)
        source_family (str)
        admissibility_reason (str)
    """
    family = _source_family(record)
    r_allowed = reasoning_allowed(record, claim_context)
    c_allowed = citation_admissible(record, claim_context)

    if not r_allowed:
        reason = f"reasoning_blocked_family_{family}"
    elif not c_allowed:
        claim_cls = _claim_class(claim_context)
        if claim_cls in _NON_CITABLE_CLAIM_CLASSES:
            reason = f"non_citable_claim_class_{claim_cls}"
        elif family in _FAMILY_PERMISSIONS and _FAMILY_PERMISSIONS[family][1] is False:
            reason = f"non_citable_source_family_{family}"
        elif family in _FAMILY_PERMISSIONS and _FAMILY_PERMISSIONS[family][1] is None:
            tier = record.get("trust_tier", "unknown")
            reason = f"academic_tier_{tier}_not_citable"
        elif claim_context and claim_context.get("final_claim_trust", 1.0) < _CITATION_CLAIM_TRUST_MINIMUM:
            trust = claim_context.get("final_claim_trust", 0)
            reason = f"claim_trust_{trust:.2f}_below_citation_minimum"
        else:
            reason = "claim_class_not_investor_citable"
    else:
        reason = "admissible"

    return {
        "reasoning_allowed": r_allowed,
        "citation_admissible": c_allowed,
        "source_family": family,
        "admissibility_reason": reason,
    }