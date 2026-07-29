"""Source-quality tiers for report fact labeling."""

from __future__ import annotations



import re

from typing import Any

from urllib.parse import urlparse



# Government, regulators, official statistics, primary filings.

TIER1_DOMAIN_FRAGMENTS = (

    ".gov.",

    ".gov/",

    ".gov.in",

    "mospi.gov",

    "rbi.org",

    "dpiit.gov",

    "nasscom.in",

    "msme.gov",

    "udyamregistration.gov",

    "sec.gov",

    "europa.eu",

    "worldbank.org",

    "imf.org",

    "oecd.org",

    "who.int",

)



# Named industry databases and reputable research publishers.

TIER2_DOMAIN_FRAGMENTS = (

    "tracxn.com",

    "crunchbase.com",

    "statista.com",

    "gartner.com",

    "forrester.com",

    "ibisworld.com",

    "grandviewresearch.com",

    "marketsandmarkets.com",

    "mckinsey.com",

    "bcg.com",

    "hbr.org",

    "economist.com",

    "reuters.com",

    "bloomberg.com",

    "ft.com",

)



# SEO, courses, glossaries, SaaS marketing/listicle sites — [SECONDARY] at best.

LOW_QUALITY_DOMAIN_FRAGMENTS = (

    "coursera.org",

    "udemy.com",

    "youtube.com",

    "youtu.be",

    "howstuffworks.com",

    "wikipedia.org",

    "investopedia.com",

    "bigideasdb.com",

    "gitnux.org",

    "medium.com",

    "substack.com",

    "wordpress.com",

    "blogspot.",

    "quora.com",

    "reddit.com",

    "pinterest.",

    "slideshare.net",

    "waveup.com",

    "saasfactor.co",

    "saasworthy.com",

    "g2.com",  # reviews useful but vendor-influenced; not [FACT]-grade alone

    "capterra.com",

    "softwareadvice.com",

    "getapp.com",

)



_FACT_TAG_RE = re.compile(r"\[FACT\]", re.I)

_PRIMARY_TAG_RE = re.compile(r"\[PRIMARY\]", re.I)

_ESTIMATE_TAG_RE = re.compile(r"\[ESTIMATE\]", re.I)





def _host(url: str) -> str:

    try:

        return (urlparse(str(url or "").strip()).netloc or "").lower()

    except Exception:

        return ""





def _name_slug(name: str) -> str:

    return re.sub(r"[^a-z0-9]", "", str(name or "").lower())





def is_vendor_self_source(url: str, entity_name: str) -> bool:

    """True when a vendor's own site/blog is cited for that vendor's positioning."""

    slug = _name_slug(entity_name)

    if len(slug) < 4:

        return False

    host = _host(url)

    host_blob = re.sub(r"[^a-z0-9]", "", host)

    path_blob = re.sub(r"[^a-z0-9]", "", str(url or "").lower())

    return slug in host_blob or slug in path_blob





def classify_source_url(url: str) -> str:

    """Return tier1 | tier2 | low | unknown."""

    host = _host(url)

    if not host:

        return "unknown"

    blob = host + str(url or "").lower()

    if any(frag in blob for frag in TIER1_DOMAIN_FRAGMENTS):

        return "tier1"

    if any(frag in blob for frag in LOW_QUALITY_DOMAIN_FRAGMENTS):

        return "low"

    if any(frag in blob for frag in TIER2_DOMAIN_FRAGMENTS):

        return "tier2"

    if "blog" in host or host.startswith("blog."):

        return "low"

    return "unknown"





def best_source_tier(sources: list[str] | None) -> str:

    tiers = [classify_source_url(u) for u in (sources or []) if str(u).strip().startswith("http")]

    if not tiers:

        return "unknown"

    if "tier1" in tiers:

        return "tier1"

    if "tier2" in tiers:

        return "tier2"

    if all(t == "low" for t in tiers):

        return "low"

    if "low" in tiers:

        return "low"

    return "unknown"





def downgrade_unverified_fact_tags(text: str, *, source_tier: str, force_secondary: bool = False) -> str:

    """Downgrade [FACT]/[PRIMARY] when citations are not tier-1/2."""

    if source_tier in ("tier1", "tier2") and not force_secondary:

        return text

    target = "[SECONDARY]" if source_tier == "low" or force_secondary else "[ESTIMATE]"

    out = _FACT_TAG_RE.sub(target, text)

    out = _PRIMARY_TAG_RE.sub("[SECONDARY]", out)

    if source_tier == "low" or force_secondary:

        out = _ESTIMATE_TAG_RE.sub("[SECONDARY]", out)

    return out





def apply_source_tier_labels(sections: list[dict[str, Any]]) -> list[dict[str, Any]]:

    """Relabel [FACT] on sections backed only by low-quality or self-sourced URLs."""

    out: list[dict[str, Any]] = []

    for sec in sections:

        if not isinstance(sec, dict):

            continue

        row = dict(sec)

        sources = [str(u) for u in (row.get("sources") or []) if str(u).strip()]

        tier = best_source_tier(sources)

        row["source_tier"] = tier

        body = str(row.get("body_markdown") or "")

        if tier not in ("tier1", "tier2"):

            row["body_markdown"] = downgrade_unverified_fact_tags(body, source_tier=tier)

        km = dict(row.get("key_metrics") or {}) if isinstance(row.get("key_metrics"), dict) else {}

        new_km: dict[str, Any] = {}

        for key, val in km.items():

            val_s = str(val or "")

            metric_tier = tier

            force_secondary = any(is_vendor_self_source(u, str(key)) for u in sources)

            if not force_secondary:

                for u in sources:

                    if is_vendor_self_source(u, str(key)):

                        force_secondary = True

                        break

            if force_secondary:

                metric_tier = "low"

            new_km[key] = downgrade_unverified_fact_tags(

                val_s,

                source_tier=metric_tier,

                force_secondary=force_secondary,

            )

        row["key_metrics"] = new_km

        out.append(row)

    return out





def filter_harvest_urls(citations: list[str]) -> tuple[list[str], list[str]]:

    """Split citations into preferred vs low-quality for harvest prompts."""

    preferred: list[str] = []

    demoted: list[str] = []

    for url in citations:

        u = str(url).strip()

        if not u.startswith("http"):

            continue

        if classify_source_url(u) == "low":

            demoted.append(u)

        else:

            preferred.append(u)

    return preferred, demoted





def institutional_source_queries(geography: str) -> list[str]:

    """Targeted search queries for tier-1/2 India/global institutional sources."""

    geo = str(geography or "").strip()

    india = "india" in geo.lower()

    if india:

        return [

            "site:msme.gov.in MSME statistics registered enterprises",

            "site:nasscom.in startup ecosystem report",

            "site:mospi.gov.in economic census MSME",

            "site:dpiit.gov.in startup india recognized startups",

            "site:tracxn.com market map",

            "site:crunchbase.com companies funding",

        ]

    return [

        "site:sec.gov 10-K market size",

        "site:worldbank.org industry statistics",

        "site:tracxn.com market",

        "site:crunchbase.com funding",

    ]

