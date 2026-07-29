"""The Office UI."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from iidatech.execution.office_day import (
    checklist_board,
    load_office_state,
    recent_activity,
    run_office_agent_cycle,
    run_office_arrival,
    run_office_delivery,
    run_office_execution_step,
    run_office_standup,
    save_office_state,
)
from iidatech.execution.office_scope import OfficeScope, filter_board_rows
from iidatech.execution.os2_workflow import load_checklist, save_checklist, sync_tasks_to_sql
from iidatech.execution.plan_ingest import get_session_business_plan, normalize_plan
from iidatech.execution.team_leader import build_checklist_from_plan
from iidatech.execution.team_leader_qc import mentor_for_phase
from iidatech.ui.os2_command_center import ensure_os2_team
from iidatech.ui.styles import inject_employee_os_styles

_PHASES = ["arrival", "standup", "execution", "agent_cycle", "delivery", "closed"]
_STATUS_LABELS = {
    "pending": "⏳ Queued",
    "assigned": "📋 Assigned",
    "in_progress": "🔄 In progress",
    "qc_review": "🔍 QC review",
    "delivered": "✅ Delivered",
    "needs_fix": "🛠️ Needs fix",
    "failed": "❌ Failed",
    "awaiting_approval": "🙋 Needs your OK",
    "skipped": "⏭️ Skipped",
}


def _default_goals(topic: str) -> list[str]:
    return [
        f"Validate market for {topic}",
        "Run competitor and pricing research (Sam)",
        "Build 20 qualified leads",
        "Draft outreach + campaign",
        "Run one external pilot",
    ]


def _ensure_checklist(
    st: Any,
    *,
    report_id: str,
    topic: str,
    industry: str,
    geography: str,
    report_context: dict[str, Any],
) -> dict[str, Any]:
    existing = load_checklist(report_id)
    if existing and existing.get("items"):
        return existing
    plan = get_session_business_plan(st)
    if not isinstance(plan, dict) and isinstance(report_context.get("report_v3"), dict):
        plan = report_context.get("report_v3")
    normalized = normalize_plan(plan, topic=topic, industry=industry, geography=geography)
    checklist = build_checklist_from_plan(
        normalized,
        topic=topic,
        industry=industry,
        geography=geography,
    )
    save_checklist(report_id, checklist)
    try:
        sync_tasks_to_sql(report_id, checklist)
    except Exception:
        pass
    return checklist


def render_office(
    st: Any,
    *,
    report_id: str,
    topic: str,
    industry: str,
    geography: str,
    report_context: dict[str, Any],
    api_keys: dict[str, str],
    api_config: dict[str, str],
    extra_harnesses: list[dict[str, Any]],
    scope: OfficeScope | None = None,
) -> None:
    inject_employee_os_styles(st)
    ensure_os2_team(report_id, topic=topic, industry=industry, geography=geography)
    state = load_office_state(st, report_id)
    scope = scope or OfficeScope()
    state["scope"] = scope.to_dict()
    harness_ids = scope.active_harness_ids([str(h.get("id") or "") for h in extra_harnesses])
    phase = str(state.get("phase") or "arrival")
    st.markdown("### The Office")
    if scope.is_full_office():
        st.caption("Clock in, standup with Taylor, watch tasks run (research first), QC, then deliverables.")
    else:
        st.caption(f"Scoped run: **{scope.label()}**. Only tasks and deliverables for your selection appear below.")
    if not state.get("onboarded"):
        with st.expander("New here? How the office works (30 seconds)", expanded=True):
            st.markdown(
                "1. **Taylor (your AI team leader)** reads your business plan and builds today's task list.\n"
                "2. Press **Run full office day** — the team researches, finds leads, drafts outreach and campaigns.\n"
                "3. Anything that touches the real world (posting to LinkedIn, sending email, updating your CRM) "
                "**pauses and asks you first**. Approve it in one click from Taylor's floating bubble or the Tasks tab.\n"
                "4. Finished work appears as downloadable files on the task board below.\n\n"
                "*You only need one API key (Perplexity or OpenAI) — add it in the expander at the top of this page.*"
            )
            if st.button("Got it — don't show again", key=f"office_onboard_{report_id}"):
                state["onboarded"] = True
                save_office_state(st, report_id, state)
                st.rerun()
    auto_approve = st.checkbox(
        "Auto-approve external actions (LinkedIn, email, HubSpot)",
        value=bool(st.session_state.get(f"office_auto_approve_{report_id}", False)),
        key=f"office_auto_approve_cb_{report_id}",
        help="Leave off so employees ask you before posting or sending.",
    )
    st.session_state[f"office_auto_approve_{report_id}"] = auto_approve
    idx = _PHASES.index(phase) if phase in _PHASES else 0
    st.progress(min(1.0, (idx + 1) / len(_PHASES)))
    with st.container(border=True):
        st.markdown("**Taylor - Team Leader and mentor**")
        st.info(state.get("last_mentor") or mentor_for_phase(phase))
    goals_text = st.text_area(
        "Priorities today",
        value="\n".join(state.get("goals") or _default_goals(topic)),
        height=90,
        key=f"office_goals_{report_id}",
    )
    goals = [g.strip() for g in goals_text.splitlines() if g.strip()]
    report_v3 = report_context.get("report_v3") if isinstance(report_context.get("report_v3"), dict) else report_context
    checklist = _ensure_checklist(
        st,
        report_id=report_id,
        topic=topic,
        industry=industry,
        geography=geography,
        report_context=report_context,
    )
    research_rows = [
        r
        for r in checklist_board(checklist)
        if "research" in str(r.get("assignee") or "").lower() or "competitor" in str(r.get("title") or "").lower()
    ]
    if research_rows:
        first = research_rows[0]
        label = _STATUS_LABELS.get(str(first.get("status")), str(first.get("status")))
        st.caption(
            f"Research queue: **{first.get('assignee')}** - {first.get('title')} (`{label}`). "
            "Sam runs competitor/pricing evidence before sales tasks."
        )
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.caption("1. Open office")
    c2.caption("2. Plan the day")
    c3.caption("3. Work one task")
    c4.caption("4. Team huddle")
    c5.caption("5. Wrap up")
    if c1.button("Clock in", key=f"off_in_{report_id}", help="Taylor opens the office and greets the team."):
        out = run_office_arrival(report_id, report_context=report_context)
        state.update({"phase": "standup", "last_mentor": out.get("mentor"), "goals": goals})
        save_office_state(st, report_id, state)
        st.rerun()
    if c2.button("Standup", key=f"off_up_{report_id}", help="Taylor turns your priorities into assigned tasks."):
        out = run_office_standup(report_id, goals, report_v3=report_v3, report_context=report_context)
        state.update({"phase": "execution", "last_mentor": out.get("mentor"), "goals": goals})
        save_office_state(st, report_id, state)
        st.rerun()
    if c3.button("Next task", key=f"off_task_{report_id}", help="Run one task and watch QC review it."):
        if not scope.is_configured():
            st.warning("Pick at least one department or employee in the scope selector above.")
            st.stop()
        if not api_keys:
            st.warning("Add API keys under Agents & team (Perplexity recommended for research).")
            st.stop()
        with st.status("Team working...", expanded=True) as status:
            step = run_office_execution_step(
                report_id,
                checklist,
                api_keys=api_keys,
                api_config=api_config,
                report_context=report_context,
                extra_harnesses=extra_harnesses,
                auto_approve=auto_approve,
                harness_ids=harness_ids,
            )
            item = step.get("item") if isinstance(step.get("item"), dict) else None
            if item:
                status.update(label=f"{item.get('assignee', 'Teammate')}: {item.get('title')}", state="complete")
            elif step.get("done"):
                status.update(label="All tasks done or waiting", state="complete")
            elif step.get("needs_approval"):
                status.update(label="Paused — your approval needed (Tasks & approvals tab)", state="complete")
                st.warning("An external action needs your approval. Open **Tasks & approvals**.")
        if step.get("done"):
            state["phase"] = "agent_cycle"
        state["last_mentor"] = mentor_for_phase("execution")
        save_office_state(st, report_id, state)
        st.rerun()
    if c4.button("Agent sync", key=f"off_sync_{report_id}", help="Employees compare notes and update the shared memory."):
        if not scope.is_full_office():
            st.info("Agent sync runs for the full office. Switch scope to **Full office** for company-wide sync.")
        else:
            cycle = run_office_agent_cycle(report_id, report_v3=report_v3, report_context=report_context)
            st.session_state[f"os2_last_cycle_{report_id}"] = cycle
            state.update({"phase": "delivery", "last_mentor": mentor_for_phase("execution")})
            save_office_state(st, report_id, state)
            st.rerun()
    if c5.button("Delivery", key=f"off_out_{report_id}", help="Package approved work and the founder brief."):
        out = run_office_delivery(report_id, report_v3=report_v3, report_context=report_context)
        state.update({"phase": "closed", "last_mentor": out.get("mentor"), "delivery": out})
        save_office_state(st, report_id, state)
        st.rerun()
    if st.button(scope.run_button_label(), type="primary", key=f"off_full_{report_id}"):
        if not scope.is_configured():
            st.warning("Pick at least one department or employee in the scope selector above.")
            st.stop()
        if not api_keys:
            st.warning("Add API keys under Agents & team first (Perplexity for research).")
            st.stop()
        checklist = _ensure_checklist(
            st,
            report_id=report_id,
            topic=topic,
            industry=industry,
            geography=geography,
            report_context=report_context,
        )
        prog = st.progress(0.0)
        run_office_arrival(report_id, report_context=report_context)
        prog.progress(0.12)
        out = run_office_standup(report_id, goals, report_v3=report_v3, report_context=report_context)
        state["last_mentor"] = out.get("mentor")
        prog.progress(0.22)
        items = checklist.get("items") or []
        scoped_count = len([i for i in items if harness_ids is None or str(i.get("harness_id") or "") in harness_ids])
        for i in range(min(25, scoped_count or 1)):
            step = run_office_execution_step(
                report_id,
                checklist,
                api_keys=api_keys,
                api_config=api_config,
                report_context=report_context,
                extra_harnesses=extra_harnesses,
                auto_approve=auto_approve,
                harness_ids=harness_ids,
            )
            prog.progress(0.22 + 0.55 * ((i + 1) / max(scoped_count, 1)))
            if step.get("done") or step.get("needs_approval"):
                break
        if scope.is_full_office():
            cycle = run_office_agent_cycle(report_id, report_v3=report_v3, report_context=report_context)
            st.session_state[f"os2_last_cycle_{report_id}"] = cycle
        prog.progress(0.88)
        delivery = run_office_delivery(report_id, report_v3=report_v3, report_context=report_context)
        prog.progress(1.0)
        state.update({"phase": "closed", "last_mentor": delivery.get("mentor"), "delivery": delivery, "goals": goals, "scope": scope.to_dict()})
        save_office_state(st, report_id, state)
        st.success(f"{scope.run_button_label()} complete.")
        st.rerun()
    board = filter_board_rows(checklist_board(checklist), harness_ids)
    if board:
        st.markdown("#### Task board")
        from iidatech.execution.os2_workflow import approve_task, retry_task, skip_task

        for row in board:
            status = str(row.get("status"))
            label = _STATUS_LABELS.get(status, status)
            cols = st.columns([6, 2]) if status in {"awaiting_approval", "needs_fix", "failed"} else None
            target = cols[0] if cols else st
            target.markdown(f"**{row.get('assignee') or 'Team'}** - {row.get('title')} (`{label}`)")
            note = str(row.get("mentor_note") or "").strip()
            if note:
                target.caption(note[:280])
            task_id = str(row.get("id") or "")
            if cols and task_id:
                if status == "awaiting_approval":
                    if cols[1].button("Approve", key=f"off_ok_{report_id}_{task_id}", type="primary"):
                        approve_task(checklist, task_id)
                        save_checklist(report_id, checklist)
                        st.rerun()
                elif status in {"needs_fix", "failed"}:
                    if cols[1].button("Retry", key=f"off_retry_{report_id}_{task_id}"):
                        retry_task(checklist, task_id)
                        save_checklist(report_id, checklist)
                        st.rerun()
                    if cols[1].button("Skip", key=f"off_skip_{report_id}_{task_id}"):
                        skip_task(checklist, task_id)
                        save_checklist(report_id, checklist)
                        st.rerun()
            for art in (row.get("artifacts") or [])[:3]:
                fp = Path(str(art))
                if fp.is_file():
                    from iidatech.ui.os2_deliverable_view import render_deliverable_preview

                    render_deliverable_preview(
                        st,
                        title=str(row.get("title") or fp.stem),
                        artifacts=[str(fp)],
                        key_prefix=f"off_board_{report_id}_{task_id}_{fp.name}",
                    )
    else:
        st.info("Taylor is building today's queue from your topic. Refresh if the board is empty.")
    delivery = state.get("delivery") if isinstance(state.get("delivery"), dict) else {}
    evening = delivery.get("evening") if isinstance(delivery.get("evening"), dict) else {}
    brief = evening.get("founder_brief") if isinstance(evening.get("founder_brief"), dict) else {}
    if brief:
        st.markdown("#### Founder brief")
        for issue in brief.get("urgent_issues") or []:
            st.warning(str(issue))
        for rec in brief.get("recommendations") or []:
            st.markdown(f"- {rec}")
        for need in brief.get("needs_approval") or []:
            st.info(f"Needs approval: {need}")
    for art in (delivery.get("artifacts") or [])[:10]:
        fp = Path(str(art))
        if fp.is_file():
            from iidatech.ui.os2_deliverable_view import render_deliverable_preview

            render_deliverable_preview(
                st,
                title=fp.stem.replace("_", " ").title(),
                artifacts=[str(fp)],
                key_prefix=f"off_delivery_{report_id}_{fp.name}",
            )
    st.markdown("#### Activity feed")
    for row in recent_activity(report_id, limit=8):
        st.markdown(f"**{row.get('from')}** - {row.get('when')}\n\n{row.get('text')}")
