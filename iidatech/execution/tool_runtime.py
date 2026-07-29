"""Tool execution runtime -- plan, execute tools, aggregate measurable outputs."""
from __future__ import annotations

from typing import Any

from iidatech.execution.action_executor import execute_agent_action, execute_task, execute_tool
from iidatech.execution.employee_profiles import get_tool_access
from iidatech.execution.performance import record_kpi
from iidatech.execution.team_memory import update_shared_team_memory
from iidatech.execution.tool_outcomes import badge_for
from iidatech.execution.tool_registry import get_tool, list_tools, resolve_tool_name, tools_for_role


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _allowed_tools(role: str) -> set[str]:
    return {resolve_tool_name(t) for t in get_tool_access(role)}


def _filter_tool_calls(tool_calls: list, role: str) -> list[dict]:
    allowed = _allowed_tools(role)
    out = []
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        name = resolve_tool_name(str(call.get("tool") or call.get("tool_name") or ""))
        if name in allowed or "all_read" in get_tool_access(role):
            out.append({**call, "tool": name})
    return out


def run_tool_calls(
    employee_id: str,
    role: str,
    tool_calls: list[dict],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute filtered tool calls for an employee."""
    filtered = _filter_tool_calls(tool_calls, role)
    if tool_calls and not filtered:
        requested = [str(c.get("tool") or c.get("tool_name") or "?") for c in tool_calls if isinstance(c, dict)]
        return {
            "success": False,
            "verified": False,
            "result": {"outputs": []},
            "artifacts": [],
            "kpis": {},
            "error": f"No permitted tools for role '{role}' (requested: {', '.join(requested[:5])}). Check TOOL_MATRIX.",
        }
    action = {"tool_calls": filtered, "role": role}
    result = execute_agent_action(employee_id, action, context=context)
    report_id = str((context or {}).get("report_id") or "")
    verified_kpis = result.get("kpis") or {}
    if report_id and verified_kpis and result.get("verified"):
        for k, v in verified_kpis.items():
            record_kpi(report_id, k, v, notes="verified")
        update_shared_team_memory(
            report_id,
            {
                "last_tool_run": {
                    "employee_id": employee_id,
                    "role": role,
                    "tools": [c.get("tool") for c in filtered],
                    "kpis": verified_kpis,
                    "artifacts": result.get("artifacts"),
                    "execution_mode": result.get("execution_mode"),
                    "verified": True,
                }
            },
        )
    elif report_id:
        update_shared_team_memory(
            report_id,
            {
                "last_tool_run": {
                    "employee_id": employee_id,
                    "role": role,
                    "tools": [c.get("tool") for c in filtered],
                    "kpis": {},
                    "artifacts": result.get("artifacts"),
                    "execution_mode": result.get("execution_mode"),
                    "verified": bool(result.get("verified")),
                }
            },
        )
    return result


def run_brain_with_tools(
    employee: dict[str, Any],
    brain: dict[str, Any],
    *,
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute tool_calls from brain output; attach execution results."""
    ctx = dict(context or {})
    ctx["employee_id"] = str(employee.get("employee_id") or "")
    ctx.setdefault("report_id", ctx.get("report_id"))
    role = str(employee.get("role") or brain.get("role") or "")
    tool_calls = _filter_tool_calls(_as_list(brain.get("tool_calls")), role)
    if not tool_calls:
        return {"success": True, "result": {"executed": 0}, "kpis": {}, "artifacts": []}
    return run_tool_calls(ctx["employee_id"], role, tool_calls, context=ctx)


def build_employee_dashboard_row(
    employee: dict[str, Any],
    *,
    brain: dict[str, Any] | None = None,
    tool_execution: dict[str, Any] | None = None,
    current_task: str | None = None,
) -> dict[str, Any]:
    """Dashboard row: name, role, task, tools, outputs, KPIs."""
    brain = brain or {}
    tool_execution = tool_execution or {}
    kpis = dict(tool_execution.get("kpis") or {})
    tools_used = [str(c.get("tool")) for c in _as_list(brain.get("tool_calls")) if c.get("tool")]
    outputs = []
    tool_badges: list[str] = []
    for out in _as_list((tool_execution.get("result") or {}).get("outputs")):
        if isinstance(out, dict):
            tool_badges.append(badge_for(out))
            if out.get("verified") and out.get("success"):
                outputs.append(out.get("result") or {})
    return {
        "name": employee.get("name"),
        "role": employee.get("role"),
        "current_task": current_task or (brain.get("plan") or ["General execution"])[0] if brain.get("plan") else brain.get("action"),
        "tools_used": tools_used,
        "tool_badges": tool_badges,
        "outputs_produced": outputs,
        "kpis_changed": kpis if tool_execution.get("verified") else {},
        "execution_mode": tool_execution.get("execution_mode", "simulated"),
        "verified": bool(tool_execution.get("verified")),
        "confidence": brain.get("confidence"),
        "action": brain.get("action"),
    }


def runtime_summary(agent_outputs: list[dict]) -> list[dict[str, Any]]:
    """Build dashboard rows for all agents in a cycle."""
    rows = []
    for out in agent_outputs:
        emp = {"employee_id": out.get("employee_id"), "name": out.get("name"), "role": out.get("role")}
        rows.append(
            build_employee_dashboard_row(
                emp,
                brain=out.get("brain"),
                tool_execution=out.get("tool_execution"),
                current_task=(out.get("brain") or {}).get("action"),
            )
        )
    return rows
