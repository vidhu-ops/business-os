"""Inter-agent negotiation and conflict resolution for Employee OS."""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from iidatech.execution.negotiation_styles import get_negotiation_style
from iidatech.execution.chat_engine import send_agent_message
from iidatech.execution.long_memory import on_team_conflict, write_long_memory
from iidatech.execution.team_memory import update_shared_team_memory
from iidatech.storage.execution_repository import list_employees, list_tasks

BUDGET_THRESHOLD_INR = 10_000.0
BLOCKED_TASK_THRESHOLD = 3


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _fmt_money(amount: float, currency: str = "INR") -> str:
    if currency == "INR":
        return f"₹{amount:,.0f}"
    return f""


def _parse_spend(text: str) -> float | None:
    blob = str(text or "")
    m = re.search(r"(?:₹|rs\.?|inr)\s*([\d,]+(?:\.\d+)?)", blob, re.I)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    m = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", blob)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            pass
    return None


def _participant_map(participants: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for p in participants:
        if not isinstance(p, dict):
            continue
        role = str(p.get("role") or "")
        if role:
            out[role] = p
    return out


def _role_argument(role: str, topic: str, context: dict[str, Any]) -> str | None:
    style = get_negotiation_style(role)
    spend = context.get("proposed_spend")
    if spend is None:
        spend = _parse_spend(topic)
    kpi = _as_dict(context.get("kpi_changes"))
    cac_rising = float(kpi.get("cac") or 0) > 0

    if role == "Growth Marketer":
        amt = _fmt_money(float(spend)) if spend else "budget"
        return f"Need {amt} ads to keep pipeline velocity — we are stalling without top-of-funnel tests."
    if role == "Finance Manager":
        if spend and spend > BUDGET_THRESHOLD_INR:
            return f"Rejected. {_fmt_money(float(spend))} spend with unproven CAC — runway impact too high."
        return "Rejected. CAC unproven — no scale spend without verified unit economics."
    if role == "Research Analyst":
        return "Evidence insufficient for this claim — corroborate pricing and demand before committing spend."
    if role == "Sales Lead":
        return "Pipeline will stall without leads — prioritize speed but protect discovery call quality."
    if role == "COO":
        return None
    return f"{role}: position on '{topic[:80]}' needs team alignment."


def _role_objection(role: str, topic: str, context: dict[str, Any]) -> str | None:
    style = get_negotiation_style(role)
    if role == "Finance Manager" and style.get("traits"):
        return "Block risky spend until LTV:CAC is validated on a paid cohort."
    if role == "Research Analyst" and "blocks_weak_claims" in style.get("traits", []):
        return "Block weak claims — missing competitor pricing and buyer proof."
    if role == "Growth Marketer" and context.get("kpi_dropping"):
        return "Objection: slowing experiments now guarantees we miss the weekly lead target."
    return None


def _role_counter(role: str, topic: str, context: dict[str, Any], prior: list[str]) -> str | None:
    if role == "Growth Marketer" and any("reject" in p.lower() for p in prior):
        return "Without spend the pipeline dies — we need a controlled test, not paralysis."
    if role == "Sales Lead" and any("evidence" in p.lower() for p in prior):
        return "Speed matters — book pilots while research closes evidence gaps in parallel."
    if role == "Finance Manager" and any("pipeline" in p.lower() for p in prior):
        return "A capped pilot is acceptable; full budget is not."
    return None


def _coo_consensus(topic: str, context: dict[str, Any], objections: list[dict]) -> tuple[str, dict[str, str], bool]:
    spend = context.get("proposed_spend")
    if spend is None:
        spend = _parse_spend(topic)
    votes: dict[str, str] = {}
    if spend and spend > BUDGET_THRESHOLD_INR:
        pilot = max(BUDGET_THRESHOLD_INR, round(float(spend) * 0.2, -2))
        consensus = f"Approve {_fmt_money(pilot)} pilot with kill criteria at 2x CAC — not full {_fmt_money(float(spend))}."
        votes = {
            "Growth Marketer": "approve_pilot",
            "Finance Manager": "approve_pilot",
            "Research Analyst": "conditional",
            "Sales Lead": "approve",
            "COO": "mediate",
        }
        escalation = False
    elif objections:
        consensus = "Defer full decision — run 7-day validation sprint before spend or scale."
        votes = {str(o.get("role")): "defer" for o in objections}
        votes["COO"] = "mediate"
        escalation = True
    else:
        consensus = f"Proceed on '{topic[:100]}' with weekly checkpoint."
        votes = {"COO": "approve"}
        escalation = False
    return consensus, votes, escalation


def run_agent_debate(topic: str, participants: list[dict], context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Run structured multi-agent debate; returns arguments, objections, consensus."""
    context = dict(context or {})
    topic = str(topic or "team decision").strip()
    pmap = _participant_map(participants)
    debate_roles = [r for r in ("Growth Marketer", "Finance Manager", "Research Analyst", "Sales Lead", "COO") if r in pmap]
    if not debate_roles:
        debate_roles = [str(p.get("role")) for p in participants if p.get("role")][:5]

    arguments: list[dict[str, Any]] = []
    objections: list[dict[str, Any]] = []
    counterarguments: list[dict[str, Any]] = []
    prior_lines: list[str] = []

    for role in debate_roles:
        if role == "COO":
            continue
        text = _role_argument(role, topic, context)
        if text:
            p = pmap.get(role, {"role": role})
            arguments.append({"role": role, "employee_id": p.get("employee_id"), "text": text, "stance": "argue"})
            prior_lines.append(text)

    for role in ("Finance Manager", "Research Analyst"):
        if role not in pmap:
            continue
        text = _role_objection(role, topic, context)
        if text:
            p = pmap[role]
            objections.append({"role": role, "employee_id": p.get("employee_id"), "text": text, "stance": "object"})
            prior_lines.append(text)

    for role in ("Growth Marketer", "Sales Lead"):
        if role not in pmap:
            continue
        text = _role_counter(role, topic, context, prior_lines)
        if text:
            p = pmap[role]
            counterarguments.append({"role": role, "employee_id": p.get("employee_id"), "text": text, "stance": "counter"})
            prior_lines.append(text)

    consensus, votes, escalation_required = _coo_consensus(topic, context, objections)
    if "COO" in pmap:
        counterarguments.append({
            "role": "COO",
            "employee_id": pmap["COO"].get("employee_id"),
            "text": consensus,
            "stance": "mediate",
        })

    report_id = str(context.get("report_id") or "")
    if report_id and escalation_required:
        growth = pmap.get("Growth Marketer", {})
        finance = pmap.get("Finance Manager", {})
        if growth.get("employee_id") and finance.get("employee_id"):
            on_team_conflict(
                report_id,
                str(growth["employee_id"]),
                str(finance["employee_id"]),
                f"Debate unresolved on: {topic[:120]}",
                severity=0.55,
            )

    return {
        "debate_id": context.get("debate_id") or f"deb_{uuid.uuid4().hex[:10]}",
        "topic": topic,
        "trigger": context.get("trigger_reason"),
        "arguments": arguments,
        "objections": objections,
        "counterarguments": counterarguments,
        "consensus": consensus,
        "votes": votes,
        "escalation_required": escalation_required,
        "started_at": _now_iso(),
        "founder_override": None,
    }


def detect_debate_triggers(
    report_id: str,
    *,
    agent_outputs: list[dict] | None = None,
    kpi_changes: dict[str, float] | None = None,
    founder_question: str | None = None,
) -> list[dict[str, Any]]:
    """Return debate specs when spend, KPI, conflict, or blocker thresholds fire."""
    triggers: list[dict[str, Any]] = []
    agent_outputs = list(agent_outputs or [])
    kpi_changes = dict(kpi_changes or {})

    max_budget = 0.0
    budget_topic = ""
    for out in agent_outputs:
        brain = _as_dict(out.get("brain"))
        for call in _as_list(brain.get("tool_calls")):
            if not isinstance(call, dict):
                continue
            budget = _as_dict(call.get("payload")).get("budget")
            try:
                b = float(budget)
            except (TypeError, ValueError):
                b = 0.0
            if b > max_budget:
                max_budget = b
                budget_topic = f"Approve {_fmt_money(b)} ad spend ({out.get('role')})"

    if max_budget >= BUDGET_THRESHOLD_INR:
        triggers.append({
            "reason": "spend_over_budget_threshold",
            "topic": budget_topic or f"Approve {_fmt_money(max_budget)} spend",
            "context": {"proposed_spend": max_budget, "trigger_reason": "spend_over_budget_threshold"},
            "roles": ["Growth Marketer", "Finance Manager", "Research Analyst", "COO"],
        })

    dropping = [k for k, v in kpi_changes.items() if float(v) < 0]
    if dropping:
        label = ", ".join(dropping[:3])
        triggers.append({
            "reason": "kpi_drop",
            "topic": f"Respond to KPI decline: {label}",
            "context": {"kpi_changes": kpi_changes, "kpi_dropping": True, "trigger_reason": "kpi_drop"},
            "roles": ["COO", "Finance Manager", "Growth Marketer"],
        })

    actions = [str(_as_dict(o.get("brain")).get("action") or "") for o in agent_outputs]
    if any(a.startswith("escalate") for a in actions) and any(a in ("launch_experiment", "launch_campaign", "run_paid_pilot") for a in actions):
        triggers.append({
            "reason": "conflicting_recommendations",
            "topic": "Research escalation vs Growth launch — resolve conflict",
            "context": {"trigger_reason": "conflicting_recommendations"},
            "roles": ["Research Analyst", "Growth Marketer", "COO", "Finance Manager"],
        })

    blocked = [t for t in list_tasks(report_id) if t.get("status") == "blocked" or t.get("blockers")]
    if len(blocked) > BLOCKED_TASK_THRESHOLD:
        triggers.append({
            "reason": "blocked_tasks",
            "topic": f"Unblock {len(blocked)} tasks — execution at risk",
            "context": {"blocked_count": len(blocked), "trigger_reason": "blocked_tasks"},
            "roles": ["COO", "Operations Manager", "Founder"],
        })

    if founder_question and str(founder_question).strip():
        q = str(founder_question).strip()
        triggers.append({
            "reason": "founder_strategic_question",
            "topic": q[:240],
            "context": {"trigger_reason": "founder_strategic_question"},
            "roles": ["Research Analyst", "Growth Marketer", "Finance Manager", "COO", "Sales Lead"],
        })

    return triggers


def _participants_for_roles(report_id: str, roles: list[str]) -> list[dict]:
    employees = list_employees(report_id)
    by_role = {str(e.get("role")): e for e in employees}
    out = []
    for role in roles:
        emp = by_role.get(role)
        if emp:
            out.append({"employee_id": emp["employee_id"], "role": role, "name": emp.get("name")})
    return out


def resolve_team_debates(
    report_id: str,
    *,
    agent_outputs: list[dict] | None = None,
    kpi_changes: dict[str, float] | None = None,
    founder_question: str | None = None,
) -> list[dict[str, Any]]:
    """Detect triggers, run debates, persist active debate for war room UI."""
    report_id = str(report_id or "").strip()
    if not report_id:
        return []
    specs = detect_debate_triggers(
        report_id,
        agent_outputs=agent_outputs,
        kpi_changes=kpi_changes,
        founder_question=founder_question,
    )
    if not specs:
        return []

    debates: list[dict[str, Any]] = []
    for spec in specs[:3]:
        roles = list(spec.get("roles") or [])
        participants = _participants_for_roles(report_id, roles)
        if not participants:
            continue
        ctx = {
            "report_id": report_id,
            "agent_outputs": agent_outputs or [],
            "kpi_changes": kpi_changes or {},
            **(_as_dict(spec.get("context"))),
        }
        debate = run_agent_debate(str(spec.get("topic") or ""), participants, ctx)
        debate["trigger"] = spec.get("reason")
        debates.append(debate)

    if not debates:
        return []

    active = debates[-1]
    update_shared_team_memory(report_id, {
        "active_debate": active,
        "debate_history": debates,
        "last_debate_at": _now_iso(),
    })

    summary = f"War room debate: {active.get('topic')} — consensus: {active.get('consensus')}"
    send_agent_message(report_id, participants[0].get("employee_id", "system"), "war_room", summary[:500])

    report_id_mem = report_id
    for d in debates:
        if d.get("escalation_required"):
            write_long_memory(
                report_id_mem,
                participants[0].get("employee_id", "system"),
                "team_conflict",
                f"Debate escalated: {d.get('topic')}",
                importance_score=0.7,
            )
            break

    return debates


def apply_founder_override(report_id: str, debate: dict[str, Any], decision: str) -> dict[str, Any]:
    """Founder final say on an active debate."""
    from iidatech.execution.task_engine import founder_employee_id

    updated = dict(debate)
    updated["founder_override"] = str(decision).strip()
    updated["consensus"] = f"Founder override: {decision}"
    updated["escalation_required"] = False
    updated["resolved_at"] = _now_iso()
    update_shared_team_memory(report_id, {"active_debate": updated})
    fid = founder_employee_id(report_id) or "founder"
    send_agent_message(report_id, fid, "war_room", f"Founder decision: {decision}")
    return updated