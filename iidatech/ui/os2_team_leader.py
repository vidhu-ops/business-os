"""Team leader UI: plan checklist, sequential approval, auto-run, OAuth connect."""
from __future__ import annotations

import json
from typing import Any

from iidatech.execution.os2_workflow import (
    approve_task,
    load_checklist,
    run_all_tasks,
    run_next_task,
    save_checklist,
    skip_task,
    sync_tasks_to_sql,
)
from iidatech.execution.team_leader import build_checklist_from_plan, next_runnable_item
from iidatech.execution.plan_ingest import get_session_business_plan, normalize_plan, set_session_business_plan
from iidatech.integrations.oauth_store import (
    apply_token_payload,
    build_authorization_url,
    connection_label,
    exchange_authorization_code,
    get_connection,
    is_connected,
    oauth_env_ready,
    oauth_state,
    parse_oauth_state,
    seed_workspace_from_env,
    set_connection,
)


def handle_oauth_redirect(st: Any, *, expected_report_id: str) -> bool:
    """Auto-complete OAuth when user returns with ?code= &state=report|provider."""
    try:
        params = st.query_params
        code = str(params.get("code") or "").strip()
        state = str(params.get("state") or "").strip()
    except Exception:
        return False
    if not code or not state:
        return False
    rid, provider = parse_oauth_state(state)
    if rid != expected_report_id or provider not in {"linkedin", "gmail", "hubspot"}:
        return False
    ok, payload = exchange_authorization_code(provider, code)
    if not ok or not isinstance(payload, dict):
        st.error(f"OAuth failed: {payload}")
        return False
    apply_token_payload(rid, provider, payload)
    try:
        st.query_params.clear()
    except Exception:
        pass
    st.success(f"{provider.title()} connected.")
    return True


def _checklist_key(report_id: str) -> str:
    return f"os2_team_checklist_{report_id}"


def _persist_session_checklist(st: Any, report_id: str, checklist: dict[str, Any]) -> None:
    checklist.pop("auto_approve", None)
    st.session_state[_checklist_key(report_id)] = checklist
    save_checklist(report_id, checklist)


def _get_checklist(st: Any, report_id: str) -> dict[str, Any] | None:
    if _checklist_key(report_id) in st.session_state:
        return st.session_state[_checklist_key(report_id)]
    loaded = load_checklist(report_id)
    if loaded:
        st.session_state[_checklist_key(report_id)] = loaded
    return loaded


