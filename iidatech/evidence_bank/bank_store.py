"""Persistent IIDATECH evidence bank store and prefetch orchestrator."""
from __future__ import annotations
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BANK_DIR = Path(__file__).resolve().parent / "data"
DOMAIN_BANK_FILES = {
    "crm_automation": "crm_automation.jsonl",
    "b2b_saas": "crm_automation.jsonl",
    "revops_sales_automation": "crm_automation.jsonl",
    "ai_workflow_automation": "crm_automation.jsonl",
    "saas_general": "saas_general.jsonl",
    "ecommerce_retail": "ecommerce_retail.jsonl",
    "consumer": "d2c_skincare.jsonl",
    "fashion": "d2c_skincare.jsonl",
    "d2c_skincare": "d2c_skincare.jsonl",
    "dental_saas": "dental_clinics.jsonl",
    "clinic_workflow": "clinic_workflow.jsonl",
    "healthcare": "healthcare_saas.jsonl",
    "healthcare_saas": "healthcare_saas.jsonl",
    "automotive": "automotive_retail.jsonl",
    "automotive_retail": "automotive_retail.jsonl",
    "agency_services": "agency_services.jsonl",
    "restaurants": "restaurants.jsonl",
    "logistics": "logistics.jsonl",
    "fintech": "fintech.jsonl",
    "edtech": "edtech.jsonl",
    "legaltech": "legaltech.jsonl",
    "hrtech": "hrtech.jsonl",
    "proptech": "proptech.jsonl",
    "dental_clinics": "dental_clinics.jsonl",
}


def evidence_bank_enabled() -> bool:
    return os.getenv("IIDATECH_EVIDENCE_BANK", "1").strip().lower() not in {"0", "false", "no", "off"}


def load_jsonl_bank(filename: str) -> list[dict[str, Any]]:
    """Curated seed banks removed — live evidence comes from Perplexity Sonar only."""
    return []


def resolve_bank_file(domain: str) -> str:
    key = (domain or "general").lower()
    return DOMAIN_BANK_FILES.get(key, "saas_general.jsonl")


def normalize_competitor_name(name: str) -> str:
    raw = (name or "").strip().lower()
    raw = raw.split("/")[0].strip()
    raw = re.sub(r"\([^)]*\)", "", raw).strip()
    raw = re.sub(
        r"\s+(?:for\s+)?(?:small\s+business(?:es)?|smb(?:s)?|india|global|enterprises?).*$",
        "",
        raw,
        flags=re.I,
    )
    base = re.sub(r"[^a-z0-9]", "", raw)
    for suffix in ("software", "platform", "suite", "cloud", "crm", "app", "india", "starter", "pro"):
        if base.endswith(suffix) and len(base) > len(suffix) + 2:
            base = base[: -len(suffix)]
    return base


_PLACEHOLDER_MARKERS = (
    "see official pricing page",
    "verify locally",
    "check g2 reviews",
)


def _is_placeholder(row: dict[str, Any]) -> bool:
    blobs = [
        str(row.get("pricing") or ""),
        str(row.get("positioning") or ""),
    ]
    for key in ("strengths", "weaknesses", "complaints"):
        for item in row.get(key) or []:
            blobs.append(str(item))
    text = " ".join(blobs).lower()
    return any(marker in text for marker in _PLACEHOLDER_MARKERS)


def _company_key(row: dict[str, Any]) -> str:
    return normalize_competitor_name(str(row.get("company_name") or row.get("name") or ""))


def _is_perplexity_row(row: dict[str, Any]) -> bool:
    blob = " ".join(
        str(row.get(key) or "")
        for key in ("discovered_via", "source_type", "source_engine")
    ).lower()
    return "perplexity" in blob


