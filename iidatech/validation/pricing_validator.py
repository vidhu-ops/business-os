"""Strict pricing row validation for IIDATECH."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from iidatech.validation.source_validator import TIER_CONTEXT, TIER_OFFICIAL, classify_source_tier

PRICE_RE = re.compile(
    r"(?:US\$|\$|₹|€|£|INR)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
    r"|(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:/mo|per month|per user|/user|/month)",
    re.I,
)
INTERVAL_RE = re.compile(r"(/mo|per month|per user|/user|per seat|/seat|annual|yearly|/yr)", re.I)

DOMAIN_PRICE_BANDS: dict[str, tuple[float, float]] = {
    "crm_automation": (5, 500),
    "b2b_saas": (5, 500),
    "d2c_skincare": (1, 5000),
    "automotive_retail": (10, 50000),
    "default": (1, 100000),
}


def _extract_price_amount(text: str) -> float | None:
    for match in PRICE_RE.finditer(text or ""):
        raw = match.group(1) or match.group(2)
        if raw:
            try:
                return float(raw.replace(",", ""))
            except ValueError:
                continue
    return None


def _trusted_domain(url: str, tier: int) -> bool:
    if tier <= 2:
        return True
    host = urlparse(str(url or "")).netloc.lower()
    return bool(host) and tier < TIER_CONTEXT


def validate_pricing_row(row: dict[str, Any], *, domain: str = "default") -> dict[str, Any]:
    blob = " ".join(
        str(row.get(k) or "")
        for k in ("plan_name", "package", "monthly_price", "estimated_price_band", "pricing", "title", "text", "metric_value", "vendor", "name")
    )
    url = str(row.get("url") or row.get("source_url") or row.get("source") or "")
    tier = classify_source_tier(row)
    plan = str(row.get("plan_name") or row.get("package") or row.get("vendor") or row.get("name") or "").strip()
    amount = _extract_price_amount(blob)
    interval = bool(INTERVAL_RE.search(blob)) or "/mo" in blob.lower()
    official = str(row.get("verification_status") or row.get("source_family") or "").lower()
    if official in {"verified_pricing_page", "official_pricing_page"} and url.startswith("http"):
        tier = min(tier, TIER_OFFICIAL)
    trusted = _trusted_domain(url, tier) or official == "verified_pricing_page"
    lo, hi = DOMAIN_PRICE_BANDS.get(domain, DOMAIN_PRICE_BANDS["default"])
    realistic = amount is None or (lo <= amount <= hi)
    valid = bool(plan) and amount is not None and interval and trusted and realistic and tier < TIER_CONTEXT
    reasons = []
    if not plan:
        reasons.append("missing_plan_name")
    if amount is None:
        reasons.append("missing_numeric_price")
    if not interval:
        reasons.append("missing_billing_interval")
    if not trusted:
        reasons.append("untrusted_domain")
    if not realistic:
        reasons.append("price_outside_domain_range")
    if tier >= TIER_CONTEXT:
        reasons.append("tier3_cannot_support_pricing")
    return {
        "valid": valid,
        "reasons": reasons,
        "tier": tier,
        "amount": amount,
        "plan_name": plan,
    }


def filter_valid_pricing_rows(rows: list[dict[str, Any]], *, domain: str = "default") -> dict[str, Any]:
    valid_rows, rejected = [], []
    for row in rows:
        if not isinstance(row, dict):
            continue
        result = validate_pricing_row(row, domain=domain)
        if result["valid"]:
            valid_rows.append({**row, "_pricing_validation": result})
        else:
            rejected.append({**row, "_pricing_validation": result})
    return {"valid": valid_rows, "rejected": rejected, "valid_count": len(valid_rows), "rejected_count": len(rejected)}