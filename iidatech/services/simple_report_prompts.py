"""Boardroom-grade prompts for the primary Perplexity + Claude report pipeline."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from iidatech.services.market_currency import currency_for_geography, currency_prompt_block
from iidatech.services.report_section_plans import format_section_outline

BOARDROOM_BRIEF = (
    "Audience: board members, angel/seed/Series A investors, and founders preparing a funding narrative. "
    "Tone: institutional, neutral, specific, decision-ready. "
    "Every factual claim must cite a real https source. "
    "No hype, no unsourced 'Validated' labels, no invented statistics."
)

TAM_SAM_SOM_FRAMEWORK = """
MARKET SIZING FRAMEWORK (use for all TAM / SAM / SOM work):

Definitions:
- TAM (Total Addressable Market): total revenue if you achieved 100% global market share with no constraints.
  Top-down: start from published total industry/category revenue for the broadest relevant market.
  Bottom-up: (total potential buyers globally) × (% who need this job-to-be-done) × (ARPU/ACV per year).

- SAM (Serviceable Addressable Market): portion of TAM you can realistically target given geography, customer segment,
  product capabilities, regulations, and GTM. Apply explicit filters with sourced percentages:
  SAM = TAM × geo_filter × segment_filter × product_fit_filter (show each filter and source).

- SOM (Serviceable Obtainable Market): realistic capture in 3–5 years given competition and execution.
  Typical VC expectation: 3–5% of SAM over 3–5 years for a focused startup (label DERIVED, show math).
  Bottom-up check: (target customers you can reach) × (realistic conversion %) × (ACV).

Dual validation (required when computing):
1. Top-down path — industry revenue → niche slice → TAM/SAM/SOM
2. Bottom-up path — buyer count × penetration × price → TAM/SAM/SOM
Reconcile both; flag if results diverge by more than 2× and explain which to use for this niche.

Labels:
- FACT = number quoted directly from a cited source
- DERIVED = calculated from sourced inputs (show formula in notes)
- ESTIMATE = conservative assumption when a filter % is not published (state assumption clearly)
- NOT FOUND = only when calculation is impossible with available sourced inputs

