"""Rank and filter SerpAPI competitor noise into named vendors."""
from __future__ import annotations

import re
from typing import Any

from iidatech.evidence_bank.google_competitor_discovery import (
    KNOWN_LEADERS,
    is_valid_competitor_display_name,
    normalize_competitor_name,
)


def parse_vendor_from_review_url(url: str, title: str = "") -> str | None:
    low = str(url or "").lower()
    if "g2.com/products/" in low:
        slug = low.split("/products/", 1)[1].split("/")[0].strip()
        if slug and slug not in {"compare", "categories"}:
            return _slug_to_brand(slug)
    if "trustradius.com/products/" in low:
        slug = low.split("/products/", 1)[1].split("/")[0].strip()
        if slug:
            return _slug_to_brand(slug)
    if "capterra.com" in low:
        m = re.search(r"/([^/]+)/reviews?", low)
        if m:
            return _slug_to_brand(m.group(1))
    for leader in re.findall(r"([A-Z][A-Za-z0-9&'.-]{2,30})\s+(?:CRM|Reviews?|Pricing)", title or ""):
        if is_valid_competitor_display_name(leader):
            return leader.strip()
    return None


def _slug_to_brand(slug: str) -> str:
    parts = [p for p in re.split(r"[-_]+", slug) if p and p not in {"crm", "software", "reviews"}]
    if not parts:
        return slug.replace("-", " ").title()[:80]
    brand = " ".join(p.capitalize() for p in parts[:4])
    return brand[:80]


def _score_competitor(name: str, rec: dict[str, Any], domain: str) -> int:
    score = 0
    norm = normalize_competitor_name(name)
    leaders = KNOWN_LEADERS.get(domain, []) + KNOWN_LEADERS.get("saas_general", [])
    for leader in leaders:
        lnorm = normalize_competitor_name(leader)
        if norm == lnorm:
            score += 1000
        elif lnorm and lnorm in norm:
            score += 700
    source_type = str(rec.get("source_type") or "").lower()
    if "review" in source_type:
        score += 250
    if source_type in {"knowledge_graph", "google_local"}:
        score += 200
    url = str(rec.get("source_url") or rec.get("website") or "")
    if parse_vendor_from_review_url(url, name):
        score += 300
    if rec.get("price"):
        score += 80
    if len(name) > 45:
        score -= 400
    if len(name.split()) >= 5:
        score -= 200
    return score


def _is_live_perplexity_competitor(rec: dict[str, Any]) -> bool:
    if str(rec.get("record_type") or "").lower() != "competitor":
        return False
    blob = " ".join(
        str(rec.get(key) or "")
        for key in ("source_engine", "source_type", "discovered_via", "verification_status")
    ).lower()
    return "perplexity" in blob


def filter_serp_competitors(
    structured: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    *,
    domain: str = "general_market",
    limit: int = 12,
) -> dict[str, Any]:
    candidates: dict[str, tuple[int, dict[str, Any], str]] = {}

    def _consider(name: str, rec: dict[str, Any], kind: str) -> None:
        clean = str(name or "").strip()
        if not clean or not is_valid_competitor_display_name(clean):
            return
        key = normalize_competitor_name(clean)
        if not key:
            return
        score = _score_competitor(clean, rec, domain)
        prev = candidates.get(key)
        if prev is None or score > prev[0]:
            tagged = dict(rec)
            tagged["_normalizer_kind"] = kind
            candidates[key] = (score, tagged, clean)

    for rec in structured or []:
        if not isinstance(rec, dict):
            continue
        if str(rec.get("record_type") or "").lower() != "competitor":
            continue
        _consider(str(rec.get("name") or rec.get("company_name") or ""), rec, "structured")
        if _is_live_perplexity_competitor(rec):
            key = normalize_competitor_name(str(rec.get("name") or rec.get("company_name") or ""))
            if key and key not in candidates:
                tagged = dict(rec)
                tagged["_normalizer_kind"] = "perplexity_live"
                candidates[key] = (5000, tagged, str(rec.get("name") or "").strip())

    for ent in entities or []:
        if not isinstance(ent, dict):
            continue
        _consider(str(ent.get("company_name") or ent.get("name") or ""), ent, "entity")

    ranked = sorted(candidates.values(), key=lambda row: row[0], reverse=True)
    strong = [row for row in ranked if row[0] >= 200]
    top = list(strong[: int(limit)])
    if len(top) < 5:
        for row in ranked:
            if row in top:
                continue
            if row[0] < 80:
                continue
            top.append(row)
            if len(top) >= min(5, int(limit)):
                break
    top = top[: max(3, int(limit))]
    allowed_keys = {normalize_competitor_name(row[2]) for row in top}
    names: list[str] = []
    leaders = KNOWN_LEADERS.get(domain, []) + KNOWN_LEADERS.get("saas_general", [])
    leader_norms = {normalize_competitor_name(l): l for l in leaders}
    for row in top:
        raw = row[2]
        norm = normalize_competitor_name(raw)
        canonical = leader_norms.get(norm)
        if not canonical and norm:
            for lnorm, lname in leader_norms.items():
                if lnorm and (lnorm in norm or norm in lnorm) and abs(len(lnorm) - len(norm)) <= 2:
                    canonical = lname
                    break
        names.append(canonical or raw)

    filtered_structured: list[dict[str, Any]] = []
    for rec in structured or []:
        if not isinstance(rec, dict):
            continue
        if _is_live_perplexity_competitor(rec):
            filtered_structured.append(rec)
            continue
        if str(rec.get("record_type") or "").lower() != "competitor":
            filtered_structured.append(rec)
            continue
        nm = str(rec.get("name") or rec.get("company_name") or "")
        if normalize_competitor_name(nm) in allowed_keys:
            filtered_structured.append(rec)

    filtered_entities: list[dict[str, Any]] = []
    for ent in entities or []:
        if not isinstance(ent, dict):
            continue
        nm = str(ent.get("company_name") or ent.get("name") or "")
        if normalize_competitor_name(nm) in allowed_keys:
            filtered_entities.append(ent)

    return {
        "names": names,
        "structured_records": filtered_structured,
        "entities": filtered_entities,
        "trace": {
            "input_competitor_records": sum(
                1 for r in (structured or [])
                if isinstance(r, dict) and str(r.get("record_type") or "").lower() == "competitor"
            ),
            "input_entities": len(entities or []),
            "kept": len(names),
            "dropped": max(0, len(candidates) - len(names)),
            "top_names": names[:10],
        },
    }
