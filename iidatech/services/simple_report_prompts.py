"""Boardroom-grade prompts for the primary Perplexity + Claude report pipeline."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from iidatech.services.report_section_plans import format_section_outline

BOARDROOM_BRIEF = (
    "Audience: board members, angel/seed/Series A investors, and founders preparing a funding narrative. "
    "Tone: institutional, neutral, specific, decision-ready. "
    "Every factual claim must cite a real https source. "
    "No hype, no unsourced 'Validated' labels, no invented statistics."
)

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
    return (
        f"You are a market sizing analyst for investor due diligence. {BOARDROOM_BRIEF}\n\n"
        f"Search the live web for TAM, SAM, and SOM for **{topic}** in **{geography}** ({industry}). Year: {year}.\n\n"
        "Search explicitly for:\n"
        f'- "{topic} TAM SAM SOM market size {geography}"\n'
        f'- "{industry} market size {geography} {year}"\n'
        "- MOSPI, RBI, NASSCOM, DPIIT, IBEF, Tracxn, Crunchbase, Zinnov, ESOMAR, Statista summaries\n"
        f'- SMB/startup counts, revenue pools, penetration rates for {topic}\n\n'
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
        '    {"metric": "SMB count|startup count|buyer population", "value": "", "source_url": "https://..."}\n'
        "  ],\n"
        '  "sources": ["https://..."]\n'
        "}\n\n"
        "Rules: find at least 3 market_size_facts or tam_candidates if public data exists. "
        "If SAM/SOM are not published, note NOT FOUND. Never invent figures."
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
    return (
        f"You are a financial analyst (Claude Opus) preparing market sizing for an investor data room. {BOARDROOM_BRIEF}\n\n"
        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\n\n"
        f"GENERAL RESEARCH:\n{research_block[:6000]}\n\n"
        f"MARKET SIZING RESEARCH:\n{sizing_block[:8000]}\n\n"
        "Return STRICT JSON only:\n"
        "{\n"
        '  "tam": {"value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""},\n'
        '  "tam_alternatives": [{"value": "", "scope": "domestic|global|niche", "source_url": "https://...", "notes": ""}],\n'
        '  "tam_reconciliation": "Explain when multiple TAM figures exist and which applies to this niche",\n'
        '  "sam": {"value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""},\n'
        '  "som": {"value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""},\n'
        '  "financial_rows": [{"metric": "", "value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""}],\n'
        '  "illustrative_scenario": {"title": "", "formula": "", "result": "", "label": "ILLUSTRATIVE ONLY"},\n'
        '  "commentary": ["2-3 investor-ready bullets on what figures mean"]\n'
        "}\n\n"
        "RULES:\n"
        "1. Use ONLY numbers from research. Every value needs source_url or NOT FOUND.\n"
        "2. Reconcile multiple TAM figures via tam_alternatives + tam_reconciliation.\n"
        "3. SAM/SOM must be NOT FOUND unless sourced — no hypotheticals in sam/som values.\n"
        "4. Hypothetical math only in illustrative_scenario (ILLUSTRATIVE ONLY).\n"
        "5. Never use 'Validated' — use FACT only with tier-1/2 source_url."
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
    sizing_section = "Market Size & Valuation" in [str(s.get("title") or "") for s in plan]
    competitive_section = "Competitive Landscape" in [str(s.get("title") or "") for s in plan]
    sizing_note = (
        "- For ## Market Size & Valuation: write qualitative context only (no TAM/SAM/SOM table — inserted separately).\n"
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
        f"RESEARCH:\n{research_block[:5000]}\n\n"
        f"COMPETITOR RESEARCH:\n{competitor_block[:5000]}\n\n"
        f"FINANCIAL FIGURES (use these numbers only — do not invent others):\n{financial_block[:4000]}\n\n"
        "Return markdown only (no JSON, no code fences).\n\n"
        "Write EXACTLY these sections in order (use ## headings exactly as titled):\n"
        f"{outline}\n\n"
        f"{sizing_note}"
        f"{competitive_note}"
        "RULES:\n"
        "- Every number in prose MUST have an inline footnote [n] (Sources appended automatically).\n"
        "- Write for investors: so-what per section, risks, and defensible claims only.\n"
        "- Do not invent TAM/SAM/SOM — reference financial figures block only.\n"
        "- Do not add market entry plans, revenue projections, or pricing models not in research.\n"
        "- Complete every listed section; do not stop mid-sentence."
    )