VC benchmarks (for commentary, not invented numbers):
- Series A investors typically want $1B+ TAM headroom at the category level
- SOM should support near-term revenue plans (3–5% SAM share is a realistic planning anchor)
""".strip()

def research_prompt(topic: str, industry: str, geography: str) -> str:
    year = datetime.now(timezone.utc).year
    return (
        f"You are an institutional market researcher. {BOARDROOM_BRIEF}\n\n"
        f"Search the live web for **{topic}** in **{geography}** ({industry}). Year: {year}.\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "research_summary": "3-5 sentences of qualitative findings for an investor memo",\n'
        '  "market_facts": [{"fact": "", "source_url": "https://...", "source_name": ""}],\n'
        '  "competitor_facts": [{"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}],\n'
        '  "pricing_facts": [{"tier": "", "price": "", "source_url": "https://..."}],\n'
        '  "sources": ["https://..."]\n'
        "}\n\n"
        "Rules: minimum 5 market_facts and 3 competitor_facts where data exists. "
        "Prioritize MOSPI, RBI, NASSCOM, DPIIT, IBEF, Tracxn, Crunchbase, industry reports, and primary vendor sites. "
        "Every fact needs a real https URL. No invented numbers."
    )

def financial_sizing_prompt(topic: str, industry: str, geography: str) -> str:
    year = datetime.now(timezone.utc).year
    currency_block = currency_prompt_block(geography)
    return (
        f"You are a market sizing analyst for investor due diligence. {BOARDROOM_BRIEF}\n\n"
        f"{TAM_SAM_SOM_FRAMEWORK}\n\n"
        f"{currency_block}\n\n"
        f"Search the live web for TAM, SAM, and SOM inputs for **{topic}** in **{geography}** ({industry}). Year: {year}.\n\n"
        "Your job is to collect PUBLISHED figures AND the building blocks needed for top-down and bottom-up sizing.\n\n"
        "Search explicitly for:\n"
        f'- "{topic} TAM SAM SOM market size {geography}"\n'
        f'- "{industry} market size {geography} {year}"\n'
        "- MOSPI, RBI, NASSCOM, DPIIT, IBEF, Tracxn, Crunchbase, Zinnov, ESOMAR, Statista, Grand View, Mordor\n"
        f'- Total addressable buyers: SMB counts, enterprise counts, households, professionals, startups in {geography}\n'
        f'- ARPU / ACV / average contract value for {topic} or adjacent category\n'
        f'- Penetration rates, adoption %, market share of incumbents, CAGR\n'
        f'- Geographic share of global market for {industry}\n\n'
        "Return STRICT JSON only:\n"
        "{\n"
        '  "market_size_facts": [\n'
        '    {"metric": "TAM|SAM|SOM|market revenue|addressable units", "value": "", "year": "", '
        '"geography_scope": "domestic|global|niche", "source_name": "", "source_url": "https://...", "notes": ""}\n'
        "  ],\n"
        '  "tam_candidates": [\n'
        '    {"value": "", "scope": "domestic|global|niche|adjacent", "source_name": "", '
        '"source_url": "https://...", "year": "", "notes": "what this number measures"}\n'
        "  ],\n"
        '  "denominator_facts": [\n'
        '    {"metric": "SMB count|startup count|buyer population|companies in segment|households|professionals", '
        '"value": "", "source_url": "https://...", "notes": ""}\n'
        "  ],\n"
        '  "top_down_inputs": [\n'
        '    {"step": "total industry revenue|category revenue|CAGR|geo share", "value": "", '
        '"source_url": "https://...", "notes": ""}\n'
        "  ],\n"
        '  "bottom_up_inputs": [\n'
        '    {"metric": "buyer_count|penetration_pct|ARPU|ACV|conversion_pct|competitor_count", "value": "", '
        '"source_url": "https://...", "notes": ""}\n'
        "  ],\n"
        f'  "reporting_currency": "{currency_for_geography(geography)["code"]}",\n'
        '  "sources": ["https://..."]\n'
        "}\n\n"
        "Rules:\n"
        "- Find at least 3 market_size_facts or tam_candidates when public data exists.\n"
        "- Collect at least 2 denominator_facts and 2 bottom_up_inputs (buyer count + price/ARPU) when available.\n"
        "- Prefer sources and figures in the primary reporting currency for this geography.\n"
        "- If published SAM/SOM do not exist, leave value empty but gather filter inputs (geo %, segment %, ARPU).\n"
        "- Never invent figures — only cite numbers with real https URLs.\n"
        "- Prefer niche-scoped TAM over inflated global category TAM when both exist; note scope in tam_candidates."
    )

def competitor_harvest_prompt(topic: str, industry: str, geography: str) -> str:
    """Dedicated Perplexity pass for Competitive Landscape only."""
    return competitive_landscape_research_prompt(topic, industry, geography)


def competitive_landscape_research_prompt(topic: str, industry: str, geography: str) -> str:
    year = datetime.now(timezone.utc).year
    return (
        f"You are a competitive intelligence specialist. Your ONLY task is a dedicated Competitive Landscape "
        f"research pass for a boardroom-ready investor report.\n\n"
        f"TOPIC: {topic}\n"
        f"INDUSTRY: {industry}\n"
        f"MARKET / GEOGRAPHY: {geography}\n"
        f"YEAR: {year}\n\n"
        "Search the live web thoroughly. Run separate searches for:\n"
        f'1. Direct competitors — SaaS/products/services for "{topic}" in {geography}\n'
        f'2. "{topic}" alternatives, "best {topic} tools", "{topic} software {geography}"\n'
        f'3. Adjacent global tools that founders in {industry} use for the same job-to-be-done\n'
        f"4. Agencies, consultancies, and content/review sites competing for the same buyer\n"
        f"5. Incumbents and market leaders in {industry} relevant to {topic}\n"
        f"6. G2, Capterra, Tracxn, Crunchbase, Similarweb listings for {topic} in {geography}\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "landscape_summary": "3-4 sentences on competitive intensity and structure",\n'
        '  "competitor_matrix": [\n'
        '    {\n'
        '      "name": "",\n'
        '      "type": "direct_saas|adjacent_global|agency|incumbent|marketplace",\n'
        '      "headquarters": "",\n'
        '      "pricing": "",\n'
        '      "target_customer": "",\n'
        '      "positioning": "",\n'
        '      "strengths": "",\n'
        '      "weaknesses": "",\n'
        '      "funding_or_scale": "",\n'
        '      "source_url": "https://...",\n'
        '      "source_name": ""\n'
        "    }\n"
        "  ],\n"
        '  "direct_saas_competitors": [{"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}],\n'
        '  "adjacent_global_tools": [{"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}],\n'
        '  "agency_or_services_competitors": [{"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}],\n'
        '  "whitespace_search": "Exact queries run for self-serve SaaS; whether any were found or not",\n'
        '  "competitive_gaps": ["observed gaps or whitespace with evidence"],\n'
        '  "sources": ["https://..."]\n'
        "}\n\n"
        "RULES:\n"
        "- Minimum 8 competitors in competitor_matrix when they exist in the market.\n"
        "- Every row needs a real https:// source_url from your search (vendor site, G2, Tracxn, news, review).\n"
        "- Include pricing only when found on a source — otherwise say NOT FOUND.\n"
        "- Do not invent companies, funding rounds, or market share.\n"
        "- If no self-serve SaaS exists, document what you searched in whitespace_search."
    )


def competitive_landscape_write_prompt(
    topic: str,
    industry: str,
    geography: str,
    competitor_block: str,
) -> str:
    return (
        f"You are a competitive intelligence writer (Claude Sonnet). Write ONLY the "
        f"## Competitive Landscape section for a funding-ready report.\n\n"
        f"TOPIC: {topic}\nINDUSTRY: {industry}\nMARKET / GEOGRAPHY: {geography}\n\n"
        f"DEDICATED PERPLEXITY COMPETITIVE LANDSCAPE RESEARCH:\n{competitor_block[:12000]}\n\n"
        "Return markdown only (no JSON, no code fences). Start with exactly: ## Competitive Landscape\n\n"
        "Structure:\n"
        "- Opening paragraph: market structure and competitive intensity\n"
        "- ### Direct competitors (table or subsections with name, pricing, positioning, source footnotes [n])\n"
        "- ### Adjacent / global tools\n"
        "- ### Agencies & services (if any)\n"
        "- ### Whitespace & gaps (only with evidence from whitespace_search)\n\n"
        "RULES:\n"
        "- Use ONLY companies and facts from the research above.\n"
        "- Every pricing claim and company fact needs an inline [n] footnote.\n"
        "- Minimum 6 named competitors across categories where research provides them.\n"
        "- Do not write any other report sections."
    )

def financial_opus_prompt(
    topic: str,
    industry: str,
    geography: str,
    research_block: str,
    sizing_block: str,
) -> str:
    currency_block = currency_prompt_block(geography)
    primary = currency_for_geography(geography)
    return (
        f"You are a financial analyst (Claude Opus) extracting SOURCED BASE FIGURES for automated TAM/SAM/SOM calculation. "
        f"{BOARDROOM_BRIEF}\n\n"
        f"{TAM_SAM_SOM_FRAMEWORK}\n\n"
        f"{currency_block}\n\n"
        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\n\n"
        f"GENERAL RESEARCH:\n{research_block[:6000]}\n\n"
        f"MARKET SIZING RESEARCH:\n{sizing_block[:8000]}\n\n"
        "TASK: Extract ONLY sourced building blocks from the research above. "
        "Do NOT output final TAM/SAM/SOM values — Python will compute them from your base_figures.\n"
        "Pick ONE industry revenue figure and ONE niche-slice % for top-down. "
        "Pick buyer count + ARPU for bottom-up. "
        "Put conflicting published TAMs in published_reference only (reference — not primary).\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "base_figures": {\n'
        '    "industry_revenue": {"value": "e.g. ₹9.2 lakh crore", "source_url": "https://...", "source_name": "IBEF", "notes": "what market this measures"},\n'
        '    "niche_slice_pct": {"value_pct": 12.5, "label": "ESTIMATE|DERIVED", "source_url": "https://...", "notes": "% of industry revenue for this niche"},\n'
        '    "buyer_count": {"value": "140 million households", "source_url": "https://...", "notes": ""},\n'
        '    "addressable_pct": {"value_pct": 35, "label": "ESTIMATE", "notes": "% of buyers realistically reachable"},\n'
        '    "arpu_annual": {"value": "₹12,000", "source_url": "https://...", "notes": "annual spend per buyer"},\n'
        '    "geo_filter_pct": {"value_pct": 100, "label": "DERIVED", "notes": "geography filter for SAM"},\n'
        '    "segment_filter_pct": {"value_pct": 25, "label": "ESTIMATE", "notes": "segment filter for SAM"},\n'
        '    "product_fit_pct": {"value_pct": 60, "label": "ESTIMATE", "notes": "product/category fit filter for SAM"},\n'
        '    "som_capture_pct": {"value_pct": 4, "label": "ESTIMATE", "notes": "3-5 year obtainable % of SAM"},\n'
        '    "published_reference": [\n'
        '      {"metric": "Published TAM label", "value": "", "scope": "niche|domestic|global|adjacent", "source_url": "https://...", "source_name": "", "notes": "reference only"}\n'
        "    ],\n"
        '    "unit_economics": {\n'
        '      "price_per_unit": {"value": "25", "source_url": "https://...", "notes": "selling price"},\n'
        '      "variable_cost_per_unit": {"value": "15", "source_url": "https://...", "notes": "direct variable cost"},\n'
        '      "cogs_per_unit": {"value": "12", "source_url": "https://...", "notes": "optional — for gross profit"},\n'
        '      "quantity_sold": {"value": "500", "notes": "annual units or use buyer_count as fallback"},\n'
        '      "fixed_costs_annual": {"value": "5000", "notes": "annual fixed opex"},\n'
        '      "sales_marketing_spend": {"value": "5000", "notes": "for CAC"},\n'
        '      "new_customers": {"value": "50", "notes": "customers acquired in period"},\n'
        '      "avg_purchase_value": {"value": "50", "notes": "optional if ARPU provided"},\n'
        '      "purchases_per_customer": {"value": "10", "notes": "orders per customer per lifespan"},\n'
        '      "customer_lifespan_years": {"value": "3", "notes": "for CLV"}\n'
        "    }\n"
        "  },\n"
        '  "commentary": ["2-3 investor bullets on headroom, SAM focus, realistic SOM — no duplicate numbers"],\n'
        '  "illustrative_scenario": {"title": "", "formula": "", "result": "", "label": "ILLUSTRATIVE ONLY"}\n'
        "}\n\n"
        "RULES:\n"
        "1. Every base figure needs a real https source_url from the research (except filter % labeled ESTIMATE).\n"
        "2. Use niche-scoped industry revenue — NOT a generic national startup/ecosystem report unless it defines this category.\n"
        "3. published_reference is for alternate published TAMs only — never mix two different rupee figures as the same fact.\n"
        "4. niche_slice_pct + segment_filter_pct must reflect THIS topic (e.g. festive household e-commerce), not all of e-commerce.\n"
        "5. unit_economics: extract any available price, variable cost, fixed costs, CAC inputs — Python applies standard formulas (Revenue, CM, break-even, CLV, ROI, etc.).\n"
        f"6. All monetary values in {primary['code']} ({primary['symbol']}).\n"
        "7. Do NOT include tam, sam, or som fields — they are computed downstream."
    )

def report_sonnet_prompt(
    topic: str,
    industry: str,
    geography: str,
    research_block: str,
    competitor_block: str,
    financial_block: str,
    plan: list[dict[str, Any]],
) -> str:
    outline = format_section_outline(plan)
    currency_block = currency_prompt_block(geography)
    sizing_section = "Market Size & Valuation" in [str(s.get("title") or "") for s in plan]
    competitive_section = "Competitive Landscape" in [str(s.get("title") or "") for s in plan]
    sizing_note = (
        "- For ## Market Size & Valuation: explain TAM/SAM/SOM in investor language (definitions, why SAM is smaller than TAM, "
        "realistic SOM over 3–5 years). Reference ONLY numbers from the financial figures block. "
        "Mention top-down vs bottom-up validation if provided. No duplicate TAM/SAM/SOM table — inserted separately.\n"
        if sizing_section
        else "- Do NOT write a standalone Financial Snapshot section — sizing table is inserted separately.\n"
    )
    competitive_note = (
        "- Do NOT write ## Competitive Landscape — it is produced in a dedicated Perplexity + Claude pass and inserted separately.\n"
        if competitive_section
        else ""
    )
    return (
        f"You are a senior market research writer (Claude Sonnet) producing a boardroom- and funding-ready report. "
        f"{BOARDROOM_BRIEF}\n\n"
        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\n\n"
        f"{currency_block}\n\n"
        f"RESEARCH:\n{research_block[:5000]}\n\n"
        f"COMPETITOR RESEARCH:\n{competitor_block[:5000]}\n\n"
        f"CANONICAL FINANCIAL FIGURES (TAM/SAM/SOM computed from sourced inputs — use ONLY these numbers in prose):\n{financial_block[:4000]}\n\n"
        "Return markdown only (no JSON, no code fences).\n\n"
        "Write EXACTLY these sections in order (use ## headings exactly as titled):\n"
        f"{outline}\n\n"
        f"{sizing_note}"
        f"{competitive_note}"
        "RULES:\n"
        "- Every number in prose MUST have an inline footnote [n] (Sources appended automatically).\n"
        "- Write for investors: so-what per section, risks, and defensible claims only.\n"
        "- Do not invent TAM/SAM/SOM — use ONLY the canonical TAM, SAM, SOM lines from the financial block.\n"
        "- Do not cite alternate or reference TAM figures from background research — only the canonical trio.\n"
        "- When discussing market size, use VC framing: TAM shows category headroom, SAM shows focus, SOM shows realistic 3–5 year capture.\n"
        "- Do not add market entry plans, revenue projections, or pricing models not in research.\n"
        "- Complete every listed section; do not stop mid-sentence."
    )
