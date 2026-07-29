"""Streamlit renderers for Employee OS customer workspace."""
from __future__ import annotations

from typing import Any

from iidatech.execution.chat_engine import send_agent_message
from iidatech.execution.memory_engine import build_agent_context
from iidatech.execution.debate_engine import apply_founder_override
from iidatech.execution.long_memory import on_founder_decision
from iidatech.storage.execution_repository import get_employee
from iidatech.ui.styles import inject_employee_os_styles
from iidatech.ui.view_models import build_employee_os_workspace


def _reply_as_employee(report_id: str, employee_id: str, message: str, *, report_context: dict | None = None) -> str:
    emp = get_employee(employee_id)
    if not emp:
        return "I'm here — could you repeat that?"
    ctx = build_agent_context(employee_id, report_context=report_context, report_id=report_id)
    name = str(emp.get("role") or "team member")
    task = ctx.get("assigned_tasks") or []
    focus = task[0].get("title") if task else (ctx.get("goals") or ["today's priorities"])[0]
    insights = ctx.get("learned_insights") or []
    insight_line = f" Quick note: {insights[-1]}." if insights else ""
    return (
        f"Got it. As your {name}, I'm on **{focus}** right now.{insight_line} "
        f"I'll factor your message into my next update."
    )


def render_company_dashboard(st: Any, dashboard: dict[str, Any]) -> None:
    st.markdown('<div class="iida-os">', unsafe_allow_html=True)
    st.markdown("### Company pulse")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f'<div class="iida-metric-card"><div class="iida-metric-label">Revenue</div>'
            f'<div class="iida-metric-value">{dashboard.get("revenue", "—")}</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="iida-metric-card"><div class="iida-metric-label">Burn</div>'
            f'<div class="iida-metric-value">{dashboard.get("burn", "—")}</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="iida-metric-card"><div class="iida-metric-label">Runway</div>'
            f'<div class="iida-metric-value">{dashboard.get("runway", "—")}</div></div>',
            unsafe_allow_html=True,
        )
    with c4:
        projects = dashboard.get("active_projects") or []
        st.markdown(
            f'<div class="iida-metric-card"><div class="iida-metric-label">Active work</div>'
            f'<div class="iida-metric-value">{len(projects)}</div></div>',
            unsafe_allow_html=True,
        )

    if dashboard.get("goals"):
        st.markdown("**Today's goals**")
        for g in dashboard["goals"]:
            st.markdown(f"- {g}")

    if dashboard.get("active_projects"):
        st.markdown("**Active projects**")
        for p in dashboard["active_projects"][:5]:
            title = p.get("title") or "Project"
            status = p.get("status") or "In progress"
            st.markdown(f"- {title} · *{status}*")

    alerts = dashboard.get("alerts") or []
    if alerts:
        st.markdown("**Alerts**")
        for a in alerts[:5]:
            css = "iida-alert-critical" if any(x in a.lower() for x in ("critical", "blocked", "churn")) else "iida-alert"
            st.markdown(f'<div class="{css}">{a}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_employee_cards(st: Any, employees: list[dict[str, Any]]) -> None:
    st.markdown("### Your team")
    if not employees:
        st.caption("No employees hired yet.")
        return
    cols = st.columns(min(3, len(employees)))
    for i, emp in enumerate(employees):
        with cols[i % len(cols)]:
            kpi_html = "".join(
                f'<div style="font-size:0.8rem;color:#64748b;">{k["label"]}: <b>{k["value"]}</b></div>'
                for k in (emp.get("kpis") or [])
            )
            badges = emp.get("tool_badges") or []
            badge_html = "".join(
                f'<span class="iida-badge iida-badge-{b.lower()}">{b}</span> '
                for b in badges[:3]
            )
            st.markdown(
                f'<div class="iida-emp-card">'
                f'<div style="display:flex;gap:0.75rem;align-items:center;">'
                f'<div class="iida-avatar" style="background:{emp.get("avatar_color")};">{emp.get("avatar_initials")}</div>'
                f'<div><div style="font-weight:650;">{emp.get("name")}</div>'
                f'<div style="color:#64748b;font-size:0.85rem;">{emp.get("role")}</div></div></div>'
                f'<div style="margin-top:0.65rem;"><span class="{emp.get("status_class")}">{emp.get("status")}</span></div>'
                f'<div style="margin-top:0.5rem;font-size:0.9rem;"><b>Task:</b> {emp.get("current_task")}</div>'
                f'<div style="margin-top:0.35rem;">{badge_html}</div>'
                f'<div class="iida-progress-bar"><div class="iida-progress-fill" style="width:{emp.get("progress_pct", 0)}%;"></div></div>'
                f'<div style="font-size:0.8rem;color:#64748b;">Progress: {emp.get("progress_pct")}%</div>'
                f'{kpi_html}</div>',
                unsafe_allow_html=True,
            )


def render_activity_feed(st: Any, activity: list[dict[str, str]]) -> None:
    st.markdown("### Live activity")
    for item in activity:
        st.markdown(
            f'<div class="iida-feed-item">{item.get("text", "")} '
            f'<span style="color:#94a3b8;font-size:0.75rem;">· {item.get("time", "")}</span></div>',
            unsafe_allow_html=True,
        )


def render_chat_panel(
    st: Any,
    *,
    report_id: str,
    chat_employees: list[dict[str, str]],
    founder_id: str | None,
    report_context: dict | None = None,
) -> None:
    st.markdown("### Chat with your team")
    if not chat_employees:
        st.caption("Hire a team to start chatting.")
        return

    labels = [f"{e['name']} — {e['role']}" for e in chat_employees]
    idx = st.selectbox("Employee", range(len(labels)), format_func=lambda i: labels[i], key=f"os_chat_emp_{report_id}")
    employee = chat_employees[idx]
    chat_key = f"os_chat_log_{report_id}_{employee['employee_id']}"
    if chat_key not in st.session_state:
        st.session_state[chat_key] = [
            {"role": "assistant", "content": f"Hi — I'm {employee['name']}, your {employee['role']}. What should I prioritize?"},
        ]

    for msg in st.session_state[chat_key]:
        if msg["role"] == "user":
            st.markdown(f'<div class="iida-chat-bubble-user"><b>You</b><br>{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="iida-chat-bubble-agent"><b>{employee["name"]}</b><br>{msg["content"]}</div>', unsafe_allow_html=True)

    user_msg = st.chat_input(f"Message {employee['name']}…", key=f"os_chat_input_{report_id}_{employee['employee_id']}")
    if user_msg and founder_id:
        st.session_state[chat_key].append({"role": "user", "content": user_msg})
        send_agent_message(report_id, founder_id, employee["employee_id"], user_msg, report_context=report_context)
        reply = _reply_as_employee(report_id, employee["employee_id"], user_msg, report_context=report_context)
        st.session_state[chat_key].append({"role": "assistant", "content": reply})
        st.rerun()


def render_approval_center(st: Any, approvals: list[dict[str, Any]], *, report_id: str, state_key: str) -> None:
    st.markdown("### Approval center")
    resolved_key = f"{state_key}_resolved"
    if resolved_key not in st.session_state:
        st.session_state[resolved_key] = set()

    pending = [a for a in approvals if a.get("id") not in st.session_state[resolved_key]]
    if not pending:
        st.success("All caught up — no pending approvals.")
        return

    for item in pending:
        st.markdown(f'<div class="iida-approval-card"><b>{item.get("requester")}</b> asks:<br>{item.get("title")}</div>', unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        aid = item.get("id")
        with c1:
            if st.button("Approve", key=f"approve_{state_key}_{aid}", type="primary"):
                st.session_state[resolved_key].add(aid)
                on_founder_decision(report_id, approved=True, title=str(item.get("title") or ""), requester_employee_id=None)
                st.toast(f"Approved: {item.get('title')}")
                st.rerun()
        with c2:
            if st.button("Reject", key=f"reject_{state_key}_{aid}"):
                st.session_state[resolved_key].add(aid)
                on_founder_decision(report_id, approved=False, title=str(item.get("title") or ""), requester_employee_id=None)
                st.toast("Request declined")
                st.rerun()


def render_founder_live_panel(st: Any, live: dict[str, Any]) -> None:
    st.markdown("### Founder live workspace")
    score = live.get("realism_score")
    if score is not None:
        st.caption(f"Execution realism: {score}/10")
    counts = live.get("tool_matrix_counts") or {}
    if counts:
        st.caption(
            f"Tools — real: {counts.get('REAL', 0)} · partial: {counts.get('PARTIAL', 0)} · "
            f"simulated: {counts.get('SIMULATED', 0)} · blocked: {counts.get('BLOCKED', 0)}"
        )

    tasks = live.get("tasks_in_progress") or []
    st.markdown("**Tasks in progress**")
    if not tasks:
        st.caption("No open tasks.")
    else:
        for t in tasks[:6]:
            st.markdown(f"- {t.get('title')} `{t.get('status')}`")

    logs = live.get("tool_logs") or []
    st.markdown("**Live tool logs**")
    if not logs:
        st.caption("Tool runs will stream here.")
    else:
        for row in logs[:8]:
            badge = "Verified" if row.get("verified") else row.get("execution_mode", "simulated")
            ok = "ok" if row.get("success") else "fail"
            st.markdown(f"`{row.get('tool_name')}` · {badge} · {ok}")
            for line in row.get("logs") or []:
                st.caption(str(line))

    arts = live.get("artifacts") or []
    if arts:
        st.markdown("**Generated files**")
        for a in arts[:5]:
            st.caption(f"{a.get('kind')} · {a.get('name')} ({a.get('tool')})")

    if live.get("emails_sent"):
        st.markdown("**Emails sent**")
        for e in live["emails_sent"][:5]:
            st.caption(f"{e.get('tool')}: {e.get('detail')}")

    if live.get("meetings_booked"):
        st.markdown("**Meetings**")
        for m in live["meetings_booked"][:5]:
            st.caption(m.get("detail", ""))

    kpis = live.get("kpis") or []
    if kpis:
        st.markdown("**KPI updates**")
        for k in kpis[:5]:
            st.caption(f"{k.get('metric_name')}: {k.get('metric_value')} ({k.get('created_at', '')[:10]})")


def render_war_room_panel(st: Any, war_room: dict[str, Any], *, report_id: str) -> None:
    st.markdown("### War room")
    if not war_room.get("active"):
        st.caption("No active debate — team debates appear when spend, KPI, or conflicts need resolution.")
        return

    trigger = war_room.get("trigger") or "team debate"
    st.markdown(
        f'<div class="iida-war-room"><b>Active debate</b> · <span style="color:#64748b;">{trigger}</span><br>'
        f'<span style="font-size:1.05rem;">{war_room.get("topic", "")}</span></div>',
        unsafe_allow_html=True,
    )

    for item in war_room.get("thread") or []:
        label = item.get("label") or "Point"
        css = "iida-debate-arg"
        if label == "Objection":
            css = "iida-debate-obj"
        elif label == "Response":
            css = "iida-debate-counter"
        st.markdown(
            f'<div class="{css}"><b>{item.get("role")}</b> <span style="color:#94a3b8;font-size:0.75rem;">({label})</span><br>'
            f'{item.get("text", "")}</div>',
            unsafe_allow_html=True,
        )

    if war_room.get("consensus"):
        esc = " · Escalation required" if war_room.get("escalation_required") else ""
        st.markdown(
            f'<div class="iida-consensus"><b>Consensus</b>{esc}<br>{war_room["consensus"]}</div>',
            unsafe_allow_html=True,
        )

    if war_room.get("vote_rows"):
        st.markdown("**Votes**")
        pills = "".join(
            f'<span class="iida-vote-pill">{v["role"]}: {v["vote"]}</span> '
            for v in war_room["vote_rows"]
        )
        st.markdown(pills, unsafe_allow_html=True)

    if war_room.get("founder_override"):
        st.info(f"Founder override: {war_room['founder_override']}")
    else:
        st.markdown("**Founder override**")
        override_key = f"war_room_override_{report_id}"
        decision = st.text_input("Your decision", key=override_key, placeholder="e.g. Approve ₹10k pilot only")
        if st.button("Apply override", key=f"war_override_btn_{report_id}"):
            if decision.strip():
                debate = {
                    "debate_id": war_room.get("debate_id"),
                    "topic": war_room.get("topic"),
                    "consensus": war_room.get("consensus"),
                }
                apply_founder_override(report_id, debate, decision.strip())
                on_founder_decision(report_id, approved=True, title=decision.strip())
                st.toast("Founder override recorded")
                st.rerun()


def render_deliverables_panel(st: Any, deliverables: list[dict[str, str]]) -> None:
    st.markdown("### Deliverables")
    if not deliverables:
        st.caption("Artifacts will appear here as your team completes work.")
        return
    for d in deliverables:
        icon = {"CSV": "📊", "Report": "📄", "Data": "📁", "Log": "📝"}.get(d.get("kind", ""), "📎")
        st.markdown(
            f'<div class="iida-deliverable">{icon} <div><b>{d.get("label")}</b><br>'
            f'<span style="color:#64748b;font-size:0.8rem;">{d.get("name")} · {d.get("size_kb")}</span></div></div>',
            unsafe_allow_html=True,
        )
        try:
            data = open(d["path"], "rb").read()
            st.download_button("Download", data=data, file_name=d.get("name"), key=f"dl_{d.get('name')}_{d.get('path')[-8:]}")
        except OSError:
            pass


def render_employee_os(
    st: Any,
    report_id: str,
    *,
    employee_cycle: dict | None = None,
    report_v3: dict | None = None,
) -> None:
    """Render full Employee OS workspace — customer safe, no raw JSON."""
    inject_employee_os_styles(st)
    workspace = build_employee_os_workspace(report_id, employee_cycle=employee_cycle, report_v3=report_v3)
    st.markdown('<div class="iida-os">', unsafe_allow_html=True)
    st.markdown("## Employee OS")
    st.caption("Your AI company — operating in real time.")

    left, right = st.columns([1.45, 1])
    with left:
        render_company_dashboard(st, workspace["dashboard"])
        st.divider()
        render_employee_cards(st, workspace["employees"])
        st.divider()
        render_deliverables_panel(st, workspace["deliverables"])

    with right:
        render_founder_live_panel(st, workspace.get("founder_live") or {})
        st.divider()
        render_war_room_panel(st, workspace.get("war_room") or {}, report_id=report_id)
        st.divider()
        render_activity_feed(st, workspace["activity"])
        st.divider()
        render_approval_center(st, workspace["approvals"], report_id=report_id, state_key=f"os_approvals_{report_id}")
        st.divider()
        render_chat_panel(
            st,
            report_id=report_id,
            chat_employees=workspace["chat_employees"],
            founder_id=workspace.get("founder_id"),
            report_context=report_v3,
        )
    st.markdown("</div>", unsafe_allow_html=True)
