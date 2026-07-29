from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.services.workspace_context import workspace_report_context, workspace_report_id
from backend.services.workspaces import load_workspace, save_workspace
from iidatech.execution.employee_os2_harness import OS2_HARNESSES, execute_harness_job, merged_harnesses
from iidatech.execution.office_scope import (
    OfficeScope,
    SCOPE_MODES,
    department_for_harness,
    departments_for_harnesses,
)
from iidatech.execution.os2_api_keys import merge_api_keys
from iidatech.execution.os2_workflow import _WORKFLOW_ROOT, load_checklist, run_next_task, save_checklist
from iidatech.execution.plan_ingest import normalize_plan
from iidatech.execution.team_leader import build_checklist_from_plan
from iidatech.execution.taylor_pulse import build_taylor_pulse
from iidatech.integrations.oauth_store import connection_status_rows, is_connected, seed_workspace_from_env
from iidatech.ui.os2_command_center import ensure_os2_team

_SESSION_KEYS: dict[str, dict[str, str]] = {}
_CHAT_DIR_NAME = "agent_chats"


def _office_state_path(report_id: str) -> Path:
    p = _WORKFLOW_ROOT / str(report_id).strip() / "office_day_state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _chat_path(report_id: str, harness_id: str) -> Path:
    p = _WORKFLOW_ROOT / str(report_id).strip() / _CHAT_DIR_NAME / f"{harness_id}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_office_state_disk(report_id: str) -> dict[str, Any]:
    path = _office_state_path(report_id)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"phase": "arrival", "log": [], "goals": []}


def save_office_state_disk(report_id: str, state: dict[str, Any]) -> None:
    _office_state_path(report_id).write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def get_session_keys(workspace_id: str) -> dict[str, str]:
    return dict(_SESSION_KEYS.get(workspace_id) or {})


def set_session_keys(workspace_id: str, keys: dict[str, str]) -> dict[str, str]:
    cleaned = {k: str(v).strip() for k, v in keys.items() if str(v or "").strip()}
    merged = merge_api_keys(cleaned)
    _SESSION_KEYS[workspace_id] = cleaned
    return merged


def merged_keys_for_workspace(workspace_id: str) -> dict[str, str]:
    return merge_api_keys(get_session_keys(workspace_id))


def load_agent_chat(report_id: str, harness_id: str) -> list[dict[str, Any]]:
    path = _chat_path(report_id, harness_id)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_agent_chat(report_id: str, harness_id: str, chat: list[dict[str, Any]]) -> None:
    _chat_path(report_id, harness_id).write_text(json.dumps(chat, ensure_ascii=False), encoding="utf-8")


def _scope_from_workspace(workspace: dict[str, Any]) -> OfficeScope:
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    scope_data = os2.get("scope") if isinstance(os2.get("scope"), dict) else {}
    if not scope_data:
        office = load_office_state_disk(workspace_report_id(workspace))
        scope_data = office.get("scope") if isinstance(office.get("scope"), dict) else {}
    return OfficeScope.from_dict(scope_data)


def save_scope(workspace: dict[str, Any], scope: OfficeScope) -> dict[str, Any]:
    report_id = workspace_report_id(workspace)
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    os2["scope"] = scope.to_dict()
    workspace["employee_os"] = os2
    office = load_office_state_disk(report_id)
    office["scope"] = scope.to_dict()
    save_office_state_disk(report_id, office)
    save_workspace(workspace)
    return scope.to_dict()


def setup_requirements(report_id: str, keys: dict[str, str], *, has_plan: bool = True) -> list[dict[str, Any]]:
    from iidatech.execution.session_api_keys import has_any_llm_key

    return [
        {
            "need": "Run agents & write copy",
            "ok": has_any_llm_key(keys),
            "required": "Yes — add an LLM key in Integrations or set OPENAI_API_KEY on the server",
        },
        {
            "need": "Live research & lead search",
            "ok": bool(keys.get("perplexity")),
            "required": "Recommended for research and lead-finding tasks",
        },
        {"need": "Send emails from agents", "ok": is_connected(report_id, "gmail"), "required": "Only if tasks send email"},
        {"need": "Post to LinkedIn", "ok": is_connected(report_id, "linkedin"), "required": "Only if tasks post to LinkedIn"},
        {"need": "Update CRM / deals", "ok": is_connected(report_id, "hubspot"), "required": "Only if tasks touch HubSpot"},
        {
            "need": "Business plan for task queue",
            "ok": has_plan,
            "required": "Yes — build a plan first, then Taylor creates your task checklist",
        },
    ]


