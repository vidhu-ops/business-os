"""Weighted domain ontology router with hard-negative guards for IIDATECH retrieval."""
from __future__ import annotations
import re
from typing import Any

_LAST_ROUTING_TRACE: dict[str, Any] = {}

DOMAIN_ONTOLOGY: dict[str, dict[str, tuple[str, ...]]] = {
    "festive_retail": {
        "strong": ("ganesh chaturthi", "ganesh", "diwali", "navratri", "durga puja", "holi", "rakhi", "onam", "pongal", "janmashtami"),
        "medium": ("festive", "puja", "rangoli", "decoration kit", "festival decor", "idol", "diyas", "craft kit", "eco-friendly decor"),
        "weak": ("apartment society", "housing society", "society decor", "community decor", "seasonal decor", "celebration kit"),
    },
    "event_services": {
        "strong": ("event setup", "event rental", "event management", "mandap rental", "wedding decor", "floral backdrop", "stage setup", "light show", "drone show", "drone light show"),
        "medium": ("mandap", "backdrop", "venue decor", "banquet setup", "sangeet decor", "reception decor", "corporate event", "event planner"),
        "weak": ("rental", "event services", "decor rental", "setup services"),
    },
    "wedding_services": {
        "strong": ("wedding mandap", "wedding planner", "wedding decor", "bridal", "mehendi", "sangeet", "wedding venue", "wedding rental"),
        "medium": ("wedding", "marriage", "shaadi", "bride", "groom", "wedding package", "destination wedding"),
        "weak": ("matrimony", "wedding services"),
    },
    "decor_retail": {
        "strong": ("decoration kit", "decor products", "home decor", "interior decor", "wall decor", "party decor"),
        "medium": ("decor", "decoration", "ornament", "centerpiece", "table decor", "festive decor"),
        "weak": ("apartment decor", "society decoration", "living room decor", "handmade decor"),
    },
    "gifting_retail": {
        "strong": ("gift hamper", "corporate gifting", "festive gifting", "gift box", "return gift", "wedding favor"),
        "medium": ("gifting", "gift shop", "gift store", "hamper", "souvenir"),
        "weak": ("gift retail", "occasion gift"),
    },
    "local_services": {
        "strong": ("local service", "hyperlocal", "neighborhood service", "society service", "apartment service"),
        "medium": ("justdial", "urban company", "local vendor", "near me", "city service", "doorstep"),
        "weak": ("local business", "community service"),
    },
    "creator_business": {
        "strong": ("content creator", "influencer business", "youtube channel", "creator economy", "digital creator"),
        "medium": ("creator", "influencer", "monetization", "personal brand", "ugc"),
        "weak": ("social media business", "online creator"),
    },
    "home_services": {
        "strong": ("home cleaning", "plumbing service", "electrician", "pest control", "home repair", "handyman"),
        "medium": ("home services", "housekeeping", "maintenance service", "facility maintenance"),
        "weak": ("home service", "residential service"),
    },
    "crm_automation": {
        "strong": ("crm automation", "sales crm", "hubspot", "pipedrive", "zoho crm"),
        "medium": ("crm", "sales pipeline", "lead management", "sales automation"),
        "weak": ("customer relationship", "sales software"),
    },
    "saas_software": {
        "strong": ("b2b saas", "saas platform", "subscription software", "cloud software"),
        "medium": ("saas", "software platform", "workflow software", "enterprise software"),
        "weak": ("business software", "automation platform"),
    },
    "d2c_skincare": {
        "strong": ("skincare brand", "organic skincare", "serum", "moisturizer", "cosmetics brand", "nykaa", "purplle", "d2c beauty"),
        "medium": ("skincare", "cosmetic", "beauty brand", "face wash", "sunscreen"),
        "weak": ("beauty", "personal care brand", "makeup"),
    },
    "automotive_retail": {
        "strong": ("car dealership", "auto garage", "luxury car service", "car retail"),
        "medium": ("automotive retail", "car workshop", "vehicle service center"),
        "weak": ("dealership", "auto repair"),
    },
    "agriculture": {
        "strong": ("agriculture", "farming", "agribusiness", "crop cultivation"),
        "medium": ("farmer", "farm produce", "horticulture", "livestock"),
        "weak": ("farm", "agri"),
    },
}

WEIGHTS = {"strong": 3.0, "medium": 2.0, "weak": 1.0}
FESTIVE_BLOCK_TERMS = ("ganesh", "diwali", "navratri", "mandap", "puja", "rangoli", "holi", "durga puja", "sangeet", "wedding decor", "festive decor", "decoration kit")
BLOCKED_DOMAINS_UNDER_FESTIVE = frozenset({"d2c_skincare", "ecommerce_retail", "agriculture", "consumer", "fashion"})
HARD_NEGATIVE_CONFIDENCE = 0.85
SELECTION_THRESHOLD = 0.45

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower()).strip()

