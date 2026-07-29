"""Employee OS 2 — multi-provider API keys + harnessed agents."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from iidatech.execution.employee_os2_harness import OS2_HARNESSES, execute_harness_job, harness_by_id, merged_harnesses
from iidatech.ui.os2_command_center import (
    ensure_os2_team,
    load_custom_harnesses,
    render_command_center,
    render_company_memory,
    render_custom_harness_builder,
    render_integrations_guide,
    render_team_hiring,
    render_war_room,
)
from iidatech.ui.os2_approvals import render_founder_chat, render_os2_approvals
from iidatech.ui.os2_office import render_office
from iidatech.ui.os2_scope_picker import render_workspace_mode_tabs
from iidatech.ui.os2_setup_requirements import render_setup_requirements
from iidatech.execution.office_scope import OfficeScope, filter_harnesses
from iidatech.ui.os2_team_leader import handle_oauth_redirect, render_oauth_connections, render_team_leader
from iidatech.execution.session_api_keys import (
    SUPPORTED_PROVIDERS,
    detect_provider,
    normalize_keys,
    provider_label,
    provider_portal_url,
)
from iidatech.execution.os2_api_keys import merge_api_keys
from iidatech.execution.plan_ingest import get_session_business_plan


def _report_id(topic: str, geography: str) -> str:
    raw = f"{topic}|{geography}".strip().lower()
    return f"os2_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


def _chat_key(harness_id: str) -> str:
    return f"os2_chat_{harness_id}"


_OS2_TABS_FULL: list[tuple[str, str]] = [
    ("office", "The Office"),
    ("tasks", "Tasks & approvals"),
    ("war_room", "War room"),
    ("command", "Command center"),
    ("agents", "Agents & team"),
    ("integrations", "Integrations"),
    ("advanced", "Advanced"),
]
_OS2_TABS_DEPARTMENT: list[tuple[str, str]] = [
    ("office", "Department office"),
    ("tasks", "Task queue"),
    ("agents", "Department agents"),
    ("integrations", "Setup & connect"),
]
_OS2_TABS_EMPLOYEE: list[tuple[str, str]] = [
    ("agents", "Employee chat"),
    ("tasks", "Their tasks"),
    ("integrations", "Setup & connect"),
]
_OS2_TABS = _OS2_TABS_FULL
_OS2_TAB_LABELS = {key: label for key, label in _OS2_TABS_FULL}


def _os2_tab_key(report_id: str, scope_mode: str = "full_office") -> str:
    return f"os2_tab_{scope_mode}_{report_id}"


def _os2_nav_tab_key(report_id: str, scope_mode: str = "full_office") -> str:
    return f"os2_nav_tab_{scope_mode}_{report_id}"


def _os2_focus_harness_key(report_id: str) -> str:
    return f"os2_focus_harness_{report_id}"


def _resolve_os2_tab(st: Any, report_id: str, scope_mode: str, tabs: list[tuple[str, str]]) -> str:
    """Return active workspace tab; honors one-shot navigation from Taylor bubble."""
    tab_key = _os2_tab_key(report_id, scope_mode)
    nav_key = _os2_nav_tab_key(report_id, scope_mode)
    if nav_key in st.session_state:
        st.session_state[tab_key] = st.session_state.pop(nav_key)
    valid = {key for key, _ in tabs}
    if tab_key not in st.session_state or st.session_state[tab_key] not in valid:
        st.session_state[tab_key] = tabs[0][0]
    return str(st.session_state[tab_key])


def _tabs_for_scope(scope: OfficeScope) -> list[tuple[str, str]]:
    if scope.mode == "employee":
        return _OS2_TABS_EMPLOYEE
    if scope.mode == "department":
        return _OS2_TABS_DEPARTMENT
    return _OS2_TABS_FULL


def _render_os2_tab_nav(st: Any, report_id: str, scope: OfficeScope) -> str:
    tabs = _tabs_for_scope(scope)
    tab_key = _os2_tab_key(report_id, scope.mode)
    labels = {key: label for key, label in tabs}
    _resolve_os2_tab(st, report_id, scope.mode, tabs)
    st.markdown("#### Step 2 — Work in your workspace")
    st.segmented_control(
        "Workspace section",
        options=[key for key, _ in tabs],
        format_func=lambda k: labels[k],
        key=tab_key,
        label_visibility="collapsed",
    )
    return str(st.session_state.get(tab_key) or tabs[0][0])


def _build_report_context(topic: str, industry: str, geography: str, st: Any) -> dict[str, Any]:
    areas = str(st.session_state.get("workspace_areas") or st.session_state.get("business_builder_areas") or "").strip()
    try:
        from iidatech.services.perplexity_report_engine import format_market_geography

        market_label = format_market_geography(geography, areas)
    except Exception:
        market_label = geography
    ctx: dict[str, Any] = {
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "country": geography,
        "areas": areas,
        "market_label": market_label,
    }
    plan = get_session_business_plan(st)
    if isinstance(plan, dict) and plan:
        ctx["business_plan"] = plan
    px = st.session_state.get("last_perplexity_report")
    if isinstance(px, dict) and px.get("success"):
        ctx["evidence_gaps"] = list(px.get("evidence_gaps") or [])
        ctx["report_markdown"] = str(px.get("report_markdown") or "")[:8000]
        ctx["report_v3"] = px
        try:
            from iidatech.services.perplexity_report_engine import competitor_truth_from_report

            ctx["competitor_truth"] = competitor_truth_from_report(px)
        except Exception:
            pass
    bb = st.session_state.get("business_builder_current_report_context")
    if isinstance(bb, dict) and bb.get("topic"):
        ctx.setdefault("topic", bb.get("topic"))
    return ctx


def _collect_api_keys(st: Any) -> tuple[dict[str, str], str, dict[str, str]]:
    main_key = str(st.session_state.get("os2_api_key") or "").strip()
    provider = str(st.session_state.get("os2_api_provider") or "auto").strip().lower()
    extra: dict[str, str] = {}
    for prov in SUPPORTED_PROVIDERS:
        val = str(st.session_state.get(f"os2_extra_key_{prov}") or "").strip()
        if val:
            extra[prov] = val
    keys = merge_api_keys(normalize_keys(main_key, provider=provider, extra=extra))
    detected = detect_provider(main_key) if main_key else ""
    primary = provider if provider not in {"", "auto"} else (detected or "custom")
    config: dict[str, str] = {}
    custom_base = str(st.session_state.get("os2_custom_base_url") or "").strip()
    custom_model = str(st.session_state.get("os2_custom_model") or "").strip()
    if custom_base:
        config["custom_base_url"] = custom_base
    if custom_model:
        config["custom_model"] = custom_model
    return keys, primary, config


def _render_agents_workspace(
    st: Any,
    *,
    report_id: str,
    topic: str,
    industry: str,
    geography: str,
    report_context: dict[str, Any],
    harnesses: list[dict[str, Any]],
    show_api_keys: bool = True,
    scope: OfficeScope | None = None,
) -> None:
    if show_api_keys:
        with st.container(border=True):
            keys_preview, _, _ = _collect_api_keys(st)
            if keys_preview:
                st.success("Active: " + ", ".join(keys_preview.keys()))
            else:
                st.warning("Add API keys in the expander at the top of this page.")

    keys, _, api_config = _collect_api_keys(st)
    scope = scope or OfficeScope()
    harnesses = filter_harnesses(harnesses, scope)
    if not harnesses and not scope.is_full_office():
        st.warning("No employees match your scope. Adjust the selector above or switch to **Full office**.")
        return
    harness_ids = [h["id"] for h in harnesses]
    labels = {h["id"]: h["name"] for h in harnesses}
    focus = st.session_state.get(_os2_focus_harness_key(report_id))
    if focus and focus in harness_ids:
        harness_ids = [focus] + [h for h in harness_ids if h != focus]
        st.info(f"Taylor routed you to **{labels[focus]}** — your task is ready below.")
    tabs = st.tabs([labels[hid] for hid in harness_ids])
    for tab, hid in zip(tabs, harness_ids):
        harness = harness_by_id(hid, harnesses) or {}
        with tab:
            st.markdown(f"**{harness.get('tagline', '')}**")
            chat = st.session_state.setdefault(_chat_key(hid), [])
            for turn in chat:
                with st.chat_message("user" if turn.get("role") == "user" else "assistant"):
                    if turn.get("role") == "user":
                        st.markdown(str(turn.get("content") or ""))
                    else:
                        from iidatech.ui.os2_deliverable_view import (
                            clean_harness_reply_for_display,
                            render_artifact_downloads,
                            render_deliverable_preview,
                        )

                        reply = str(turn.get("content") or "")
                        arts = list(turn.get("artifacts") or [])
                        summary = clean_harness_reply_for_display(reply)
                        if summary:
                            st.markdown(summary)
                        if arts:
                            render_deliverable_preview(
                                st,
                                title=labels[hid],
                                reply=reply,
                                artifacts=arts,
                                key_prefix=f"os2_chat_{hid}_{hash(str(turn)) % 10**5}",
                            )
                            render_artifact_downloads(st, arts, key_prefix=f"os2_raw_{hid}")
            starters = harness.get("starters") or []
            if starters:
                scols = st.columns(min(3, len(starters)))
                for i, starter in enumerate(starters[:3]):
                    if scols[i].button(starter[:40] + ("..." if len(starter) > 40 else ""), key=f"os2_starter_{hid}_{i}"):
                        st.session_state[f"os2_pending_{hid}"] = starter
                        st.rerun()
            pending = st.session_state.pop(f"os2_pending_{hid}", None)
            prompt = st.chat_input(f"Tell {labels[hid]} what to deliver...", key=f"os2_chat_input_{hid}")
            user_msg = pending or prompt
            if user_msg:
                chat.append({"role": "user", "content": user_msg})
                with st.spinner(f"{labels[hid]} working..."):
                    result = execute_harness_job(
                        hid, user_msg, report_id=report_id, api_keys=keys, api_config=api_config,
                        extra_harnesses=harnesses, report_context=report_context,
                    )
                try:
                    from iidatech.execution.os2_team_bridge import notify_task_completion

                    notify_task_completion(
                        report_id,
                        {
                            "harness_id": hid,
                            "title": str(user_msg)[:120],
                            "status": "completed" if result.get("success") else "failed",
                            "task_kind": "harness",
                            "artifacts": list(result.get("artifacts") or []),
                            "error": "" if result.get("success") else str(result.get("reply") or ""),
                        },
                        result,
                        report_context=report_context,
                    )
                except Exception:
                    pass
                chat.append({"role": "assistant", "content": str(result.get("reply") or "Done."), "artifacts": list(result.get("artifacts") or [])})
                st.session_state[_chat_key(hid)] = chat
                st.rerun()


def render_employee_os2(st: Any, *, topic: str, industry: str, geography: str) -> None:
    st.markdown("## Team & Execution")
    st.caption("Pick **Full office**, **Department**, or **Employee / team** — then work in the workspace that opens below.")

    report_id = _report_id(topic, geography)
    if handle_oauth_redirect(st, expected_report_id=report_id):
        st.rerun()
    report_context = _build_report_context(topic, industry, geography, st)
    ensure_os2_team(report_id, topic=topic, industry=industry, geography=geography)
    st.caption(f"Project: **{topic}** | {geography}")

    custom = load_custom_harnesses(st, report_id)
    harnesses = merged_harnesses(custom)
    labels = {h["id"]: h["name"] for h in harnesses}
    keys, _, api_config = _collect_api_keys(st)

    from iidatech.execution.office_day import load_office_state, save_office_state

    office_state = load_office_state(st, report_id)
    scope = render_workspace_mode_tabs(st, report_id=report_id, harnesses=harnesses, office_state=office_state)
    office_state["scope"] = scope.to_dict()
    save_office_state(st, report_id, office_state)
    harness_filter = scope.active_harness_ids([str(h.get("id") or "") for h in harnesses])

    render_setup_requirements(st, report_id=report_id, keys=keys)

    with st.expander("API keys (Perplexity, OpenAI, …)", expanded=not bool(keys)):
        _render_api_keys_compact(st, keys)

    if not scope.is_configured():
        st.stop()

    _render_taylor_bubble(
        st,
        report_id=report_id,
        topic=topic,
        geography=geography,
        report_context=report_context,
        api_keys=keys,
        api_config=api_config,
        extra_harnesses=harnesses,
        scope=scope,
    )

    active_tab = _render_os2_tab_nav(st, report_id, scope)
    if active_tab == "office" and scope.mode != "employee":
        render_office(
            st,
            report_id=report_id,
            topic=topic,
            industry=industry,
            geography=geography,
            report_context=report_context,
            api_keys=keys,
            api_config=api_config,
            extra_harnesses=harnesses,
            scope=scope,
        )
    elif active_tab == "tasks":
        if scope.mode == "full_office":
            render_os2_approvals(
                st,
                report_id=report_id,
                report_context=report_context,
                api_keys=keys,
                api_config=api_config,
                extra_harnesses=harnesses,
            )
            st.divider()
        render_team_leader(
            st,
            report_id=report_id,
            topic=topic,
            industry=industry,
            geography=geography,
            report_context=report_context,
            api_keys=keys,
            api_config=api_config,
            extra_harnesses=harnesses,
            harness_ids=harness_filter,
        )
    elif active_tab == "war_room" and scope.is_full_office():
        render_war_room(st, report_id=report_id)
        st.divider()
        render_founder_chat(st, report_id=report_id, report_context=report_context)
    elif active_tab == "command" and scope.is_full_office():
        render_command_center(st, report_id=report_id, topic=topic, geography=geography, harness_labels=labels)
    elif active_tab == "agents":
        if scope.mode != "employee":
            render_team_hiring(st, report_id=report_id, topic=topic, industry=industry, geography=geography)
            st.divider()
        _render_agents_workspace(
            st,
            report_id=report_id,
            topic=topic,
            industry=industry,
            geography=geography,
            report_context=report_context,
            harnesses=harnesses,
            show_api_keys=False,
            scope=scope,
        )
    elif active_tab == "integrations":
        render_setup_requirements(st, report_id=report_id, keys=keys, expanded=True)
        render_integrations_guide(st)
        render_oauth_connections(st, report_id=report_id)
    elif active_tab == "advanced" and scope.is_full_office():
        render_custom_harness_builder(st, report_id=report_id)
        render_company_memory(st, report_id=report_id)


def _render_taylor_bubble(
    st: Any,
    *,
    report_id: str,
    topic: str,
    geography: str,
    report_context: dict[str, Any],
    api_keys: dict[str, str],
    api_config: dict[str, str],
    extra_harnesses: list[dict[str, Any]],
    scope: OfficeScope | None = None,
) -> None:
    """Floating team-leader bubble: status, approvals, suggestions, voice."""
    try:
        from iidatech.execution.agent_queue import approve_pending_queue_items, load_queue
        from iidatech.execution.automation_steps import automation_report_id
        from iidatech.execution.os2_workflow import (
            load_checklist,
            retry_task,
            run_next_task,
            save_checklist,
        )
        from iidatech.execution.taylor_pulse import build_taylor_pulse
        from iidatech.ui.taylor_bubble import render_taylor_bubble
    except Exception:
        return

    checklist = load_checklist(report_id)
    auto_id = automation_report_id(topic, geography)
    queue = load_queue(auto_id)
    pulse = build_taylor_pulse(
        report_id,
        checklist=checklist,
        queue=queue,
        has_api_keys=bool(api_keys),
    )
    action = render_taylor_bubble(st, report_id=report_id, pulse=pulse)
    if not action:
        return

    kind = str(action.get("action") or "")
    if kind == "approve_all":
        approved = 0
        if checklist:
            for item in checklist.get("items") or []:
                if str(item.get("status")) == "awaiting_approval" or (
                    bool(item.get("external")) and not item.get("approved") and str(item.get("status")) == "pending"
                ):
                    item["approved"] = True
                    item["status"] = "approved"
                    approved += 1
            if approved:
                save_checklist(report_id, checklist)
        approved += approve_pending_queue_items(auto_id)
        st.toast(f"Taylor: approved {approved} step(s). Running now.", icon="✅")
        st.rerun()
    elif kind == "retry_failed":
        if checklist:
            count = 0
            for item in checklist.get("items") or []:
                if str(item.get("status")) == "qc_failed":
                    retry_task(checklist, str(item.get("id")))
                    count += 1
            if count:
                save_checklist(report_id, checklist)
                st.toast(f"Taylor: {count} task(s) queued for retry.", icon="🔁")
        st.rerun()
    elif kind == "run_next":
        if checklist:
            harness_ids = (scope or OfficeScope()).active_harness_ids(
                [str(h.get("id") or "") for h in extra_harnesses]
            )
            with st.spinner("Taylor is running the next task..."):
                run_next_task(
                    report_id,
                    checklist,
                    api_keys=api_keys,
                    api_config=api_config,
                    report_context=report_context,
                    extra_harnesses=extra_harnesses,
                    harness_ids=harness_ids,
                )
            save_checklist(report_id, checklist)
        st.rerun()
    elif kind == "employee_prompt":
        hid = str(action.get("harness_id") or "")
        prompt = str(action.get("prompt") or "")
        if hid and prompt:
            st.session_state[f"os2_pending_{hid}"] = prompt
            mode = (scope or OfficeScope()).mode
            st.session_state[_os2_nav_tab_key(report_id, mode)] = "agents"
            st.session_state[_os2_focus_harness_key(report_id)] = hid
            st.rerun()


def _render_api_keys_compact(st: Any, keys: dict[str, str]) -> None:
    prov_options = ["auto"] + list(SUPPORTED_PROVIDERS)
    provider = st.selectbox(
        "Provider (for main key)",
        options=prov_options,
        format_func=lambda p: "Auto-detect" if p == "auto" else provider_label(p),
        index=prov_options.index(st.session_state.get("os2_api_provider", "auto"))
        if st.session_state.get("os2_api_provider", "auto") in prov_options
        else 0,
        key="os2_api_provider_select",
    )
    st.session_state["os2_api_provider"] = provider
    api_key = st.text_input("API key", type="password", value=str(st.session_state.get("os2_api_key") or ""), key="os2_api_key_input")
    if api_key:
        st.session_state["os2_api_key"] = api_key
    keys_now, _, _ = _collect_api_keys(st)
    if keys_now:
        st.success("Active: " + ", ".join(keys_now.keys()))
    elif keys:
        st.success("Active from .env: " + ", ".join(keys.keys()))
    else:
        st.warning("Add PERPLEXITY_API_KEY or OPENAI_API_KEY in `.env` or above.")
