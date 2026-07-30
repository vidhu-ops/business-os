"""Simple market report: Sonar research + sizing + competitors -> Opus financials -> Sonnet report."""





from __future__ import annotations





import os





import re





import time





from datetime import datetime, timezone





from typing import Any





from urllib.parse import urlparse





from iidatech.evidence_bank.perplexity_client import (





    call_perplexity_json,





    perplexity_enabled,





    report_analyst_model,





    report_financial_model,





    report_search_model,





)





from iidatech.llm.anthropic_report import call_anthropic_json





from iidatech.llm.usage_ledger import perplexity_usage_row, sum_ledger





from iidatech.services.market_currency import currency_for_geography
from iidatech.services.perplexity_report_engine import format_market_geography


from iidatech.services.report_section_plans import (


    budget_for_sections,


    normalize_section_count,


    section_plan,


    section_titles,


    sonnet_max_tokens,


)


from iidatech.services.simple_report_prompts import (
    competitor_harvest_prompt,
    competitive_landscape_write_prompt,
    financial_opus_prompt,
    financial_sizing_prompt,
    report_sonnet_prompt,
    research_prompt,
)





from iidatech.services.report_source_tier import classify_source_url





_SPACED_WORD_RE = re.compile(r"(\b[a-zA-Z]\b\s+)((?:\b[a-zA-Z]\b\s+){3,}[a-zA-Z]\b)")





_SPACED_RUN_RE = re.compile(r"(?:\b[a-zA-Z]\b\s+){4,}[a-zA-Z]\b")





_SECTION_HEADING_RE = re.compile(r"^##\s+", re.M)





def simple_report_budget_usd() -> float:





    try:





        return max(0.05, float(os.getenv("SIMPLE_REPORT_BUDGET_USD", "0.50") or "0.50"))





    except ValueError:





        return 0.50





def _ledger_cost(ledger: list[dict[str, Any]]) -> float:





    return float(sum_ledger(ledger, successful_only=False).get("cost_usd") or 0.0)





def _budget_ok(ledger: list[dict[str, Any]], cap: float | None = None) -> bool:


    limit = float(cap if cap is not None else simple_report_budget_usd())


    return _ledger_cost(ledger) < limit





def repair_spaced_text(text: str) -> str:





    """Fix export corruption like 'r e f l e c t s' inside table cells."""





    s = str(text or "")





    def _collapse(match: re.Match[str]) -> str:





        return match.group(1) + match.group(2).replace(" ", "")





    s = _SPACED_WORD_RE.sub(_collapse, s)





    return _SPACED_RUN_RE.sub(lambda m: m.group(0).replace(" ", ""), s)





def _source_label(url: str) -> str:





    host = urlparse(str(url or "")).netloc or str(url or "")





    return host.replace("www.", "") or "source"





def _research_prompt(topic: str, industry: str, geography: str) -> str:





    year = datetime.now(timezone.utc).year





    return (





        f"You are a market researcher. Search the live web for **{topic}** in **{geography}** ({industry}). "





        f"Year: {year}.\n\n"





        "Return STRICT JSON only:\n"





        "{\n"





        '  "research_summary": "3-5 sentences of qualitative findings",\n'





        '  "market_facts": [{"fact": "", "source_url": "https://...", "source_name": ""}],\n'





        '  "competitor_facts": [{"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}],\n'





        '  "pricing_facts": [{"tier": "", "price": "", "source_url": "https://..."}],\n'





        '  "sources": ["https://..."]\n'





        "}\n\n"





        "Rules: minimum 5 market_facts and 3 competitor_facts where data exists. "





        "Every fact needs a real https URL from search. No invented numbers without a source."





    )





def _financial_sizing_prompt(topic: str, industry: str, geography: str) -> str:





    year = datetime.now(timezone.utc).year





    return (





        f"You are a market sizing researcher. Search the live web for TAM, SAM, and SOM data for "





        f"**{topic}** in **{geography}** ({industry}). Year: {year}.\n\n"





        "Search explicitly for:\n"





        f'- "{topic} TAM SAM SOM market size {geography}"\n'





        f'- "{industry} market size {geography} {year}"\n'





        "- MOSPI, RBI, NASSCOM, DPIIT, IBEF, Tracxn, Crunchbase, Zinnov, industry reports\n"





        f'- SMB/startup counts, revenue pools, and penetration rates relevant to {topic}\n\n'





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





        "Rules: find at least 3 market_size_facts or tam_candidates if any public data exists. "





        "If SAM/SOM are not published, return empty value with notes 'NOT FOUND'. "





        "Never invent figures — only cite numbers with real https URLs."





    )





