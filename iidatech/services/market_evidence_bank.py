"""Tiered evidence bank for Understand your market.

Tier 1 = official APIs and trusted-publisher rows harvested via Perplexity
domain-restricted search plus direct data sources (World Bank, FRED, etc.).
Perplexity narrative in the report draft is separate from this bank.
"""
from __future__ import annotations

import os
import re
from typing import Any

TIER_VERIFIED = "tier1_verified"
TIER_REPORTED = "tier2_reported"

_PRICE_TOKEN = re.compile(
    r"(?:USD|INR|EUR|GBP|Rs\.?|[$\u20b9\u20ac\u00a3])\s?\d[\d,]*(?:\.\d+)?(?:\s?(?:-|to)\s?(?:USD|INR|Rs\.?|[$\u20b9])?\s?\d[\d,]*(?:\.\d+)?)?(?:\s?(?:per|/)\s?(?:month|mo|user|seat|year|yr|annum))?",
    re.IGNORECASE,
)


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _secret(*names: str) -> str:
    try:
        from on_demand_research import local_secret_value

        val = local_secret_value(*names)
        if val:
            return str(val)
    except Exception:
        pass
    for name in names:
        val = str(os.getenv(name) or "").strip()
        if val:
            return val
    return ""


def _route_domain_safe(topic: str, industry: str, geography: str) -> str:
    try:
        from iidatech.routing.domain_router import route_domain

        return str(route_domain(topic, industry, geography).get("selected_domain") or "")
    except Exception:
        return ""


def _row_tier(row: dict[str, Any]) -> str:
    status = str(row.get("verification_status") or "").strip().lower()
    if status in {"firecrawl_verified", "pricing_discrepancy"}:
        return TIER_VERIFIED
    if row.get("firecrawl_pricing") or row.get("pricing_page_url"):
        return TIER_VERIFIED
    return TIER_REPORTED


def _verified_price(row: dict[str, Any]) -> str:
    """Tier-1 price for a row: scraped value wins over Perplexity's claim."""
    fc = str(row.get("firecrawl_pricing") or "").strip()
    if fc:
        return fc
    if _row_tier(row) == TIER_VERIFIED:
        return str(row.get("price") or row.get("pricing") or "").strip()
    return ""


def _trusted_rows_to_bank_rows(harvest: dict[str, Any]) -> list[dict[str, Any]]:
    """Map trusted-publisher harvest rows into bank rows (always Tier 1)."""
    out: list[dict[str, Any]] = []
    for r in _as_list(harvest.get("rows")):
        if not isinstance(r, dict) or not r.get("url"):
            continue
        metrics = _as_list(r.get("extracted_metrics"))
        source_tier = int(r.get("source_tier") or 2)
        base = {
            "name": str(r.get("name") or r.get("publisher") or "").strip()[:160],
            "record_type": str(r.get("record_type") or "trusted_source"),
            # Source-tier 1 (official) and 2 (institutional/analyst) count as
            # bank Tier 1. Source-tier 3 (directional, e.g. Crunchbase free)
            # stays Tier 2: triangulation only, never overrides a claim.
            "tier": TIER_VERIFIED if source_tier in (1, 2) else TIER_REPORTED,
            "source_tier": source_tier,
            "verified_price": "",
            "reported_price": "",
            "url": str(r.get("url")),
            "publisher": str(r.get("publisher") or ""),
            "verification_status": str(r.get("verification_status") or "trusted_publisher"),
            "pricing_discrepancy": False,
        }
        if metrics:
            for m in metrics[:3]:
                row = dict(base)
                row["metric_name"] = str(m.get("metric") or "")
                row["metric_value"] = str(m.get("value") or "")
                row["metric_context"] = str(m.get("context") or "")[:220]
                out.append(row)
        else:
            row = dict(base)
            row["metric_name"] = "source_reference"
            row["metric_value"] = str(r.get("snippet") or "")[:180]
            out.append(row)
    return out


