"""Source trust tier classification for IIDATECH (PR1-A).

Assigns Tier 1-4 to evidence records based on source family, host domain,
and academic sub-classification rules.

Tier 1 - Hard trusted (government, official filings, official statistics,
          peer-reviewed market-relevant academic).
Tier 2 - Soft trusted (analyst reports, industry surveys, trade associations).
Tier 3 - Context only (vendor docs, approved press, preprints, low-relevance academic).
Tier 4 - Blocked / near-blocked (public_web default, SEO, scraped HTML,
          social/forum, spam, irrelevant academic).

All functions are pure. No Streamlit. No app.py imports. No side effects.

Feature flag (applied by caller): IIDATECH_SOURCE_TRUST_TIERS
"""
from __future__ import annotations

from typing import Any

TIER_HARD_TRUSTED = 1
TIER_SOFT_TRUSTED = 2
TIER_CONTEXT_ONLY = 3
TIER_BLOCKED = 4

TIER_LABELS: dict[int, str] = {
    1: "hard_trusted",
    2: "soft_trusted",
    3: "context_only",
    4: "blocked",
}

_TIER1_FAMILIES: frozenset[str] = frozenset({
    "government", "government_statistics", "central_bank",
    "international_organization", "regulatory_body", "company_filing",
    "official_statistic", "census", "national_health_authority",
})

_TIER2_FAMILIES: frozenset[str] = frozenset({
    "analyst_report", "market_research", "industry_survey",
    "trade_association", "ngo_report", "benchmark_report",
    "professional_survey", "clinical_study", "conference_proceeding",
})

_TIER3_FAMILIES: frozenset[str] = frozenset({
    "vendor_documentation", "product_documentation", "company_blog",
    "industry_news", "approved_press", "trade_press", "financial_news",
    "academic_preprint", "thesis", "technical_whitepaper",
})

_ACADEMIC_FAMILIES: frozenset[str] = frozenset({
    "academic_research", "peer_reviewed_journal", "research_paper", "academic",
})

_TIER4_FAMILIES: frozenset[str] = frozenset({
    "public_web", "scraped_html", "seo_content",
    "news_aggregator", "unknown", "synthetic_model",
    "financial_model_bank", "route_only",
})

_QUALITATIVE_CONTEXT_FAMILIES: frozenset[str] = frozenset({
    "social_media", "forum", "reddit",
})

_PEER_REVIEWED_HOST_TOKENS: frozenset[str] = frozenset({
    "pubmed", "ncbi.nlm.nih.gov", "doi.org", "jstor.org", "springer.com",
    "elsevier.com", "wiley.com", "nature.com", "science.org", "bmj.com",
    "thelancet.com", "jamanetwork.com", "tandfonline.com", "sage", "oxford",
    "cambridge", "ieee.org", "acm.org", "ssrn.com",
})

_PREPRINT_HOST_TOKENS: frozenset[str] = frozenset({
    "arxiv.org", "biorxiv.org", "medrxiv.org",
    "researchgate.net", "academia.edu", "preprint",
})

_BLOCKED_SUBJECT_TOKENS: frozenset[str] = frozenset({
    "fluid dynamics", "navier-stokes", "turbulence", "aerodynamics",
    "thermodynamics", "quantum field", "quantum mechanics", "particle physics",
    "astrophysics", "cosmology", "nuclear physics", "crystallography",
    "polymer physics", "celestial mechanics", "hydrology", "geomorphology",
    "seismology", "geophysics", "topology", "number theory",
    "differential geometry", "abstract algebra", "combinatorics",
    "mathematical logic", "pure mathematics",
})

_MARKET_RELEVANT_SUBJECT_TOKENS: frozenset[str] = frozenset({
    "market", "economics", "economy", "gdp", "industry", "healthcare",
    "digital health", "health informatics", "telemedicine", "e-health",
    "fintech", "financial technology", "banking", "insurance", "supply chain",
    "logistics", "retail", "e-commerce", "saas", "software adoption",
    "enterprise software", "artificial intelligence", "machine learning",
    "adoption", "technology adoption", "consumer behavior", "willingness to pay",
    "price elasticity", "market sizing", "tam", "sam", "som",
    "operations research", "decision sciences", "industrial engineering",
    "optimization", "management science",
})

