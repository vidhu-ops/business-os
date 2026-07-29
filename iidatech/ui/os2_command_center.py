"""Employee OS 2 - command center, CRM tracker, team hiring, integrations guide."""
from __future__ import annotations

import re
from typing import Any

from iidatech.execution.employees import CORE_ROLES, default_roles_for_business_type, hire_default_team, infer_business_type
from iidatech.execution.execution_logger import list_tool_executions
from iidatech.execution.memory_engine import load_team_shared_memory
from iidatech.execution.session_api_keys import SUPPORTED_PROVIDERS, provider_label, provider_portal_url
from iidatech.execution.task_engine import hire_employee
from iidatech.execution.team_memory import get_shared_team_memory
from iidatech.integrations.sales import list_pipeline_leads
from iidatech.storage.execution_repository import list_employees, list_tasks, list_team_messages
from iidatech.ui.view_models import build_war_room_debate
from iidatech.ui.workspace import render_war_room_panel

_BASE_HARNESS_ROLES = {
    "sales_lead": "Sales Lead",
    "growth_marketer": "Growth Marketer",
    "research_analyst": "Research Analyst",
    "creative_producer": "Growth Marketer",
    "ops_manager": "Operations Manager",
}


def ensure_os2_team(report_id: str, *, topic: str, industry: str, geography: str) -> list[dict[str, Any]]:
    roster = list_employees(report_id, active_only=False)
    if roster:
        return roster
    bt = infer_business_type(industry=industry, topic=topic)
    return hire_default_team(report_id, business_type=bt)


def _custom_harness_key(report_id: str) -> str:
    return f"os2_custom_harnesses_{report_id}"


def load_custom_harnesses(st: Any, report_id: str) -> list[dict[str, Any]]:
    raw = st.session_state.get(_custom_harness_key(report_id)) or []
    return [h for h in raw if isinstance(h, dict) and h.get("id")]


def save_custom_harness(st: Any, report_id: str, harness: dict[str, Any]) -> None:
    key = _custom_harness_key(report_id)
    items = load_custom_harnesses(st, report_id)
    items = [h for h in items if h.get("id") != harness.get("id")]
    items.append(harness)
    st.session_state[key] = items