def build_market_evidence_bank(topic: str, industry: str, geography: str) -> dict[str, Any]:
    """One merged, tiered row set gathered before report generation.

    Tier 1 comes from IIDATECH's trusted-source harvest: direct official APIs
    plus Perplexity domain-restricted publisher search. No Tavily/Firecrawl.
    """
    try:
        from iidatech.validation.competitor_evidence import is_synthetic_competitor_name
    except ImportError:
        def is_synthetic_competitor_name(_n: Any) -> bool:  # type: ignore[misc]
            return False

    domain = _route_domain_safe(topic, industry, geography)

    trusted_harvest: dict[str, Any] = {"rows": [], "gaps": [], "diagnostics": []}
    try:
        from iidatech.evidence_bank.trusted_sources import harvest_trusted_sources

        trusted_harvest = harvest_trusted_sources(topic, industry, geography)
    except Exception as exc:
        trusted_harvest = {"rows": [], "gaps": [f"trusted-source harvest failed: {str(exc)[:160]}"], "diagnostics": []}
    rows: list[dict[str, Any]] = _trusted_rows_to_bank_rows(trusted_harvest)
    discrepancies: list[dict[str, Any]] = []
    intel: dict[str, Any] = {"enabled": False, "trace": {}}

    try:
        from iidatech.evidence_bank.source_policy import is_blocked_source_url, is_verified_bank_row
    except ImportError:
        def is_blocked_source_url(_u: str) -> bool:  # type: ignore[misc]
            return False

        def is_verified_bank_row(row: dict[str, Any]) -> bool:  # type: ignore[misc]
            return str(row.get("tier") or "") == TIER_VERIFIED

    filtered_rows: list[dict[str, Any]] = []
    for raw in rows:
        if not isinstance(raw, dict):
            continue
        name = str(raw.get("name") or "").strip()
        record_type = str(raw.get("record_type") or "").strip().lower()
        if record_type == "competitor" and is_synthetic_competitor_name(name):
            continue
        url = str(raw.get("url") or "").strip()
        if url and is_blocked_source_url(url):
            continue
        if not is_verified_bank_row(raw):
            continue
        filtered_rows.append(raw)
    rows = filtered_rows

    tier1 = [r for r in rows if r["tier"] == TIER_VERIFIED]
    tier2 = [r for r in rows if r["tier"] == TIER_REPORTED]
    trusted_rows = [
        r for r in rows
        if r.get("verification_status") in ("trusted_publisher", "official_statistics", "directional_source")
    ]
    competitors = [r for r in rows if r["record_type"] == "competitor" and r["name"]]

    gaps: list[str] = list(trusted_harvest.get("gaps") or [])
    if len(competitors) < 3:
        gaps.append(f"Only {len(competitors)} named competitors found; funding-grade needs 3+.")
    if not any(r.get("verified_price") or r.get("metric_name") in {"user_rating", "review_count"} for r in rows):
        gaps.append("No independently verified pricing or review-platform benchmarks from trusted sources.")
    if not trusted_rows:
        gaps.append("No trusted-publisher rows (Statista/analyst/government/G2-class); report leans on Perplexity draft only.")

    # Persist fetched data and merge any prior store for this topic/geography.
    store_meta: dict[str, Any] = {}
    try:
        from iidatech.evidence_bank.verified_store import load_stored_rows, merge_harvest_into_store

        store_meta = merge_harvest_into_store(
            topic,
            industry,
            geography,
            _as_list(trusted_harvest.get("rows")),
            rows,
        )
        stored = load_stored_rows(topic, industry, geography)
        if stored:
            seen_urls = {str(r.get("url") or "") + str(r.get("metric_name") or "") for r in rows}
            for s in stored:
                key = str(s.get("url") or "") + str(s.get("metric_name") or "")
                if key in seen_urls:
                    continue
                if s.get("tier") == TIER_VERIFIED or s.get("verification_status") in (
                    "official_statistics", "trusted_publisher", "firecrawl_verified",
                ):
                    rows.append(s)
                    seen_urls.add(key)
    except Exception as exc:
        store_meta = {"error": str(exc)[:160]}

    tier1 = [r for r in rows if r.get("tier") == TIER_VERIFIED]
    tier2 = [r for r in rows if r.get("tier") == TIER_REPORTED]
    trusted_rows = [
        r for r in rows
        if r.get("verification_status") in ("trusted_publisher", "official_statistics", "directional_source")
    ]
    competitors = [r for r in rows if r.get("record_type") == "competitor" and r.get("name")]

    try:
        from iidatech.evidence_bank.report_postprocess import dedupe_bank_rows

        rows, url_contradictions = dedupe_bank_rows(rows)
    except ImportError:
        url_contradictions = []

    return {
        "enabled": bool(intel.get("enabled")) or bool(trusted_rows) or bool(store_meta.get("rows_total")),
        "domain": domain,
        "rows": rows,
        "tier1_count": len(tier1),
        "tier2_count": len(tier2),
        "trusted_row_count": len(trusted_rows),
        "trusted_categories": list(trusted_harvest.get("categories_hit") or []),
        "competitor_count": len(competitors),
        "pricing_discrepancies": discrepancies,
        "secondary_sources": [],
        "gaps": gaps,
        "store": store_meta,
        "url_contradictions": url_contradictions,
        "trace": {
            "intel_trace": _as_dict(intel.get("trace")),
            "trusted_diags": _as_list(trusted_harvest.get("diagnostics")),
            "degrade_reason": str(intel.get("degrade_reason") or ""),
        },
    }