def _competitor_harvest_prompt(topic: str, industry: str, geography: str) -> str:





    year = datetime.now(timezone.utc).year





    return (





        f"You are a competitive intelligence researcher. Search the live web for competitors to "





        f"**{topic}** in **{geography}** ({industry}). Year: {year}.\n\n"





        "Search for ALL of these categories:\n"





        f'1. Direct SaaS / self-serve software products for "{topic}"\n'





        "2. Global adjacent tools (SparkToro, Exploding Topics, Similarweb, CB Insights, G2, Capterra, Semrush, etc.)\n"





        "3. Agencies, consultancies, and content/media competitors\n"





        f'4. Explicit search: "{topic} alternatives", "{topic} SaaS", "best {topic} tools"\n\n'





        "Return STRICT JSON only:\n"





        "{\n"





        '  "direct_saas_competitors": [\n'





        '    {"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}\n'





        "  ],\n"





        '  "adjacent_global_tools": [\n'





        '    {"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}\n'





        "  ],\n"





        '  "agency_or_services_competitors": [\n'





        '    {"name": "", "pricing": "", "positioning": "", "source_url": "https://..."}\n'





        "  ],\n"





        '  "whitespace_search": "What you searched for self-serve SaaS and whether any were found",\n'





        '  "sources": ["https://..."]\n'





        "}\n\n"





        "Rules: minimum 6 named competitors across categories where they exist. "





        "If no self-serve SaaS exists, say so and list what you searched. Every entry needs source_url."





    )





def _financial_prompt(





    topic: str,





    industry: str,





    geography: str,





    research_block: str,





    sizing_block: str,





) -> str:





    return (





        f"You are a financial analyst (Claude Opus). Build TAM/SAM/SOM from the Perplexity research below.\n\n"





        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\n\n"





        f"GENERAL RESEARCH:\n{research_block[:6000]}\n\n"





        f"MARKET SIZING RESEARCH (Perplexity TAM/SAM/SOM search):\n{sizing_block[:8000]}\n\n"





        "Return STRICT JSON only:\n"





        "{\n"





        '  "tam": {"value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""},\n'





        '  "tam_alternatives": [\n'





        '    {"value": "", "scope": "domestic|global|niche", "source_url": "https://...", "notes": "why different from primary TAM"}\n'





        "  ],\n"





        '  "tam_reconciliation": "Explain when multiple TAM figures exist and which applies to this niche",\n'





        '  "sam": {"value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""},\n'





        '  "som": {"value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""},\n'





        '  "financial_rows": [\n'





        '    {"metric": "", "value": "", "label": "FACT|ESTIMATE|DERIVED|NOT FOUND", "source_url": "https://...", "source_name": "", "notes": ""}\n'





        "  ],\n"





        '  "illustrative_scenario": {\n'





        '    "title": "Optional worked example only",\n'





        '    "formula": "",\n'





        '    "result": "",\n'





        '    "label": "ILLUSTRATIVE ONLY"\n'





        "  },\n"





        '  "commentary": ["2-3 bullets on what figures mean for founders"]\n'





        "}\n\n"





        "RULES:\n"





        "1. Use ONLY numbers from the research above. Every value needs source_url or label NOT FOUND.\n"





        "2. If multiple TAM figures exist, pick ONE primary TAM for the niche and put others in tam_alternatives with tam_reconciliation.\n"





        "3. SAM/SOM must be NOT FOUND unless a sourced figure exists — do not smuggle hypotheticals into sam/som values.\n"





        "4. Hypothetical bottom-up math goes ONLY in illustrative_scenario with label ILLUSTRATIVE ONLY.\n"





        "5. Never use the word Validated — use FACT only with a tier-1/2 source_url."





    )





def _report_prompt(





    topic: str,





    industry: str,





    geography: str,





    research_block: str,





    competitor_block: str,





    financial_block: str,





) -> str:





    return (





        f"You are a market research writer (Claude Sonnet). Write a founder-ready report in markdown.\n\n"





        f"Topic: {topic}\nIndustry: {industry}\nMarket: {geography}\n\n"





        f"RESEARCH:\n{research_block[:5000]}\n\n"





        f"COMPETITOR RESEARCH:\n{competitor_block[:5000]}\n\n"





        f"FINANCIAL FIGURES (use these numbers only — do not invent others):\n{financial_block[:4000]}\n\n"





        "Return markdown only (no JSON, no code fences).\n\n"





        "Write these ## sections in order:\n"





        "Executive Summary, Market Overview, Competitive Landscape, Opportunities & Risks, Recommendations.\n\n"





        "Do NOT write a Financial Snapshot section — it is inserted separately with sourced tables.\n\n"





        "RULES:\n"





        "- Every number in prose MUST have an inline footnote [n] (Sources are appended automatically).\n"





        "- Never write 'Validated' without a footnote. Use FACT/ESTIMATE/DERIVED/NOT FOUND honestly.\n"





        "- End the report after ## Recommendations. Do not add market entry plans, revenue projections, or pricing models.\n"





        "- Competitive Landscape: cover at least 6 competitors from research — direct SaaS, global adjacents, and agencies.\n"





        "- If claiming whitespace/no self-serve competitor, cite the whitespace_search evidence.\n"





        "- Do not invent TAM/SAM/SOM — reference the financial figures block only.\n"





        "- Complete every section; do not stop mid-sentence."





    )





