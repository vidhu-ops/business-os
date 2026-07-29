"""Memory engine -- private employee, shared team, and agent context assembly."""
from __future__ import annotations

from typing import Any

from iidatech.execution.company_state import load_company_state
from iidatech.execution.employee_profiles import build_employee_profile
from iidatech.execution.long_memory import relationship_narratives
from iidatech.storage.execution_repository import (
    get_employee,
    get_employee_memory,
    get_employee_private_memory,
    list_employees,
    list_founder_preferences,
    list_kpi_history,
    list_long_memory,
    list_relationships_for_employee,
    list_tasks,
    list_team_messages,
    touch_long_memory,
    upsert_employee_private_memory,
    upsert_employee_memory,
    upsert_team_shared_memory_row,
    get_team_shared_memory_row,
)


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def load_employee_memory(employee_id: str) -> dict[str, Any]:
    """Load private employee memory (preferences, past tasks, learned insights)."""
    emp = get_employee(employee_id)
    if not emp:
        return {"preferences": {}, "past_tasks": [], "learned_insights": []}
    report_id = str(emp.get("report_id") or "")
    private = get_employee_private_memory(report_id, employee_id)
    # Legacy fallback from employee_memory scope=private
    legacy = get_employee_memory(report_id, employee_id, "private")
    if legacy and not private.get("learned_insights"):
        private["learned_insights"] = _as_list(legacy.get("learned_insights") or legacy.get("insights"))
        private["preferences"] = {**_as_dict(private.get("preferences")), **_as_dict(legacy.get("preferences"))}
        private["past_tasks"] = private.get("past_tasks") or _as_list(legacy.get("past_tasks"))
    return private


def update_employee_memory(employee_id: str, memory: dict[str, Any] | None) -> dict[str, Any]:
    """Update private employee memory."""
    emp = get_employee(employee_id)
    if not emp:
        return {"preferences": {}, "past_tasks": [], "learned_insights": []}
    report_id = str(emp.get("report_id") or "")
    memory = memory if isinstance(memory, dict) else {}
    current = load_employee_memory(employee_id)

    preferences = memory.get("preferences")
    if preferences is not None:
        preferences = {**_as_dict(current.get("preferences")), **_as_dict(preferences)}

    past_tasks = memory.get("past_tasks")
    if past_tasks is None:
        past_tasks = current.get("past_tasks")
    else:
        past_tasks = list(past_tasks)

    insights = memory.get("learned_insights")
    if insights is not None:
        merged = list(current.get("learned_insights") or [])
        for item in _as_list(insights):
            if item not in merged:
                merged.append(item)
        insights = merged[-100:]
    else:
        insights = current.get("learned_insights")

    result = upsert_employee_private_memory(
        report_id,
        employee_id,
        preferences=preferences if preferences is not None else None,
        past_tasks=past_tasks,
        learned_insights=insights,
    )
    # Keep legacy table in sync for older readers
    upsert_employee_memory(report_id, employee_id, "private", result)
    return result


def load_team_shared_memory(report_id: str) -> dict[str, Any]:
    """Load shared team memory (goals, blockers, company context)."""
    report_id = str(report_id or "").strip()
    if not report_id:
        return {"goals": [], "blockers": [], "company_context": {}}
    row = get_team_shared_memory_row(report_id)
    legacy = get_employee_memory(report_id, "_team", "shared")
    if legacy:
        ctx = _as_dict(row.get("company_context"))
        ctx.update({k: v for k, v in legacy.items() if k not in ctx})
        row["company_context"] = ctx
        if not row.get("goals") and legacy.get("goals"):
            row["goals"] = _as_list(legacy.get("goals"))
        if not row.get("blockers") and legacy.get("blockers"):
            row["blockers"] = _as_list(legacy.get("blockers"))
    return row


