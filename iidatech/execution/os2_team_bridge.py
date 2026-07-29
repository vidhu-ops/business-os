"""Bridge OS2 harness agents to SQL employee roster + team messaging."""
from __future__ import annotations

from typing import Any

HARNESS_ROLE_MAP: dict[str, str] = {
    "sales_lead": "Sales Lead",
    "growth_marketer": "Growth Marketer",
    "research_analyst": "Research Analyst",
    "creative_producer": "Growth Marketer",
    "ops_manager": "Operations Manager",
}


def employee_id_for_harness(report_id: str, harness_id: str) -> str | None:
    """Resolve SQL employee_id for a harness (for messaging + tool logs)."""
    role = HARNESS_ROLE_MAP.get(str(harness_id or "").strip())
    if not role:
        return None
    try:
        from iidatech.storage.execution_repository import list_employees

        for emp in list_employees(report_id):
            if str(emp.get("role") or "") == role:
                return str(emp.get("employee_id") or "") or None
    except Exception:
        return None
    return None


def notify_task_completion(
    report_id: str,
    item: dict[str, Any],
    result: dict[str, Any],
    *,
    report_context: dict[str, Any] | None = None,
) -> None:
    """Post completion to war room + notify next assignee in checklist."""
    from iidatech.execution.chat_engine import send_agent_message
    from iidatech.execution.task_engine import complete_task, founder_employee_id
    from iidatech.storage.execution_repository import list_employees

    harness_id = str(item.get("harness_id") or "")
    sender = employee_id_for_harness(report_id, harness_id) or f"os2_{harness_id}"
    title = str(item.get("title") or "Task")
    status = str(item.get("status") or "")
    ok = status == "completed" and bool(result.get("success", True))
    arts = list(item.get("artifacts") or result.get("artifacts") or [])
    art_note = f" Files: {len(arts)}." if arts else ""
    summary = f"{'Completed' if ok else 'Failed'}: {title}.{art_note}"
    if not ok:
        summary += f" {str(item.get('error') or result.get('reply') or '')[:200]}"

    send_agent_message(report_id, sender, "war_room", summary, report_context=report_context)

    fid = founder_employee_id(report_id)
    if fid and sender != fid:
        send_agent_message(report_id, sender, fid, summary[:400], report_context=report_context)

    tid = str(item.get("sql_task_id") or "")
    if tid and ok:
        try:
            complete_task(tid)
        except Exception:
            pass

    # Hand off to next harness owner in checklist
    try:
        from iidatech.execution.os2_workflow import load_checklist
        from iidatech.execution.team_leader import next_runnable_item

        checklist = load_checklist(report_id)
        if not checklist:
            return
        nxt = next_runnable_item(checklist, auto_approve=True)
        if not nxt:
            return
        next_hid = str(nxt.get("harness_id") or "")
        next_eid = employee_id_for_harness(report_id, next_hid)
        if next_eid and next_eid != sender:
            handoff = f"Your turn: {nxt.get('title')} — prior step '{title}' is done."
            send_agent_message(report_id, sender, next_eid, handoff, report_context=report_context)
    except Exception:
        pass

    role_by_id = {str(e.get("employee_id")): str(e.get("role")) for e in list_employees(report_id)}
    if str(item.get("task_kind") or "").startswith("oauth") and not ok:
        prov = str(item.get("oauth_provider") or "integration")
        send_agent_message(
            report_id,
            sender,
            "war_room",
            f"OAuth blocked ({prov}): connect under Integrations tab, then re-run.",
            report_context=report_context,
        )