def _extract_report_body(report_api: dict[str, Any]) -> tuple[str, list[str]]:





    parsed = report_api.get("parsed") if isinstance(report_api.get("parsed"), dict) else {}





    body = str(parsed.get("report_markdown") or "").strip()





    sources = [str(u) for u in (parsed.get("sources") or []) if str(u).startswith("http")]





    if body:





        return body, sources





    raw = str(report_api.get("raw_content") or "").strip()





    if raw.startswith("```"):





        lines = raw.splitlines()





        if lines and lines[0].startswith("```"):





            lines = lines[1:]





        if lines and lines[-1].strip() == "```":





            lines = lines[:-1]





        raw = "\n".join(lines).strip()





    if raw.startswith("#"):





        return raw, sources





    return body, sources





def _format_financial_row(label: str, row: dict[str, Any]) -> str:





    if not row:





        return ""





    value = str(row.get("value") or "").strip()





    tag = str(row.get("label") or "").strip()





    notes = str(row.get("notes") or "").strip()





    url = str(row.get("source_url") or "").strip()





    name = str(row.get("source_name") or "").strip()





    line = f"- **{label}**: {value}"





    if tag:





        line += f" ({tag})"





    if notes:





        line += f" — {notes}"





    if url.startswith("http"):





        cite = name or _source_label(url)





        line += f" — [{cite}]({url})"





    return line





def _format_harvest_section(title: str, parsed: dict[str, Any], citations: list[str]) -> str:





    lines = [title]





    summary = str(parsed.get("research_summary") or parsed.get("whitespace_search") or "").strip()





    if summary:





        lines.append(f"SUMMARY: {summary}")





    list_keys = (





        "market_facts",





        "competitor_facts",





        "pricing_facts",





        "market_size_facts",





        "tam_candidates",





        "denominator_facts",





        "direct_saas_competitors",





        "adjacent_global_tools",





        "agency_or_services_competitors",
        "competitor_matrix",
        "landscape_summary",
        "competitive_gaps",
    )





    for key in list_keys:





        rows = parsed.get(key) if isinstance(parsed.get(key), list) else []





        if rows:





            lines.append(f"{key.upper()}:")





            for row in rows[:20]:





                if isinstance(row, dict):





                    lines.append(f"- {row}")





    if citations:





        lines.append("CITATIONS:")





        for url in citations[:20]:





            lines.append(f"- {url}")





    return "\n".join(lines).strip()





def _format_research_block(parsed: dict[str, Any], citations: list[str]) -> str:





    return _format_harvest_section("GENERAL RESEARCH", parsed, citations)





def _format_financial_block(parsed: dict[str, Any]) -> str:





    if not isinstance(parsed, dict):





        return ""





    lines = []





    for key in ("tam", "sam", "som"):





        row = parsed.get(key) if isinstance(parsed.get(key), dict) else {}





        formatted = _format_financial_row(key.upper(), row)





        if formatted:





            lines.append(formatted)





    alts = parsed.get("tam_alternatives") if isinstance(parsed.get("tam_alternatives"), list) else []





    if alts:





        lines.append("")





        lines.append("TAM alternatives:")





        for row in alts[:6]:





            if isinstance(row, dict):





                lines.append(





                    f"- {row.get('value', '')} ({row.get('scope', '')}) — {row.get('notes', '')} "





                    f"{row.get('source_url', '')}"





                )





    recon = str(parsed.get("tam_reconciliation") or "").strip()





    if recon:





        lines.append("")





        lines.append(f"TAM reconciliation: {recon}")





    rows = parsed.get("financial_rows") if isinstance(parsed.get("financial_rows"), list) else []





    if rows:





        lines.append("")





        lines.append("Other figures:")





        for row in rows[:12]:





            if isinstance(row, dict):





                metric = str(row.get("metric") or "Metric").strip()





                lines.append(_format_financial_row(metric, row))





    scenario = parsed.get("illustrative_scenario") if isinstance(parsed.get("illustrative_scenario"), dict) else {}





    if scenario and str(scenario.get("result") or scenario.get("formula") or "").strip():





        lines.append("")





        lines.append(f"Illustrative scenario ({scenario.get('label', 'ILLUSTRATIVE ONLY')}): {scenario}")





    commentary = parsed.get("commentary") or []





    if commentary:





        lines.append("")





        lines.append("Commentary:")





        for bullet in commentary:





            if str(bullet).strip():





                lines.append(f"- {bullet}")





    return "\n".join(lines).strip()