def update_team_shared_memory(report_id: str, patch: dict[str, Any] | None) -> dict[str, Any]:
    """Patch shared team memory."""
    report_id = str(report_id or "").strip()
    patch = patch if isinstance(patch, dict) else {}
    current = load_team_shared_memory(report_id)

    goals = patch.get("goals")
    if goals is None and patch.get("goal"):
        goals = list(current.get("goals") or []) + [patch["goal"]]

    blockers = patch.get("blockers")
    if blockers is None and patch.get("blocker"):
        blockers = list(current.get("blockers") or []) + [patch["blocker"]]

    company_context = None
    if patch:
        ctx_keys = {k: v for k, v in patch.items() if k not in ("goals", "blockers", "goal", "blocker")}
        if ctx_keys:
            company_context = {**_as_dict(current.get("company_context")), **ctx_keys}

    result = upsert_team_shared_memory_row(
        report_id,
        goals=goals if goals is not None else None,
        blockers=blockers if blockers is not None else None,
        company_context=company_context,
    )
    upsert_employee_memory(report_id, "_team", "shared", {**result.get("company_context", {}), "goals": result.get("goals"), "blockers": result.get("blockers")})
    return result


def record_work_memory(
    employee_id: str,
    *,
    task_title: str | None = None,
    insight: str | None = None,
    preference: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Append past work / learned insight after tool execution."""
    mem = load_employee_memory(employee_id)
    if task_title:
        past = list(mem.get("past_tasks") or [])
        past.append({"title": task_title, "status": "completed"})
        mem["past_tasks"] = past[-50:]
    if insight:
        insights = list(mem.get("learned_insights") or [])
        if insight not in insights:
            insights.append(insight)
        mem["learned_insights"] = insights[-100:]
    if preference:
        mem["preferences"] = {**_as_dict(mem.get("preferences")), **_as_dict(preference)}
    return update_employee_memory(employee_id, mem)


def _task_outcome_buckets(report_id: str, employee_id: str) -> tuple[list[dict], list[dict]]:
    success, failed = [], []
    for t in list_tasks(report_id):
        if str(t.get("owner_employee_id") or "") != employee_id:
            continue
        status = str(t.get("status") or "")
        if status == "completed":
            success.append(t)
        elif status in ("blocked",) or t.get("blockers"):
            failed.append(t)
    for row in list_long_memory(report_id, employee_id, memory_type="task_outcome", limit=30):
        text = str(row.get("memory_text") or "")
        entry = {"title": text, "memory_id": row.get("memory_id"), "importance_score": row.get("importance_score")}
        if text.lower().startswith("completed"):
            success.append(entry)
        elif text.lower().startswith("failed") or "blocked" in text.lower():
            failed.append(entry)
    return success[:25], failed[:25]


def _build_context_brief(
    *,
    report_id: str,
    employee_id: str,
    roster: list[dict],
    founder_prefs: list[dict],
    long_mem: list[dict],
    rel_lines: list[str],
) -> list[str]:
    brief: list[str] = []
    role_by_id = {str(e["employee_id"]): str(e.get("role") or "") for e in roster}
    for pref in founder_prefs[:6]:
        val = str(pref.get("preference_value") or "").strip()
        if val:
            brief.append(val)
    for mem in long_mem[:8]:
        text = str(mem.get("memory_text") or "").strip()
        if text and text not in brief:
            brief.append(text)
    for line in rel_lines:
        if line not in brief:
            brief.append(line)
    # Cross-role patterns visible to all agents
    team_mem = list_long_memory(report_id, memory_type="team_conflict", limit=5)
    for mem in team_mem:
        text = str(mem.get("memory_text") or "")
        other = role_by_id.get(str(mem.get("employee_id") or ""), "teammate")
        if text and f"{other}:" not in text:
            brief.append(f"{other}: {text}")
        elif text:
            brief.append(text)
    return brief[:12]


def build_agent_context(
    agent_id: str,
    *,
    report_context: dict[str, Any] | None = None,
    report_id: str | None = None,
) -> dict[str, Any]:
    """Assemble full agent context: role, goals, KPIs, past work, blockers, dependencies."""
    emp = get_employee(agent_id)
    if not emp:
        return {"employee": None, "role": "", "goals": [], "kpis": {}, "past_work": [], "blockers": [], "dependencies": []}

    rid = str(report_id or emp.get("report_id") or "")
    profile = build_employee_profile(emp)
    private = load_employee_memory(agent_id)
    shared = load_team_shared_memory(rid)
    company = load_company_state(rid)

    assigned = [t for t in list_tasks(rid) if t.get("owner_employee_id") == agent_id and t.get("status") != "completed"]
    team_tasks = list_tasks(rid)
    blockers: list[str] = list(shared.get("blockers") or [])
    dependencies: list[str] = []
    for t in assigned:
        blockers.extend(_as_list(t.get("blockers")))
        for dep in _as_list(t.get("dependencies")):
            dependencies.append(str(dep))

    kpi_map = dict(company.get("kpis") or {})
    for row in list_kpi_history(rid, limit=15):
        name = str(row.get("kpi_name") or "")
        if name:
            kpi_map[name] = row.get("kpi_value")

    past_work = list(private.get("past_tasks") or [])
    ctx_blob = _as_dict(shared.get("company_context"))
    if ctx_blob.get("last_tool_run"):
        past_work.append(ctx_blob["last_tool_run"])

    roster = [
        {"employee_id": e["employee_id"], "name": e["name"], "role": e["role"]}
        for e in list_employees(rid)
    ]
    past_success, past_failed = _task_outcome_buckets(rid, agent_id)
    founder_prefs = list_founder_preferences(rid, limit=20)
    long_mem = list_long_memory(rid, agent_id, limit=25)
    rel_lines = relationship_narratives(rid, agent_id, roster)
    rel_map = {
        str(r.get("other_employee_id")): {
            "trust_score": r.get("trust_score"),
            "conflict_score": r.get("conflict_score"),
            "collaboration_score": r.get("collaboration_score"),
        }
        for r in list_relationships_for_employee(rid, agent_id)
    }
    context_brief = _build_context_brief(
        report_id=rid,
        employee_id=agent_id,
        roster=roster,
        founder_prefs=founder_prefs,
        long_mem=long_mem,
        rel_lines=rel_lines,
    )
    touch_long_memory([str(m["memory_id"]) for m in long_mem[:10] if m.get("memory_id")])

    inbox_messages: list[dict[str, Any]] = []
    role_by_id = {str(e["employee_id"]): str(e.get("role") or "") for e in roster}
    for msg in reversed(list_team_messages(rid, limit=40)):
        if not isinstance(msg, dict):
            continue
        receiver = str(msg.get("receiver_id") or "")
        mode = str(msg.get("mode") or "")
        if receiver == agent_id or mode == "war_room":
            sender_id = str(msg.get("sender_id") or "")
            inbox_messages.append(
                {
                    "from_id": sender_id,
                    "from_role": role_by_id.get(sender_id, sender_id),
                    "message": str(msg.get("message") or "")[:500],
                    "mode": mode,
                    "created_at": msg.get("created_at"),
                }
            )
    inbox_messages = list(reversed(inbox_messages[-12:]))
    inbox_preview = get_employee_memory(rid, agent_id, "inbox")

    team_state = {
        "goals": list(shared.get("goals") or []),
        "blockers": list(shared.get("blockers") or []),
        "company_day": _as_dict(ctx_blob.get("company_day")),
        "revenue": company.get("revenue"),
        "burn": company.get("burn"),
        "active_campaigns": company.get("active_campaigns") or [],
        "open_task_count": len([t for t in team_tasks if t.get("status") != "completed"]),
        "blocked_task_count": len([t for t in team_tasks if t.get("status") == "blocked" or t.get("blockers")]),
    }

    return {
        "employee": emp,
        "employee_id": agent_id,
        "report_id": rid,
        "role": profile.get("role"),
        "department": profile.get("department"),
        "personality": profile.get("personality"),
        "goals": list(shared.get("goals") or []) or list(profile.get("goals") or []),
        "kpis": kpi_map,
        "company_state": company,
        "team_state": team_state,
        "growth_metrics": company.get("growth_metrics") or {},
        "active_campaigns": company.get("active_campaigns") or [],
        "past_work": past_work,
        "current_tasks": assigned,
        "past_successful_tasks": past_success,
        "past_failed_tasks": past_failed,
        "founder_preferences": founder_prefs,
        "relationship_map": rel_map,
        "relationship_narratives": rel_lines,
        "long_term_memory": long_mem,
        "context_brief": context_brief,
        "inbox_messages": inbox_messages,
        "inbox_preview": inbox_preview if isinstance(inbox_preview, dict) else {},
        "learned_insights": list(private.get("learned_insights") or []),
        "preferences": _as_dict(private.get("preferences")),
        "blockers": sorted(set(b for b in blockers if b)),
        "dependencies": sorted(set(dependencies)),
        "assigned_tasks": assigned,
        "team_tasks": team_tasks,
        "shared_team_memory": shared,
        "private_memory": private,
        "report_context": report_context or {},
        "team_roster": roster,
    }
