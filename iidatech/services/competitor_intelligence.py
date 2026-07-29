"""Deterministic competitor intelligence pack from evidence records."""
from __future__ import annotations
import re
from typing import Any
from urllib.parse import urlparse

_VALIDATION_REQUIRED = {
    "status": "validation_required",
    "verified": False,
    "reason": "insufficient real evidence",
}

_COMPETITOR_HINTS = re.compile(r"\b(hubspot|pipedrive|salesforce|zoho|zendesk|shopify|stripe|notion|zapier|make\.com|n8n|freshworks|monday|asana|slack|intercom|gorgias)\b", re.I)
_PRICE_RE = re.compile(r"(?:\$|₹|usd|inr)\s*[\d,]+(?:\.\d+)?|\d+(?:\.\d+)?\s*(?:%|/mo|/month|per user|/seat)", re.I)


def _as_dict(v):
    return v if isinstance(v, dict) else {}

def _as_list(v):
    return v if isinstance(v, list) else []

def _host(url: str) -> str:
    try:
        return urlparse(str(url or "")).netloc.lower()
    except Exception:
        return ""

def _extract_name(record: dict[str, Any]) -> str:
    title = str(record.get("title") or "")
    publisher = str(record.get("publisher") or "")
    for token in _COMPETITOR_HINTS.findall(title + " " + publisher):
        return token.title() if token.lower() != "make.com" else "Make"
    if publisher and "." in publisher:
        return publisher.split(".")[0].title()
    name = title.split("-")[0].strip()[:60] or publisher[:60]
    return name if name else ""

def _pricing_from_record(record: dict[str, Any]) -> str:
    blob = " ".join(str(record.get(k, "")) for k in ("title", "text", "summary", "metric_value", "metric_name"))
    m = _PRICE_RE.search(blob)
    return m.group(0) if m else ""

def _merge_competitor(target: dict[str, Any], record: dict[str, Any]) -> dict[str, Any] | None:
    name = _extract_name(record)
    if not name:
        return None
    key = name.lower()
    row = target.get(key) or {
        "name": name,
        "official_url": record.get("url", ""),
        "pricing": "",
        "pricing_model": "",
        "target_customer": "",
        "positioning": "",
        "strengths": [],
        "weaknesses": [],
        "moat": "",
        "estimated_margin": "",
        "market_gap": "",
        "sources": [],
    }
    url = str(record.get("url") or "")
    if url and not row.get("official_url"):
        row["official_url"] = url
    price = _pricing_from_record(record)
    if price and not row.get("pricing"):
        row["pricing"] = price
    family = str(record.get("source_family") or "").lower()
    if "pricing" in family or "pricing" in str(record.get("title", "")).lower():
        row["pricing_model"] = row["pricing_model"] or "subscription_or_tiered"
    text = str(record.get("text") or record.get("summary") or "")[:400].lower()
    if any(w in text for w in ("enterprise", "smb", "small business")):
        row["target_customer"] = row["target_customer"] or ("SMB" if "smb" in text or "small business" in text else "Enterprise")
    if record.get("trust_tier", 4) >= 4:
        row["weaknesses"] = list(dict.fromkeys(_as_list(row["weaknesses"]) + ["Source is weak social/blog — verify independently"]))
    if "review" in text or "g2" in str(record.get("publisher", "")).lower():
        row["market_gap"] = row["market_gap"] or "Review-driven switching pain — validate with buyer interviews"
    row["sources"] = list(dict.fromkeys(_as_list(row["sources"]) + [str(record.get("publisher") or record.get("url") or "evidence")[:80]]))[:6]
    target[key] = row
    return row

def build_competitor_intelligence(records: list[dict[str, Any]] | None, *, diligence_pack: dict | None = None) -> dict[str, Any]:
    records = list(records or [])
    diligence = _as_dict(diligence_pack)
    prebuilt = _as_dict(diligence.get("competitor_intelligence_pack"))
    if prebuilt.get("competitors") and prebuilt.get("evidence_status") == "live_serp_discovery":
        return {
            "competitor_count": int(prebuilt.get("competitor_count") or len(prebuilt.get("competitors") or [])),
            "competitors": list(prebuilt.get("competitors") or [])[:20],
            "strategic_insights": prebuilt.get("strategic_insights")
            or {
                "why_customers_buy": [],
                "why_customers_churn": [],
                "gap_opportunities": [],
            },
            "evidence_status": "live_serp_discovery",
            "discovery_source": "serp_intelligence",
        }
    merged: dict[str, dict[str, Any]] = {}

    for row in _as_list(diligence.get("competitive_benchmark")):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if name and not re.search(r"\bvendor\s*\d+\b", name, re.I):
            pseudo = {
                "title": name,
                "text": row.get("benchmark_metrics") or row.get("positioning") or "",
                "url": row.get("source") or "",
                "source_family": "serp_intelligence" if row.get("verification_status") == "live_serp" else "analyst_report",
                "trust_tier": 2,
            }
            _merge_competitor(merged, pseudo)
            continue
        pseudo = {"title": row.get("competitor_archetypes") or row.get("segment"), "text": row.get("benchmark_metrics"), "source_family": "analyst_report", "trust_tier": 2}
        _merge_competitor(merged, pseudo)

    for record in records:
        if not isinstance(record, dict):
            continue
        blob = " ".join(str(record.get(k, "")) for k in ("title", "text", "publisher", "source_family")).lower()
        if not any(h in blob for h in ("competitor", "compete", "versus", "vs ", "alternative", "pricing", "hubspot", "pipedrive")) and record.get("source_family") not in {"local_operator_listing", "pricing_reference"}:
            if not _COMPETITOR_HINTS.search(blob):
                continue
        try:
            from iidatech.retrieval.source_trust import annotate_truth_fields
            record = annotate_truth_fields(record)
        except Exception:
            pass
        _merge_competitor(merged, record)

    competitors = list(merged.values())[:20]
    if not competitors:
        return {
            **_VALIDATION_REQUIRED,
            "competitor_count": 0,
            "competitors": [],
            "strategic_insights": {},
            "evidence_status": "insufficient_competitor_evidence",
        }
    for comp in competitors:
        if not comp.get("positioning"):
            comp["positioning"] = f"{comp.get('name')} targets {comp.get('target_customer') or 'segment buyers'}"
        if not comp.get("moat"):
            comp["moat"] = "Incumbent distribution and brand — verify switching costs"
        if not comp.get("market_gap"):
            comp["market_gap"] = "Narrow wedge + faster implementation + ICP-specific workflow"

    return {
        "competitor_count": len(competitors),
        "competitors": competitors,
        "strategic_insights": {
            "why_customers_buy": [],
            "why_customers_churn": [],
            "gap_opportunities": [c.get("market_gap") for c in competitors[:5] if c.get("market_gap")],
        },
        "evidence_status": "derived_from_ranked_evidence" if competitors else "insufficient_competitor_evidence",
    }