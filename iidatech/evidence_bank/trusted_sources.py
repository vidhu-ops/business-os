"""Trusted-source harvester: IIDATECH's own evidence bank.

Retrieves data ONLY from a registry of verified publishers (analyst firms with
published methodology, government/statistical offices, and review platforms)
and extracts metrics deterministically with regex - no LLM involved. Rows from
here are Tier 1 in the market evidence bank.

Retrieval providers:
- Direct official APIs (World Bank, FRED, BLS, EIA, Census, data.gov.in, Comtrade)
- Perplexity Sonar with search_domain_filter (domain-restricted publisher search)
"""
from __future__ import annotations

import os
import re
from typing import Any

# ---------------------------------------------------------------------------
# Registry of free, verifiable sources. Each entry: domains + what the source
# is trusted FOR. A row is only admissible for its category.
#
# source_tier follows the IIDATECH tiering:
#   1 = Primary/Official (government statistical agencies, central banks,
#       SEC/Companies House, WHO/FAO/ILO/IMF/World Bank)
#   2 = Institutional/Aggregated (OECD, Our World in Data, analyst firms and
#       review platforms with published methodology)
#   3 = Directional/Supplementary (Crunchbase free tier, trade press) - used
#       for triangulation only, never to override or verify a claim.
#
# "core" categories run for every report. "industries"/"geographies" packs run
# only when the report matches, keeping API calls bounded.
# ---------------------------------------------------------------------------
TRUSTED_SOURCE_REGISTRY: dict[str, dict[str, Any]] = {
    # ---- Core: every report ------------------------------------------------
    "market_sizing_analyst": {
        "label": "Analyst market sizing (methodology published; free previews/press releases)",
        "source_tier": 2,
        "core": True,
        "domains": [
            "statista.com",
            "grandviewresearch.com",
            "fortunebusinessinsights.com",
            "mordorintelligence.com",
            "marketsandmarkets.com",
            "precedenceresearch.com",
        ],
        "trust_note": "Cited in real pitch decks; publish methodology notes.",
        "query": "{topic} market size forecast CAGR {geography}",
    },
    "competitor_reviews": {
        "label": "Verified user-review platforms (review volume, ratings, segment grids)",
        "source_tier": 2,
        "core": True,
        "domains": [
            "g2.com",
            "capterra.com",
            "trustradius.com",
            "softwareadvice.com",
            "gartner.com",
        ],
        "trust_note": "Real user review counts, feature grids, SMB vs enterprise segmentation.",
        "query": "{topic} software reviews ratings comparison {geography}",
    },
    "government_statistics": {
        "label": "Multilateral / official statistics (fully free, fully verified)",
        "source_tier": 1,
        "core": True,
        "domains": [
            "worldbank.org",
            "imf.org",
            "un.org",
            "comtrade.un.org",
            "wto.org",
            "unctad.org",
            "fao.org",
            "ilo.org",
            "who.int",
        ],
        "trust_note": "Primary statistical sources; strongest tier for macro and demand-side data.",
        "query": "{industry} {topic} statistics adoption {geography}",
    },
    "institutional_aggregators": {
        "label": "Institutional aggregators with transparent methodology",
        "source_tier": 2,
        "core": True,
        "domains": [
            "oecd.org",
            "ourworldindata.org",
            "weforum.org",
        ],
        "trust_note": "Cleaned, sourced datasets with full methodology transparency.",
        "query": "{industry} {topic} data trends {geography}",
    },
    "filings_registries": {
        "label": "Regulatory filings and company registries (free, primary)",
        "source_tier": 1,
        "core": True,
        "domains": [
            "sec.gov",
            "company-information.service.gov.uk",
            "opencorporates.com",
            "gleif.org",
            "sedarplus.ca",
            "mca.gov.in",
        ],
        "trust_note": "Primary financial disclosures and verified corporate identity.",
        "query": "{topic} public company filings revenue {geography}",
    },
    "startup_funding_directional": {
        "label": "Directional startup/funding signals (triangulation only)",
        "source_tier": 3,
        "core": True,
        "domains": [
            "crunchbase.com",
        ],
        "trust_note": "Free tier is directional; never standalone proof of a claim.",
        "query": "{topic} startups funding rounds {geography}",
    },
    # ---- Industry packs ----------------------------------------------------
    "industry_technology": {
        "label": "Technology / software industry statistics",
        "source_tier": 2,
        "industries": ["software", "saas", "tech", "ai", "it ", "cloud", "developer", "app", "crm", "automation"],
        "domains": ["survey.stackoverflow.co", "github.blog", "w3techs.com"],
        "trust_note": "Developer surveys and web technology usage statistics.",
        "query": "{topic} technology adoption usage statistics {geography}",
    },
    "industry_healthcare": {
        "label": "Healthcare / life sciences official data",
        "source_tier": 1,
        "industries": ["health", "medical", "pharma", "dental", "clinic", "hospital", "biotech", "wellness"],
        "domains": ["who.int", "cdc.gov", "clinicaltrials.gov"],
        "trust_note": "WHO GHO, CDC, and clinical trial registries.",
        "query": "{topic} health statistics prevalence {geography}",
    },
    "industry_energy": {
        "label": "Energy official statistics",
        "source_tier": 1,
        "industries": ["energy", "solar", "power", "renewable", "oil", "gas", "electric", "battery", "ev "],
        "domains": ["eia.gov", "iea.org", "irena.org"],
        "trust_note": "EIA fully free with API; IEA/IRENA partially free.",
        "query": "{topic} energy statistics capacity {geography}",
    },
    "industry_agriculture": {
        "label": "Agriculture / food official statistics",
        "source_tier": 1,
        "industries": ["agri", "farm", "food", "crop", "dairy", "grocery"],
        "domains": ["fao.org", "usda.gov"],
        "trust_note": "FAOSTAT global; USDA NASS for US.",
        "query": "{topic} agriculture production statistics {geography}",
    },
    "industry_manufacturing": {
        "label": "Manufacturing / industrial statistics",
        "source_tier": 1,
        "industries": ["manufactur", "industrial", "factory", "machin", "hardware", "automotive", "car "],
        "domains": ["unido.org", "census.gov"],
        "trust_note": "UNIDO and Annual Survey of Manufactures.",
        "query": "{topic} manufacturing output statistics {geography}",
    },
    "industry_retail": {
        "label": "Retail / e-commerce official statistics",
        "source_tier": 1,
        "industries": ["retail", "ecommerce", "e-commerce", "d2c", "commerce", "consumer", "shop"],
        "domains": ["census.gov", "ec.europa.eu"],
        "trust_note": "US Census retail trade; Eurostat retail indices.",
        "query": "{topic} retail trade e-commerce statistics {geography}",
    },
    "industry_labor": {
        "label": "Labor / employment official statistics",
        "source_tier": 1,
        "industries": ["labor", "labour", "hr ", "staffing", "recruit", "employment", "workforce", "gig"],
        "domains": ["ilo.org", "bls.gov", "ec.europa.eu"],
        "trust_note": "ILOSTAT, BLS, Eurostat labour market data.",
        "query": "{topic} employment wages statistics {geography}",
    },
    "industry_real_estate": {
        "label": "Real estate / housing official statistics",
        "source_tier": 1,
        "industries": ["real estate", "property", "housing", "proptech", "rental", "construction"],
        "domains": ["fred.stlouisfed.org", "ec.europa.eu"],
        "trust_note": "FRED housing indices; Eurostat housing prices.",
        "query": "{topic} housing property price statistics {geography}",
    },
    "industry_environment": {
        "label": "Environment / climate official data",
        "source_tier": 1,
        "industries": ["climate", "environment", "carbon", "sustainab", "eco-friendly", "recycl", "waste"],
        "domains": ["nasa.gov", "noaa.gov", "copernicus.eu", "globalcarbonatlas.org"],
        "trust_note": "NASA Earthdata, NOAA, Copernicus, Global Carbon Atlas.",
        "query": "{topic} environmental climate statistics {geography}",
    },
    "industry_patents": {
        "label": "Patents, R&D and innovation statistics",
        "source_tier": 1,
        "industries": ["patent", "r&d", "innovation", "deeptech", "biotech", "semiconductor"],
        "domains": ["wipo.int", "uspto.gov", "patents.google.com"],
        "trust_note": "WIPO IP statistics, USPTO, Google Patents.",
        "query": "{topic} patent filings innovation statistics {geography}",
    },
    # ---- Country statistical agency packs ---------------------------------
    "stats_india": {
        "label": "India national statistics",
        "source_tier": 1,
        "geographies": ["india", "indian"],
        "domains": ["mospi.gov.in", "data.gov.in", "rbi.org.in", "ibef.org"],
        "trust_note": "MOSPI, data.gov.in, RBI, IBEF.",
        "query": "{industry} {topic} statistics India",
    },
    "stats_us": {
        "label": "US national statistics",
        "source_tier": 1,
        "geographies": ["united states", "usa", "us ", "america"],
        "domains": ["census.gov", "bls.gov", "data.gov", "fred.stlouisfed.org"],
        "trust_note": "Census, BLS, data.gov, FRED.",
        "query": "{industry} {topic} statistics United States",
    },
    "stats_uk": {
        "label": "UK national statistics",
        "source_tier": 1,
        "geographies": ["united kingdom", "uk", "britain", "england"],
        "domains": ["ons.gov.uk"],
        "trust_note": "Office for National Statistics.",
        "query": "{industry} {topic} statistics United Kingdom",
    },
    "stats_eu": {
        "label": "EU statistics (Eurostat)",
        "source_tier": 1,
        "geographies": ["europe", "eu ", "european", "germany", "france", "spain", "italy", "netherlands"],
        "domains": ["ec.europa.eu"],
        "trust_note": "Eurostat.",
        "query": "{industry} {topic} statistics Europe",
    },
    "stats_china": {
        "label": "China national statistics",
        "source_tier": 1,
        "geographies": ["china", "chinese"],
        "domains": ["stats.gov.cn"],
        "trust_note": "National Bureau of Statistics of China.",
        "query": "{industry} {topic} statistics China",
    },
    "stats_japan": {
        "label": "Japan national statistics",
        "source_tier": 1,
        "geographies": ["japan", "japanese"],
        "domains": ["stat.go.jp"],
        "trust_note": "Statistics Bureau of Japan.",
        "query": "{industry} {topic} statistics Japan",
    },
    "stats_canada": {
        "label": "Canada national statistics",
        "source_tier": 1,
        "geographies": ["canada", "canadian"],
        "domains": ["statcan.gc.ca"],
        "trust_note": "Statistics Canada.",
        "query": "{industry} {topic} statistics Canada",
    },
    "stats_australia": {
        "label": "Australia national statistics",
        "source_tier": 1,
        "geographies": ["australia", "australian"],
        "domains": ["abs.gov.au"],
        "trust_note": "Australian Bureau of Statistics.",
        "query": "{industry} {topic} statistics Australia",
    },
    "stats_brazil": {
        "label": "Brazil national statistics",
        "source_tier": 1,
        "geographies": ["brazil", "brazilian"],
        "domains": ["ibge.gov.br"],
        "trust_note": "IBGE.",
        "query": "{industry} {topic} statistics Brazil",
    },
    "stats_south_africa": {
        "label": "South Africa national statistics",
        "source_tier": 1,
        "geographies": ["south africa"],
        "domains": ["statssa.gov.za"],
        "trust_note": "Stats SA.",
        "query": "{industry} {topic} statistics South Africa",
    },
}


