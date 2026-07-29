"""Gitnux Market Data adapter - optional benchmark enrichment for report harvest."""
from __future__ import annotations

import json
import os
import re
import time
from typing import Any
from urllib.parse import urlparse

import requests

_GITNUX_BASE = "https://gitnux.org"
_STATISTIC_SITEMAP = f"{_GITNUX_BASE}/sitemap/shards/statistic.xml"
_USER_AGENT = "IIDATECH/1.0 (+https://gitnux.org/topics/)"
_CACHE_TTL_SEC = 6 * 60 * 60
_URL_CACHE: dict[str, Any] = {"loaded_at": 0.0, "urls": []}
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "for",
        "and",
        "or",
        "in",
        "on",
        "of",
        "to",
        "with",
        "india",
        "global",
        "us",
        "uk",
        "saas",
        "b2b",
        "b2c",
        "software",
        "industry",
        "statistics",
        "statistic",
        "market",
    }
)
_GENERIC_TOPIC_TOKENS = frozenset(
    {
        "automation",
        "platform",
        "tool",
        "tools",
        "service",
        "services",
        "solution",
        "solutions",
        "digital",
        "cloud",
    }
)
_HAS_DIGIT_RE = re.compile(r"\d")
_KEY_TAKEAWAY_RE = re.compile(r"##\s*Key Takeaways\s*(.*?)(?:\n##\s|\Z)", re.I | re.S)
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+)$", re.M)
_STAT_LINE_RE = re.compile(r"(?:^|\n)\d{2}\s*\n\s*([^\n]{20,400})", re.M)
_NEXT_DATA_RE = re.compile(
    r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
    re.S,
)


def gitnux_enabled() -> bool:
    return os.getenv("IIDATECH_GITNUX_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "off",
        "no",
    }


def _topic_tokens(topic: str, industry: str = "") -> set[str]:
    blob = f"{topic} {industry}".lower()
    tokens = {t for t in re.findall(r"[a-z0-9]{3,}", blob)}
    return {t for t in tokens if t not in _STOPWORDS}


def _slug_tokens(url: str) -> set[str]:
    path = urlparse(url).path.strip("/")
    slug = path.replace("-statistics", "").replace("-stats", "")
    return {t for t in re.findall(r"[a-z0-9]{3,}", slug) if t not in _STOPWORDS}


def _score_url(url: str, topic_tokens: set[str]) -> float:
    slug_tokens = _slug_tokens(url)
    if not topic_tokens or not slug_tokens:
        return 0.0
    overlap = len(topic_tokens & slug_tokens)
    if overlap == 0:
        return 0.0
    precision = overlap / max(len(slug_tokens), 1)
    recall = overlap / max(len(topic_tokens), 1)
    score = (0.65 * recall) + (0.35 * precision)
    anchor_tokens = topic_tokens - _GENERIC_TOPIC_TOKENS
    if anchor_tokens and not (anchor_tokens & slug_tokens):
        score *= 0.25
    if url.endswith("-industry-statistics/") or url.endswith("-industry-statistics"):
        score += 0.05
    return score


def _load_statistic_urls(*, force: bool = False) -> list[str]:
    now = time.time()
    if (
        not force
        and _URL_CACHE.get("urls")
        and (now - float(_URL_CACHE.get("loaded_at") or 0)) < _CACHE_TTL_SEC
    ):
        return list(_URL_CACHE["urls"])
    try:
        resp = requests.get(
            _STATISTIC_SITEMAP,
            timeout=45,
            headers={"User-Agent": _USER_AGENT},
        )
        resp.raise_for_status()
        urls = re.findall(r"<loc>([^<]+)</loc>", resp.text)
        urls = [u.strip() for u in urls if "statistics" in u.lower()]
        _URL_CACHE["urls"] = urls
        _URL_CACHE["loaded_at"] = now
        return urls
    except Exception:
        return list(_URL_CACHE.get("urls") or [])


