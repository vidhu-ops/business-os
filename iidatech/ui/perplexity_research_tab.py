"""Streamlit tab: IIDATECH direct market research reports."""
from __future__ import annotations

from typing import Any

from iidatech.evidence_bank.perplexity_client import perplexity_enabled, report_perplexity_model, report_search_model
from iidatech.evidence_bank.statista_client import statista_enabled, statista_mode
from iidatech.llm.anthropic_report import analyst_model, financial_model
from iidatech.services.perplexity_report_engine import (
    FRAMEWORKS_ENABLED,
    build_report_plan,
    extension_section_count,
    format_market_geography,
    generate_perplexity_report,
    to_business_report_context,
)
from iidatech.ui.frontend_brand import brand_frontend_text, market_research_download_filename


def _topic_key(value: Any) -> str:
    return str(value or "").strip()


def _store_report_attempt(st: Any, result: dict[str, Any]) -> None:
    if not isinstance(result, dict):
        return
    st.session_state["last_perplexity_report"] = result
    if result.get("success"):
        st.session_state["business_builder_current_report_context"] = to_business_report_context(result)


def _render_report_failure(st: Any, result: dict[str, Any]) -> None:
    err = str(result.get("error") or "Market research failed.")
    traces = result.get("perplexity_traces") or []
    for trace in traces:
        for item in trace.get("errors") or []:
            text = str(item)
            if "401" in text or "Unauthorized" in text:
                err = (
                    "Perplexity rejected your API key (401 Unauthorized). "
                    "Create a new key at perplexity.ai/settings/api and set PERPLEXITY_API_KEY in `.env`, then restart the app."
                )
                break
    st.error(brand_frontend_text(err))
    if traces:
        with st.expander("Research trace (technical)", expanded=False):
            st.json(traces)


def _sync_report_to_business_builder(st: Any, result: dict[str, Any]) -> None:
    _store_report_attempt(st, result)


def render_market_research_download(st: Any, result: dict[str, Any], *, key_suffix: str = "main") -> None:
    if not isinstance(result, dict) or not result.get("success"):
        return
    markdown = brand_frontend_text(str(result.get("report_markdown") or ""))
    topic = str(result.get("topic") or "market")
    st.download_button(
        "Download IIDATECH market research (Markdown)",
        data=markdown,
        file_name=market_research_download_filename(topic),
        mime="text/markdown",
        use_container_width=True,
        key=f"iidatech_market_research_download_{key_suffix}",
    )