def select_categories(topic: str, industry: str, geography: str, *, max_categories: int = 9) -> list[str]:
    """Core categories always run; industry and country packs run only on match
    so API-call count stays bounded per report."""
    blob = f" {topic} {industry} ".lower()
    geo = f" {str(geography or '').lower()} "
    selected = [k for k, v in TRUSTED_SOURCE_REGISTRY.items() if v.get("core")]
    for key, spec in TRUSTED_SOURCE_REGISTRY.items():
        if spec.get("core"):
            continue
        needles = spec.get("industries") or []
        if needles and any(n in blob for n in needles):
            selected.append(key)
            continue
        geo_needles = spec.get("geographies") or []
        if geo_needles and any(g in geo for g in geo_needles):
            selected.append(key)
    return selected[:max_categories]

_TIMEOUT = 25

# ---------------------------------------------------------------------------
# Deterministic metric extraction (regex only, per LLM-usage policy)
# ---------------------------------------------------------------------------
_MONEY_RE = re.compile(
    r"(?:USD|US\$|EUR|GBP|INR|Rs\.?|[$\u20b9\u20ac\u00a3])\s?([\d.,]+)\s?(trillion|billion|million|bn|mn|crore|lakh)",
    re.IGNORECASE,
)
_CAGR_RE = re.compile(r"CAGR\s*(?:of\s*)?([\d.]+)\s?%|grow(?:ing|th)?\s(?:at|of)\s(?:a\s)?(?:CAGR\s(?:of\s)?)?([\d.]+)\s?%", re.IGNORECASE)
_RATING_RE = re.compile(r"([0-5]\.\d)\s*(?:/|out of)\s*5", re.IGNORECASE)
_REVIEWS_RE = re.compile(r"([\d,]{2,})\s+(?:user\s+)?reviews", re.IGNORECASE)
_YEAR_RE = re.compile(r"\b(20[12]\d|203[0-5])\b")