def _row_priority(row: dict[str, Any]) -> tuple[int, int, int]:
    """Lower tuple = preferred merge base. Perplexity narrative rows beat pricing-only patches."""
    if _is_perplexity_row(row):
        tier = 0
    elif str(row.get("verification_status") or "") == "firecrawl_verified":
        tier = 1
    elif row.get("source_type") in {"official_pricing_page", "manual"}:
        tier = 2
    else:
        tier = 3
    discrepancy_penalty = 1 if row.get("pricing_discrepancy") else 0
    narrative_richness = -(
        len(str(row.get("positioning") or ""))
        + sum(len(str(x)) for x in (row.get("strengths") or [])[:4])
        + sum(len(str(x)) for x in (row.get("weaknesses") or [])[:4])
    )
    return (tier, discrepancy_penalty, narrative_richness)


def _merge_list_field(left: list[Any], right: list[Any], *, limit: int = 8) -> list[Any]:
    return list(dict.fromkeys([*(left or []), *(right or [])]))[:limit]


def _apply_pricing_resolution(row: dict[str, Any]) -> dict[str, Any]:
    """Firecrawl wins pricing when a discrepancy was flagged; Perplexity keeps everything else."""
    out = dict(row)
    if out.get("pricing_discrepancy"):
        firecrawl_price = str(out.get("firecrawl_pricing") or "").strip()
        if firecrawl_price:
            if not out.get("perplexity_pricing"):
                out["perplexity_pricing"] = str(out.get("pricing") or out.get("price") or "").strip()
            out["pricing"] = firecrawl_price
    elif not str(out.get("pricing") or "").strip():
        out["pricing"] = str(out.get("price") or out.get("firecrawl_pricing") or "").strip()
    return out


