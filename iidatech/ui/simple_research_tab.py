"""Primary market research tab — Perplexity + Claude, 3/8/16/25 sections."""
from __future__ import annotations
from typing import Any
from iidatech.evidence_bank.perplexity_client import (
    perplexity_enabled,
    report_analyst_model,
    report_financial_model,
    report_search_model,
)
from iidatech.services.perplexity_report_engine import format_market_geography
from iidatech.services.report_section_plans import SIMPLE_SECTION_COUNTS, section_plan, section_titles
from iidatech.services.simple_perplexity_report import generate_simple_perplexity_report, simple_report_budget_usd
from iidatech.services.report_section_plans import budget_for_sections
from iidatech.ui.frontend_brand import brand_frontend_text, market_research_download_filename

def render_simple_research_tab(st, topic, industry, geography, scope_assessment=None, *, areas=""):
    scope_ok = bool((scope_assessment or {}).get("ok", True))
    market_label = format_market_geography(geography, areas)
    st.markdown("#### Market research report")
    section_count = st.radio(
        "Report depth (sections)",
        options=list(SIMPLE_SECTION_COUNTS),
        format_func=lambda n: f"{n} sections — {', '.join(section_titles(n)[:3])}{'…' if n > 3 else ''}",
        horizontal=True,
        key="primary_report_section_count",
    )
    budget = budget_for_sections(section_count, base_budget=simple_report_budget_usd())
    plan = section_plan(section_count)
    st.caption(
        f"Boardroom- and funding-ready report via **{report_search_model()}** (research + sizing + competitors) → "
        f"**{report_financial_model()}** (TAM/SAM/SOM) → **{report_analyst_model()}** ({section_count} sections). "
        f"Budget cap **${budget:.2f}**. Market: **{market_label}**."
    )
    with st.expander("Sections included", expanded=False):
        for i, title in enumerate(section_titles(section_count), 1):
            st.markdown(f"{i}. {title}")
    if not perplexity_enabled():
        st.error("Set PERPLEXITY_API_KEY in `.env` to use this tab.")
        return
    if not scope_ok:
        st.warning("Narrow the topic in the fields above before generating.")
    col_run, col_dl = st.columns([1, 1])
    run = col_run.button(
        "Generate report",
        type="primary",
        use_container_width=True,
        disabled=not scope_ok or not str(topic or "").strip(),
        key="primary_generate_report_btn",
    )
    if run:
        with st.spinner(f"Building {section_count}-section report (cap ${budget:.2f})…"):
            result = generate_simple_perplexity_report(
                topic,
                industry=industry,
                geography=geography,
                areas=areas,
                section_count=section_count,
            )
        st.session_state["last_simple_report"] = result
        if not result.get("success"):
            st.error(brand_frontend_text(str(result.get("error") or "Report failed.")))
            if result.get("traces"):
                with st.expander("Trace", expanded=False):
                    st.json(result["traces"])
            return
    result = st.session_state.get("last_simple_report")
    if not isinstance(result, dict):
        return
    if str(result.get("topic") or "").strip() != str(topic or "").strip():
        return
    if int(result.get("section_count") or 0) != int(section_count):
        return
    if not result.get("success"):
        return
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sections", section_count)
    m2.metric("Est. cost", f"${float(result.get('estimated_cost_usd') or 0):.3f}")
    m3.metric("Budget cap", f"${budget:.2f}")
    m4.metric("Within budget", "Yes" if result.get("within_budget", True) else "No")
    totals = result.get("usage_totals") if isinstance(result.get("usage_totals"), dict) else {}
    if totals:
        st.caption(f"{totals.get('calls', 0)} API calls · {totals.get('total_tokens', 0):,} tokens")
    ledger = result.get("usage_ledger") or []
    if ledger:
        with st.expander("Cost by pass", expanded=False):
            for row in ledger:
                st.markdown(f"- **{row.get('phase')}** · {row.get('model')}: ${float(row.get('cost_usd') or 0):.4f}")
    for warn in result.get("warnings") or []:
        st.warning(str(warn)[:400])
    with col_dl:
        st.download_button(
            "Download report (Markdown)",
            data=brand_frontend_text(str(result.get("report_markdown") or "")),
            file_name=market_research_download_filename(topic).replace("MarketResearch", "MarketReport"),
            mime="text/markdown",
            use_container_width=True,
            key="primary_report_download",
        )
    st.markdown(brand_frontend_text(str(result.get("report_markdown") or "")))
