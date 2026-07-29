"""Structured unit-economics grounding for synthesis (no hallucinated values)."""

from __future__ import annotations

import re
from typing import Any

_PRICE_RE = re.compile(r"(?:\$|₹|rs\.?|inr|usd)\s*[\d,]+(?:\.\d+)?", re.I)
_PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_NUM_RE = re.compile(r"[\d,]+(?:\.\d+)?")


def _blob(record: dict[str, Any]) -> str:
    return " ".join(
        str(record.get(k, "") or "")
        for k in ("title", "text", "metric", "metric_name", "metric_value", "publisher")
    ).lower()


def _first_price(blob: str) -> str | None:
    m = _PRICE_RE.search(blob)
    return m.group(0) if m else None


def _domain_profile(domain: str, industry: str) -> str:
    d = (domain or "").lower()
    ind = (industry or "").lower()
    if d in {"crm_automation", "b2b_saas", "saas_software"} or "saas" in ind:
        return "saas"
    if d in {"ecommerce_retail"} or "ecommerce" in ind or "retail" in ind:
        return "d2c"
    if d in {"automotive", "automotive_retail"} or "automotive" in ind:
        return "automotive"
    return "general"


def _field(value: Any, *, confidence: str = "unverified", source: str = "") -> dict[str, Any] | None:
    if value is None or value == "":
        return None
    return {"value": value, "confidence": confidence, "source": source[:120]}


