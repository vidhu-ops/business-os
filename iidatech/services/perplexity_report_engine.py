"""Perplexity-first report builder - direct Sonar sections without legacy diligence pipeline."""
from __future__ import annotations

import hashlib
import os
import time
from datetime import datetime, timezone
from typing import Any

from iidatech.evidence_bank.gitnux_client import (
    format_gitnux_block,
    gitnux_benchmark_pack,
    gitnux_enabled,
    merge_gitnux_into_harvest,
)
from iidatech.evidence_bank.statista_client import (
    format_statista_block,
    merge_statista_into_harvest,
    statista_enabled,
    statista_harvest_pack,
)
from iidatech.evidence_bank.perplexity_client import (
    call_perplexity_json,
    fetch_web_research_harvest,
    perplexity_enabled,
    report_perplexity_model,
    report_search_model,
)
from iidatech.llm.anthropic_report import analyst_model, anthropic_enabled, call_anthropic_json, financial_model
from iidatech.llm.usage_ledger import perplexity_usage_row, project_phase_cost, sum_ledger
from iidatech.services.report_math_verify import (
    apply_math_audit,
    apply_number_gate,
    apply_pricing_footnotes,
    build_figure_ledger,
    merge_structured_ledger,
    sanitize_report_text,
    sanitize_section_commentary,
)
from iidatech.services.report_source_tier import apply_source_tier_labels, institutional_source_queries
from iidatech.storage.cache_repository import log_api_cost

# Framework extensions (Porter, SWOT, etc.) are disabled until re-enabled in product.
FRAMEWORKS_ENABLED = False

SECTION_CATALOG: list[dict[str, Any]] = [
    {"id": 1, "title": "Executive Summary", "sub": ["Key Findings", "Market Snapshot", "Investment Highlights", "Report Scope"]},
    {"id": 2, "title": "Market Overview & Definition", "sub": ["Market Definition", "Scope & Coverage", "Key Assumptions", "Currency & Units"]},
    {"id": 3, "title": "Market Size & Valuation", "sub": ["Current Market Value", "TAM / SAM / SOM", "Revenue by Segment", "Value Chain"]},
    {"id": 4, "title": "Historical Market Data", "sub": ["5-Year Revenue Trend", "Volume Growth", "Price Evolution", "Market Inflection Points"]},
    {"id": 5, "title": "Market Segmentation", "sub": ["By Product Type", "By Application", "By End-User Industry", "By Business Model"]},
    {"id": 6, "title": "Regional Analysis", "sub": ["Geographic Breakdown", "Country Priorities", "Local Dynamics", "Expansion Notes"]},
    {"id": 7, "title": "Competitive Landscape", "sub": ["Market Concentration", "Competitive Intensity", "Strategic Groups", "Barriers to Entry"]},
    {"id": 8, "title": "Key Player Profiles", "sub": ["Top Companies", "Product Portfolios", "Financial Highlights", "Recent Developments"]},
    {"id": 9, "title": "Market Share Analysis", "sub": ["Revenue Share", "Volume Share", "Geographic Share", "Segment Share"]},
    {"id": 10, "title": "Growth Drivers", "sub": ["Demand-Side Drivers", "Supply-Side Enablers", "Technology Catalysts", "Policy Tailwinds"]},
    {"id": 11, "title": "Restraints & Challenges", "sub": ["Key Bottlenecks", "Cost Pressures", "Regulatory Hurdles", "Talent Gaps"]},
    {"id": 12, "title": "Opportunities & White Spaces", "sub": ["Untapped Segments", "Emerging Geographies", "Innovation Gaps", "Partnership Opportunities"]},
    {"id": 13, "title": "Market Trends", "sub": ["Technology Trends", "Consumer Behavior", "Business Model Innovation", "Sustainability"]},
    {"id": 14, "title": "Technology Landscape", "sub": ["Core Technologies", "Emerging Tech", "IP Activity", "R&D Spend"]},
    {"id": 15, "title": "Regulatory Environment", "sub": ["Global Framework", "Regional Compliance", "Upcoming Legislation", "Compliance Cost"]},
    {"id": 16, "title": "Supply Chain Analysis", "sub": ["Upstream Suppliers", "Manufacturing", "Distribution", "Last-Mile"]},
    {"id": 17, "title": "Pricing Analysis", "sub": ["Pricing Models", "Price Benchmarking", "Price Sensitivity", "Margin Structure"]},
    {"id": 18, "title": "Consumer Behavior", "sub": ["Buyer Personas", "Purchase Journey", "Decision Criteria", "Switching Costs"]},
    {"id": 19, "title": "Investment & Funding Activity", "sub": ["VC & PE Flows", "Notable Deals", "Valuation Multiples", "Investor Sentiment"]},
    {"id": 20, "title": "M&A Activity", "sub": ["Deal Volume", "Strategic Rationale", "Cross-Border Deals", "Integration"]},
    {"id": 21, "title": "Market Forecast (2026-2031)", "sub": ["Revenue Projections", "CAGR by Segment", "Scenarios", "Assumptions"]},
    {"id": 22, "title": "Strategic Recommendations", "sub": ["For Incumbents", "For New Entrants", "For Investors", "Quick-Win Playbook"]},
    {"id": 23, "title": "Appendix & Methodology", "sub": ["Research Methodology", "Data Sources", "Glossary", "Limitations"]},
    {"id": 24, "title": "Founder Build Plan", "sub": ["Business Concept", "MVP Scope", "Build Steps", "Validation Milestones"]},
    {"id": 25, "title": "Operating Model & Hiring Plan", "sub": ["Org Chart", "Who to Hire", "Role Costs", "Operating Cadence"]},
    {"id": 26, "title": "Porter Five Forces", "sub": ["Rivalry", "Supplier power", "Buyer power", "Substitutes", "New entrants", "Implications"]},
    {"id": 27, "title": "SWOT Analysis", "sub": ["Strengths", "Weaknesses", "Opportunities", "Threats", "Strategic implications"]},
    {"id": 28, "title": "Value Chain Mapping", "sub": ["Upstream", "Core activities", "Downstream", "Margin pools", "Bottlenecks"]},
    {"id": 29, "title": "AI Disruption Analysis", "sub": ["Automation risk", "AI-native entrants", "Incumbent response", "Timeline", "So what"]},
    {"id": 30, "title": "Emerging Startups", "sub": ["Notable startups", "Funding stage", "Differentiation", "Threat level"]},
    {"id": 31, "title": "VC Funding History", "sub": ["Round volume", "Notable deals", "Valuation trends", "Investor themes"]},
    {"id": 32, "title": "Acquisition Landscape", "sub": ["Recent M&A", "Acquirers", "Rationale", "Integration patterns"]},
    {"id": 33, "title": "Patent Activity", "sub": ["Key filers", "Technology themes", "IP moats", "Freedom to operate"]},
    {"id": 34, "title": "Hiring Trends", "sub": ["In-demand roles", "Geo hiring", "Salary signals", "Talent bottlenecks"]},
    {"id": 35, "title": "GitHub Activity", "sub": ["Open-source projects", "Contributor trends", "Tech stack signals"]},
    {"id": 36, "title": "Product Roadmap Analysis", "sub": ["Public roadmaps", "Release cadence", "Feature gaps vs leaders"]},
    {"id": 37, "title": "Customer Segmentation", "sub": ["Segments", "Needs", "Willingness to pay", "Reachability"]},
    {"id": 38, "title": "Regional Opportunity Heatmap", "sub": ["Priority regions", "Demand signals", "Competitive density", "Go-to-market fit"]},
    {"id": 39, "title": "Pricing Waterfall", "sub": ["List price", "Discounts", "Packaging", "Net realized price", "Competitive price bands"]},
    {"id": 40, "title": "Unit Economics", "sub": ["Revenue per account", "Gross margin", "Payback", "Contribution margin"]},
    {"id": 41, "title": "Customer Acquisition Cost (CAC)", "sub": ["Channel CAC", "Blended CAC", "Benchmarks", "Trend"]},
    {"id": 42, "title": "LTV & Retention Economics", "sub": ["LTV", "LTV:CAC", "Retention curves", "Expansion revenue"]},
    {"id": 43, "title": "Churn Benchmarks", "sub": ["Logo churn", "Revenue churn", "Cohort behavior", "Industry benchmarks"]},
    {"id": 44, "title": "Adoption Funnel", "sub": ["Awareness", "Trial", "Activation", "Paid conversion", "Drop-off drivers"]},
    {"id": 45, "title": "Industry Lifecycle", "sub": ["Stage", "Growth rate", "Consolidation", "Innovation cycle"]},
    {"id": 46, "title": "Scenario Forecasts & Monte Carlo", "sub": ["Variables", "Distribution assumptions", "Simulation outcomes", "Confidence bands"]},
    {"id": 47, "title": "Bull / Base / Bear Cases", "sub": ["Bull case", "Base case", "Bear case", "Trigger events", "Implied TAM/SAM"]},
    {"id": 48, "title": "TAM Estimation Models", "sub": ["Top-down", "Bottom-up", "Reconciliation", "Sensitivity"]},
    {"id": 49, "title": "Primary Interviews & Voice of Customer", "sub": ["Interview themes", "Buyer quotes", "Jobs-to-be-done", "Unmet needs"]},
    {"id": 50, "title": "Regulatory Outlook", "sub": ["Current rules", "Pending legislation", "Compliance cost", "Market access impact"]},
    {"id": 51, "title": "Technology Maturity", "sub": ["Maturity curve", "Adoption S-curve", "Standards", "Integration complexity"]},
    {"id": 52, "title": "Investment Scorecard", "sub": ["Market attractiveness", "Competitive moat", "Execution risk", "Overall score rationale"]},
    {"id": 53, "title": "Insights, Decisions & Strategic Implications", "sub": ["Top insights", "Decisions for founders", "Decisions for investors", "90-day priorities"]},
    {"id": 54, "title": "What Buyers Complain About", "sub": ["Top pain themes", "SMB/ICP complaints", "Support issues", "Pricing friction"]},
    {"id": 55, "title": "Buying Journey", "sub": ["Discovery", "Evaluation", "Proof", "Procurement", "Time-to-decision"]},
    {"id": 56, "title": "Why Implementations Fail", "sub": ["Root causes", "Change management", "Integration failures", "Adoption gaps"]},
    {"id": 57, "title": "Switching Costs", "sub": ["Data migration", "Workflow lock-in", "Training", "Contract exit"]},
    {"id": 58, "title": "What Makes Customers Churn", "sub": ["Churn triggers", "Early warning signals", "Save plays", "Benchmarks"]},
    {"id": 59, "title": "Reddit & Community Discussions", "sub": ["Subreddits", "Recurring threads", "Sentiment", "Feature debates"]},
    {"id": 60, "title": "G2 & Review Platform Analysis", "sub": ["Ratings", "Pros/cons themes", "Review velocity", "Competitive comparison"]},
    {"id": 61, "title": "Feature Requests & Unmet Needs", "sub": ["Top requests", "Missing capabilities", "Workarounds", "Product opportunities"]},
    {"id": 62, "title": "Financial Data Table", "sub": ["Sourced market figures", "Unit economics", "Pricing benchmarks", "Derived calculations", "Labeled estimates", "Not found"]},
]

