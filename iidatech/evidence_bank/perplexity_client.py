"""Perplexity Sonar market intelligence for IIDATECH evidence bank."""
from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

_PRICE_NUM_RE = re.compile(
    r"(?:US\$|\$|EUR|GBP|INR)\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"
    r"|(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:/mo|per month|/month|/user|per user)"
    r"|[\u20b9\u20ac\u00a3]\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)",
    re.I,
)

_PROMPT = """You are a market research analyst. For the topic below, return
STRICT JSON only (no markdown, no commentary) with this exact shape:

{{
  "top_competitors": [
    {{"name": "", "pricing": "", "positioning": "", "strengths": [], "weaknesses": [], "source_url": ""}}
  ],
  "market_size_estimate": "",
  "buyer_complaints": [""],
  "pricing_benchmarks": "",
  "sources": [""]
}}

Only include facts you can support with a real source. If you do not have
enough real data for a field, use an empty string or empty list rather than
guessing.

Topic: {topic}
Industry: {industry}
Geography: {geography}
"""


def perplexity_enabled() -> bool:
    return bool(_api_key())


def _api_key() -> str:
    try:
        from iidatech.execution.session_api_keys import get_perplexity_override

        override = get_perplexity_override()
        if override:
            return override
    except ImportError:
        pass
    try:
        from on_demand_research import local_secret_value

        return local_secret_value("PERPLEXITY_API_KEY", "PPLX_API_KEY")
    except Exception:
        pass
    for name in ("PERPLEXITY_API_KEY", "PPLX_API_KEY"):
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def _parse_json_blob(text: str) -> dict[str, Any] | None:
    if not text:
        return None
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def _extract_monthly_amount(price_text: str) -> float | None:
    text = str(price_text or "").strip()
    if not text:
        return None
    match = _PRICE_NUM_RE.search(text)
    if not match:
        return None
    raw = match.group(1) or match.group(2) or match.group(3)
    if not raw:
        return None
    try:
        return float(raw.replace(",", ""))
    except ValueError:
        return None


_MONTHLY_PRICE_RE = re.compile(r"/mo\b|/month\b|per\s+month\b|/user\b|per\s+user\b|/seat\b|per\s+seat\b", re.I)

from iidatech.services.market_currency import currency_for_geography as _currency_for_geography

_GEO_EXPECTED_CURRENCY: dict[str, str] = {
    "india": "INR",
    "united states": "USD",
    "usa": "USD",
    "u.s.": "USD",
    "united kingdom": "GBP",
    "uk": "GBP",
}


def _detect_price_currency(price_text: str) -> str | None:
    text = str(price_text or "")
    upper = text.upper()
    if "₹" in text or re.search(r"\b(?:INR|RS\.?)\b", upper):
        return "INR"
    if "£" in text or re.search(r"\bGBP\b", upper):
        return "GBP"
    if "€" in text or re.search(r"\bEUR\b", upper):
        return "EUR"
    if "$" in text or re.search(r"\b(?:USD|US\$)\b", upper):
        return "USD"
    return None


def _expected_currency_for_geography(geography: str) -> str | None:
    cur = _currency_for_geography(geography)
    if cur.get("localized"):
        return str(cur.get("code") or "") or None
    geo = str(geography or "").strip().lower()
    if not geo or geo in {"global", "world", "worldwide", "international"}:
        return None
    for key, currency in _GEO_EXPECTED_CURRENCY.items():
        if key in geo:
            return currency
    return None


def _consumer_product_vertical(*, domain: str, industry: str, topic: str = "") -> bool:
    blob = f"{domain} {industry} {topic}".lower()
    needles = (
        "d2c",
        "ecommerce",
        "retail",
        "skincare",
        "grooming",
        "baby",
        "ayurvedic",
        "beauty",
        "home products",
        "eco-friendly",
        "supplements",
        "personal care",
        "organic brand",
    )
    return any(needle in blob for needle in needles)


