"""Autonomous company operating loop -- morning goals, agent workday, evening brief."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from iidatech.execution.agent_runtime import run_agent_company_cycle
from iidatech.execution.company_state import load_company_state, update_company_state
from iidatech.execution.long_memory import on_kpi_change
from iidatech.execution.memory_engine import record_work_memory, update_team_shared_memory
from iidatech.execution.performance import record_kpi
from iidatech.execution.task_engine import assign_task, complete_task, create_task
from iidatech.storage.execution_repository import (
    get_employee,
    list_employees,
    list_kpi_history,
    list_tasks,
    list_team_messages,
)

_ROLE_TASK_HINTS: dict[str, tuple[str, ...]] = {
    "Growth Marketer": ("campaign", "growth", "ads", "linkedin", "pilot", "lead", "outreach"),
    "Sales Lead": ("sales", "pipeline", "outbound", "discovery", "proposal", "meeting"),
    "Research Analyst": ("research", "evidence", "competitor", "market"),
    "COO": ("ops", "workflow", "process", "standup", "blocker"),
    "Finance Manager": ("runway", "cash", "finance", "invoice", "pnl", "budget"),
}

_EMPTY_RESULT: dict[str, Any] = {
    "completed_tasks": [],
    "blocked_tasks": [],
    "messages": [],
    "kpi_changes": {},
    "founder_brief": {},
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _normalize_goals(founder_goals: Any) -> list[str]:
    if isinstance(founder_goals, str):
        return [g.strip() for g in founder_goals.split("\n") if g.strip()]
    if isinstance(founder_goals, list):
        return [str(g).strip() for g in founder_goals if str(g).strip()]
    if isinstance(founder_goals, dict):
        return [str(v).strip() for v in founder_goals.values() if str(v).strip()]
    return []


def _kpi_map(report_id: str) -> dict[str, float]:
    out: dict[str, float] = {}
    for row in list_kpi_history(report_id, limit=100):
        name = str(row.get("kpi_name") or "").strip()
        if not name:
            continue
        try:
            out[name] = float(row.get("kpi_value") or 0)
        except (TypeError, ValueError):
            continue
    state = load_company_state(report_id)
    for name, val in (state.get("kpis") or {}).items():
        try:
            out[str(name)] = float(val)
        except (TypeError, ValueError):
            continue
    return out


def _kpi_delta(before: dict[str, float], after: dict[str, float]) -> dict[str, float]:
    keys = set(before) | set(after)
    delta: dict[str, float] = {}
    for key in keys:
        diff = round(float(after.get(key, 0)) - float(before.get(key, 0)), 4)
        if diff:
            delta[key] = diff
    return delta


def _best_owner_for_task(title: str, employees: list[dict]) -> str | None:
    title_l = title.lower()
    best_id, best_score = None, 0
    for emp in employees:
        role = str(emp.get("role") or "")
        if role == "Founder":
            continue
        hints = _ROLE_TASK_HINTS.get(role, ())
        score = sum(1 for h in hints if h in title_l)
        if score > best_score:
            best_score, best_id = score, str(emp["employee_id"])
    if best_id:
        return best_id
    for emp in employees:
        if str(emp.get("role")) != "Founder":
            return str(emp["employee_id"])
    return None


def _pick_and_assign_tasks(report_id: str) -> list[dict[str, Any]]:
    employees = list_employees(report_id)
    assigned: list[dict[str, Any]] = []
    for task in list_tasks(report_id):
        if task.get("status") == "completed":
            continue
        if task.get("owner_employee_id"):
            continue
        owner = _best_owner_for_task(str(task.get("title") or ""), employees)
        if owner:
            assigned.append(assign_task(task["task_id"], owner) or task)
    return assigned


def _tasks_snapshot(report_id: str) -> tuple[list[dict], list[dict]]:
    tasks = list_tasks(report_id)
    completed = [t for t in tasks if t.get("status") == "completed"]
    blocked = [t for t in tasks if t.get("status") == "blocked" or t.get("blockers")]
    return completed, blocked


def _day_state(report_id: str) -> dict[str, Any]:
    from iidatech.execution.memory_engine import load_team_shared_memory

    shared = load_team_shared_memory(report_id)
    ctx = shared.get("company_context") if isinstance(shared.get("company_context"), dict) else {}
    return ctx.get("company_day") if isinstance(ctx.get("company_day"), dict) else {}


def _save_day_state(report_id: str, day: dict[str, Any]) -> None:
    update_team_shared_memory(report_id, {"company_day": day})


def _empty_brief(goals: list[str] | None = None) -> dict[str, Any]:
    return {
        "today": {},
        "risks": [],
        "needs_approval": [],
        "goals": goals or [],
        "generated_at": _now_iso(),
    }


def _format_currency(amount: float, currency: str = "INR") -> str:
    if currency == "INR":
        return f"₹{amount:,.0f}"
    return f"${amount:,.0f}"


def _build_evening_founder_brief(
    report_id: str,
    *,
    kpi_changes: dict[str, float],
    completed: list[dict],
    blocked: list[dict],
    messages: list[dict],
    agent_cycle: dict[str, Any] | None = None,
    report_v3: dict[str, Any] | None = None,
    founder_goals: list[str] | None = None,
) -> dict[str, Any]:
    today: dict[str, Any] = {}
    if kpi_changes.get("leads_generated"):
        today["leads_generated"] = int(kpi_changes["leads_generated"])
    if kpi_changes.get("qualified_leads"):
        today["qualified_leads"] = int(kpi_changes["qualified_leads"])
    meetings = int(kpi_changes.get("meetings_booked") or 0)
    if not meetings:
        meetings = sum(
            1
            for t in list_tasks(report_id)
            if "discovery" in str(t.get("title", "")).lower() or "meeting" in str(t.get("title", "")).lower()
        )
    if meetings:
        today["meetings_booked"] = meetings
    revenue = float(kpi_changes.get("revenue_added") or kpi_changes.get("mrr") or 0)
    if revenue:
        today["revenue_added"] = revenue
        today["revenue_added_display"] = _format_currency(revenue)

    risks: list[str] = []
    for t in blocked[:5]:
        for b in t.get("blockers") or []:
            if b and b not in risks:
                risks.append(str(b))
    if kpi_changes.get("cac", 0) > 0:
        risks.append("CAC rising")
    ctx = load_company_state(report_id)
    churn = (ctx.get("growth_metrics") or {}).get("churn_risk")
    if churn or any("churn" in str(r).lower() for r in risks):
        if "churn risk" not in risks:
            risks.append("churn risk")
    if report_v3:
        for row in (report_v3.get("risk_heatmap") or [])[:3]:
            if isinstance(row, dict):
                label = str(row.get("risk") or row.get("category") or "").strip()
                if label and label not in risks:
                    risks.append(label)

    needs_approval: list[str] = []
    for msg in messages:
        text = str(msg.get("message") or "").lower()
        if "approval" in text or "budget" in text:
            needs_approval.append(str(msg.get("message")))
    if agent_cycle:
        for out in agent_cycle.get("agent_outputs") or []:
            te = out.get("tool_execution") or {}
            for item in (te.get("result") or {}).get("outputs") or []:
                err = str(item.get("error") or "")
                if err.startswith("approval_required:"):
                    tool = str(item.get("tool") or "tool")
                    needs_approval.append(f"Approve {tool.replace('_', ' ')} spend")
            brain = out.get("brain") or {}
            for call in brain.get("tool_calls") or []:
                if isinstance(call, dict) and call.get("approved") is False:
                    budget = (call.get("payload") or {}).get("budget")
                    if budget:
                        needs_approval.append(_format_currency(float(budget)) + " ad budget")
    for goal in founder_goals or []:
        gl = str(goal).lower()
        if "budget" in gl or "₹" in goal or "$" in goal:
            needs_approval.append(str(goal) if "approve" in gl else f"Approve: {goal}")

    brief = {
        "today": today,
        "risks": risks[:8],
        "needs_approval": list(dict.fromkeys(needs_approval))[:8],
        "goals": founder_goals or [],
        "completed_tasks": completed[:25],
        "blocked_tasks": blocked[:25],
        "recommendations": (agent_cycle or {}).get("founder_brief", {}).get("recommendations", [])[:8],
        "generated_at": _now_iso(),
    }
    if agent_cycle and agent_cycle.get("founder_brief"):
        brief["cycle_summary"] = {
            "agents_run": len(agent_cycle.get("agent_outputs") or []),
            "urgent_issues": agent_cycle["founder_brief"].get("urgent_issues", [])[:5],
        }
    return brief


def _result(
    report_id: str,
    *,
    completed: list[dict] | None = None,
    blocked: list[dict] | None = None,
    messages: list[dict] | None = None,
    kpi_changes: dict[str, float] | None = None,
    founder_brief: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "report_id": report_id,
        "completed_tasks": completed or [],
        "blocked_tasks": blocked or [],
        "messages": messages or [],
        "kpi_changes": kpi_changes or {},
        "founder_brief": founder_brief or {},
    }


def start_company_day(
    report_id: str,
    founder_goals: Any,
    *,
    report_v3: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Morning: founder sets goals, baseline KPIs captured, day tasks seeded."""
    report_id = str(report_id or "").strip()
    goals = _normalize_goals(founder_goals)
    kpi_baseline = _kpi_map(report_id)

    update_team_shared_memory(report_id, {"goals": goals, "day_started_at": _now_iso()})
    day = {
        "status": "active",
        "started_at": _now_iso(),
        "founder_goals": goals,
        "kpi_baseline": kpi_baseline,
        "cycles_run": 0,
        "report_v3_attached": bool(report_v3),
    }
    _save_day_state(report_id, day)

    for goal in goals[:6]:
        title = goal if len(goal) <= 240 else goal[:237] + "..."
        existing = [t for t in list_tasks(report_id) if str(t.get("title")) == title and t.get("status") != "completed"]
        if not existing:
            create_task(report_id, title=title, priority="high")

    brief = _empty_brief(goals)
    brief["phase"] = "morning"
    brief["message"] = f"Day started with {len(goals)} founder goal(s)."
    return _result(report_id, founder_brief=brief, kpi_changes={})