SECTION_PRESETS: dict[int, list[int]] = {
    3: [1, 3, 7],
    6: [1, 2, 3, 7, 17, 22],
    16: list(range(1, 17)),
    25: list(range(1, 26)),
}

MARKET_READY_EXTENSION_IDS: list[int] = list(range(26, 62))

FINANCIAL_TABLE_SECTION_ID = 62

# Claude Opus owns all figures in these sections; Sonar must not draft them.
FINANCIAL_SECTION_IDS = frozenset({3, 4, 9, 17, 19, 21, 39, 40, 41, 42, 43, 46, 47, 48, 62})

# Claude Sonnet owns competitor evidence in these sections.
COMPETITOR_SECTION_IDS = frozenset({7, 8, 60})

_LABELING_LEGEND = (
    "**Label key:** `[FACT]` verified from tier-1/2 source (gov stats, filings, Tracxn/Crunchbase) · "
    "`[DERIVED]` calculated step-by-step from facts · `[ESTIMATE]` modeled or blog-sourced · "
    "`[SECONDARY]` aggregator or marketing content · `[ASSUMPTION]` input you must validate · "
    "`[OPINION]` analyst judgment · `[PRIMARY]` direct filing/survey/interview · "
    "`[NOT FOUND]` no reliable data"
)

_COMPETITOR_MIN_NAMED = 3
_COMPETITOR_COVERAGE_WARNING = (
    "> **⚠️ Search coverage warning:** Fewer than 3 named competitors were verified from search results. "
    "This usually means **incomplete retrieval**, not a true market gap. Treat any 'zero competitors' "
    "claim as unverified until you cross-check Tracxn, Crunchbase, or category leaders manually."
)


def _report_debug_mode() -> bool:
    return os.getenv("IIDATECH_REPORT_DEBUG", "").strip().lower() in ("1", "true", "yes")

_BATCH_SIZE = 7


def format_market_geography(geography: str, areas: str = "") -> str:
    """Combine country/market with optional city or metro focus for prompts and headers."""
    geo = str(geography or "Global").strip() or "Global"
    areas_s = str(areas or "").strip()
    if areas_s:
        return f"{geo} — {areas_s}"
    return geo


def section_plan(section_count: int, *, include_extensions: bool = False) -> list[dict[str, Any]]:
    count = int(section_count)
    if count not in SECTION_PRESETS:
        raise ValueError(f"section_count must be one of {sorted(SECTION_PRESETS)}")
    by_id = {row["id"]: row for row in SECTION_CATALOG}
    base_ids = list(SECTION_PRESETS[count])
    all_ids = list(base_ids)
    if include_extensions and FRAMEWORKS_ENABLED:
        seen = set(all_ids)
        all_ids.extend(sid for sid in MARKET_READY_EXTENSION_IDS if sid not in seen)
    return [by_id[sid] for sid in all_ids if sid in by_id]


def build_report_plan(
    section_count: int,
    *,
    include_extensions: bool = False,
    include_financial_table: bool = True,
) -> list[dict[str, Any]]:
    """Core preset + optional financial table + optional framework extensions."""
    by_id = {row["id"]: row for row in SECTION_CATALOG}
    base_ids = list(SECTION_PRESETS[int(section_count)])
    ids = list(base_ids)
    if include_financial_table and FINANCIAL_TABLE_SECTION_ID not in ids:
        if 3 in ids:
            ids.insert(ids.index(3) + 1, FINANCIAL_TABLE_SECTION_ID)
        else:
            ids.append(FINANCIAL_TABLE_SECTION_ID)
    if include_extensions and FRAMEWORKS_ENABLED:
        seen = set(ids)
        ids.extend(sid for sid in MARKET_READY_EXTENSION_IDS if sid not in seen)
    return [by_id[sid] for sid in ids if sid in by_id]