def render_oauth_connections(st: Any, *, report_id: str) -> None:
    seed_workspace_from_env(report_id)
    st.markdown("### Connect accounts (OAuth / tokens)")
    ready = [p for p in ("linkedin", "hubspot", "gmail") if oauth_env_ready(p)]
    if ready:
        st.success("OAuth app credentials loaded from `.env` for: " + ", ".join(ready) + ". Click the authorization link below once per app.")
    st.caption(
        "LinkedIn + HubSpot can load from `.env`. For **Gmail**, add `GMAIL_CLIENT_ID` / `GMAIL_CLIENT_SECRET` "
        "from [Google Cloud Console](https://console.cloud.google.com/apis/credentials) (OAuth client, redirect "
        "`http://127.0.0.1:8501/`) **or** use SMTP app password below."
    )

    providers = [
        ("linkedin", "LinkedIn", "https://www.linkedin.com/developers/"),
        ("gmail", "Gmail", "https://console.cloud.google.com/"),
        ("hubspot", "HubSpot", "https://developers.hubspot.com/"),
    ]
    for pid, label, portal in providers:
        with st.expander(f"{label} — {connection_label(report_id, pid)}", expanded=not is_connected(report_id, pid)):
            st.markdown(f"[Developer portal]({portal})")
            auth_url, auth_err = build_authorization_url(pid, state=oauth_state(report_id, pid))
            if auth_url:
                st.markdown(f"[Open OAuth authorization]({auth_url})")
            elif auth_err:
                st.caption(auth_err)

            if pid == "linkedin":
                conn = get_connection(report_id, pid)
                token = st.text_input("Access token", type="password", value=str(conn.get("access_token") or ""), key=f"os2_oauth_li_tok_{report_id}")
                urn = st.text_input("Author URN (urn:li:person:... or urn:li:organization:...)", value=str(conn.get("author_urn") or ""), key=f"os2_oauth_li_urn_{report_id}")
                code = st.text_input("OAuth code (paste after redirect)", key=f"os2_oauth_li_code_{report_id}")
                if st.button(f"Save LinkedIn connection", key=f"os2_oauth_li_save_{report_id}"):
                    if code.strip():
                        ok, payload = exchange_authorization_code(pid, code.strip())
                        if ok and isinstance(payload, dict):
                            fields = apply_token_payload(report_id, pid, payload)
                            if urn.strip():
                                set_connection(report_id, pid, {"author_urn": urn.strip()})
                        else:
                            st.error(str(payload))
                            st.stop()
                    elif token.strip():
                        set_connection(report_id, pid, {"access_token": token.strip(), "author_urn": urn.strip()})
                    st.success("LinkedIn connected.")
                    st.rerun()

            elif pid == "gmail":
                conn = get_connection(report_id, pid)
                st.caption("Option A: Gmail API OAuth token. Option B: App password SMTP (recommended for local dev).")
                token = st.text_input("OAuth access token", type="password", value=str(conn.get("access_token") or ""), key=f"os2_oauth_gm_tok_{report_id}")
                smtp_user = st.text_input("SMTP user (Gmail address)", value=str(conn.get("smtp_user") or ""), key=f"os2_oauth_gm_user_{report_id}")
                smtp_pass = st.text_input("SMTP app password", type="password", value=str(conn.get("smtp_password") or ""), key=f"os2_oauth_gm_pass_{report_id}")
                code = st.text_input("OAuth code", key=f"os2_oauth_gm_code_{report_id}")
                if st.button(f"Save Gmail connection", key=f"os2_oauth_gm_save_{report_id}"):
                    fields = {"smtp_user": smtp_user.strip(), "smtp_password": smtp_pass.strip()}
                    if code.strip():
                        ok, payload = exchange_authorization_code(pid, code.strip())
                        if ok and isinstance(payload, dict):
                            apply_token_payload(report_id, pid, {**payload, **fields})
                        else:
                            st.error(str(payload))
                            st.stop()
                    elif token.strip():
                        fields["access_token"] = token.strip()
                        set_connection(report_id, pid, fields)
                    else:
                        set_connection(report_id, pid, fields)
                    st.success("Gmail connected.")
                    st.rerun()

            else:
                conn = get_connection(report_id, pid)
                token = st.text_input("Private app / OAuth access token", type="password", value=str(conn.get("access_token") or conn.get("token") or ""), key=f"os2_oauth_hs_tok_{report_id}")
                code = st.text_input("OAuth code", key=f"os2_oauth_hs_code_{report_id}")
                if st.button(f"Save HubSpot connection", key=f"os2_oauth_hs_save_{report_id}"):
                    if code.strip():
                        ok, payload = exchange_authorization_code(pid, code.strip())
                        if ok and isinstance(payload, dict):
                            apply_token_payload(report_id, pid, payload)
                        else:
                            st.error(str(payload))
                            st.stop()
                    elif token.strip():
                        set_connection(report_id, pid, {"access_token": token.strip()})
                    st.success("HubSpot connected.")
                    st.rerun()