def _fallback_financial_from_sizing(parsed_sizing: dict[str, Any]) -> dict[str, Any]:





    """When Opus returns empty JSON, build financial block from Perplexity sizing harvest."""





    if not isinstance(parsed_sizing, dict) or not parsed_sizing:





        return {}





    tam: dict[str, Any] = {}





    sam: dict[str, Any] = {}





    som: dict[str, Any] = {}





    alts: list[dict[str, Any]] = []





    rows: list[dict[str, Any]] = []





    for fact in parsed_sizing.get("market_size_facts") or []:





        if not isinstance(fact, dict):





            continue





        metric = str(fact.get("metric") or "").upper()





        row = {





            "value": str(fact.get("value") or "[NOT FOUND]"),





            "label": "FACT" if str(fact.get("value") or "").strip() else "NOT FOUND",





            "source_url": str(fact.get("source_url") or ""),





            "source_name": str(fact.get("source_name") or ""),





            "notes": str(fact.get("notes") or fact.get("geography_scope") or ""),





        }





        rows.append({"metric": metric or "Figure", **row})





        if "TAM" in metric and not tam.get("value"):





            tam = row





        elif "SAM" in metric and not sam.get("value"):





            sam = row





        elif "SOM" in metric and not som.get("value"):





            som = row





    for cand in parsed_sizing.get("tam_candidates") or []:





        if not isinstance(cand, dict):





            continue





        alt = {





            "value": str(cand.get("value") or ""),





            "scope": str(cand.get("scope") or ""),





            "source_url": str(cand.get("source_url") or ""),





            "notes": str(cand.get("notes") or ""),





        }





        if alt["value"]:





            alts.append(alt)





        if not tam.get("value") and alt["value"]:





            tam = {





                "value": alt["value"],





                "label": "FACT",





                "source_url": alt["source_url"],





                "source_name": str(cand.get("source_name") or ""),





                "notes": f"Primary TAM candidate ({alt['scope']})",





            }





    for key, target in (("tam", tam), ("sam", sam), ("som", som)):





        if not target:





            target = {"value": "[NOT FOUND]", "label": "NOT FOUND", "source_url": "", "notes": "Not found in Perplexity sizing search"}





            if key == "tam":





                tam = target





            elif key == "sam":





                sam = target





            else:





                som = target





    recon = ""





    if len(alts) > 1:





        recon = "Multiple TAM figures found; primary TAM is the first niche-scoped figure. See alternate TAM table."





    elif alts and tam.get("value") and alts[0].get("value") != tam.get("value"):





        recon = f"Primary TAM ({tam.get('value')}) differs from alternate ({alts[0].get('value')}): {alts[0].get('notes', '')}"





    return {





        "tam": tam,





        "sam": sam,





        "som": som,





        "tam_alternatives": alts,





        "tam_reconciliation": recon,





        "financial_rows": rows,





        "illustrative_scenario": {},





        "commentary": [],





    }





def _trim_hallucinated_tail(body: str) -> str:





    """Remove continuation-pass junk (projections, market entry plans, etc.)."""





    s = str(body or "")





    cut_markers = [





        "\n# Market Research",





        "\n## Market Entry Strategy",





        "\n## Financial Projections",





        "\n## Competitive Positioning",





        "\n## Revenue Model",





        "\n### 3-Year Projections",





        "\n- Continued\n",





    ]





    for marker in cut_markers:





        idx = s.find(marker)





        if idx != -1:





            s = s[:idx].rstrip()





    if s and not s.rstrip().endswith((".", "!", "?", "`", '"', "]")):





        s = s.rstrip() + "\n\n_(Section may be incomplete — re-run if needed.)_"





    return s





def _clean_report_markers(body: str) -> str:





    return str(body or "").replace("[WHITESPACE]", "[see whitespace_search in competitor research]")





def _table_cell(text: str) -> str:





    return repair_spaced_text(str(text or "").strip().replace("|", "/").replace("\n", " "))





def _row_source_cite(row: dict[str, Any], registry: dict[str, int]) -> str:





    url = str(row.get("source_url") or "").strip()





    if not url.startswith("http"):





        return "—"





    if url not in registry:





        registry[url] = len(registry) + 1





    name = str(row.get("source_name") or "").strip() or _source_label(url)





    tier = classify_source_url(url)





    return f"[{registry[url]}] {name} ({tier}) — {url}"





