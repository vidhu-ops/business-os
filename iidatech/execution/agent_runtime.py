"""Autonomous agent company cycle — employees reason, act, and brief the founder."""
from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

from iidatech.execution.debate_engine import resolve_team_debates
from iidatech.execution.long_memory import on_collaboration, on_escalation_ignored, on_team_conflict
from iidatech.execution.chat_engine import send_agent_message
from iidatech.execution.employee_brains import run_employee_brain
from iidatech.execution.employee_profiles import build_employee_profile, profiles_for_team
from iidatech.execution.task_engine import block_task, complete_task, create_task, founder_employee_id
from iidatech.execution.team_memory import build_agent_context, update_shared_team_memory
from iidatech.execution.tool_runtime import run_brain_with_tools, runtime_summary
from iidatech.storage.execution_repository import list_employees, list_tasks


def _role_id_map(report_id: str) -> dict[str, str]:
    return {str(e.get("role")): str(e["employee_id"]) for e in list_employees(report_id)}


def _resolve_message_target(report_id: str, to_label: str, role_map: dict[str, str]) -> str | None:
    label = (to_label or "").strip()
    if label.lower() == "founder":
        return founder_employee_id(report_id) or role_map.get("Founder")
    return role_map.get(label)


def _apply_brain_output(
    report_id: str,
    employee: dict[str, Any],
    brain: dict[str, Any],
    *,
    role_map: dict[str, str],
) -> dict[str, Any]:
    """Translate brain output into tasks, blocks, and messages."""
    applied: dict[str, Any] = {"sub_tasks_created": [], "messages_sent": [], "tasks_updated": []}
    eid = str(employee.get("employee_id"))

    for title in brain.get("sub_tasks") or []:
        if not str(title).strip():
            continue
        task = create_task(report_id, title=str(title)[:240], owner_employee_id=eid, priority="medium")
        applied["sub_tasks_created"].append(task.get("task_id"))

    action = str(brain.get("action") or "")
    assigned = _tasks_for_employee(report_id, eid)
    if action == "unblock_task" and assigned:
        for t in assigned:
            if t.get("status") == "blocked" and t.get("blockers"):
                from iidatech.execution.task_engine import unblock_task

                unblock_task(t["task_id"], t["blockers"][0])
                applied["tasks_updated"].append(t["task_id"])
                break
    elif action == "complete_support" and assigned:
        pass  # reserved for future auto-complete rules

    for blocker in brain.get("blockers") or []:
        if assigned:
            block_task(assigned[0]["task_id"], str(blocker))
            applied["tasks_updated"].append(assigned[0]["task_id"])

    for msg in brain.get("messages") or []:
        if not isinstance(msg, dict):
            continue
        receiver = _resolve_message_target(report_id, str(msg.get("to", "")), role_map)
        text = str(msg.get("text") or "").strip()
        if receiver and text:
            record = send_agent_message(report_id, eid, receiver, text)
            applied["messages_sent"].append(record.get("message_id"))
            on_collaboration(report_id, eid, receiver, note=f"Messaged {msg.get('to')}: {text[:80]}")

    return applied


def _tasks_for_employee(report_id: str, employee_id: str) -> list[dict[str, Any]]:
    return [t for t in list_tasks(report_id) if t.get("owner_employee_id") == employee_id and t.get("status") != "completed"]