def _backfill_price_plausible(
    price_text: str,
    *,
    geography: str,
    domain: str,
    industry: str,
    topic: str = "",
) -> tuple[bool, str]:
    """Reject scraped prices with wrong currency for geography or implausible vertical bands."""
    text = str(price_text or "").strip()
    if not text:
        return False, "empty_price"

    currency = _detect_price_currency(text)
    expected = _expected_currency_for_geography(geography)
    if expected and currency and currency != expected:
        return False, f"currency_mismatch:{currency}_vs_{expected}"

    amount = _extract_monthly_amount(text)
    consumer = _consumer_product_vertical(domain=domain, industry=industry, topic=topic)
    monthly = bool(_MONTHLY_PRICE_RE.search(text))

    if consumer and monthly:
        return False, "consumer_vertical_monthly_subscription"

    if consumer and currency == "USD" and amount is not None and amount > 250:
        return False, "consumer_vertical_usd_too_high"

    if consumer and currency == "INR" and amount is not None and amount > 25_000:
        return False, "consumer_vertical_inr_too_high"

    if expected == "INR" and currency == "USD":
        return False, "currency_mismatch:USD_vs_INR"

    return True, "ok"


def _row_passes_report_relevance_gate(
    row: dict[str, Any],
    *,
    topic: str,
    industry: str,
    domain: str,
) -> bool:
    try:
        from iidatech.validation.relevance_gate import is_record_relevant_to_report

        record = {
            "source_family": "pricing_reference",
            "title": f"{row.get('name', '')} pricing",
            "publisher": str(row.get("name") or ""),
            "metric_name": "Pricing signal",
            "metric_value": str(row.get("price") or row.get("firecrawl_pricing") or ""),
            "text": " ".join(
                str(row.get(key) or "")
                for key in ("name", "price", "source_url", "pricing_page_url", "firecrawl_pricing")
            ),
            "url": str(row.get("source_url") or row.get("pricing_page_url") or ""),
        }
        return is_record_relevant_to_report(record, topic, industry, domain)[0]
    except Exception:
        return True


def _flag_unverified_backfill(
    row: dict[str, Any],
    ent: dict[str, Any] | None,
    *,
    scraped_band: str,
    scraped_url: str,
    reason: str,
) -> None:
    row["firecrawl_pricing"] = scraped_band
    row["pricing_page_url"] = scraped_url
    row["verification_status"] = "unverified_currency_mismatch"
    row["price_plausibility_reason"] = reason
    row["price_source"] = "firecrawl_backfill_rejected"
    if ent:
        ent["firecrawl_pricing"] = scraped_band
        ent["pricing_page_url"] = scraped_url
        ent["verification_status"] = "unverified_currency_mismatch"
        ent["price_plausibility_reason"] = reason


def _prices_differ_meaningfully(reported: str, scraped: str) -> bool:
    reported = str(reported or "").strip()
    scraped = str(scraped or "").strip()
    if not reported or not scraped:
        return False
    a = _extract_monthly_amount(reported)
    b = _extract_monthly_amount(scraped)
    if a is not None and b is not None:
        baseline = max(a, b, 1.0)
        return abs(a - b) / baseline > 0.15
    return reported.lower() not in scraped.lower() and scraped.lower() not in reported.lower()


def _call_perplexity_api(topic: str, industry: str, geography: str) -> dict[str, Any]:
    key = _api_key()
    if not key:
        return {"error": "PERPLEXITY_API_KEY not configured", "enabled": False}
    prompt = _PROMPT.format(topic=topic, industry=industry, geography=geography)
    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
        content = str((data.get("choices") or [{}])[0].get("message", {}).get("content") or "")
        parsed = _parse_json_blob(content)
        return {
            "enabled": True,
            "raw_content": content,
            "parsed": parsed,
            "usage": data.get("usage") or {},
            "model": data.get("model") or "sonar-pro",
            "prompt": prompt[:400],
        }
    except Exception as exc:
        return {"error": str(exc)[:240], "enabled": False}