def batchable_sections(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Narrative-only sections for Sonar (excludes Claude financial + competitor passes)."""
    return narrative_sections(plan)


def narrative_sections(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in plan:
        sid = int(row.get("id") or 0)
        if sid in FINANCIAL_SECTION_IDS or sid in COMPETITOR_SECTION_IDS:
            continue
        out.append(row)
    return out


def financial_sections_in_plan(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in plan if int(row.get("id") or 0) in FINANCIAL_SECTION_IDS]


def competitor_sections_in_plan(plan: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in plan if int(row.get("id") or 0) in COMPETITOR_SECTION_IDS]


def extension_section_count() -> int:
    return len(MARKET_READY_EXTENSION_IDS)


def _batch_sections(sections: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    if len(sections) <= _BATCH_SIZE:
        return [sections]
    return [sections[i : i + _BATCH_SIZE] for i in range(0, len(sections), _BATCH_SIZE)]


def _section_prompt(
    topic: str,
    industry: str,
    geography: str,
    batch: list[dict[str, Any]],
    fact_pack: str = "",
) -> str:
    lines = []
    for row in batch:
        subs = ", ".join(str(s) for s in (row.get("sub") or [])[:8])
        lines.append(f'- id={row["id"]} title="{row["title"]}" cover: {subs}')
    section_list = "\n".join(lines)
    fact_block = ""
    if fact_pack.strip():
        fact_block = (
            "\nVERIFIED FINANCIAL LEDGER (reference by metric name only — do NOT repeat dollar amounts, "
            "percentages, CAGR, or market sizes in your prose):\n"
            f"{fact_pack[:12000]}\n"
        )
    year = datetime.now(timezone.utc).year

    return (
        "You are a senior market intelligence analyst writing QUALITATIVE narrative sections only. "
        "A separate Claude financial pass already owns all numbers — you must not invent any.\n\n"
        "ASSIGNMENT (stay inside this frame — reject adjacent markets)\n\n"
        f"- Topic niche (ONLY research this): {topic}\n"
        f"- Industry context: {industry}\n"
        f"- Geography / market: {geography}\n"
        f"- Reporting year: {year}\n"
        f"{fact_block}\n"
        "TOPIC LOCK\n"
        f"- Every paragraph must directly help someone evaluating **{topic}** in **{geography}**.\n"
        "- If a company, statistic, or trend is not about this exact topic, DELETE it.\n"
        "- Name the topic in the opening sentence of each section.\n\n"
        "NO NUMBERS RULE (mandatory)\n"
        "- Do NOT include dollar amounts, rupee amounts, percentages, CAGR, market size, pricing, "
        "funding totals, headcount figures, or any numeric market claim.\n"
        "- Describe trends qualitatively (e.g. 'pricing pressure is rising' not '$49/seat').\n"
        "- If a metric is essential, write: 'see Financial Data Table (section 62)' — do not state the value.\n"
        "- key_metrics must be an empty object {} for every section.\n\n"
        "OUTPUT — STRICT JSON only (no markdown fences):\n"
        "{\n"
        '  "sections": [\n'
        "    {\n"
        '      "id": 1,\n'
        '      "title": "section title",\n'
        '      "body_markdown": "Qualitative markdown only — no digits used as market/financial claims.",\n'
        '      "key_insights": [],\n'
        '      "key_metrics": {},\n'
        '      "sources": ["https://..."]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "SECTION RULES\n"
        "1. Leave key_insights as an empty array — analyst commentary is added later.\n"
        "2. Search live web for qualitative signals: regulation, buyer behavior, product trends, competitive dynamics.\n"
        "3. Do not invent company names without a real URL in sources.\n"
        "4. Cover ALL subsections listed for each section id.\n"
        "5. We render your JSON verbatim — do not reference internal systems.\n\n"
        "Write these sections only:\n"
        f"{section_list}\n"
    )


def _search_harvest_prompt(topic: str, industry: str, geography: str) -> str:
    year = datetime.now(timezone.utc).year
    return (
        f"You are a financial and competitive intelligence researcher. Search the live web for "
        f"**{topic}** in **{geography}** ({industry}). Reporting year: {year}.\n\n"
        "Find ONLY facts you can tie to a real URL from your search results.\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "financial_facts": [\n'
        '    {"metric": "TAM", "value": "$X or range", "source_url": "https://...", "year": "2025", "publisher": ""}\n'
        "  ],\n"
        '  "competitor_facts": [\n'
        '    {"name": "Company", "pricing": "$X/mo or tier summary", "positioning": "", "source_url": "https://...", "notes": ""}\n'
        "  ],\n"
        '  "pricing_facts": [\n'
        '    {"tier": "Pro", "price": "$X/mo", "source_url": "https://...", "notes": ""}\n'
        "  ],\n"
        '  "search_notes": ""\n'
        "}\n\n"
        "RULES: Minimum 8 financial_facts and 5 competitor_facts where data exists. "
        "Prefer primary sources: government statistics (MOSPI, RBI, DPIIT), NASSCOM, Tracxn, Crunchbase, "
        "SEC filings, and named industry databases. Deprioritize Coursera, YouTube, glossaries, and SEO blogs. "
        "Use [NOT FOUND] only when search truly has no data — never guess. "
        "Every row needs source_url starting with https://.\n"
    )


def _institutional_harvest_prompt(topic: str, industry: str, geography: str) -> str:
    year = datetime.now(timezone.utc).year
    queries = institutional_source_queries(geography)
    query_block = "\n".join(f"- {q}" for q in queries)
    return (
        f"Institutional source pass for **{topic}** in **{geography}** ({industry}). Year: {year}.\n\n"
        "Run targeted searches using these queries (prioritize tier-1/2 URLs only):\n"
        f"{query_block}\n\n"
        "Return STRICT JSON only (same shape as general harvest):\n"
        "{\n"
        '  "financial_facts": [\n'
        '    {"metric": "MSME count", "value": "...", "source_url": "https://msme.gov.in/...", '
        '"year": "2024", "publisher": "MSME Ministry"}\n'
        "  ],\n"
        '  "competitor_facts": [],\n'
        '  "pricing_facts": [],\n'
        '  "search_notes": ""\n'
        "}\n\n"
        "RULES: source_url MUST be government (.gov.in), NASSCOM, MOSPI, RBI, DPIIT, Tracxn, or Crunchbase. "
        "Reject blogs, glossaries, YouTube, and vendor marketing pages entirely.\n"
    )


def _merge_harvest_dicts(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    """Merge institutional facts ahead of general web harvest."""
    import json as _json

    out: dict[str, Any] = dict(secondary or {})
    for key in ("financial_facts", "competitor_facts", "pricing_facts"):
        pri_rows = [r for r in (primary.get(key) or []) if isinstance(r, dict)]
        sec_rows = [r for r in (out.get(key) or []) if isinstance(r, dict)]
        seen: set[str] = set()
        merged: list[dict[str, Any]] = []
        for row in pri_rows + sec_rows:
            sig = _json.dumps(row, sort_keys=True, default=str)
            if sig in seen:
                continue
            seen.add(sig)
            merged.append(row)
        out[key] = merged
    notes = [str(primary.get("search_notes") or "").strip(), str(secondary.get("search_notes") or "").strip()]
    out["search_notes"] = " | ".join(n for n in notes if n)
    return out


def _format_harvest_block(harvest: dict[str, Any], citations: list[str]) -> str:
    lines = ["WEB SEARCH RESULTS (use ONLY these facts — do not invent beyond them):", ""]
    for key in ("financial_facts", "competitor_facts", "pricing_facts"):
        rows = harvest.get(key) if isinstance(harvest.get(key), list) else []
        if not rows:
            continue
        lines.append(f"{key.upper()}:")
        for row in rows[:25]:
            if isinstance(row, dict):
                lines.append(f"- {row}")
        lines.append("")
    if citations:
        lines.append("CITATIONS FROM SEARCH:")
        for url in citations[:20]:
            lines.append(f"- {url}")
    notes = str(harvest.get("search_notes") or "").strip()
    if notes:
        lines.append(f"NOTES: {notes}")
    return "\n".join(lines).strip()


def _fetch_search_harvest(
    topic: str,
    industry: str,
    geography: str,
    *,
    report_id: str = "",
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    """Sonar-pro live search harvest — feeds Claude financial + competitor passes."""
    model = report_search_model()
    prompt = _search_harvest_prompt(topic, industry, geography)
    trace: dict[str, Any] = {
        "errors": [],
        "phase": "sonar_search_harvest",
        "model": model,
        "provider": "perplexity",
        "section_ids": [],
    }
    api = fetch_web_research_harvest(prompt, timeout=200)
    trace["usage"] = api.get("usage") or {}
    ledger_row = perplexity_usage_row(api.get("usage"), model=str(api.get("model") or model), phase="sonar_search_harvest")
    trace["usage_ledger"] = ledger_row
    if report_id:
        _ledger_log(report_id, ledger_row)
    if api.get("error"):
        trace["errors"].append(str(api["error"]))
        return {}, [], trace
    parsed = api.get("parsed") if isinstance(api.get("parsed"), dict) else {}
    citations = [str(u).strip() for u in (api.get("citations") or []) if str(u).strip().startswith("http")]
    if not parsed and api.get("raw_content"):
        trace["errors"].append("search_harvest_parse_failed")
        trace["raw_preview"] = str(api.get("raw_content") or "")[:800]
    return parsed, citations, trace


def _fetch_institutional_harvest(
    topic: str,
    industry: str,
    geography: str,
    *,
    report_id: str = "",
) -> tuple[dict[str, Any], list[str], dict[str, Any]]:
    """Second Sonar pass biased to gov / database sources."""
    model = report_search_model()
    prompt = _institutional_harvest_prompt(topic, industry, geography)
    trace: dict[str, Any] = {
        "errors": [],
        "phase": "sonar_institutional_harvest",
        "model": model,
        "provider": "perplexity",
        "section_ids": [],
    }
    api = fetch_web_research_harvest(prompt, timeout=150)
    trace["usage"] = api.get("usage") or {}
    ledger_row = perplexity_usage_row(
        api.get("usage"), model=str(api.get("model") or model), phase="sonar_institutional_harvest"
    )
    trace["usage_ledger"] = ledger_row
    if report_id:
        _ledger_log(report_id, ledger_row)
    if api.get("error"):
        trace["errors"].append(str(api["error"]))
        return {}, [], trace
    parsed = api.get("parsed") if isinstance(api.get("parsed"), dict) else {}
    citations = [str(u).strip() for u in (api.get("citations") or []) if str(u).strip().startswith("http")]
    if not parsed and api.get("raw_content"):
        trace["errors"].append("institutional_harvest_parse_failed")
    return parsed, citations, trace


def _financial_package_prompt(
    topic: str,
    industry: str,
    geography: str,
    *,
    section_rows: list[dict[str, Any]],
    harvest_block: str = "",
) -> str:
    year = datetime.now(timezone.utc).year
    section_lines = []
    for row in section_rows:
        subs = ", ".join(str(s) for s in (row.get("sub") or [])[:6])
        section_lines.append(f'- id={row["id"]} title="{row["title"]}" — cover: {subs}')
    section_list = "\n".join(section_lines)
    harvest_section = f"\n{harvest_block[:14000]}\n" if harvest_block.strip() else ""
    return (
        f"You are a financial research analyst (Claude Opus). Build ALL financial figures for this report.\n\n"
        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\nYear: {year}\n"
        f"{harvest_section}\n"
        "Use ONLY facts from WEB SEARCH RESULTS above. Every figure needs a source_url from that list. "
        "If a metric is missing from search, use label [NOT FOUND] — never invent.\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "financial_ledger": [\n'
        '    {"metric": "TAM", "value": "$X", "label": "FACT|DERIVED|ESTIMATE|NOT FOUND", '
        '"source_url": "https://...", "year": "2025", "notes": ""}\n'
        "  ],\n"
        '  "sections": [\n'
        "    {\n"
        f'      "id": {FINANCIAL_TABLE_SECTION_ID},\n'
        '      "title": "Financial Data Table",\n'
        '      "body_markdown": "Markdown table: Metric | Value | Label | Source/Assumptions | Year | Notes",\n'
        '      "what_this_means": ["2-4 bullets on what figures mean for founders/investors"],\n'
        '      "how_to_use": ["2-4 actionable bullets"],\n'
        '      "key_metrics": {},\n'
        '      "sources": ["https://..."]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "1. Include section 62 (Financial Data Table) plus every financial section id listed below.\n"
        "2. Every Value must have Label + source_url (or [NOT FOUND]).\n"
        "3. Use [FACT] only when source_url is government, official statistics, or a named database "
        "(NASSCOM, RBI, MOSPI, Tracxn, Crunchbase, SEC). Blogs, courses, YouTube, SEO pages = [SECONDARY].\n"
        "4. [DERIVED] rows must show formula in Notes.\n"
        "5. Add what_this_means and how_to_use for each section (financial commentary).\n"
        "6. Minimum 12 rows in section 62 where data exists.\n\n"
        f"Write these financial sections:\n{section_list}\n"
    )


def _competitor_landscape_prompt(
    topic: str,
    industry: str,
    geography: str,
    *,
    section_rows: list[dict[str, Any]],
    harvest_block: str = "",
) -> str:
    section_lines = []
    for row in section_rows:
        subs = ", ".join(str(s) for s in (row.get("sub") or [])[:6])
        section_lines.append(f'- id={row["id"]} title="{row["title"]}" — cover: {subs}')
    section_list = "\n".join(section_lines)
    harvest_section = f"\n{harvest_block[:14000]}\n" if harvest_block.strip() else ""
    return (
        f"You are a competitive intelligence analyst (Claude Sonnet). Build competitor sections from search evidence.\n\n"
        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\n"
        f"{harvest_section}\n"
        "Use ONLY competitor_facts and pricing_facts from WEB SEARCH RESULTS. "
        "Every named competitor needs a source_url. Do not invent companies.\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "competitor_matrix": [\n'
        '    {"name": "Company", "pricing": "$X/mo", "positioning": "", "source_url": "https://...", "evidence_backed": true}\n'
        "  ],\n"
        '  "sections": [\n'
        "    {\n"
        '      "id": 7,\n'
        '      "title": "Competitive Landscape",\n'
        '      "body_markdown": "Markdown with named competitors and qualitative positioning — cite pricing from matrix.",\n'
        '      "key_metrics": {"company_name": "[FACT] pricing summary with source"},\n'
        '      "sources": ["https://..."]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "RULES:\n"
        "1. Minimum 3 named competitors with URLs where they exist in search results.\n"
        "2. If harvest has fewer than 3 competitor_facts, say search coverage was incomplete — do not claim a market gap.\n"
        "3. key_metrics keys should be competitor names; values are pricing/positioning with [FACT] only for tier-1/2 URLs, else [SECONDARY].\n"
        "4. Never use a vendor's own blog as the sole source for that vendor — label [SECONDARY] and cross-check.\n"
        "5. Cover every section id listed below.\n\n"
        f"Write these competitor sections:\n{section_list}\n"
    )


def _normalize_section_row(row: dict[str, Any], *, citations: list[str] | None = None) -> dict[str, Any]:
    sources = [str(u).strip() for u in (row.get("sources") or []) if str(u).strip()]
    for url in citations or []:
        if url not in sources:
            sources.append(url)
    return {
        "id": int(row.get("id") or 0),
        "title": str(row.get("title") or "").strip(),
        "body_markdown": str(row.get("body_markdown") or row.get("content") or "").strip(),
        "key_insights": [],
        "what_this_means": [str(x).strip() for x in (row.get("what_this_means") or []) if str(x).strip()],
        "how_to_use": [str(x).strip() for x in (row.get("how_to_use") or []) if str(x).strip()],
        "key_metrics": row.get("key_metrics") if isinstance(row.get("key_metrics"), dict) else {},
        "sources": sources,
    }


def _format_financial_context(ledger: dict[str, Any], financial_sections: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    entries = ledger.get("allowed_tokens") or []
    if entries:
        lines.append("Allowed figure tokens (from verified financial pass):")
        for token in entries[:40]:
            lines.append(f"- {token}")
    for sec in financial_sections:
        sid = sec.get("id")
        title = sec.get("title")
        excerpt = str(sec.get("body_markdown") or "")[:1500]
        if excerpt:
            lines.append(f"\n### Section {sid}: {title}\n{excerpt}")
    return "\n".join(lines).strip()


def _fetch_batch(
    topic: str,
    industry: str,
    geography: str,
    batch: list[dict[str, Any]],
    fact_pack: str = "",
    *,
    report_id: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prompt = _section_prompt(topic, industry, geography, batch, fact_pack=fact_pack)
    model = report_perplexity_model()
    api = call_perplexity_json(prompt, timeout=200, search_domain_filter=None, model=model)
    citations = [str(u).strip() for u in (api.get("citations") or []) if str(u).strip().startswith("http")]
    trace: dict[str, Any] = {
        "usage": api.get("usage") or {},
        "model": api.get("model") or model,
        "errors": [],
        "section_ids": [row["id"] for row in batch],
        "provider": "perplexity",
        "phase": "perplexity_narrative_draft",
    }
    ledger_row = perplexity_usage_row(
        api.get("usage"), model=str(trace["model"]), phase="perplexity_narrative_draft"
    )
    trace["usage_ledger"] = ledger_row
    if report_id:
        _ledger_log(report_id, ledger_row)
    if api.get("error"):
        trace["errors"].append(str(api["error"]))
        return [], trace
    parsed = api.get("parsed") if isinstance(api.get("parsed"), dict) else {}
    rows = parsed.get("sections") if isinstance(parsed.get("sections"), list) else []

    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = int(row.get("id") or 0)
        if not sid:
            continue
        normalized = _normalize_section_row(row, citations=citations)
        normalized["key_metrics"] = {}
        out.append(normalized)
    if not out and api.get("raw_content"):
        trace["errors"].append("perplexity_json_parse_failed")
        trace["raw_preview"] = str(api.get("raw_content") or "")[:800]
    return out, trace


def _report_id(topic: str, geography: str) -> str:
    return f"px_{hashlib.sha256(f'{topic}|{geography}'.lower().encode()).hexdigest()[:12]}"


def _ledger_log(report_id: str, row: dict[str, Any]) -> None:
    try:
        log_api_cost(
            report_id,
            str(row.get("provider") or ""),
            str(row.get("model") or ""),
            int(row.get("input_tokens") or 0),
            int(row.get("output_tokens") or 0),
            float(row.get("cost_usd") or 0.0),
        )
    except Exception:
        pass


def _fetch_financial_package(
    topic: str,
    industry: str,
    geography: str,
    *,
    section_rows: list[dict[str, Any]],
    harvest_block: str = "",
    harvest_citations: list[str] | None = None,
    report_id: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """Financial figures + commentary — Claude Opus, grounded on Sonar search harvest."""
    model = financial_model()
    prompt = _financial_package_prompt(
        topic, industry, geography, section_rows=section_rows, harvest_block=harvest_block
    )
    trace: dict[str, Any] = {
        "errors": [],
        "section_ids": [int(r.get("id") or 0) for r in section_rows],
        "phase": "opus_financial_figures",
        "model": model,
        "provider": "perplexity",
    }
    if not section_rows:
        return [], {}, trace
    if not anthropic_enabled():
        trace["errors"].append("PERPLEXITY_API_KEY not configured for financial pass")
        return [], {}, trace
    api = call_anthropic_json(prompt=prompt, model=model, max_tokens=6000, timeout=240)
    trace["usage"] = api.get("usage") or {}
    ledger_row = perplexity_usage_row(api.get("usage"), model=str(api.get("model") or model), phase="opus_financial_figures")
    trace["usage_ledger"] = ledger_row
    if report_id:
        _ledger_log(report_id, ledger_row)
    if api.get("error"):
        trace["errors"].append(str(api["error"]))
        ledger_row["error"] = str(api["error"])
        return [], {}, trace
    parsed = api.get("parsed") if isinstance(api.get("parsed"), dict) else {}
    financial_ledger = parsed.get("financial_ledger") if isinstance(parsed.get("financial_ledger"), list) else []
    rows = parsed.get("sections") if isinstance(parsed.get("sections"), list) else []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = int(row.get("id") or 0)
        if not sid:
            continue
        normalized = _normalize_section_row(row, citations=harvest_citations)
        normalized["key_insights"] = list(normalized.get("what_this_means") or [])
        out.append(normalized)
    if not out and api.get("raw_content"):
        trace["errors"].append("opus_financial_package_parse_failed")
        trace["raw_preview"] = str(api.get("raw_content") or "")[:800]
    ledger_meta = {
        "financial_ledger": financial_ledger,
        "opus_structured": bool(out),
    }
    return out, ledger_meta, trace


def _fetch_competitor_landscape(
    topic: str,
    industry: str,
    geography: str,
    *,
    section_rows: list[dict[str, Any]],
    harvest_block: str = "",
    harvest_citations: list[str] | None = None,
    report_id: str = "",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Competitor sections — Claude Sonnet, grounded on Sonar search harvest."""
    model = analyst_model()
    prompt = _competitor_landscape_prompt(
        topic, industry, geography, section_rows=section_rows, harvest_block=harvest_block
    )
    trace: dict[str, Any] = {
        "errors": [],
        "section_ids": [int(r.get("id") or 0) for r in section_rows],
        "phase": "sonnet_competitor_landscape",
        "model": model,
        "provider": "perplexity",
    }
    if not section_rows:
        return [], [], trace
    if not anthropic_enabled():
        trace["errors"].append("PERPLEXITY_API_KEY not configured for competitor pass")
        return [], [], trace
    api = call_anthropic_json(prompt=prompt, model=model, max_tokens=5000, timeout=240)
    trace["usage"] = api.get("usage") or {}
    ledger_row = perplexity_usage_row(
        api.get("usage"), model=str(api.get("model") or model), phase="sonnet_competitor_landscape"
    )
    trace["usage_ledger"] = ledger_row
    if report_id:
        _ledger_log(report_id, ledger_row)
    if api.get("error"):
        trace["errors"].append(str(api["error"]))
        ledger_row["error"] = str(api["error"])
        return [], [], trace
    parsed = api.get("parsed") if isinstance(api.get("parsed"), dict) else {}
    matrix = parsed.get("competitor_matrix") if isinstance(parsed.get("competitor_matrix"), list) else []
    rows = parsed.get("sections") if isinstance(parsed.get("sections"), list) else []
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        sid = int(row.get("id") or 0)
        if not sid:
            continue
        out.append(_normalize_section_row(row, citations=harvest_citations))
    if not out and api.get("raw_content"):
        trace["errors"].append("sonnet_competitor_parse_failed")
        trace["raw_preview"] = str(api.get("raw_content") or "")[:800]
    return out, matrix, trace


def _apply_competitor_coverage_warning(
    sections: list[dict[str, Any]],
    competitor_matrix: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Flag thin competitor retrieval instead of implying a market gap."""
    named = [
        row
        for row in (competitor_matrix or [])
        if isinstance(row, dict) and str(row.get("name") or "").strip()
    ]
    if len(named) >= _COMPETITOR_MIN_NAMED:
        return sections
    out: list[dict[str, Any]] = []
    for sec in sections:
        row = dict(sec)
        sid = int(row.get("id") or 0)
        if sid in COMPETITOR_SECTION_IDS:
            body = str(row.get("body_markdown") or "").strip()
            if _COMPETITOR_COVERAGE_WARNING not in body:
                row["body_markdown"] = f"{_COMPETITOR_COVERAGE_WARNING}\n\n{body}".strip()
            row["search_coverage_incomplete"] = True
        out.append(row)
    return out


def _analyst_commentary_prompt(
    topic: str,
    industry: str,
    geography: str,
    sections: list[dict[str, Any]],
) -> str:
    blocks = []
    for row in sections:
        sid = int(row.get("id") or 0)
        title = str(row.get("title") or "")
        body = str(row.get("body_markdown") or "")[:6000]
        blocks.append(f"### Section {sid}: {title}\n{body}\n")
    joined = "\n".join(blocks)
    return (
        "You are a senior strategy analyst. Read the research sections below (already drafted). "
        "Do NOT rewrite the research body. Add ONLY analyst commentary per section.\n\n"
        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "sections": [\n'
        "    {\n"
        '      "id": 1,\n'
        '      "what_this_means": ["2-4 bullets: what the data means for a founder/investor"],\n'
        '      "how_to_use": ["2-4 bullets: concrete actions — who to call, what to test, what to avoid"]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "RULES: One entry per section id below. No new facts or numbers — interpret what is already written.\n"
        "Use plain text bullets only — NO LaTeX, NO $...$ math, NO markdown tables in bullets.\n\n"
        f"{joined}"
    )


def _apply_analyst_commentary(
    sections: list[dict[str, Any]],
    topic: str,
    industry: str,
    geography: str,
    *,
    report_id: str = "",
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Analyst review pass — Claude Sonnet via Perplexity Agent API."""
    model = analyst_model()
    trace: dict[str, Any] = {
        "errors": [],
        "phase": "sonnet_analyst_commentary",
        "model": model,
        "provider": "perplexity",
        "section_ids": [int(s.get("id") or 0) for s in sections],
    }
    if not sections:
        return sections, trace
    if not anthropic_enabled():
        trace["errors"].append("PERPLEXITY_API_KEY not configured for analyst pass")
        return sections, trace
    needs_commentary = [
        sec
        for sec in sections
        if not (sec.get("what_this_means") or sec.get("how_to_use"))
        and int(sec.get("id") or 0) not in FINANCIAL_SECTION_IDS
    ]
    if not needs_commentary:
        trace["phase"] = "sonnet_analyst_commentary"
        trace["skipped"] = "all_sections_already_have_commentary"
        return sections, trace
    prompt = _analyst_commentary_prompt(topic, industry, geography, needs_commentary)
    api = call_anthropic_json(prompt=prompt, model=model, max_tokens=4096, timeout=200)
    trace["usage"] = api.get("usage") or {}
    ledger_row = perplexity_usage_row(api.get("usage"), model=str(api.get("model") or model), phase="sonnet_analyst_commentary")
    trace["usage_ledger"] = ledger_row
    if report_id:
        _ledger_log(report_id, ledger_row)
    if api.get("error"):
        trace["errors"].append(str(api["error"]))
        ledger_row["error"] = str(api["error"])
        return sections, trace
    parsed = api.get("parsed") if isinstance(api.get("parsed"), dict) else {}
    rows = parsed.get("sections") if isinstance(parsed.get("sections"), list) else []
    by_id = {int(r.get("id") or 0): r for r in rows if isinstance(r, dict)}
    out: list[dict[str, Any]] = []
    for sec in sections:
        row = dict(sec)
        aid = int(row.get("id") or 0)
        extra = by_id.get(aid) or {}
        row["what_this_means"] = [
            str(x).strip() for x in (extra.get("what_this_means") or []) if str(x).strip()
        ]
        row["how_to_use"] = [
            str(x).strip() for x in (extra.get("how_to_use") or []) if str(x).strip()
        ]
        # Legacy key_insights field mirrors what_this_means for downstream consumers
        row["key_insights"] = list(row["what_this_means"])
        out.append(sanitize_section_commentary(row))
    if not by_id and api.get("raw_content"):
        trace["errors"].append("sonnet_analyst_parse_failed")
        trace["raw_preview"] = str(api.get("raw_content") or "")[:800]
    return out, trace


def _competitors_from_matrix(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in matrix:
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        out.append(
            {
                "name": name,
                "pricing": str(row.get("pricing") or "").strip(),
                "positioning": str(row.get("positioning") or "").strip(),
                "source": str(row.get("source_url") or row.get("source") or "claude_competitor_pass"),
                "url": str(row.get("source_url") or row.get("url") or "").strip(),
                "discovered_via": "claude_competitor_pass",
                "evidence_backed": bool(row.get("evidence_backed", True)),
            }
        )
    return out


def _competitors_from_section_metrics(section: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    km = section.get("key_metrics") if isinstance(section.get("key_metrics"), dict) else {}
    for key, val in km.items():
        key_s = str(key or "").strip()
        val_s = str(val or "").strip()
        if not key_s or not val_s:
            continue
        name = key_s.replace("_pricing", "").replace("_price", "").replace("_", " ").strip()
        if len(name) < 2:
            continue
        out.append(
            {
                "name": name,
                "pricing": val_s,
                "positioning": "",
                "source": "perplexity_competitor_pass",
                "url": "",
                "discovered_via": "perplexity_competitor_pass",
                "evidence_backed": True,
            }
        )
    return out


def competitor_truth_from_report(report: dict[str, Any] | None) -> dict[str, Any]:
    """Build competitor_truth.matrix for agent tools from a Perplexity report payload."""
    if not isinstance(report, dict):
        return {"matrix": [], "source": "none"}
    matrix = report.get("competitor_matrix")
    if isinstance(matrix, list) and matrix:
        parsed = _competitors_from_matrix(matrix)
        if parsed:
            return {"matrix": parsed, "source": "claude_competitor_pass"}
    matrix_rows: list[dict[str, Any]] = []
    for sec in report.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        if int(sec.get("id") or 0) in {7, 8, 60}:
            matrix_rows.extend(_competitors_from_section_metrics(sec))
    if matrix_rows:
        return {"matrix": matrix_rows, "source": "perplexity_report_sections"}
    return {"matrix": [], "source": "none"}


def build_markdown_report(
    topic: str,
    industry: str,
    geography: str,
    sections: list[dict[str, Any]],
    *,
    section_count: int,
    runtime_sec: float,
    evidence_audit: dict[str, Any] | None = None,
    plan: list[dict[str, Any]] | None = None,
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    plan_rows = plan if isinstance(plan, list) and plan else None
    by_id = {int(r.get("id") or 0): r for r in sections if isinstance(r, dict)}
    if plan_rows:
        display_rows: list[tuple[int, dict[str, Any]]] = []
        for idx, prow in enumerate(plan_rows, 1):
            sid = int(prow.get("id") or 0)
            row = by_id.get(sid)
            if row:
                display_rows.append((idx, row))
            else:
                display_rows.append(
                    (
                        idx,
                        {
                            "id": sid,
                            "title": prow.get("title") or f"Section {sid}",
                            "body_markdown": (
                                "_This module was in your report plan but was not returned by the research pipeline. "
                                "Regenerate or increase section depth._"
                            ),
                            "key_insights": [],
                            "key_metrics": {},
                            "sources": [],
                            "missing": True,
                        },
                    )
                )
        catalog_ids = ", ".join(str(int(p.get("id") or 0)) for p in plan_rows)
        delivered = sum(1 for _, row in display_rows if not row.get("missing"))
    else:
        sorted_sections = sorted(sections, key=lambda r: int(r.get("id") or 0))
        display_rows = [(idx, row) for idx, row in enumerate(sorted_sections, 1)]
        catalog_ids = ", ".join(str(int(r.get("id") or 0)) for r in sorted_sections)
        delivered = len(sorted_sections)

    lines = [
        f"# IIDATECH Market Research Report — {topic}",
        "",
        f"- **Industry:** {industry}",
        f"- **Market:** {geography}",
        f"- **Sections delivered:** {delivered} of {section_count} planned (catalog modules: {catalog_ids})",
        f"- **Generated:** {ts}",
        f"- **Research runtime:** {runtime_sec:.1f}s",
        "",
        _LABELING_LEGEND,
        "",
        "---",
        "",
    ]
    for display_idx, row in display_rows:
        sid = row.get("id")
        title = row.get("title") or f"Section {sid}"
        lines.append(f"## {display_idx}. {title}")
        lines.append(f"*Catalog module {sid}*")
        lines.append("")
        body = sanitize_report_text(str(row.get("body_markdown") or "").strip())
        lines.append(body or "_No content returned for this section._")
        means = row.get("what_this_means") if isinstance(row.get("what_this_means"), list) else []
        if means:
            lines.append("")
            lines.append("### What this means")
            for bullet in means:
                lines.append(f"- {bullet}")
        how = row.get("how_to_use") if isinstance(row.get("how_to_use"), list) else []
        if how:
            lines.append("")
            lines.append("### How to use this info")
            for bullet in how:
                lines.append(f"- {bullet}")
        insights = row.get("key_insights") if isinstance(row.get("key_insights"), list) else []
        if insights and not means:
            lines.append("")
            lines.append("### Key insights")
            for bullet in insights:
                lines.append(f"- {bullet}")
        metrics = row.get("key_metrics") if isinstance(row.get("key_metrics"), dict) else {}
        if metrics:
            lines.append("")
            lines.append("**Key metrics**")
            for key, val in metrics.items():
                lines.append(f"- **{key}:** {sanitize_report_text(str(val))}")
        sources = [str(u) for u in (row.get("sources") or []) if str(u).strip()]
        if sources:
            lines.append("")
            lines.append("**Sources**")
            for idx, url in enumerate(sources, 1):
                lines.append(f"- [{idx}] {url}")
        lines.append("")
    if evidence_audit and _report_debug_mode():
        lines.extend(
            [
                "---",
                "",
                "### Evidence audit (deterministic — not model self-score)",
                "",
                f"- Verified ledger figures: **{evidence_audit.get('ledger_figure_count', 0)}**",
                f"- Uncited numbers stripped from narrative: **{evidence_audit.get('stripped_uncited_numbers', 0)}**",
                f"- Math issues flagged: **{evidence_audit.get('math_issues', 0)}**",
                f"- Named competitors (Claude pass): **{evidence_audit.get('competitor_count', 0)}**",
                f"- Search citations harvested: **{evidence_audit.get('search_citations', 0)}**",
                f"- Gitnux benchmark reports: **{evidence_audit.get('gitnux_reports', 0)}** "
                f"({evidence_audit.get('gitnux_facts', 0)} facts)",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def generate_perplexity_report(
    topic: str,
    *,
    industry: str = "General",
    geography: str = "Global",
    areas: str = "",
    section_count: int = 6,
    include_extensions: bool = False,
    include_financial_table: bool = True,
) -> dict[str, Any]:
    started = time.time()
    topic = str(topic or "").strip()
    industry = str(industry or "General").strip() or "General"
    geography = str(geography or "Global").strip() or "Global"
    areas = str(areas or "").strip()
    market_label = format_market_geography(geography, areas)
    if not topic:
        return {"success": False, "error": "Topic is required."}
    if not perplexity_enabled():
        return {"success": False, "error": "PERPLEXITY_API_KEY is not configured."}
    try:
        plan = build_report_plan(
            section_count,
            include_extensions=False if not FRAMEWORKS_ENABLED else include_extensions,
            include_financial_table=include_financial_table,
        )
    except ValueError as exc:
        return {"success": False, "error": str(exc)}

    report_id = _report_id(topic, market_label)
    all_sections: list[dict[str, Any]] = []
    traces: list[dict[str, Any]] = []
    usage_ledger: list[dict[str, Any]] = []
    competitor_matrix: list[dict[str, Any]] = []
    figure_ledger: dict[str, Any] = {}
    number_audit: dict[str, Any] = {}
    math_audit: dict[str, Any] = {}

    fin_plan = financial_sections_in_plan(plan) if include_financial_table else []
    comp_plan = competitor_sections_in_plan(plan)
    narrative_plan = narrative_sections(plan)

    harvest, harvest_citations, harvest_trace = _fetch_search_harvest(
        topic, industry, market_label, report_id=report_id
    )
    traces.append(harvest_trace)
    if harvest_trace.get("usage_ledger"):
        usage_ledger.append(harvest_trace["usage_ledger"])

    inst_harvest, inst_citations, inst_trace = _fetch_institutional_harvest(
        topic, industry, market_label, report_id=report_id
    )
    traces.append(inst_trace)
    if inst_trace.get("usage_ledger"):
        usage_ledger.append(inst_trace["usage_ledger"])
    if inst_harvest:
        harvest = _merge_harvest_dicts(inst_harvest, harvest)
    harvest_citations = list(dict.fromkeys([*inst_citations, *harvest_citations]))

    statista_pack: dict[str, Any] = {}
    statista_trace: dict[str, Any] = {"phase": "statista_harvest", "errors": [], "section_ids": []}
    if statista_enabled():
        try:
            statista_pack = statista_harvest_pack(topic, industry, market_label)
            harvest, statista_citations = merge_statista_into_harvest(harvest, statista_pack)
            harvest_citations = list(dict.fromkeys([*statista_citations, *harvest_citations]))
            statista_trace["credits_used"] = statista_pack.get("credits_used", 0)
            statista_trace["fact_count"] = len(statista_pack.get("financial_facts") or [])
            statista_trace["mode"] = statista_pack.get("mode")
            if statista_pack.get("errors"):
                statista_trace["errors"].extend(statista_pack["errors"])
            if not statista_pack.get("financial_facts"):
                statista_trace["note"] = statista_pack.get("note") or "no_statista_facts"
        except Exception as exc:
            statista_trace["errors"].append(str(exc)[:200])
    else:
        statista_trace["skipped"] = "statista_disabled_or_missing_api_key"
    traces.append(statista_trace)

    gitnux_pack: dict[str, Any] = {}
    gitnux_trace: dict[str, Any] = {"phase": "gitnux_benchmark", "errors": [], "section_ids": []}
    if gitnux_enabled():
        try:
            gitnux_pack = gitnux_benchmark_pack(topic, industry, max_reports=1)
            harvest, gitnux_citations = merge_gitnux_into_harvest(harvest, gitnux_pack)
            harvest_citations = list(dict.fromkeys([*harvest_citations, *gitnux_citations]))
            gitnux_trace["matched_reports"] = gitnux_pack.get("matched_reports") or []
            gitnux_trace["fact_count"] = len(gitnux_pack.get("financial_facts") or [])
            if not gitnux_pack.get("matched_reports"):
                gitnux_trace["note"] = gitnux_pack.get("note") or "no_match"
        except Exception as exc:
            gitnux_trace["errors"].append(str(exc)[:200])
    else:
        gitnux_trace["skipped"] = "gitnux_disabled"
    traces.append(gitnux_trace)

    harvest_block = _format_harvest_block(harvest, harvest_citations)
    statista_block = format_statista_block(statista_pack)
    if statista_block:
        harvest_block = f"{statista_block}\n\n{harvest_block}"
    gitnux_block = format_gitnux_block(gitnux_pack)
    if gitnux_block:
        harvest_block = f"{harvest_block}\n\n{gitnux_block}"

    financial_sections: list[dict[str, Any]] = []
    if fin_plan:
        financial_sections, ledger_meta, fin_trace = _fetch_financial_package(
            topic,
            industry,
            market_label,
            section_rows=fin_plan,
            harvest_block=harvest_block,
            harvest_citations=harvest_citations,
            report_id=report_id,
        )
        traces.append(fin_trace)
        if fin_trace.get("usage_ledger"):
            usage_ledger.append(fin_trace["usage_ledger"])
        if ledger_meta.get("financial_ledger"):
            figure_ledger["opus_financial_ledger"] = ledger_meta["financial_ledger"]
        all_sections.extend(financial_sections)

    competitor_sections: list[dict[str, Any]] = []
    if comp_plan:
        competitor_sections, competitor_matrix, comp_trace = _fetch_competitor_landscape(
            topic,
            industry,
            market_label,
            section_rows=comp_plan,
            harvest_block=harvest_block,
            harvest_citations=harvest_citations,
            report_id=report_id,
        )
        traces.append(comp_trace)
        if comp_trace.get("usage_ledger"):
            usage_ledger.append(comp_trace["usage_ledger"])
        all_sections.extend(competitor_sections)

    if financial_sections or competitor_sections:
        relabel_ids = FINANCIAL_SECTION_IDS | COMPETITOR_SECTION_IDS
        relabeled: list[dict[str, Any]] = []
        for row in all_sections:
            sid = int(row.get("id") or 0)
            if sid in relabel_ids:
                relabeled.extend(apply_source_tier_labels([row]))
            else:
                relabeled.append(row)
        all_sections = relabeled

    if competitor_sections:
        all_sections = _apply_competitor_coverage_warning(all_sections, competitor_matrix)

    ledger = build_figure_ledger(financial_sections)
    ledger = merge_structured_ledger(ledger, figure_ledger.get("opus_financial_ledger"))
    figure_ledger.update(ledger)
    fact_pack = _format_financial_context(ledger, financial_sections)

    narrative_sections_out: list[dict[str, Any]] = []
    batches = _batch_sections(narrative_plan)
    for batch in batches:
        rows, trace = _fetch_batch(
            topic, industry, market_label, batch, fact_pack=fact_pack, report_id=report_id
        )
        traces.append(trace)
        if trace.get("usage_ledger"):
            usage_ledger.append(trace["usage_ledger"])
        narrative_sections_out.extend(rows)

    protected_ids = FINANCIAL_SECTION_IDS | COMPETITOR_SECTION_IDS
    narrative_sections_out, number_audit = apply_number_gate(
        narrative_sections_out,
        ledger=ledger,
        protected_section_ids=protected_ids,
    )
    all_sections.extend(narrative_sections_out)

    if financial_sections:
        audited_fin, math_audit = apply_math_audit(financial_sections)
        fin_by_id = {int(s.get("id") or 0): s for s in audited_fin}
        merged: dict[int, dict[str, Any]] = {}
        for row in all_sections:
            sid = int(row.get("id") or 0)
            merged[sid] = fin_by_id.get(sid, row)
        all_sections = list(merged.values())

    by_id: dict[int, dict[str, Any]] = {}
    for row in all_sections:
        by_id[int(row["id"])] = row
    ordered = []
    for prow in plan:
        sid = int(prow["id"])
        if sid in by_id:
            ordered.append(by_id[sid])
        else:
            ordered.append(
                {
                    "id": sid,
                    "title": prow.get("title") or f"Section {sid}",
                    "body_markdown": (
                        "_This module was in your report plan but was not returned by the research pipeline. "
                        "Regenerate or increase section depth._"
                    ),
                    "key_insights": [],
                    "key_metrics": {},
                    "sources": [],
                    "missing": True,
                }
            )

    ordered = apply_pricing_footnotes(ordered, audit=math_audit)

    if ordered:
        ordered, analyst_trace = _apply_analyst_commentary(
            ordered, topic, industry, market_label, report_id=report_id
        )
        traces.append(analyst_trace)
        if analyst_trace.get("usage_ledger"):
            usage_ledger.append(analyst_trace["usage_ledger"])

    evidence_audit = {
        "ledger_figure_count": figure_ledger.get("figure_count", 0),
        "stripped_uncited_numbers": number_audit.get("stripped_count", 0),
        "math_issues": len(math_audit.get("math_issues") or []),
        "competitor_count": len(competitor_matrix),
        "competitor_search_incomplete": len(competitor_matrix) < _COMPETITOR_MIN_NAMED,
        "search_citations": len(harvest_citations),
        "gitnux_reports": len(gitnux_pack.get("matched_reports") or []),
        "gitnux_facts": len(gitnux_pack.get("financial_facts") or []),
        "statista_credits_used": statista_pack.get("credits_used", 0) if statista_pack else 0,
        "statista_facts": len(statista_pack.get("financial_facts") or []) if statista_pack else 0,
    }

    runtime = round(time.time() - started, 1)
    markdown = build_markdown_report(
        topic,
        industry,
        market_label,
        ordered,
        section_count=len(plan),
        runtime_sec=runtime,
        evidence_audit=evidence_audit,
        plan=plan,
    )
    usage_total = 0.0
    for tr in traces:
        cost = (tr.get("usage") or {}).get("cost") or {}
        if isinstance(cost, dict):
            usage_total += float(cost.get("total_cost") or 0.0)
    ledger_totals = sum_ledger(usage_ledger, successful_only=True)
    if ledger_totals.get("cost_usd"):
        usage_total = float(ledger_totals["cost_usd"])

    phase_status: dict[str, str] = {}
    for tr in traces:
        phase = str(tr.get("phase") or "unknown")
        if tr.get("errors"):
            phase_status[phase] = "failed"
        elif tr.get("skipped"):
            phase_status[phase] = "skipped"
        elif tr.get("usage_ledger", {}).get("total_tokens") or phase in {
            "sonar_search_harvest",
            "gitnux_benchmark",
            "opus_financial_figures",
            "sonnet_competitor_landscape",
            "perplexity_narrative_draft",
            "sonnet_analyst_commentary",
        }:
            phase_status[phase] = "ok"
        else:
            phase_status[phase] = "skipped"

    secondary_failed = any(
        p in phase_status and phase_status[p] == "failed"
        for p in (
            "sonar_search_harvest",
            "opus_financial_figures",
            "sonnet_competitor_landscape",
            "sonnet_analyst_commentary",
        )
    )
    partial_success = bool(ordered) and secondary_failed

    projected: dict[str, Any] = {}
    if partial_success:
        projected = {
            "sonar_search_harvest": project_phase_cost(report_search_model(), 4000, 800),
            "opus_financial_figures": project_phase_cost(financial_model(), 8000, 1500),
            "sonnet_competitor_landscape": project_phase_cost(analyst_model(), 6000, 1200),
            "sonnet_analyst_commentary": project_phase_cost(analyst_model(), 15000, 2000),
        }
        projected["total_if_secondary_passes_ok"] = round(
            float(usage_total or 0) + sum(float(v) for v in projected.values()),
            4,
        )

    error_msg = None if ordered else "IIDATECH research returned no usable sections."
    warnings: list[str] = []
    for tr in traces:
        for item in tr.get("errors") or []:
            text = str(item)
            if text and text not in warnings:
                warnings.append(text)
            if "401" in text or "Unauthorized" in text:
                error_msg = "PERPLEXITY_API_KEY rejected (401 Unauthorized)."
    if warnings and ordered:
        error_msg = None

    return {
        "success": bool(ordered),
        "partial_success": partial_success,
        "phase_status": phase_status,
        "projected_cost_usd": projected if projected else None,
        "report_id": report_id,
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "areas": areas,
        "market_label": market_label,
        "section_count": len(plan),
        "include_extensions": False,
        "frameworks_enabled": FRAMEWORKS_ENABLED,
        "include_financial_table": include_financial_table,
        "sections": ordered,
        "sections_written": sum(1 for s in ordered if not s.get("missing")),
        "sections_planned": len(plan),
        "catalog_section_ids": [int(p["id"]) for p in plan],
        "report_markdown": markdown,
        "runtime_sec": runtime,
        "provider": "sonar_harvest+opus_financial+sonnet_competitor+sonar_narrative",
        "perplexity_traces": traces,
        "usage_ledger": usage_ledger,
        "usage_totals": ledger_totals,
        "math_audit": math_audit,
        "number_audit": number_audit,
        "figure_ledger": figure_ledger,
        "competitor_matrix": competitor_matrix,
        "gitnux_pack": gitnux_pack if gitnux_pack else None,
        "statista_pack": statista_pack if statista_pack else None,
        "evidence_audit": evidence_audit,
        "models": {
            "search": report_search_model(),
            "draft": report_perplexity_model(),
            "financial": financial_model(),
            "analyst": analyst_model(),
        },
        "estimated_cost_usd": round(usage_total, 4) if usage_total else None,
        "warnings": warnings,
        "error": error_msg,
    }


def to_business_report_context(report: dict[str, Any]) -> dict[str, Any]:
    """Adapt a direct market research report for business builder / plan generators."""
    if not isinstance(report, dict) or not report.get("success"):
        return {}
    sections_list = [row for row in (report.get("sections") or []) if isinstance(row, dict)]
    sections_dict: dict[str, Any] = {}
    citations: list[dict[str, str]] = []
    metric_rows: dict[str, Any] = {}
    for row in sections_list:
        sid = str(int(row.get("id") or 0) or len(sections_dict) + 1)
        body = str(row.get("body_markdown") or "").strip()
        sources = [str(u).strip() for u in (row.get("sources") or []) if str(u).strip()]
        key_metrics = row.get("key_metrics") if isinstance(row.get("key_metrics"), dict) else {}
        sections_dict[sid] = {
            "title": row.get("title"),
            "content": body,
            "markdown": body,
            "key_metrics": key_metrics,
            "key_insights": row.get("key_insights") if isinstance(row.get("key_insights"), list) else [],
            "sources": sources,
        }
        for url in sources:
            citations.append({"url": url, "title": url, "publisher": "web", "source_type": "iidatech_research"})
        for key, val in key_metrics.items():
            metric_rows[str(key)] = val

    summaries: list[dict[str, Any]] = []
    for row in sorted(sections_list, key=lambda r: int(r.get("id") or 0)):
        summaries.append(
            {
                "id": row.get("id"),
                "title": row.get("title"),
                "excerpt": str(row.get("body_markdown") or "")[:2500],
                "key_insights": row.get("key_insights") if isinstance(row.get("key_insights"), list) else [],
                "key_metrics": row.get("key_metrics") if isinstance(row.get("key_metrics"), dict) else {},
            }
        )

    quantitative: dict[str, Any] = {}
    for key, val in metric_rows.items():
        lk = key.lower()
        if "tam" in lk and "tam" not in quantitative:
            quantitative["tam"] = val
        elif "sam" in lk and "sam" not in quantitative:
            quantitative["sam"] = val
        elif "som" in lk and "som" not in quantitative:
            quantitative["som"] = val
        elif "cagr" in lk and "cagr" not in quantitative:
            quantitative["cagr"] = val

    comp_truth = competitor_truth_from_report(report)
    markdown = str(report.get("report_markdown") or "")
    return {
        "topic": report.get("topic"),
        "industry": report.get("industry"),
        "geography": report.get("geography"),
        "areas": report.get("areas") or "",
        "market_label": report.get("market_label") or report.get("geography"),
        "source": "iidatech_market_research",
        "competitor_truth": comp_truth,
        "sections": sections_dict,
        "report_markdown": markdown,
        "topic_intelligence_brief": {
            "source": "iidatech_market_research",
            "section_summaries": summaries,
            "report_excerpt": markdown[:12000],
        },
        "evidence_completeness": {
            "sections_written": report.get("sections_written"),
            "section_count": report.get("section_count"),
            "source": "iidatech_market_research",
        },
        "diligence_pack": {
            "citation_ledger": citations,
            "research_summary": markdown[:12000],
        },
        "quantitative_model": quantitative,
    }