def build_financial_snapshot_section(
    financial: dict[str, Any],
    geography: str = "",
) -> tuple[str, dict[str, int]]:





    registry: dict[str, int] = {}





    has_rows = isinstance(financial, dict) and any(





        isinstance(financial.get(k), dict) and str(financial.get(k, {}).get('value') or '').strip()





        for k in ('tam', 'sam', 'som')





    )





    if not has_rows:





        return "## Financial Snapshot\n\n| Metric | Value | Label | Source | Notes |\n| --- | --- | --- | --- | --- |\n| TAM | [NOT FOUND] | NOT FOUND | — | No sourced TAM in research |\n| SAM | [NOT FOUND] | NOT FOUND | — | No sourced SAM in research |\n| SOM | [NOT FOUND] | NOT FOUND | — | No sourced SOM in research |\n", registry





    lines = ["## Financial Snapshot", ""]

    cur = financial.get("currency") if isinstance(financial.get("currency"), dict) else {}
    if not cur.get("code") and geography:
        cur = currency_for_geography(geography)
    if cur.get("code"):
        lines.append(
            f"*All figures in **{cur.get('code')}** ({cur.get('symbol', '')}) — {cur.get('name', cur.get('code'))}*"
        )
        lines.append("")

    lines.extend(["### Primary market sizing", ""])





    lines.append("| Metric | Value | Label | Source | Notes |")





    lines.append("| --- | --- | --- | --- | --- |")





    for key in ("tam", "sam", "som"):





        row = financial.get(key) if isinstance(financial.get(key), dict) else {}





        if not row:





            continue





        lines.append(





            "| "





            + " | ".join(





                [





                    _table_cell(key.upper()),





                    _table_cell(row.get("value", "")),





                    _table_cell(row.get("label", "")),





                    _table_cell(_row_source_cite(row, registry)),





                    _table_cell(row.get("notes", "")),





                ]





            )





            + " |"





        )





    top_down = financial.get("top_down") if isinstance(financial.get("top_down"), dict) else {}
    bottom_up = financial.get("bottom_up") if isinstance(financial.get("bottom_up"), dict) else {}
    validation = financial.get("validation") if isinstance(financial.get("validation"), dict) else {}

    for method_title, block in (("Top-down method", top_down), ("Bottom-up method", bottom_up)):
        formula = str(block.get("formula") or "").strip()
        result = str(block.get("result") or "").strip()
        method = str(block.get("method") or "").strip()
        if not (formula or result or method):
            continue
        lines.extend(["", f"### {method_title}", ""])
        if method:
            lines.append(f"**Approach:** {repair_spaced_text(method)}")
        if formula:
            lines.append(f"**Formula:** {repair_spaced_text(formula)}")
        if result:
            lines.append(f"**Result:** {repair_spaced_text(result)}")
        label = str(block.get("label") or "").strip()
        notes = str(block.get("notes") or "").strip()
        if label:
            lines.append(f"**Label:** {label}")
        if notes:
            lines.append(f"**Notes:** {repair_spaced_text(notes)}")

    val_notes = str(validation.get("notes") or "").strip()
    td_res = str(validation.get("top_down_result") or "").strip()
    bu_res = str(validation.get("bottom_up_result") or "").strip()
    if td_res or bu_res or val_notes:
        lines.extend(["", "### Dual validation (top-down vs bottom-up)", ""])
        if td_res:
            lines.append(f"- **Top-down:** {repair_spaced_text(td_res)}")
        if bu_res:
            lines.append(f"- **Bottom-up:** {repair_spaced_text(bu_res)}")
        reconciled = validation.get("reconciled")
        if reconciled is not None:
            lines.append(f"- **Within 2×:** {'Yes' if reconciled else 'No — see notes'}")
        if val_notes:
            lines.append(f"- {repair_spaced_text(val_notes)}")

    alts = financial.get("tam_alternatives") if isinstance(financial.get("tam_alternatives"), list) else []





    if alts:





        lines.extend(["", "### Alternate TAM figures (reconciled)", ""])





        lines.append("| Value | Scope | Source | Why different |")





        lines.append("| --- | --- | --- | --- |")





        for row in alts[:6]:





            if not isinstance(row, dict):





                continue





            lines.append(





                "| "





                + " | ".join(





                    [





                        _table_cell(row.get("value", "")),





                        _table_cell(row.get("scope", "")),





                        _table_cell(_row_source_cite(row, registry)),





                        _table_cell(row.get("notes", "")),





                    ]





                )





                + " |"





            )





    recon = str(financial.get("tam_reconciliation") or "").strip()





    if recon:





        lines.extend(["", "### TAM reconciliation", "", repair_spaced_text(recon)])





    extra = financial.get("financial_rows") if isinstance(financial.get("financial_rows"), list) else []





    if extra:





        lines.extend(["", "### Other sourced figures", ""])





        lines.append("| Metric | Value | Label | Source | Notes |")





        lines.append("| --- | --- | --- | --- | --- |")





        for row in extra[:10]:





            if not isinstance(row, dict):





                continue





            lines.append(





                "| "





                + " | ".join(





                    [





                        _table_cell(row.get("metric", "")),





                        _table_cell(row.get("value", "")),





                        _table_cell(row.get("label", "")),





                        _table_cell(_row_source_cite(row, registry)),





                        _table_cell(row.get("notes", "")),





                    ]





                )





                + " |"





            )





    scenario = financial.get("illustrative_scenario") if isinstance(financial.get("illustrative_scenario"), dict) else {}





    if scenario and str(scenario.get("result") or scenario.get("formula") or "").strip():





        lines.extend(





            [





                "",





                "### Illustrative scenario (not market sizing data)",





                "",





                "> **ILLUSTRATIVE ONLY — do not cite as TAM/SAM/SOM**",





                f"> {repair_spaced_text(str(scenario.get('title') or 'Worked example'))}",





                f"> Formula: {repair_spaced_text(str(scenario.get('formula') or ''))}",





                f"> Result: {repair_spaced_text(str(scenario.get('result') or ''))}",





            ]





        )





    commentary = financial.get("commentary") if isinstance(financial.get("commentary"), list) else []

    if commentary:

        lines.extend(["", "### Investor takeaways", ""])

        for bullet in commentary[:5]:

            text = str(bullet or "").strip()

            if text:

                lines.append(f"- {repair_spaced_text(text)}")





    return "\n".join(lines).strip() + "\n", registry







