"""Action executor -- runs employee tools with real connectors when configured."""

from __future__ import annotations

from typing import Any

from iidatech.execution.execution_logger import log_tool_execution
from iidatech.execution.real_tool_handlers import TOOL_HANDLERS
from iidatech.execution.tool_outcomes import tool_result
from iidatech.execution.tool_registry import get_tool, resolve_tool_name


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _attach_tool_meta(out: dict[str, Any], spec: dict | None) -> dict[str, Any]:
    spec = spec or {}
    out.setdefault("execution_mode", spec.get("execution_mode", out.get("execution_mode", "simulated")))
    out.setdefault("verified", bool(spec.get("verified", out.get("verified", False))))
    out.setdefault("task_id", out.get("task_id") or "")
    out.setdefault("metrics", out.get("metrics") or {})
    out.setdefault("logs", out.get("logs") or [])
    out.setdefault("errors", out.get("errors") or ([] if not out.get("error") else [out.get("error")]))
    return out


def execute_tool(
    tool_name: str,
    payload: dict[str, Any] | None,
    *,
    context: dict[str, Any] | None = None,
    approved: bool = False,
) -> dict[str, Any]:
    resolved = resolve_tool_name(tool_name)
    spec = get_tool(resolved)
    if not spec:
        return tool_result(success=False, error=f"unknown_tool:{tool_name}", execution_mode="simulated", verified=False)
    if spec.get("requires_approval") and not approved:
        return tool_result(success=False, error=f"approval_required:{resolved}", execution_mode="simulated", verified=False)
    handler = TOOL_HANDLERS.get(resolved)
    if not handler:
        return tool_result(success=False, error=f"no_handler:{resolved}", execution_mode="simulated", verified=False)
    ctx = dict(context or {})
    pl = dict(payload or {})
    if ctx.get("report_id") and "report_id" not in pl:
        pl["report_id"] = ctx["report_id"]
    try:
        out = handler(pl, ctx)
        out = _attach_tool_meta(out, spec)
        report_id = str(ctx.get("report_id") or pl.get("report_id") or "")
        if report_id:
            log_tool_execution(
                report_id=report_id,
                tool_name=resolved,
                outcome=out,
                task_id=str(out.get("task_id") or ctx.get("task_id") or ""),
                employee_id=str(ctx.get("employee_id") or ""),
            )
        return out
    except Exception as exc:
        return tool_result(success=False, error=str(exc)[:240], execution_mode="simulated", verified=False, errors=[str(exc)[:240]])


def execute_agent_action(agent_id: str, action: dict[str, Any], *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = dict(context or {})
    ctx["employee_id"] = agent_id
    tool_calls = _as_list(action.get("tool_calls"))
    if not tool_calls:
        return tool_result(success=True, result={"executed": 0, "outputs": []}, execution_mode="simulated", verified=False)
    outputs, merged_kpis, artifacts = [], {}, []
    any_ok = False
    for call in tool_calls:
        if not isinstance(call, dict):
            continue
        out = execute_tool(
            str(call.get("tool") or call.get("tool_name") or ""),
            _as_dict(call.get("payload")),
            context=ctx,
            approved=bool(call.get("approved")),
        )
        outputs.append({"tool": call.get("tool"), **out})
        any_ok = any_ok or bool(out.get("success"))
        if out.get("verified") and out.get("kpis"):
            merged_kpis.update(out.get("kpis") or {})
        artifacts.extend(out.get("artifacts") or [])
    return tool_result(
        success=any_ok,
        result={"executed": len(outputs), "outputs": outputs},
        kpis=merged_kpis,
        artifacts=artifacts,
        execution_mode="real" if any(o.get("execution_mode") == "real" for o in outputs) else "simulated",
        verified=any(o.get("verified") for o in outputs),
    )


def execute_task(task: dict[str, Any], *, context: dict[str, Any] | None = None) -> dict[str, Any]:
    ctx = dict(context or {})
    ctx["task_id"] = str(task.get("task_id") or "")
    title = str(task.get("title") or "").lower()
    owner = str(task.get("owner_employee_id") or ctx.get("employee_id") or "")
    if "competitor" in title or "evidence" in title:
        tool_calls = [{"tool": "competitor_lookup", "payload": {}}, {"tool": "evidence_writer", "payload": {"gaps": [title]}, "approved": True}]
    elif "runway" in title or "cash" in title:
        # Only run with founder-supplied figures; never fabricate "verified" financials.
        fin = ctx.get("verified_financials") if isinstance(ctx.get("verified_financials"), dict) else {}
        payload: dict[str, Any] = {}
        if fin.get("cash") is not None and fin.get("monthly_burn") is not None:
            payload = {"verified_financials": True, "cash": fin["cash"], "monthly_burn": fin["monthly_burn"]}
        tool_calls = [{"tool": "runway_calculator", "payload": payload}]
    else:
        tool_calls = [{"tool": "task_scheduler", "payload": {"tasks": [task.get("title")]}}]
    return execute_agent_action(owner, {"tool_calls": tool_calls}, context=ctx)