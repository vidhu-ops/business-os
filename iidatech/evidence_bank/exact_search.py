"""Domain-aware exact search query builder — delegates to industry retrieval planner."""

from __future__ import annotations

import re
from typing import Any

from iidatech.retrieval.industry_planner import build_industry_queries, resolve_retrieval_profile_key

SOURCE_TRUST_BY_PATTERN = (
    (re.compile(r"site:.*pricing|/pricing", re.I), 0.95, "official_pricing"),
    (re.compile(r"g2\.com|capterra|getapp|softwareadvice", re.I), 0.85, "review_platform"),
    (re.compile(r"reddit\.com", re.I), 0.55, "reddit_practitioner"),
    (re.compile(r"filetype:pdf.*benchmark|benchmark report", re.I), 0.80, "analyst_report"),
)


def build_exact_queries(topic: str, domain: str, *, target: str = "", industry: str = "") -> dict[str, list[str]]:
    """Build domain-specific query families — no cross-domain CRM pricing leakage."""
    plan = build_industry_queries(topic, domain, target or "", industry=industry)
    profile_key = resolve_retrieval_profile_key(domain, topic, industry)
    return {
        "profile_id": plan.get("profile_id", profile_key),
        "pricing_queries": list(plan.get("pricing_queries") or []),
        "competitor_queries": list(plan.get("competitor_queries") or []),
        "complaint_queries": list(plan.get("buyer_queries") or []),
        "benchmark_queries": list(plan.get("regulation_queries") or []),
    }


def _trust_for_url(url: str, query: str) -> tuple[float, str]:
    blob = f"{url} {query}".lower()
    for pattern, trust, label in SOURCE_TRUST_BY_PATTERN:
        if pattern.search(blob):
            return trust, label
    if "pricing" in blob:
        return 0.92, "pricing_page"
    return 0.70, "exact_search"


def run_exact_search_layer(*, topic: str, industry: str, target: str, domain: str, limit: int = 6) -> dict[str, Any]:
    """Tavily/Exa exact search removed from research pipeline — use Perplexity Sonar instead."""
    families = build_exact_queries(topic, domain, target=target, industry=industry)
    flat_queries: list[str] = []
    for key in ("pricing_queries", "competitor_queries", "complaint_queries", "benchmark_queries"):
        flat_queries.extend(families.get(key, []))
    return {
        "records": [],
        "queries": flat_queries,
        "hit_count": 0,
        "query_families": families,
        "disabled": True,
        "reason": "exact_search_removed_use_perplexity",
    }