def _build_founder_brief(
    report_id: str,
    *,
    agent_outputs: list[dict[str, Any]],
    report_v3: dict[str, Any] | None,
) -> dict[str, Any]:
    tasks = list_tasks(report_id)
    completed = [t for t in tasks if t.get("status") == "completed"]
    active = [t for t in tasks if t.get("status") not in ("completed", "blocked")]
    blocked = [t for t in tasks if t.get("status") == "blocked" or t.get("blockers")]

    urgent: list[dict[str, Any]] = []
    for out in agent_outputs:
        if out.get("brain", {}).get("action", "").startswith("escalate") or out.get("brain", {}).get("blockers"):
            urgent.append({
                "role": out.get("role"),
                "action": out.get("brain", {}).get("action"),
                "issue": (out.get("brain", {}).get("blockers") or ["review needed"])[0],
                "confidence": out.get("brain", {}).get("confidence"),
            })
    if report_v3:
        for r in (report_v3.get("risk_heatmap") or [])[:3]:
            if isinstance(r, dict) and r.get("severity") in ("critical", "high"):
                urgent.append({"role": "risk_monitor", "action": "risk_alert", "issue": r.get("risk"), "confidence": r.get("probability")})

    recommendations: list[str] = []
    for out in sorted(agent_outputs, key=lambda x: float((x.get("brain") or {}).get("confidence") or 0), reverse=True)[:5]:
        brain = out.get("brain") or {}
        recommendations.append(f"[{out.get('role')}] {brain.get('action')}: {brain.get('reasoning', '')[:160]}")

    return {
        "completed_tasks": completed[:25],
        "active_tasks": active[:25],
        "blocked_tasks": blocked[:25],
        "urgent_issues": urgent[:10],
        "recommendations": recommendations[:8],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_agent_company_cycle(report_id: str, *, report_v3: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Autonomous company loop:
    1. employees load tasks
    2. each employee runs brain
    3. tasks updated / subtasks created
    4. blockers assigned
    5. messages sent
    6. founder brief generated
    """
    employees = list_employees(report_id)
    profiles = profiles_for_team(employees)
    role_map = _role_id_map(report_id)
    all_tasks = list_tasks(report_id)

    agent_outputs: list[dict[str, Any]] = []
    for emp in employees:
        role = str(emp.get("role") or "")
        if role == "Founder":
            continue  # founder receives brief, does not run worker loop first pass
        profile = build_employee_profile(emp)
        context = build_agent_context(report_id, emp["employee_id"], report_context=report_v3 or {})
        context["employee_profile"] = profile
        context["team_tasks"] = all_tasks

        brain = run_employee_brain(emp, context)
        exec_ctx = {**context, "report_id": report_id}
        tool_execution = run_brain_with_tools(emp, brain, context=exec_ctx)
        applied = _apply_brain_output(report_id, emp, brain, role_map=role_map)
        applied["tool_execution"] = tool_execution
        agent_outputs.append({
            "employee_id": emp["employee_id"],
            "name": emp.get("name"),
            "role": role,
            "brain": brain,
            "tool_execution": tool_execution,
            "applied": applied,
        })

    escalations = [o for o in agent_outputs if str((o.get("brain") or {}).get("action") or "").startswith("escalate")]
    launches = [
        o for o in agent_outputs
        if str((o.get("brain") or {}).get("action") or "") in ("launch_experiment", "launch_campaign", "run_paid_pilot")
    ]
    for esc in escalations:
        issue = ((esc.get("brain") or {}).get("blockers") or ["evidence gap"])[0]
        for launch in launches:
            if launch.get("employee_id") != esc.get("employee_id"):
                on_escalation_ignored(
                    report_id,
                    str(esc["employee_id"]),
                    str(launch["employee_id"]),
                    issue=str(issue),
                )

    kpi_changes: dict[str, float] = {}
    for out in agent_outputs:
        te = out.get("tool_execution") or {}
        for k, v in (te.get("kpis") or {}).items():
            try:
                kpi_changes[str(k)] = float(v)
            except (TypeError, ValueError):
                pass

    debates = resolve_team_debates(report_id, agent_outputs=agent_outputs, kpi_changes=kpi_changes)

    founder_brief = _build_founder_brief(report_id, agent_outputs=agent_outputs, report_v3=report_v3)
    fid = founder_employee_id(report_id)
    if fid and founder_brief.get("recommendations"):
        top = founder_brief["recommendations"][0]
        send_agent_message(report_id, fid, "war_room", f"Daily brief: {top}")

    update_shared_team_memory(report_id, {
        "last_agent_cycle": {
            "generated_at": founder_brief.get("generated_at"),
            "agents_run": len(agent_outputs),
            "urgent_count": len(founder_brief.get("urgent_issues") or []),
            "debates_run": len(debates),
        },
        "founder_brief": founder_brief,
    })

    return {
        "report_id": report_id,
        "profiles": profiles,
        "agent_outputs": agent_outputs,
        "founder_brief": founder_brief,
        "employee_dashboard": runtime_summary(agent_outputs),
        "debates": debates,
    }
