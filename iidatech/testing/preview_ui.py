"""Streamlit UI helpers for manual product preview."""
from __future__ import annotations

import json
from typing import Any

from iidatech.testing.manual_preview import disable_manual_preview, enable_manual_preview, is_manual_preview


def sync_manual_preview_toggle(enabled: bool) -> None:
    if enabled:
        enable_manual_preview()
    else:
        disable_manual_preview()


def render_manual_preview_banner(st: Any) -> bool:
    active = is_manual_preview()
    if active:
        st.info(
            "**Manual preview mode** — LLM calls are mocked. Reports use deterministic research/V3/business data. "
            "Set `IIDATECH_MANUAL_PREVIEW=0` or uncheck the toggle to run live synthesis."
        )
    return active


def render_product_preview(st: Any, result: dict[str, Any]) -> None:
    if not result or not result.get("success"):
        st.error("Preview failed to generate.")
        return

    st.subheader("Product preview (zero API cost)")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Score", result.get("report_score", "—"))
    m2.metric("Domain", result.get("routed_domain") or "—")
    m3.metric("Runtime", f"{result.get('runtime_sec', 0)}s")
    m4.metric("Team", result.get("employee_team_size", 0))

    tabs = st.tabs(["Customer report (V3)", "Business plan", "Execution", "Employees", "Raw JSON"])

    with tabs[0]:
        from iidatech.ui.plain_render import prepend_degradation_banner

        st.markdown(prepend_degradation_banner(result.get("report_v3_markdown") or "_No V3 markdown_", result))

    with tabs[1]:
        bp = result.get("business_blueprint") or {}
        st.markdown(f"**Wedge:** {(bp.get('positioning') or {}).get('statement') or bp.get('value_proposition', '—')}")
        mo = bp.get("market_opportunity") or {}
        st.markdown(f"**TAM (preview):** {mo.get('tam', '—')}")
        st.json(bp)

    with tabs[2]:
        ex = result.get("execution_blueprint") or {}
        p0 = ex.get("phase_0_validation") or {}
        tasks = p0.get("daily_tasks") or []
        if tasks:
            st.markdown("**Week 1 tasks**")
            for t in tasks[:8]:
                st.markdown(f"- {t.get('task') if isinstance(t, dict) else t}")
        cal = (result.get("report_v3") or {}).get("execution_calendar") or {}
        if cal:
            st.markdown("**Execution calendar**")
            for key in ("week_1", "week_2", "week_3", "month_2", "month_3", "month_6"):
                block = cal.get(key) or {}
                if block:
                    st.markdown(f"**{key.replace('_', ' ').title()}** — {block.get('focus', '')}")
        st.json(ex)

    with tabs[3]:
        cycle = result.get("employee_cycle") or {}
        report_id = f"preview_{abs(hash((result.get('topic') or '') + (result.get('geography') or ''))) % 10_000_000}"
        try:
            from iidatech.ui.workspace import render_employee_os
            render_employee_os(st, report_id, employee_cycle=cycle, report_v3=result.get("report_v3"))
        except Exception as exc:
            st.warning(f"Employee OS UI unavailable: {exc}")
            brief = cycle.get("founder_brief") or {}
            if brief.get("recommendations"):
                st.markdown("**Founder brief recommendations**")
                for r in brief["recommendations"]:
                    st.markdown(f"- {r}")

    with tabs[4]:
        st.code(json.dumps({
            "routed_domain": result.get("routed_domain"),
            "report_score": result.get("report_score"),
            "boardroom": result.get("boardroom"),
        }, indent=2), language="json")
