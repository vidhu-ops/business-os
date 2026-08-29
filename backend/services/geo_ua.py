"""Geo / device helpers for first-party web analytics."""
from __future__ import annotations

import hashlib
import os
import re
from typing import Any
from urllib.parse import unquote, urlparse

from fastapi import Request

BOT_MARKERS = (
    "bot",
    "spider",
    "crawler",
    "preview",
    "facebookexternalhit",
    "slackbot",
    "whatsapp",
    "telegram",
    "discordbot",
    "linkedinbot",
    "twitterbot",
    "applebot",
    "semrush",
    "ahrefs",
    "pingdom",
    "uptimerobot",
    "headlesschrome",
    "bytespider",
    "gptbot",
    "claudebot",
    "perplexitybot",
)

SEARCH_HOSTS = ("google.", "bing.", "duckduckgo.", "yahoo.", "yandex.", "baidu.", "ecosia.", "brave.")
SOCIAL_HOSTS = (
    "facebook.",
    "instagram.",
    "twitter.",
    "t.co",
    "x.com",
    "linkedin.",
    "youtube.",
    "youtu.be",
    "reddit.",
    "whatsapp.",
    "telegram.",
    "pinterest.",
    "tiktok.",
    "threads.net",
    "lnkd.in",
)

COUNTRY_NAMES: dict[str, str] = {
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "AE": "United Arab Emirates",
    "SG": "Singapore",
    "AU": "Australia",
    "CA": "Canada",
    "DE": "Germany",
    "FR": "France",
    "NL": "Netherlands",
    "IE": "Ireland",
    "JP": "Japan",
    "KR": "South Korea",
    "CN": "China",
    "BR": "Brazil",
    "MX": "Mexico",
    "ZA": "South Africa",
    "NG": "Nigeria",
    "KE": "Kenya",
    "PK": "Pakistan",
    "BD": "Bangladesh",
    "LK": "Sri Lanka",
    "NP": "Nepal",
    "ID": "Indonesia",
    "MY": "Malaysia",
    "TH": "Thailand",
    "VN": "Vietnam",
    "PH": "Philippines",
    "SA": "Saudi Arabia",
    "QA": "Qatar",
    "KW": "Kuwait",
    "IL": "Israel",
    "TR": "Turkey",
    "ES": "Spain",
    "IT": "Italy",
    "PT": "Portugal",
    "SE": "Sweden",
    "NO": "Norway",
    "DK": "Denmark",
    "FI": "Finland",
    "PL": "Poland",
    "CH": "Switzerland",
    "AT": "Austria",
    "BE": "Belgium",
    "NZ": "New Zealand",
    "HK": "Hong Kong",
    "TW": "Taiwan",
    "RU": "Russia",
    "UA": "Ukraine",
    "AR": "Argentina",
    "CL": "Chile",
    "CO": "Colombia",
    "EG": "Egypt",
    "GH": "Ghana",
    "TZ": "Tanzania",
    "UG": "Uganda",
}

_ID_RE = re.compile(r"^[A-Za-z0-9_-]{8,80}$")


def valid_id(value: str | None) -> bool:
    return bool(value) and bool(_ID_RE.match(str(value).strip()))


def is_bot_ua(ua: str) -> bool:
    low = (ua or "").lower()
    if not low:
        return False
    return any(marker in low for marker in BOT_MARKERS)


def parse_ua(ua: str) -> dict[str, str]:
    low = (ua or "").lower()
    device = "desktop"
    if "ipad" in low or "tablet" in low:
        device = "tablet"
    elif "mobi" in low or ("android" in low and "mobile" in low) or "iphone" in low:
        device = "mobile"
    elif "android" in low:
        device = "mobile"

    os_name = "Unknown"
    if "iphone" in low or "ipad" in low or "ios" in low:
        os_name = "iOS"
    elif "android" in low:
        os_name = "Android"
    elif "mac os" in low or "macintosh" in low:
        os_name = "macOS"
    elif "windows" in low:
        os_name = "Windows"
    elif "cros" in low:
        os_name = "Chrome OS"
    elif "linux" in low:
        os_name = "Linux"

    browser = "Unknown"
    if "edg/" in low or "edgios" in low:
        browser = "Edge"
    elif "opr/" in low or "opera" in low:
        browser = "Opera"
    elif "samsungbrowser" in low:
        browser = "Samsung Internet"
    elif "firefox/" in low or "fxios" in low:
        browser = "Firefox"
    elif "crios" in low or ("chrome/" in low and "chromium" not in low):
        browser = "Chrome"
    elif "safari/" in low and "chrome" not in low and "crios" not in low:
        browser = "Safari"

    return {"device": device, "os": os_name, "browser": browser}


