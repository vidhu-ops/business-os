"""Block cross-domain competitor poison before narrative synthesis and ledgers."""
from __future__ import annotations

import re
from typing import Any

_AUTOMOTIVE_BRANDS = frozenset({
    "audi", "bmw", "mercedes", "mercedes-benz", "porsche", "lamborghini",
    "cardekho", "carwale", "ferrari", "bentley", "jaguar",
})

_FESTIVE_NOISE = frozenset({
    "ganesh", "diwali", "navratri", "janmashtami", "durga puja", "holi",
})

_PLACEHOLDER_MARKERS = (
    "see official pricing page",
    "verify locally",
    "check g2 reviews",
)

_SUBSTRING_TRAP_NAMES = frozenset({"audi", "bmw", "nykaa", "plum", "mini"})

_ECOMMERCE_LISTING_HOSTS = ("amazon.in", "amazon.com", "flipkart.com", "nykaa.com")


def _word_in_text(word: str, text: str) -> bool:
    return bool(re.search(rf"\b{re.escape(word)}\b", text, flags=re.I))


def extract_competitor_name(record: dict[str, Any]) -> str:
    title = str(record.get("title") or "").strip()
    match = re.match(r"^(.+?)\s+competitor intelligence$", title, flags=re.I)
    if match:
        return match.group(1).strip()
    metric = str(record.get("metric_name") or "")
    match = re.match(r"^Named competitor:\s*(.+)$", metric, flags=re.I)
    if match:
        return match.group(1).strip()
    return str(record.get("company_name") or record.get("publisher") or "").strip()


def is_placeholder_competitor_record(record: dict[str, Any]) -> bool:
    blob = " ".join(
        str(record.get(key) or "")
        for key in ("pricing", "metric_value", "text", "title", "positioning")
    ).lower()
    return any(marker in blob for marker in _PLACEHOLDER_MARKERS)


def _domain_blob(domain: str, topic: str, industry: str) -> str:
    return f"{domain} {topic} {industry}".lower()


def _automotive_domain_active(domain: str, topic: str, industry: str) -> bool:
    blob = _domain_blob(domain, topic, industry)
    return any(
        term in blob
        for term in (
            "automotive", "car retail", "dealership", "garage", "luxury car",
            "vehicle", "car workshop", "auto retail",
        )
    )


def _festive_domain_active(domain: str, topic: str, industry: str) -> bool:
    blob = _domain_blob(domain, topic, industry)
    return any(term in blob for term in ("festive", "ganesh", "diwali", "decoration", "puja", "kit"))


def competitor_name_in_source_text(name: str, record: dict[str, Any]) -> bool:
    blob = " ".join(
        str(record.get(key) or "")
        for key in ("text", "title", "url", "metric_value", "metric_name")
    )
    lowered = name.lower()
    if lowered in _SUBSTRING_TRAP_NAMES:
        return _word_in_text(lowered, blob)
    return lowered in blob.lower()


_AUTOMOTIVE_BLOB_PHRASES = (
    "luxury car",
    "auto retail",
    "car market",
    "car retail",
    "car dealer",
    "navnit motors",
)


def record_has_out_of_domain_automotive_signal(
    record: dict[str, Any],
    *,
    domain: str,
    topic: str,
    industry: str,
) -> bool:
    """Reject automotive poison in non-automotive diligence tables."""
    if _automotive_domain_active(domain, topic, industry):
        return False
    blob = " ".join(
        str(record.get(key) or "")
        for key in ("text", "title", "url", "metric_value", "metric_name", "publisher")
    )
    for brand in _AUTOMOTIVE_BRANDS:
        if _word_in_text(brand, blob):
            return True
    blob_low = blob.lower()
    return any(phrase in blob_low for phrase in _AUTOMOTIVE_BLOB_PHRASES)


def financial_diligence_record_relevant_for_topic(
    record: dict[str, Any],
    *,
    topic: str,
    industry: str,
    domain: str,
    topic_match_score: float | None = None,
    min_topic_match: float = 0.20,
) -> tuple[bool, str]:
    """Gate diligence tables, ledgers, verification inputs, and narrative merge."""
    _ = topic_match_score, min_topic_match  # superseded by canonical relevance gate
    ok, reason = competitor_record_relevant_for_topic(
        record,
        topic=topic,
        industry=industry,
        domain=domain,
    )
    if not ok:
        return False, reason
    from iidatech.validation.relevance_gate import is_record_relevant_to_report

    return is_record_relevant_to_report(record, topic, industry, domain)