def _merge_competitor_row(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    """Merge duplicate company rows; primary supplies Perplexity narrative fields."""
    merged = dict(primary)
    secondary = dict(secondary)

    for field in (
        "pricing_discrepancy",
        "perplexity_pricing",
        "firecrawl_pricing",
        "pricing_page_url",
        "verification_status",
        "discovered_via",
        "source_type",
        "source_engine",
    ):
        if field == "pricing_discrepancy":
            merged[field] = bool(merged.get(field) or secondary.get(field))
        else:
            merged[field] = merged.get(field) or secondary.get(field)

    for field in ("positioning", "gtm_model", "category", "country", "industry"):
        if not str(merged.get(field) or "").strip() and secondary.get(field):
            merged[field] = secondary[field]

    for field in ("strengths", "weaknesses", "complaints"):
        merged[field] = _merge_list_field(
            list(merged.get(field) or []),
            list(secondary.get(field) or []),
        )

    urls: list[str] = []
    for source in (merged, secondary):
        urls.extend(list(source.get("source_urls") or []))
        page_url = str(source.get("pricing_page_url") or "").strip()
        if page_url:
            urls.append(page_url)
    merged["source_urls"] = list(dict.fromkeys(url for url in urls if url))[:6]

    return _apply_pricing_resolution(merged)


def dedupe_competitor_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    best: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = _company_key(row)
        if not key:
            continue
        candidate = dict(row)
        if not candidate.get("company_name") and candidate.get("name"):
            candidate["company_name"] = candidate["name"]

        existing = best.get(key)
        if existing is None:
            best[key] = _apply_pricing_resolution(candidate)
            continue

        if _row_priority(candidate) < _row_priority(existing):
            best[key] = _merge_competitor_row(candidate, existing)
        else:
            best[key] = _merge_competitor_row(existing, candidate)

    return list(best.values())


def discovered_bank_path(domain: str) -> Path:
    base = resolve_bank_file(domain).replace(".jsonl", "")
    return BANK_DIR / f"{base}_discovered.jsonl"


def merge_discovered_competitors_into_bank(domain: str, new_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Seed bank persistence disabled — discovered rows stay in-memory for the report only."""
    return {"added": 0, "discovered_file": "", "total_discovered": 0, "persisted": False}


def load_full_competitor_bank(domain: str) -> list[dict[str, Any]]:
    return []


def _topic_match(row: dict[str, Any], topic: str, target: str) -> float:
    blob = f"{topic} {target}".lower()
    company = str(row.get("company_name", "")).lower()
    category = str(row.get("category", "")).lower()
    country = str(row.get("country", "")).lower()
    score = 0.0
    for token in re.findall(r"[a-z0-9]+", blob):
        if len(token) < 4:
            continue
        if token in company or token in category:
            score += 0.25
    if country and country in target.lower():
        score += 0.35
    if "global" in target.lower():
        score += 0.15
    return min(score, 1.0)


def search_competitor_bank(domain: str, topic: str, target: str, limit: int = 12) -> list[dict[str, Any]]:
    return []


def bank_row_to_learned_record(row: dict[str, Any], domain: str, target: str):
    from on_demand_research import LearnedRecord, now_iso, record_id
    urls = row.get("source_urls") or []
    url = urls[0] if urls else f"https://iidatech.local/evidence_bank/{row.get('company_name','unknown')}"
    trust = float(row.get("trust_score") or 1.0)
    text_parts = [
        f"Company: {row.get('company_name')}",
        f"Positioning: {row.get('positioning')}",
        f"Pricing: {row.get('pricing')}",
        f"GTM: {row.get('gtm_model')}",
        f"Strengths: {', '.join(row.get('strengths') or [])}",
        f"Weaknesses: {', '.join(row.get('weaknesses') or [])}",
        f"Complaints: {', '.join(row.get('complaints') or [])}",
        f"Metrics: {json.dumps(row.get('metrics') or {}, ensure_ascii=False)}",
        f"Source type: {row.get('source_type')} | Last verified: {row.get('last_verified')}",
        "IIDATECH proprietary competitor intelligence bank — verify before investor citation.",
    ]
    return LearnedRecord(
        id=record_id(url, row.get("company_name", ""), target),
        source_family="competitor_intelligence",
        publisher=str(row.get("company_name") or "competitor_bank"),
        title=f"{row.get('company_name')} — {row.get('category', 'competitor')}",
        url=url,
        retrieved_at=now_iso(),
        geography=target or row.get("country") or "Global",
        year=str(datetime.now(timezone.utc).year),
        metric_name="competitor_intelligence_bank",
        metric_value=str(row.get("pricing") or "")[:240],
        unit="bank_row",
        topic_tags=["iidatech_evidence_bank", domain, "competitor_bank", str(row.get("industry", ""))],
        text=" ".join(text_parts)[:2200],
        confidence=trust,
        industry=str(row.get("industry") or ""),
        claim_type="competitor",
        evidence_tier="bank_verified",
        allowed_use="Competitor intelligence from IIDATECH bank; confirm pricing on official page before citation.",
    )


def search_benchmark_bank(domain: str, target: str) -> list[dict[str, Any]]:
    try:
        from iidatech.data.financial_benchmark_bank import build_benchmark_financial_pack
        pack = build_benchmark_financial_pack(domain)
        return [{"benchmark_domain": pack.get("benchmark_domain"), "unit_economics_benchmarks": pack.get("unit_economics_benchmarks"), "disclaimer": pack.get("disclaimer"), "trust_score": 0.82, "source_type": "benchmark_bank"}]
    except Exception:
        return []


def benchmark_to_learned_record(row: dict[str, Any], domain: str, target: str):
    from on_demand_research import LearnedRecord, now_iso, record_id
    url = "https://iidatech.local/evidence_bank/financial_benchmark"
    ue = row.get("unit_economics_benchmarks") or {}
    return LearnedRecord(
        id=record_id(url, domain, target),
        source_family="financial_model_bank",
        publisher="IIDATECH Benchmark Bank",
        title=f"Financial benchmarks — {row.get('benchmark_domain', domain)}",
        url=url,
        retrieved_at=now_iso(),
        geography=target or "Global",
        year=str(datetime.now(timezone.utc).year),
        metric_name="benchmark_unit_economics",
        metric_value=json.dumps(ue, ensure_ascii=False)[:500],
        unit="benchmark",
        topic_tags=["iidatech_evidence_bank", domain, "benchmark_bank"],
        text=f"Benchmark-derived assumptions (not company data). {row.get('disclaimer', '')} Values: {json.dumps(ue, ensure_ascii=False)}",
        confidence=float(row.get("trust_score") or 0.82),
        claim_type="benchmark",
        evidence_tier="benchmark_derived",
        allowed_use="Planning benchmark only — label as assumption.",
    )


def prefetch_evidence_layers(
    *,
    topic: str,
    industry: str,
    target: str,
    domain: str,
    diagnostics: list[dict] | None = None,
    max_records: int = 12,
    search_api_keys: dict | None = None,
    search_api_budgets: dict | None = None,
) -> dict[str, Any]:
    """Retrieval order: SQL semantic memory -> benchmark banks -> Perplexity Sonar (+ Firecrawl verify)."""
    if not evidence_bank_enabled():
        return {"records": [], "trace": {"enabled": False}, "diagnostics": []}
    from iidatech.evidence_bank.google_competitor_discovery import (
        discover_live_competitors,
        serp_entities_to_learned_records,
        serp_enabled,
    )
    from on_demand_research import LearnedRecord, clean_html_text, now_iso, record_id

    records = []
    trace = {
        "semantic_memory_hits": 0,
        "bank_hits": 0,
        "benchmark_hits": 0,
        "serp_competitor_hits": 0,
        "exact_search_hits": 0,
        "perplexity_hits": 0,
        "firecrawl_pricing_checks": 0,
        "pricing_discrepancies": 0,
        "new_competitors_discovered": 0,
    }
    layer_diags: list[dict] = []

    try:
        from iidatech.storage.semantic_memory import search_semantic_records, semantic_memory_ready

        if semantic_memory_ready():
            sem_hits = search_semantic_records(f"{topic} {industry}", limit=max(8, max_records))
            for hit in sem_hits:
                industry_tag = str(hit.get("industry") or domain or "")
                title = str(hit.get("title") or hit.get("company") or hit.get("product") or hit.get("complaint") or hit.get("metric") or "semantic memory hit")
                snippet = json.dumps({k: v for k, v in hit.items() if k not in {"embedding_model"}}, ensure_ascii=False)[:700]
                records.append(
                    LearnedRecord(
                        id=record_id(str(hit.get("record_key") or title), topic, target),
                        source_family="sql_semantic_memory",
                        publisher=str(hit.get("source_table") or "sql_semantic_memory"),
                        title=clean_html_text(title, 200),
                        url=str(hit.get("url") or hit.get("source_url") or ""),
                        retrieved_at=now_iso(),
                        geography=target or "Global",
                        year=str(hit.get("year") or ""),
                        metric_name="semantic_similarity",
                        metric_value=str(hit.get("similarity_score") or ""),
                        unit="cosine",
                        topic_tags=["iidatech_semantic_memory", domain, industry_tag, str(hit.get("source_table") or "")],
                        text=f"SQL semantic memory ({hit.get('source_table')}). similarity={hit.get('similarity_score')}. {snippet}",
                        confidence=min(0.95, 0.55 + float(hit.get("similarity_score") or 0) * 0.4),
                        industry=industry,
                        claim_type="semantic_memory",
                        evidence_tier="sql_semantic_memory",
                        allowed_use="Cross-domain SQL semantic match — verify on source.",
                    )
                )
            trace["semantic_memory_hits"] = len(sem_hits)
            layer_diags.append({
                "provider": "SQL Semantic Memory",
                "configured": True,
                "attempted": True,
                "returned": len(sem_hits),
                "accepted": len(sem_hits),
            })
        else:
            layer_diags.append({"provider": "SQL Semantic Memory", "configured": False, "attempted": False, "returned": 0, "accepted": 0})
    except Exception as exc:
        trace["semantic_memory_error"] = str(exc)[:200]
        layer_diags.append({"provider": "SQL Semantic Memory", "configured": False, "attempted": True, "returned": 0, "accepted": 0, "error": str(exc)[:120]})

    bank_rows = search_competitor_bank(domain, topic, target, limit=max(6, max_records // 2))
    for row in bank_rows:
        records.append(bank_row_to_learned_record(row, domain, target))
    trace["bank_hits"] = len(bank_rows)
    layer_diags.append({"provider": "IIDATECH Competitor Bank", "configured": True, "attempted": True, "returned": len(bank_rows), "accepted": len(bank_rows)})

    bench_rows = search_benchmark_bank(domain, target)
    for row in bench_rows:
        records.append(benchmark_to_learned_record(row, domain, target))
    trace["benchmark_hits"] = len(bench_rows)
    layer_diags.append({"provider": "IIDATECH Benchmark Bank", "configured": True, "attempted": True, "returned": len(bench_rows), "accepted": len(bench_rows)})

    report_degraded = False
    degrade_reason = ""
    serp_entities: list[dict] = []
    serp_intelligence_block: dict[str, Any] = {
        "enabled": False,
        "structured_records": [],
        "entities": [],
        "queries": [],
        "trace": {},
        "pricing_discrepancies": [],
    }
    if serp_enabled():
        from iidatech.evidence_bank.serp_intelligence import structured_to_learned_records

        serp_payload = discover_live_competitors(topic, domain, target, industry=industry)
        report_degraded = bool(serp_payload.get("report_degraded"))
        degrade_reason = str(serp_payload.get("degrade_reason") or "")
        serp_entities = serp_payload.get("entities") or []
        structured = serp_payload.get("structured_records") or []
        merge_result = merge_discovered_competitors_into_bank(domain, serp_entities)
        trace["new_competitors_discovered"] = int(merge_result.get("added") or 0)
        serp_records = serp_entities_to_learned_records(serp_entities[:max(6, max_records // 3)], domain, target)
        serp_records.extend(structured_to_learned_records(structured[:max(8, max_records // 2)], domain, target))
        records.extend(serp_records)
        intel_trace = serp_payload.get("trace") or {}
        trace["serp_competitor_hits"] = len(serp_records)
        trace["perplexity_hits"] = int(intel_trace.get("perplexity_hits") or 0)
        trace["firecrawl_pricing_checks"] = int(intel_trace.get("firecrawl_checks") or 0)
        trace["pricing_discrepancies"] = int(intel_trace.get("pricing_discrepancies") or 0)
        trace["structured_records_generated"] = int(intel_trace.get("structured_records_generated") or 0)
        trace["serp_queries"] = (serp_payload.get("queries") or [])[:12]
        serp_intelligence_block = {
            "enabled": True,
            "structured_records": structured,
            "entities": serp_entities,
            "queries": serp_payload.get("queries") or [],
            "trace": intel_trace,
            "pricing_discrepancies": serp_payload.get("pricing_discrepancies") or [],
        }
        layer_diags.append({
            "provider": "Perplexity Sonar",
            "configured": True,
            "attempted": True,
            "returned": len(serp_entities) + len(structured),
            "accepted": len(serp_records),
        })
    else:
        trace["serp_competitor_hits"] = 0
        report_degraded = True
        degrade_reason = degrade_reason or "perplexity_not_configured"
        layer_diags.append({
            "provider": "Perplexity Sonar",
            "configured": False,
            "attempted": False,
            "returned": 0,
            "accepted": 0,
        })

    if diagnostics is not None:
        diagnostics.extend(layer_diags)
    return {
        "records": records[:max_records],
        "trace": trace,
        "diagnostics": layer_diags,
        "serp_intelligence": serp_intelligence_block,
        "report_degraded": report_degraded,
        "report_degrade_reason": degrade_reason,
    }