def fact_pack_for_prompt(bank: dict[str, Any], max_rows: int = 18) -> str:
    """Compact grounding block injected into every section prompt."""
    try:
        from iidatech.evidence_bank.source_policy import verified_bank_rows
    except ImportError:
        verified_bank_rows = lambda rs: [r for r in rs if r.get("tier") == TIER_VERIFIED]  # type: ignore

    rows = verified_bank_rows(_as_list(bank.get("rows")))[:max_rows]
    if not rows:
        gaps = _as_list(bank.get("gaps"))
        if not gaps:
            return ""
    lines = [
        "VERIFIED FACT PACK (pre-gathered evidence from official/trusted publishers only; treat as ground truth):",
    ]
    for r in rows:
        price = r.get("verified_price") or r.get("reported_price")
        bits = [f'name="{r["name"]}"' if r.get("name") else "", f'type={r["record_type"]}']
        if price:
            bits.append(f'price="{price}"')
        if r.get("metric_name"):
            bits.append(f'{r["metric_name"]}="{r["metric_value"]}"')
        bits.append("tier=VERIFIED")
        if r.get("url"):
            bits.append(f'source={r["url"]}')
        lines.append("- " + " ".join(b for b in bits if b))
    gaps = _as_list(bank.get("gaps"))
    if gaps:
        lines.append("KNOWN GAPS (state these honestly, do not fill with guesses): " + "; ".join(gaps))
    return "\n".join(lines)


