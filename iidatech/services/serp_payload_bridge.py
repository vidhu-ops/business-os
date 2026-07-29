"""Wire live market intelligence (Perplexity Sonar) into report payload and research_brain."""
from __future__ import annotations

import re
from typing import Any

_SEED_VENDOR_RE = re.compile(r"\bvendor\s*\d+\b|d2c skincare vendor|generic competitor", re.I)


def _as_dict(value: Any) -> dict:
    return value if isinstance(value, dict) else {}


def _as_list(value: Any) -> list:
    return value if isinstance(value, list) else []


def is_seed_vendor_name(name: str) -> bool:
    text = str(name or "").strip().lower()
    if not text or len(text) < 2:
        return True
    return bool(_SEED_VENDOR_RE.search(text))


def _live_competitor_names(structured: list[dict[str, Any]], entities: list[dict[str, Any]]) -> list[str]:
    try:
        from iidatech.evidence_bank.google_competitor_discovery import is_valid_competitor_display_name
    except ImportError:
        def is_valid_competitor_display_name(name: str) -> bool:
            return bool(name) and not is_seed_vendor_name(name)

    names: list[str] = []
    seen: set[str] = set()
    for rec in structured:
        if str(rec.get("record_type") or "competitor").lower() != "competitor":
            continue
        name = str(rec.get("name") or rec.get("company_name") or "").strip()
        if not name or is_seed_vendor_name(name) or not is_valid_competitor_display_name(name):
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    for ent in entities:
        name = str(ent.get("company_name") or ent.get("name") or "").strip()
        if not name or is_seed_vendor_name(name) or not is_valid_competitor_display_name(name):
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    return names


def normalize_serp_block(raw: dict[str, Any] | None) -> dict[str, Any]:
    raw = _as_dict(raw)
    structured = [r for r in _as_list(raw.get("structured_records")) if isinstance(r, dict)]
    entities = [r for r in _as_list(raw.get("entities")) if isinstance(r, dict)]
    enabled = bool(raw.get("enabled", True)) and bool(structured or entities or raw.get("queries"))
    return {
        "enabled": enabled,
        "structured_records": structured,
        "entities": entities,
        "queries": list(_as_list(raw.get("queries"))),
        "trace": dict(_as_dict(raw.get("trace"))),
        "pricing_discrepancies": list(_as_list(raw.get("pricing_discrepancies"))),
        "report_degraded": bool(raw.get("report_degraded")),
        "degrade_reason": str(raw.get("degrade_reason") or ""),
    }


def resolve_report_domain(topic: str, industry: str, geography: str, domain: str | None = None) -> str:
    if domain:
        return str(domain)
    try:
        from iidatech.routing.domain_router import route_domain

        routed = route_domain(topic, industry, geography)
        selected = str(routed.get("selected_domain") or "").strip()
        if selected:
            return selected
    except Exception:
        pass
    return "general_market"


def fetch_serp_intelligence(
    topic: str,
    industry: str,
    geography: str,
    *,
    domain: str | None = None,
) -> dict[str, Any]:
    """Fetch market intelligence via Perplexity Sonar (kept as serp_intelligence for report compat)."""
    domain = resolve_report_domain(topic, industry, geography, domain)
    try:
        from iidatech.evidence_bank.perplexity_client import fetch_market_intelligence, perplexity_enabled

        if not perplexity_enabled():
            return {
                "enabled": False,
                "structured_records": [],
                "entities": [],
                "queries": [],
                "trace": {"error": "PERPLEXITY_API_KEY not configured"},
                "report_degraded": True,
                "degrade_reason": "perplexity_not_configured",
            }
        payload = fetch_market_intelligence(topic, domain, geography, industry=industry)
        block = normalize_serp_block({**payload, "enabled": bool(payload.get("enabled"))})
        block["report_degraded"] = bool(payload.get("report_degraded"))
        block["degrade_reason"] = str(payload.get("degrade_reason") or "")
        block["pricing_discrepancies"] = list(payload.get("pricing_discrepancies") or [])
        return block
    except Exception as exc:
        return {
            "enabled": False,
            "structured_records": [],
            "entities": [],
            "queries": [],
            "trace": {"error": str(exc)[:240]},
            "report_degraded": True,
            "degrade_reason": str(exc)[:240],
        }