def _plan_has_competitive_landscape(titles: list[str]) -> bool:
    return "Competitive Landscape" in (titles or [])


def _insert_competitive_landscape_section(body: str, section_md: str) -> str:
    """Replace or insert ## Competitive Landscape from dedicated write pass."""
    text = str(body or "").strip()
    section = str(section_md or "").strip()
    if not section:
        return text
    if not section.lstrip().startswith("##"):
        section = "## Competitive Landscape\n\n" + section
    pattern = r"^##\s+Competitive Landscape\b.*?(?=^##\s+|\Z)"
    if re.search(pattern, text, re.I | re.M | re.S):
        return re.sub(pattern, section.rstrip() + "\n\n", text, count=1, flags=re.I | re.M | re.S)
    for anchor in ("## Market Size & Valuation", "## Market Overview & Definition", "## Market Overview"):
        marker = re.search(rf"^{re.escape(anchor)}\b", text, re.I | re.M)
        if marker:
            nxt = re.search(r"^##\s+", text[marker.end() :], re.M)
            if nxt:
                pos = marker.end() + nxt.start()
                return text[:pos] + "\n\n" + section + "\n\n" + text[pos:]
    return text + "\n\n" + section

def _insert_financial_snapshot(body: str, financial_section: str, section_titles: list[str] | None = None) -> str:





    text = str(body or "").strip()





    if not text:





        return financial_section





    if re.search(r"^##\s+Financial Snapshot\b", text, re.I | re.M):





        return re.sub(





            r"^##\s+Financial Snapshot\b.*?(?=^##\s+|\Z)",





            financial_section.strip(),





            text,





            count=1,





            flags=re.I | re.M | re.S,





        )





    marker = re.search(r"^##\s+Competitive Landscape\b", text, re.I | re.M)





    if marker:





        return text[: marker.start()] + financial_section + "\n\n" + text[marker.start() :]





    marker = re.search(r"^##\s+Opportunities\b", text, re.I | re.M)





    if marker:





        return text[: marker.start()] + financial_section + "\n\n" + text[marker.start() :]





    return text + "\n\n" + financial_section





def _collect_urls(*chunks: Any) -> list[str]:





    urls: list[str] = []





    seen: set[str] = set()





    def _walk(obj: Any) -> None:





        if isinstance(obj, dict):





            for k, v in obj.items():





                if k in ("source_url", "url") and str(v).strip().startswith("http"):





                    u = str(v).strip()





                    if u not in seen:





                        seen.add(u)





                        urls.append(u)





                else:





                    _walk(v)





        elif isinstance(obj, list):





            for item in obj:





                _walk(item)





        elif isinstance(obj, str) and obj.strip().startswith("http"):





            u = obj.strip()





            if u not in seen:





                seen.add(u)





                urls.append(u)





    for chunk in chunks:





        _walk(chunk)





    return urls





def append_sources_section(body: str, urls: list[str], registry: dict[str, int] | None = None) -> str:





    text = str(body or "").rstrip()





    if re.search(r"^##\s+Sources\b", text, re.I | re.M):





        return text





    reg = dict(registry or {})





    for url in urls:





        if url not in reg:





            reg[url] = len(reg) + 1





    lines = ["", "## Sources", ""]





    for url in sorted(reg.keys(), key=lambda u: reg[u]):





        tier = classify_source_url(url)





        lines.append(f"[{reg[url]}] {_source_label(url)} ({tier}) — {url}")





    if len(lines) <= 3:





        lines.append("_No source URLs collected._")





    return text + "\n" + "\n".join(lines) + "\n"





def is_truncated(text: str) -> bool:





    s = str(text or "").strip()





    if not s:





        return True





    tail = s[-280:].strip()





    if tail.endswith((".", "!", "?", ")", "]", "`", '"')):





        return False





    if re.search(r"\b(A|An|The|To|For|If|When|While|Because|However|Although)\s*$", tail, re.I):





        return True





    return not tail.endswith((".", "!", "?"))





def _run_sonar_phase(





    *,





    prompt: str,





    phase: str,





    search_model: str,





    ledger: list[dict[str, Any]],





    traces: list[dict[str, Any]],





) -> dict[str, Any]:





    api = call_perplexity_json(prompt, model=search_model, timeout=120)





    trace = {"phase": phase, "model": search_model, "errors": []}





    if api.get("error"):





        trace["errors"].append(str(api["error"]))





        traces.append(trace)





        return {"error": api["error"], "trace": trace}





    row = perplexity_usage_row(api.get("usage"), model=str(api.get("model") or search_model), phase=phase)





    ledger.append(row)





    traces.append({**trace, "usage_ledger": row})





    parsed = api.get("parsed") if isinstance(api.get("parsed"), dict) else {}





    citations = [str(u).strip() for u in (api.get("citations") or []) if str(u).strip().startswith("http")]





    for u in parsed.get("sources") or []:





        if str(u).strip().startswith("http") and str(u) not in citations:





            citations.append(str(u))





    block = _format_harvest_section(phase.upper(), parsed, citations)





    if not block and api.get("raw_content"):





        block = str(api.get("raw_content") or "")[:8000]





    return {"parsed": parsed, "citations": citations, "block": block, "api": api}





