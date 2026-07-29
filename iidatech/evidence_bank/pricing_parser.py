"""Pricing page parser for competitor intelligence (official + aggregator sources)."""
from __future__ import annotations

import re
from typing import Any

PRICE_RE = re.compile(
    r"(?:US\$|\$|₹|€|£)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
    r"|(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:/mo|per month|per user|/user|per seat|/seat|/month)"
    r"|(?:starting at|from)\s*(?:US\$|\$)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
    re.I,
)
PLAN_NAME_RE = re.compile(r"\b(Free|Starter|Basic|Essential|Professional|Pro|Enterprise|Business|Growth|Team)\b", re.I)


def _pricing_confidence(source_type: str) -> float:
    if source_type in {"official_pricing_page", "official_site", "pricing_page"}:
        return 0.98
    if source_type in {"review_platform", "g2", "capterra"}:
        return 0.85
    return 0.65


def parse_pricing_page(html_or_text: str, *, company: str = "", source_type: str = "official_site") -> dict[str, Any]:
    text = re.sub(r"<[^>]+>", " ", html_or_text or "")
    text = re.sub(r"\s+", " ", text).strip()
    tiers = extract_pricing_tiers(text, company=company)
    trial = extract_trial_freemium(text)
    setup = extract_setup_fee(text)
    confidence = _pricing_confidence(source_type)
    return {
        "company": company,
        "tiers": tiers,
        "trial_available": trial.get("trial_available"),
        "freemium": trial.get("freemium"),
        "setup_fee": setup,
        "pricing_confidence": confidence,
        "source_type": source_type,
    }


def extract_pricing_tiers(text: str, *, company: str = "") -> list[dict[str, Any]]:
    tiers: list[dict[str, Any]] = []
    seen_plans: set[str] = set()
    for match in PRICE_RE.finditer(text):
        amount = match.group(1) or match.group(2) or match.group(3)
        if not amount:
            continue
        before = text[max(0, match.start() - 60): match.start()]
        plan_matches = list(PLAN_NAME_RE.finditer(before))
        plan_name = plan_matches[-1].group(1) if plan_matches else "Standard"
        window = text[max(0, match.start() - 80): match.end() + 80]
        key = plan_name.lower()
        if key in seen_plans:
            continue
        amount_val = float(amount.replace(",", ""))
        if amount_val <= 0 and plan_name.lower() == "free":
            seen_plans.add(key)
            continue
        seen_plans.add(key)
        monthly = f"${amount.replace(',', '')}/mo"
        tiers.append({
            "company": company,
            "plan_name": plan_name,
            "monthly_price": monthly,
            "annual_price": "",
            "setup_fee": "",
            "trial_available": "trial" in window.lower() or "free" in window.lower(),
            "freemium": "free" in plan_name.lower(),
            "pricing_confidence": _pricing_confidence("official_site"),
        })
        if len(tiers) >= 6:
            break
    return tiers


def extract_trial_freemium(text: str) -> dict[str, bool]:
    lower = (text or "").lower()
    return {
        "trial_available": bool(re.search(r"\b(\d+\s*day|\d+\s*week)\s*(free\s*)?trial\b", lower)),
        "freemium": bool(re.search(r"\bfree (plan|tier|crm|forever)\b", lower)),
    }


def extract_setup_fee(text: str) -> str:
    match = re.search(
        r"setup fee[^$₹€£]{0,30}((?:US\$|\$|₹|€|£)\s*\d[\d,]*(?:\.\d{2})?)",
        text or "",
        re.I,
    )
    if match:
        return match.group(1).strip()
    if re.search(r"\bno setup fee\b", text or "", re.I):
        return "none"
    return ""