def render_team_leader(
    st: Any,
    *,
    report_id: str,
    topic: str,
    industry: str,
    geography: str,
    report_context: dict[str, Any],
    api_keys: dict[str, str],
    api_config: dict[str, str],
    extra_harnesses: list[dict[str, Any]] | None = None,
    harness_ids: set[str] | None = None,
) -> None:
    st.markdown("### Team leader")
    st.caption("Taylor (COO) reads your business plan, assigns tasks to the right agents, and runs them one-by-one with approval.")

    plan = get_session_business_plan(st)
    if not isinstance(plan, dict) or not plan:
        st.warning(
            "No business plan in session yet. Build one in **Turn idea into business plan**, "
            "or upload JSON / Markdown below."
        )
        uploaded = st.file_uploader(
            "Upload plan (JSON or Markdown)",
            type=["json", "md", "txt"],
            key=f"os2_plan_upload_{report_id}",
        )
        if uploaded:
            try:
                raw = uploaded.getvalue().decode("utf-8", errors="ignore")
                if uploaded.name.lower().endswith(".json"):
                    plan = json.loads(raw)
                else:
                    plan = raw
                if plan:
                    normalized = normalize_plan(plan, topic=topic, industry=industry, geography=geography)
                    set_session_business_plan(st, normalized)
                    st.success("Plan loaded and normalized.")
                    st.rerun()
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                st.error(f"Invalid plan file: {exc}")
        return

    plan = normalize_plan(plan, topic=topic, industry=industry, geography=geography)

    checklist = _get_checklist(st, report_id)
    approve_key = f"os2_auto_approve_{report_id}"
    auto_approve = st.checkbox(
        "Auto-approve internal tasks (external LinkedIn/email/CRM still need your OK)",
        value=bool(st.session_state.get(approve_key, False)),
        key=approve_key,
    )

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("Analyze plan and build checklist", type="primary", key=f"os2_build_checklist_{report_id}"):
            checklist = build_checklist_from_plan(plan, topic=topic, industry=industry, geography=geography)
            _persist_session_checklist(st, report_id, checklist)
            sync_tasks_to_sql(report_id, checklist)
            st.rerun()
    with col_b:
        if checklist and st.button("Approve and run next task", key=f"os2_run_next_{report_id}"):
            nxt = next_runnable_item(checklist, auto_approve=auto_approve, harness_ids=harness_ids)
            if nxt and not auto_approve:
                approve_task(checklist, str(nxt.get("id")))
            with st.spinner("Running next task..."):
                step = run_next_task(
                    report_id,
                    checklist,
                    auto_approve=auto_approve,
                    api_keys=api_keys,
                    api_config=api_config,
                    report_context=report_context,
                    extra_harnesses=extra_harnesses,
                    harness_ids=harness_ids,
                )
            _persist_session_checklist(st, report_id, checklist)
            if step.get("needs_approval"):
                st.info(step.get("message"))
            elif step.get("done"):
                st.success(step.get("message"))
            else:
                st.success(f"Completed: {step.get('message')}")
            st.rerun()
    with col_c:
        if checklist and st.button("Run all remaining (auto-approve)", key=f"os2_run_all_{report_id}"):
            with st.spinner("Running full task queue — this may take several minutes..."):
                logs = run_all_tasks(
                    report_id,
                    checklist,
                    api_keys=api_keys,
                    api_config=api_config,
                    report_context=report_context,
                    extra_harnesses=extra_harnesses,
                    harness_ids=harness_ids,
                )
            _persist_session_checklist(st, report_id, checklist)
            qc_blocked = next((lg for lg in logs if lg.get("qc_blocked")), None)
            if qc_blocked:
                item = qc_blocked.get("item") or {}
                st.warning(f"Stopped: **{item.get('title')}** failed QC — review and retry before continuing.")
            else:
                st.success(f"Ran {len(logs)} step(s).")
            st.rerun()

    if not checklist:
        return

    st.info(str(checklist.get("summary") or ""))

    items = sorted(checklist.get("items") or [], key=lambda x: int(x.get("seq") or 0))
    if harness_ids is not None:
        items = [i for i in items if str(i.get("harness_id") or "") in harness_ids]
        if not items:
            st.warning("No tasks in queue for your current workspace scope.")
            return

    rows = []
    for item in items:
        status = str(item.get("status") or "pending")
        ext = " [external]" if item.get("external") else ""
        rows.append({
            "#": item.get("seq"),
            "Assignee": item.get("assignee"),
            "Task": str(item.get("title") or "") + ext,
            "Status": status,
            "Approved": "yes" if item.get("approved") or auto_approve else "no",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)

    awaiting = [
        i for i in items
        if str(i.get("status")) in {"awaiting_approval", "pending", "approved"} and str(i.get("status")) != "completed"
    ]
    if awaiting and not auto_approve:
        nxt = awaiting[0]
        with st.container(border=True):
            st.markdown(f"**Next up for approval:** {nxt.get('title')}")
            st.caption(f"Assigned to: {nxt.get('assignee')} | Kind: {nxt.get('task_kind', 'harness')}")
            st.write(str(nxt.get("prompt") or "")[:1200])
            if nxt.get("external"):
                prov = str(nxt.get("oauth_provider") or "")
                if not is_connected(report_id, prov):
                    st.warning(f"Connect {prov} under Integrations before this step can succeed.")
            ac1, ac2 = st.columns(2)
            with ac1:
                if st.button("Approve this task only", key=f"os2_approve_one_{nxt.get('id')}"):
                    approve_task(checklist, str(nxt.get("id")))
                    _persist_session_checklist(st, report_id, checklist)
                    st.rerun()
            with ac2:
                if st.button("Skip", key=f"os2_skip_{nxt.get('id')}"):
                    skip_task(checklist, str(nxt.get("id")))
                    _persist_session_checklist(st, report_id, checklist)
                    st.rerun()

    completed = [i for i in items if str(i.get("status")) == "completed"]
    if completed:
        with st.expander(f"Completed outputs ({len(completed)})", expanded=False):
            for item in completed[-5:]:
                st.markdown(f"**{item.get('title')}** — {item.get('assignee')}")
                from iidatech.ui.os2_deliverable_view import render_deliverable_preview

                render_deliverable_preview(
                    st,
                    title=str(item.get("title") or "Task output"),
                    reply=str(item.get("result") or ""),
                    artifacts=list(item.get("artifacts") or []),
                    key_prefix=f"tl_done_{item.get('id')}",
                )
