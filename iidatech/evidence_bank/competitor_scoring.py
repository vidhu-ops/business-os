"""Competitor quality scoring and ranking for IIDATECH evidence bank."""
from __future__ import annotations

import re
from typing import Any

CATEGORY_BANDS = (
    (0.82, "leader"),
    (0.68, "strong challenger"),
    (0.52, "mid-market"),
    (0.38, "niche"),
    (0.0, "weak"),
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def score_competitor_strength(row: dict[str, Any]) -> dict[str, Any]:
    metrics = row.get("metrics") or {}
    trust = _safe_float(row.get("trust_score"), 0.7)
    mention_freq = _safe_float(metrics.get("mention_frequency") or row.get("mention_frequency"), 0)
    review_count = _safe_float(metrics.get("review_count") or metrics.get("g2_reviews"), 0)
    g2_rating = _safe_float(metrics.get("g2_rating"), 0)
    funding = str(metrics.get("funding") or metrics.get("funding_usd") or "").lower()
    urls = row.get("source_urls") or []
    domain_authority = _domain_authority_proxy(urls)

    funding_score = 0.35
    if "billion" in funding or "unicorn" in funding:
        funding_score = 0.95
    elif "million" in funding or re.search(r"\$\d+m", funding):
        funding_score = 0.72
    elif metrics.get("public") or metrics.get("ipo"):
        funding_score = 0.88

    search_proxy = min(1.0, mention_freq / 5.0) if mention_freq else 0.25
    review_score = min(1.0, review_count / 500.0) * 0.7 + (g2_rating / 5.0) * 0.3 if review_count or g2_rating else 0.2
    manual_boost = 0.12 if not row.get("provisional") else 0.0
    official_boost = 0.08 if row.get("source_type") == "official_pricing_page" else 0.0

    composite = (
        funding_score * 0.22
        + search_proxy * 0.18
        + review_score * 0.20
        + domain_authority * 0.15
        + trust * 0.15
        + manual_boost
        + official_boost
    )
    composite = max(0.0, min(1.0, composite))
    category = _band_label(composite)
    return {
        "company_name": row.get("company_name"),
        "strength_score": round(composite, 4),
        "category_band": category,
        "components": {
            "funding_score": round(funding_score, 3),
            "search_proxy": round(search_proxy, 3),
            "review_score": round(review_score, 3),
            "domain_authority": round(domain_authority, 3),
            "trust": round(trust, 3),
        },
    }


def _domain_authority_proxy(urls: list[Any]) -> float:
    if not urls:
        return 0.25
    score = 0.35
    for url in urls:
        u = str(url).lower()
        if any(x in u for x in ("g2.com", "capterra.com", "forbes.com", "crunchbase.com")):
            score = max(score, 0.75)
        elif re.search(r"https?://[^/]+\.(com|io|co)/", u):
            score = max(score, 0.55)
    return min(score, 0.9)


def _band_label(score: float) -> str:
    for threshold, label in CATEGORY_BANDS:
        if score >= threshold:
            return label
    return "weak"


def build_competitor_rankings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    scored = []
    for row in rows:
        s = score_competitor_strength(row)
        merged = {**row, **s}
        scored.append(merged)
    scored.sort(key=lambda r: (-float(r.get("strength_score") or 0), str(r.get("company_name", ""))))
    for idx, row in enumerate(scored, start=1):
        row["rank"] = idx
    return scored