def build_simple_markdown(





    topic: str,





    industry: str,





    geography: str,





    *,





    report_body: str,





    financial: dict[str, Any],





    runtime_sec: float,





    cost_usd: float,





) -> str:





    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")





    header = (





        f"# {topic}\n\n"





        f"- **Industry:** {industry}\n"





        f"- **Market:** {geography}\n"





        f"- **Generated:** {ts}\n"





        f"- **Prepared by:** IIDATECH Research\n\n"





        "---\n\n"





    )





    body = repair_spaced_text(str(report_body or "").strip()) or "_No report body returned._"





    return header + body + "\n"





def generate_simple_perplexity_report(





    topic: str,





    *,





    industry: str = "General",





    geography: str = "Global",





    areas: str = "",


    section_count: int = 3,





) -> dict[str, Any]:





    started = time.time()





    topic = str(topic or "").strip()





    industry = str(industry or "General").strip() or "General"





    market_label = format_market_geography(geography, areas)


    sections = normalize_section_count(section_count)


    plan = section_plan(sections)


    titles = section_titles(sections)


    budget = budget_for_sections(sections, base_budget=simple_report_budget_usd())





    if not topic:





        return {"success": False, "error": "Topic is required."}





    if not perplexity_enabled():





        return {"success": False, "error": "PERPLEXITY_API_KEY is not configured."}





    ledger: list[dict[str, Any]] = []





    traces: list[dict[str, Any]] = []





    warnings: list[str] = []





    search_model = report_search_model()





    # --- Phase 1: general research ---





    research = _run_sonar_phase(





        prompt=research_prompt(topic, industry, market_label),





        phase="sonar_research",





        search_model=search_model,





        ledger=ledger,





        traces=traces,





    )





    if research.get("error"):





        return {





            "success": False,





            "error": str(research["error"]),





            "traces": traces,





            "usage_ledger": ledger,





            "pipeline": "simple",





        }





    parsed_research = research.get("parsed") or {}





    research_block = str(research.get("block") or "")





    citations = list(research.get("citations") or [])





    # --- Phase 2: Perplexity TAM/SAM/SOM search ---





    sizing_block = ""





    parsed_sizing: dict[str, Any] = {}





    if _budget_ok(ledger, budget):





        sizing = _run_sonar_phase(





            prompt=financial_sizing_prompt(topic, industry, market_label),





            phase="sonar_market_sizing",





            search_model=search_model,





            ledger=ledger,





            traces=traces,





        )





        if sizing.get("error"):





            warnings.append(f"Market sizing search failed: {sizing['error']}")





        else:





            parsed_sizing = sizing.get("parsed") or {}





            sizing_block = str(sizing.get("block") or "")





            citations = list(dict.fromkeys(citations + list(sizing.get("citations") or [])))





    else:





        warnings.append(f"Skipped market sizing search — budget ${_ledger_cost(ledger):.3f}")





    # --- Phase 3: dedicated Perplexity Competitive Landscape research ---





    competitor_block = ""





    parsed_competitors: dict[str, Any] = {}





    if _budget_ok(ledger, budget):





        competitors = _run_sonar_phase(





            prompt=competitor_harvest_prompt(topic, industry, market_label),





            phase="sonar_competitive_landscape",





            search_model=search_model,





            ledger=ledger,





            traces=traces,





        )





        if competitors.get("error"):





            warnings.append(f"Competitor search failed: {competitors['error']}")





        else:





            parsed_competitors = competitors.get("parsed") or {}





            competitor_block = str(competitors.get("block") or "")





            citations = list(dict.fromkeys(citations + list(competitors.get("citations") or [])))





    else:





        warnings.append(f"Skipped competitor search — budget ${_ledger_cost(ledger):.3f}")





    financial_parsed: dict[str, Any] = {}





    # --- Phase 4: Opus financial synthesis ---





    if _budget_ok(ledger, budget):





        fin_model = report_financial_model()





        fin_api = call_anthropic_json(





            prompt=financial_opus_prompt(topic, industry, market_label, research_block, sizing_block),





            model=fin_model,





            max_tokens=2200,





            timeout=150,





        )





        fin_trace = {"phase": "opus_financial", "model": fin_model, "errors": []}





        if fin_api.get("error"):





            fin_trace["errors"].append(str(fin_api["error"]))





            warnings.append(f"Financial pass failed: {fin_api['error']}")





        else:





            fin_row = perplexity_usage_row(





                fin_api.get("usage"), model=str(fin_api.get("model") or fin_model), phase="opus_financial"





            )





            ledger.append(fin_row)





            fin_trace["usage_ledger"] = fin_row





            financial_parsed = fin_api.get("parsed") if isinstance(fin_api.get("parsed"), dict) else {}





            if not financial_parsed or not str((financial_parsed.get("tam") or {}).get("value") or "").strip():





                financial_parsed = _fallback_financial_from_sizing(parsed_sizing)





        traces.append(fin_trace)





    else:





        warnings.append(f"Skipped Opus financial pass — budget ${_ledger_cost(ledger):.3f}")





    financial_block = _format_financial_block(financial_parsed)





    financial_section, source_registry = build_financial_snapshot_section(financial_parsed, market_label)





    # --- Phase 5: Sonnet report ---





    report_parsed: dict[str, Any] = {}





    report_api: dict[str, Any] = {}





    if _budget_ok(ledger, budget):





        analyst_model = report_analyst_model()





        report_api = call_anthropic_json(





            prompt=report_sonnet_prompt(


                topic, industry, market_label, research_block, competitor_block, financial_block, plan


            ),





            model=analyst_model,





            max_tokens=sonnet_max_tokens(sections),





            timeout=200,





        )





        rep_trace = {"phase": "sonnet_report", "model": analyst_model, "errors": []}





        if report_api.get("error"):





            rep_trace["errors"].append(str(report_api["error"]))





            warnings.append(f"Report pass failed: {report_api['error']}")





        else:





            rep_row = perplexity_usage_row(





                report_api.get("usage"), model=str(report_api.get("model") or analyst_model), phase="sonnet_report"





            )





            ledger.append(rep_row)





            rep_trace["usage_ledger"] = rep_row





            report_parsed = report_api.get("parsed") if isinstance(report_api.get("parsed"), dict) else {}





        traces.append(rep_trace)





    else:





        warnings.append(f"Skipped Sonnet report pass — budget ${_ledger_cost(ledger):.3f}")





    report_body, report_sources = _extract_report_body(report_api)





    report_body = _clean_report_markers(_trim_hallucinated_tail(report_body))





    if not report_body and financial_block:





        report_body = research_block





    competitive_section_md = ""
    if _plan_has_competitive_landscape(titles) and _budget_ok(ledger, budget):
        competitive_api = call_anthropic_json(
            prompt=competitive_landscape_write_prompt(
                topic, industry, market_label, competitor_block
            ),
            model=report_analyst_model(),
            max_tokens=min(3500, sonnet_max_tokens(sections)),
            timeout=120,
        )
        comp_trace = {"phase": "sonnet_competitive_landscape", "model": report_analyst_model(), "errors": []}
        if competitive_api.get("error"):
            comp_trace["errors"].append(str(competitive_api["error"]))
            warnings.append(f"Competitive Landscape write failed: {competitive_api['error']}")
        else:
            comp_row = perplexity_usage_row(
                competitive_api.get("usage"),
                model=str(competitive_api.get("model") or report_analyst_model()),
                phase="sonnet_competitive_landscape",
            )
            ledger.append(comp_row)
            comp_trace["usage_ledger"] = comp_row
            competitive_section_md, _ = _extract_report_body(competitive_api)
            competitive_section_md = _clean_report_markers(_trim_hallucinated_tail(competitive_section_md))
        traces.append(comp_trace)
    elif _plan_has_competitive_landscape(titles):
        warnings.append(f"Skipped Competitive Landscape write — budget ${_ledger_cost(ledger):.3f}")

    report_body = _insert_competitive_landscape_section(report_body, competitive_section_md)
    report_body = _insert_financial_snapshot(report_body, financial_section, titles)





    all_urls = _collect_urls(





        citations,





        parsed_research,





        parsed_sizing,





        parsed_competitors,





        financial_parsed,





        report_sources,





    )





    report_body = append_sources_section(report_body, all_urls, source_registry)





    totals = sum_ledger(ledger, successful_only=True)





    cost_usd = float(totals.get("cost_usd") or _ledger_cost(ledger))





    runtime = round(time.time() - started, 1)





    over_budget = cost_usd > budget





    markdown = build_simple_markdown(





        topic,





        industry,





        market_label,





        report_body=report_body,





        financial=financial_parsed,





        runtime_sec=runtime,





        cost_usd=cost_usd,





    )





    if over_budget:





        warnings.append(f"Run exceeded budget cap (${cost_usd:.3f} > ${budget:.2f})")





    if is_truncated(report_body):





        warnings.append("Report may still be incomplete after continuation pass.")





    return {





        "success": bool(report_body.strip()),





        "pipeline": "simple",


        "section_count": sections,


        "section_titles": titles,


        "topic": topic,





        "industry": industry,





        "geography": geography,





        "areas": areas,





        "market_label": market_label,





        "report_markdown": markdown,





        "financial": financial_parsed,





        "research": parsed_research,





        "market_sizing": parsed_sizing,





        "competitors": parsed_competitors,





        "sources": all_urls,





        "runtime_sec": runtime,





        "estimated_cost_usd": round(cost_usd, 4),





        "budget_usd": budget,





        "within_budget": not over_budget,





        "usage_ledger": ledger,





        "usage_totals": totals,





        "traces": traces,





        "warnings": warnings,





        "models": {





            "research": search_model,





            "financial": report_financial_model(),





            "report": report_analyst_model(),





        },





        "error": None if report_body.strip() else "Report generation returned no content.",





    }





