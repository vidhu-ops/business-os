"""Verified-source policy for Understand your market.

The evidence bank can be large while report quality drops if Perplexity section
generation still searches the open web (YouTube, Reddit, blogs). This module
centralises blocked hosts and trusted-domain allowlists used to filter bank
rows, fact packs, citations, and Perplexity search_domain_filter.
"""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from iidatech.evidence_bank.report_postprocess import is_refusal_text

# Social, forum, video, and generic UGC — never funding-grade primary evidence.
BLOCKED_HOST_FRAGMENTS: tuple[str, ...] = (
    "youtube.com",
    "youtu.be",
    "reddit.com",
    "redd.it",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "quora.com",
    "pinterest.com",
    "medium.com",
    "substack.com",
    "vimeo.com",
    "twitch.tv",
    "discord.com",
    "discord.gg",
    "linkedin.com/posts",
    "blogspot.com",
    "wordpress.com",
    "wikipedia.org",
    "fandom.com",
    "stackexchange.com",
    "stackoverflow.com/questions",  # Q&A threads, not the annual survey
)

_VERIFIED_STATUSES: frozenset[str] = frozenset({
    "official_statistics",
    "trusted_publisher",
    "firecrawl_verified",
    "pricing_discrepancy",
    "directional_source",  # tier-3 triangulation only; excluded from fact pack
})


def host_of(url: str) -> str:
    try:
        host = (urlparse(str(url or "").strip()).netloc or "").lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""


def is_blocked_source_url(url: str) -> bool:
    """True for YouTube, Reddit, social, forums, and generic UGC hosts."""
    raw = str(url or "").strip().lower()
    if not raw:
        return False
    host = host_of(raw)
    path = raw.split(host, 1)[-1] if host and host in raw else raw
    blob = f"{host}{path}"
    return any(frag in blob for frag in BLOCKED_HOST_FRAGMENTS)


def filter_blocked_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        u = str(url or "").strip()
        if not u or u in seen or is_blocked_source_url(u):
            continue
        seen.add(u)
        out.append(u)
    return out


def all_trusted_domains(*, max_domains: int = 20) -> list[str]:
    """Flatten trusted registry domains for Perplexity search_domain_filter."""
    try:
        from iidatech.evidence_bank.trusted_sources import TRUSTED_SOURCE_REGISTRY
    except ImportError:
        return []
    seen: list[str] = []
    for spec in TRUSTED_SOURCE_REGISTRY.values():
        for dom in spec.get("domains") or []:
            d = str(dom).strip().lower()
            if d and d not in seen:
                seen.append(d)
            if len(seen) >= max_domains:
                return seen
    return seen


def url_on_trusted_registry(url: str) -> bool:
    try:
        from iidatech.evidence_bank.trusted_sources import TRUSTED_SOURCE_REGISTRY, _url_in_registry
    except ImportError:
        return False
    domains = [d for spec in TRUSTED_SOURCE_REGISTRY.values() for d in (spec.get("domains") or [])]
    return _url_in_registry(url, domains)


def is_verified_bank_row(row: dict[str, Any]) -> bool:
    """Row admissible as verified evidence in fact pack / appendix."""
    if str(row.get("tier") or "") != "tier1_verified":
        return False
    value = str(
        row.get("metric_value") or row.get("verified_price") or row.get("reported_price") or ""
    )
    if is_refusal_text(value) or is_refusal_text(str(row.get("name") or "")):
        return False
    metric = str(row.get("metric_name") or "")
    if metric == "source_reference" and (not value or len(value) < 12 or is_refusal_text(value)):
        return False
    status = str(row.get("verification_status") or "").strip().lower()
    if status in {"perplexity_live", "perplexity_reported"}:
        return False
    url = str(row.get("url") or "")
    if url and is_blocked_source_url(url):
        return False
    if status in _VERIFIED_STATUSES:
        return status != "directional_source"
    # Firecrawl-scraped competitor pricing rows
    if row.get("verified_price") and status in {"", "firecrawl_verified", "pricing_discrepancy"}:
        return True
    if url and url_on_trusted_registry(url):
        return True
    return bool(row.get("record_type") == "official_statistics_api")


def verified_bank_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [r for r in rows if isinstance(r, dict) and is_verified_bank_row(r)]


def sanitize_section(section: dict[str, Any]) -> dict[str, Any]:
    """Drop blocked or truncated URLs from section citations."""
    try:
        from iidatech.evidence_bank.report_postprocess import filter_valid_urls
    except ImportError:
        filter_valid_urls = lambda urls: urls  # type: ignore
    out = dict(section)
    out["sources"] = filter_blocked_urls(filter_valid_urls([str(u) for u in (section.get("sources") or [])]))
    return out