def structured_to_brain_records(
    structured: list[dict[str, Any]],
    entities: list[dict[str, Any]],
    *,
    domain: str,
    geography: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(row: dict[str, Any]) -> None:
        name = str(row.get("title") or row.get("publisher") or "").strip().lower()
        if not name or name in seen:
            return
        seen.add(name)
        rows.append(row)

    for rec in structured:
        rtype = str(rec.get("record_type") or "competitor").lower()
        name = str(rec.get("name") or rec.get("company_name") or rec.get("title") or "").strip()
        if not name or is_seed_vendor_name(name):
            continue
        text_bits = [
            str(rec.get("positioning") or ""),
            str(rec.get("review_text") or ""),
            str(rec.get("complaints") or ""),
            str(rec.get("wtp_signals") or ""),
            str(rec.get("objections") or ""),
        ]
        _add(
            {
                "record_type": rtype,
                "claim_type": rtype,
                "source_family": f"serp_{rtype}",
                "title": name[:120],
                "publisher": name[:120],
                "company_name": name[:120],
                "url": str(rec.get("source_url") or rec.get("url") or ""),
                "metric_value": str(rec.get("price") or rec.get("pricing") or ""),
                "monthly_price": str(rec.get("price") or rec.get("pricing") or ""),
                "text": " | ".join(bit for bit in text_bits if bit.strip())[:700],
                "confidence": 0.66,
                "evidence_tier": "serp_intelligence",
                "domain": domain,
                "geography": geography,
            }
        )

    for ent in entities:
        name = str(ent.get("company_name") or ent.get("name") or "").strip()
        if not name or is_seed_vendor_name(name):
            continue
        _add(
            {
                "record_type": "competitor",
                "claim_type": "competitor",
                "source_family": "serp_competitor_intelligence",
                "title": name[:120],
                "publisher": name[:120],
                "company_name": name[:120],
                "url": str(ent.get("website") or ent.get("url") or ""),
                "metric_value": str(ent.get("pricing") or ""),
                "text": str(ent.get("positioning") or "")[:500],
                "confidence": float(ent.get("trust_score") or 0.62),
                "evidence_tier": "serp_intelligence",
                "domain": domain,
                "geography": geography,
            }
        )
    return rows


def _merge_citation_ledger(ledger: list[dict[str, Any]], brain_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = list(ledger)
    seen = {str(item.get("title") or "").strip().lower() for item in out if isinstance(item, dict)}
    for row in brain_rows:
        title = str(row.get("title") or "").strip()
        key = title.lower()
        if not title or key in seen:
            continue
        seen.add(key)
        out.append(
            {
                "grade": "B",
                "title": title,
                "url": row.get("url") or "",
                "source_family": row.get("source_family") or "serp_intelligence",
                "publisher": row.get("publisher") or title,
                "year": "",
                "metric": row.get("metric_value") or "",
                "use_in_report": "serp_live_discovery",
            }
        )
    return out[:40]


def _merge_competitor_pack(pack: dict[str, Any], brain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    out = dict(pack)
    competitors = list(_as_list(out.get("competitors")))
    seen = {str(c.get("name") or c.get("company") or "").lower() for c in competitors if isinstance(c, dict)}
    for row in brain_rows:
        if str(row.get("record_type") or "").lower() != "competitor":
            continue
        name = str(row.get("title") or "").strip()
        if not name or is_seed_vendor_name(name) or name.lower() in seen:
            continue
        seen.add(name.lower())
        competitors.append(
            {
                "name": name,
                "segment": "serp_discovered",
                "pricing": row.get("metric_value") or row.get("monthly_price") or "unknown",
                "url": row.get("url") or "",
                "source": "serp_intelligence",
                "verification_status": "live_serp",
            }
        )
    out["competitors"] = competitors[:20]
    return out


def build_live_competitive_benchmark(
    structured: list[dict[str, Any]],
    entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Named competitor benchmark rows from live SERP structured records."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _append(name: str, *, positioning: str = "", pricing: str = "", url: str = "", segment: str = "live_serp") -> None:
        if not name or is_seed_vendor_name(name):
            return
        key = name.lower()
        if key in seen:
            return
        seen.add(key)
        rows.append(
            {
                "name": name,
                "segment": segment,
                "competitor_archetypes": name,
                "positioning": positioning,
                "pricing": pricing or "unknown",
                "source": url,
                "benchmark_metrics": f"pricing={pricing or 'n/a'}; source=serp_live_discovery",
                "source_need": "vendor pricing page and reviews",
                "verification_status": "live_serp",
            }
        )

    for rec in structured:
        if str(rec.get("record_type") or "competitor").lower() != "competitor":
            continue
        _append(
            str(rec.get("name") or rec.get("company_name") or "").strip(),
            positioning=str(rec.get("positioning") or ""),
            pricing=str(rec.get("price") or rec.get("pricing") or ""),
            url=str(rec.get("source_url") or rec.get("url") or ""),
            segment=str(rec.get("segment") or "live_serp"),
        )
    for ent in entities:
        _append(
            str(ent.get("company_name") or ent.get("name") or "").strip(),
            positioning=str(ent.get("positioning") or ""),
            pricing=str(ent.get("pricing") or ""),
            url=str(ent.get("website") or ent.get("url") or ""),
            segment="serp_entity",
        )
    return rows[:15]


def _merge_competitive_benchmark(static_rows: list[dict[str, Any]], live_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Prefer live named competitors; keep static named rows; drop archetype-only filler when live exists."""
    live = list(live_rows)
    if not live:
        return [r for r in static_rows if not is_seed_vendor_name(str(r.get("name") or r.get("competitor_archetypes") or ""))]

    merged: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in live + static_rows:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        archetype = str(row.get("competitor_archetypes") or "").strip()
        label = name or archetype
        if is_seed_vendor_name(label):
            continue
        # Skip generic archetype-only rows once we have live named competitors.
        if live and not name and archetype and "," in archetype:
            continue
        key = (name or archetype).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(row)
    return merged[:15]


def _live_pricing_rows(structured: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rec in structured:
        rtype = str(rec.get("record_type") or "competitor").lower()
        if rtype not in {"competitor", "pricing"}:
            continue
        price = str(rec.get("price") or rec.get("pricing") or "").strip()
        if not price or price.lower() in {"unknown", "n/a"}:
            continue
        vendor = str(rec.get("name") or rec.get("company_name") or "competitor").strip()
        if is_seed_vendor_name(vendor):
            continue
        rows.append(
            {
                "vendor": vendor,
                "package": rec.get("product") or rec.get("plan") or "listed offer",
                "price_band": price,
                "source": rec.get("source_url") or rec.get("url") or "",
                "source_family": "serp_pricing",
                "verification_status": "live_serp",
            }
        )
    return rows[:12]


def build_live_competitor_intelligence_pack(brain_rows: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        from iidatech.evidence_bank.google_competitor_discovery import is_valid_competitor_display_name
    except ImportError:
        def is_valid_competitor_display_name(name: str) -> bool:
            return bool(name) and not is_seed_vendor_name(name)

    competitors: list[dict[str, Any]] = []
    for row in brain_rows:
        if str(row.get("record_type") or "").lower() != "competitor":
            continue
        name = str(row.get("title") or row.get("company_name") or "").strip()
        if not name or is_seed_vendor_name(name) or not is_valid_competitor_display_name(name):
            continue
        competitors.append(
            {
                "name": name,
                "official_url": row.get("url") or "",
                "pricing": row.get("metric_value") or row.get("monthly_price") or "",
                "pricing_model": "listed_price" if row.get("metric_value") else "",
                "target_customer": "",
                "positioning": (row.get("text") or "")[:240],
                "strengths": [],
                "weaknesses": [],
                "moat": "",
                "estimated_margin": "",
                "market_gap": "",
                "sources": ["serp_live_discovery"],
                "verification_status": "live_serp",
            }
        )
    if not competitors:
        return {
            "status": "validation_required",
            "verified": False,
            "competitor_count": 0,
            "competitors": [],
            "evidence_status": "insufficient_competitor_evidence",
        }
    return {
        "verified": True,
        "competitor_count": len(competitors),
        "competitors": competitors[:20],
        "evidence_status": "live_serp_discovery",
        "discovery_source": "serp_intelligence",
    }


def enrich_diligence_pack_live_competitors(
    pack: dict[str, Any],
    *,
    topic: str,
    industry: str,
    geography: str,
    domain: str | None = None,
    serp_block: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Populate diligence pack with live SERP competitors (not seed vendors)."""
    out = dict(pack)
    block = normalize_serp_block(serp_block or out.get("serp_intelligence"))
    if not (block.get("structured_records") or block.get("entities")):
        block = fetch_serp_intelligence(topic, industry, geography, domain=domain)

    if block.get("report_degraded") or not (block.get("structured_records") or block.get("entities")):
        out["report_degraded"] = True
        out["report_degrade_reason"] = (
            str(block.get("degrade_reason") or block.get("trace", {}).get("error") or "perplexity_evidence_unavailable")
        )

    domain_value = resolve_report_domain(topic, industry, geography, domain or out.get("domain"))
    out["domain"] = out.get("domain") or domain_value
    out["serp_intelligence"] = block

    structured = block.get("structured_records") or []
    entities = block.get("entities") or []

    live_names: list[str] = []
    try:
        from iidatech.evidence_bank.competitor_normalizer import filter_serp_competitors

        normalized = filter_serp_competitors(structured, entities, domain=domain_value, limit=12)
        structured = normalized["structured_records"]
        entities = normalized["entities"]
        live_names = list(normalized.get("names") or [])
        out["competitor_normalization"] = normalized.get("trace") or {}
    except Exception as exc:
        out["competitor_normalization"] = {"error": str(exc)[:200]}

    block = {**block, "structured_records": structured, "entities": entities}
    out["serp_intelligence"] = block

    live_benchmark = build_live_competitive_benchmark(structured, entities)
    out["competitive_benchmark"] = _merge_competitive_benchmark(
        _as_list(out.get("competitive_benchmark")),
        live_benchmark,
    )

    brain_rows = structured_to_brain_records(structured, entities, domain=domain_value, geography=geography)
    out["serp_brain_records"] = brain_rows
    out["citation_ledger"] = _merge_citation_ledger(_as_list(out.get("citation_ledger")), brain_rows)
    out["competitor_intelligence_pack"] = build_live_competitor_intelligence_pack(brain_rows)

    pricing_pack = dict(_as_dict(out.get("pricing_intelligence_pack")))
    live_prices = _live_pricing_rows(structured)
    market_hints = [r for r in structured if str(r.get("record_type") or "").lower() == "market_signal"]
    if market_hints:
        out["market_sizing_hints"] = market_hints[:8]

    comp_pack = _as_dict(out.get("competitor_intelligence_pack"))
    try:
        from iidatech.services.pricing_harvest import harvest_verified_pricing

        harvest = harvest_verified_pricing(
            competitors=_as_list(comp_pack.get("competitors")),
            structured=structured,
            entities=entities,
            live_competitor_names=live_names,
            topic=topic,
            domain=domain_value,
            geography=geography,
        )
        verified = list(_as_list(harvest.get("verified_rows")))
        out["pricing_harvest"] = {
            "status": harvest.get("status"),
            "verified_count": harvest.get("verified_count"),
            "pages_scraped": harvest.get("pages_scraped"),
            "trace": harvest.get("trace"),
            "rejected_count": len(_as_list(harvest.get("rejected_rows"))),
        }
        if verified:
            live_prices = verified + [r for r in live_prices if str(r.get("vendor") or "").lower() not in {
                str(v.get("vendor") or "").lower() for v in verified
            }]
            for comp in _as_list(comp_pack.get("competitors")):
                if not isinstance(comp, dict):
                    continue
                vendor = str(comp.get("name") or "").lower()
                match = next((v for v in verified if str(v.get("vendor") or "").lower() == vendor), None)
                if match and match.get("estimated_price_band"):
                    comp["pricing"] = match.get("estimated_price_band")
                    comp["pricing_model"] = comp.get("pricing_model") or "verified_page"
                    comp["verification_status"] = "verified_pricing_page"
            out["competitor_intelligence_pack"] = comp_pack
            matrix_rows = []
            for row in verified:
                matrix_rows.append(
                    {
                        "name": row.get("vendor") or row.get("name"),
                        "competitor": row.get("vendor") or row.get("name"),
                        "plan": row.get("plan_name") or row.get("package"),
                        "price": row.get("estimated_price_band") or row.get("monthly_price"),
                        "pricing": row.get("estimated_price_band") or row.get("monthly_price"),
                        "source": row.get("source_url") or row.get("url"),
                        "url": row.get("source_url") or row.get("url"),
                        "source_family": "official_pricing_page",
                        "verification_status": "verified_pricing_page",
                        "evidence_backed": True,
                    }
                )
            if matrix_rows:
                out["verified_competitor_pricing_matrix"] = matrix_rows
    except Exception as exc:
        out["pricing_harvest"] = {"status": "error", "error": str(exc)[:200]}

    try:
        from iidatech.services.pricing_bank_bridge import merge_pricing_bank_rows

        verified_n = int(_as_dict(out.get("pricing_harvest")).get("verified_count") or 0)
        pricing_pack = merge_pricing_bank_rows(
            pricing_pack,
            topic=topic,
            industry=industry,
            geography=geography,
            domain=domain_value,
            limit=12 if verified_n < 2 else 8,
        )
    except Exception as exc:
        pricing_pack.setdefault("pricing_bank_error", str(exc)[:200])

    if live_prices:
        sourced = list(_as_list(pricing_pack.get("sourced_pricing_records")))
        seen = {str(r.get("vendor") or "").lower() for r in sourced if isinstance(r, dict)}
        for row in live_prices:
            vendor = str(row.get("vendor") or "").lower()
            if vendor and vendor not in seen:
                sourced.append(row)
                seen.add(vendor)
        pricing_pack["sourced_pricing_records"] = sourced[:20]
        pricing_pack["live_serp_pricing_count"] = len(live_prices)
    out["pricing_intelligence_pack"] = pricing_pack
    out["live_competitor_count"] = len(live_names) if live_names else len(_live_competitor_names(structured, entities))
    out["live_competitor_names"] = live_names or _live_competitor_names(structured, entities)

    try:
        from iidatech.services.tam_bottom_up_harvest import harvest_bottom_up_tam

        verified_rows = list(_as_list(_as_dict(out.get("pricing_harvest")).get("verified_rows")))
        if not verified_rows:
            verified_rows = list(_as_list(out.get("verified_competitor_pricing_matrix")))
        tam_harvest = harvest_bottom_up_tam(
            topic=topic,
            industry=industry,
            geography=geography,
            domain=domain_value,
            pricing_rows=verified_rows,
            diligence_pack=out,
        )
        out["tam_harvest"] = {
            "status": "complete" if tam_harvest.get("complete") else "incomplete",
            "missing": tam_harvest.get("missing"),
            "trace": tam_harvest.get("trace"),
        }
        if tam_harvest.get("complete"):
            out["bottom_up_market_calculation"] = tam_harvest["bottom_up_market_calculation"]
    except Exception as exc:
        out["tam_harvest"] = {"status": "error", "error": str(exc)[:200]}

    try:
        from iidatech.proprietary_data.loader import query_buyer_voice

        voices = query_buyer_voice(topic, industry, geography, domain=domain_value, limit=8)
        if voices:
            out["buyer_voice_bank"] = voices
            survey = dict(_as_dict(out.get("survey_interview_findings")))
            signals = list(_as_list(survey.get("buyer_pain_signals")))
            for row in voices[:6]:
                if not isinstance(row, dict):
                    continue
                signals.append(
                    {
                        "source": row.get("source"),
                        "source_type": row.get("source_type"),
                        "pain_category": row.get("pain_category"),
                        "complaint": row.get("complaint"),
                        "willingness_to_pay_signal": row.get("willingness_to_pay_signal"),
                        "region": row.get("region"),
                        "evidence_namespace": "buyer_voice_bank",
                    }
                )
            survey["buyer_pain_signals"] = signals[:12]
            out["survey_interview_findings"] = survey
    except Exception as exc:
        out.setdefault("buyer_voice_bank_error", str(exc)[:200])

    return out


def attach_serp_intelligence_to_report(
    *,
    topic: str,
    industry: str,
    geography: str,
    diligence_pack: dict[str, Any],
    harvest_serp: dict[str, Any] | None = None,
    domain: str | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Attach serp_intelligence to diligence_pack and merge live rows for research_brain."""
    pack = dict(diligence_pack)
    if int(pack.get("live_competitor_count") or 0) > 0 and _as_list(
        _as_dict(pack.get("competitor_intelligence_pack")).get("competitors")
    ):
        return pack

    existing = normalize_serp_block(pack.get("serp_intelligence"))
    harvested = normalize_serp_block(harvest_serp)

    if force_refresh or not (existing.get("structured_records") or existing.get("entities")):
        if harvested.get("structured_records") or harvested.get("entities"):
            block = harvested
        else:
            block = fetch_serp_intelligence(topic, industry, geography, domain=domain)
    else:
        block = existing

    if block.get("report_degraded") or not (block.get("structured_records") or block.get("entities")):
        pack["report_degraded"] = True
        pack["report_degrade_reason"] = str(
            block.get("degrade_reason") or block.get("trace", {}).get("error") or "perplexity_evidence_unavailable"
        )

    domain_value = resolve_report_domain(topic, industry, geography, domain or pack.get("domain"))
    pack["domain"] = pack.get("domain") or domain_value
    pack["serp_intelligence"] = block

    brain_rows = structured_to_brain_records(
        block.get("structured_records") or [],
        block.get("entities") or [],
        domain=domain_value,
        geography=geography,
    )
    pack["serp_brain_records"] = brain_rows
    pack["citation_ledger"] = _merge_citation_ledger(_as_list(pack.get("citation_ledger")), brain_rows)
    comp_pack = _merge_competitor_pack(_as_dict(pack.get("competitor_intelligence_pack")), brain_rows)
    pack["competitor_intelligence_pack"] = comp_pack
    if not _as_list(comp_pack.get("competitors")):
        pack["competitor_intelligence_pack"] = build_live_competitor_intelligence_pack(brain_rows)
    live_benchmark = build_live_competitive_benchmark(
        block.get("structured_records") or [],
        block.get("entities") or [],
    )
    if live_benchmark:
        pack["competitive_benchmark"] = _merge_competitive_benchmark(
            _as_list(pack.get("competitive_benchmark")),
            live_benchmark,
        )
    return pack