def _parsed_to_structured(
    parsed: dict[str, Any],
    *,
    domain: str,
    topic: str,
    industry: str = "",
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    competitors = parsed.get("top_competitors") or []
    if isinstance(competitors, list):
        for row in competitors:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or "").strip()
            if not name:
                continue
            price = str(row.get("pricing") or "").strip()
            source_url = str(row.get("source_url") or "").strip()
            comp = {
                "record_type": "competitor",
                "name": name[:120],
                "price": price,
                "positioning": str(row.get("positioning") or "")[:300],
                "strengths": list(row.get("strengths") or [])[:6],
                "weaknesses": list(row.get("weaknesses") or [])[:6],
                "source_engine": "perplexity_sonar",
                "source_url": source_url,
                "source_type": "perplexity_sonar",
                "industry": domain,
                "discovered_via": "perplexity_sonar",
            }
            if _row_passes_report_relevance_gate(
                comp, topic=topic, industry=industry or domain, domain=domain
            ):
                comp["verification_status"] = "perplexity_live"
            else:
                comp["verification_status"] = "unverified_off_topic"
            records.append(comp)
            if price:
                pricing_row = {
                    "record_type": "pricing",
                    "name": name[:120],
                    "price": price,
                    "source_url": source_url,
                    "source_engine": "perplexity_sonar",
                    "source_type": "perplexity_sonar",
                }
                if _row_passes_report_relevance_gate(
                    pricing_row, topic=topic, industry=industry or domain, domain=domain
                ):
                    pricing_row["verification_status"] = "perplexity_live"
                else:
                    pricing_row["verification_status"] = "unverified_off_topic"
                records.append(pricing_row)

    market_size = str(parsed.get("market_size_estimate") or "").strip()
    if market_size:
        records.append(
            {
                "record_type": "market_signal",
                "name": "market size estimate",
                "metric": market_size[:200],
                "snippet": market_size[:500],
                "source_engine": "perplexity_sonar",
                "verification_status": "perplexity_live",
                "confidence_tier": "proxy_hint",
            }
        )

    benchmarks = str(parsed.get("pricing_benchmarks") or "").strip()
    if benchmarks:
        records.append(
            {
                "record_type": "market_signal",
                "name": "pricing benchmarks",
                "metric": benchmarks[:200],
                "snippet": benchmarks[:500],
                "source_engine": "perplexity_sonar",
                "verification_status": "perplexity_live",
                "confidence_tier": "proxy_hint",
            }
        )

    complaints = parsed.get("buyer_complaints") or []
    if isinstance(complaints, list):
        for complaint in complaints[:8]:
            text = str(complaint or "").strip()
            if len(text) < 8:
                continue
            records.append(
                {
                    "record_type": "buyer_voice",
                    "name": "buyer sentiment",
                    "complaints": [text],
                    "review_text": text[:500],
                    "source_engine": "perplexity_sonar",
                    "verification_status": "perplexity_live",
                }
            )
    return records


def _pricing_urls_for_competitor(name: str, source_url: str) -> list[str]:
    from iidatech.services.pricing_harvest import _guess_pricing_urls, _known_pricing_url

    urls: list[str] = []
    if source_url:
        urls.append(source_url)
    known = _known_pricing_url(name)
    if known:
        urls.append(known)
    if source_url:
        urls.extend(_guess_pricing_urls(source_url))
    return [u for i, u in enumerate(urls) if u and u not in urls[:i]]


def _scrape_competitor_price(name: str, urls: list[str]) -> tuple[str, str]:
    from iidatech.evidence_bank.pricing_parser import parse_pricing_page
    from iidatech.services.pricing_harvest import _scrape_page_text

    for url in urls[:3]:
        text, method = _scrape_page_text(url)
        if not text or method == "unavailable":
            continue
        parsed = parse_pricing_page(text, company=name, source_type="official_site")
        tiers = list(parsed.get("tiers") or [])
        if tiers:
            scraped_band = str(tiers[0].get("monthly_price") or "").strip()
            if scraped_band:
                return scraped_band, url
    return "", ""


