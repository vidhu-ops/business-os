"""KPI tracking and daily founder operating cycle."""
from __future__ import annotations
from datetime import datetime, timezone
from iidatech.execution.long_memory import on_kpi_change
from iidatech.execution.team_memory import update_shared_team_memory
from iidatech.storage.execution_repository import insert_kpi_snapshot, list_employees, list_kpi_history, list_tasks

def record_kpi(report_id, kpi_name, kpi_value, notes="", *, employee_id=None):
    prior = None
    for row in list_kpi_history(report_id, limit=30):
        if str(row.get("kpi_name") or "") == str(kpi_name):
            try:
                prior = float(row.get("kpi_value"))
            except (TypeError, ValueError):
                prior = None
            break
    insert_kpi_snapshot(report_id, kpi_name, kpi_value, notes)
    try:
        new_v = float(kpi_value)
        if prior is not None:
            on_kpi_change(report_id, employee_id, str(kpi_name), prior, new_v)
    except (TypeError, ValueError):
        pass

def _is_delayed(task):
    due = task.get("due_date")
    if not due or task.get("status") == "completed":
        return False
    try:
        dt = datetime.fromisoformat(str(due).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt < datetime.now(timezone.utc)
    except ValueError:
        return False

def run_daily_company_cycle(report_id, *, report_v3=None):
    tasks = list_tasks(report_id)
    completed = [t for t in tasks if t.get("status") == "completed"]
    delayed = [t for t in tasks if _is_delayed(t)]
    blockers = [{"task_id": t["task_id"], "title": t.get("title"), "blockers": t.get("blockers") or []} for t in tasks if t.get("status") == "blocked" or t.get("blockers")]
    risks = []
    if report_v3:
        for row in (report_v3.get("risk_heatmap") or report_v3.get("risk_map") or [])[:5]:
            if isinstance(row, dict):
                risks.append({"risk": row.get("risk") or row.get("category"), "severity": row.get("severity") or row.get("probability"), "mitigation": row.get("mitigation")})
    kpis = list_kpi_history(report_id, limit=10)
    recommendations = []
    if delayed:
        recommendations.append(f"Clear {len(delayed)} delayed task(s) — reassign or extend due dates.")
    if blockers:
        recommendations.append(f"Resolve {len(blockers)} blocked task(s) before starting new work.")
    open_tasks = [t for t in tasks if t.get("status") != "completed"]
    unowned = [t for t in open_tasks if not t.get("owner_employee_id")]
    if unowned:
        recommendations.append(f"Assign owners to {len(unowned)} unowned open task(s).")
    if not kpis:
        recommendations.append("Log baseline KPIs (MRR, leads, CAC) to enable trend review.")
    if report_v3:
        w1 = (report_v3.get("execution_calendar") or {}).get("week_1") or {}
        if w1.get("actions"):
            recommendations.append(f"Week 1 focus: {w1['actions'][0]}")
    brief = {"generated_at": datetime.now(timezone.utc).isoformat(), "active_employees": len(list_employees(report_id)), "open_tasks": len(open_tasks), "top_recommendation": recommendations[0] if recommendations else "Maintain weekly KPI cadence."}
    update_shared_team_memory(report_id, {"last_daily_cycle": brief})
    return {"completed_tasks": completed[:20], "delayed_tasks": delayed[:20], "blockers": blockers, "risks": risks, "recommendations": recommendations, "founder_brief": brief}