def build_unit_economics_grounding(
    *,
    topic: str,
    industry: str,
    domain: str,
    evidence_records: list[dict[str, Any]] | None = None,
    strict_market_model: dict[str, Any] | None = None,
    diligence_pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    records = list(evidence_records or [])
    mm = strict_market_model or {}
    dp = diligence_pack or {}
    profile = _domain_profile(domain, industry)

    pricing_rows = []
    pricing_pack = dp.get("pricing_intelligence_pack")
    if isinstance(pricing_pack, dict):
        pricing_rows = list(pricing_pack.get("pricing_rows") or [])
    for row in pricing_rows[:6]:
        if isinstance(row, dict):
            records.append({
                "title": row.get("package", "pricing"),
                "metric": row.get("estimated_price_band", ""),
                "source_family": "pricing_reference",
                "publisher": row.get("source", "diligence_pack"),
            })

    known: dict[str, Any] = {}
    unknowns: list[str] = []

    prices: list[tuple[str, str]] = []
    for rec in records[:24]:
        if not isinstance(rec, dict):
            continue
        blob = _blob(rec)
        price = _first_price(blob)
        if price:
            prices.append((price, str(rec.get("publisher") or rec.get("title") or "")[:80]))

    headline = mm.get("headline") or {}
    if headline.get("tam_base_fmt") and "WITHHELD" not in str(headline.get("tam_base_fmt")).upper():
        known["tam_display"] = _field(headline.get("tam_base_fmt"), confidence="estimated", source="strict_market_model")
    else:
        unknowns.append("TAM not verified")

    if profile == "saas":
        if prices:
            known["pricing_reference"] = _field(prices[0][0], confidence="estimated", source=prices[0][1])
        else:
            unknowns.append("direct SaaS pricing unavailable")
        for key in ("ARPU", "CAC", "LTV", "churn", "gross_margin"):
            unknowns.append(f"{key} unverified")
    elif profile == "d2c":
        if len(prices) >= 1:
            known["retail_or_list_price"] = _field(prices[0][0], confidence="estimated", source=prices[0][1])
        if len(prices) >= 2:
            known["supplier_or_cogs_proxy"] = _field(prices[1][0], confidence="estimated", source=prices[1][1])
        if not prices:
            unknowns.append("retail anchor price unavailable")
        for key in ("COGS", "contribution_margin", "repeat_purchase_rate", "shipping_cost", "CAC"):
            if key == "COGS" and known.get("supplier_or_cogs_proxy"):
                continue
            unknowns.append(f"{key} unverified")
    elif profile == "automotive":
        if prices:
            known["observed_price_signal"] = _field(prices[0][0], confidence="estimated", source=prices[0][1])
        for key in ("avg_ticket_size", "labor_margin", "utilization", "parts_markup"):
            unknowns.append(f"{key} unverified")
    else:
        if prices:
            known["pricing_signal"] = _field(prices[0][0], confidence="estimated", source=prices[0][1])
        unknowns.append("domain unit economics unverified")

    funding = dp.get("funding_readiness_pack")
    if isinstance(funding, dict) and funding.get("figure_audit_table"):
        known["funding_figure_audit_present"] = _field(True, confidence="derived", source="funding_readiness_pack")

    # de-dupe unknowns preserve order
    seen: set[str] = set()
    financial_unknowns = []
    for item in unknowns:
        if item not in seen:
            seen.add(item)
            financial_unknowns.append(item)

    benchmark_pack: dict[str, Any] = {}
    if financial_unknowns or len(known) < 2:
        try:
            from iidatech.data.financial_benchmark_bank import build_benchmark_financial_pack, get_financial_benchmarks
            benchmark_pack = build_benchmark_financial_pack(domain)
            bench = get_financial_benchmarks(domain)
            if profile == "saas":
                for key, bench_key in (("CAC", "median_cac"), ("ARPU", "median_arpu"), ("churn", "median_churn_monthly"), ("gross_margin", "gross_margin")):
                    if any(key in u for u in financial_unknowns) and bench.get(bench_key) is not None:
                        known[key.lower()] = _field(bench[bench_key], confidence="benchmark-derived", source="financial_benchmark_bank")
                        financial_unknowns = [u for u in financial_unknowns if key not in u]
            elif profile == "d2c":
                for key, bench_key in (("COGS", "cogs_pct"), ("CAC", "median_cac"), ("contribution_margin", "gross_margin")):
                    if any(key in u for u in financial_unknowns) and bench.get(bench_key) is not None:
                        known[key.lower()] = _field(bench[bench_key], confidence="benchmark-derived", source="financial_benchmark_bank")
                        financial_unknowns = [u for u in financial_unknowns if key not in u]
            else:
                if any("CAC" in u for u in financial_unknowns) and bench.get("median_cac") is not None:
                    known["cac_benchmark"] = _field(bench["median_cac"], confidence="benchmark-derived", source="financial_benchmark_bank")
        except Exception:
            benchmark_pack = {}

    return {
        "domain_profile": profile,
        "known_values": {k: v for k, v in known.items() if v},
        "financial_unknowns": financial_unknowns[:12],
        "benchmark_financial_pack": benchmark_pack,
    }


def build_report_confidence_block(
    *,
    evidence_completeness: dict[str, Any] | None = None,
    unit_economics: dict[str, Any] | None = None,
    funding_readiness_pack: dict[str, Any] | None = None,
    final_audit: dict[str, Any] | None = None,
) -> dict[str, Any]:
    completeness = evidence_completeness if isinstance(evidence_completeness, dict) else {}
    ue = unit_economics if isinstance(unit_economics, dict) else {}
    funding = funding_readiness_pack if isinstance(funding_readiness_pack, dict) else {}
    audit = final_audit if isinstance(final_audit, dict) else {}

    comp_score = float(completeness.get("score") or 0)
    unknown_count = len(ue.get("financial_unknowns") or [])
    known_count = len(ue.get("known_values") or {})

    if comp_score >= 75:
        research = "High"
    elif comp_score >= 55:
        research = "Medium"
    else:
        research = "Low"

    if unknown_count <= 2 and known_count >= 3:
        financial = "Medium"
    elif unknown_count <= 5 and known_count >= 1:
        financial = "Low"
    else:
        financial = "Very Low"

    funding_ready = bool(funding.get("funding_ready") or audit.get("funding_ready"))
    audit_score = audit.get("market_style_score")
    if funding_ready and isinstance(audit_score, (int, float)) and float(audit_score) >= 8.0:
        investment = "High"
    elif isinstance(audit_score, (int, float)) and float(audit_score) >= 6.5:
        investment = "Medium"
    elif isinstance(audit_score, (int, float)) and float(audit_score) >= 4.5:
        investment = "Medium-Low"
    else:
        investment = "Low"

    return {
        "research_confidence": research,
        "financial_confidence": financial,
        "investment_confidence": investment,
        "evidence_completeness_score": comp_score,
        "financial_unknown_count": unknown_count,
        "financial_known_count": known_count,
        "display_lines": [
            f"Research Confidence: {research}",
            f"Financial Confidence: {financial}",
            f"Investment Confidence: {investment}",
        ],
    }