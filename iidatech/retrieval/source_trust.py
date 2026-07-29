"""Data Truth Layer v1 - source trust tiers and truth weighting for retrieval."""
from __future__ import annotations
import os
import re
from typing import Any

TIER_WEIGHTS = {1: 1.0, 2: 0.8, 3: 0.6, 4: 0.35}
TIER_LABELS = {1: "tier_1_primary", 2: "tier_2_analyst", 3: "tier_3_reviews", 4: "tier_4_social"}

_TIER1_TOKENS = (
    "sec.gov", "edgar", "10-k", "10-q", "s-1", "annual report", "earnings report",
    "investor relations", "ir.", "gov.in", "gov.uk", "europa.eu", "mospi", "census.gov",
    "pricing page", "/pricing", "official pricing", "audited financial", "company_filing",
)
_TIER2_TOKENS = (
    "gartner", "mckinsey", "bain.com", "deloitte", "bcg.com", "kpmg", "ibisworld",
    "forrester", "idc.com", "industry association", "chamber of commerce", "nielsen",
    "analyst_report", "market_research", "trade_association",
)
_TIER3_TOKENS = (
    "g2.com", "capterra", "trustpilot", "getapp", "softwareadvice", "marketplace",
    "amazon.", "flipkart", "app store", "play.google", "review", "producthunt",
)
_TIER4_TOKENS = (
    "reddit.com", "quora.com", "youtube.com", "youtu.be", "twitter.com", "x.com",
    "facebook.com", "instagram.com", "medium.com", "substack", "blog.", "forum",
    "social_media", "reddit", "forum",
)

_TIER1_FAMILIES = frozenset({
    "government", "government_statistics", "central_bank", "company_filing", "company_filings",
    "company_reports", "official_survey", "regulatory_body", "pricing_reference", "local_operator_listing",
})
_TIER2_FAMILIES = frozenset({
    "analyst_report", "industry_pack_analyst", "industry_pack_government", "macro_trend_data",
    "industry_trend_data", "benchmark_report", "trade_association", "magazine_article",
})
_TIER3_FAMILIES = frozenset({
    "statista_public_metadata", "industry_news", "approved_press", "financial_news", "user_uploaded_survey",
})
_TIER4_FAMILIES = frozenset({
    "reddit_practitioner", "youtube_transcript", "podcast_interview", "published_voice_signal",
    "social_media", "forum", "anecdotal", "public_web",
})


def data_truth_layer_enabled() -> bool:
    return os.getenv("IIDATECH_DATA_TRUTH_LAYER", "1").strip().lower() not in {"0", "false", "no", "off"}


def _blob(record: dict[str, Any]) -> str:
    parts = [record.get("title"), record.get("publisher"), record.get("url"), record.get("source_family"), record.get("text"), record.get("summary")]
    return " ".join(str(p) for p in parts if p).lower()