def build_team_checklist(workspace: dict[str, Any]) -> dict[str, Any]:
    report_id = workspace_report_id(workspace)
    topic = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or "Global").strip()
    plan_block = workspace.get("business_plan") if isinstance(workspace.get("business_plan"), dict) else {}
    plan = plan_block.get("plan_json") if isinstance(plan_block.get("plan_json"), dict) else {}
    if not plan and plan_block.get("markdown"):
        plan = {"business_concept": {"idea": topic, "industry": industry, "geography": geography}}
    normalized = normalize_plan(plan, topic=topic, industry=industry, geography=geography)
    checklist = build_checklist_from_plan(normalized, topic=topic, industry=industry, geography=geography)
    save_checklist(report_id, checklist)
    return checklist


def bootstrap_os2(workspace_id: str) -> dict[str, Any]:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    report_id = workspace_report_id(workspace)
    topic = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or "Global").strip()
    seed_workspace_from_env(report_id)
    ensure_os2_team(report_id, topic=topic, industry=industry, geography=geography)
    keys = merged_keys_for_workspace(workspace_id)
    scope = _scope_from_workspace(workspace)
    office_state = load_office_state_disk(report_id)
    checklist = load_checklist(report_id)
    pulse = build_taylor_pulse(report_id, checklist=checklist, has_api_keys=bool(keys))
    harnesses = merged_harnesses(_custom_harnesses(workspace))
    departments = departments_for_harnesses(harnesses)
    dept_map = {h["id"]: department_for_harness(h) for h in harnesses if h.get("id")}
    return {
        "report_id": report_id,
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "areas": str(workspace.get("areas") or ""),
        "scope": scope.to_dict(),
        "scope_modes": list(SCOPE_MODES),
        "departments": departments,
        "harness_departments": dept_map,
        "agents": [
            {
                "id": h["id"],
                "name": h.get("name"),
                "role": h.get("role"),
                "tagline": h.get("tagline"),
                "starters": h.get("starters") or [],
                "department": department_for_harness(h),
            }
            for h in harnesses
        ],
        "office_state": office_state,
        "checklist": checklist,
        "setup_requirements": setup_requirements(
            report_id,
            keys,
            has_plan=bool((workspace.get("business_plan") or {}).get("available")),
        ),
        "oauth_status": connection_status_rows(report_id),
        "taylor_pulse": pulse,
        "has_research": bool((workspace.get("research_report") or {}).get("available")),
        "has_plan": bool((workspace.get("business_plan") or {}).get("available")),
        "active_key_providers": list(keys.keys()),
    }


def run_agent_chat(
    workspace_id: str,
    harness_id: str,
    message: str,
) -> dict[str, Any]:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    report_id = workspace_report_id(workspace)
    keys = merged_keys_for_workspace(workspace_id)
    report_context = workspace_report_context(workspace)
    chat = load_agent_chat(report_id, harness_id)
    chat.append({"role": "user", "content": message})
    result = execute_harness_job(
        harness_id,
        message,
        report_id=report_id,
        api_keys=keys,
        report_context=report_context,
    )
    assistant = {
        "role": "assistant",
        "content": str(result.get("reply") or "Done."),
        "artifacts": list(result.get("artifacts") or []),
        "success": bool(result.get("success")),
    }
    chat.append(assistant)
    save_agent_chat(report_id, harness_id, chat)
    runs = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    history = list(runs.get("runs") or [])
    history.insert(0, {"harness_id": harness_id, "message": message, "success": assistant["success"], "reply": assistant["content"]})
    runs["runs"] = history[:30]
    runs["available"] = True
    workspace["employee_os"] = runs
    save_workspace(workspace)
    return {"success": assistant["success"], "result": result, "chat": chat}


def run_checklist_next(workspace_id: str, *, auto_approve_external: bool = False) -> dict[str, Any]:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    report_id = workspace_report_id(workspace)
    checklist = load_checklist(report_id)
    if not checklist:
        checklist = build_team_checklist(workspace)
    scope = _scope_from_workspace(workspace)
    all_ids = [str(h["id"]) for h in OS2_HARNESSES]
    harness_filter = scope.active_harness_ids(all_ids)
    keys = merged_keys_for_workspace(workspace_id)
    outcome = run_next_task(
        report_id,
        checklist,
        api_keys=keys,
        report_context=workspace_report_context(workspace),
        auto_approve_external=auto_approve_external,
        harness_ids=harness_filter,
    )
    return outcome


