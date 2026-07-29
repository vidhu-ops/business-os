"""Competitor / pricing evidence rules — block synthetic names from customer output."""
from __future__ import annotations

import re
from typing import Any

_VALIDATION = "VALIDATION REQUIRED"

_FAKE_COMPETITOR = re.compile(r"^competitor\s*[#:]?\s*\d+\b", re.I)
_SEED_VENDOR = re.compile(r"\bvendor\s*\d+\b", re.I)
_GENERIC_NAMES = frozenset(
    {
        "competitor",
        "market leader",
        "generic competitor",
        "placeholder competitor",
        "market aggregate",
        "unknown vendor",
    }
)
_SYNTHETIC_SOURCES = frozenset(
    {
        "",
        "preview",
        "synthetic",
        "manual_preview",
        "preview-mock",
        "preview band",
        "estimated",
        "unverified",
        "vendor pricing page",
    }
)

DEFAULT_COMPETITOR_EVIDENCE_GAPS = (
    "competitor names",
    "pricing pages",
    "review sources",
)

_LIVE_SERP_STATUSES = frozenset({"live_serp", "live_serp_discovery", "verified_pricing_page"})
_LIVE_SERP_FAMILIES = frozenset({"serp_pricing", "serp_intelligence", "serp_live_discovery"})


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _diligence(payload: dict[str, Any]) -> dict[str, Any]:
    return _as_dict(payload.get("diligence_pack"))


def has_live_competitor_evidence(payload: dict[str, Any]) -> bool:
    """True when live SERP competitor discovery populated the pack."""
    diligence = _diligence(payload)
    if int(diligence.get("live_competitor_count") or 0) >= 2:
        return True
    pack = _as_dict(diligence.get("competitor_intelligence_pack"))
    if pack.get("evidence_status") == "live_serp_discovery" and _as_list(pack.get("competitors")):
        return True
    serp = _as_dict(payload.get("serp_intelligence") or diligence.get("serp_intelligence"))
    competitors = [
        r
        for r in _as_list(serp.get("structured_records"))
        if isinstance(r, dict) and str(r.get("record_type") or "competitor").lower() == "competitor"
    ]
    return len(competitors) >= 2


def has_live_pricing_evidence(payload: dict[str, Any]) -> bool:
    diligence = _diligence(payload)
    pack = _as_dict(diligence.get("pricing_intelligence_pack"))
    sourced = [r for r in _as_list(pack.get("sourced_pricing_records")) if isinstance(r, dict)]
    if any(is_verified_pricing_row(r) or is_live_serp_evidence_row(r) for r in sourced):
        return True
    serp = _as_dict(payload.get("serp_intelligence") or diligence.get("serp_intelligence"))
    for row in _as_list(serp.get("structured_records")):
        if not isinstance(row, dict):
            continue
        price = str(row.get("price") or row.get("pricing") or "").strip()
        if price and price.lower() not in {"unknown", "n/a"}:
            return True
    return False


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def is_synthetic_competitor_name(name: Any) -> bool:
    raw = str(name or "").strip()
    if not raw:
        return True
    if _FAKE_COMPETITOR.search(raw):
        return True
    if _SEED_VENDOR.search(raw):
        return True
    if _norm(raw) in _GENERIC_NAMES:
        return True
    if raw.startswith("Tier ") and len(raw) > 5 and raw[5:6].isdigit():
        return True
    return False


def competitor_row_source(row: dict[str, Any]) -> str:
    return _norm(
        row.get("source")
        or row.get("url")
        or row.get("source_url")
        or row.get("official_url")
        or row.get("what_to_verify")
        or row.get("publisher")
    )


def is_live_serp_evidence_row(row: dict[str, Any]) -> bool:
    """True when row came from live SERP discovery (P0-2 bridge)."""
    if not isinstance(row, dict):
        return False
    status = _norm(row.get("verification_status") or row.get("evidence_status"))
    if status in _LIVE_SERP_STATUSES:
        return True
    if _norm(row.get("discovery_source")) == "serp_intelligence":
        return True
    family = _norm(row.get("source_family"))
    if family in _LIVE_SERP_FAMILIES:
        return True
    sources = row.get("sources")
    if isinstance(sources, list) and any("serp" in _norm(s) for s in sources):
        return True
    return False


