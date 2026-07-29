"""Unified founder approvals for Employee OS 2 (checklist + agent brief)."""
from __future__ import annotations

from typing import Any

from iidatech.execution.os2_workflow import (
    approve_task,
    failed_checklist_items,
    load_checklist,
    retry_task,
    run_task,
    save_checklist,
    skip_task,
)
from iidatech.execution.memory_engine import load_team_shared_memory
from iidatech.storage.execution_repository import list_employees
from iidatech.ui.workspace import render_approval_center
from iidatech.ui.view_models import build_approval_items


def _pending_checklist_items(checklist: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not checklist:
        return []
    pending: list[dict[str, Any]] = []
    for item in checklist.get("items") or []:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "pending")
        external = bool(item.get("external"))
        approved = bool(item.get("approved"))
        if external and not approved and status in {"pending", "approved"}:
            pending.append(item)
        if status == "qc_failed":
            pending.append(item)
    return pending


def render_os2_approvals(
    st: Any,
    *,
    report_id: str,
    report_context: dict[str, Any] | None = None,
    api_keys: dict[str, str] | None = None,
    api_config: dict[str, str] | None = None,
    extra_harnesses: list[dict[str, Any]] | None = None,
) -> None:
    st.markdown("### Approvals")
    st.caption("External posts, emails, and CRM syncs pause here until you approve.")

    checklist = load_checklist(report_id)
    failed = failed_checklist_items(checklist)
    if failed:
        st.markdown("**Failed tasks — retry or skip to unblock the queue**")
        for item in failed:
            title = str(item.get("title") or "Task")
            assignee = str(item.get("assignee") or "Team")
            err = str(item.get("error") or item.get("result") or "execution failed")[:400]
            with st.container(border=True):
                st.markdown(f"**{assignee}** — {title}")
                st.error(err)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Retry", key=f"os2_failed_retry_{item.get('id')}_{report_id}", type="primary"):
                        if checklist:
                            retry_task(checklist, str(item.get("id")))
                            target = next(
                                (i for i in (checklist.get("items") or []) if str(i.get("id")) == str(item.get("id"))),
                                None,
                            )
                            if target:
                                with st.spinner(f"Retrying {title}..."):
                                    run_task(
                                        report_id,
                                        checklist,
                                        target,
                                        api_keys=api_keys,
                                        api_config=api_config,
                                        report_context=report_context,
                                        extra_harnesses=extra_harnesses,
                                    )
                                save_checklist(report_id, checklist)
                        st.rerun()
                with c2:
                    if st.button("Skip", key=f"os2_failed_skip_{item.get('id')}_{report_id}"):
                        if checklist:
                            skip_task(checklist, str(item.get("id")))
                            save_checklist(report_id, checklist)
                        st.rerun()

    pending = _pending_checklist_items(checklist)
    if pending:
        st.markdown("**Checklist waiting on you**")
        for item in pending:
            title = str(item.get("title") or "Task")
            assignee = str(item.get("assignee") or "Team")
            status = str(item.get("status") or "")
            with st.container(border=True):
                st.markdown(f"**{assignee}** — {title}")
                if status == "qc_failed":
                    qc = item.get("qc") if isinstance(item.get("qc"), dict) else {}
                    st.warning(str(qc.get("mentor_note") or "QC failed — retry from The Office."))
                    if st.button("Retry task", key=f"os2_retry_{item.get('id')}_{report_id}"):
                        item["status"] = "approved"
                        item["approved"] = True
                        item.pop("qc", None)
                        save_checklist(report_id, checklist)
                        st.rerun()
                else:
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("Approve", key=f"os2_app_{item.get('id')}", type="primary"):
                            approve_task(checklist, str(item.get("id")))
                            save_checklist(report_id, checklist)
                            st.rerun()
                    with c2:
                        if st.button("Skip", key=f"os2_skip_{item.get('id')}"):
                            item["status"] = "skipped"
                            save_checklist(report_id, checklist)
                            st.rerun()
    elif not failed:
        st.success("No checklist items waiting for approval.")

    shared = load_team_shared_memory(report_id)
    brief = (shared.get("company_context") or {}).get("founder_brief") or {}
    if isinstance(brief, dict) and (brief.get("needs_approval") or brief.get("recommendations")):
        st.markdown("**Taylor brief — decisions needed**")
        for line in brief.get("needs_approval") or []:
            st.markdown(f"- {line}")
        for rec in (brief.get("recommendations") or [])[:5]:
            st.caption(str(rec))

    cycle = st.session_state.get(f"os2_last_cycle_{report_id}")
    approvals = build_approval_items(report_id, employee_cycle=cycle if isinstance(cycle, dict) else None)
    if approvals:
        render_approval_center(st, approvals, report_id=report_id, state_key=f"os2_approvals_{report_id}")


def render_founder_chat(st: Any, *, report_id: str, report_context: dict[str, Any] | None = None) -> None:
    from iidatech.execution.task_engine import founder_employee_id
    from iidatech.ui.workspace import render_chat_panel

    employees = list_employees(report_id, active_only=True)
    chat_rows = [
        {"employee_id": str(e.get("employee_id") or ""), "name": str(e.get("name") or e.get("role") or "Team"), "role": str(e.get("role") or "")}
        for e in employees
        if str(e.get("role") or "") != "Founder"
    ]
    render_chat_panel(st, report_id=report_id, chat_employees=chat_rows, founder_id=founder_employee_id(report_id), report_context=report_context)