def _workspace_bundle(workspace_id: str) -> tuple[dict[str, Any], str, dict[str, Any], OfficeScope, dict[str, str]]:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    report_id = workspace_report_id(workspace)
    report_context = workspace_report_context(workspace)
    scope = _scope_from_workspace(workspace)
    keys = merged_keys_for_workspace(workspace_id)
    return workspace, report_id, report_context, scope, keys


def command_center_snapshot(workspace_id: str) -> dict[str, Any]:
    from iidatech.execution.execution_logger import list_tool_executions
    from iidatech.execution.team_memory import get_shared_team_memory
    from iidatech.integrations.sales import list_pipeline_leads
    from iidatech.storage.execution_repository import list_employees, list_tasks, list_team_messages

    _, report_id, _, _, _ = _workspace_bundle(workspace_id)
    employees = list_employees(report_id)
    tasks = list_tasks(report_id)
    leads = list_pipeline_leads(report_id, limit=25)
    exec_logs = list_tool_executions(report_id, limit=20)
    memory = get_shared_team_memory(report_id)
    role_by_id = {str(e.get("employee_id")): str(e.get("role") or e.get("name")) for e in employees}
    roster = []
    for emp in employees:
        eid = str(emp.get("employee_id") or "")
        emp_tasks = [t for t in tasks if t.get("owner_employee_id") == eid and t.get("status") != "completed"]
        emp_tools = [log for log in exec_logs if str(log.get("employee_id") or "") == eid]
        last_tool = str(emp_tools[0].get("tool_name") or "-") if emp_tools else "-"
        status = "working" if emp_tools else ("blocked" if any(t.get("status") == "blocked" for t in emp_tasks) else "idle")
        roster.append(
            {
                "name": emp.get("name") or emp.get("role"),
                "role": emp.get("role"),
                "status": status,
                "open_tasks": len(emp_tasks),
                "last_tool": last_tool,
            }
        )
    messages = []
    for msg in list_team_messages(report_id, limit=15):
        messages.append(
            {
                "when": str(msg.get("created_at") or "")[:19],
                "from": role_by_id.get(str(msg.get("sender_id") or ""), "team"),
                "mode": str(msg.get("mode") or ""),
                "message": str(msg.get("message") or "")[:200],
            }
        )
    return {
        "metrics": {
            "team": len(employees),
            "open_tasks": sum(1 for t in tasks if t.get("status") != "completed"),
            "crm_leads": len(leads),
            "tool_runs": len(exec_logs),
        },
        "roster": roster,
        "tool_runs": [
            {
                "when": str(log.get("created_at") or "")[:19],
                "tool": log.get("tool_name"),
                "ok": log.get("success"),
                "verified": log.get("verified"),
            }
            for log in exec_logs[:12]
        ],
        "leads": [
            {
                "company": l.get("company") or l.get("name"),
                "contact": l.get("name"),
                "email": l.get("email"),
                "status": l.get("status"),
            }
            for l in leads[:15]
        ],
        "messages": messages,
        "last_leads_csv": memory.get("last_leads_csv"),
    }


def war_room_snapshot(workspace_id: str) -> dict[str, Any]:
    from iidatech.storage.execution_repository import list_employees, list_team_messages
    from iidatech.ui.view_models import build_war_room_debate

    _, report_id, _, _, _ = _workspace_bundle(workspace_id)
    debate = build_war_room_debate(report_id)
    employees = list_employees(report_id)
    role_by_id = {str(e.get("employee_id")): str(e.get("role") or e.get("name")) for e in employees}
    channel = []
    for msg in [m for m in list_team_messages(report_id, limit=40) if str(m.get("mode") or "") == "war_room"][-12:]:
        channel.append(
            {
                "from": role_by_id.get(str(msg.get("sender_id") or ""), "Team"),
                "when": str(msg.get("created_at") or "")[:16],
                "message": str(msg.get("message") or ""),
            }
        )
    return {"debate": debate, "channel": channel}