def extract_metrics_from_text(text: str) -> list[dict[str, str]]:
    """Pull market-size, CAGR, rating, and review-count figures with context."""
    text = str(text or "")
    metrics: list[dict[str, str]] = []

    def _context(start: int, end: int) -> str:
        return re.sub(r"\s+", " ", text[max(0, start - 80): end + 80]).strip()

    for m in _MONEY_RE.finditer(text):
        metrics.append({
            "metric": "market_value",
            "value": f"{m.group(0)}",
            "context": _context(m.start(), m.end()),
        })
    for m in _CAGR_RE.finditer(text):
        pct = m.group(1) or m.group(2)
        if pct:
            metrics.append({"metric": "cagr", "value": f"{pct}%", "context": _context(m.start(), m.end())})
    for m in _RATING_RE.finditer(text):
        metrics.append({"metric": "user_rating", "value": f"{m.group(1)}/5", "context": _context(m.start(), m.end())})
    for m in _REVIEWS_RE.finditer(text):
        metrics.append({"metric": "review_count", "value": m.group(1), "context": _context(m.start(), m.end())})

    years = _YEAR_RE.findall(text)
    if years:
        for row in metrics:
            row.setdefault("years_mentioned", ",".join(sorted(set(years))[:4]))
    return metrics[:10]