def reconcile_sections_with_bank(
    sections: list[dict[str, Any]],
    bank: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Deterministic contradiction pass: Tier-1 verified price replaces a
    conflicting Perplexity price near the same company name in section prose
    and key_metrics. Returns (sections, corrections)."""
    try:
        from iidatech.evidence_bank.perplexity_client import _prices_differ_meaningfully
    except ImportError:
        def _prices_differ_meaningfully(a: str, b: str) -> bool:  # type: ignore[misc]
            return a.strip().lower() != b.strip().lower()

    verified = {
        r["name"].lower(): r
        for r in _as_list(bank.get("rows"))
        if r.get("tier") == TIER_VERIFIED and r.get("name") and r.get("verified_price")
    }
    corrections: list[dict[str, Any]] = []
    if not verified:
        return sections, corrections

    out: list[dict[str, Any]] = []
    for section in sections:
        body = str(section.get("body_markdown") or "")
        metrics = dict(_as_dict(section.get("key_metrics")))
        for name_lc, row in verified.items():
            v_price = row["verified_price"]
            pattern = re.compile(re.escape(row["name"]) + r"[^\n]{0,100}?(" + _PRICE_TOKEN.pattern + r")", re.IGNORECASE)
            for match in list(pattern.finditer(body)):
                found = match.group(1)
                if _prices_differ_meaningfully(found, v_price):
                    body = body.replace(found, f"{v_price} (verified)", 1)
                    corrections.append(
                        {
                            "section_id": section.get("id"),
                            "company": row["name"],
                            "replaced": found,
                            "verified": v_price,
                            "source": row.get("url", ""),
                        }
                    )
            for m_key, m_val in list(metrics.items()):
                if name_lc in str(m_key).lower() and _prices_differ_meaningfully(str(m_val), v_price):
                    metrics[m_key] = f"{v_price} (verified)"
                    corrections.append(
                        {
                            "section_id": section.get("id"),
                            "company": row["name"],
                            "replaced": str(m_val),
                            "verified": v_price,
                            "source": row.get("url", ""),
                            "field": m_key,
                        }
                    )
        updated = dict(section)
        updated["body_markdown"] = body
        updated["key_metrics"] = metrics
        out.append(updated)
    return out, corrections


# Section ids -> record types / metric keywords for post-draft enrichment.
_SECTION_EVIDENCE_HINTS: dict[int, tuple[str, ...]] = {
    1: ("official_statistics_api", "market_sizing_analyst", "gdp", "population"),
    2: ("government_statistics", "institutional_aggregators"),
    3: ("market_sizing_analyst", "official_statistics_api", "market_value", "cagr"),
    4: ("market_sizing_analyst", "official_statistics_api", "market_value"),
    6: ("government_statistics", "stats_"),
    7: ("competitor_reviews", "competitor", "filings_registries"),
    8: ("filings_registries", "competitor", "competitor_reviews"),
    10: ("government_statistics", "institutional_aggregators", "industry_"),
    11: ("government_statistics", "institutional_aggregators"),
    13: ("industry_", "institutional_aggregators", "market_sizing_analyst"),
    15: ("filings_registries", "government_statistics"),
    16: ("industry_manufacturing", "industry_retail", "government_statistics"),
    17: ("competitor", "competitor_reviews", "verified_price", "user_rating"),
    19: ("filings_registries", "startup_funding_directional"),
    21: ("market_sizing_analyst", "official_statistics_api", "cagr", "market_value"),
}


def _row_for_section(section_id: int, row: dict[str, Any]) -> bool:
    hints = _SECTION_EVIDENCE_HINTS.get(int(section_id), ())
    if not hints:
        return False
    rt = str(row.get("record_type") or "")
    mn = str(row.get("metric_name") or "").lower()
    for hint in hints:
        if hint.endswith("_") and rt.startswith(hint):
            return True
        if hint in rt or hint in mn:
            return True
    return False


def _format_bank_row_line(row: dict[str, Any]) -> str:
    name = str(row.get("name") or row.get("publisher") or "Source")
    value = (
        row.get("verified_price")
        or row.get("metric_value")
        or row.get("reported_price")
        or ""
    )
    url = str(row.get("url") or "")
    metric = str(row.get("metric_name") or "").strip()
    if metric and value:
        text = f"**{name}** — {metric}: {value}"
    elif value:
        text = f"**{name}** — {value}"
    else:
        text = f"**{name}**"
    if url:
        text += f" ([source]({url}))"
    return f"- {text}"


def enrich_sections_from_bank(
    sections: list[dict[str, Any]],
    bank: dict[str, Any],
    *,
    topic: str = "",
    industry: str = "",
    geography: str = "",
    max_rows_per_section: int = 5,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """After draft report: inject verified bank rows missing from section prose/metrics."""
    try:
        from iidatech.evidence_bank.report_postprocess import (
            filter_valid_urls,
            has_parseable_figure,
            is_refusal_text,
            is_valid_source_url,
            score_row_relevance,
        )
        from iidatech.evidence_bank.source_policy import filter_blocked_urls, verified_bank_rows
    except ImportError:
        verified_bank_rows = lambda rs: [r for r in rs if r.get("tier") == TIER_VERIFIED]  # type: ignore
        filter_blocked_urls = lambda urls: urls  # type: ignore
        is_refusal_text = lambda _t: False  # type: ignore
        is_valid_source_url = lambda _u: True  # type: ignore
        has_parseable_figure = lambda _t: False  # type: ignore
        filter_valid_urls = lambda urls: urls  # type: ignore
        score_row_relevance = lambda *a, **k: 0.0  # type: ignore

    verified = verified_bank_rows(_as_list(bank.get("rows")))
    if not verified:
        return sections, []

    enrichments: list[dict[str, Any]] = []
    out: list[dict[str, Any]] = []

    for section in sections:
        sid = int(section.get("id") or 0)
        body = str(section.get("body_markdown") or "")
        metrics = dict(_as_dict(section.get("key_metrics")))
        sources = list(section.get("sources") or [])
        body_lc = body.lower()

        candidates = [r for r in verified if _row_for_section(sid, r)]
        if sid == 1 and not candidates:
            candidates = verified[: max_rows_per_section * 2]
        candidates = sorted(
            candidates,
            key=lambda r: score_row_relevance(
                r, topic=topic, industry=industry, geography=geography, report_blob=body_lc
            ),
            reverse=True,
        )

        added_lines: list[str] = []
        for row in candidates:
            if len(added_lines) >= max_rows_per_section:
                break
            value = str(row.get("metric_value") or row.get("verified_price") or "")
            metric = str(row.get("metric_name") or "")
            url = str(row.get("url") or "")
            if is_refusal_text(value) or (metric == "source_reference" and not has_parseable_figure(value)):
                continue
            if value and value.lower() in body_lc:
                continue
            if metric and metric.lower() in body_lc and value:
                continue
            if url and not is_valid_source_url(url):
                continue
            line = _format_bank_row_line(row)
            added_lines.append(line)
            label = metric if metric and metric != "source_reference" else str(row.get("name") or "metric")[:40]
            if label and value and label not in metrics:
                metrics[label] = f"{value} (verified bank)"
            if url and url not in sources:
                sources.append(url)
            enrichments.append({
                "section_id": sid,
                "metric_name": metric,
                "metric_value": value,
                "url": url,
                "source": "verified_evidence_bank",
            })

        updated = dict(section)
        if added_lines:
            block = "\n\n### Verified evidence additions (IIDATECH evidence bank)\n" + "\n".join(added_lines)
            updated["body_markdown"] = body.rstrip() + block
        updated["key_metrics"] = metrics
        updated["sources"] = filter_blocked_urls(filter_valid_urls([str(u) for u in sources if str(u).strip()]))[:12]
        out.append(updated)

    return out, enrichments


def build_evidence_appendix_section(
    bank: dict[str, Any],
    corrections: list[dict[str, Any]],
    *,
    sections: list[dict[str, Any]] | None = None,
    topic: str = "",
    industry: str = "",
    geography: str = "",
) -> dict[str, Any] | None:
    """Deterministic appendix (no LLM) listing the tiered evidence bank."""
    try:
        from iidatech.evidence_bank.report_postprocess import ledger_rows_for_report, public_store_label
        from iidatech.evidence_bank.source_policy import verified_bank_rows as _vbr

        all_rows = _vbr(_as_list(bank.get("rows")))
        rows = ledger_rows_for_report(
            all_rows,
            sections or [],
            topic=topic,
            industry=industry,
            geography=geography,
        )
    except ImportError:
        rows = [r for r in _as_list(bank.get("rows")) if r.get("tier") == TIER_VERIFIED]
        ledger_rows_for_report = None  # type: ignore
        public_store_label = lambda _m: ""  # type: ignore

    url_contradictions = _as_list(bank.get("url_contradictions"))
    if not rows and not corrections and not url_contradictions:
        return None

    lines = [
        "This appendix lists the evidence bank gathered before report generation. "
        "Tier 1 = independently verified (scraped/corroborated). Tier 2 = reported by the research engine with a source URL. "
        "Where the two disagreed, Tier 1 values were shown in the report. "
        "Rows are ranked by relevance to this report's cited figures and topic.",
        "",
        "| Item | Type | Tier | Value | Verification | Source |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        value = r.get("verified_price") or r.get("reported_price") or r.get("metric_value") or "-"
        tier_label = "Tier 1" if r.get("tier") == TIER_VERIFIED else "Tier 2"
        lines.append(
            f"| {r.get('name') or r.get('metric_name') or '-'} | {r.get('record_type')} | {tier_label} "
            f"| {value} | {r.get('verification_status')} | {r.get('url') or '-'} |"
        )

    all_resolved = len(corrections) + len(url_contradictions)
    if corrections or url_contradictions:
        lines += ["", f"**Contradictions resolved ({all_resolved}):** verified data replaced reported or duplicate values."]
        for c in corrections[:10]:
            lines.append(
                f"- {c.get('company') or c.get('metric_name') or 'item'}: "
                f"`{c.get('replaced')}` replaced by `{c.get('verified')}` ({c.get('source')})"
            )
        for c in url_contradictions[:10]:
            lines.append(
                f"- {c.get('url')}: kept `{c.get('kept')}` over `{c.get('discarded')}` ({c.get('resolution')})"
            )

    gaps = _as_list(bank.get("gaps"))
    if gaps:
        lines += ["", "**Evidence gaps:**"] + [f"- {g}" for g in gaps]

    store = _as_dict(bank.get("store"))
    label = public_store_label(store)
    if label:
        lines += ["", f"**{label}**"]

    return {
        "id": 99,
        "title": "Evidence Bank & Verification Ledger",
        "body_markdown": "\n".join(lines),
        "key_metrics": {
            "tier1_rows": bank.get("tier1_count", 0),
            "tier2_rows": bank.get("tier2_count", 0),
            "trusted_publisher_rows": bank.get("trusted_row_count", 0),
            "contradictions_resolved": all_resolved,
        },
        "sources": [r.get("url") for r in rows[:12] if r.get("url")],
    }