def diligence_record_relevant_for_topic(
    record: dict[str, Any],
    *,
    topic: str,
    industry: str,
    domain: str,
    topic_match_score: float | None = None,
    min_topic_match: float = 0.20,
) -> tuple[bool, str]:
    """Canonical relevance gate alias for diligence / ledger / synthesis paths."""
    return financial_diligence_record_relevant_for_topic(
        record,
        topic=topic,
        industry=industry,
        domain=domain,
        topic_match_score=topic_match_score,
        min_topic_match=min_topic_match,
    )


def filter_diligence_records(
    records: list[dict[str, Any]],
    *,
    topic: str,
    industry: str,
    domain: str,
    geography: str = "",
    min_topic_match: float = 0.20,
    topic_match_score_fn: Any | None = None,
) -> list[dict[str, Any]]:
    """Filter any record list through the unified diligence relevance gate."""
    kept: list[dict[str, Any]] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        score: float | None = None
        if topic_match_score_fn is not None:
            try:
                raw = topic_match_score_fn(record, topic, industry, geography or "")
                if isinstance(raw, dict):
                    score = float(raw.get("score", 0) or 0)
                else:
                    score = float(raw or 0)
            except Exception:
                score = None
        ok, _reason = diligence_record_relevant_for_topic(
            record,
            topic=topic,
            industry=industry or str(record.get("industry") or ""),
            domain=domain,
            topic_match_score=score,
            min_topic_match=min_topic_match,
        )
        if ok:
            kept.append(record)
    return kept


def competitor_record_relevant_for_topic(
    record: dict[str, Any],
    *,
    topic: str,
    industry: str,
    domain: str,
) -> tuple[bool, str]:
    family = str(record.get("source_family") or "").lower()
    unit = str(record.get("unit") or "").lower()
    if family != "competitor_intelligence" and unit != "competitor":
        return True, "not_competitor_row"

    if is_placeholder_competitor_record(record):
        return False, "placeholder_competitor_pricing"

    name = extract_competitor_name(record)
    if not name:
        return False, "empty_competitor_name"

    nlow = name.lower()
    if nlow in _AUTOMOTIVE_BRANDS and not _automotive_domain_active(domain, topic, industry):
        return False, f"automotive_brand_out_of_domain:{name}"

    if nlow in _FESTIVE_NOISE and not _festive_domain_active(domain, topic, industry):
        return False, f"festive_noise_out_of_domain:{name}"

    if nlow in _SUBSTRING_TRAP_NAMES and not competitor_name_in_source_text(name, record):
        return False, f"substring_false_positive:{name}"

    url = str(record.get("url") or "").lower()
    if any(host in url for host in _ECOMMERCE_LISTING_HOSTS):
        if nlow in _AUTOMOTIVE_BRANDS or (
            nlow in _SUBSTRING_TRAP_NAMES and not _automotive_domain_active(domain, topic, industry)
        ):
            return False, "ecommerce_listing_not_competitor"

    return True, "ok"


def filter_records_for_narrative_synthesis(
    records: list[dict[str, Any]],
    *,
    topic: str,
    industry: str,
    domain: str,
    geography: str = "",
) -> list[dict[str, Any]]:
    return filter_diligence_records(
        records,
        topic=topic,
        industry=industry,
        domain=domain,
        geography=geography,
        min_topic_match=0.15,
    )


def should_index_learned_competitor_record(record: dict[str, Any]) -> bool:
    if str(record.get("source_family") or "").lower() != "competitor_intelligence":
        return True
    domain = ""
    for tag in record.get("topic_tags") or []:
        tag_s = str(tag).lower()
        if tag_s not in {
            "on_demand_research", "structured_extraction", "competitor", "credible_web",
            "source_discovery", "free_public", "funding_diligence_evidence", "buyer_proxy",
        } and len(tag_s) > 2:
            domain = tag_s
            break
    topic = str(record.get("text") or record.get("metric_value") or record.get("title") or "")
    industry = str(record.get("industry") or "")
    ok, _reason = competitor_record_relevant_for_topic(
        record,
        topic=topic,
        industry=industry,
        domain=domain or "general_market",
    )
    return ok