def _topic_tokens(topic: str, industry: str) -> list[str]:
    stop = {"the", "and", "for", "with", "market", "industry", "business", "solutions", "services"}
    tokens = re.findall(r"[a-zA-Z]{4,}", f"{topic} {industry}".lower())
    return [t for t in tokens if t not in stop][:10]


def _is_relevant(title: str, snippet: str, tokens: list[str]) -> bool:
    """Relevance gate: the page must actually be ABOUT the topic, not just from
    a trusted domain (shape alone is never enough)."""
    if not tokens:
        return True
    blob = f"{title} {snippet}".lower()
    return any(t in blob for t in tokens)


def _domain_of(url: str) -> str:
    m = re.match(r"https?://(?:www\.)?([^/]+)", str(url or "").lower())
    return m.group(1) if m else ""


def _url_in_registry(url: str, domains: list[str]) -> bool:
    host = _domain_of(url)
    return any(host == d or host.endswith("." + d) for d in domains)


def _secret(*names: str) -> str:
    try:
        from on_demand_research import local_secret_value

        val = local_secret_value(*names)
        if val:
            return str(val)
    except Exception:
        pass
    for name in names:
        val = str(os.getenv(name) or "").strip()
        if val:
            return val
    return ""


# ---------------------------------------------------------------------------
# Providers (domain-restricted via Perplexity Sonar only)
# ---------------------------------------------------------------------------

def _perplexity_domain_search(query: str, domains: list[str], limit: int) -> tuple[list[dict], dict]:
    """Fallback: Sonar restricted with search_domain_filter; citations become rows."""
    key = _secret("PERPLEXITY_API_KEY", "PERPLEXITY_KEY")
    if not key:
        return [], {"provider": "perplexity_domain", "configured": False}
    import requests

    try:
        resp = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "sonar-pro",
                "messages": [{
                    "role": "user",
                    "content": (
                        f"{query}. Quote exact figures with units and years from the sources. "
                        "Only state what the sources literally say."
                    ),
                }],
                "search_domain_filter": domains[:10],
            },
            timeout=60,
        )
        resp.raise_for_status()
        data = resp.json()
        content = str((data.get("choices") or [{}])[0].get("message", {}).get("content") or "")
        citations = list(data.get("citations") or [])
        # Integrity rule: the answer text is an AGGREGATE across all citations.
        # Attaching it (and metrics parsed from it) to every URL would stamp
        # identical figures onto unrelated sources. Only the first citation
        # carries the aggregate snippet; the rest enter as bare references.
        rows = []
        for idx, url in enumerate(citations[:limit]):
            url_s = str(url or "").strip()
            if url_s:
                rows.append({
                    "title": url_s[:220],
                    "url": url_s,
                    "snippet": content[:1200] if idx == 0 else "",
                    "retrieval_provider": "perplexity_domain_filter",
                })
        return rows, {"provider": "perplexity_domain", "configured": True, "returned": len(rows)}
    except Exception as exc:
        return [], {"provider": "perplexity_domain", "configured": True, "error": str(exc)[:160]}


# ---------------------------------------------------------------------------
# World Bank Open Data direct API (keyless, fully free, Tier 1 primary)
# ---------------------------------------------------------------------------
_WB_COUNTRY_CODES: dict[str, str] = {
    "india": "IND", "united states": "USA", "usa": "USA", "america": "USA",
    "united kingdom": "GBR", "uk": "GBR", "britain": "GBR",
    "china": "CHN", "japan": "JPN", "canada": "CAN", "australia": "AUS",
    "brazil": "BRA", "south africa": "ZAF", "germany": "DEU", "france": "FRA",
    "global": "WLD", "world": "WLD", "europe": "EMU",
}
_WB_INDICATORS: dict[str, str] = {
    "SP.POP.TOTL": "population_total",
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
    "IT.NET.USER.ZS": "internet_users_pct",
}


def _wb_country_code(geography: str) -> str:
    geo = str(geography or "").strip().lower()
    for needle, code in _WB_COUNTRY_CODES.items():
        if needle in geo:
            return code
    return "WLD"


