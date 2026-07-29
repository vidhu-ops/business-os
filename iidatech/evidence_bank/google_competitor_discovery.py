"""Live competitor discovery for IIDATECH evidence bank (Perplexity Sonar + Firecrawl verify)."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

_SERP_TRACE: dict[str, Any] = {"queries": [], "raw_hits": 0, "entities": []}

REVIEW_AGGREGATOR_SITES = ("g2.com", "capterra.com", "trustradius.com", "trustpilot.com")

DOMAIN_QUERY_HINTS: dict[str, list[str]] = {
    "crm_automation": ["CRM", "sales CRM", "CRM software SMB"],
    "d2c_skincare": ["skincare brand", "D2C beauty", "skincare India"],
    "festive_retail": ["festive decoration kit", "Diwali decor", "Ganesh Chaturthi kit"],
    "event_services": ["event decor rental", "mandap rental", "drone light show"],
    "wedding_services": ["wedding mandap", "wedding decor", "wedding planner"],
    "decor_retail": ["home decor kit", "decoration products", "apartment decor"],
    "gifting_retail": ["gift hamper", "festive gifting", "corporate gift box"],
    "local_services": ["local service provider", "society vendor", "hyperlocal service"],
    "home_services": ["home cleaning service", "home repair", "facility maintenance"],
    "creator_business": ["content creator business", "influencer monetization"],
    "dental_clinics": ["dental clinic", "dental chain", "dentist"],
    "automotive_retail": ["car dealership", "auto garage", "automotive retail"],
    "agency_services": ["marketing agency", "digital agency", "creative agency"],
    "restaurants": ["restaurant chain", "QSR brand", "cloud kitchen"],
    "saas_general": ["B2B SaaS", "SaaS startup", "software company"],
    "clinic_workflow": ["clinic management", "practice management software", "EMR"],
    "ecommerce_retail": ["ecommerce brand", "online retail", "D2C store"],
    "logistics": ["logistics company", "3PL provider", "last mile delivery"],
    "fintech": ["fintech startup", "payments platform", "neobank"],
    "edtech": ["edtech platform", "online learning", "LMS"],
    "legaltech": ["legal tech", "contract management", "law firm software"],
    "hrtech": ["HR software", "payroll platform", "ATS recruiting"],
    "proptech": ["proptech", "property management software", "real estate tech"],
    "healthcare_saas": ["healthcare SaaS", "health tech", "patient engagement"],
}

KNOWN_LEADERS: dict[str, list[str]] = {
    "crm_automation": ["HubSpot", "Salesforce", "Zoho CRM", "Pipedrive", "Microsoft Dynamics 365"],
    "d2c_skincare": ["Mamaearth", "Nykaa", "Minimalist", "Pilgrim", "Dot and Key"],
    "festive_retail": ["Amazon India", "Flipkart", "IndiaMART", "Etsy", "Meesho"],
    "event_services": ["WedMeGood", "Weddingz", "Eventila", "BookEventz"],
    "wedding_services": ["WedMeGood", "Weddingz", "ShaadiSaga", "UrbanClap Wedding"],
    "decor_retail": ["Amazon India", "Flipkart", "Pepperfry", "Urban Ladder", "IndiaMART"],
    "gifting_retail": ["Ferns N Petals", "IGP", "Amazon India", "Flipkart"],
    "dental_clinics": ["Clove Dental", "Sabka Dentist", "Dental Solutions", "Apollo Dental"],
    "automotive_retail": ["CarDekho", "CarWale", "Spinny", "Cars24", "Mahindra First Choice"],
    "agency_services": ["WPP", "Ogilvy", "Dentsu", "Publicis", "Accenture Song"],
    "restaurants": ["McDonalds", "Dominos", "Starbucks", "KFC", "Subway"],
}


def serp_enabled() -> bool:
    """Backward-compatible alias — evidence bank now uses Perplexity, not SerpAPI."""
    from iidatech.evidence_bank.perplexity_client import perplexity_enabled

    return perplexity_enabled()


def perplexity_enabled() -> bool:
    from iidatech.evidence_bank.perplexity_client import perplexity_enabled as _enabled

    return _enabled()


def _serp_api_key() -> str:
    try:
        from on_demand_research import local_secret_value

        return local_secret_value("SERPAPI_KEY", "SERP_API_KEY", "SERPAPI_API_KEY")
    except Exception:
        pass
    for name in ("SERPAPI_KEY", "SERP_API_KEY", "SERPAPI_API_KEY"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _serp_max_queries() -> int:
    try:
        return max(1, int(os.getenv("SERPAPI_MAX_QUERIES_PER_REPORT", "4")))
    except ValueError:
        return 4


def build_competitor_discovery_queries(topic: str, domain: str, target: str = "") -> dict[str, list[str]]:
    base = f"{topic} {target}".strip()
    hints = DOMAIN_QUERY_HINTS.get(domain, [topic])
    primary = hints[0] if hints else topic
    leaders = KNOWN_LEADERS.get(domain, [])[:3]
    leader_a = leaders[0] if leaders else primary
    leader_b = leaders[1] if len(leaders) > 1 else primary
    local_suffix = target if target and target.lower() not in {"global", ""} else ""

    discovery = [
        f"best {primary} for SMB",
        f"{primary} alternatives to {leader_a}",
        f"top {primary} companies {local_suffix}".strip(),
        f"best {primary} brands {local_suffix}".strip() if local_suffix else f"top {primary} startups",
    ]
    comparison = [
        f"{leader_a} vs {leader_b}",
        f"best alternatives to {leader_a}",
        f"{primary} comparison {local_suffix}".strip(),
    ]
    review_aggregators = [
        f"{primary} site:g2.com",
        f"{primary} site:capterra.com",
        f"{primary} site:trustradius.com",
        f"{primary} reviews site:trustpilot.com",
    ]
    local_queries: list[str] = []
    if local_suffix:
        local_queries = [
            f"top {primary} in {local_suffix}",
            f"best premium {primary} {local_suffix}",
            f"best {primary} near {local_suffix}",
        ]
    pricing = [
        f"{leader_a} pricing plans",
        f"site:{_domain_slug(leader_a)} pricing" if leader_a else f"{primary} pricing per month",
        f"{primary} pricing site:g2.com",
    ]
    return {
        "competitor_discovery": discovery,
        "comparison": comparison,
        "review_aggregators": review_aggregators,
        "local_competitors": local_queries,
        "pricing_discovery": pricing,
    }


def _domain_slug(company: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "", company.lower().split()[0])
    return f"{slug}.com" if slug else "company.com"


def _serp_google_search(query: str, *, num: int = 8) -> dict[str, Any]:
    from iidatech.storage.cache_repository import infer_cache_kind
    from iidatech.storage.provider_cache import cached_provider_call

    def _call() -> dict[str, Any]:
        import requests

        key = _serp_api_key()
        if not key:
            return {"organic_results": [], "error": "missing_serpapi_key"}
        params = {
            "engine": "google",
            "q": query,
            "api_key": key,
            "num": min(10, max(3, num)),
        }
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
                    return {
                        "organic_results": [],
                        "error": str(data.get("error") or response.text or response.status_code)[:200],
                    }
                if isinstance(data, dict) and data.get("error"):
                    return {"organic_results": [], "error": str(data.get("error"))[:200]}
                return data if isinstance(data, dict) else {"organic_results": []}
            except Exception as exc:
                last_error = str(exc)[:200]
                if attempt == 0:
                    time.sleep(1.5)
        return {"organic_results": [], "error": last_error or "serpapi_request_failed"}

    return cached_provider_call(
        "serpapi",
        query,
        infer_cache_kind(query, "serpapi"),
        "",
        _call,
        model="google",
        estimated_cost=0.01,
    )


def normalize_competitor_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (name or "").lower())


def _looks_like_noise(norm: str) -> bool:
    noise = {
        "best", "top", "review", "reviews", "pricing", "alternatives", "comparison",
        "software", "guide", "reddit", "quora", "wikipedia", "youtube", "linkedin",
        "user", "page", "home", "login", "signin", "signup", "menu", "search",
        "results", "about", "contact", "blog", "news", "features", "product",
        "products", "services", "support", "help", "download", "free", "trial",
        "more", "read", "view", "click", "here", "learn", "get", "see", "all",
        "crm", "crmsoftware", "softwarecrm", "app", "web", "site", "www",
    }
    if norm in noise or len(norm) < 3:
        return True
    if norm.isdigit():
        return True
    return False


def is_valid_competitor_display_name(name: str) -> bool:
    """Reject SERP/shopping/UI junk before counting live competitors."""
    text = str(name or "").strip()
    if not text or len(text) < 2:
        return False
    if len(text) > 55:
        return False
    norm = normalize_competitor_name(text)
    if _looks_like_noise(norm):
        return False
    low = text.lower()
    if low in {"user", "page", "home", "login", "sign in", "sign up", "menu", "search"}:
        return False
    if re.search(r"\b(vendor\s*\d+|generic competitor|d2c skincare vendor)\b", low):
        return False
    common = {
        "user", "reviews", "review", "small", "business", "best", "marketing", "automation",
        "workflow", "platform", "software", "choose", "choosing", "compare", "july", "june", "bring",
        "commerce", "ecommerce", "brands", "india", "personal", "care", "primarily", "we",
        "the", "and", "for", "vs", "quick", "study", "case", "surat",
        "sales", "customer", "desk", "management", "verified", "agile", "verified", "choosing",
        "marketing", "workflow", "platform", "share", "sharecrm",
    }
    words = re.findall(r"[a-z0-9]+", low)
    if not words:
        return False
    if all(w in common for w in words):
        return False
    if len(words) <= 2 and words[0] in common:
        return False
    return True


def _names_from_serp_text(text: str, domain: str) -> list[str]:
    names: list[str] = []
    for match in re.finditer(r"([A-Z][A-Za-z0-9&'.-]{1,40})\s+vs\.?\s+([A-Z][A-Za-z0-9&'.-]{1,40})", text):
        names.extend([match.group(1), match.group(2)])
    for match in re.finditer(r"alternatives?\s+to\s+([A-Z][A-Za-z0-9&'.-]{1,40})", text, re.I):
        names.append(match.group(1))
    for match in re.finditer(r"([A-Z][A-Za-z0-9&'.-]{2,30})\s+(CRM|Review|Pricing|Software|Platform|App)", text):
        names.append(match.group(1))
    for leader in KNOWN_LEADERS.get(domain, []):
        if leader.lower() in text.lower():
            names.append(leader)
    deduped: list[str] = []
    seen: set[str] = set()
    for n in names:
        key = normalize_competitor_name(n)
        if key and key not in seen:
            seen.add(key)
            deduped.append(n)
    return deduped[:8]


def extract_competitor_entities(search_results: list[dict[str, Any]], *, domain: str = "") -> list[dict[str, Any]]:
    entities: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(name: str, source_url: str, source_type: str, category: str, mention_count: int = 1):
        norm = normalize_competitor_name(name)
        if not norm or len(norm) < 3 or norm in seen:
            return
        if _looks_like_noise(norm):
            return
        seen.add(norm)
        entities.append({
            "company_name": name.strip()[:120],
            "normalized_name": norm,
            "source_urls": [source_url] if source_url else [],
            "source_type": source_type,
            "category": category,
            "mention_frequency": mention_count,
            "discovered_via": "serpapi",
            "provisional": True,
            "verification_status": "unverified",
            "industry": domain or "general",
            "country": "Global",
            "positioning": f"Discovered via SerpAPI ({source_type})",
            "pricing": "unknown",
            "metrics": {"mention_frequency": mention_count},
            "strengths": [],
            "weaknesses": [],
            "complaints": [],
            "gtm_model": "unknown",
            "trust_score": 0.62 if "review" in source_type else 0.58,
            "last_verified": datetime.now(timezone.utc).strftime("%Y-%m"),
        })

    for block in search_results:
        if not isinstance(block, dict):
            continue
        for item in block.get("organic_results") or []:
            title = str(item.get("title") or "")
            link = str(item.get("link") or item.get("url") or "")
            snippet = str(item.get("snippet") or "")
            source_type = "serp_organic"
            if any(site in link.lower() for site in REVIEW_AGGREGATOR_SITES):
                source_type = "review_platform"
            for name in _names_from_serp_text(f"{title} {snippet}", domain):
                _add(name, link, source_type, "discovered", 1)
        kg = block.get("knowledge_graph") or {}
        if isinstance(kg, dict) and kg.get("title"):
            _add(str(kg["title"]), str(kg.get("website") or ""), "knowledge_graph", "market_leader", 2)
        for rel in block.get("related_questions") or []:
            if isinstance(rel, dict):
                for name in _names_from_serp_text(str(rel.get("question") or ""), domain):
                    _add(name, "", "related_question", "discovered", 1)

    return entities


def discover_live_competitors(
    topic: str,
    domain: str,
    target: str = "",
    *,
    max_queries: int | None = None,
    industry: str = "",
) -> dict[str, Any]:
    global _SERP_TRACE
    from iidatech.evidence_bank.perplexity_client import fetch_market_intelligence

    result = fetch_market_intelligence(topic, domain, target, industry=industry or domain)
    intel = result.get("trace") or {}
    _SERP_TRACE = {
        "queries": result.get("queries", []),
        "query_families": {"provider": "perplexity_sonar"},
        "raw_hits": int(intel.get("perplexity_hits") or 0),
        "entities": [e.get("company_name") for e in (result.get("entities") or [])[:20]],
        "errors": intel.get("errors") or [],
        "pricing_discrepancies": result.get("pricing_discrepancies") or [],
        **intel,
    }
    return {
        "entities": result.get("entities") or [],
        "structured_records": result.get("structured_records") or [],
        "queries": result.get("queries") or [],
        "trace": competitor_search_trace(),
        "enabled": bool(result.get("enabled")),
        "report_degraded": bool(result.get("report_degraded")),
        "degrade_reason": str(result.get("degrade_reason") or ""),
        "pricing_discrepancies": result.get("pricing_discrepancies") or [],
        "raw_result_count": len(result.get("structured_records") or []),
    }


def competitor_search_trace() -> dict[str, Any]:
    return dict(_SERP_TRACE)


def serp_entities_to_learned_records(entities: list[dict[str, Any]], domain: str, target: str):
    from iidatech.evidence_bank.bank_store import bank_row_to_learned_record
    records = []
    for row in entities:
        row = dict(row)
        row.setdefault("trust_score", 0.60)
        records.append(bank_row_to_learned_record(row, domain, target))
    return records