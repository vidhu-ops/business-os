"""Harvest verified competitor pricing from official pages via Firecrawl + SerpAPI."""

from __future__ import annotations



import os

import re

from typing import Any

from urllib.parse import urlparse



from iidatech.evidence_bank.pricing_parser import parse_pricing_page

from iidatech.validation.pricing_validator import filter_valid_pricing_rows



_PRICING_PATHS = ("/pricing", "/plans", "/pricing/", "/plans/", "/price", "/packages")

_AGGREGATOR_HOSTS = frozenset(

    {

        "g2.com",

        "capterra.com",

        "getapp.com",

        "softwareadvice.com",

        "trustpilot.com",

        "amazon.",

        "flipkart.com",

        "nykaa.com",

        "reddit.com",

        "youtube.com",

    }

)

_OFFICIAL_HOST_HINTS = re.compile(r"(pricing|plans|price|packages)", re.I)



KNOWN_VENDOR_PRICING_URLS: dict[str, str] = {

    "hubspot": "https://www.hubspot.com/pricing/crm",

    "pipedrive": "https://www.pipedrive.com/pricing",

    "salesforce": "https://www.salesforce.com/small-business/pricing/",

    "zoho crm": "https://www.zoho.com/crm/zohocrm-pricing.html",

    "zoho": "https://www.zoho.com/crm/zohocrm-pricing.html",

    "freshsales": "https://www.freshworks.com/crm/pricing/",

    "freshworks": "https://www.freshworks.com/crm/pricing/",

    "monday": "https://monday.com/pricing",

    "monday.com": "https://monday.com/pricing",

}



_DOMAIN_ALIASES = {

    "crm_automation": "b2b_saas",

    "saas_general": "b2b_saas",

    "general_market": "default",

}





def _as_dict(value: Any) -> dict:

    return value if isinstance(value, dict) else {}





def _as_list(value: Any) -> list:

    return value if isinstance(value, list) else []





def _host(url: str) -> str:

    try:

        return urlparse(str(url or "")).netloc.lower()

    except Exception:

        return ""





def _is_aggregator(url: str) -> bool:

    host = _host(url)

    return any(token in host for token in _AGGREGATOR_HOSTS)





def _validator_domain(domain: str) -> str:

    key = str(domain or "default").strip().lower()

    return _DOMAIN_ALIASES.get(key, key)





def _known_pricing_url(company: str) -> str:

    key = re.sub(r"\s+", " ", str(company or "").strip().lower())

    if key in KNOWN_VENDOR_PRICING_URLS:

        return KNOWN_VENDOR_PRICING_URLS[key]

    first = key.split()[0] if key else ""

    return KNOWN_VENDOR_PRICING_URLS.get(first, "")





def _guess_pricing_urls(base_url: str) -> list[str]:

    base = str(base_url or "").strip()

    if not base:

        return []

    parsed = urlparse(base if "://" in base else f"https://{base}")

    host = parsed.netloc or parsed.path.split("/")[0]

    if not host:

        return []

    scheme = parsed.scheme or "https"

    root = f"{scheme}://{host}"

    urls = [root + path for path in _PRICING_PATHS]

    if _OFFICIAL_HOST_HINTS.search(base):

        urls.insert(0, base)

    return urls





def _serp_pricing_page_url(company: str, *, hint_url: str = "") -> str:
    """SerpAPI pricing lookup removed — use hint URL or known vendor map only."""
    return ""





def _scrape_page_text(url: str) -> tuple[str, str]:

    key = str(os.getenv("FIRECRAWL_API_KEY") or os.getenv("FIRECRAWL_KEY") or "").strip()

    try:

        from on_demand_research import extract_page_text



        return extract_page_text(url, firecrawl_key=key, limit=4800)

    except Exception:

        return "", "unavailable"





def _competitor_seed_rows(

    competitors: list[dict[str, Any]],

    structured: list[dict[str, Any]],

    entities: list[dict[str, Any]],

    *,

    live_names: list[str] | None = None,

) -> list[dict[str, Any]]:

    seeds: list[dict[str, Any]] = []

    seen: set[str] = set()



    def _add(name: str, url: str = "") -> None:

        name = str(name or "").strip()

        if not name:

            return

        key = name.lower()

        if key in seen:

            return

        seen.add(key)

        seeds.append({"name": name, "url": str(url or _known_pricing_url(name) or "").strip()})



    for name in _as_list(live_names):

        _add(str(name))



    for row in competitors + structured + entities:

        if not isinstance(row, dict):

            continue

        name = str(

            row.get("name")

            or row.get("company_name")

            or row.get("company")

            or row.get("vendor")

            or row.get("title")

            or ""

        ).strip()

        url = str(

            row.get("official_url")

            or row.get("website")

            or row.get("source_url")

            or row.get("url")

            or ""

        ).strip()

        _add(name, url)

    return seeds





