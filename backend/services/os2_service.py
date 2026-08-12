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
    """Merge new keys into the workspace session — never wipe previously saved providers."""
    cleaned = {str(k).strip().lower(): str(v).strip() for k, v in keys.items() if str(v or "").strip()}
    existing = dict(_SESSION_KEYS.get(workspace_id) or {})
    existing.update(cleaned)
    _SESSION_KEYS[workspace_id] = existing
    return merge_api_keys(existing)


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

    has_pplx = bool(keys.get("perplexity"))
    has_llm = has_any_llm_key(keys)
    return [
        {
            "need": "Run agents & write copy",
            "ok": has_llm or has_pplx,
            "required": (
                "Yes — add Perplexity (research) and/or an LLM key in Integrations. "
                "Server PERPLEXITY_API_KEY also unlocks basic research runs."
            ),
        },
        {
            "need": "Live research & lead search",
            "ok": has_pplx,
            "required": "Recommended — Perplexity for research/leads (use a paid key for complex multi-market work)",
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
    from iidatech.execution.collaboration_engine import annotate_checklist_items, build_collaboration_plan

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
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    humans = list(os2.get("humans") or [])
    agents = list(os2.get("agents") or [])
    items = annotate_checklist_items(list(checklist.get("items") or []), humans)
    checklist = {**checklist, "items": items}
    collab = build_collaboration_plan(checklist, agents=agents, humans=humans)
    os2["collaboration"] = collab
    workspace["employee_os"] = os2
    save_workspace(workspace)
    save_checklist(report_id, checklist)
    return checklist


def bootstrap_os2(workspace_id: str) -> dict[str, Any]:
    from backend.services.demo_service import ensure_demo_employee_os, ensure_demo_os2_disk, is_readonly_workspace

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    report_id = workspace_report_id(workspace)
    topic = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or "Global").strip()
    seed_workspace_from_env(report_id)
    ensure_os2_team(report_id, topic=topic, industry=industry, geography=geography)
    if is_readonly_workspace(workspace):
        ensure_demo_os2_disk(report_id)
    os2 = ensure_demo_employee_os(workspace)
    keys = merged_keys_for_workspace(workspace_id)
    scope = _scope_from_workspace(workspace)
    if is_readonly_workspace(workspace) and not scope.is_configured():
        from iidatech.execution.office_scope import OfficeScope

        scope_data = os2.get("scope") if isinstance(os2.get("scope"), dict) else {}
        if scope_data:
            scope = OfficeScope.from_dict(scope_data)
    office_state = load_office_state_disk(report_id)
    checklist = load_checklist(report_id)
    pulse = build_taylor_pulse(report_id, checklist=checklist, has_api_keys=bool(keys))
    harnesses = merged_harnesses(_custom_harnesses(workspace))
    departments = departments_for_harnesses(harnesses)
    dept_map = {h["id"]: department_for_harness(h) for h in harnesses if h.get("id")}
    hired_agents = list(os2.get("agents") or [])
    agents = _agents_for_bootstrap(workspace, harnesses)
    if is_readonly_workspace(workspace) and hired_agents:
        # Prefer demo hired agents on the floor/chat roster.
        agents = [
            {
                "id": str(a.get("harness_id") or a.get("id")),
                "name": a.get("name"),
                "role": a.get("role"),
                "tagline": a.get("tagline") or "",
                "department": a.get("department"),
                "harness_id": a.get("harness_id") or a.get("id"),
                "starters": [],
            }
            for a in hired_agents
        ]
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
        "hired_departments": list(os2.get("departments") or []),
        "humans": list(os2.get("humans") or []),
        "hired_agents": hired_agents,
        "collaboration": os2.get("collaboration") if isinstance(os2.get("collaboration"), dict) else {},
        "agents": agents,
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
        "demo_readonly": bool(is_readonly_workspace(workspace)),
    }