def fetch_worldbank_indicators(geography: str) -> tuple[list[dict[str, Any]], dict]:
    """Structured macro rows straight from the World Bank API (no key, no LLM)."""
    import requests

    code = _wb_country_code(geography)
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for indicator, metric_name in _WB_INDICATORS.items():
        try:
            resp = requests.get(
                f"https://api.worldbank.org/v2/country/{code}/indicator/{indicator}",
                params={"format": "json", "per_page": 5, "mrnev": 1},
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            payload = resp.json()
            entries = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
            for entry in entries or []:
                value = entry.get("value")
                if value is None:
                    continue
                rows.append({
                    "name": f"World Bank {metric_name} ({entry.get('country', {}).get('value', code)}, {entry.get('date')})",
                    "record_type": "official_statistics_api",
                    "publisher": "worldbank.org",
                    "url": f"https://data.worldbank.org/indicator/{indicator}?locations={code}",
                    "snippet": "",
                    "extracted_metrics": [{
                        "metric": metric_name,
                        "value": str(value),
                        "context": f"World Bank indicator {indicator}, year {entry.get('date')}",
                        "years_mentioned": str(entry.get("date") or ""),
                    }],
                    "retrieval_provider": "worldbank_api",
                    "verification_status": "official_statistics",
                    "source_tier": 1,
                    "trust_note": "World Bank Open Data API; primary official source.",
                })
                break
        except Exception as exc:
            errors.append(f"{indicator}: {str(exc)[:120]}")
    diag = {"provider": "worldbank_api", "configured": True, "country_code": code, "returned": len(rows)}
    if errors:
        diag["errors"] = errors
    return rows, diag


def _api_evidence_row(
    *,
    name: str,
    metric_name: str,
    metric_value: str,
    context: str,
    url: str,
    publisher: str,
    provider: str,
    year: str = "",
) -> dict[str, Any]:
    metrics = [{
        "metric": metric_name,
        "value": metric_value,
        "context": context[:220],
    }]
    if year:
        metrics[0]["years_mentioned"] = year
    return {
        "name": name[:160],
        "record_type": "official_statistics_api",
        "publisher": publisher,
        "url": url,
        "snippet": "",
        "extracted_metrics": metrics,
        "retrieval_provider": provider,
        "verification_status": "official_statistics",
        "source_tier": 1,
        "trust_note": f"Direct API ({provider}); primary official source.",
    }


_COMTRADE_REPORTER_NUMERIC: dict[str, int] = {
    "IND": 356, "USA": 842, "GBR": 826, "CHN": 156, "DEU": 276, "FRA": 251,
    "JPN": 392, "CAN": 124, "AUS": 36, "BRA": 76, "ZAF": 710, "WLD": 0,
}


def fetch_fred_indicators(geography: str) -> tuple[list[dict[str, Any]], dict]:
    """FRED macro series (US-focused; key from fred.stlouisfed.org/docs/api/api_key.html)."""
    key = _secret("FRED_API_KEY", "FRED_KEY")
    if not key:
        return [], {"provider": "fred_api", "configured": False}
    geo = str(geography or "").lower()
    if not any(g in geo for g in ("united states", "usa", "us ", "america", "global", "world")):
        return [], {"provider": "fred_api", "configured": True, "skipped": "non_us_geography"}
    import requests

    series = {
        "UNRATE": ("unemployment_rate_pct", "Unemployment rate"),
        "CPIAUCSL": ("cpi_all_urban_index", "CPI all urban consumers"),
        "FEDFUNDS": ("fed_funds_rate_pct", "Federal funds effective rate"),
        "CSUSHPINSA": ("case_shiller_housing_index", "Case-Shiller US home price index"),
    }
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for series_id, (metric_name, label) in series.items():
        try:
            resp = requests.get(
                "https://api.stlouisfed.org/fred/series/observations",
                params={
                    "series_id": series_id,
                    "api_key": key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 1,
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            obs = (resp.json().get("observations") or [{}])[0]
            value = str(obs.get("value") or "").strip()
            if not value or value == ".":
                continue
            year = str(obs.get("date") or "")[:4]
            rows.append(_api_evidence_row(
                name=f"FRED {label} ({obs.get('date', '')})",
                metric_name=metric_name,
                metric_value=value,
                context=f"FRED series {series_id} observation {obs.get('date')}",
                url=f"https://fred.stlouisfed.org/series/{series_id}",
                publisher="fred.stlouisfed.org",
                provider="fred_api",
                year=year,
            ))
        except Exception as exc:
            errors.append(f"{series_id}: {str(exc)[:120]}")
    diag = {"provider": "fred_api", "configured": True, "returned": len(rows)}
    if errors:
        diag["errors"] = errors
    return rows, diag


def fetch_bls_indicators(geography: str) -> tuple[list[dict[str, Any]], dict]:
    """BLS labor/inflation series (key lifts rate limits: data.bls.gov/registrationEngine/)."""
    key = _secret("BLS_API_KEY", "BLS_KEY")
    import requests

    geo = str(geography or "").lower()
    if not any(g in geo for g in ("united states", "usa", "us ", "america", "global", "world")):
        return [], {"provider": "bls_api", "configured": bool(key), "skipped": "non_us_geography"}
    series = {
        "LNS14000000": ("unemployment_rate_pct", "Unemployment rate"),
        "CUUR0000SA0": ("cpi_all_urban_index", "CPI all urban consumers"),
        "CES0500000003": ("avg_hourly_earnings_usd", "Average hourly earnings, total private"),
    }
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    payload: dict[str, Any] = {"seriesid": list(series.keys()), "startyear": "2023", "endyear": "2026"}
    if key:
        payload["registrationkey"] = key
    try:
        resp = requests.post(
            "https://api.bls.gov/publicAPI/v2/timeseries/data/",
            json=payload,
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        for block in (resp.json().get("Results", {}) or {}).get("series", []):
            sid = str(block.get("seriesID") or "")
            meta = series.get(sid)
            if not meta:
                continue
            metric_name, label = meta
            point = next((p for p in (block.get("data") or []) if p.get("value") not in (None, "")), None)
            if not point:
                continue
            year = str(point.get("year") or "")
            period = str(point.get("periodName") or point.get("period") or "")
            value = str(point.get("value") or "")
            rows.append(_api_evidence_row(
                name=f"BLS {label} ({period} {year})",
                metric_name=metric_name,
                metric_value=value,
                context=f"BLS series {sid} {period} {year}",
                url=f"https://api.bls.gov/publicAPI/v2/timeseries/data/{sid}",
                publisher="bls.gov",
                provider="bls_api",
                year=year,
            ))
    except Exception as exc:
        errors.append(str(exc)[:160])
    diag = {"provider": "bls_api", "configured": True, "returned": len(rows)}
    if errors:
        diag["errors"] = errors
    return rows, diag


def fetch_eia_indicators(industry: str, geography: str) -> tuple[list[dict[str, Any]], dict]:
    """EIA energy statistics (key: eia.gov/opendata/register.php)."""
    key = _secret("EIA_API_KEY", "EIA_KEY")
    if not key:
        return [], {"provider": "eia_api", "configured": False}
    blob = f" {industry} {geography} ".lower()
    if not any(t in blob for t in ("energy", "solar", "power", "renewable", "oil", "gas", "electric", "battery", "united states", "usa", "global")):
        return [], {"provider": "eia_api", "configured": True, "skipped": "non_energy_topic"}
    import requests

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        resp = requests.get(
            "https://api.eia.gov/v2/electricity/electric-power-operational-data/data/",
            params={
                "api_key": key,
                "frequency": "annual",
                "data[0]": "generation",
                "length": 1,
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        data = (resp.json().get("response") or {}).get("data") or []
        if data:
            row = data[0]
            value = str(row.get("generation") or "")
            period = str(row.get("period") or "")
            if value:
                rows.append(_api_evidence_row(
                    name=f"EIA US electricity generation ({period})",
                    metric_name="electricity_generation",
                    metric_value=value,
                    context=f"EIA electricity operational data period {period}",
                    url="https://www.eia.gov/opendata/",
                    publisher="eia.gov",
                    provider="eia_api",
                    year=period[:4],
                ))
    except Exception as exc:
        errors.append(str(exc)[:160])
    diag = {"provider": "eia_api", "configured": True, "returned": len(rows)}
    if errors:
        diag["errors"] = errors
    return rows, diag


def fetch_census_indicators(geography: str) -> tuple[list[dict[str, Any]], dict]:
    """US Census retail trade (key: api.census.gov/data/key_signup.html)."""
    key = _secret("CENSUS_API_KEY", "CENSUS_KEY")
    if not key:
        return [], {"provider": "census_api", "configured": False}
    geo = str(geography or "").lower()
    if not any(g in geo for g in ("united states", "usa", "us ", "america", "global", "world")):
        return [], {"provider": "census_api", "configured": True, "skipped": "non_us_geography"}
    import requests

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    try:
        resp = requests.get(
            "https://api.census.gov/data/timeseries/eits/marts",
            params={
                "get": "cell_value,time,data_type_code",
                "category_code": "44X72",
                "data_type_code": "SM",
                "time": "2024",
                "key": key,
            },
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        payload = resp.json()
        if isinstance(payload, list) and len(payload) > 1:
            header = payload[0]
            for rec in payload[1:2]:
                row_map = dict(zip(header, rec))
                value = str(row_map.get("cell_value") or "")
                period = str(row_map.get("time") or "")
                if value:
                    rows.append(_api_evidence_row(
                        name=f"US Census retail sales estimate ({period})",
                        metric_name="retail_sales_millions_usd",
                        metric_value=value,
                        context=f"Census MARTS category 44X72 SM {period}",
                        url="https://api.census.gov/data/timeseries/eits/marts.html",
                        publisher="census.gov",
                        provider="census_api",
                        year=period[:4],
                    ))
    except Exception as exc:
        errors.append(str(exc)[:160])
    diag = {"provider": "census_api", "configured": True, "returned": len(rows)}
    if errors:
        diag["errors"] = errors
    return rows, diag


def fetch_comtrade_indicators(geography: str) -> tuple[list[dict[str, Any]], dict]:
    """UN Comtrade merchandise trade (key: comtradedeveloper.un.org, product comtrade-v1).

    Python equivalent of ropensci/comtradr — uses COMTRADE_PRIMARY env var per
    https://github.com/ropensci/comtradr and https://uncomtrade.org/docs/api-subscription-keys/
    """
    key = _secret("COMTRADE_PRIMARY", "COMTRADE_API_KEY", "COMTRADE_SUBSCRIPTION_KEY", "COMTRADE_KEY")
    if not key:
        return [], {"provider": "comtrade_api", "configured": False}
    iso3 = _wb_country_code(geography)
    reporter = _COMTRADE_REPORTER_NUMERIC.get(iso3)
    if reporter is None or reporter == 0:
        return [], {"provider": "comtrade_api", "configured": True, "skipped": "no_country_reporter"}
    import requests

    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for flow_code, flow_label in (("X", "exports"), ("M", "imports")):
        try:
            resp = requests.get(
                "https://comtradeapi.un.org/data/v1/get/C/A/HS",
                headers={"Ocp-Apim-Subscription-Key": key},
                params={
                    "reporterCode": reporter,
                    "partnerCode": 0,
                    "flowCode": flow_code,
                    "period": "2023",
                    "cmdCode": "TOTAL",
                    "maxRecords": 1,
                },
                timeout=_TIMEOUT,
            )
            resp.raise_for_status()
            payload = resp.json()
            dataset = payload.get("data") or payload.get("dataset") or []
            if isinstance(dataset, dict):
                dataset = dataset.get("value") or []
            if not dataset:
                continue
            row = dataset[0] if isinstance(dataset[0], dict) else {}
            value = row.get("primaryValue") or row.get("TradeValue") or row.get("tradeValue")
            if value is None:
                continue
            year = str(row.get("period") or row.get("refYear") or "2023")
            rows.append(_api_evidence_row(
                name=f"UN Comtrade {flow_label} ({iso3}, {year})",
                metric_name=f"merchandise_{flow_label}_usd",
                metric_value=str(value),
                context=f"UN Comtrade reporter {reporter} partner World flow {flow_code}",
                url="https://comtradeplus.un.org/",
                publisher="comtrade.un.org",
                provider="comtrade_api",
                year=year,
            ))
        except Exception as exc:
            errors.append(f"{flow_code}: {str(exc)[:120]}")
    diag = {"provider": "comtrade_api", "configured": True, "reporter": reporter, "returned": len(rows)}
    if errors:
        diag["errors"] = errors
    return rows, diag


def fetch_datagov_in_indicators(geography: str) -> tuple[list[dict[str, Any]], dict]:
    """data.gov.in open datasets (key: data.gov.in, optional DATA_GOV_IN_RESOURCE_ID)."""
    key = _secret("DATA_GOV_IN_API_KEY", "DATA_GOV_IN_KEY")
    resource_id = _secret("DATA_GOV_IN_RESOURCE_ID")
    if not key:
        return [], {"provider": "datagov_in_api", "configured": False}
    geo = str(geography or "").lower()
    if "india" not in geo and "indian" not in geo:
        return [], {"provider": "datagov_in_api", "configured": True, "skipped": "non_india_geography"}
    if not resource_id:
        return [], {"provider": "datagov_in_api", "configured": True, "skipped": "no_resource_id"}
    import requests

    rows: list[dict[str, Any]] = []
    try:
        resp = requests.get(
            f"https://api.data.gov.in/resource/{resource_id}",
            params={"api-key": key, "format": "json", "limit": 1},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        records = (resp.json().get("records") or [])[:1]
        for rec in records:
            if not isinstance(rec, dict):
                continue
            snippet = "; ".join(f"{k}={v}" for k, v in list(rec.items())[:4])
            rows.append(_api_evidence_row(
                name=f"data.gov.in {resource_id[:40]}",
                metric_name="dataset_record",
                metric_value=snippet[:180],
                context=f"data.gov.in resource {resource_id}",
                url=f"https://data.gov.in/resource/{resource_id}",
                publisher="data.gov.in",
                provider="datagov_in_api",
            ))
    except Exception as exc:
        return [], {"provider": "datagov_in_api", "configured": True, "error": str(exc)[:160]}
    return rows, {"provider": "datagov_in_api", "configured": True, "returned": len(rows)}


def fetch_official_api_bundle(
    topic: str,
    industry: str,
    geography: str,
) -> tuple[list[dict[str, Any]], list[dict]]:
    """Run all direct official API fetchers (deterministic, no LLM)."""
    rows: list[dict[str, Any]] = []
    diags: list[dict] = []
    fetchers: list[tuple[str, Any]] = [
        ("fred", lambda: fetch_fred_indicators(geography)),
        ("bls", lambda: fetch_bls_indicators(geography)),
        ("eia", lambda: fetch_eia_indicators(industry, geography)),
        ("census", lambda: fetch_census_indicators(geography)),
        ("comtrade", lambda: fetch_comtrade_indicators(geography)),
        ("datagov_in", lambda: fetch_datagov_in_indicators(geography)),
    ]
    for name, fetcher in fetchers:
        try:
            batch, diag = fetcher()
            rows.extend(batch)
            diags.append(diag)
        except Exception as exc:
            diags.append({"provider": name, "error": str(exc)[:160]})
    return rows, diags


# ---------------------------------------------------------------------------
# Harvest
# ---------------------------------------------------------------------------

def harvest_trusted_sources(
    topic: str,
    industry: str,
    geography: str,
    *,
    max_rows_per_category: int = 4,
) -> dict[str, Any]:
    """Build IIDATECH's own tiered evidence rows from the trusted registry."""
    tokens = _topic_tokens(topic, industry)
    rows: list[dict[str, Any]] = []
    diags: list[dict] = []
    seen_urls: set[str] = set()
    categories = select_categories(topic, industry, geography)

    try:
        from iidatech.evidence_bank.source_policy import is_blocked_source_url
    except ImportError:
        def is_blocked_source_url(_u: str) -> bool:  # type: ignore[misc]
            return False

    # Structured official data first (direct APIs, no search involved).
    wb_rows, wb_diag = fetch_worldbank_indicators(geography)
    rows.extend(wb_rows)
    diags.append(wb_diag)
    api_rows, api_diags = fetch_official_api_bundle(topic, industry, geography)
    rows.extend(api_rows)
    diags.extend(api_diags)

    for category in categories:
        spec = TRUSTED_SOURCE_REGISTRY[category]
        domains = list(spec["domains"])
        source_tier = int(spec.get("source_tier") or 2)
        query = str(spec["query"]).format(topic=topic, industry=industry, geography=geography).strip()

        found: list[dict] = []
        results, diag = _perplexity_domain_search(query, domains, max_rows_per_category * 2)
        diag["category"] = category
        diags.append(diag)
        found.extend(results)

        kept = 0
        for r in found:
            url = str(r.get("url") or "").strip()
            if not url or url in seen_urls:
                continue
            if is_blocked_source_url(url):
                continue
            # Hard gate 1: URL must actually be on a registry domain.
            if not _url_in_registry(url, domains):
                continue
            # Hard gate 2: content must be about the topic, not just trusted-shaped.
            if not _is_relevant(r.get("title", ""), r.get("snippet", ""), tokens):
                continue
            metrics = extract_metrics_from_text(f"{r.get('title', '')} {r.get('snippet', '')}")
            seen_urls.add(url)
            rows.append({
                "name": r.get("title", "")[:160],
                "record_type": category,
                "publisher": _domain_of(url),
                "url": url,
                "snippet": str(r.get("snippet") or "")[:800],
                "extracted_metrics": metrics,
                "retrieval_provider": r.get("retrieval_provider", ""),
                "verification_status": "official_statistics" if source_tier == 1 else (
                    "trusted_publisher" if source_tier == 2 else "directional_source"
                ),
                "source_tier": source_tier,
                "trust_note": spec["trust_note"],
            })
            kept += 1
            if kept >= max_rows_per_category:
                break

    categories_hit = sorted({r["record_type"] for r in rows})
    gaps = []
    for category in categories:
        if category not in categories_hit:
            gaps.append(f"No admissible {TRUSTED_SOURCE_REGISTRY[category]['label']} rows retrieved.")

    return {
        "rows": rows,
        "row_count": len(rows),
        "categories_selected": categories,
        "categories_hit": categories_hit,
        "gaps": gaps,
        "registry": {k: v["domains"] for k, v in TRUSTED_SOURCE_REGISTRY.items()},
        "diagnostics": diags,
    }