def office_board_snapshot(workspace_id: str) -> dict[str, Any]:
    from iidatech.execution.office_day import checklist_board, recent_activity
    from iidatech.execution.office_scope import filter_board_rows
    from iidatech.execution.team_leader_qc import mentor_for_phase

    workspace, report_id, _, scope, _ = _workspace_bundle(workspace_id)
    office_state = load_office_state_disk(report_id)
    checklist = load_checklist(report_id) or build_team_checklist(workspace)
    harnesses = merged_harnesses(_custom_harnesses(workspace))
    harness_ids = scope.active_harness_ids([str(h.get("id") or "") for h in harnesses])
    board = filter_board_rows(checklist_board(checklist), harness_ids)
    phase = str(office_state.get("phase") or "arrival")
    return {
        "phase": phase,
        "last_mentor": office_state.get("last_mentor") or mentor_for_phase(phase),
        "goals": office_state.get("goals") or [],
        "onboarded": bool(office_state.get("onboarded")),
        "board": board,
        "activity": recent_activity(report_id, limit=8),
        "delivery": office_state.get("delivery") if isinstance(office_state.get("delivery"), dict) else {},
    }


def run_office_action(
    workspace_id: str,
    action: str,
    *,
    goals: list[str] | None = None,
    auto_approve: bool = False,
) -> dict[str, Any]:
    from iidatech.execution.office_day import (
        run_office_agent_cycle,
        run_office_arrival,
        run_office_delivery,
        run_office_execution_step,
        run_office_standup,
    )
    from iidatech.execution.team_leader_qc import mentor_for_phase

    workspace, report_id, report_context, scope, keys = _workspace_bundle(workspace_id)
    if not scope.is_configured():
        raise ValueError("Configure workspace scope first")
    harnesses = merged_harnesses(_custom_harnesses(workspace))
    harness_ids = scope.active_harness_ids([str(h.get("id") or "") for h in harnesses])
    state = load_office_state_disk(report_id)
    report_v3 = report_context.get("report_v3") if isinstance(report_context.get("report_v3"), dict) else report_context
    checklist = load_checklist(report_id) or build_team_checklist(workspace)
    goal_list = goals if goals else list(state.get("goals") or [])
    outcome: dict[str, Any] = {"action": action}

    if action == "clock_in":
        out = run_office_arrival(report_id, report_context=report_context)
        state.update({"phase": "standup", "last_mentor": out.get("mentor"), "goals": goal_list})
        outcome["result"] = out
    elif action == "standup":
        out = run_office_standup(report_id, goal_list, report_v3=report_v3, report_context=report_context)
        state.update({"phase": "execution", "last_mentor": out.get("mentor"), "goals": goal_list})
        outcome["result"] = out
    elif action == "next_task":
        if not keys:
            raise ValueError(
                "No AI API keys found. Add OPENAI_API_KEY or PERPLEXITY_API_KEY in your server settings, "
                "or enter keys under Integrations → API keys."
            )
        step = run_office_execution_step(
            report_id,
            checklist,
            api_keys=keys,
            report_context=report_context,
            extra_harnesses=harnesses,
            auto_approve=auto_approve,
            harness_ids=harness_ids,
        )
        if step.get("done"):
            state["phase"] = "agent_cycle"
        state["last_mentor"] = mentor_for_phase("execution")
        outcome["step"] = step
    elif action == "agent_sync":
        if not scope.is_full_office():
            raise ValueError("Agent sync requires Full office scope")
        cycle = run_office_agent_cycle(report_id, report_v3=report_v3, report_context=report_context)
        state.update({"phase": "delivery", "last_mentor": mentor_for_phase("execution")})
        outcome["cycle"] = cycle
    elif action == "delivery":
        out = run_office_delivery(report_id, report_v3=report_v3, report_context=report_context)
        state.update({"phase": "closed", "last_mentor": out.get("mentor"), "delivery": out})
        outcome["result"] = out
    elif action == "full_day":
        if not keys:
            raise ValueError(
                "No AI API keys found. Add OPENAI_API_KEY or PERPLEXITY_API_KEY in your server settings, "
                "or enter keys under Integrations → API keys."
            )
        run_office_arrival(report_id, report_context=report_context)
        out = run_office_standup(report_id, goal_list, report_v3=report_v3, report_context=report_context)
        state["last_mentor"] = out.get("mentor")
        items = checklist.get("items") or []
        scoped_count = len([i for i in items if str(i.get("harness_id") or "") in harness_ids])
        for _ in range(min(25, scoped_count or 1)):
            step = run_office_execution_step(
                report_id,
                checklist,
                api_keys=keys,
                report_context=report_context,
                extra_harnesses=harnesses,
                auto_approve=auto_approve,
                harness_ids=harness_ids,
            )
            if step.get("done") or step.get("needs_approval"):
                break
        if scope.is_full_office():
            run_office_agent_cycle(report_id, report_v3=report_v3, report_context=report_context)
        delivery = run_office_delivery(report_id, report_v3=report_v3, report_context=report_context)
        state.update({"phase": "closed", "last_mentor": delivery.get("mentor"), "delivery": delivery, "goals": goal_list})
        outcome["delivery"] = delivery
    elif action == "company_cycle":
        from iidatech.execution.agent_runtime import run_agent_company_cycle

        cycle = run_agent_company_cycle(report_id, report_v3=report_v3 if isinstance(report_v3, dict) else None)
        outcome["cycle"] = cycle
    elif action == "debate_sync":
        from iidatech.execution.agent_runtime import run_agent_company_cycle

        run_agent_company_cycle(report_id, report_v3=report_v3 if isinstance(report_v3, dict) else None)
        outcome["ok"] = True
    else:
        raise ValueError(f"Unknown office action: {action}")

    state["scope"] = scope.to_dict()
    save_office_state_disk(report_id, state)
    outcome["office"] = office_board_snapshot(workspace_id)
    outcome["checklist"] = load_checklist(report_id)
    return outcome


