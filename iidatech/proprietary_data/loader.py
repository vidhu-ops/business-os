"""Load and query IIDATECH proprietary JSONL datasets."""
from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from iidatech.proprietary_data.industry_map import resolve_vertical

_DATA_DIR = Path(__file__).resolve().parent

# DEPRECATED for competitor_matrix / confidence scoring (audit 2026-07-06):
# competitor_pricing_bank.jsonl is 100% seed-generated (0 live-verified rows).
# Competitor rows must come from Perplexity + Firecrawl. Bank kept for
# seed_bank_refresh backfill and pricing_bank_bridge until those paths migrate.
_BANK_FILES = {
    "competitor_pricing": "competitor_pricing_bank.jsonl",
    "buyer_voice": "buyer_voice_bank.jsonl",
    "supplier_cost": "supplier_cost_bank.jsonl",
    "benchmark": "benchmark_bank_v2.jsonl",
}


@lru_cache(maxsize=4)
def _load_bank(name: str) -> tuple[dict[str, Any], ...]:
    filename = _BANK_FILES.get(name)
    if not filename:
        return ()
    path = _DATA_DIR / filename
    if not path.exists():
        return ()
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    rows.append(row)
            except json.JSONDecodeError:
                continue
    return tuple(rows)


def _sql_ready() -> bool:
    try:
        from iidatech.storage.db import sql_storage_ready
        return sql_storage_ready()
    except Exception:
        return False


def bank_row_counts() -> dict[str, int]:
    if _sql_ready():
        from iidatech.storage.repositories import bank_row_counts as sql_counts
        return sql_counts()
    return {name: len(_load_bank(name)) for name in _BANK_FILES}


def _region_match(row_region: str, geography: str) -> bool:
    geo = (geography or "Global").strip().lower()
    reg = (row_region or "Global").strip().lower()
    if geo in {"", "global", "worldwide", "international"}:
        return True
    if reg in {"", "global", "worldwide", "international"}:
        return True
    return geo in reg or reg in geo


def query_competitor_pricing(
    topic: str,
    industry: str,
    geography: str = "Global",
    *,
    domain: str | None = None,
    limit: int = 40,
) -> list[dict[str, Any]]:
    """DEPRECATED for competitor_matrix scoring — seed bank only.

    Returns rows from competitor_pricing_bank.jsonl when explicitly enabled via
    IIDATECH_COMPETITOR_PRICING_BANK=1. Default off so stale seed data cannot
    feed competitor_matrix or real_confidence specificity.
    """
    if os.getenv("IIDATECH_COMPETITOR_PRICING_BANK", "0").strip().lower() not in {"1", "true", "yes"}:
        return []
    vertical = resolve_vertical(topic, industry, domain)
    if _sql_ready():
        from iidatech.storage.repositories import get_competitor_pricing
        rows = get_competitor_pricing(vertical, geography, limit=limit)
        filtered = [
            row for row in rows
            if str(row.get("industry") or "") == vertical
            or vertical in str(row.get("industry") or "")
        ]
        return (filtered or rows)[:limit]
    rows = []
    for row in _load_bank("competitor_pricing"):
        ind = str(row.get("industry") or "")
        if ind != vertical and vertical not in ind:
            continue
        if not _region_match(str(row.get("region") or ""), geography):
            continue
        rows.append(row)
    rows.sort(key=lambda r: float(r.get("trust_score") or 0), reverse=True)
    return rows[:limit]


def query_buyer_voice(
    topic: str,
    industry: str,
    geography: str = "Global",
    *,
    domain: str | None = None,
    limit: int = 80,
) -> list[dict[str, Any]]:
    vertical = resolve_vertical(topic, industry, domain)
    if _sql_ready():
        from iidatech.storage.repositories import get_buyer_voice
        return get_buyer_voice(vertical, geography, limit=limit)
    rows = []
    for row in _load_bank("buyer_voice"):
        if str(row.get("industry") or "") != vertical:
            continue
        if not _region_match(str(row.get("region") or ""), geography):
            continue
        rows.append(row)
    rows.sort(key=lambda r: float(r.get("frequency") or 0), reverse=True)
    return rows[:limit]


def query_supplier_costs(
    topic: str,
    industry: str,
    geography: str = "Global",
    *,
    domain: str | None = None,
    limit: int = 30,
) -> list[dict[str, Any]]:
    vertical = resolve_vertical(topic, industry, domain)
    if _sql_ready():
        from iidatech.storage.repositories import get_supplier_costs
        return get_supplier_costs(vertical, geography, limit=limit)
    rows = []
    for row in _load_bank("supplier_cost"):
        if str(row.get("industry") or "") != vertical:
            continue
        if not _region_match(str(row.get("region") or ""), geography):
            continue
        rows.append(row)
    rows.sort(key=lambda r: float(r.get("trust_score") or 0), reverse=True)
    return rows[:limit]


def query_benchmarks(
    topic: str,
    industry: str,
    geography: str = "Global",
    *,
    domain: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    vertical = resolve_vertical(topic, industry, domain)
    if _sql_ready():
        from iidatech.storage.repositories import get_benchmarks
        return get_benchmarks(vertical, geography, limit=limit)
    rows = []
    for row in _load_bank("benchmark"):
        if str(row.get("industry") or "") != vertical:
            continue
        if not _region_match(str(row.get("geography") or ""), geography):
            continue
        rows.append(row)
    rows.sort(key=lambda r: float(r.get("trust_score") or 0), reverse=True)
    return rows[:limit]


def load_proprietary_context(
    topic: str,
    industry: str,
    geography: str,
    *,
    domain: str | None = None,
) -> dict[str, Any]:
    vertical = resolve_vertical(topic, industry, domain)
    semantic_memory: list[dict[str, Any]] = []
    try:
        from iidatech.storage.db import init_schema
        from iidatech.storage.semantic_memory import search_cross_industry_patterns, semantic_memory_ready

        init_schema()
        if semantic_memory_ready():
            semantic_memory = search_cross_industry_patterns(f"{topic} {industry}", limit=12)
    except Exception:
        semantic_memory = []
    return {
        "vertical": vertical,
        "semantic_memory": semantic_memory,
        "competitor_pricing": query_competitor_pricing(topic, industry, geography, domain=domain),
        "buyer_voice": query_buyer_voice(topic, industry, geography, domain=domain),
        "supplier_costs": query_supplier_costs(topic, industry, geography, domain=domain),
        "benchmarks": query_benchmarks(topic, industry, geography, domain=domain),
        "source_priority": [
            "sql_semantic_memory",
            "sql_cache",
            "sql_database",
            "proprietary_datasets",
            "evidence_bank",
            "serpapi",
            "exact_search",
            "exa",
            "tavily",
        ],
    }