def match_gitnux_report(
    topic: str,
    industry: str = "",
    *,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not gitnux_enabled():
        return []
    tokens = _topic_tokens(topic, industry)
    if not tokens:
        return []
    ranked: list[tuple[float, str]] = []
    for url in _load_statistic_urls():
        score = _score_url(url, tokens)
        if score > 0:
            ranked.append((score, url))
    ranked.sort(key=lambda row: row[0], reverse=True)
    out: list[dict[str, Any]] = []
    for score, url in ranked[: max(1, int(limit))]:
        slug = urlparse(url).path.strip("/").replace("-", " ")
        out.append({"url": url, "score": round(score, 3), "slug": slug})
    return out


def _walk_stat_strings(node: Any, found: list[str], *, depth: int = 0) -> None:
    if depth > 8:
        return
    if isinstance(node, str):
        text = node.strip()
        if len(text) < 20 or len(text) > 500:
            return
        if not _HAS_DIGIT_RE.search(text):
            return
        if text not in found:
            found.append(text)
        return
    if isinstance(node, dict):
        for val in node.values():
            _walk_stat_strings(val, found, depth=depth + 1)
        return
    if isinstance(node, list):
        for item in node[:80]:
            _walk_stat_strings(item, found, depth=depth + 1)


def _extract_stats_from_next_data(html: str) -> list[str]:
    match = _NEXT_DATA_RE.search(html or "")
    if not match:
        return []
    try:
        data = json.loads(match.group(1))
    except json.JSONDecodeError:
        return []
    found: list[str] = []
    _walk_stat_strings(data, found)
    return found[:40]


def _extract_stats_from_markdownish(html: str) -> list[str]:
    text = re.sub(r"<[^>]+>", "\n", html or "")
    text = re.sub(r"\n{3,}", "\n\n", text)
    stats: list[str] = []
    kt = _KEY_TAKEAWAY_RE.search(text)
    if kt:
        for bullet in _BULLET_RE.findall(kt.group(1)):
            line = re.sub(r"\s+", " ", bullet).strip()
            if len(line) >= 20 and _HAS_DIGIT_RE.search(line):
                stats.append(line)
    for line in _STAT_LINE_RE.findall(text):
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned and cleaned not in stats:
            stats.append(cleaned)
    return stats[:40]


def _stat_to_fact(stat: str, *, source_url: str, idx: int) -> dict[str, Any]:
    year_match = re.search(r"\b(19|20)\d{2}\b", stat)
    publisher = ""
    pub_match = re.search(r"\((?:per|source:?\s*)?([A-Za-z][^)()]{2,40})\)", stat)
    if pub_match:
        publisher = pub_match.group(1).strip()
    metric = "benchmark"
    lower = stat.lower()
    for key in (
        "tam",
        "sam",
        "som",
        "cagr",
        "revenue",
        "market size",
        "adoption",
        "pricing",
        "cac",
        "ltv",
    ):
        if key in lower:
            metric = (
                key.upper()
                if key in {"tam", "sam", "som", "cagr", "cac", "ltv"}
                else key.replace(" ", "_")
            )
            break
    value = stat[:177] + "..." if len(stat) > 180 else stat
    return {
        "metric": f"{metric}_{idx}",
        "value": value,
        "source_url": source_url,
        "year": year_match.group(0) if year_match else "",
        "publisher": publisher or "Gitnux (secondary aggregator)",
        "label": "FACT",
        "notes": "Gitnux statistic - verify primary source in stat text.",
    }


def fetch_gitnux_report(url: str) -> dict[str, Any]:
    trace: dict[str, Any] = {"url": url, "errors": []}
    if not gitnux_enabled():
        trace["errors"].append("gitnux_disabled")
        return {"success": False, "trace": trace}
    try:
        resp = requests.get(url, timeout=30, headers={"User-Agent": _USER_AGENT})
        resp.raise_for_status()
        html = resp.text
    except Exception as exc:
        trace["errors"].append(str(exc)[:200])
        return {"success": False, "trace": trace}
    title_match = re.search(r"<title>([^<]+)</title>", html, re.I)
    title = (
        re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else url
    )
    stats = _extract_stats_from_next_data(html)
    if len(stats) < 4:
        stats = _extract_stats_from_markdownish(html)
    facts = [
        _stat_to_fact(line, source_url=url, idx=i + 1)
        for i, line in enumerate(stats[:25])
    ]
    trace["stat_count"] = len(facts)
    return {
        "success": bool(facts),
        "url": url,
        "title": title,
        "financial_facts": facts,
        "competitor_facts": [],
        "pricing_facts": [],
        "trace": trace,
    }


def gitnux_benchmark_pack(
    topic: str,
    industry: str = "",
    *,
    max_reports: int = 1,
) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "enabled": gitnux_enabled(),
        "matched_reports": [],
        "financial_facts": [],
        "competitor_facts": [],
        "pricing_facts": [],
        "source_urls": [],
    }
    if not gitnux_enabled():
        return empty
    matches = match_gitnux_report(topic, industry, limit=max_reports)
    if not matches:
        empty["note"] = "no_gitnux_slug_match"
        return empty
    financial_facts: list[dict[str, Any]] = []
    source_urls: list[str] = []
    matched_reports: list[dict[str, Any]] = []
    for match in matches[: max(1, int(max_reports))]:
        report = fetch_gitnux_report(str(match.get("url") or ""))
        if not report.get("success"):
            continue
        url = str(report.get("url") or "")
        matched_reports.append(
            {
                "url": url,
                "title": report.get("title"),
                "score": match.get("score"),
                "stat_count": len(report.get("financial_facts") or []),
            }
        )
        if url and url not in source_urls:
            source_urls.append(url)
        financial_facts.extend(report.get("financial_facts") or [])
    return {
        "enabled": True,
        "matched_reports": matched_reports,
        "financial_facts": financial_facts[:30],
        "competitor_facts": [],
        "pricing_facts": [],
        "source_urls": source_urls,
        "note": "gitnux_secondary_benchmark",
    }


