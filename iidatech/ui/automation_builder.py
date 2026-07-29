"""Visual automation builder — pick steps, run with agent team queue."""
from __future__ import annotations

import hashlib
import time
from typing import Any

import streamlit as st

from iidatech.execution.agent_queue import (
    approve_pending_queue_items,
    ensure_automation_team,
    init_queue_from_spec,
    load_queue,
    process_next_queue_item,
    run_full_queue,
)
from iidatech.execution.automation_steps import (
    AUTOMATION_STEP_CATALOG,
    automation_report_id,
    build_spec_from_steps,
)
from iidatech.integrations.oauth_store import connection_status_rows
from iidatech.integrations.oauth_store import seed_workspace_from_env
from iidatech.execution.os2_api_keys import merge_api_keys
from iidatech.storage.execution_repository import list_team_messages


def _finalize_spec(spec: dict[str, Any], name: str) -> dict[str, Any]:
    rid = f"auto-{int(time.time() * 1000)}-{hashlib.sha1(name.encode('utf-8', errors='ignore')).hexdigest()[:8]}"
    spec["id"] = rid
    spec["name"] = name
    spec["created_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    spec["status"] = "Ready to run with agents"
    spec["simple_explanation"] = [
        "Employees run steps one at a time — others wait in line.",
        "External posts and emails pause for your approval.",
        "War room messages show who is working and who is blocked.",
    ]
    return spec


def render_automation_builder_section(
    idea: str,
    industry: str,
    geography: str,
    *,
    save_automation_spec,
    append_automation_chat,
    report_context: dict | None = None,
) -> None:
    st.markdown("#### Automation builder (pick your steps)")
    st.caption(
        "Choose what your virtual team should do. Taylor (COO) coordinates — "
        "each employee waits in line, messages the war room, and asks you before external actions."
    )

    report_id = automation_report_id(idea, geography)
    seed_workspace_from_env(report_id)
    api_keys = merge_api_keys()
    labels = [s["label"] for s in AUTOMATION_STEP_CATALOG]
    id_by_label = {s["label"]: s["id"] for s in AUTOMATION_STEP_CATALOG}
    queue = load_queue(report_id)
    has_queued_items = any(str(it.get("status")) == "queued" for it in (queue.get("items") or []))

    with st.container(border=True):
        picked_labels = st.multiselect(
            "Steps (in order)",
            options=labels,
            default=[labels[0], labels[1], labels[9]] if len(labels) > 9 else labels[:3],
            key="auto_builder_steps",
        )
        flow_name = st.text_input("Automation name", value="My company workflow", key="auto_builder_name")
        c1, c2 = st.columns(2)
        with c1:
            build_btn = st.button("Build automation from steps", type="primary", key="auto_builder_build")
        with c2:
            run_btn = st.button(
                "Run next step with agent team",
                key="auto_builder_run_step",
                disabled=not has_queued_items,
                help="Build automation from steps first — queue is empty." if not has_queued_items else None,
            )

        if build_btn and picked_labels:
            step_ids = [id_by_label[l] for l in picked_labels if l in id_by_label]
            spec = build_spec_from_steps(step_ids, idea=idea, industry=industry, geography=geography, name=flow_name)
            spec = _finalize_spec(spec, flow_name)
            save_automation_spec(idea, geography, spec)
            ensure_automation_team(report_id, topic=idea, industry=industry, geography=geography)
            init_queue_from_spec(report_id, spec)
            append_automation_chat(idea, geography, "assistant", f"Built **{flow_name}** with {len(step_ids)} steps. Employees are queued.", spec["id"])
            st.session_state["active_automation_artifact_id"] = spec["id"]
            st.success("Automation built — approve and run below, or use Run next step.")
            st.rerun()

        if run_btn and has_queued_items:
            ensure_automation_team(report_id, topic=idea, industry=industry, geography=geography)
            ctx = dict(report_context or {})
            ctx["_step_defs"] = list(AUTOMATION_STEP_CATALOG)
            step = process_next_queue_item(
                report_id,
                idea=idea,
                industry=industry,
                geography=geography,
                api_keys=api_keys,
                report_context=ctx,
            )
            if step.get("needs_approval"):
                st.warning("Paused — an employee needs your approval for an external action.")
            elif step.get("done"):
                st.info(step.get("message", "Queue done."))
            else:
                st.success(f"Step finished: {step.get('item', {}).get('label', '')}")
            st.rerun()

    with st.expander("Connector status (Gmail, LinkedIn, HubSpot)", expanded=False):
        rows = connection_status_rows(report_id)
        if rows:
            st.dataframe(rows, hide_index=True, width="stretch")
        else:
            st.caption("Connect apps in Employee OS 2 → Integrations tab.")
        missing = [r for r in rows if str(r.get("Status") or "").lower() != "connected"]
        if missing:
            st.warning("Some connectors are not connected — read/load steps may fail until you authorize.")

    queue = load_queue(report_id)
    items = queue.get("items") or []
    if items:
        st.markdown("**Agent queue**")
        waiting_founder = [it for it in items if str(it.get("status")) == "needs_founder"]
        if waiting_founder:
            st.warning(f"{len(waiting_founder)} step(s) paused for your approval.")
            if st.button("Approve external step & continue", key="auto_builder_approve_ext", type="primary"):
                approve_pending_queue_items(report_id)
                ctx = dict(report_context or {})
                ctx["_step_defs"] = list(AUTOMATION_STEP_CATALOG)
                process_next_queue_item(
                    report_id,
                    idea=idea,
                    industry=industry,
                    geography=geography,
                    api_keys=api_keys,
                    report_context=ctx,
                    auto_approve_external=True,
                )
                st.rerun()
        for it in items:
            icon = {"queued": "⏳", "running": "▶", "completed": "✓", "needs_founder": "🛑", "failed": "✗"}.get(str(it.get("status")), "·")
            st.write(f"{icon} **{it.get('role')}** — {it.get('label')} — _{it.get('status')}_")
            if it.get("result"):
                st.caption(str(it.get("result"))[:240])

    st.markdown("**Team war room (live messages)**")
    msgs = list_team_messages(report_id, limit=12)
    if not msgs:
        st.caption("No team messages yet — build an automation and run a step.")
    for m in reversed(msgs):
        who = str(m.get("sender_id") or "Team")
        st.write(f"**{who}:** {str(m.get('message') or '')[:400]}")


def run_agent_queue_for_spec(
    spec: dict,
    idea: str,
    industry: str,
    geography: str,
    report_context: dict | None = None,
) -> list[dict[str, Any]]:
    report_id = automation_report_id(idea, geography)
    ensure_automation_team(report_id, topic=idea, industry=industry, geography=geography)
    if spec.get("picked_steps"):
        init_queue_from_spec(report_id, spec)
    ctx = dict(report_context or {})
    ctx["_step_defs"] = list(spec.get("picked_steps") or AUTOMATION_STEP_CATALOG)
    return run_full_queue(
        report_id,
        idea=idea,
        industry=industry,
        geography=geography,
        api_keys=merge_api_keys(),
        report_context=ctx,
    )