def get_source_trust_tier(record: dict[str, Any]) -> dict[str, Any]:
    record = record if isinstance(record, dict) else {}
    if record.get("trust_tier") in TIER_WEIGHTS and record.get("truth_weight") is not None:
        tier = int(record["trust_tier"])
        return {"trust_tier": tier, "truth_weight": float(record["truth_weight"]), "trust_tier_label": TIER_LABELS.get(tier, "unknown"), "trust_reason": record.get("trust_reason", "preset")}

    family = str(record.get("source_family") or record.get("family") or "").lower()
    blob = _blob(record)

    tier, reason = 4, "default_weak"
    if family == "competitor_intelligence" or "iidatech_evidence_bank" in blob or "iidatech_evidence_bank" in str(record.get("topic_tags") or []):
        tier, reason = 1, "iidatech_competitor_bank"
    elif family in _TIER1_FAMILIES or any(t in blob for t in _TIER1_TOKENS):
        tier, reason = 1, "tier1_primary_source"
    elif family in _TIER2_FAMILIES or any(t in blob for t in _TIER2_TOKENS):
        tier, reason = 2, "tier2_analyst_or_association"
    elif family in _TIER3_FAMILIES or any(t in blob for t in _TIER3_TOKENS):
        tier, reason = 3, "tier3_reviews_or_marketplace"
    elif family in _TIER4_FAMILIES or any(t in blob for t in _TIER4_TOKENS):
        tier, reason = 4, "tier4_social_or_blog"

    try:
        from iidatech.integrity.source_trust_tier import classify_source_trust_tier
        integrity = classify_source_trust_tier(record)
        itier = int(integrity.get("trust_tier", tier))
        if itier == 1:
            tier, reason = 1, f"integrity_{integrity.get('trust_tier_reason', reason)}"
        elif itier == 2 and tier > 2:
            tier, reason = 2, f"integrity_{integrity.get('trust_tier_reason', reason)}"
        elif itier >= 4:
            tier, reason = 4, f"integrity_{integrity.get('trust_tier_reason', reason)}"
    except Exception:
        pass

    weight = TIER_WEIGHTS[tier]
    return {"trust_tier": tier, "truth_weight": weight, "trust_tier_label": TIER_LABELS[tier], "trust_reason": reason}


def compute_source_truth_score(record: dict[str, Any], base_score: float | None = None) -> float:
    meta = get_source_trust_tier(record)
    weight = float(meta["truth_weight"])
    base = float(base_score if base_score is not None else record.get("_selection_relevance_score") or record.get("quality_score") or record.get("confidence") or 0.5)
    if base > 1.5:
        base = base / 100.0
    numeric_bonus = 0.05 if record.get("hard_numeric") or re.search(r"\d", str(record.get("metric_value") or "")) else 0.0
    geo_bonus = 0.03 if record.get("geographic_match") else 0.0
    return round(max(0.0, min(1.5, base * (0.55 + 0.45 * weight) + numeric_bonus + geo_bonus)), 4)


def annotate_truth_fields(record: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(record, dict):
        return {}
    row = dict(record)
    meta = get_source_trust_tier(row)
    row.update(meta)
    row["source_truth_score"] = compute_source_truth_score(row, row.get("_selection_relevance_score"))
    return row


def apply_truth_weighting(records: list[dict[str, Any]], *, base_score_key: str = "_selection_relevance_score") -> list[dict[str, Any]]:
    if not data_truth_layer_enabled():
        return list(records or [])
    out: list[dict[str, Any]] = []
    for record in records or []:
        if not isinstance(record, dict):
            continue
        row = annotate_truth_fields(record)
        base = float(row.get(base_score_key) or 0.0)
        row["truth_augmented_score"] = round(base + (row.get("source_truth_score", 0.0) * 0.35), 4)
        out.append(row)
    out.sort(key=lambda r: float(r.get("truth_augmented_score") or 0.0), reverse=True)
    return out


def truth_augmented_rank_score(record: dict[str, Any], base_score: float) -> float:
    if not data_truth_layer_enabled():
        return base_score
    row = annotate_truth_fields({**record, "_selection_relevance_score": base_score})
    return float(row.get("truth_augmented_score") or base_score)


def summarize_truth_quality(records: list[dict[str, Any]]) -> dict[str, Any]:
    weighted = apply_truth_weighting(records) if records else []
    tiers = {1: 0, 2: 0, 3: 0, 4: 0}
    for row in weighted:
        tiers[int(row.get("trust_tier", 4))] = tiers.get(int(row.get("trust_tier", 4)), 0) + 1
    avg_truth = round(sum(float(r.get("source_truth_score", 0)) for r in weighted) / max(len(weighted), 1), 3)
    return {"record_count": len(weighted), "tier_counts": tiers, "avg_source_truth_score": avg_truth, "high_trust_count": tiers.get(1, 0) + tiers.get(2, 0)}