def kickoff_outreach_pipeline(workspace_id: str, message: str = "", *, auto_approve_external: bool = False) -> dict[str, Any]:
    """Build + start find-leads -> personalize -> send-queue on the workspace report id."""
    from iidatech.execution.agent_queue import ensure_automation_team, init_queue_from_spec, process_next_queue_item, load_queue
    from iidatech.execution.automation_steps import build_daily_outreach_spec
    from iidatech.execution.outreach_pipeline import parse_lead_target
    from iidatech.execution.os2_api_keys import merge_api_keys

    workspace, report_id, report_context, _scope, keys = _workspace_bundle(workspace_id)
    idea = str(workspace.get("idea") or report_context.get("topic") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or report_context.get("geography") or "Global").strip()
    target = parse_lead_target(message, default=30)
    spec = build_daily_outreach_spec(idea=idea, industry=industry, geography=geography, target=target)
    ensure_automation_team(report_id, topic=idea, industry=industry, geography=geography)
    queue = init_queue_from_spec(report_id, spec)
    # Run first non-external step(s) immediately so leads start generating
    logs = []
    for _ in range(2):
        step = process_next_queue_item(
            report_id,
            idea=idea,
            industry=industry,
            geography=geography,
            api_keys=keys or merge_api_keys(),
            report_context=report_context,
            auto_approve_external=auto_approve_external,
        )
        logs.append(step)
        if step.get("done") or step.get("needs_approval"):
            break
        if step.get("item") and str(step["item"].get("status")) == "failed":
            break
    queue = load_queue(report_id)
    pending = sum(1 for it in (queue.get("items") or []) if str(it.get("status")) in ("queued", "needs_founder", "running"))
    return {
        "success": True,
        "target": target,
        "report_id": report_id,
        "queue": queue,
        "ran": logs,
        "message": (
            f"Started daily outreach for ~{target} leads: find -> personalize -> send queue. "
            f"{pending} step(s) still open. Approve sends under Tasks & Approvals or ask me to approve all / run next."
        ),
    }


def _taylor_office_brief(workspace: dict[str, Any], report_id: str, keys: dict[str, str]) -> str:
    """COO-style status across research, plan, Employee OS tasks, and automation."""
    checklist = load_checklist(report_id)
    pulse = build_taylor_pulse(report_id, checklist=checklist, has_api_keys=bool(keys))
    research = workspace.get("research_report") if isinstance(workspace.get("research_report"), dict) else {}
    plan = workspace.get("business_plan") if isinstance(workspace.get("business_plan"), dict) else {}
    auto = workspace.get("automation") if isinstance(workspace.get("automation"), dict) else {}
    idea = str(workspace.get("idea") or "this project").strip()
    industry = str(workspace.get("industry") or "").strip()
    geo = str(workspace.get("country") or "").strip()

    lines = [
        f"Taylor here — floor lead for **{idea}**"
        + (f" ({industry}" + (f", {geo}" if geo else "") + ")" if industry else "")
        + ".",
    ]
    if pulse.get("headline"):
        lines.append(str(pulse["headline"]))

    lines.append(
        "Research: "
        + ("ready — use it for competitor/lead tasks." if research.get("available") else "not generated yet — run Market Research or ask Sam.")
    )
    lines.append(
        "Plan: "
        + ("available — I can build the task checklist from it." if plan.get("available") else "missing — build a plan so I can staff the office.")
    )

    items = list((checklist or {}).get("items") or []) if isinstance(checklist, dict) else []
    if items:
        by = {}
        for it in items:
            st = str(it.get("status") or "pending")
            by[st] = by.get(st, 0) + 1
        parts = [f"{k}={v}" for k, v in sorted(by.items())]
        lines.append("Tasks: " + ", ".join(parts) + f" (total {len(items)}).")
    else:
        lines.append("Tasks: no checklist yet — say **build checklist** after the plan is ready.")

    queue = auto.get("active_spec") if isinstance(auto.get("active_spec"), dict) else {}
    if queue or auto.get("last_run"):
        lines.append("Automation: a workflow is wired — say **run next** to advance the queue, or ask for daily leads + email.")
    else:
        lines.append("Automation: none active — ask me to find leads and email them, or open Automation to compose a flow.")

    if not keys.get("perplexity") and not keys:
        lines.append("Blocked: add API keys under Integrations (Perplexity for research/leads).")
    elif not keys.get("perplexity"):
        lines.append("Note: Perplexity unlocks live research/leads; server key may cover basics.")

    sugg = [str(s.get("label") or "") for s in (pulse.get("suggestions") or [])[:3] if isinstance(s, dict)]
    if sugg:
        lines.append("Next moves: " + " · ".join(sugg))
    else:
        lines.append(
            "I can: build checklist · run next task · approve all · retry failed · run office day · "
            "ask Sam for competitors · kick off daily leads + email."
        )
    return "\n\n".join(lines)