def render_perplexity_research_tab(
    st: Any,
    topic: str,
    industry: str,
    geography: str,
    scope_assessment: dict | None = None,
    *,
    areas: str = "",
) -> None:
    scope_ok = bool((scope_assessment or {}).get("ok", True))
    market_label = format_market_geography(geography, areas)
    ext = extension_section_count()
    st.markdown("#### Report depth")
    st.caption(
        f"**{report_search_model()}** harvests financial + competitor facts (live search); "
        f"**Statista** ({'on' if statista_enabled() else 'off — set STATISTA_API_KEY'}) "
        f"adds licensed data via `{statista_mode()}`; "
        f"**Gitnux** adds matched benchmark stats when available; "
        f"**{financial_model()}** builds all financial figures + commentary; "
        f"**{analyst_model()}** builds competitor sections; "
        f"**{report_perplexity_model()}** drafts qualitative narrative only (no numbers). "
        f"Market: **{market_label}**. Framework packs are temporarily unavailable."
    )
    if not perplexity_enabled():
        st.error("Set PERPLEXITY_API_KEY in .env to use this tab.")
        return
    if not scope_ok:
        st.warning("Narrow the topic in the fields above before generating.")

    depth = st.radio(
        "Core section depth",
        options=[3, 6, 16, 25],
        index=1,
        horizontal=True,
        format_func=lambda n: f"{n} core sections",
        key="perplexity_section_depth",
    )
    include_financial = st.checkbox(
        "Include financial data table (Opus pass — figures only)",
        value=True,
        key="perplexity_include_financial_table",
        help="Claude Opus (via Perplexity) pulls TAM/pricing/unit-economics into a labeled table scoped to your topic.",
    )
    if FRAMEWORKS_ENABLED:
        include_extensions = st.checkbox(
            f"Add market-ready frameworks (+{ext} sections: Porter, SWOT, G2/Reddit trends, etc.)",
            value=False,
            key="perplexity_include_extensions",
        )
    else:
        include_extensions = False
        st.info("Market-ready framework pack (Porter, SWOT, G2/Reddit, etc.) is temporarily unavailable.")
    plan = build_report_plan(
        int(depth),
        include_extensions=include_extensions,
        include_financial_table=include_financial,
    )
    with st.expander(f"All {len(plan)} sections included", expanded=False):
        for row in plan:
            subs = ", ".join(str(s) for s in (row.get("sub") or [])[:4])
            st.markdown(f"- **{row['id']}. {row['title']}** — {subs}")

    col_run, col_dl = st.columns([1, 1])
    run = col_run.button(
        "Generate IIDATECH market research",
        type="primary",
        use_container_width=True,
        disabled=not scope_ok or not str(topic or "").strip(),
        key="perplexity_generate_report_btn",
    )

    if run:
        total = len(plan)
        with st.spinner(f"Researching {total} sections — may take several minutes..."):
            result = generate_perplexity_report(
                topic,
                industry=industry,
                geography=geography,
                areas=areas,
                section_count=int(depth),
                include_extensions=include_extensions,
                include_financial_table=include_financial,
            )
        _sync_report_to_business_builder(st, result)
        if not result.get("success"):
            _render_report_failure(st, result)
            return

    result = st.session_state.get("last_perplexity_report")
    if not isinstance(result, dict) or _topic_key(result.get("topic")) != _topic_key(topic):
        return

    if not result.get("success"):
        _render_report_failure(st, result)
        return

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Sections delivered", f"{result.get('sections_written', 0)}/{result.get('sections_planned', result.get('section_count', 0))}")
    m2.metric("Runtime", f"{result.get('runtime_sec', 0)}s")
    cost = result.get("estimated_cost_usd")
    m3.metric("Est. API cost", f"${cost:.3f}" if cost else "n/a")
    totals = result.get("usage_totals") if isinstance(result.get("usage_totals"), dict) else {}
    m4.metric("Total tokens", f"{totals.get('total_tokens', 0):,}" if totals.get("total_tokens") else "n/a")

    ledger = result.get("usage_ledger") or []
    if ledger:
        with st.expander("Token usage by pass (live API)", expanded=True):
            for row in ledger:
                st.markdown(
                    f"- **{row.get('phase')}** · {row.get('provider')}/{row.get('model')}: "
                    f"in={row.get('input_tokens', 0):,} out={row.get('output_tokens', 0):,} "
                    f"→ ${float(row.get('cost_usd') or 0):.4f}"
                )
            if totals:
                st.caption(
                    f"Sum: {totals.get('calls', 0)} calls · "
                    f"{totals.get('input_tokens', 0):,} in / {totals.get('output_tokens', 0):,} out · "
                    f"${float(totals.get('cost_usd') or 0):.4f}"
                )

    if result.get("areas"):
        st.caption(f"Local focus: **{result.get('areas')}** within **{result.get('geography')}**")

    partial_success = bool(result.get("partial_success"))
    if partial_success:
        st.warning(
            "Report is **partial**: the Perplexity draft completed, but the Opus financial pass and/or "
            "Sonnet analyst commentary did not run. Check your Perplexity balance and regenerate."
        )

    projected = result.get("projected_cost_usd")
    projected_total = None
    if isinstance(projected, dict):
        projected_total = projected.get("total_if_secondary_passes_ok") or projected.get("total_if_anthropic_ok")
    if isinstance(projected, dict) and projected_total:
        st.caption(
            f"Projected full 3-pass cost (when Opus/Sonnet passes succeed): "
            f"**${float(projected_total):.3f}** "
            f"(measured draft ${float(result.get('estimated_cost_usd') or 0):.3f} "
            f"+ projected Opus/Sonnet ${float(projected.get('opus_financial_figures', 0)) + float(projected.get('sonnet_analyst_commentary', 0)):.3f})"
        )

    for warn in result.get("warnings") or []:
        if "credit balance is too low" in str(warn).lower():
            continue
        st.warning(str(warn)[:500])

    with col_dl:
        render_market_research_download(st, result, key_suffix="tab")

    st.caption("Attached automatically when you build a business plan for the same topic.")
    st.markdown(brand_frontend_text(str(result.get("report_markdown") or "")))