_ACADEMIC_DEFAULT_MAX_AGE_YEARS = 8
_CURRENT_YEAR = 2026


def _text_for_record(record: dict[str, Any]) -> str:
    parts = [
        record.get("title", ""),
        record.get("abstract", ""),
        record.get("description", ""),
        record.get("metric_name", ""),
        record.get("source", ""),
        record.get("tags", ""),
    ]
    if isinstance(parts[-1], list):
        parts[-1] = " ".join(parts[-1])
    return " ".join(str(p) for p in parts if p).lower()


def _host_for_record(record: dict[str, Any]) -> str:
    url = record.get("url") or record.get("source_url") or ""
    return str(url).lower()


def _record_year(record: dict[str, Any]) -> int | None:
    raw = record.get("year") or record.get("publication_year") or record.get("data_year")
    if raw is None:
        return None
    try:
        return int(str(raw)[:4])
    except (ValueError, TypeError):
        return None


def _source_family(record: dict[str, Any]) -> str:
    return str(
        record.get("source_family")
        or record.get("source_type")
        or record.get("family")
        or "unknown"
    ).lower()


def classify_academic_subject(record: dict[str, Any]) -> str:
    """Return ontology bucket: market_economics | healthcare_clinical |
    industry_engineering | pure_science | blocked | unknown"""
    text = _text_for_record(record)
    subject_tags = record.get("subject_tags") or record.get("disciplines") or []
    if isinstance(subject_tags, str):
        subject_tags = [subject_tags]
    combined = text + " " + " ".join(str(t) for t in subject_tags).lower()

    hard_science_score = academic_hard_science_score(record)
    market_relevance_score = academic_market_relevance_score(record)

    if hard_science_score >= 0.50 and market_relevance_score < 0.45:
        return "blocked"

    if market_relevance_score >= 0.45:
        if any(t in combined for t in (
            "healthcare", "clinical", "health", "medical", "pharma", "patient"
        )):
            return "healthcare_clinical"
        if any(t in combined for t in (
            "economics", "gdp", "market", "fintech", "saas",
            "e-commerce", "supply chain", "tam", "sam",
        )):
            return "market_economics"
        return "industry_engineering"

    if market_relevance_score >= 0.25 and hard_science_score < 0.50:
        return "industry_engineering"

    return "unknown"


def academic_hard_science_score(record: dict[str, Any]) -> float:
    """Weighted hard-science score for academic records."""
    text = _text_for_record(record)
    hits = sum(1 for token in _BLOCKED_SUBJECT_TOKENS if token in text)
    return round(min(hits * 0.25, 1.0), 3)


def academic_market_relevance_score(record: dict[str, Any]) -> float:
    """Weighted market/industry relevance score for academic records."""
    text = _text_for_record(record)
    hits = sum(1 for token in _MARKET_RELEVANT_SUBJECT_TOKENS if token in text)
    return round(min(hits * 0.10, 1.0), 3)


def _is_peer_reviewed(record: dict[str, Any]) -> bool:
    explicit = record.get("peer_reviewed")
    if explicit is not None:
        return bool(explicit)

    work_type = str(record.get("work_type") or record.get("publication_type") or "").lower()
    if work_type in ("journal-article", "journal_article", "article"):
        return True
    if "preprint" in work_type or "thesis" in work_type:
        return False

    host = _host_for_record(record)
    for token in _PEER_REVIEWED_HOST_TOKENS:
        if token in host:
            return True
    for token in _PREPRINT_HOST_TOKENS:
        if token in host:
            return False

    return False


