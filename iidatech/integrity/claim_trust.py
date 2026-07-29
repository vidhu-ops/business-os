"""Claim-level trust scoring for IIDATECH (PR1-A/PR1-B).

Separates source-level trust from claim-level trust and applies extraction
confidence. Reddit, forums, and social media are qualitative context only:
numeric claims from those sources receive zero claim trust.

All functions are pure. No Streamlit. No app.py imports. No side effects.
"""
from __future__ import annotations

import re
from typing import Any

CLAIM_CLASS_AUDITED_FINANCIAL = "audited_financial"
CLAIM_CLASS_GOVERNMENT_STAT = "government_stat"
CLAIM_CLASS_REGULATORY_FACT = "regulatory_fact"
CLAIM_CLASS_SURVEY_ESTIMATE = "survey_estimate"
CLAIM_CLASS_ANALYST_ESTIMATE = "analyst_estimate"
CLAIM_CLASS_MARKETING_TAM = "marketing_tam"
CLAIM_CLASS_PROMOTIONAL = "promotional_claim"
CLAIM_CLASS_SYNTHETIC = "synthetic_model_output"
CLAIM_CLASS_UNKNOWN = "unknown"

_CLAIM_CLASS_BASE_TRUST: dict[str, float] = {
    CLAIM_CLASS_AUDITED_FINANCIAL: 0.95,
    CLAIM_CLASS_GOVERNMENT_STAT: 0.92,
    CLAIM_CLASS_REGULATORY_FACT: 0.88,
    CLAIM_CLASS_SURVEY_ESTIMATE: 0.65,
    CLAIM_CLASS_ANALYST_ESTIMATE: 0.62,
    CLAIM_CLASS_MARKETING_TAM: 0.38,
    CLAIM_CLASS_PROMOTIONAL: 0.22,
    CLAIM_CLASS_SYNTHETIC: 0.00,
    CLAIM_CLASS_UNKNOWN: 0.40,
}

CLAIM_TRUST_FLOOR_HARD_NUMERIC = 0.75
CLAIM_TRUST_FLOOR_CITATION_LEDGER = 0.70
CLAIM_TRUST_FLOOR_MARKET_CONTEXT = 0.50
CLAIM_TRUST_FLOOR_PRODUCT_CONTEXT = 0.40

_QUALITATIVE_CONTEXT_ONLY_FAMILIES: frozenset[str] = frozenset({
    "social_media",
    "forum",
    "reddit",
})

_AUDITED_TOKENS: frozenset[str] = frozenset({
    "audited", "annual report", "10-k", "10k", "sec filing", "form 10",
    "gaap", "ifrs", "financial statement", "balance sheet", "income statement",
    "cash flow", "revenue", "net income", "operating income", "earnings",
    "eps", "ebitda",
})

_GOVERNMENT_STAT_TOKENS: frozenset[str] = frozenset({
    "census", "bureau of statistics", "national statistics", "government data",
    "ministry", "federal reserve", "central bank", "gdp", "cpi", "inflation",
    "employment rate", "unemployment", "population", "world bank", "imf",
    "oecd", "united nations", "who", "world health organization", "eurostat",
    "mospi", "nsso", "rbi", "sebi",
})

_REGULATORY_TOKENS: frozenset[str] = frozenset({
    "regulation", "compliance", "mandate", "requirement", "law", "act",
    "directive", "license", "licensing", "approval", "fda", "ema",
    "cdsco", "hipaa", "gdpr", "dpdp",
})

_SURVEY_TOKENS: frozenset[str] = frozenset({
    "survey", "poll", "respondents", "sample size", "n=", "questionnaire", "interview",
})

_ANALYST_TOKENS: frozenset[str] = frozenset({
    "forecast", "projection", "cagr", "analyst", "gartner", "idc", "mckinsey",
    "bain", "deloitte", "pwc", "kpmg", "ey", "frost", "ihs markit", "mordor",
    "grand view", "marketsandmarkets", "statista", "bloomberg", "technavio",
})

_MARKETING_TAM_TOKENS: frozenset[str] = frozenset({
    "total addressable market", "tam", "sam", "som", "our tam", "company tam",
    "investor presentation", "pitch deck", "deck", "slide",
    "opportunity size", "market opportunity",
})

_PROMOTIONAL_TOKENS: frozenset[str] = frozenset({
    "market leader", "fastest growing", "industry leading", "#1", "number one",
    "best in class", "world class", "disrupting", "revolutionary",
    "game changer", "transformative",
})

_RANGE_RE = re.compile(r"\b\d+[\.,]?\d*\s*(?:-|to)\s*\d+[\.,]?\d*\b", re.IGNORECASE)
_NUMBER_RE = re.compile(r"\d")

_APPROXIMATE_PHRASES: tuple[str, ...] = (
    "about", "around", "approximately", "roughly", "nearly", "almost", "over",
    "more than", "less than", "at least", "estimated", "estimate",
    "estimated at", "estimated to be", "roughly estimated",
    "approximately equal", "in the range", "in the vicinity",
)

_SPECULATIVE_PHRASES: tuple[str, ...] = (
    " may ", " might ", " could ", " would ", " should reach",
    " expected to", " projected to", " anticipated to",
    " forecast to", " likely to", " potentially",
)

_PROMOTIONAL_PHRASES: tuple[str, ...] = (
    "up to", "as much as", "as high as", "up to $",
    "as little as", "starting from", "from just",
)

