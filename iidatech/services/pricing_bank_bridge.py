"""Merge curated competitor pricing bank rows into diligence pricing pack."""
from __future__ import annotations

from statistics import median
from typing import Any

from iidatech.proprietary_data.loader import query_competitor_pricing
from iidatech.proprietary_data.industry_map import resolve_vertical


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def bank_row_to_sourced_pricing(row: dict[str, Any]) -> dict[str, Any]:
    company = str(row.get("company") or "").strip()
    plan = str(row.get("plan") or "Standard").strip()
    price = row.get("price")
    interval = str(row.get("billing_interval") or "per user/month")
    try:
        amount = float(price)
        monthly = f"${amount:g}/mo"
    except (TypeError, ValueError):
        monthly = str(price or "")
    url = str(row.get("source_url") or "").strip()
    return {
        "name": company,
        "vendor": company,
        "competitor": company,
        "plan_name": plan,
        "package": plan,
        "monthly_price": monthly,
        "estimated_price_band": monthly,
        "price_band": monthly,
        "pricing": monthly,
        "source": url,
        "url": url,
        "source_url": url,
        "source_family": "curated_pricing_bank",
        "source_type": "curated_pricing_bank",
        "verification_status": "verified_pricing_page",
        "evidence_backed": True,
        "trust_score": row.get("trust_score"),
        "bank_region": row.get("region"),
        "last_verified": row.get("last_verified"),
    }


def merge_pricing_bank_rows(
    pricing_pack: dict[str, Any],
    *,
    topic: str,
    industry: str,
    geography: str,
    domain: str | None = None,
    limit: int = 12,
) -> dict[str, Any]:
    """Fill pricing pack from proprietary bank when live harvest is thin."""
    pack = dict(pricing_pack or {})
    vertical = resolve_vertical(topic, industry, domain)
    bank_rows = query_competitor_pricing(topic, industry, geography, domain=vertical, limit=limit)

    sourced = list(_as_list(pack.get("sourced_pricing_records")))
    seen = {
        (
            str(r.get("vendor") or r.get("name") or "").lower(),
            str(r.get("plan_name") or r.get("package") or "").lower(),
        )
        for r in sourced
        if isinstance(r, dict)
    }

    added = 0
    for row in bank_rows:
        pricing_blob = str(row.get("price") or row.get("pricing") or "").lower()
        if "see official pricing page" in pricing_blob:
            continue
        converted = bank_row_to_sourced_pricing(row)
        key = (
            str(converted.get("vendor") or "").lower(),
            str(converted.get("plan_name") or "").lower(),
        )
        if key in seen:
            continue
        seen.add(key)
        sourced.append(converted)
        added += 1

    pack["sourced_pricing_records"] = sourced[:24]
    pack["pricing_bank_count"] = len(bank_rows)
    pack["pricing_bank_merged"] = added
    return pack


def median_verified_acv_monthly(rows: list[dict[str, Any]]) -> float | None:
    amounts: list[float] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        blob = " ".join(
            str(row.get(k) or "")
            for k in ("monthly_price", "estimated_price_band", "pricing", "price")
        )
        try:
            from iidatech.validation.pricing_validator import _extract_price_amount

            val = _extract_price_amount(blob)
            if val is not None and 5 <= val <= 2500:
                amounts.append(float(val))
        except Exception:
            continue
    if not amounts:
        return None
    return float(median(amounts))