def merge_gitnux_into_harvest(
    harvest: dict[str, Any],
    gitnux_pack: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    out = dict(harvest or {})
    citations: list[str] = []
    if not gitnux_pack or not gitnux_pack.get("enabled"):
        return out, citations
    for key in ("financial_facts", "competitor_facts", "pricing_facts"):
        existing = out.get(key) if isinstance(out.get(key), list) else []
        extra = gitnux_pack.get(key) if isinstance(gitnux_pack.get(key), list) else []
        out[key] = list(existing) + list(extra)
    notes = str(out.get("search_notes") or "").strip()
    reports = gitnux_pack.get("matched_reports") or []
    if reports:
        titles = "; ".join(
            f"{r.get('title')} ({r.get('url')})" for r in reports[:2]
        )
        gitnux_note = f"Gitnux benchmark reports: {titles}"
        out["search_notes"] = f"{notes}\n{gitnux_note}".strip() if notes else gitnux_note
    for url in gitnux_pack.get("source_urls") or []:
        u = str(url).strip()
        if u.startswith("http") and u not in citations:
            citations.append(u)
    out["gitnux"] = {
        "matched_reports": reports,
        "fact_count": len(gitnux_pack.get("financial_facts") or []),
    }
    return out, citations


def format_gitnux_block(gitnux_pack: dict[str, Any]) -> str:
    if not gitnux_pack or not gitnux_pack.get("matched_reports"):
        return ""
    lines = [
        "GITNUX BENCHMARK DATA (secondary aggregator - verify primary sources in each stat):",
        "",
    ]
    for report in gitnux_pack.get("matched_reports") or []:
        lines.append(
            f"- Report: {report.get('title')} - {report.get('url')} "
            f"(match score {report.get('score')})"
        )
    lines.append("")
    for fact in (gitnux_pack.get("financial_facts") or [])[:15]:
        if isinstance(fact, dict):
            lines.append(
                f"- [{fact.get('metric')}] {fact.get('value')} "
                f"(via Gitnux -> {fact.get('publisher') or 'see stat text'})"
            )
    return "\n".join(lines).strip()