def run_company_cycle(
    report_id: str,
    *,
    report_v3: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Agents review goals, pick tasks, execute tools, communicate, escalate blockers."""
    report_id = str(report_id or "").strip()
    day = _day_state(report_id)
    if not day:
        start_company_day(report_id, [], report_v3=report_v3)
        day = _day_state(report_id)

    kpi_before = _kpi_map(report_id)
    since = day.get("started_at")
    msg_before = len(list_team_messages(report_id, since=since))

    _pick_and_assign_tasks(report_id)
    cycle = run_agent_company_cycle(report_id, report_v3=report_v3)

    for out in cycle.get("agent_outputs") or []:
        eid = str(out.get("employee_id") or "")
        brain = out.get("brain") or {}
        te = out.get("tool_execution") or {}
        if te.get("success") and eid:
            insight = str(brain.get("action") or "")
            if insight:
                record_work_memory(eid, insight=f"{out.get('role')}: {insight}")
        assigned = [
            t for t in list_tasks(report_id)
            if t.get("owner_employee_id") == eid and t.get("status") not in ("completed", "blocked")
        ]
        if te.get("success") and assigned and float(brain.get("confidence") or 0) >= 0.7:
            complete_task(assigned[0]["task_id"])

    kpi_after = _kpi_map(report_id)
    kpi_changes = _kpi_delta(kpi_before, kpi_after)
    for key, delta in kpi_changes.items():
        try:
            on_kpi_change(report_id, None, key, float(kpi_before.get(key, 0)), float(kpi_after.get(key, 0)))
        except (TypeError, ValueError):
            pass
    completed, blocked = _tasks_snapshot(report_id)
    messages = list_team_messages(report_id, since=since)[msg_before:]

    day["cycles_run"] = int(day.get("cycles_run") or 0) + 1
    day["last_cycle_at"] = _now_iso()
    day["last_agent_cycle"] = {
        "agent_outputs": [
            {"role": o.get("role"), "brain": o.get("brain"), "tool_execution": o.get("tool_execution")}
            for o in (cycle.get("agent_outputs") or [])
        ],
        "founder_brief": cycle.get("founder_brief"),
    }
    _save_day_state(report_id, day)

    goals = day.get("founder_goals") or []
    brief = _build_evening_founder_brief(
        report_id,
        kpi_changes=kpi_changes,
        completed=completed,
        blocked=blocked,
        messages=messages,
        agent_cycle=cycle,
        report_v3=report_v3,
        founder_goals=goals,
    )
    brief["phase"] = "workday"
    update_team_shared_memory(report_id, {"last_company_cycle": brief})

    return _result(
        report_id,
        completed=completed,
        blocked=blocked,
        messages=messages,
        kpi_changes=kpi_changes,
        founder_brief=brief,
    )


def end_company_day(
    report_id: str,
    *,
    report_v3: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evening: submit reports, update KPIs, deliver founder brief."""
    report_id = str(report_id or "").strip()
    day = _day_state(report_id)
    if not day:
        start_company_day(report_id, [], report_v3=report_v3)
        day = _day_state(report_id)

    baseline = day.get("kpi_baseline") if isinstance(day.get("kpi_baseline"), dict) else {}
    kpi_after = _kpi_map(report_id)
    kpi_changes = _kpi_delta({k: float(v) for k, v in baseline.items()}, kpi_after)

    if kpi_changes.get("leads_generated"):
        record_kpi(report_id, "daily_leads", kpi_changes["leads_generated"], notes="company_day_close")
    if kpi_changes.get("mrr"):
        update_company_state(report_id, {"revenue": float(load_company_state(report_id).get("revenue") or 0) + kpi_changes["mrr"]})

    since = day.get("started_at")
    messages = list_team_messages(report_id, since=since)
    completed, blocked = _tasks_snapshot(report_id)

    brief = _build_evening_founder_brief(
        report_id,
        kpi_changes=kpi_changes,
        completed=completed,
        blocked=blocked,
        messages=messages,
        agent_cycle=day.get("last_agent_cycle"),
        report_v3=report_v3,
        founder_goals=day.get("founder_goals") or [],
    )
    brief["phase"] = "evening"
    brief["status"] = "closed"

    day["status"] = "closed"
    day["ended_at"] = _now_iso()
    day["final_brief"] = brief
    _save_day_state(report_id, day)
    update_team_shared_memory(report_id, {"founder_brief": brief, "company_day_closed": _now_iso()})

    return _result(
        report_id,
        completed=completed,
        blocked=blocked,
        messages=messages,
        kpi_changes=kpi_changes,
        founder_brief=brief,
    )
