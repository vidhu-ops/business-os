"""Harvest source-backed bottom-up TAM/SAM/SOM from benchmarks + verified pricing."""
from __future__ import annotations

import re
from statistics import median
from typing import Any

from iidatech.proprietary_data.industry_map import resolve_vertical
from iidatech.proprietary_data.loader import query_benchmarks
from iidatech.services.pricing_bank_bridge import median_verified_acv_monthly

_DEFAULT_SEATS = 3
_DEFAULT_FREQ = 12
_DEFAULT_SAM_SHARE = 0.20
_DEFAULT_SOM_CAPTURE = 0.03

_COUNT_RE = re.compile(
    r"([\d,.]+)\s*(million|billion|thousand|mn|bn|k)?\s*(?:small\s+business|smb|companies|businesses|firms)",
    re.I,
)


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def _short_usd(value: float) -> str:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "n/a"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:,.0f}"


def _geo_rank(row_geo: str, target_geo: str) -> int:
    row = (row_geo or "Global").strip().lower()
    target = (target_geo or "Global").strip().lower()
    if row == target:
        return 0
    if target in {"", "global", "worldwide", "international"}:
        return 1 if row == "global" else 2
    if row in {"", "global", "worldwide", "international"}:
        return 1
    if target in row or row in target:
        return 2
    return 3


def _best_benchmark(rows: list[dict[str, Any]], metric: str, geography: str) -> dict[str, Any] | None:
    candidates = [r for r in rows if str(r.get("metric") or "") == metric]
    if not candidates:
        return None
    candidates.sort(
        key=lambda r: (
            _geo_rank(str(r.get("geography") or ""), geography),
            -float(r.get("trust_score") or 0),
        )
    )
    return candidates[0]


def _scale_count(raw: float, unit: str) -> float:
    unit = (unit or "").lower()
    if unit in {"billion", "bn"}:
        return raw * 1_000_000_000
    if unit in {"million", "mn"}:
        return raw * 1_000_000
    if unit in {"thousand", "k"}:
        return raw * 1_000
    return raw


def _parse_serp_buyer_count(topic: str, geography: str) -> tuple[float | None, str]:
    try:
        from iidatech.evidence_bank.serp_intelligence import _serp_call
    except ImportError:
        return None, ""
    query = f"{topic} number of SMBs {geography}".strip()
    payload = _serp_call("google", query, cache_kind="tam_bottom_up")
    if payload.get("error"):
        return None, ""
    snippets: list[str] = []
    for block in _as_list(payload.get("organic_results")):
        if isinstance(block, dict):
            snippets.append(str(block.get("snippet") or ""))
            snippets.append(str(block.get("title") or ""))
    blob = " ".join(snippets)
    best: float | None = None
    for match in _COUNT_RE.finditer(blob):
        try:
            raw = float(match.group(1).replace(",", ""))
        except ValueError:
            continue
        scaled = _scale_count(raw, match.group(2) or "")
        if scaled > 0 and (best is None or scaled > best):
            best = scaled
    return best, query