def host_from_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlparse(raw if "://" in raw else f"https://{raw}")
        return (parsed.hostname or "").lower().removeprefix("www.")
    except Exception:
        return ""


def classify_source(*, referrer: str, utm_source: str, utm_medium: str, landing_host: str = "") -> str:
    medium = (utm_medium or "").strip().lower()
    source = (utm_source or "").strip().lower()
    if medium in {"cpc", "ppc", "paid", "paidsearch", "paidsocial", "ads"}:
        return "paid"
    if medium in {"email", "e-mail", "newsletter"}:
        return "email"
    if source in {"google", "bing", "duckduckgo"} or medium == "organic":
        return "organic"
    if source in {"facebook", "instagram", "linkedin", "twitter", "x", "youtube", "reddit"}:
        return "social"
    host = host_from_url(referrer)
    if not host:
        return "direct"
    if landing_host and (host == landing_host or host.endswith(f".{landing_host}")):
        return "internal"
    if any(token in host for token in SEARCH_HOSTS):
        return "organic"
    if any(token in host for token in SOCIAL_HOSTS):
        return "social"
    return "referral"


def _header(request: Request, *names: str) -> str:
    for name in names:
        value = request.headers.get(name)
        if value:
            return unquote(str(value)).strip()
    return ""


def client_ip(request: Request) -> str:
    forwarded = _header(request, "cf-connecting-ip", "true-client-ip", "x-real-ip")
    if forwarded:
        return forwarded.split(",")[0].strip()
    xff = _header(request, "x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return ""


def hash_ip(ip: str) -> str:
    raw = (ip or "").strip()
    if not raw:
        return ""
    secret = (os.getenv("JWT_SECRET") or "iidatech-analytics").encode("utf-8")
    return hashlib.sha256(secret + b":" + raw.encode("utf-8")).hexdigest()[:32]


def mask_ip(ip: str) -> str:
    raw = (ip or "").strip()
    if not raw:
        return ""
    if ":" in raw:
        parts = raw.split(":")
        return ":".join(parts[:3] + ["xxxx"])
    parts = raw.split(".")
    if len(parts) == 4:
        return ".".join(parts[:3] + ["x"])
    return ""


def geo_from_request(request: Request, client: dict[str, Any] | None = None) -> dict[str, str]:
    client = client if isinstance(client, dict) else {}
    country = (
        _header(
            request,
            "cf-ipcountry",
            "cf-ip-country",
            "x-vercel-ip-country",
            "cloudfront-viewer-country",
            "x-country-code",
        )
        .upper()
        .replace("XX", "")
        .replace("T1", "")
    )
    city = _header(request, "cf-ipcity", "cf-ip-city", "x-vercel-ip-city")
    region = _header(
        request,
        "cf-region",
        "cf-ipregion",
        "x-vercel-ip-country-region",
        "cloudfront-viewer-country-region-name",
    )
    region_code = _header(request, "cf-region-code", "x-vercel-ip-country-region")
    postal = _header(request, "cf-postal-code", "x-vercel-ip-postal-code")
    timezone = (
        str(client.get("timezone") or "").strip()
        or _header(request, "cf-timezone", "x-vercel-ip-timezone")
    )
    continent = _header(request, "cf-ipcontinent", "x-vercel-ip-continent")
    ip = client_ip(request)
    place_parts = [part for part in (city, region, COUNTRY_NAMES.get(country, country)) if part]
    return {
        "country": country[:2],
        "country_name": COUNTRY_NAMES.get(country, country),
        "city": city[:80],
        "region": region[:80],
        "region_code": region_code[:16],
        "postal": postal[:16],
        "continent": continent[:8],
        "timezone": timezone[:64],
        "place": ", ".join(place_parts)[:160],
        "ip_hash": hash_ip(ip),
        "ip_masked": mask_ip(ip),
        "language": (
            str(client.get("language") or "").strip()
            or (request.headers.get("accept-language") or "").split(",")[0].strip()
        )[:32],
    }