def _academic_market_relevance_prior(record: dict[str, Any]) -> float:
    subject_class = classify_academic_subject(record)
    market_score = academic_market_relevance_score(record)
    hard_science_score = academic_hard_science_score(record)

    if subject_class == "blocked":
        return 0.05

    base = min(market_score, 0.70)

    if subject_class in ("market_economics", "healthcare_clinical"):
        base = min(base + 0.20, 0.90)
    elif subject_class == "industry_engineering":
        base = min(base + 0.10, 0.80)

    if hard_science_score >= 0.50:
        base *= 0.60

    return round(base, 3)


def classify_academic_tier(
    record: dict[str, Any],
    *,
    max_age_years: int = _ACADEMIC_DEFAULT_MAX_AGE_YEARS,
    market_relevance_floor: float = 0.55,
) -> tuple[int, str]:
    """Resolve Tier 1/3/4 for academic records. All four gates must pass for Tier 1."""
    subject_class = classify_academic_subject(record)
    if subject_class == "blocked":
        return TIER_BLOCKED, "academic_blocked_subject"

    peer_reviewed = _is_peer_reviewed(record)
    if not peer_reviewed:
        family = _source_family(record)
        if family in ("academic_preprint", "thesis"):
            return TIER_BLOCKED, "academic_preprint_not_peer_reviewed"
        return TIER_CONTEXT_ONLY, "academic_not_peer_reviewed"

    year = _record_year(record)
    min_year = _CURRENT_YEAR - max_age_years
    if year is not None and year < min_year:
        return TIER_CONTEXT_ONLY, f"academic_stale_year_{year}"

    relevance = _academic_market_relevance_prior(record)
    if relevance < market_relevance_floor:
        return TIER_CONTEXT_ONLY, f"academic_low_market_relevance_{relevance:.2f}"

    if subject_class == "unknown":
        return TIER_CONTEXT_ONLY, "academic_unknown_subject"

    return TIER_HARD_TRUSTED, "academic_peer_reviewed_market_relevant"


def classify_source_trust_tier(record: dict[str, Any]) -> dict[str, Any]:
    """Classify a record source trust tier. Returns tier, label, reason, and flags."""
    family = _source_family(record)

    if family in _ACADEMIC_FAMILIES:
        tier, reason = classify_academic_tier(record)
        subject_class = classify_academic_subject(record)
        peer_reviewed = _is_peer_reviewed(record)
        relevance = _academic_market_relevance_prior(record)
        return {
            "trust_tier": tier,
            "trust_tier_label": TIER_LABELS[tier],
            "trust_tier_reason": reason,
            "academic_subject_class": subject_class,
            "academic_peer_reviewed": peer_reviewed,
            "academic_relevance_prior": relevance,
            "allows_investor_retrieval": tier <= TIER_SOFT_TRUSTED,
            "allows_hard_numeric": tier == TIER_HARD_TRUSTED,
        }

    if family in _TIER1_FAMILIES:
        tier, reason = TIER_HARD_TRUSTED, f"tier1_family_{family}"
    elif family in _TIER2_FAMILIES:
        tier, reason = TIER_SOFT_TRUSTED, f"tier2_family_{family}"
    elif family in _TIER3_FAMILIES:
        tier, reason = TIER_CONTEXT_ONLY, f"tier3_family_{family}"
    elif family in _QUALITATIVE_CONTEXT_FAMILIES:
        tier, reason = TIER_CONTEXT_ONLY, f"tier3_qualitative_context_family_{family}"
    elif family in _TIER4_FAMILIES:
        tier, reason = TIER_BLOCKED, f"tier4_family_{family}"
    else:
        tier, reason = TIER_BLOCKED, f"tier4_unknown_family_{family}"

    return {
        "trust_tier": tier,
        "trust_tier_label": TIER_LABELS[tier],
        "trust_tier_reason": reason,
        "academic_subject_class": None,
        "academic_peer_reviewed": None,
        "academic_relevance_prior": None,
        "allows_investor_retrieval": tier <= TIER_SOFT_TRUSTED,
        "allows_hard_numeric": tier == TIER_HARD_TRUSTED,
    }


def source_trust_tier(record: dict[str, Any]) -> int:
    """Return integer trust tier for a record."""
    return classify_source_trust_tier(record)["trust_tier"]