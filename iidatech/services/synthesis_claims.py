"""Pass-0 claim selector for IIDATECH section synthesis."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

_GROWTH_TERMS = (
    "cagr", "growing", "growth", "market size", "tam", "projected", "forecast",
    "billion", "million",
)
_SECTION_PRIORITY = {
    "Competitive Landscape": ("pricing", "competitor", "buyer_pain", "market_size", "risk"),
    "Key Player Profiles": ("competitor", "pricing", "buyer_pain", "market_size", "risk"),
    "Market Share Analysis": ("competitor", "pricing", "market_size", "buyer_pain", "risk"),
    "Pricing Analysis": ("pricing", "buyer_pain", "competitor", "market_size", "risk"),
    "Consumer Behavior": ("buyer_pain", "competitor", "pricing", "market_size", "risk"),
    "Market Size & Valuation": ("market_size", "pricing", "buyer_pain", "competitor", "risk"),
    "Market Trends": ("market_size", "buyer_pain", "competitor", "pricing", "risk"),
    "Executive Summary": ("pricing", "competitor", "buyer_pain", "market_size", "risk"),
}
_NAMED_VENDORS = (
    "hubspot", "salesforce", "zoho", "pipedrive", "monday", "freshsales",
    "bmw", "mercedes", "audi", "lamborghini", "cardekho", "carwale",
    "nykaa", "purplle", "flipkart", "amazon",
)


def _record_blob(record: dict[str, Any]) -> str:
    return " ".join(
        str(record.get(k, "") or "")
        for k in ("title", "text", "metric", "metric_name", "metric_value", "publisher", "source_family", "url")
    ).lower()


def _is_low_signal_record(record: dict[str, Any]) -> bool:
    tags = " ".join(str(t).lower() for t in (record.get("topic_tags") or []))
    publisher = str(record.get("publisher") or "").lower()
    if "landscape_seed" in tags or publisher == "industry_landscape_seed":
        return True
    family = str(record.get("source_family") or "").lower()
    blob = _record_blob(record)
    if family in {"analyst_report", "magazine_article", "blog_article"}:
        growth_only = any(t in blob for t in _GROWTH_TERMS)
        has_named = any(v in blob for v in _NAMED_VENDORS)
        has_price = bool(re.search(r"(?:\$|₹|rs\.?|inr|usd)\s*\d", blob))
        if growth_only and not has_named and not has_price:
            return True
    return False


def _named_entity(blob: str) -> str:
    for name in _NAMED_VENDORS:
        if name in {"audi", "bmw", "mini"}:
            if re.search(rf"\b{re.escape(name)}\b", blob):
                return name
            continue
        if name in blob:
            return name
    m = re.search(r"([a-z][a-z0-9.-]{2,}\.(?:com|in|co\.in))", blob)
    return m.group(1) if m else ""


def infer_claim_type(record: dict[str, Any]) -> str:
    record_type = str(record.get("record_type") or record.get("claim_type") or "").lower()
    unit = str(record.get("unit") or "").lower()
    family = str(record.get("source_family") or "").lower()
    blob = _record_blob(record)
    if record_type in {"pricing", "competitor", "buyer_pain", "market_size", "risk"}:
        return record_type
    if unit == "competitor" or family in {"competitor_intelligence", "local_operator_listing"}:
        return "competitor"
    if any(t in blob for t in ("service center", "dealership", "workshop", "garage", "authorized dealer")):
        return "competitor"
    if re.search(r"\d+\s*(?:centers|dealers|outlets|workshops)", blob):
        return "competitor"
    if unit == "buyer_pain" or family in {"buyer_signal", "review_platform", "reddit_practitioner", "youtube_transcript"}:
        return "buyer_pain"
    if unit == "pricing" or family in {"pricing_reference", "vendor_pricing", "marketplace_pricing"}:
        return "pricing"
    if any(name in blob for name in _NAMED_VENDORS) and family != "pricing_reference":
        if any(t in blob for t in ("review", "complaint", "pain", "frustrat", "switch")):
            return "buyer_pain"
        return "competitor"
    if any(t in blob for t in _GROWTH_TERMS):
        return "market_size"
    if re.search(r"(?:\$|₹|rs\.?|inr|usd)\s*\d", blob) or re.search(r"\d+\s*(?:/month|per user|per seat)", blob):
        return "pricing"
    if any(t in blob for t in ("risk", "regulation", "compliance", "barrier", "challenge")):
        return "risk"
    return "competitor" if "competitor" in blob or "operator" in blob else "risk"


def _claim_text(record: dict[str, Any], claim_type: str) -> str:
    metric = str(record.get("metric") or "").strip()
    if not metric:
        metric = " ".join(
            str(record.get(k, "") or "").strip()
            for k in ("metric_name", "metric_value")
            if record.get(k)
        ).strip()
    title = str(record.get("title") or "Untitled").strip()
    publisher = str(record.get("publisher") or "").strip()
    text = str(record.get("text") or record.get("summary") or "").strip()
    if metric:
        body = f"{title}: {metric}"
    elif text:
        body = f"{title}: {text[:140]}"
    else:
        body = title
    if publisher and publisher.lower() not in body.lower():
        body = f"{publisher} — {body}"
    return body[:240]


def _evidence_id(record: dict[str, Any], idx: int) -> str:
    return str(record.get("record_id") or record.get("id") or f"E{idx}")


def count_pre_merge_claims(top_records: list[dict[str, Any]]) -> int:
    return sum(
        1
        for record in top_records[:12]
        if isinstance(record, dict) and not _is_low_signal_record(record)
    )


def merge_similar_claims(claims: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not claims:
        return []
    merged: list[dict[str, Any]] = []
    for claim in claims:
        placed = False
        ctype = str(claim.get("claim_type"))
        entity = str(claim.get("_entity") or "")
        keywords = set(claim.get("_keywords") or set())
        for bucket in merged:
            if bucket.get("claim_type") != ctype:
                continue
            if ctype == "market_size":
                bucket["evidence_ids"] = list(dict.fromkeys((bucket.get("evidence_ids") or []) + (claim.get("evidence_ids") or [])))
                bucket["claim"] = "Macro growth signals (context only unless tied to niche buyers)."
                placed = True
                break
            if ctype == "pricing" and entity and entity != bucket.get("_entity"):
                continue
            if ctype == "competitor" and entity and entity != bucket.get("_entity"):
                continue
            overlap = keywords & set(bucket.get("_keywords") or set())
            union = keywords | set(bucket.get("_keywords") or set())
            if union and len(overlap) / max(len(union), 1) >= 0.55:
                bucket["evidence_ids"] = list(dict.fromkeys((bucket.get("evidence_ids") or []) + (claim.get("evidence_ids") or [])))
                if len(str(claim.get("claim", ""))) > len(str(bucket.get("claim", ""))):
                    bucket["claim"] = claim["claim"]
                bucket["_keywords"] = union
                placed = True
                break
        if not placed:
            merged.append(dict(claim))
    for i, row in enumerate(merged, start=1):
        row["claim_id"] = f"C{i}"
        row.pop("_keywords", None)
        row.pop("_entity", None)
    return merged


def select_diverse_claims(claims: list[dict[str, Any]], section_title: str, max_total: int = 5) -> list[dict[str, Any]]:
    order = _SECTION_PRIORITY.get(section_title, _SECTION_PRIORITY["Competitive Landscape"])
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in claims:
        buckets[str(row.get("claim_type"))].append(row)
    picked: list[dict[str, Any]] = []
    per_type_cap = {"pricing": 2, "competitor": 2, "buyer_pain": 2, "market_size": 1, "risk": 1}
    while len(picked) < max_total:
        progressed = False
        for ctype in order:
            cap = per_type_cap.get(ctype, 1)
            if buckets.get(ctype) and sum(1 for p in picked if p.get("claim_type") == ctype) < cap:
                picked.append(buckets[ctype].pop(0))
                progressed = True
                if len(picked) >= max_total:
                    break
        if not progressed:
            break
    for i, row in enumerate(picked, start=1):
        row["claim_id"] = f"C{i}"
    return picked[:max_total]


def build_section_claims(section: dict | str, top_records: list[dict[str, Any]], *, topic: str = "", industry: str = "", domain: str = "") -> list[dict[str, Any]]:
    section_title = section.get("title", section) if isinstance(section, dict) else str(section)
    if topic and domain:
        try:
            from iidatech.validation.competitor_relevance import filter_records_for_narrative_synthesis

            top_records = filter_records_for_narrative_synthesis(
                top_records, topic=topic, industry=industry, domain=domain,
            )
        except Exception:
            pass
    claims: list[dict[str, Any]] = []
    for idx, record in enumerate(top_records[:12], start=1):
        if not isinstance(record, dict) or _is_low_signal_record(record):
            continue
        claim_type = infer_claim_type(record)
        blob = _claim_text(record, claim_type).lower()
        claims.append({
            "claim_id": f"C{len(claims) + 1}",
            "claim_type": claim_type,
            "priority": 5,
            "claim": _claim_text(record, claim_type),
            "evidence_ids": [_evidence_id(record, idx)],
            "confidence": str(record.get("evidence_tier") or record.get("evidence_type") or "medium").lower()[:24] or "medium",
            "_keywords": set(re.findall(r"[a-z0-9]{4,}", blob)),
            "_entity": _named_entity(blob),
        })
    merged = merge_similar_claims(claims)
    return select_diverse_claims(merged, section_title, max_total=5)


def prioritize_claims_for_section(claims: list[dict[str, Any]], section_title: str) -> list[dict[str, Any]]:
    order = _SECTION_PRIORITY.get(section_title, _SECTION_PRIORITY["Competitive Landscape"])
    type_rank = {claim_type: idx for idx, claim_type in enumerate(order)}

    def sort_key(row: dict[str, Any]) -> tuple[int, str]:
        return (type_rank.get(str(row.get("claim_type")), 99), str(row.get("claim_id")))

    ranked = sorted(claims, key=sort_key)
    for priority, row in enumerate(ranked, start=1):
        row["priority"] = priority
    return ranked


def build_evidence_digest(top_records: list[dict[str, Any]], claims: list[dict[str, Any]]) -> dict[str, str]:
    needed = {eid for row in claims for eid in (row.get("evidence_ids") or [])}
    digest: dict[str, str] = {}
    for idx, record in enumerate(top_records[:12], start=1):
        eid = _evidence_id(record, idx)
        if eid not in needed:
            continue
        digest[eid] = _claim_text(record, infer_claim_type(record))[:180]
    return digest


def build_synthesis_compact_payload(
    section_title: str,
    claims: list[dict[str, Any]],
    *,
    confidence_flags: dict[str, Any] | None = None,
    missing_data: list[str] | None = None,
    topic: str = "",
    evidence_digest: dict[str, str] | None = None,
) -> dict[str, Any]:
    compact_claims = [
        {
            "claim_id": row.get("claim_id"),
            "claim_type": row.get("claim_type"),
            "priority": row.get("priority"),
            "claim": row.get("claim"),
            "evidence_ids": row.get("evidence_ids", [])[:3],
            "confidence": row.get("confidence"),
        }
        for row in claims[:5]
    ]
    payload = {
        "topic": topic,
        "section": section_title,
        "top_claims": compact_claims,
        "evidence_digest": evidence_digest or {},
        "confidence_flags": confidence_flags or {},
        "missing_data": (missing_data or [])[:6],
    }
    payload["_payload_chars"] = len(__import__("json").dumps(payload, ensure_ascii=False))
    if payload["_payload_chars"] > 4000:
        payload["evidence_digest"] = {k: v[:120] for k, v in (evidence_digest or {}).items()}
        for row in payload["top_claims"]:
            row["claim"] = str(row.get("claim", ""))[:160]
        payload["_payload_chars"] = len(__import__("json").dumps(payload, ensure_ascii=False))
    return payload


SYNTHESIS_ANALYST_SYSTEM = (
    "You are a senior market analyst. Your job is NOT to summarize evidence. "
    "Your job is to: (1) identify the strongest business implications, "
    "(2) explain competitive advantage, (3) expose weaknesses, "
    "(4) give actionable conclusions. Reject generic statements. "
    "Forbidden outputs include: 'market is growing', 'competition exists', 'opportunity is large', "
    "'competition is strong'. Every statement must be specific, name entities/prices from top_claims, "
    "and cite claim_id values. Use evidence_digest only to disambiguate units. "
    "Do not invent numbers or vendors not in top_claims/evidence_digest."
)