_OCR_RES = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b[0O][0O]\b",
        r"\bl[1I]\b",
        r"\bS\$",
        r"\b\d+[lI]\b",
    )
]


def _text_for_record(record: dict[str, Any]) -> str:
    parts = [
        record.get("title", ""),
        record.get("metric_name", ""),
        record.get("description", ""),
        record.get("source", ""),
        record.get("tags", ""),
        record.get("section_context", ""),
    ]
    if isinstance(parts[-1], list):
        parts[-1] = " ".join(parts[-1])
    return " ".join(str(p) for p in parts if p).lower()


def _text_for_claim(claim_context: dict[str, Any] | None) -> str:
    if not claim_context:
        return ""
    parts = [
        claim_context.get("claim_text", ""),
        claim_context.get("metric_name", ""),
        claim_context.get("section_title", ""),
        claim_context.get("excerpt", ""),
    ]
    return " ".join(str(p) for p in parts if p).lower()


def _source_family(record: dict[str, Any]) -> str:
    return str(
        record.get("source_family")
        or record.get("source_type")
        or record.get("family")
        or ""
    ).lower()


def classify_claim_class(
    record: dict[str, Any],
    claim_context: dict[str, Any] | None = None,
) -> str:
    """Return the claim class string for a record and optional claim context."""
    family = _source_family(record)
    if family in ("synthetic_model", "financial_model_bank"):
        return CLAIM_CLASS_SYNTHETIC

    combined = _text_for_record(record) + " " + _text_for_claim(claim_context)

    for token in _AUDITED_TOKENS:
        if token in combined:
            return CLAIM_CLASS_AUDITED_FINANCIAL
    for token in _GOVERNMENT_STAT_TOKENS:
        if token in combined:
            return CLAIM_CLASS_GOVERNMENT_STAT
    for token in _REGULATORY_TOKENS:
        if token in combined:
            return CLAIM_CLASS_REGULATORY_FACT
    for token in _SURVEY_TOKENS:
        if token in combined:
            return CLAIM_CLASS_SURVEY_ESTIMATE
    for token in _ANALYST_TOKENS:
        if token in combined:
            return CLAIM_CLASS_ANALYST_ESTIMATE
    for token in _PROMOTIONAL_TOKENS:
        if token in combined:
            return CLAIM_CLASS_PROMOTIONAL
    for token in _MARKETING_TAM_TOKENS:
        if token in combined:
            return CLAIM_CLASS_MARKETING_TAM

    return CLAIM_CLASS_UNKNOWN


def compute_extraction_confidence(
    record: dict[str, Any],
    claim_context: dict[str, Any] | None = None,
) -> float:
    """Return extraction confidence multiplier [0.0, 1.0]."""
    combined = _text_for_record(record) + " " + _text_for_claim(claim_context)
    confidence = 1.0

    if _RANGE_RE.search(combined):
        confidence *= 0.75

    approx_hits = sum(1 for phrase in _APPROXIMATE_PHRASES if phrase in combined)
    if approx_hits >= 2:
        confidence *= 0.70
    elif approx_hits == 1:
        confidence *= 0.82

    spec_hits = sum(1 for phrase in _SPECULATIVE_PHRASES if phrase in combined)
    if spec_hits >= 2:
        confidence *= 0.60
    elif spec_hits == 1:
        confidence *= 0.72

    promo_hits = sum(1 for phrase in _PROMOTIONAL_PHRASES if phrase in combined)
    if promo_hits >= 1:
        confidence *= 0.55

    ocr_hits = sum(1 for pattern in _OCR_RES if pattern.search(combined))
    if ocr_hits >= 2:
        confidence *= 0.55
    elif ocr_hits == 1:
        confidence *= 0.72

    family = _source_family(record)
    if family in ("public_web", "scraped_html", "seo_content"):
        confidence *= 0.65
    elif family in _QUALITATIVE_CONTEXT_ONLY_FAMILIES:
        confidence *= 0.45

    return round(max(confidence, 0.05), 3)


def _has_numeric_claim_text(record: dict[str, Any], claim_context: dict[str, Any] | None) -> bool:
    combined = _text_for_record(record) + " " + _text_for_claim(claim_context)
    return bool(_NUMBER_RE.search(combined))


def claim_trust_score(
    record: dict[str, Any],
    claim_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute final claim trust for a record and optional claim context."""
    claim_class = classify_claim_class(record, claim_context)
    base = _CLAIM_CLASS_BASE_TRUST[claim_class]
    extraction_conf = compute_extraction_confidence(record, claim_context)
    final = round(base * extraction_conf, 3)

    numeric_rejected = (
        _source_family(record) in _QUALITATIVE_CONTEXT_ONLY_FAMILIES
        and _has_numeric_claim_text(record, claim_context)
    )
    if numeric_rejected:
        final = 0.0

    return {
        "claim_class": claim_class,
        "base_claim_trust": base,
        "extraction_confidence": extraction_conf,
        "final_claim_trust": final,
        "eligible_hard_numeric": final >= CLAIM_TRUST_FLOOR_HARD_NUMERIC,
        "eligible_citation_ledger": final >= CLAIM_TRUST_FLOOR_CITATION_LEDGER,
        "eligible_market_context": final >= CLAIM_TRUST_FLOOR_MARKET_CONTEXT,
        "numeric_claim_rejected": numeric_rejected,
    }
