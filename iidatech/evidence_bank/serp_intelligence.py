"""Deep SerpAPI integration: Google Search, Local, Shopping, News, Maps reviews."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from iidatech.evidence_bank.google_competitor_discovery import (
    KNOWN_LEADERS,
    REVIEW_AGGREGATOR_SITES,
    _looks_like_noise,
    _names_from_serp_text,
    _serp_api_key,
    _serp_max_queries,
    normalize_competitor_name,
    serp_enabled,
)

def _default_serp_trace() -> dict[str, Any]:
    return {
        "serp_search_hits": 0,
        "serp_local_hits": 0,
        "serp_reviews_hits": 0,
        "serp_shopping_hits": 0,
        "serp_news_hits": 0,
        "structured_records_generated": 0,
        "queries": [],
        "engines": [],
        "errors": [],
    }


_serp_intel_trace_ctx: ContextVar[dict[str, Any] | None] = ContextVar(
    "serp_intel_trace",
    default=None,
)


def _active_serp_trace() -> dict[str, Any]:
    current = _serp_intel_trace_ctx.get()
    if current is None:
        return _default_serp_trace()
    return current

_WTP_PATTERNS = (
    r"would pay",
    r"willing to pay",
    r"too expensive",
    r"overpriced",
    r"worth (?:it|the price)",
    r"budget",
    r"\$\d+",
    r"₹\s*\d+",
    r"inr\s*\d+",
)
_COMPLAINT_PATTERNS = (
    r"too expensive",
    r"poor (?:service|quality)",
    r"delayed",
    r"not worth",
    r"disappoint",
    r"complaint",
    r"bad experience",
    r"refund",
    r"broken",
    r"damaged",
)
_MARKET_SIZE_RE = re.compile(
    r"(?:market\s+(?:size|worth|valued|value)|TAM|industry)\s+(?:of|at|is|to reach|expected to reach|projected to reach)?\s*"
    r"([\$£€₹]?\s*[\d,.]+)\s*(billion|million|trillion|bn|mn|B|M|T)?",
    re.I,
)


def _geo_params(target: str) -> dict[str, str]:
    """SerpAPI geo params — gl/hl/google_domain per geography."""
    geo = _geo_hint(target)
    low = geo.lower()
    if any(token in low for token in ("india", "mumbai", "delhi", "bangalore", "bengaluru", "hyderabad")):
        return {"gl": "in", "hl": "en", "google_domain": "google.co.in", "location": geo}
    if any(token in low for token in ("uk", "united kingdom", "london", "britain")):
        return {"gl": "uk", "hl": "en", "google_domain": "google.co.uk", "location": geo}
    if any(token in low for token in ("australia", "sydney", "melbourne")):
        return {"gl": "au", "hl": "en", "google_domain": "google.com.au", "location": geo}
    if low in {"", "global", "world", "worldwide", "international"}:
        return {"gl": "us", "hl": "en", "google_domain": "google.com"}
    return {"gl": "us", "hl": "en", "location": geo}


def _append_market_pricing_queries(
    plan: dict[str, list[dict[str, str]]],
    *,
    topic: str,
    base: str,
    geo: str,
    leader: str = "",
) -> None:
    """Universal market-size and pricing discovery queries across SerpAPI engines."""
    market_queries = [
        {"q": f"{topic} market size billion"},
        {"q": f"{topic} total addressable market TAM"},
        {
            "q": (
                f'"{topic}" market size site:statista.com OR site:grandviewresearch.com '
                f"OR site:mordorintelligence.com OR site:marketsandmarkets.com"
            )
        },
    ]
    pricing_queries = [
        {"q": f"{leader} pricing plans" if leader else f"{base} pricing plans"},
        {"q": f"{base} pricing comparison", "tbm": "shop"},
        {"q": f"{base} subscription price per month"},
    ]
    for item in market_queries + pricing_queries:
        plan.setdefault("google", []).append(item)
    if topic:
        plan.setdefault("google_shopping", []).append({"q": f"{topic} pricing {geo}".strip()})
        plan.setdefault("google_news", []).append({"q": f"{topic} market growth funding {geo}".strip()})


def _serp_call(engine: str, query: str, *, cache_kind: str = "competitor_search", extra: dict[str, str] | None = None) -> dict[str, Any]:
    from iidatech.storage.provider_cache import cached_provider_call

    def _live() -> dict[str, Any]:
        import requests

        key = _serp_api_key()
        if not key:
            return {"error": "missing_serpapi_key"}
        params: dict[str, str] = {"engine": engine, "q": query, "api_key": key}
        if extra:
            params.update(extra)
        geo_defaults = _geo_params(str(extra.get("location") if extra else "") or "India")
        for key_name, val in geo_defaults.items():
            if key_name not in params and val:
                params[key_name] = val
        if engine in {"google_local", "google_maps"} and "location" not in params:
            params.setdefault("location", geo_defaults.get("location") or "India")
        url = "https://serpapi.com/search.json"
        last_error = ""
        for attempt in range(2):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers={"User-Agent": "IIDATECH/1.0"},
                    timeout=45,
                )
                data = response.json() if response.content else {}
                if response.status_code >= 400:
                    return {"error": str(data.get("error") or response.text or response.status_code)[:200]}
                if isinstance(data, dict) and data.get("error"):
                    return {"error": str(data.get("error"))[:200]}
                return data if isinstance(data, dict) else {}
            except Exception as exc:
                last_error = str(exc)[:200]
                if attempt == 0:
                    time.sleep(1.5)
        return {"error": last_error or "serpapi_request_failed"}

    cache_query = f"{engine}::{query}"
    return cached_provider_call(
        "serpapi",
        cache_query,
        cache_kind,
        "",
        _live,
        model=engine,
        estimated_cost=0.012,
    )


def _geo_hint(target: str) -> str:
    t = str(target or "").strip()
    if not t or t.lower() in {"global", "world", "worldwide", "international"}:
        return "India"
    return t


def build_vertical_serp_plan(topic: str, domain: str, target: str = "") -> dict[str, list[dict[str, str]]]:
    """Return endpoint-specific Serp query plan keyed by engine."""
    base = f"{topic} {target}".strip()
    geo = _geo_hint(target)
    leaders = KNOWN_LEADERS.get(domain, [])[:2]
    leader = leaders[0] if leaders else ""

    plan: dict[str, list[dict[str, str]]] = {
        "google": [],
        "google_local": [],
        "google_shopping": [],
        "google_news": [],
        "google_maps": [],
    }

    saas_domains = {
        "crm_automation", "b2b_saas", "saas_software", "saas_general", "clinic_workflow",
        "healthcare_saas", "ai_workflow_automation", "revops_sales_automation",
    }
    d2c_domains = {"d2c_skincare", "ecommerce_retail", "consumer", "fashion", "decor_retail", "gifting_retail"}
    restaurant_domains = {"restaurants", "hospitality", "food"}
    festive_domains = {"festive_retail", "event_services", "wedding_services", "decor_retail", "gifting_retail"}
    clinic_domains = {"dental_clinics", "clinic_workflow", "healthcare_saas", "healthcare"}

    if domain in saas_domains:
        plan["google"] = [
            {"q": f"{base} CRM pricing site:g2.com"},
            {"q": f"{base} site:capterra.com reviews"},
            {"q": f"{leader} pricing plans" if leader else f"{base} software pricing"},
            {"q": f"{base} alternatives comparison"},
        ]
    elif domain in d2c_domains:
        plan["google_shopping"] = [{"q": base}, {"q": f"{topic} buy online {geo}"}]
        plan["google"] = [
            {"q": f"site:amazon.in {topic}"},
            {"q": f"site:flipkart.com {topic}"},
            {"q": f"{topic} reviews site:nykaa.com OR site:trustpilot.com"},
        ]
    elif domain in restaurant_domains:
        plan["google_local"] = [
            {"q": f"{topic} restaurant {geo}", "location": geo},
            {"q": f"best {topic} near {geo}", "location": geo},
        ]
        plan["google_maps"] = [{"q": f"{topic} restaurant {geo}", "type": "search"}]
        plan["google"] = [{"q": f"{topic} menu prices {geo}"}, {"q": f"{topic} zomato swiggy reviews"}]
    elif domain in festive_domains:
        plan["google_shopping"] = [
            {"q": f"{topic} decoration kit"},
            {"q": f"eco-friendly {topic} kit"},
        ]
        plan["google"] = [
            {"q": f"site:amazon.in {topic}"},
            {"q": f"site:flipkart.com {topic}"},
            {"q": f"site:indiamart.com {topic}"},
            {"q": f"site:justdial.com {topic} {geo}"},
        ]
        plan["google_local"] = [
            {"q": f"festive decor vendors {geo}", "location": geo},
            {"q": f"{topic} suppliers near me", "location": geo},
        ]
        plan["google_maps"] = [{"q": f"{topic} decor shop {geo}", "type": "search"}]
        plan["google_news"] = [{"q": f"{topic} festival market India"}]
    elif domain in clinic_domains:
        plan["google_local"] = [
            {"q": f"dental clinic {geo}", "location": geo},
            {"q": f"{topic} near {geo}", "location": geo},
        ]
        plan["google_maps"] = [{"q": f"dental clinic {topic} {geo}", "type": "search"}]
        plan["google"] = [
            {"q": f"{topic} consultation price {geo}"},
            {"q": f"{topic} reviews site:practo.com OR google reviews"},
        ]
    else:
        plan["google"] = [{"q": base}, {"q": f"{base} competitors pricing reviews"}]
        if geo:
            plan["google_local"] = [{"q": f"{base} {geo}", "location": geo}]

    _append_market_pricing_queries(plan, topic=topic, base=base, geo=geo, leader=leader)
    return plan


def _extract_price(text: str) -> str:
    for pattern in (
        r"₹\s*[\d,]+(?:\.\d+)?",
        r"\$\s*[\d,]+(?:\.\d+)?",
        r"INR\s*[\d,]+",
        r"[\d,]+\s*/\s*mo",
        r"[\d,]+\s*per\s+month",
    ):
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(0).strip()
    return ""


def _buyer_signals(text: str) -> dict[str, Any]:
    low = str(text or "").lower()
    complaints = [p for p in _COMPLAINT_PATTERNS if re.search(p, low)]
    wtp = [p for p in _WTP_PATTERNS if re.search(p, low)]
    objections: list[str] = []
    for phrase in ("integration", "support", "delivery", "quality", "setup", "hidden fees"):
        if phrase in low:
            objections.append(phrase)
    return {
        "complaints": complaints,
        "wtp_signals": wtp,
        "objections": objections,
    }


def _extract_market_signal(text: str, *, source_url: str = "", title: str = "", engine: str = "") -> dict[str, Any] | None:
    snippet = str(text or "").strip()
    if len(snippet) < 16:
        return None
    match = _MARKET_SIZE_RE.search(snippet)
    if not match:
        return None
    metric = match.group(0).strip()[:160]
    return {
        "record_type": "market_signal",
        "name": title or "market size signal",
        "metric": metric,
        "snippet": snippet[:500],
        "source_engine": engine,
        "source_url": source_url,
        "verification_status": "live_serp",
        "confidence_tier": "proxy_hint",
    }


def extract_structured_from_payload(engine: str, payload: dict[str, Any], *, domain: str = "", topic: str = "") -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not isinstance(payload, dict) or payload.get("error"):
        return records

    def _competitor(
        name: str,
        *,
        source_url: str = "",
        price: str = "",
        reviews: dict | None = None,
        positioning: str = "",
        locality: str = "",
        source_type: str = "",
        complaints: list | None = None,
        wtp: list | None = None,
    ) -> None:
        norm = normalize_competitor_name(name)
        if not norm or _looks_like_noise(norm):
            return
        records.append({
            "record_type": "competitor",
            "name": name.strip()[:120],
            "price": price,
            "reviews": reviews or {},
            "complaints": complaints or [],
            "positioning": positioning or f"SerpAPI {engine} hit",
            "locality": locality,
            "wtp_signals": wtp or [],
            "source_engine": engine,
            "source_url": source_url,
            "source_type": source_type or engine,
            "industry": domain,
            "verification_status": "live_serp" if source_url or price else "unverified",
        })
        if price and source_url:
            records.append({
                "record_type": "pricing",
                "name": name.strip()[:120],
                "price": price,
                "source_url": source_url,
                "source_engine": engine,
                "source_type": source_type or engine,
                "verification_status": "live_serp",
            })

    def _market_signal(text: str, *, source_url: str = "", title: str = "") -> None:
        row = _extract_market_signal(text, source_url=source_url, title=title, engine=engine)
        if row:
            records.append(row)

    def _buyer_voice(text: str, *, source_url: str = "", name: str = "", rating: Any = None) -> None:
        if len(str(text or "")) < 12:
            return
        signals = _buyer_signals(text)
        if not signals["complaints"] and not signals["wtp_signals"] and not signals["objections"]:
            return
        records.append({
            "record_type": "buyer_voice",
            "name": name or "reviewer",
            "complaints": signals["complaints"],
            "wtp_signals": signals["wtp_signals"],
            "objections": signals["objections"],
            "review_text": str(text)[:500],
            "reviews": {"rating": rating},
            "source_engine": engine,
            "source_url": source_url,
            "industry": domain,
        })

    if engine == "google_shopping":
        for item in payload.get("shopping_results") or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "")
            link = str(item.get("link") or item.get("product_link") or "")
            price = str(item.get("price") or item.get("extracted_price") or "")
            source = str(item.get("source") or "")
            _competitor(
                title or source,
                source_url=link,
                price=price,
                positioning=f"Shopping listing via {source}" if source else "Google Shopping",
                source_type="google_shopping",
            )
            snippet = str(item.get("snippet") or item.get("description") or "")
            _buyer_voice(snippet, source_url=link, name=title, rating=item.get("rating"))

    if engine in {"google_local", "google_maps", "google"}:
        local_items = list(payload.get("local_results") or [])
        if engine == "google_maps":
            local_items.extend(payload.get("place_results") or [])
            if isinstance(payload.get("place_results"), dict):
                local_items.append(payload["place_results"])
        for item in local_items:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or item.get("name") or "")
            link = str(item.get("link") or item.get("website") or "")
            address = str(item.get("address") or item.get("address_lines", [""])[0] if isinstance(item.get("address_lines"), list) else "")
            rating = item.get("rating")
            reviews_cnt = item.get("reviews") or item.get("reviews_count")
            reviews = {"rating": rating, "count": reviews_cnt}
            _competitor(
                title,
                source_url=link,
                positioning=str(item.get("type") or item.get("service_options") or "local vendor"),
                locality=address,
                reviews=reviews,
                source_type="google_local",
            )
            for review in item.get("user_reviews") or item.get("reviews_data") or []:
                if isinstance(review, dict):
                    _buyer_voice(
                        str(review.get("snippet") or review.get("text") or ""),
                        source_url=link,
                        name=title,
                        rating=review.get("rating"),
                    )

    if engine == "google":
        for box_key in ("answer_box", "featured_snippet"):
            box = payload.get(box_key) or {}
            if isinstance(box, dict):
                text = " ".join(
                    str(box.get(k) or "")
                    for k in ("answer", "snippet", "description", "title", "list", "table")
                )
                link = str(box.get("link") or box.get("source") or "")
                _market_signal(text, source_url=link, title=str(box.get("title") or topic))
        for item in payload.get("related_questions") or payload.get("people_also_ask") or []:
            if not isinstance(item, dict):
                continue
            text = f"{item.get('question') or ''} {item.get('snippet') or item.get('answer') or ''}"
            _market_signal(text, source_url=str(item.get("link") or ""), title=str(item.get("question") or ""))
        for item in payload.get("inline_shopping_results") or payload.get("shopping_results") or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "")
            link = str(item.get("link") or item.get("product_link") or "")
            price = str(item.get("price") or item.get("extracted_price") or "")
            _competitor(
                title,
                source_url=link,
                price=price,
                positioning="Google inline shopping",
                source_type="google_inline_shopping",
            )
        for item in payload.get("organic_results") or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "")
            link = str(item.get("link") or "")
            snippet = str(item.get("snippet") or "")
            price = _extract_price(f"{title} {snippet}")
            source_type = "serp_organic"
            if any(site in link.lower() for site in ("amazon.", "flipkart.", "indiamart.", "justdial.")):
                source_type = "marketplace_listing"
                _competitor(
                    title or link.split("/")[2],
                    source_url=link,
                    price=price,
                    positioning=title[:160] or "marketplace listing",
                    source_type=source_type,
                )
            elif any(site in link.lower() for site in REVIEW_AGGREGATOR_SITES):
                source_type = "review_platform"
                try:
                    from iidatech.evidence_bank.competitor_normalizer import parse_vendor_from_review_url

                    vendor = parse_vendor_from_review_url(link, title)
                    if vendor:
                        _competitor(
                            vendor,
                            source_url=link,
                            price=price,
                            positioning=title[:160] or "review platform",
                            source_type=source_type,
                        )
                except ImportError:
                    pass
            for name in _names_from_serp_text(f"{title} {snippet}", domain):
                _competitor(
                    name,
                    source_url=link,
                    price=price,
                    positioning=title[:160],
                    source_type=source_type,
                )
            _buyer_voice(snippet, source_url=link, name=title)
            _market_signal(f"{title} {snippet}", source_url=link, title=title)
        kg = payload.get("knowledge_graph") or {}
        if isinstance(kg, dict) and kg.get("title"):
            _competitor(
                str(kg["title"]),
                source_url=str(kg.get("website") or ""),
                positioning="knowledge graph",
                source_type="knowledge_graph",
                reviews={"rating": kg.get("rating"), "count": kg.get("review_count")},
            )

    if engine == "google_news":
        for item in payload.get("news_results") or []:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "")
            link = str(item.get("link") or "")
            snippet = str(item.get("snippet") or "")
            for name in _names_from_serp_text(f"{title} {snippet}", domain):
                _competitor(name, source_url=link, positioning=title[:160], source_type="google_news")
            _buyer_voice(snippet, source_url=link, name=title)
            _market_signal(f"{title} {snippet}", source_url=link, title=title)

    return records


def structured_to_competitor_entities(structured: list[dict[str, Any]], *, domain: str = "") -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in structured:
        if row.get("record_type") != "competitor":
            continue
        name = str(row.get("name") or "")
        norm = normalize_competitor_name(name)
        if not norm or norm in seen:
            continue
        seen.add(norm)
        reviews = row.get("reviews") if isinstance(row.get("reviews"), dict) else {}
        entities.append({
            "company_name": name,
            "normalized_name": norm,
            "source_urls": [row.get("source_url")] if row.get("source_url") else [],
            "source_type": row.get("source_type") or row.get("source_engine") or "serpapi",
            "category": "discovered",
            "mention_frequency": 1,
            "discovered_via": "serpapi",
            "provisional": True,
            "verification_status": "live_serp" if (row.get("source_url") or row.get("price")) else "unverified",
            "industry": domain or row.get("industry") or "general",
            "country": row.get("locality") or "Global",
            "positioning": row.get("positioning") or "",
            "pricing": row.get("price") or "unknown",
            "metrics": {"reviews": reviews, "locality": row.get("locality") or ""},
            "strengths": [],
            "weaknesses": [],
            "complaints": row.get("complaints") or [],
            "gtm_model": "unknown",
            "trust_score": 0.65 if reviews.get("rating") else 0.60,
            "last_verified": datetime.now(timezone.utc).strftime("%Y-%m"),
        })
    return entities


def structured_to_learned_records(structured: list[dict[str, Any]], domain: str, target: str):
    from iidatech.evidence_bank.bank_store import bank_row_to_learned_record
    from on_demand_research import LearnedRecord, clean_html_text, now_iso, record_id

    records = []
    for row in structured:
        rtype = row.get("record_type")
        if rtype == "competitor":
            records.append(bank_row_to_learned_record(structured_to_competitor_entities([row], domain=domain)[0], domain, target))
        elif rtype == "buyer_voice":
            title = f"Buyer voice: {row.get('name') or 'review'}"
            text_bits = [
                f"complaints={row.get('complaints')}",
                f"wtp={row.get('wtp_signals')}",
                f"objections={row.get('objections')}",
                str(row.get("review_text") or ""),
            ]
            records.append(
                LearnedRecord(
                    id=record_id(str(row.get("source_url") or title), domain, target),
                    source_family="serp_buyer_voice",
                    publisher=str(row.get("source_engine") or "serpapi"),
                    title=clean_html_text(title, 180),
                    url=str(row.get("source_url") or ""),
                    retrieved_at=now_iso(),
                    geography=target or "Global",
                    year="",
                    metric_name="buyer_voice_signal",
                    metric_value=str(row.get("wtp_signals") or row.get("complaints") or "")[:200],
                    unit="review",
                    topic_tags=["iidatech_serp", domain, "buyer_voice", str(row.get("source_engine") or "")],
                    text=" | ".join(text_bits)[:900],
                    confidence=0.62,
                    industry=domain,
                    claim_type="buyer_voice",
                    evidence_tier="serp_reviews",
                    allowed_use="Review-derived buyer signal — verify on source.",
                )
            )
    return records


def _count_hits(engine: str, payload: dict[str, Any]) -> int:
    if not isinstance(payload, dict):
        return 0
    if engine == "google_shopping":
        return len(payload.get("shopping_results") or [])
    if engine == "google_news":
        return len(payload.get("news_results") or [])
    if engine in {"google_local", "google_maps"}:
        n = len(payload.get("local_results") or [])
        if isinstance(payload.get("place_results"), dict):
            n += 1
        elif isinstance(payload.get("place_results"), list):
            n += len(payload["place_results"])
        return n
    n = len(payload.get("organic_results") or [])
    n += len(payload.get("local_results") or [])
    n += len(payload.get("shopping_results") or [])
    return n


def run_serp_intelligence(
    topic: str,
    domain: str,
    target: str = "",
    *,
    max_calls: int | None = None,
) -> dict[str, Any]:
    if not serp_enabled():
        return {
            "entities": [],
            "structured_records": [],
            "queries": [],
            "trace": serp_intelligence_trace(),
            "enabled": False,
        }

    plan = build_vertical_serp_plan(topic, domain, target)
    budget = max_calls if max_calls is not None else max(6, _serp_max_queries() * 2)
    calls: list[tuple[str, dict[str, str]]] = []
    for engine, items in plan.items():
        for item in items:
            calls.append((engine, item))
    calls = calls[:budget]

    structured: list[dict[str, Any]] = []
    payloads: list[tuple[str, dict[str, Any]]] = []
    trace = {
        "serp_search_hits": 0,
        "serp_local_hits": 0,
        "serp_reviews_hits": 0,
        "serp_shopping_hits": 0,
        "serp_news_hits": 0,
        "structured_records_generated": 0,
        "queries": [],
        "engines": [],
        "errors": [],
    }

    for engine, params in calls:
        query = str(params.get("q") or topic)
        extra = {k: v for k, v in params.items() if k != "q"}
        if "location" not in extra:
            extra["location"] = _geo_hint(target)
        cache_kind = "news" if engine == "google_news" else "competitor_search"
        if engine == "google_shopping" or extra.get("tbm") == "shop":
            cache_kind = "pricing_pages"
        payload = _serp_call(engine, query, cache_kind=cache_kind, extra=extra)
        payloads.append((engine, payload))
        trace["queries"].append(query)
        trace["engines"].append(engine)
        if payload.get("error"):
            trace["errors"].append(str(payload["error"])[:120])
            continue
        hits = _count_hits(engine, payload)
        if engine == "google_shopping":
            trace["serp_shopping_hits"] += hits
        elif engine == "google_news":
            trace["serp_news_hits"] += hits
        elif engine in {"google_local", "google_maps"}:
            trace["serp_local_hits"] += hits
        else:
            trace["serp_search_hits"] += hits
        batch = extract_structured_from_payload(engine, payload, domain=domain, topic=topic)
        structured.extend(batch)
        trace["serp_reviews_hits"] += sum(1 for r in batch if r.get("record_type") == "buyer_voice")

    from iidatech.evidence_bank.bank_store import dedupe_competitor_rows

    entities = dedupe_competitor_rows(structured_to_competitor_entities(structured, domain=domain))
    trace["structured_records_generated"] = len(structured)
    trace_snapshot = {**trace, "entities": [e.get("company_name") for e in entities[:20]]}
    _serp_intel_trace_ctx.set(trace_snapshot)
    return {
        "entities": entities,
        "structured_records": structured,
        "queries": trace["queries"],
        "trace": dict(trace_snapshot),
        "enabled": True,
        "plan": plan,
    }


def serp_intelligence_trace() -> dict[str, Any]:
    return dict(_active_serp_trace())
