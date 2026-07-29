"""Deterministic post-processing for Understand-your-market reports."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_BRACKET_CITE_RE = re.compile(r"\s*\[(\d{1,2})\]")
_VALID_URL_RE = re.compile(r"^https?://[^\s<>\"']+\.[a-z]{2,}(/[^\s]*)?$", re.IGNORECASE)

_REFUSAL_PHRASES: tuple[str, ...] = (
    "not enough directly relevant",
    "not enough relevant",
    "insufficient information",
    "don't have enough",
    "do not have enough",
    "cannot provide",
    "can't provide",
    "unable to find",
    "no directly relevant",
    "i don't have",
    "there is not enough",
    "could not find sufficient",
    "no reliable data",
)

_MONEY_IN_TEXT_RE = re.compile(
    r"(?:USD|US\$|INR|Rs\.?|[$\u20b9])\s?[\d.,]+\s?(?:billion|million|mn|bn|crore|lakh)?",
    re.IGNORECASE,
)


def has_parseable_figure(text: str) -> bool:
    return bool(_MONEY_IN_TEXT_RE.search(str(text or "")) or re.search(r"\d+\s*%", str(text or "")))


def is_refusal_text(text: str) -> bool:
    blob = str(text or "").strip().lower()
    if not blob or len(blob) < 20:
        return False
    return any(p in blob for p in _REFUSAL_PHRASES)


def is_valid_source_url(url: str) -> bool:
    u = str(url or "").strip()
    if len(u) < 12 or " " in u:
        return False
    if u.endswith("-") or u.endswith("ww") or u.count("://") != 1:
        return False
    try:
        parsed = urlparse(u)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.netloc or ""
        if not host or "." not in host:
            return False
        if len(host.split(".")[-1]) < 2:
            return False
    except Exception:
        return False
    return bool(_VALID_URL_RE.match(u))


def filter_valid_urls(urls: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for url in urls:
        u = str(url or "").strip()
        if not u or u in seen or not is_valid_source_url(u):
            continue
        seen.add(u)
        out.append(u)
    return out


def normalize_url(url: str) -> str:
    u = str(url or "").strip().lower().rstrip("/")
    if u.startswith("https://www."):
        return "https://" + u[12:]
    if u.startswith("http://www."):
        return "http://" + u[11:]
    return u


def _row_value(row: dict[str, Any]) -> str:
    return str(
        row.get("verified_price")
        or row.get("metric_value")
        or row.get("reported_price")
        or ""
    ).strip()


def _values_meaningfully_differ(a: str, b: str) -> bool:
    if not a or not b:
        return False
    return re.sub(r"\s+", " ", a.lower()) != re.sub(r"\s+", " ", b.lower())


def _row_quality_score(row: dict[str, Any]) -> tuple[int, int]:
    """Higher is better. Prefer parseable figures over source_reference refusals."""
    value = _row_value(row)
    metric = str(row.get("metric_name") or "")
    score = 0
    if metric == "source_reference":
        score -= 5
    if is_refusal_text(value) or is_refusal_text(str(row.get("name") or "")):
        score -= 20
    if _MONEY_IN_TEXT_RE.search(value):
        score += 8
    if re.search(r"\d+\s*%", value):
        score += 5
    if metric in {"market_value", "cagr", "gdp_current_usd", "user_rating", "review_count"}:
        score += 4
    if row.get("record_type") == "official_statistics_api":
        score += 3
    return (score, len(value))


def dedupe_bank_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """One row per URL+metric; surface duplicate-URL contradictions."""
    best: dict[str, dict[str, Any]] = {}
    contradictions: list[dict[str, Any]] = []

    for row in rows:
        if not isinstance(row, dict):
            continue
        value = _row_value(row)
        if is_refusal_text(value) or is_refusal_text(str(row.get("metric_name") or "")):
            continue
        if metric := str(row.get("metric_name") or ""):
            if metric == "source_reference" and (not value or is_refusal_text(value) or len(value) < 8):
                continue
        url = normalize_url(str(row.get("url") or ""))
        if not url or not is_valid_source_url(url):
            continue
        key = f"{url}|{row.get('metric_name') or ''}"
        existing = best.get(key)
        if existing is None:
            best[key] = dict(row)
            continue
        if _values_meaningfully_differ(_row_value(existing), value):
            contradictions.append({
                "url": url,
                "metric_name": row.get("metric_name"),
                "kept": _row_value(existing),
                "discarded": value,
                "resolution": "kept_higher_quality_row",
            })
        if _row_quality_score(row) > _row_quality_score(existing):
            best[key] = dict(row)

    # Same URL, different metrics — flag market_value conflicts
    by_url: dict[str, list[dict[str, Any]]] = {}
    for row in best.values():
        u = normalize_url(str(row.get("url") or ""))
        by_url.setdefault(u, []).append(row)
    final: list[dict[str, Any]] = []
    for url, group in by_url.items():
        market_rows = [r for r in group if str(r.get("metric_name") or "") == "market_value"]
        if len(market_rows) > 1:
            market_rows.sort(key=_row_quality_score, reverse=True)
            kept = market_rows[0]
            for dropped in market_rows[1:]:
                contradictions.append({
                    "url": url,
                    "metric_name": "market_value",
                    "kept": _row_value(kept),
                    "discarded": _row_value(dropped),
                    "resolution": "single_market_value_per_url",
                })
            final.extend([r for r in group if str(r.get("metric_name") or "") != "market_value"])
            final.append(kept)
        else:
            final.extend(group)
    return final, contradictions


def _topic_tokens(topic: str, industry: str, geography: str) -> list[str]:
    stop = {"the", "and", "for", "with", "market", "industry", "items", "global"}
    return [
        t for t in re.findall(r"[a-z]{4,}", f"{topic} {industry} {geography}".lower())
        if t not in stop
    ]


def score_row_relevance(
    row: dict[str, Any],
    *,
    topic: str,
    industry: str,
    geography: str,
    report_blob: str = "",
) -> float:
    tokens = _topic_tokens(topic, industry, geography)
    blob = " ".join(
        str(row.get(k) or "")
        for k in ("name", "metric_name", "metric_value", "metric_context", "publisher", "url", "record_type")
    ).lower()
    geo = geography.lower()
    score = 0.0
    for t in tokens:
        if t in blob:
            score += 1.5
    if "india" in geo and ("india" in blob or "ibef" in blob or "mospi" in blob or "rbi" in blob):
        score += 3.0
    if "india" in geo and any(x in blob for x in ("europe", "european union", "eu ", "oecd retail")):
        score -= 4.0
    value = _row_value(row)
    if value and value.lower() in report_blob.lower():
        score += 5.0
    if _MONEY_IN_TEXT_RE.search(value) and value.lower() in report_blob.lower():
        score += 8.0
    if is_refusal_text(value):
        score -= 50.0
    score += _row_quality_score(row)[0] * 0.3
    return score


def ledger_rows_for_report(
    rows: list[dict[str, Any]],
    sections: list[dict[str, Any]],
    *,
    topic: str,
    industry: str,
    geography: str,
    max_rows: int = 25,
) -> list[dict[str, Any]]:
    """Ledger shows load-bearing + topic-relevant rows first; drops filler."""
    report_blob = " ".join(
        str(s.get("body_markdown") or "") + " " + " ".join(str(v) for v in (s.get("key_metrics") or {}).values())
        for s in sections
    ).lower()

    # Pull anchor figures cited in report into ledger even if row name mismatches
    cited_values: set[str] = set()
    for m in _MONEY_IN_TEXT_RE.findall(report_blob):
        cited_values.add(m.lower().strip())

    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        value = _row_value(row)
        if is_refusal_text(value):
            continue
        rel = score_row_relevance(row, topic=topic, industry=industry, geography=geography, report_blob=report_blob)
        if any(cv in value.lower() for cv in cited_values if len(cv) > 4):
            rel += 10.0
        if rel < 0.5:
            continue
        scored.append((rel, row))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [r for _, r in scored[:max_rows]]


def sync_section_citations(section: dict[str, Any]) -> dict[str, Any]:
    """Finalize sources then strip stale [N] bracket refs that drift after enrichment."""
    out = dict(section)
    sources = filter_valid_urls([str(u) for u in (section.get("sources") or []) if str(u).strip()])
    body = str(section.get("body_markdown") or "")
    body = _BRACKET_CITE_RE.sub("", body)
    metrics = dict(section.get("key_metrics") or {})
    clean_metrics = {}
    for k, v in metrics.items():
        vs = str(v or "")
        if is_refusal_text(vs):
            continue
        clean_metrics[k] = vs
    out["body_markdown"] = body
    out["sources"] = sources
    out["key_metrics"] = clean_metrics
    return out


def public_store_label(store_meta: dict[str, Any]) -> str:
    total = int(store_meta.get("rows_total") or 0)
    if total <= 0:
        return ""
    return f"IIDATECH evidence bank: {total} verified rows on file for this topic."


def completeness_score(
    sections: list[dict[str, Any]],
    expected: int,
    gaps: list[str] | None = None,
) -> float:
    if expected <= 0:
        return 0.0
    filled = sum(1 for s in sections if len(str(s.get("body_markdown") or "").strip()) > 120)
    base = 10.0 * filled / expected
    cap = 10.0
    gap_text = " ".join(str(g) for g in (gaps or [])).lower()
    if "only 0 named competitors" in gap_text or "no independently verified pricing" in gap_text:
        cap = min(cap, 5.0)
    if "no trusted-publisher rows" in gap_text:
        cap = min(cap, 6.0)
    if len(gaps or []) >= 3:
        cap = min(cap, 6.5)
    return round(min(cap, base), 1)