def _verify_pricing_with_firecrawl(
    structured: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    *,
    geography: str = "",
    domain: str = "",
    industry: str = "",
    topic: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    discrepancies: list[dict[str, Any]] = []
    firecrawl_key = str(os.getenv("FIRECRAWL_API_KEY") or os.getenv("FIRECRAWL_KEY") or "").strip()
    if not firecrawl_key:
        return structured, entities, discrepancies

    competitor_rows = [r for r in structured if str(r.get("record_type") or "").lower() == "competitor"]
    entity_by_name = {
        str(e.get("company_name") or e.get("name") or "").strip().lower(): e
        for e in entities
        if isinstance(e, dict)
    }

    for row in competitor_rows[:10]:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        reported = str(row.get("price") or "").strip()
        source_url = str(row.get("source_url") or "").strip()
        if not reported and not source_url:
            continue
        urls = _pricing_urls_for_competitor(name, source_url)
        if not urls:
            continue

        scraped_band, scraped_url = _scrape_competitor_price(name, urls)
        if not scraped_band:
            continue

        ent = entity_by_name.get(name.lower())
        plausible, plaus_reason = _backfill_price_plausible(
            scraped_band,
            geography=geography,
            domain=domain,
            industry=industry,
            topic=topic,
        )

        if not reported:
            if not plausible:
                _flag_unverified_backfill(
                    row, ent, scraped_band=scraped_band, scraped_url=scraped_url, reason=plaus_reason
                )
                continue
            if not _row_passes_report_relevance_gate(
                row, topic=topic, industry=industry, domain=domain
            ):
                _flag_unverified_backfill(
                    row,
                    ent,
                    scraped_band=scraped_band,
                    scraped_url=scraped_url,
                    reason="off_topic_for_report",
                )
                continue
            row["price"] = scraped_band
            row["firecrawl_pricing"] = scraped_band
            row["pricing_page_url"] = scraped_url
            row["verification_status"] = "firecrawl_verified"
            row["price_source"] = "firecrawl_backfill"
            if ent:
                ent["pricing"] = scraped_band
                ent["firecrawl_pricing"] = scraped_band
                ent["pricing_page_url"] = scraped_url
                ent["verification_status"] = "firecrawl_verified"
            continue

        if _prices_differ_meaningfully(reported, scraped_band):
            discrepancy = {
                "competitor": name,
                "perplexity_pricing": reported,
                "firecrawl_pricing": scraped_band,
                "pricing_page_url": scraped_url,
                "flag": "pricing_discrepancy",
            }
            discrepancies.append(discrepancy)
            row["pricing_discrepancy"] = True
            row["perplexity_pricing"] = reported
            row["firecrawl_pricing"] = scraped_band
            row["pricing_page_url"] = scraped_url
            row["verification_status"] = "pricing_discrepancy"
            if ent:
                ent["pricing_discrepancy"] = True
                ent["perplexity_pricing"] = reported
                ent["firecrawl_pricing"] = scraped_band
                ent["pricing_page_url"] = scraped_url
                ent["verification_status"] = "pricing_discrepancy"
        else:
            if not plausible:
                _flag_unverified_backfill(
                    row, ent, scraped_band=scraped_band, scraped_url=scraped_url, reason=plaus_reason
                )
                continue
            if not _row_passes_report_relevance_gate(
                row, topic=topic, industry=industry, domain=domain
            ):
                _flag_unverified_backfill(
                    row,
                    ent,
                    scraped_band=scraped_band,
                    scraped_url=scraped_url,
                    reason="off_topic_for_report",
                )
                continue
            row["verification_status"] = "firecrawl_verified"
            row["price"] = scraped_band
            if ent:
                ent["pricing"] = scraped_band
                ent["verification_status"] = "firecrawl_verified"

    return structured, entities, discrepancies


def fetch_market_intelligence(
    topic: str,
    domain: str,
    target: str = "",
    *,
    industry: str = "",
) -> dict[str, Any]:
    """Fetch competitor/pricing/TAM/buyer data via Perplexity; verify pricing with Firecrawl."""
    trace: dict[str, Any] = {
        "provider": "perplexity_sonar",
        "model": "sonar-pro",
        "perplexity_hits": 0,
        "structured_records_generated": 0,
        "firecrawl_checks": 0,
        "pricing_discrepancies": 0,
        "errors": [],
    }
    empty: dict[str, Any] = {
        "entities": [],
        "structured_records": [],
        "queries": [],
        "trace": trace,
        "enabled": False,
        "report_degraded": True,
        "degrade_reason": "",
        "pricing_discrepancies": [],
    }

    if not perplexity_enabled():
        trace["errors"].append("PERPLEXITY_API_KEY not configured")
        empty["degrade_reason"] = "perplexity_not_configured"
        return empty

    api = _call_perplexity_api(topic, industry or domain, target or "Global")
    if api.get("error") or not api.get("parsed"):
        err = str(api.get("error") or "perplexity_parse_failed")
        trace["errors"].append(err)
        empty["trace"] = trace
        empty["degrade_reason"] = err
        return empty

    parsed = api["parsed"]
    structured = _parsed_to_structured(parsed, domain=domain, topic=topic, industry=industry)
    trace["perplexity_hits"] = len(structured)

    try:
        from iidatech.evidence_bank.serp_intelligence import structured_to_competitor_entities

        entities = structured_to_competitor_entities(structured, domain=domain)
        for ent in entities:
            ent["discovered_via"] = "perplexity_sonar"
            ent["source_type"] = "perplexity_sonar"
    except Exception as exc:
        entities = []
        trace["errors"].append("entity_build:" + str(exc)[:120])

    structured, entities, discrepancies = _verify_pricing_with_firecrawl(
        structured,
        entities,
        geography=target or "Global",
        domain=domain,
        industry=industry or domain,
        topic=topic,
    )
    trace["firecrawl_checks"] = len(
        [r for r in structured if r.get("record_type") == "competitor" and (r.get("price") or r.get("source_url"))]
    )
    trace["firecrawl_backfills"] = sum(
        1 for r in structured
        if r.get("record_type") == "competitor" and r.get("price_source") == "firecrawl_backfill"
    )
    trace["firecrawl_backfill_rejected"] = sum(
        1 for r in structured
        if r.get("record_type") == "competitor" and r.get("price_source") == "firecrawl_backfill_rejected"
    )
    trace["pricing_discrepancies"] = len(discrepancies)
    trace["structured_records_generated"] = len(structured)
    trace["usage"] = api.get("usage") or {}

    prompt_label = "perplexity_sonar:" + topic[:80] + ":" + (target or "Global")
    degraded = not structured and not entities

    return {
        "entities": entities,
        "structured_records": structured,
        "queries": [prompt_label],
        "trace": trace,
        "enabled": bool(structured or entities),
        "report_degraded": degraded,
        "degrade_reason": "perplexity_empty_response" if degraded else "",
        "pricing_discrepancies": discrepancies,
        "raw_sources": list(parsed.get("sources") or [])[:12],
    }


_AGENT_API_URL = "https://api.perplexity.ai/v1/responses"


def report_perplexity_model() -> str:
    return (os.getenv("PERPLEXITY_REPORT_MODEL") or os.getenv("PERPLEXITY_MODEL") or "sonar").strip()


def report_search_model() -> str:
    return (os.getenv("PERPLEXITY_SEARCH_MODEL") or "sonar-pro").strip()


def fetch_web_research_harvest(
    prompt: str,
    *,
    timeout: int = 180,
) -> dict[str, Any]:
    """Live web search via Sonar-pro; returns parsed JSON + Perplexity citations."""
    return call_perplexity_json(prompt, model=report_search_model(), timeout=timeout)


def report_financial_model() -> str:
    for name in ("PERPLEXITY_FINANCIAL_MODEL", "IIDATECH_FINANCIAL_MODEL"):
        val = (os.getenv(name) or "").strip()
        if val:
            return val
    return "anthropic/claude-opus-4-8"


def report_analyst_model() -> str:
    for name in ("PERPLEXITY_ANALYST_MODEL", "IIDATECH_ANALYST_MODEL"):
        val = (os.getenv(name) or "").strip()
        if val:
            return val
    return "anthropic/claude-sonnet-4-5"


def _is_agent_model(model: str) -> bool:
    return "/" in str(model or "").strip()


def _extract_agent_output_text(data: dict[str, Any]) -> str:
    parts: list[str] = []
    for item in data.get("output") or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "message":
            for block in item.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "output_text":
                    parts.append(str(block.get("text") or ""))
        elif item.get("type") == "output_text":
            parts.append(str(item.get("text") or ""))
    return "".join(parts)


def call_perplexity_agent_json(
    prompt: str,
    *,
    model: str,
    max_output_tokens: int = 4096,
    timeout: int = 200,
) -> dict[str, Any]:
    """Call Perplexity Agent API (/v1/responses) for third-party models (anthropic/*, perplexity/glm-5.2, etc.)."""
    key = _api_key()
    if not key:
        return {"error": "PERPLEXITY_API_KEY not configured", "enabled": False}
    model_name = str(model or "").strip()
    if not model_name:
        return {"error": "model required", "enabled": False}
    payload: dict[str, Any] = {
        "model": model_name,
        "input": prompt,
        "max_output_tokens": int(max_output_tokens),
    }
    try:
        resp = requests.post(
            _AGENT_API_URL,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        if resp.status_code >= 400:
            return {"error": f"HTTP {resp.status_code}: {resp.text[:300]}", "enabled": False}
        data = resp.json()
        if data.get("error"):
            err = data["error"]
            if isinstance(err, dict):
                return {"error": str(err.get("message") or err)[:300], "enabled": False}
            return {"error": str(err)[:300], "enabled": False}
        text = _extract_agent_output_text(data)
        parsed = _parse_json_blob(text)
        return {
            "enabled": True,
            "raw_content": text,
            "parsed": parsed if isinstance(parsed, dict) else {},
            "usage": data.get("usage") or {},
            "model": str(data.get("model") or model_name),
            "api": "agent",
        }
    except Exception as exc:
        return {"error": str(exc)[:300], "enabled": False}


def call_perplexity_json(
    prompt: str,
    *,
    timeout: int = 120,
    search_domain_filter: list[str] | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Call Perplexity with an arbitrary prompt; return parsed JSON when the model complies."""
    model_name = (model or report_perplexity_model()).strip() or "sonar"
    if _is_agent_model(model_name):
        return call_perplexity_agent_json(
            prompt,
            model=model_name,
            max_output_tokens=4096,
            timeout=timeout,
        )
    key = _api_key()
    if not key:
        return {"error": "PERPLEXITY_API_KEY not configured", "enabled": False}
    try:
        payload: dict[str, Any] = {
            "model": model_name,
            "messages": [{"role": "user", "content": prompt}],
        }
        if search_domain_filter:
            payload["search_domain_filter"] = [str(d).strip() for d in search_domain_filter if str(d).strip()][:20]
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        content = str((data.get("choices") or [{}])[0].get("message", {}).get("content") or "")
        parsed = _parse_json_blob(content)
        return {
            "enabled": True,
            "raw_content": content,
            "parsed": parsed,
            "usage": data.get("usage") or {},
            "model": data.get("model") or model_name,
            "citations": list(data.get("citations") or []),
        }
    except Exception as exc:
        return {"error": str(exc)[:240], "enabled": False}


def search_web(query: str, *, limit: int = 8) -> tuple[list[dict[str, str]], dict[str, Any]]:
    """Generic web search for integrations.search (provider/title/url/snippet rows)."""
    key = _api_key()
    if not key:
        return [], {"provider": "perplexity", "configured": False, "attempted": False, "backend": "perplexity_sonar"}
    q = str(query or "").strip()
    if not q:
        return [], {"provider": "perplexity", "configured": True, "attempted": False, "backend": "perplexity_sonar"}
    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "sonar-pro",
                "messages": [{"role": "user", "content": q}],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        message = (data.get("choices") or [{}])[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        citations = list(data.get("citations") or message.get("citations") or [])
        rows: list[dict[str, str]] = []
        for idx, url in enumerate(citations):
            if len(rows) >= limit:
                break
            url_s = str(url or "").strip()
            if not url_s:
                continue
            rows.append(
                {
                    "provider": "Perplexity",
                    "title": url_s,
                    "url": url_s,
                    "snippet": content[:500] if content and idx == 0 else "",
                }
            )
        if not rows and content:
            rows.append(
                {
                    "provider": "Perplexity",
                    "title": q[:120],
                    "url": "",
                    "snippet": content[:500],
                }
            )
        clipped = rows[:limit]
        return clipped, {
            "provider": "perplexity",
            "configured": True,
            "attempted": True,
            "result_count": len(clipped),
            "backend": "perplexity_sonar",
        }
    except Exception as exc:
        return [], {
            "provider": "perplexity",
            "configured": True,
            "attempted": True,
            "error": str(exc)[:200],
            "backend": "perplexity_sonar",
        }


_LEADS_PROMPT = """You are a B2B lead researcher. Find real companies and public contacts matching this request.

ICP / segment: {icp}
Geography: {geography}
Target count: {limit}

Return STRICT JSON only (no markdown fences, no commentary) with this exact shape:
{{
  "leads": [
    {{
      "company": "",
      "contact_name": "",
      "title": "",
      "email": "",
      "phone": "",
      "website": "",
      "linkedin_url": "",
      "location": "",
      "source_url": "",
      "notes": ""
    }}
  ]
}}

Rules:
- Only include real organizations you can tie to a real source URL.
- Each lead MUST have a non-empty company name plus website OR source_url.
- Leave email and phone blank if not found in public sources — never invent addresses.
- Prefer identifiable decision-makers (founder, CEO, VP Sales, head of ops) when available.
- Return up to {limit} distinct companies.
"""


def search_structured_leads(
    *,
    icp: str,
    geography: str = "",
    limit: int = 20,
) -> dict[str, Any]:
    """Live lead retrieval via Perplexity Sonar — returns parsed JSON + citations."""
    key = _api_key()
    if not key:
        return {"configured": False, "attempted": False, "leads": [], "error": "perplexity_not_configured"}
    icp_s = str(icp or "target companies").strip()
    geo = str(geography or "Global").strip()
    cap = max(5, min(int(limit or 20), 50))
    prompt = _LEADS_PROMPT.format(icp=icp_s, geography=geo, limit=cap)
    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": "sonar-pro", "messages": [{"role": "user", "content": prompt}]},
            timeout=90,
        )
        resp.raise_for_status()
        data = resp.json()
        message = (data.get("choices") or [{}])[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        parsed = _parse_json_blob(content) or {}
        citations = list(data.get("citations") or message.get("citations") or [])
        return {
            "configured": True,
            "attempted": True,
            "parsed": parsed,
            "raw_content": content[:4000],
            "citations": citations,
            "provider": "perplexity",
            "backend": "perplexity_sonar",
        }
    except Exception as exc:
        return {
            "configured": True,
            "attempted": True,
            "parsed": {},
            "leads": [],
            "error": str(exc)[:240],
            "provider": "perplexity",
            "backend": "perplexity_sonar",
        }