def is_verified_competitor_row(row: dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    name = str(row.get("name") or row.get("competitor") or row.get("competitor_archetypes") or "").strip()
    if is_synthetic_competitor_name(name):
        return False
    if is_live_serp_evidence_row(row) and name:
        return True
    if row.get("official_url"):
        return True
    source = competitor_row_source(row)
    if source in _SYNTHETIC_SOURCES:
        return False
    if row.get("evidence_backed") is True and source not in _SYNTHETIC_SOURCES:
        return True
    if row.get("url") or row.get("source_url"):
        return True
    if source and source not in _SYNTHETIC_SOURCES and not source.startswith("preview"):
        return True
    trust = row.get("trust_score")
    try:
        trust_f = float(trust) if trust is not None else 0.0
    except (TypeError, ValueError):
        trust_f = 0.0
    return trust_f >= 0.85 and bool(row.get("source") or row.get("url"))


def is_verified_pricing_row(row: dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    competitor = str(row.get("name") or row.get("competitor") or row.get("vendor") or row.get("competitor_archetypes") or "").strip()
    if competitor and is_synthetic_competitor_name(competitor):
        return False
    band = str(
        row.get("estimated_price_band")
        or row.get("price_band")
        or row.get("price")
        or row.get("pricing")
        or row.get("package")
        or ""
    )
    if _VALIDATION in band or _norm(band) == _norm(_VALIDATION):
        return False
    low_band = band.lower()
    if any(token in low_band for token in ("billion", "million", "market size", "cagr", "tam")):
        if "/mo" not in low_band and "per month" not in low_band and "per user" not in low_band:
            return False
    try:
        from iidatech.validation.pricing_validator import _extract_price_amount

        amount = _extract_price_amount(band)
        if amount is not None and amount > 2500:
            return False
    except Exception:
        pass
    if is_live_serp_evidence_row(row) and band:
        return True
    source = competitor_row_source(row)
    if source in _SYNTHETIC_SOURCES:
        return False
    if row.get("url") or row.get("source_url"):
        return True
    if row.get("evidence_backed") is True:
        return True
    return bool(source and source not in _SYNTHETIC_SOURCES)


def compute_competitor_trust_score(row: dict[str, Any]) -> float:
    """Derive per-row trust from source signals instead of uniform seed-bank defaults."""
    from urllib.parse import urlparse

    engine_blob = " ".join(
        str(row.get(key) or "")
        for key in ("source_engine", "source_type", "discovered_via", "verification_status")
    ).lower()
    if "perplexity" in engine_blob:
        score = 0.84
        if str(row.get("source_url") or row.get("url") or "").startswith("http"):
            score += 0.04
        if str(row.get("pricing") or row.get("price") or "").strip():
            score += 0.03
        if str(row.get("verification_status") or "").lower() in {"perplexity_live", "firecrawl_verified"}:
            score += 0.02
        return round(min(0.93, score), 2)

    url = str(row.get("source_url") or row.get("source") or row.get("url") or "").lower()
    host = urlparse(url).netloc.lower() if url.startswith("http") else url

    _KNOWN_HOST_TRUST: dict[str, float] = {
        "hubspot.com": 0.90,
        "salesforce.com": 0.89,
        "pipedrive.com": 0.88,
        "zoho.com": 0.88,
        "freshworks.com": 0.87,
        "monday.com": 0.86,
        "cerave.com": 0.84,
        "theordinary.com": 0.83,
        "minimalist.com": 0.82,
        "plumgoodness.com": 0.81,
        "curvedental.com": 0.85,
        "carestack.com": 0.84,
        "dentally.com": 0.83,
        "dentrix.com": 0.82,
        "opendental.com": 0.81,
    }
    score: float | None = None
    for host_key, host_trust in _KNOWN_HOST_TRUST.items():
        if host_key in host:
            score = host_trust
            break

    if score is None:
        if any(h in host for h in ("g2.com", "capterra.com", "trustpilot.com", "trustradius.com")):
            score = 0.78
        elif any(h in host for h in ("gartner.com", "forrester.com", "idc.com")):
            score = 0.86
        elif "pricing" in url or "/price" in url:
            score = 0.87
        else:
            try:
                from iidatech.validation.source_validator import classify_source_tier

                tier = classify_source_tier(row)
                score = {1: 0.88, 2: 0.80, 3: 0.68, 4: 0.55}.get(tier, 0.72)
            except Exception:
                score = 0.72

    region = str(row.get("region") or "").strip().lower()
    if region == "india":
        score += 0.01

    seeded = row.get("trust_score")
    try:
        seeded_f = float(seeded) if seeded is not None else None
    except (TypeError, ValueError):
        seeded_f = None
    if seeded_f is not None and seeded_f not in {0.92, 0.75}:
        score = max(score, seeded_f)

    return round(min(0.93, max(0.55, score)), 2)


def filter_verified_competitor_matrix(matrix: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in matrix:
        if not isinstance(row, dict):
            continue
        if not is_verified_competitor_row(row):
            continue
        name = str(row.get("name") or row.get("competitor") or "").strip()
        key = _norm(name)
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def filter_verified_pricing_rows(rows: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        if not isinstance(row, dict) or not is_verified_pricing_row(row):
            continue
        competitor = _norm(row.get("name") or row.get("competitor") or row.get("vendor") or "")
        plan = _norm(row.get("plan") or row.get("plan_name") or row.get("package") or "")
        price = _norm(
            row.get("estimated_price_band")
            or row.get("price_band")
            or row.get("price")
            or row.get("pricing")
            or ""
        )
        key = f"{competitor}|{plan}|{price}"
        if key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def build_competitor_evidence_gap(*, extra: list[str] | None = None) -> dict[str, Any]:
    gaps = list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
    if extra:
        for item in extra:
            if item and item not in gaps:
                gaps.append(item)
    return {
        "status": "evidence_gap",
        "missing_evidence": gaps,
        "competitor_count": 0,
        "market_leaders": [],
        "matrix": [],
    }


def competitor_evidence_gap_markdown(gaps: list[str] | None = None) -> str:
    items = gaps or list(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
    lines = ["**Missing evidence:**", ""]
    for item in items:
        lines.append(f"- {item}")
    return "\n".join(lines)