def render_command_center(st: Any, *, report_id: str, topic: str, geography: str, harness_labels: dict[str, str]) -> None:
    st.markdown("### Command center")
    st.caption("Live tracker for tool runs, CRM leads, tasks, and agent status.")
    employees = list_employees(report_id)
    tasks = list_tasks(report_id)
    leads = list_pipeline_leads(report_id, limit=25)
    exec_logs = list_tool_executions(report_id, limit=20)
    memory = get_shared_team_memory(report_id)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Team", len(employees))
    c2.metric("Open tasks", sum(1 for t in tasks if t.get("status") != "completed"))
    c3.metric("CRM leads", len(leads))
    c4.metric("Tool runs", len(exec_logs))
    c5.metric("Harnesses", len(harness_labels))
    rows = []
    for emp in employees:
        eid = str(emp.get("employee_id") or "")
        emp_tasks = [t for t in tasks if t.get("owner_employee_id") == eid and t.get("status") != "completed"]
        emp_tools = [log for log in exec_logs if str(log.get("employee_id") or "") == eid]
        last_tool = str(emp_tools[0].get("tool_name") or "-") if emp_tools else "-"
        status = "working" if emp_tools else ("blocked" if any(t.get("status") == "blocked" for t in emp_tasks) else "idle")
        rows.append({"Employee": emp.get("name") or emp.get("role"), "Role": emp.get("role"), "Status": status, "Open tasks": len(emp_tasks), "Last tool": last_tool})
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    else:
        st.info("Hire the team under Team and hiring, then run agents under Agents.")
    if exec_logs:
        st.markdown("**Recent tool runs**")
        st.dataframe([{"When": str(log.get("created_at") or "")[:19], "Tool": log.get("tool_name"), "OK": log.get("success"), "Verified": log.get("verified")} for log in exec_logs[:12]], use_container_width=True, hide_index=True)
    if leads:
        st.markdown("**CRM pipeline**")
        st.dataframe([{"Company": l.get("company") or l.get("name"), "Contact": l.get("name"), "Email": l.get("email"), "Status": l.get("status")} for l in leads[:15]], use_container_width=True, hide_index=True)
    if memory.get("last_leads_csv"):
        st.caption(f"Latest leads CSV: {memory.get('last_leads_csv')}")

    st.markdown("**Team activity**")
    role_by_id = {str(e.get("employee_id")): str(e.get("role") or e.get("name")) for e in employees}
    messages = list_team_messages(report_id, limit=25)
    if messages:
        feed = []
        for msg in messages[-15:]:
            sender = role_by_id.get(str(msg.get("sender_id") or ""), str(msg.get("sender_id") or "team")[:12])
            mode = str(msg.get("mode") or "")
            text = str(msg.get("message") or "")[:200]
            feed.append({"When": str(msg.get("created_at") or "")[:19], "From": sender, "Mode": mode, "Message": text})
        st.dataframe(feed, use_container_width=True, hide_index=True)
    else:
        st.caption("Messages appear here when agents complete tasks or debate in the war room.")

    c_run1, c_run2 = st.columns(2)
    with c_run1:
        if st.button("Run full company cycle (all agents)", key=f"os2_company_cycle_{report_id}", type="primary"):
            try:
                from iidatech.execution.agent_runtime import run_agent_company_cycle

                ctx = st.session_state.get("business_builder_current_report_context") or {}
                v3 = ctx.get("report_v3") if isinstance(ctx.get("report_v3"), dict) else ctx
                with st.spinner("Running all agents — brains, tools, messages, debates..."):
                    out = run_agent_company_cycle(report_id, report_v3=v3 if isinstance(v3, dict) else None)
                st.session_state[f"os2_last_cycle_{report_id}"] = out
                st.success(f"Cycle complete — {len(out.get('agent_outputs') or [])} agents ran.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc)[:300])
    with c_run2:
        if st.button("Run company day (morning → work → evening)", key=f"os2_company_day_{report_id}"):
            try:
                from iidatech.execution.company_loop import end_company_day, run_company_cycle, start_company_day

                ctx = st.session_state.get("business_builder_current_report_context") or {}
                v3 = ctx.get("report_v3") if isinstance(ctx.get("report_v3"), dict) else ctx
                goals = [f"Grow {topic}", "Book discovery calls", "Launch pilot campaign"]
                start_company_day(report_id, goals, report_v3=v3 if isinstance(v3, dict) else None)
                run_company_cycle(report_id, report_v3=v3 if isinstance(v3, dict) else None)
                end_company_day(report_id, report_v3=v3 if isinstance(v3, dict) else None)
                st.success("Company day simulated.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc)[:300])


def render_team_hiring(st: Any, *, report_id: str, topic: str, industry: str, geography: str) -> None:
    st.markdown("### Team and hiring")
    ensure_os2_team(report_id, topic=topic, industry=industry, geography=geography)
    st.dataframe([{"Name": e.get("name"), "Role": e.get("role"), "Dept": e.get("department")} for e in list_employees(report_id)], use_container_width=True, hide_index=True)
    with st.expander("Add catalog role", expanded=False):
        existing = {str(e.get("role")) for e in list_employees(report_id)}
        for spec in default_roles_for_business_type(infer_business_type(industry=industry, topic=topic)):
            if spec["role"] in existing:
                continue
            if st.button(f"Hire {spec['role']}", key=f"os2_hire_{spec['role']}_{report_id}"):
                hire_employee(report_id, name=f"Virtual {spec['role']}", role=spec["role"], department=spec["department"], authority_level=int(spec["authority_level"]))
                st.rerun()
    with st.form(f"os2_custom_hire_{report_id}"):
        name = st.text_input("Custom hire name")
        role = st.selectbox("Role template", sorted(set(_BASE_HARNESS_ROLES.values())))
        if st.form_submit_button("Add to roster") and name.strip():
            dept = next((r["department"] for r in CORE_ROLES if r["role"] == role), "Operations")
            hire_employee(report_id, name=name.strip(), role=role, department=dept, authority_level=6)
            st.rerun()


def render_company_memory(st: Any, *, report_id: str) -> None:
    st.markdown("### Company memory")
    merged = {**get_shared_team_memory(report_id), **load_team_shared_memory(report_id)}
    st.json(merged if merged else {"note": "Memory populates as agents execute tools."})


def render_war_room(st: Any, *, report_id: str) -> None:
    ensure_os2_team(report_id, topic="", industry="", geography="")
    render_war_room_panel(st, build_war_room_debate(report_id), report_id=report_id)

    from iidatech.storage.execution_repository import list_employees, list_team_messages

    employees = list_employees(report_id)
    role_by_id = {str(e.get("employee_id")): str(e.get("role") or e.get("name")) for e in employees}
    war_msgs = [m for m in list_team_messages(report_id, limit=40) if str(m.get("mode") or "") == "war_room"]
    if war_msgs:
        st.markdown("**Team channel**")
        for msg in war_msgs[-12:]:
            who = role_by_id.get(str(msg.get("sender_id") or ""), "Team")
            st.markdown(f"**{who}** · {str(msg.get('created_at') or '')[:16]}")
            st.write(str(msg.get("message") or ""))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Run team debate sync", key=f"os2_debate_{report_id}"):
            try:
                from iidatech.execution.agent_runtime import run_agent_company_cycle

                ctx = st.session_state.get("business_builder_current_report_context") or {}
                v3 = ctx.get("report_v3") if isinstance(ctx.get("report_v3"), dict) else ctx
                run_agent_company_cycle(report_id, report_v3=v3 if isinstance(v3, dict) else None)
                st.rerun()
            except Exception as exc:
                st.warning(str(exc)[:200])
    with col2:
        if st.button("Sync agent messages", key=f"os2_msg_sync_{report_id}"):
            st.rerun()


def render_custom_harness_builder(st: Any, *, report_id: str) -> list[dict[str, Any]]:
    st.markdown("### Custom harnesses")
    custom = load_custom_harnesses(st, report_id)
    for h in custom:
        st.caption(f"{h.get('name')} -> {h.get('base_harness_id')}")
    with st.form(f"os2_new_harness_{report_id}"):
        name = st.text_input("Name", placeholder="Priya - Partnerships")
        base = st.selectbox("Base agent", list(_BASE_HARNESS_ROLES.keys()), format_func=lambda k: _BASE_HARNESS_ROLES[k])
        tagline = st.text_input("Tagline", value="Custom workflows")
        starters = st.text_area("Starters (one per line)", value="Find 10 leads")
        if st.form_submit_button("Create") and name.strip():
            slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:24] or "agent"
            save_custom_harness(st, report_id, {"id": f"custom_{slug}", "name": name.strip(), "role": _BASE_HARNESS_ROLES[base], "base_harness_id": base, "tagline": tagline, "starters": [s.strip() for s in starters.splitlines() if s.strip()][:5]})
            st.rerun()
    return load_custom_harnesses(st, report_id)


def render_integrations_guide(st: Any) -> None:
    st.markdown("### APIs, OAuth, and direct posting")
    st.markdown("**No keys:** drafts, command center, war room, hiring, memory. **Perplexity:** live leads/search. **LLM keys:** polish copy. **OAuth:** direct post/send to LinkedIn, email, CRM (Phase 2).")
    for prov in SUPPORTED_PROVIDERS:
        url = provider_portal_url(prov)
        if url:
            st.markdown(f"- [{provider_label(prov)}]({url})")
    for label, url in [("LinkedIn Developers", "https://www.linkedin.com/developers/"), ("Google Cloud", "https://console.cloud.google.com/"), ("HubSpot", "https://developers.hubspot.com/")]:
        st.markdown(f"- OAuth hub: [{label}]({url})")