def _collect_pricing_rows(
    pricing_rows: list[dict[str, Any]] | None,
    diligence_pack: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _as_list(pricing_rows):
        if isinstance(row, dict):
            rows.append(row)
    pack = _as_dict(diligence_pack)
    pricing_pack = _as_dict(pack.get("pricing_intelligence_pack"))
    for row in _as_list(pricing_pack.get("sourced_pricing_records")):
        if isinstance(row, dict):
            rows.append(row)
    for row in _as_list(pack.get("verified_competitor_pricing_matrix")):
        if isinstance(row, dict):
            rows.append(row)
    return rows


def harvest_bottom_up_tam(
    *,
    topic: str,
    industry: str,
    geography: str,
    domain: str | None = None,
    pricing_rows: list[dict[str, Any]] | None = None,
    diligence_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    vertical = resolve_vertical(topic, industry, domain)
    benchmarks = query_benchmarks(topic, industry, geography, domain=vertical, limit=80)
    buyer_row = _best_benchmark(benchmarks, "buyer_count", geography)
    ticket_row = _best_benchmark(benchmarks, "avg_ticket", geography)

    trace: dict[str, Any] = {
        "vertical": vertical,
        "benchmark_rows": len(benchmarks),
        "buyer_source": buyer_row,
        "ticket_source": ticket_row,
    }

    buyer_count: float | None = None
    if buyer_row:
        try:
            buyer_count = float(buyer_row.get("value"))
        except (TypeError, ValueError):
            buyer_count = None

    if not buyer_count or buyer_count <= 0:
        serp_count, serp_query = _parse_serp_buyer_count(topic, geography)
        trace["serp_buyer_query"] = serp_query
        trace["serp_buyer_count"] = serp_count
        if serp_count and serp_count > 0:
            buyer_count = serp_count
            trace["buyer_source"] = {"source_type": "serp_snippet", "value": serp_count}

    all_pricing = _collect_pricing_rows(pricing_rows, diligence_pack)
    harvested_monthly = median_verified_acv_monthly(all_pricing)
    trace["pricing_row_count"] = len(all_pricing)
    trace["harvested_monthly_median"] = harvested_monthly

    avg_ticket: float | None = harvested_monthly
    ticket_source = "pricing_harvest_median"
    if avg_ticket is None and ticket_row:
        try:
            avg_ticket = float(ticket_row.get("value"))
            ticket_source = "benchmark_bank"
        except (TypeError, ValueError):
            avg_ticket = None

    missing: list[str] = []
    if not buyer_count or buyer_count <= 0:
        missing.append("buyer_count")
    if not avg_ticket or avg_ticket <= 0:
        missing.append("avg_ticket")

    if missing:
        return {
            "complete": False,
            "missing": missing,
            "trace": trace,
        }

    seats = _DEFAULT_SEATS
    frequency = _DEFAULT_FREQ
    sam_share = _DEFAULT_SAM_SHARE
    som_capture = _DEFAULT_SOM_CAPTURE

    annual_spend_per_buyer = float(avg_ticket) * seats * frequency
    tam = float(buyer_count) * annual_spend_per_buyer
    sam = tam * sam_share
    som = sam * som_capture

    sources: list[dict[str, Any]] = []
    if buyer_row:
        sources.append(
            {
                "input": "buyer_count",
                "value": buyer_count,
                "source_type": buyer_row.get("source_type"),
                "geography": buyer_row.get("geography"),
                "trust_score": buyer_row.get("trust_score"),
            }
        )
    elif trace.get("serp_buyer_count"):
        sources.append({"input": "buyer_count", "value": buyer_count, "source_type": "serp_snippet"})
    sources.append(
        {
            "input": "avg_ticket_monthly",
            "value": avg_ticket,
            "source_type": ticket_source,
            "geography": (ticket_row or {}).get("geography") if ticket_row else geography,
            "trust_score": (ticket_row or {}).get("trust_score") if ticket_row else None,
        }
    )

    bottom_up = {
        "status": "source_backed_bottom_up",
        "formula": "buyer_count × avg_monthly_ticket × seats_per_buyer × purchase_frequency",
        "buyer_count": int(buyer_count) if buyer_count == int(buyer_count) else buyer_count,
        "avg_ticket": round(float(avg_ticket), 2),
        "purchase_frequency": frequency,
        "seats_per_buyer": seats,
        "sam_share_assumption": sam_share,
        "som_capture_share_assumption": som_capture,
        "tam": tam,
        "tam_result": {
            "tam": tam,
            "tam_usd": tam,
            "tam_fmt": _short_usd(tam),
            "sam": sam,
            "sam_fmt": _short_usd(sam),
            "som": som,
            "som_fmt": _short_usd(som),
        },
        "current_outputs": {
            "Base TAM": _short_usd(tam),
            "SAM": _short_usd(sam),
            "SOM": _short_usd(som),
        },
        "calculation_inputs": {
            "buyer_count": buyer_count,
            "avg_monthly_ticket_usd": avg_ticket,
            "seats_per_buyer": seats,
            "purchase_frequency_months": frequency,
            "annual_spend_per_buyer_usd": annual_spend_per_buyer,
            "sam_share_assumption": sam_share,
            "som_capture_share_assumption": som_capture,
        },
        "sources": sources,
        "assumption_table": [
            {
                "input": "Seats per buyer",
                "value": seats,
                "source_or_basis": "SMB CRM planning default; validate with ICP seat survey",
            },
            {
                "input": "SAM share",
                "value": sam_share,
                "source_or_basis": "serviceable segment assumption; validate channel/geo fit",
            },
            {
                "input": "SOM capture",
                "value": som_capture,
                "source_or_basis": "early capture assumption; validate GTM capacity",
            },
        ],
        "evidence_namespace": "BENCHMARK_BANK+PRICING_HARVEST",
        "citation_allowed": True,
        "not_investor_citable": False,
        "verification_rule": "Denominator and ticket from benchmark bank and/or verified pricing pages; SAM/SOM shares are labeled assumptions.",
    }

    return {
        "complete": True,
        "bottom_up_market_calculation": bottom_up,
        "trace": trace,
    }
