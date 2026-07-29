"""Strict source tier enforcement for IIDATECH evidence claims."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

TIER_OFFICIAL = 1
TIER_ANALYST_REVIEW = 2
TIER_CONTEXT = 3

_TIER1_HOSTS = (
    "sec.gov", "edgar", "investor.", "ir.", "annual-report", "gov.in", "gov.uk",
    "mospi.gov", "rbi.org", "census.gov", "europa.eu", "worldbank.org",
)
_TIER1_FAMILIES = frozenset({
    "government_data", "official_company_registry", "company_filings", "official_financial_data",
    "official_pricing_page", "official_site", "procurement_data", "competitor_intelligence",
    "benchmark_bank", "curated_seed_bank",
})
_TIER2_FAMILIES = frozenset({
    "analyst_report", "review_platform", "g2", "capterra", "trustradius", "statista_public_metadata",
})
_TIER3_FAMILIES = frozenset({
    "reddit_practitioner", "youtube_transcript", "magazine_article", "blog", "serp_organic",
    "exact_search", "local_operator_listing", "pricing_reference",
})

FINANCIAL_CLAIM_TYPES = frozenset({
    "pricing", "tam", "sam", "som", "unit_economics", "financial", "cac", "ltv", "margin", "revenue",
})


def classify_source_tier(record: dict[str, Any]) -> int:
    family = str(record.get("source_family") or record.get("source_type") or "").lower()
    url = str(
        record.get("url")
        or (record.get("source_urls") or [""])[0] if isinstance(record.get("source_urls"), list) else ""
    ).lower()
    host = urlparse(url).netloc.lower() if url.startswith("http") else url
    if family in _TIER1_FAMILIES or any(h in host or h in url for h in _TIER1_HOSTS):
        return TIER_OFFICIAL
    if family in _TIER2_FAMILIES or any(x in host for x in ("g2.com", "capterra.com", "gartner.com", "forrester.com")):
        return TIER_ANALYST_REVIEW
    if family in _TIER3_FAMILIES or record.get("provisional") or record.get("discovered_via") == "serpapi":
        return TIER_CONTEXT
    if "pricing" in url and family not in _TIER3_FAMILIES:
        return TIER_OFFICIAL
    return TIER_ANALYST_REVIEW if family else TIER_CONTEXT


def tier_allows_claim(tier: int, claim_type: str) -> bool:
    claim = (claim_type or "").lower()
    if tier == TIER_OFFICIAL:
        return True
    if tier == TIER_ANALYST_REVIEW:
        return claim not in {"unit_economics", "tam", "sam", "som"}
    if tier == TIER_CONTEXT:
        return claim not in FINANCIAL_CLAIM_TYPES
    return False


def validate_record_for_claim(record: dict[str, Any], claim_type: str) -> dict[str, Any]:
    tier = classify_source_tier(record)
    allowed = tier_allows_claim(tier, claim_type)
    return {
        "tier": tier,
        "claim_type": claim_type,
        "allowed": allowed,
        "reason": "" if allowed else f"tier_{tier}_cannot_support_{claim_type}",
        "url": record.get("url") or "",
        "source_family": record.get("source_family") or record.get("source_type"),
    }


def filter_records_for_claim(records: list[dict[str, Any]], claim_type: str) -> tuple[list[dict], list[dict]]:
    accepted, rejected = [], []
    for row in records:
        if not isinstance(row, dict):
            continue
        v = validate_record_for_claim(row, claim_type)
        if v["allowed"]:
            accepted.append(row)
        else:
            rejected.append({**row, "_tier_rejection": v["reason"]})
    return accepted, rejected


def audit_citation_ledger(ledger: list[dict[str, Any]]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    for row in ledger:
        if not isinstance(row, dict):
            continue
        claim = str(row.get("claim_type") or "general").lower()
        if claim in FINANCIAL_CLAIM_TYPES:
            v = validate_record_for_claim(row, claim)
            if not v["allowed"]:
                violations.append(v)
    return {"violation_count": len(violations), "violations": violations[:20]}