def run_taylor_action(workspace_id: str, action: str) -> dict[str, Any]:
    from iidatech.execution.agent_queue import approve_pending_queue_items
    from iidatech.execution.automation_steps import automation_report_id
    from iidatech.execution.os2_workflow import retry_task, save_checklist

    workspace, report_id, _, _, _ = _workspace_bundle(workspace_id)
    topic = str(workspace.get("idea") or "").strip()
    geography = str(workspace.get("country") or "Global").strip()
    checklist = load_checklist(report_id) or {}
    approved = 0

    if action == "approve_all":
        if checklist:
            for item in checklist.get("items") or []:
                if str(item.get("status")) == "awaiting_approval" or (
                    bool(item.get("external")) and not item.get("approved") and str(item.get("status")) == "pending"
                ):
                    item["approved"] = True
                    item["status"] = "approved"
                    approved += 1
            if approved:
                save_checklist(report_id, checklist)
        approved += approve_pending_queue_items(automation_report_id(topic, geography))
        return {"approved": approved, "checklist": load_checklist(report_id)}
    if action == "retry_failed":
        count = 0
        if checklist:
            for item in checklist.get("items") or []:
                if str(item.get("status")) == "qc_failed":
                    retry_task(checklist, str(item.get("id")))
                    count += 1
            if count:
                save_checklist(report_id, checklist)
        return {"retried": count, "checklist": load_checklist(report_id)}
    if action == "run_next":
        return run_checklist_next(workspace_id, auto_approve_external=False)
    raise ValueError(f"Unknown Taylor action: {action}")


def run_task_action(workspace_id: str, task_id: str, action: str) -> dict[str, Any]:
    from iidatech.execution.os2_workflow import approve_task, retry_task, run_task, skip_task

    workspace, report_id, report_context, _, keys = _workspace_bundle(workspace_id)
    checklist = load_checklist(report_id)
    if not checklist:
        raise ValueError("No checklist — build from plan first")
    harnesses = merged_harnesses(_custom_harnesses(workspace))
    if action == "approve":
        approve_task(checklist, task_id)
    elif action == "skip":
        skip_task(checklist, task_id)
    elif action == "retry":
        retry_task(checklist, task_id)
        target = next((i for i in (checklist.get("items") or []) if str(i.get("id")) == task_id), None)
        if target:
            run_task(
                report_id,
                checklist,
                target,
                api_keys=keys,
                report_context=report_context,
                extra_harnesses=harnesses,
            )
    else:
        raise ValueError(f"Unknown task action: {action}")
    save_checklist(report_id, checklist)
    return {"checklist": checklist, "office": office_board_snapshot(workspace_id)}


def oauth_links(workspace_id: str) -> list[dict[str, Any]]:
    from iidatech.integrations.oauth_store import build_authorization_url, connection_label, is_connected, oauth_env_ready, oauth_state

    _, report_id, _, _, _ = _workspace_bundle(workspace_id)
    rows = []
    for pid, label in [("linkedin", "LinkedIn"), ("gmail", "Gmail"), ("hubspot", "HubSpot")]:
        auth_url, auth_err = build_authorization_url(pid, state=oauth_state(report_id, pid))
        rows.append(
            {
                "provider": pid,
                "label": label,
                "status": connection_label(report_id, pid),
                "connected": is_connected(report_id, pid),
                "env_ready": oauth_env_ready(pid),
                "authorize_url": auth_url,
                "error": auth_err,
            }
        )
    return rows