def harvest_verified_pricing(

    *,

    competitors: list[dict[str, Any]] | None = None,

    structured: list[dict[str, Any]] | None = None,

    entities: list[dict[str, Any]] | None = None,

    live_competitor_names: list[str] | None = None,

    topic: str = "",

    domain: str = "default",

    geography: str = "",

    max_pages: int | None = None,

) -> dict[str, Any]:

    budget = max_pages

    if budget is None:

        budget = int(

            os.getenv("IIDATECH_PRICING_HARVEST_MAX_PAGES")

            or os.getenv("FIRECRAWL_MAX_PAGE_EXTRACTS_PER_REPORT")

            or "5"

        )

    budget = max(0, min(budget, 8))



    seeds = _competitor_seed_rows(

        _as_list(competitors),

        _as_list(structured),

        _as_list(entities),

        live_names=_as_list(live_competitor_names),

    )[:10]



    harvested_rows: list[dict[str, Any]] = []

    trace: list[dict[str, Any]] = []

    pages_used = 0

    validator_domain = _validator_domain(domain)



    for seed in seeds:

        if pages_used >= budget:

            break

        company = seed["name"]

        hint_url = seed.get("url") or ""

        candidate_urls: list[str] = []



        known = _known_pricing_url(company)

        if known:

            candidate_urls.append(known)



        if hint_url and not _is_aggregator(hint_url):

            if _OFFICIAL_HOST_HINTS.search(hint_url):

                candidate_urls.append(hint_url)

            else:

                candidate_urls.extend(_guess_pricing_urls(hint_url))



        serp_url = _serp_pricing_page_url(company, hint_url=hint_url)

        if serp_url and serp_url not in candidate_urls:

            candidate_urls.insert(0, serp_url)



        deduped: list[str] = []

        seen_urls: set[str] = set()

        for url in candidate_urls:

            if url and url not in seen_urls:

                deduped.append(url)

                seen_urls.add(url)

        candidate_urls = deduped



        page_text = ""

        source_url = ""

        method = ""

        for url in candidate_urls:

            if pages_used >= budget:

                break

            text, method = _scrape_page_text(url)

            if len(text) < 80:

                trace.append({"company": company, "url": url, "status": "empty_page", "method": method})

                continue

            page_text = text

            source_url = url

            pages_used += 1

            break



        if not page_text:

            trace.append({"company": company, "status": "no_pricing_page", "candidates": candidate_urls[:4]})

            continue



        host = _host(source_url)

        source_type = "official_pricing_page" if _OFFICIAL_HOST_HINTS.search(source_url) else "official_site"

        parsed = parse_pricing_page(page_text, company=company, source_type=source_type)

        for tier in _as_list(parsed.get("tiers")):

            if not isinstance(tier, dict):

                continue

            plan = str(tier.get("plan_name") or company or "Standard").strip()

            monthly = str(tier.get("monthly_price") or "").strip()

            if not monthly:

                continue

            harvested_rows.append(

                {

                    "name": company,

                    "vendor": company,

                    "competitor": company,

                    "plan_name": plan,

                    "package": plan,

                    "monthly_price": monthly,

                    "estimated_price_band": monthly,

                    "price_band": monthly,

                    "pricing": monthly,

                    "source": source_url,

                    "url": source_url,

                    "source_url": source_url,

                    "publisher": host,

                    "source_family": "official_pricing_page",

                    "source_type": "official_pricing_page",

                    "verification_status": "verified_pricing_page",

                    "evidence_backed": True,

                    "pricing_confidence": parsed.get("pricing_confidence"),

                    "extraction_method": method,

                }

            )



        trace.append(

            {

                "company": company,

                "url": source_url,

                "status": "parsed",

                "tiers": len(_as_list(parsed.get("tiers"))),

                "method": method,

            }

        )



    validated = filter_valid_pricing_rows(harvested_rows, domain=validator_domain)

    valid_rows = list(validated.get("valid") or [])

    status = "verified" if len(valid_rows) >= 2 else ("partial" if valid_rows or harvested_rows else "insufficient")

    return {

        "verified_rows": valid_rows,

        "all_rows": harvested_rows,

        "rejected_rows": list(validated.get("rejected") or []),

        "verified_count": len(valid_rows),

        "pages_scraped": pages_used,

        "trace": trace,

        "status": status,

        "validator_domain": validator_domain,

    }

