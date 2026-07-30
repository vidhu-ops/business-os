"""Resolve reporting currency from market / geography for research and sizing."""
from __future__ import annotations

from typing import Any

# (substring match in normalized geography, ISO code, symbol, display name)
_GEO_CURRENCIES: tuple[tuple[str, str, str, str], ...] = (
    ("india", "INR", "₹", "Indian Rupee"),
    ("united states", "USD", "$", "US Dollar"),
    ("u.s.", "USD", "$", "US Dollar"),
    ("usa", "USD", "$", "US Dollar"),
    ("united kingdom", "GBP", "£", "British Pound"),
    ("uk", "GBP", "£", "British Pound"),
    ("england", "GBP", "£", "British Pound"),
    ("germany", "EUR", "€", "Euro"),
    ("france", "EUR", "€", "Euro"),
    ("netherlands", "EUR", "€", "Euro"),
    ("european union", "EUR", "€", "Euro"),
    ("europe", "EUR", "€", "Euro"),
    ("uae", "AED", "AED", "UAE Dirham"),
    ("united arab emirates", "AED", "AED", "UAE Dirham"),
    ("dubai", "AED", "AED", "UAE Dirham"),
    ("singapore", "SGD", "S$", "Singapore Dollar"),
    ("australia", "AUD", "A$", "Australian Dollar"),
    ("canada", "CAD", "C$", "Canadian Dollar"),
    ("japan", "JPY", "¥", "Japanese Yen"),
    ("china", "CNY", "¥", "Chinese Yuan"),
    ("saudi arabia", "SAR", "SAR", "Saudi Riyal"),
    ("south africa", "ZAR", "R", "South African Rand"),
    ("brazil", "BRL", "R$", "Brazilian Real"),
    ("mexico", "MXN", "MX$", "Mexican Peso"),
    ("indonesia", "IDR", "Rp", "Indonesian Rupiah"),
    ("malaysia", "MYR", "RM", "Malaysian Ringgit"),
    ("philippines", "PHP", "₱", "Philippine Peso"),
    ("vietnam", "VND", "₫", "Vietnamese Dong"),
    ("nigeria", "NGN", "₦", "Nigerian Naira"),
    ("kenya", "KES", "KES", "Kenyan Shilling"),
    ("bangladesh", "BDT", "৳", "Bangladeshi Taka"),
    ("pakistan", "PKR", "Rs", "Pakistani Rupee"),
    ("sri lanka", "LKR", "Rs", "Sri Lankan Rupee"),
    ("new zealand", "NZD", "NZ$", "New Zealand Dollar"),
    ("switzerland", "CHF", "CHF", "Swiss Franc"),
    ("sweden", "SEK", "kr", "Swedish Krona"),
    ("norway", "NOK", "kr", "Norwegian Krone"),
    ("denmark", "DKK", "kr", "Danish Krone"),
    ("south korea", "KRW", "₩", "South Korean Won"),
    ("taiwan", "TWD", "NT$", "New Taiwan Dollar"),
    ("hong kong", "HKD", "HK$", "Hong Kong Dollar"),
    ("israel", "ILS", "₪", "Israeli Shekel"),
    ("turkey", "TRY", "₺", "Turkish Lira"),
    ("egypt", "EGP", "E£", "Egyptian Pound"),
    ("qatar", "QAR", "QAR", "Qatari Riyal"),
    ("kuwait", "KWD", "KWD", "Kuwaiti Dinar"),
)

_GLOBAL_MARKERS = frozenset({"global", "world", "worldwide", "international", ""})

_FORMAT_HINTS: dict[str, str] = {
    "INR": "Use INR (₹) as primary. Large values may use Cr (crores) or L (lakhs) with full figure in notes, e.g. ₹2,400 Cr.",
    "USD": "Use USD ($) as primary. Use $X.XB / $XM / $XK as appropriate.",
    "GBP": "Use GBP (£) as primary.",
    "EUR": "Use EUR (€) as primary.",
    "AED": "Use AED as primary for UAE market figures.",
    "SGD": "Use SGD (S$) as primary.",
    "AUD": "Use AUD (A$) as primary.",
    "CAD": "Use CAD (C$) as primary.",
    "JPY": "Use JPY (¥) as primary; prefer 億/万 or M/B with clarity in notes.",
}


def _normalize_geography(geography: str) -> str:
    raw = str(geography or "").strip().lower()
    if "—" in raw:
        raw = raw.split("—", 1)[0].strip()
    if " - " in raw:
        raw = raw.split(" - ", 1)[0].strip()
    if "," in raw and raw.count(",") == 1:
        # "Bengaluru, India" → prefer country token
        parts = [p.strip() for p in raw.split(",", 1)]
        if len(parts[1]) > len(parts[0]):
            raw = parts[1]
    return raw


def currency_for_geography(geography: str) -> dict[str, Any]:
    """Return reporting currency for a market label or country string."""
    geo = _normalize_geography(geography)
    if geo in _GLOBAL_MARKERS:
        return {
            "code": "USD",
            "symbol": "$",
            "name": "US Dollar",
            "geography": geography or "Global",
            "localized": False,
            "format_hint": _FORMAT_HINTS["USD"],
        }
    for needle, code, symbol, name in _GEO_CURRENCIES:
        if needle in geo:
            return {
                "code": code,
                "symbol": symbol,
                "name": name,
                "geography": geography,
                "localized": True,
                "format_hint": _FORMAT_HINTS.get(code, f"Use {code} ({symbol}) as primary for all TAM/SAM/SOM values."),
            }
    return {
        "code": "USD",
        "symbol": "$",
        "name": "US Dollar",
        "geography": geography,
        "localized": False,
        "format_hint": (
            f"No exact currency mapping for '{geography}'. Use USD ($) as primary and note local currency "
            "in sources when figures are country-specific."
        ),
    }


def currency_prompt_block(geography: str) -> str:
    """Prompt text instructing models to use the correct local currency."""
    cur = currency_for_geography(geography)
    lines = [
        "CURRENCY (mandatory for this report):",
        f"- Market / geography: {cur['geography']}",
        f"- Primary reporting currency: {cur['code']} ({cur['symbol']}) — {cur['name']}",
        f"- {cur['format_hint']}",
        "- Express TAM, SAM, SOM, ARPU, ACV, and revenue pool figures in this primary currency.",
        "- If a source quotes a different currency, convert using the source's FX rate when given, "
        "or show both (e.g. '₹2,400 Cr (~USD 290M)') with the source URL.",
        "- Do not mix currencies in the primary TAM/SAM/SOM table without conversion or explicit dual notation.",
    ]
    if cur["localized"]:
        lines.append(
            f"- This is a country-specific market ({cur['geography']}); do NOT default to USD unless the source is explicitly global USD."
        )
    return "\n".join(lines)