def company_memory_snapshot(workspace_id: str) -> dict[str, Any]:
    from iidatech.execution.memory_engine import load_team_shared_memory
    from iidatech.execution.team_memory import get_shared_team_memory

    _, report_id, _, _, _ = _workspace_bundle(workspace_id)
    merged = {**get_shared_team_memory(report_id), **load_team_shared_memory(report_id)}
    return merged if merged else {"note": "Memory populates as agents execute tools."}


def _custom_harnesses(workspace: dict[str, Any]) -> list[dict[str, Any]]:
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    raw = os2.get("custom_harnesses") or []
    return [h for h in raw if isinstance(h, dict) and h.get("id")]


def _save_custom_harnesses(workspace: dict[str, Any], harnesses: list[dict[str, Any]]) -> None:
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    os2["custom_harnesses"] = harnesses
    workspace["employee_os"] = os2
    save_workspace(workspace)


def list_custom_harnesses(workspace_id: str) -> list[dict[str, Any]]:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    return _custom_harnesses(workspace)


def add_custom_harness(workspace_id: str, harness: dict[str, Any]) -> list[dict[str, Any]]:
    import re

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    name = str(harness.get("name") or "").strip()
    if not name:
        raise ValueError("Name required")
    base = str(harness.get("base_harness_id") or "sales_lead").strip()
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:24] or "agent"
    roles = {
        "sales_lead": "Sales Lead",
        "growth_marketer": "Growth Marketer",
        "research_analyst": "Research Analyst",
        "creative_producer": "Growth Marketer",
        "ops_manager": "Operations Manager",
    }
    item = {
        "id": f"custom_{slug}",
        "name": name,
        "role": roles.get(base, "Operations Manager"),
        "base_harness_id": base,
        "tagline": str(harness.get("tagline") or "Custom workflows"),
        "starters": [s.strip() for s in (harness.get("starters") or []) if str(s).strip()][:5],
    }
    items = [h for h in _custom_harnesses(workspace) if h.get("id") != item["id"]]
    items.append(item)
    _save_custom_harnesses(workspace, items)
    return items


def list_employees_snapshot(workspace_id: str) -> dict[str, Any]:
    from iidatech.execution.employees import CORE_ROLES, default_roles_for_business_type, infer_business_type
    from iidatech.storage.execution_repository import list_employees

    workspace, report_id, _, _, _ = _workspace_bundle(workspace_id)
    topic = str(workspace.get("idea") or "")
    industry = str(workspace.get("industry") or "General")
    employees = list_employees(report_id)
    bt = infer_business_type(industry=industry, topic=topic)
    catalog = default_roles_for_business_type(bt)
    existing = {str(e.get("role")) for e in employees}
    available = [r for r in catalog if r["role"] not in existing]
    return {
        "employees": employees,
        "catalog_roles": available,
        "core_roles": [r["role"] for r in CORE_ROLES],
    }


def hire_employee_action(workspace_id: str, *, name: str, role: str, catalog: bool = False) -> dict[str, Any]:
    from iidatech.execution.employees import CORE_ROLES, default_roles_for_business_type, infer_business_type
    from iidatech.execution.task_engine import hire_employee
    from iidatech.ui.os2_command_center import ensure_os2_team

    workspace, report_id, _, _, _ = _workspace_bundle(workspace_id)
    topic = str(workspace.get("idea") or "")
    industry = str(workspace.get("industry") or "General")
    geography = str(workspace.get("country") or "Global")
    ensure_os2_team(report_id, topic=topic, industry=industry, geography=geography)
    if catalog:
        bt = infer_business_type(industry=industry, topic=topic)
        spec = next((r for r in default_roles_for_business_type(bt) if r["role"] == role), None)
        if not spec:
            raise ValueError("Role not in catalog")
        hire_employee(report_id, name=f"Virtual {role}", role=role, department=spec["department"], authority_level=int(spec["authority_level"]))
    else:
        dept = next((r["department"] for r in CORE_ROLES if r["role"] == role), "Operations")
        hire_employee(report_id, name=name.strip(), role=role, department=dept, authority_level=6)
    return list_employees_snapshot(workspace_id)
