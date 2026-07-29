"""Dataset-first research analysts using proprietary JSONL banks."""
from __future__ import annotations

import re
from statistics import mean, median
from typing import Any

from iidatech.proprietary_data.loader import (
    query_benchmarks,
    query_buyer_voice,
    query_supplier_costs,
)
from iidatech.validation.competitor_evidence import compute_competitor_trust_score, is_synthetic_competitor_name

PAIN_BUCKETS = ("price", "trust", "onboarding", "service", "delivery", "quality")
_VALIDATION = "VALIDATION REQUIRED"


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _ctx_fields(ctx: dict[str, Any]) -> tuple[str, str, str, dict, dict, list]:
    return (
        str(ctx.get("topic") or ""),
        str(ctx.get("industry") or ""),
        str(ctx.get("geography") or "Global"),
        _as_dict(ctx.get("report")),
        _as_dict(ctx.get("proprietary")),
        _as_list(ctx.get("records")),
    )


def _float(v: Any) -> float | None:
    if v in (None, "", "WITHHELD"):
        return None
    try:
        return float(str(v).replace(",", "").replace("$", ""))
    except (TypeError, ValueError):
        return None


def _benchmark_map(rows: list[dict]) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in rows:
        metric = str(row.get("metric") or "").strip().lower()
        val = _float(row.get("value"))
        if metric and val is not None and metric not in out:
            out[metric] = val
    return out