def _haystack(topic: str, industry: str, country: str = "") -> str:
    return _normalize(f"{topic} {industry} {country}")

def _term_hits(haystack: str, term: str) -> bool:
    needle = term.lower().strip()
    if not needle:
        return False
    if any(ch in needle for ch in (" ", "_", "/", "-", ".")):
        return needle in haystack
    return re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack) is not None

def score_domains(topic: str, industry: str, country: str = "") -> dict[str, float]:
    haystack = _haystack(topic, industry, country)
    scores: dict[str, float] = {}
    for domain, buckets in DOMAIN_ONTOLOGY.items():
        total = 0.0
        for bucket, terms in buckets.items():
            weight = WEIGHTS[bucket]
            for term in terms:
                if _term_hits(haystack, term):
                    total += weight
        if total:
            scores[domain] = round(total, 3)
    return scores

def _festive_signal(haystack: str) -> bool:
    return any(_term_hits(haystack, term) for term in FESTIVE_BLOCK_TERMS)

def apply_hard_negatives(scores: dict[str, float], haystack: str) -> tuple[dict[str, float], list[str], str]:
    adjusted = dict(scores)
    rejected: list[str] = []
    reason = ""
    if not _festive_signal(haystack):
        return adjusted, rejected, reason
    reason = "festive/event hard-negative: blocked skincare/agriculture/beauty routing"
    for domain in list(adjusted):
        if domain in BLOCKED_DOMAINS_UNDER_FESTIVE:
            rejected.append(domain)
            del adjusted[domain]
    if "eco-friendly" in haystack or "eco friendly" in haystack:
        for bleed in ("consumer", "ecommerce_retail", "climate"):
            if bleed in adjusted:
                adjusted[bleed] = round(adjusted[bleed] * 0.35, 3)
    return adjusted, rejected, reason

def _confidence(top_score: float, second_score: float) -> float:
    if top_score <= 0:
        return 0.0
    margin = top_score - second_score
    return round(min(0.98, 0.42 + (top_score * 0.08) + (margin * 0.06)), 3)

def route_domain(topic: str, industry: str, country: str = "") -> dict[str, Any]:
    haystack = _haystack(topic, industry, country)
    raw_scores = score_domains(topic, industry, country)
    domain_scores, rejected_domains, negative_reason = apply_hard_negatives(raw_scores, haystack)
    if not domain_scores:
        trace = {"domain_scores": raw_scores, "selected_domain": "", "rejected_domains": rejected_domains, "reason": negative_reason or "no domain scored above zero", "confidence": 0.0}
        _store_trace(trace)
        return trace
    ranked = sorted(domain_scores.items(), key=lambda item: (-item[1], item[0]))
    selected_domain, top_score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = _confidence(top_score, second_score)
    if _festive_signal(haystack) and selected_domain in BLOCKED_DOMAINS_UNDER_FESTIVE and confidence < HARD_NEGATIVE_CONFIDENCE:
        for domain, score in ranked[1:]:
            if domain not in BLOCKED_DOMAINS_UNDER_FESTIVE:
                selected_domain, top_score = domain, score
                confidence = _confidence(top_score, second_score)
                break
    reason_parts = []
    if negative_reason:
        reason_parts.append(negative_reason)
    reason_parts.append(f"top={selected_domain} score={top_score} confidence={confidence}")
    if rejected_domains:
        reason_parts.append(f"rejected={','.join(rejected_domains)}")
    selected = selected_domain if confidence >= SELECTION_THRESHOLD else ""
    trace = {"domain_scores": raw_scores, "selected_domain": selected, "rejected_domains": rejected_domains, "reason": "; ".join(reason_parts), "confidence": confidence, "ranked": [{"domain": d, "score": s} for d, s in ranked[:5]]}
    _store_trace(trace)
    return trace

def classify_domain_with_trace(topic: str, industry: str, country: str = "") -> dict[str, Any]:
    return route_domain(topic, industry, country)

def get_last_routing_trace() -> dict[str, Any]:
    return dict(_LAST_ROUTING_TRACE)

def should_block_domain(topic: str, domain: str, industry: str = "") -> tuple[bool, str]:
    haystack = _haystack(topic, industry)
    if not _festive_signal(haystack):
        return False, ""
    if domain in BLOCKED_DOMAINS_UNDER_FESTIVE:
        return True, "festive hard-negative blocked domain"
    if domain in {"d2c_skincare", "agriculture"} and _festive_signal(haystack) and not any(_term_hits(haystack, t) for t in ("skincare", "serum", "moisturizer", "cosmetic", "nykaa")):
        return True, "festive context overrides beauty/agriculture bleed"
    return False, ""

def _store_trace(trace: dict[str, Any]) -> None:
    global _LAST_ROUTING_TRACE
    _LAST_ROUTING_TRACE = trace