def _taylor_run_intent(workspace_id: str, message: str) -> dict[str, Any]:
    """Parse founder language and execute real Employee OS / research / automation work."""
    from iidatech.execution.outreach_pipeline import is_outreach_pipeline_intent

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    report_id = workspace_report_id(workspace)
    keys = merged_keys_for_workspace(workspace_id)
    report_context = workspace_report_context(workspace)
    extra = merged_harnesses(_custom_harnesses(workspace))
    msg = message.strip().lower()

    if is_outreach_pipeline_intent(message):
        outcome = kickoff_outreach_pipeline(workspace_id, message)
        return {
            "role": "assistant",
            "content": str(outcome.get("message") or "Outreach pipeline started."),
            "artifacts": [],
            "success": bool(outcome.get("success")),
            "acted": "outreach",
        }

    if any(k in msg for k in ("build checklist", "build task", "create checklist", "staff the plan", "from the plan")):
        if not (workspace.get("business_plan") or {}).get("available") and not (workspace.get("idea") or "").strip():
            return {
                "role": "assistant",
                "content": "I need a business plan (or at least a project idea) before I can build the task checklist. Open Plan, generate one, then ask me again.",
                "artifacts": [],
                "success": False,
                "acted": "build_checklist_blocked",
            }
        checklist = build_team_checklist(workspace)
        n = len(list(checklist.get("items") or []))
        return {
            "role": "assistant",
            "content": f"Checklist built — {n} tasks queued from the plan. Say **run next** and I will put the first agent to work.",
            "artifacts": [],
            "success": True,
            "acted": "build_checklist",
        }

    if any(k in msg for k in ("approve all", "approve pending", "approve everything")) or (
        "approve" in msg and "task" in msg
    ):
        outcome = run_taylor_action(workspace_id, "approve_all")
        return {
            "role": "assistant",
            "content": f"Approved {outcome.get('approved', 0)} pending item(s). External sends stay gated until you confirm.",
            "artifacts": [],
            "success": True,
            "acted": "approve_all",
        }

    if any(k in msg for k in ("retry failed", "retry", "qc failed", "try again")):
        outcome = run_taylor_action(workspace_id, "retry_failed")
        retried = int(outcome.get("retried") or 0)
        if retried:
            # Immediately run next so retry actually ships work
            nxt = run_taylor_action(workspace_id, "run_next")
            return {
                "role": "assistant",
                "content": f"Retried {retried} failed task(s). {nxt.get('message') or 'Running the next one now.'}",
                "artifacts": [],
                "success": True,
                "acted": "retry_failed",
            }
        return {
            "role": "assistant",
            "content": "No QC-failed tasks to retry. Say **run next** or ask for a status brief.",
            "artifacts": [],
            "success": True,
            "acted": "retry_failed",
        }

    if any(
        k in msg
        for k in (
            "run next",
            "next task",
            "run the next",
            "keep going",
            "continue the office",
            "process next",
        )
    ):
        outcome = run_taylor_action(workspace_id, "run_next")
        return {
            "role": "assistant",
            "content": str(outcome.get("message") or "Processed the next task."),
            "artifacts": list((outcome.get("queue") or {}).get("item", {}).get("artifacts") or [])
            if isinstance(outcome.get("queue"), dict)
            else [],
            "success": True,
            "acted": "run_next",
        }

    if any(k in msg for k in ("office day", "full day", "run the office", "start the day", "standup")):
        outcome = run_office_action(workspace_id, "full_day", goals=[], auto_approve=False)
        return {
            "role": "assistant",
            "content": "Office day kicked off — arrival, standup, execution, and delivery. Check Tasks & Approvals for anything that needs your sign-off.",
            "artifacts": [],
            "success": True,
            "acted": "full_day",
            "outcome": outcome,
        }

    if any(k in msg for k in ("company cycle", "full cycle", "run cycle")):
        outcome = run_office_action(workspace_id, "company_cycle", goals=[], auto_approve=False)
        return {
            "role": "assistant",
            "content": "Full company cycle started across hired agents. I will surface blockers in Approvals.",
            "artifacts": [],
            "success": True,
            "acted": "company_cycle",
            "outcome": outcome,
        }

    if any(k in msg for k in ("competitor", "pricing evidence", "research pass", "ask sam", "sam —", "sam research")):
        result = execute_harness_job(
            "research_analyst",
            message if len(message.strip()) > 12 else "Search competitors and pricing",
            report_id=report_id,
            api_keys=keys,
            report_context=report_context,
            extra_harnesses=extra,
        )
        return {
            "role": "assistant",
            "content": "I put Sam on it.\n\n" + str(result.get("reply") or "Research run finished."),
            "artifacts": list(result.get("artifacts") or []),
            "success": bool(result.get("success")),
            "acted": "research_analyst",
        }

    if any(k in msg for k in ("find leads", "lead list", "qualified leads")) and "email" not in msg:
        result = execute_harness_job(
            "sales_lead",
            message if len(message.strip()) > 8 else "Find 20 qualified leads and export CSV",
            report_id=report_id,
            api_keys=keys,
            report_context=report_context,
            extra_harnesses=extra,
        )
        return {
            "role": "assistant",
            "content": "Alex is on leads.\n\n" + str(result.get("reply") or "Lead run finished."),
            "artifacts": list(result.get("artifacts") or []),
            "success": bool(result.get("success")),
            "acted": "sales_lead",
        }

    if any(k in msg for k in ("integration", "api key", "perplexity", "gmail", "linkedin", "hubspot")):
        return {
            "role": "assistant",
            "content": (
                "Integrations are under Employee OS → Integrations. "
                "Perplexity powers research/leads; an LLM key powers prompts; Gmail/LinkedIn/HubSpot unlock outbound. "
                "IIDA can open that tab for you — or paste keys there, then tell me to **run next**."
            ),
            "artifacts": [],
            "success": True,
            "acted": "guide_integrations",
        }

    if any(
        k in msg
        for k in (
            "status",
            "what's going",
            "whats going",
            "how are we",
            "brief me",
            "update me",
            "overview",
            "where are we",
            "what should we",
        )
    ) or msg in ("hi", "hello", "hey", "help"):
        return {
            "role": "assistant",
            "content": _taylor_office_brief(workspace, report_id, keys),
            "artifacts": [],
            "success": True,
            "acted": "brief",
        }

    # Default: COO brief + acknowledge the ask
    brief = _taylor_office_brief(workspace, report_id, keys)
    return {
        "role": "assistant",
        "content": (
            f"Understood — \"{message.strip()[:160]}\".\n\n{brief}\n\n"
            "Say the verb and I execute: **build checklist**, **run next**, **approve all**, "
            "**retry failed**, **run office day**, **find leads**, or **competitor pass**."
        ),
        "artifacts": [],
        "success": True,
        "acted": "brief_default",
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
    extra_harnesses = merged_harnesses(_custom_harnesses(workspace))
    chat = load_agent_chat(report_id, harness_id)
    chat.append({"role": "user", "content": message})

    if harness_id == "taylor":
        assistant = _taylor_run_intent(workspace_id, message)
    else:
        result = execute_harness_job(
            harness_id,
            message,
            report_id=report_id,
            api_keys=keys,
            report_context=report_context,
            extra_harnesses=extra_harnesses,
        )
        assistant = {
            "role": "assistant",
            "content": str(result.get("reply") or "Done."),
            "artifacts": list(result.get("artifacts") or []),
            "success": bool(result.get("success")),
        }
    chat.append(assistant)
    save_agent_chat(report_id, harness_id, chat)
    # Reload workspace — Taylor actions may have mutated it
    workspace = load_workspace(workspace_id) or workspace
    runs = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    history = list(runs.get("runs") or [])
    history.insert(0, {"harness_id": harness_id, "message": message, "success": assistant["success"], "reply": assistant["content"]})
    runs["runs"] = history[:30]
    runs["available"] = True
    workspace["employee_os"] = runs
    save_workspace(workspace)
    return {"success": assistant["success"], "result": assistant, "chat": chat}


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
    checklist = load_checklist(report_id)
    if not checklist:
        from backend.services.demo_service import is_readonly_workspace

        if is_readonly_workspace(workspace):
            from backend.services.demo_service import demo_checklist_snapshot, ensure_demo_os2_disk

            ensure_demo_os2_disk(report_id)
            checklist = load_checklist(report_id) or demo_checklist_snapshot()
        else:
            checklist = build_team_checklist(workspace)
    harnesses = merged_harnesses(_custom_harnesses(workspace))
    harness_ids = scope.active_harness_ids([str(h.get("id") or "") for h in harnesses])
    board = filter_board_rows(checklist_board(checklist), harness_ids)
    if not board:
        board = checklist_board(checklist)
    phase = str(office_state.get("phase") or "arrival")
    activity = recent_activity(report_id, limit=8)
    if not activity and isinstance(office_state.get("log"), list):
        activity = list(office_state.get("log") or [])[:8]
    return {
        "phase": phase,
        "last_mentor": office_state.get("last_mentor") or mentor_for_phase(phase),
        "goals": office_state.get("goals") or [],
        "onboarded": bool(office_state.get("onboarded")),
        "board": board,
        "activity": activity,
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
        approved += approve_pending_queue_items(report_id)
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
        from iidatech.execution.agent_queue import process_next_queue_item

        # Prefer draining the executable outreach/automation queue when present.
        queue_outcome = process_next_queue_item(
            report_id,
            idea=topic,
            industry=str(workspace.get("industry") or "General"),
            geography=geography,
            api_keys=merged_keys_for_workspace(workspace_id),
            report_context=workspace_report_context(workspace),
            auto_approve_external=False,
        )
        if not queue_outcome.get("done") or queue_outcome.get("needs_approval") or queue_outcome.get("item"):
            return {"message": str(queue_outcome.get("message") or queue_outcome.get("item", {}).get("result") or "Processed queue step."), "queue": queue_outcome}
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
    from iidatech.integrations.canva_client import (
        canva_env_ready,
        canva_ready_for_users,
        connection_status as canva_status,
        use_service_account,
    )
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
    if use_service_account():
        rows.append(
            {
                "provider": "canva",
                "label": "Canva (platform)",
                "status": canva_status(report_id),
                "connected": canva_ready_for_users(),
                "env_ready": canva_env_ready(),
                "authorize_url": "",
                "error": "" if canva_env_ready() else "Set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET on the server.",
                "use_in_automations": "Visuals use the IIDATECH Canva account — no client sign-in required.",
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


def _employee_os_block(workspace: dict[str, Any]) -> dict[str, Any]:
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    os2.setdefault("departments", [])
    os2.setdefault("humans", [])
    os2.setdefault("agents", [])
    os2.setdefault("collaboration", {})
    workspace["employee_os"] = os2
    return os2


def departments_snapshot(workspace_id: str) -> dict[str, Any]:
    from backend.services.demo_service import ensure_demo_employee_os
    from iidatech.execution.department_catalog import catalog_list, department_display_name

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    os2 = ensure_demo_employee_os(workspace) or _employee_os_block(workspace)
    hired = list(os2.get("departments") or [])
    return {
        "catalog": catalog_list(),
        "hired": hired,
        "agents": list(os2.get("agents") or []),
        "agent_count": len(os2.get("agents") or []),
        "department_names": {h.get("id"): department_display_name(str(h.get("id") or "")) for h in hired},
    }


def set_departments_hiring(workspace_id: str, departments: list[dict[str, Any]]) -> dict[str, Any]:
    from iidatech.execution.department_catalog import (
        catalog_list,
        custom_harness_for_agent,
        department_by_id,
        department_display_name,
        provision_agent_specs,
    )
    from iidatech.execution.office_scope import OfficeScope
    from iidatech.execution.task_engine import hire_employee
    from iidatech.ui.os2_command_center import ensure_os2_team

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    report_id = workspace_report_id(workspace)
    topic = str(workspace.get("idea") or "")
    industry = str(workspace.get("industry") or "General")
    geography = str(workspace.get("country") or "Global")
    ensure_os2_team(report_id, topic=topic, industry=industry, geography=geography)

    os2 = _employee_os_block(workspace)
    existing_agents = list(os2.get("agents") or [])
    hired: list[dict[str, Any]] = []
    new_agents: list[dict[str, Any]] = []
    hired_ids: set[str] = set()

    for row in departments:
        dept_id = str(row.get("id") or "").strip()
        if not dept_id:
            continue
        if not department_by_id(dept_id):
            raise ValueError(f"Unknown department: {dept_id}")
        headcount = max(0, min(20, int(row.get("headcount") or 0)))
        if headcount <= 0:
            continue
        hired_ids.add(dept_id)
        hired.append({
            "id": dept_id,
            "name": str(row.get("name") or department_display_name(dept_id)),
            "headcount": headcount,
        })
        specs = provision_agent_specs(dept_id, headcount, existing_agents)
        new_agents.extend(specs)
        for spec in specs:
            if spec.get("id") not in {a.get("id") for a in existing_agents}:
                hire_employee(
                    report_id,
                    name=str(spec.get("name") or spec.get("id")),
                    role=str(spec.get("role") or "Team Member"),
                    department=department_display_name(dept_id),
                    authority_level=6,
                )

    # Keep agents from departments no longer hired only if still in hired set
    kept = [a for a in new_agents if str(a.get("department") or "") in hired_ids]
    os2["departments"] = hired
    os2["agents"] = kept

    # Sync custom harnesses for multi-agent departments
    custom = [h for h in _custom_harnesses(workspace) if not str(h.get("id") or "").startswith("agent_")]
    for agent in kept:
        ch = custom_harness_for_agent(agent)
        if ch and ch["id"] not in {c.get("id") for c in custom}:
            custom.append(ch)
    os2["custom_harnesses"] = custom
    workspace["employee_os"] = os2

    dept_names = [department_display_name(h["id"]) for h in hired]
    harness_ids = [str(a.get("harness_id") or a.get("id") or "") for a in kept if a.get("harness_id") or a.get("id")]
    scope = OfficeScope(
        mode="department" if hired else "full_office",
        departments=dept_names,
        harness_ids=harness_ids,
    )
    save_scope(workspace, scope)
    save_workspace(workspace)

    return {
        "departments": hired,
        "agents": kept,
        "catalog": catalog_list(),
        "scope": scope.to_dict(),
    }


def list_humans_snapshot(workspace_id: str) -> dict[str, Any]:
    from backend.services.demo_service import ensure_demo_employee_os

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    os2 = ensure_demo_employee_os(workspace) or _employee_os_block(workspace)
    return {"humans": list(os2.get("humans") or [])}


def add_human_employee(workspace_id: str, *, name: str, role: str, departments: list[str] | None = None) -> dict[str, Any]:
    from iidatech.execution.department_catalog import new_human_id

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    name = name.strip()
    if not name:
        raise ValueError("Name required")
    os2 = _employee_os_block(workspace)
    humans = list(os2.get("humans") or [])
    human = {
        "id": new_human_id(),
        "name": name,
        "role": role.strip() or "Team member",
        "departments": [str(d) for d in (departments or []) if str(d).strip()],
    }
    humans.append(human)
    os2["humans"] = humans
    workspace["employee_os"] = os2
    save_workspace(workspace)
    return {"human": human, "humans": humans}


def remove_human_employee(workspace_id: str, human_id: str) -> dict[str, Any]:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    os2 = _employee_os_block(workspace)
    humans = [h for h in (os2.get("humans") or []) if str(h.get("id")) != human_id]
    if len(humans) == len(os2.get("humans") or []):
        raise ValueError("Human employee not found")
    os2["humans"] = humans
    workspace["employee_os"] = os2
    save_workspace(workspace)
    return {"humans": humans}


def org_chart_snapshot(workspace_id: str) -> dict[str, Any]:
    from backend.services.demo_service import ensure_demo_employee_os
    from iidatech.execution.department_catalog import build_org_tree, catalog_list

    workspace = load_workspace(workspace_id)
    if not workspace:
        raise ValueError("Project not found")
    os2 = ensure_demo_employee_os(workspace) or _employee_os_block(workspace)
    hired = list(os2.get("departments") or [])
    agents = list(os2.get("agents") or [])
    humans = list(os2.get("humans") or [])
    tree = build_org_tree(hired, agents, humans)
    return {"tree": tree, "catalog": catalog_list(), "departments": hired, "agents": agents, "humans": humans}


def collaboration_snapshot(workspace_id: str) -> dict[str, Any]:
    from backend.services.demo_service import ensure_demo_employee_os, is_readonly_workspace
    from iidatech.execution.collaboration_engine import build_collaboration_plan

    workspace, report_id, _, _, _ = _workspace_bundle(workspace_id)
    os2 = ensure_demo_employee_os(workspace) or _employee_os_block(workspace)
    if is_readonly_workspace(workspace) and isinstance(os2.get("collaboration"), dict) and os2.get("collaboration"):
        return os2["collaboration"]
    checklist = load_checklist(report_id)
    plan = build_collaboration_plan(
        checklist,
        agents=list(os2.get("agents") or []),
        humans=list(os2.get("humans") or []),
    )
    os2["collaboration"] = plan
    workspace["employee_os"] = os2
    save_workspace(workspace)
    return plan


def _agents_for_bootstrap(workspace: dict[str, Any], harnesses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge default harness agents with hired department agents."""
    from iidatech.execution.department_catalog import department_display_name

    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    hired_agents = list(os2.get("agents") or [])
    harness_by_id = {str(h.get("id") or ""): h for h in harnesses}
    seen: set[str] = set()
    out: list[dict[str, Any]] = []

    # Taylor / team leader first
    out.append({
        "id": "taylor",
        "name": "Taylor — Team Leader (COO)",
        "role": "COO",
        "tagline": "Orchestrates your virtual team",
        "starters": ["Run next task", "Approve all external actions", "Summarize team progress"],
        "department": "Operations",
        "is_leader": True,
    })
    seen.add("taylor")

    for agent in hired_agents:
        hid = str(agent.get("harness_id") or agent.get("id") or "")
        base = harness_by_id.get(hid) or harness_by_id.get(str(agent.get("base_harness_id") or ""))
        out.append({
            "id": hid or str(agent.get("id")),
            "agent_id": str(agent.get("id")),
            "name": agent.get("name"),
            "role": agent.get("role"),
            "tagline": (base or {}).get("tagline") or f"{department_display_name(str(agent.get('department') or ''))} agent",
            "starters": list((base or {}).get("starters") or [])[:3],
            "department": department_display_name(str(agent.get("department") or "")),
        })
        seen.add(hid)

    for h in harnesses:
        hid = str(h.get("id") or "")
        if hid in seen:
            continue
        out.append({
            "id": hid,
            "name": h.get("name"),
            "role": h.get("role"),
            "tagline": h.get("tagline"),
            "starters": h.get("starters") or [],
            "department": department_for_harness(h),
        })
    return out


def run_broadcast_chat(workspace_id: str, message: str, *, from_agent: str = "taylor") -> dict[str, Any]:
    """Store a team-wide message and optional agent-to-agent thread note."""
    from iidatech.storage.execution_repository import ensure_war_room, insert_team_message

    workspace, report_id, _, _, _ = _workspace_bundle(workspace_id)
    os2 = _employee_os_block(workspace)
    threads = list(os2.get("broadcast_threads") or [])
    entry = {"from": from_agent, "message": message, "replies": []}
    threads.insert(0, entry)
    os2["broadcast_threads"] = threads[:50]
    workspace["employee_os"] = os2
    save_workspace(workspace)
    room_id = ensure_war_room(report_id)
    insert_team_message(
        report_id,
        sender_id=from_agent,
        receiver_id=None,
        room_id=room_id,
        mode="war_room",
        message=message,
    )
    return {"thread": entry, "threads": threads[:20]}