def _live_competitor_matrix_from_report(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Build competitor matrix from Perplexity serp_intelligence only (no seed bank)."""
    diligence = _as_dict(report.get("diligence_pack"))
    serp = _as_dict(report.get("serp_intelligence")) or _as_dict(diligence.get("serp_intelligence"))
    matrix: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in _as_list(serp.get("structured_records")):
        if not isinstance(row, dict):
            continue
        if str(row.get("record_type") or "").lower() != "competitor":
            continue
        name = str(row.get("name") or row.get("competitor") or "").strip()
        if not name or is_synthetic_competitor_name(name):
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        price_text = str(row.get("price") or row.get("pricing") or "").strip()
        matrix.append(
            {
                "name": name[:80],
                "pricing": price_text or None,
                "price": price_text or None,
                "source": row.get("source_url") or row.get("url"),
                "source_url": row.get("source_url") or row.get("url"),
                "source_engine": row.get("source_engine"),
                "source_type": row.get("source_type"),
                "discovered_via": row.get("discovered_via"),
                "verification_status": row.get("verification_status"),
                "positioning": row.get("positioning"),
                "trust_score": compute_competitor_trust_score(row),
            }
        )
    return matrix


def competitor_analyst_from_datasets(ctx: dict[str, Any]) -> dict[str, Any]:
    topic, industry, geography, report, _proprietary, _records = _ctx_fields(ctx)
    matrix = _live_competitor_matrix_from_report(report)

    prices: list[float] = []
    for row in matrix:
        price = _float(row.get("price"))
        if price is not None and price > 0:
            prices.append(price)
        else:
            amount = _float(_extract_price_number(str(row.get("pricing") or "")))
            if amount is not None and amount > 0:
                prices.append(amount)

    matrix.sort(key=lambda r: float(r.get("trust_score") or 0), reverse=True)
    leaders = [r["name"] for r in matrix[:3]]
    weak = [r["name"] for r in matrix if float(r.get("trust_score") or 0) < 0.75][:5]

    pricing_bands: dict[str, Any] = {"low": None, "avg": None, "premium": None}
    if prices:
        prices_sorted = sorted(prices)
        pricing_bands = {
            "low": round(prices_sorted[0], 2),
            "avg": round(mean(prices), 2),
            "premium": round(prices_sorted[-1], 2),
            "median": round(median(prices), 2),
            "sample_size": len(prices),
        }

    gaps: list[str] = []
    if len(matrix) < 3:
        gaps.append("Need 3+ live Perplexity competitors in serp_intelligence")
    if len(prices) < 2:
        gaps.append("Need 2+ Firecrawl- or Perplexity-validated price points")
    feature_gap = []
    if matrix:
        plans = {str(r.get("plan") or "").lower() for r in matrix}
        if "starter" in " ".join(plans) and "professional" not in " ".join(plans):
            feature_gap.append("Mid-tier plan coverage missing vs market leaders")

    return {
        "competitor_matrix": matrix[:15],
        "competitor_count": len(matrix),
        "pricing_bands": pricing_bands,
        "market_leaders": leaders,
        "weak_competitors": weak,
        "market_gaps": gaps,
        "avg_pricing": pricing_bands.get("avg"),
        "premium_pricing": pricing_bands.get("premium"),
        "low_cost_pricing": pricing_bands.get("low"),
        "feature_gap": feature_gap,
        "dataset_rows_used": len(matrix),
        "confidence": "high" if len(matrix) >= 3 and len(prices) >= 2 else "low",
        "source": "perplexity_serp_intelligence",
    }


def _extract_price_number(text: str) -> float | None:
    return _float(re.sub(r"[^\d.]", "", text.split("/")[0]) if text else None)


def customer_analyst_from_datasets(ctx: dict[str, Any]) -> dict[str, Any]:
    topic, industry, geography, _report, proprietary, _records = _ctx_fields(ctx)
    voice_rows = proprietary.get("buyer_voice") or query_buyer_voice(topic, industry, geography, limit=120)

    buckets: dict[str, list[dict]] = {k: [] for k in PAIN_BUCKETS}
    for row in voice_rows:
        cat = str(row.get("pain_category") or "").lower()
        if cat not in buckets:
            for bucket in PAIN_BUCKETS:
                if bucket in cat:
                    cat = bucket
                    break
            else:
                cat = "quality"
        buckets.setdefault(cat, []).append(row)

    top_pains: list[dict[str, Any]] = []
    top_desires: list[dict[str, Any]] = []
    for bucket, rows in buckets.items():
        if not rows:
            continue
        freq = sum(int(r.get("frequency") or 1) for r in rows)
        sample = str(rows[0].get("complaint") or "")[:200]
        top_pains.append({"category": bucket, "frequency": freq, "sample": sample})
        top_desires.append({
            "category": bucket,
            "desired_outcome": rows[0].get("desired_outcome"),
            "frequency": freq,
        })
    top_pains.sort(key=lambda x: x["frequency"], reverse=True)
    top_desires.sort(key=lambda x: x["frequency"], reverse=True)

    wtp_distribution: dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0}
    objections: dict[str, int] = {}
    for row in voice_rows:
        wtp = str(row.get("willingness_to_pay_signal") or "").lower()
        sent = _float(row.get("sentiment_score")) or 0.0
        if "pay" in wtp or "budget" in wtp:
            if sent >= 0:
                wtp_distribution["positive"] += 1
            elif sent < -0.3:
                wtp_distribution["negative"] += 1
            else:
                wtp_distribution["neutral"] += 1
        complaint = str(row.get("complaint") or "")[:120]
        if complaint:
            objections[complaint] = objections.get(complaint, 0) + int(row.get("frequency") or 1)

    dominant_objections = [
        {"objection": k, "count": v}
        for k, v in sorted(objections.items(), key=lambda kv: kv[1], reverse=True)[:8]
    ]

    return {
        "top_pains": top_pains[:8],
        "top_desires": top_desires[:8],
        "wtp_distribution": wtp_distribution,
        "dominant_objections": dominant_objections,
        "pain_clusters": top_pains[:8],
        "buyer_voice_rows_used": len(voice_rows),
        "confidence": "high" if len(voice_rows) >= 6 and top_pains else "low",
        "source": "proprietary_datasets",
    }


def financial_analyst_from_datasets(ctx: dict[str, Any]) -> dict[str, Any]:
    topic, industry, geography, report, proprietary, _records = _ctx_fields(ctx)
    benchmarks = proprietary.get("benchmarks") or query_benchmarks(topic, industry, geography, limit=80)
    suppliers = proprietary.get("supplier_costs") or query_supplier_costs(topic, industry, geography, limit=40)
    # competitor_pricing bank deprecated for scoring — financial uses benchmarks/model only
    pricing: list[dict[str, Any]] = []

    bench = _benchmark_map(benchmarks)
    diligence = _as_dict(report.get("diligence_pack"))
    bottom_up = _as_dict(diligence.get("bottom_up_market_calculation"))
    model = _as_dict(report.get("quantitative_model"))
    headline = _as_dict(model.get("headline"))

    buyer_count = _float(bottom_up.get("buyer_count") or model.get("buyer_count") or bench.get("buyer_count"))
    avg_ticket = _float(bottom_up.get("avg_ticket") or model.get("avg_ticket") or bench.get("avg_ticket"))
    frequency = _float(bottom_up.get("purchase_frequency") or model.get("purchase_frequency") or bench.get("purchase_frequency")) or 1.0

    market_sizes: dict[str, Any] = {
        "tam": {"value": None, "computed": False, "denominators": {}},
        "sam": {"value": None, "computed": False, "denominators": {}},
        "som": {"value": None, "computed": False, "denominators": {}},
    }

    if buyer_count and avg_ticket:
        tam_val = buyer_count * avg_ticket * frequency
        market_sizes["tam"] = {
            "value": round(tam_val, 2),
            "computed": True,
            "denominators": {
                "buyer_count": buyer_count,
                "avg_ticket": avg_ticket,
                "purchase_frequency": frequency,
            },
            "formula": "buyer_count * avg_ticket * purchase_frequency",
        }
        sam_share = _float(headline.get("sam_share") or bench.get("sam_share")) or 0.15
        som_share = _float(headline.get("som_share") or bench.get("som_share")) or 0.03
        market_sizes["sam"] = {
            "value": round(tam_val * sam_share, 2),
            "computed": True,
            "denominators": {"tam": tam_val, "sam_share": sam_share},
        }
        market_sizes["som"] = {
            "value": round(tam_val * som_share, 2),
            "computed": True,
            "denominators": {"tam": tam_val, "som_share": som_share},
        }
    else:
        for key in ("tam", "sam", "som"):
            market_sizes[key]["reason"] = _VALIDATION

    cac = _float(bench.get("cac"))
    ltv = _float(bench.get("ltv"))
    margin = _float(bench.get("gross margin"))
    contribution = _float(bench.get("contribution margin"))
    payback = (cac / (avg_ticket * (margin or 0) / 100)) if cac and avg_ticket and margin else None

    unit_economics = {
        "cac": cac,
        "ltv": ltv,
        "margin": margin,
        "contribution_margin": contribution,
        "payback_months": round(payback, 2) if payback else None,
        "ltv_cac_ratio": round(ltv / cac, 2) if ltv and cac else None,
    }

    sell_prices = [_float(r.get("price")) for r in pricing]
    sell_prices = [p for p in sell_prices if p is not None and p > 0]
    cogs_samples = []
    for row in suppliers[:12]:
        unit = _float(row.get("unit_cost")) or 0.0
        pack = _float(row.get("packaging_cost")) or 0.0
        ship = _float(row.get("shipping_cost")) or 0.0
        cogs_samples.append(unit + pack + ship)

    invalid_business_model = False
    invalid_reasons: list[str] = []
    if sell_prices and cogs_samples:
        avg_sell = mean(sell_prices)
        avg_cogs = mean(cogs_samples)
        if avg_cogs > avg_sell:
            invalid_business_model = True
            invalid_reasons.append("COGS exceeds average selling price from dataset anchors")

    impossible: list[str] = []
    if cac and ltv and ltv < cac:
        impossible.append("LTV below CAC")
    if margin is not None and margin < 0:
        impossible.append("negative_margin")

    return {
        "tam": market_sizes["tam"],
        "sam": market_sizes["sam"],
        "som": market_sizes["som"],
        "market_sizes": market_sizes,
        "unit_economics": unit_economics,
        "invalid_business_model": invalid_business_model,
        "invalid_business_model_reasons": invalid_reasons,
        "impossible_economics": impossible,
        "benchmark_rows_used": len(benchmarks),
        "supplier_rows_used": len(suppliers),
        "confidence": "high" if market_sizes["tam"].get("computed") and not invalid_business_model else "low",
        "source": "proprietary_datasets",
    }


def strategy_analyst_from_datasets(
    ctx: dict[str, Any],
    comp: dict[str, Any],
    cust: dict[str, Any],
    fin: dict[str, Any],
) -> dict[str, Any]:
    topic, industry, geography, _report, _proprietary, _records = _ctx_fields(ctx)

    top_pain = (cust.get("top_pains") or [{}])[0].get("category") if cust.get("top_pains") else ""
    top_desire = (cust.get("top_desires") or [{}])[0].get("desired_outcome") if cust.get("top_desires") else ""
    leaders = comp.get("market_leaders") or []
    gaps = comp.get("market_gaps") or []
    feature_gap = comp.get("feature_gap") or []

    evidence_bits: list[str] = []
    if top_pain:
        evidence_bits.append(f"buyer pain: {top_pain}")
    if leaders:
        evidence_bits.append(f"leaders: {', '.join(leaders[:3])}")
    if comp.get("low_cost_pricing") is not None:
        evidence_bits.append(f"low-cost anchor: {comp.get('low_cost_pricing')}")

    if comp.get("competitor_count", 0) >= 5 and top_pain:
        best_wedge = f"Underserved {top_pain} segment within {topic}"
    elif comp.get("competitor_count", 0) >= 2:
        best_wedge = f"Workflow wedge on {top_pain or 'integration'} for {industry}"
    else:
        best_wedge = f"Define narrow category for {topic} before scaling"

    positioning = {
        "statement": f"For {geography} {industry} buyers, solve {top_pain or 'core workflow pain'} better than {leaders[0] if leaders else 'incumbents'}",
        "evidence": evidence_bits[:5],
    }

    launch_strategy = []
    if geography and geography.lower() not in {"", "global", "worldwide"}:
        launch_strategy.append(f"Geo-first GTM in {geography} with local pricing currency")
    if leaders:
        launch_strategy.append(f"Competitive contrast against {leaders[0]} using validated pricing pages")
    if top_desire:
        launch_strategy.append(f"Lead with outcome: {top_desire}")

    first_revenue_path = []
    if fin.get("tam", {}).get("computed"):
        first_revenue_path.append("Paid pilot / implementation sprint while product matures")
    if cust.get("wtp_distribution", {}).get("positive", 0) > 0:
        first_revenue_path.append("Tiered subscription anchored to dataset pricing bands")
    if not first_revenue_path:
        first_revenue_path.append(_VALIDATION)

    moat_strategy = []
    if feature_gap:
        moat_strategy.extend(feature_gap[:2])
    if fin.get("unit_economics", {}).get("ltv_cac_ratio"):
        moat_strategy.append("Retention-led expansion once LTV/CAC validated in cohort")
    if not moat_strategy:
        moat_strategy.append("Evidence-backed vertical workflow depth")

    return {
        "best_wedge": best_wedge,
        "positioning": positioning,
        "launch_strategy": launch_strategy[:5],
        "first_revenue_path": first_revenue_path[:4],
        "moat_strategy": moat_strategy[:5],
        "wedge": best_wedge,
        "gtm": launch_strategy[:5],
        "fast_revenue_path": first_revenue_path[:4],
        "confidence": "medium" if evidence_bits else "low",
        "source": "proprietary_datasets",
        "validated_evidence_only": True,
    }