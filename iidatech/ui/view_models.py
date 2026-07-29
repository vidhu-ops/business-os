"""Transform execution backend data into customer-facing view models (no raw JSON)."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from iidatech.execution.company_state import load_company_state
from iidatech.execution.execution_logger import list_tool_executions
from iidatech.execution.memory_engine import load_team_shared_memory
from iidatech.execution.tool_audit import audit_report
from iidatech.storage.execution_repository import (
    get_employee,
    list_employees,
    list_kpi_history,
    list_tasks,
    list_team_messages,
)

_ARTIFACT_ROOT = Path(__file__).resolve().parents[2] / "business_build_outputs" / "employee_runtime"


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


_ROLE_DISPLAY: dict[str, str] = {
    "Growth Marketer": "Growth Manager",
    "Research Analyst": "Research Analyst",
    "Sales Lead": "Sales Lead",
    "Finance Manager": "Finance Manager",
    "COO": "Chief Operating Officer",
    "Operations Manager": "Operations Manager",
    "Founder": "Founder",
    "Product Manager": "Product Manager",
}

_ROLE_COLORS: dict[str, str] = {
    "Growth Marketer": "#7C3AED",
    "Research Analyst": "#0EA5E9",
    "Sales Lead": "#10B981",
    "Finance Manager": "#F59E0B",
    "COO": "#6366F1",
    "Operations Manager": "#64748B",
    "Founder": "#0F172A",
    "Product Manager": "#EC4899",
}

_FRIENDLY_NAMES: dict[str, str] = {
    "Growth Marketer": "Sarah",
    "Research Analyst": "Alex",
    "Sales Lead": "Jordan",
    "Finance Manager": "Morgan",
    "COO": "Riley",
    "Operations Manager": "Casey",
    "Product Manager": "Taylor",
}


def _fmt_money(value: float, currency: str = "INR") -> str:
    if currency == "INR":
        return f"₹{value:,.0f}"
    return f"${value:,.0f}"


def _fmt_number(value: Any) -> str:
    try:
        n = float(value)
    except (TypeError, ValueError):
        return str(value)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    if n == int(n):
        return str(int(n))
    return f"{n:.1f}"


def _relative_time(iso: str | None) -> str:
    if not iso:
        return "just now"
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        mins = int(delta.total_seconds() / 60)
        if mins < 1:
            return "just now"
        if mins < 60:
            return f"{mins}m ago"
        hours = mins // 60
        if hours < 24:
            return f"{hours}h ago"
        return f"{hours // 24}d ago"
    except ValueError:
        return ""


def _display_name(emp: dict) -> str:
    role = str(emp.get("role") or "")
    raw = str(emp.get("name") or "")
    if raw.lower().startswith("virtual "):
        return _FRIENDLY_NAMES.get(role, raw.replace("Virtual ", ""))
    return raw or _FRIENDLY_NAMES.get(role, "Team member")


def _initials(name: str) -> str:
    parts = [p for p in name.split() if p]
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return (parts[0][:2] if parts else "TM").upper()


def _dashboard_row_map(cycle: dict | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not cycle:
        return out
    for row in cycle.get("employee_dashboard") or []:
        role = str(row.get("role") or "")
        out[role] = row
    for agent in cycle.get("agent_outputs") or []:
        role = str(agent.get("role") or "")
        if role not in out:
            out[role] = {
                "name": agent.get("name"),
                "role": role,
                "current_task": (agent.get("brain") or {}).get("action"),
                "tools_used": [c.get("tool") for c in (agent.get("brain") or {}).get("tool_calls") or [] if isinstance(c, dict)],
                "kpis_changed": (agent.get("tool_execution") or {}).get("kpis") or {},
                "confidence": (agent.get("brain") or {}).get("confidence"),
            }
    return out


def build_company_dashboard(
    report_id: str,
    *,
    employee_cycle: dict | None = None,
    report_v3: dict | None = None,
) -> dict[str, Any]:
    state = load_company_state(report_id)
    shared = load_team_shared_memory(report_id)
    kpis = dict(state.get("kpis") or {})
    for row in list_kpi_history(report_id, limit=15):
        name = str(row.get("kpi_name") or "")
        if name:
            kpis[name] = row.get("kpi_value")

    revenue = float(state.get("revenue") or kpis.get("mrr") or 0)
    burn = float(state.get("burn") or 0)
    runway = float(kpis.get("runway_months") or 0) if kpis.get("runway_months") is not None else 0

    tasks = list_tasks(report_id)
    active_projects = [
        {"title": t.get("title"), "owner": t.get("owner_employee_id"), "status": t.get("status", "open").replace("_", " ").title()}
        for t in tasks
        if t.get("status") not in ("completed",)
    ][:8]
    campaigns = state.get("active_campaigns") or []
    for c in campaigns[:3]:
        if isinstance(c, dict):
            active_projects.append({"title": f"{c.get('channel', 'Campaign').title()} campaign", "status": c.get("status", "Active").title()})

    alerts: list[str] = []
    brief = (employee_cycle or {}).get("founder_brief") or shared.get("company_context", {}).get("founder_brief") or {}
    if isinstance(brief, dict):
        for risk in brief.get("risks") or []:
            if risk and risk not in alerts:
                alerts.append(str(risk))
        for issue in brief.get("urgent_issues") or []:
            if isinstance(issue, dict):
                label = issue.get("issue") or issue.get("action")
                if label:
                    alerts.append(str(label))
    for t in tasks:
        if t.get("status") == "blocked" or t.get("blockers"):
            alerts.append(f"Blocked: {t.get('title')}")
    if report_v3:
        for r in (report_v3.get("risk_heatmap") or [])[:2]:
            if isinstance(r, dict) and r.get("risk"):
                alerts.append(str(r["risk"]))

    return {
        "revenue": _fmt_money(revenue) if revenue else "—",
        "revenue_raw": revenue,
        "burn": _fmt_money(burn) if burn else "—",
        "burn_raw": burn,
        "runway": f"{runway:.1f} months" if runway else "—",
        "runway_raw": runway,
        "active_projects": active_projects,
        "alerts": alerts[:6],
        "goals": list(shared.get("goals") or [])[:5],
    }


def build_employee_cards(
    report_id: str,
    *,
    employee_cycle: dict | None = None,
) -> list[dict[str, Any]]:
    dash = _dashboard_row_map(employee_cycle)
    cards: list[dict[str, Any]] = []
    for emp in list_employees(report_id):
        if str(emp.get("role")) == "Founder":
            continue
        role = str(emp.get("role") or "")
        eid = str(emp.get("employee_id") or "")
        name = _display_name(emp)
        row = dash.get(role) or {}
        assigned = [t for t in list_tasks(report_id) if t.get("owner_employee_id") == eid and t.get("status") != "completed"]
        blocked = [t for t in assigned if t.get("status") == "blocked" or t.get("blockers")]
        current = row.get("current_task") or (assigned[0].get("title") if assigned else "Planning next priority")
        if isinstance(current, list):
            current = current[0] if current else "Planning next priority"

        if blocked:
            status, status_class = "Blocked", "iida-status-blocked"
        elif row.get("tools_used") or assigned:
            status, status_class = "Working", "iida-status-working"
        else:
            status, status_class = "Available", "iida-status-idle"

        conf = float(row.get("confidence") or 0.65)
        progress = int(min(95, max(12, conf * 100)))

        kpi_items: list[dict[str, str]] = []
        for k, v in (row.get("kpis_changed") or {}).items():
            kpi_items.append({"label": k.replace("_", " ").title(), "value": _fmt_number(v)})
        if not kpi_items and assigned:
            for t in assigned[:2]:
                kpi_items.append({"label": "Task", "value": str(t.get("title", ""))[:28]})

        badges = list(row.get("tool_badges") or [])
        if not badges and row.get("tools_used"):
            badges = ["Simulated"] * len(row["tools_used"])

        cards.append({
            "employee_id": eid,
            "name": name,
            "role": _ROLE_DISPLAY.get(role, role),
            "avatar_initials": _initials(name),
            "avatar_color": _ROLE_COLORS.get(role, "#64748B"),
            "status": status,
            "status_class": status_class,
            "current_task": str(current).replace("_", " ").title()[:60],
            "progress_pct": progress,
            "kpis": kpi_items[:3],
            "tool_badges": badges[:4],
            "execution_verified": bool(row.get("verified")),
        })
    return cards


def build_activity_feed(
    report_id: str,
    *,
    employee_cycle: dict | None = None,
    limit: int = 12,
) -> list[dict[str, str]]:
    events: list[dict[str, str]] = []
    role_names = {str(e["employee_id"]): _display_name(e) for e in list_employees(report_id)}
    role_by_id = {str(e["employee_id"]): str(e.get("role") or "") for e in list_employees(report_id)}

    for msg in reversed(list_team_messages(report_id, limit=limit)):
        sender = role_names.get(str(msg.get("sender_id")), "Team")
        text = str(msg.get("message") or "").strip()
        if text:
            events.append({
                "text": f"**{sender}** — {text[:160]}",
                "time": _relative_time(msg.get("created_at")),
            })

    if employee_cycle:
        for out in employee_cycle.get("agent_outputs") or []:
            role = str(out.get("role") or "")
            name = _display_name({"name": out.get("name"), "role": role})
            te = out.get("tool_execution") or {}
            if not te.get("verified"):
                continue
            kpis = te.get("kpis") or {}
            if kpis.get("competitors_found"):
                n = int(kpis["competitors_found"])
                events.append({"text": f"**{name}** found {n} verified competitor{'s' if n != 1 else ''}", "time": "today"})
            if kpis.get("runway_months"):
                events.append({"text": f"**{name}** updated runway to {kpis['runway_months']} months (verified)", "time": "today"})
            brain = out.get("brain") or {}
            for m in brain.get("messages") or []:
                if isinstance(m, dict) and m.get("text"):
                    events.append({"text": f"**{name}** messaged team: {m['text'][:120]}", "time": "today"})

    if not events:
        events.append({"text": "**Team** is online — awaiting verified execution outputs", "time": "just now"})
    return events[:limit]


def build_approval_items(
    report_id: str,
    *,
    employee_cycle: dict | None = None,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    shared = load_team_shared_memory(report_id)
    brief = (employee_cycle or {}).get("founder_brief") or shared.get("company_context", {}).get("founder_brief") or {}
    if isinstance(brief, dict):
        for i, label in enumerate(brief.get("needs_approval") or []):
            items.append({
                "id": f"brief_{i}",
                "title": str(label),
                "requester": "Team",
                "kind": "budget" if "budget" in str(label).lower() or "₹" in str(label) else "action",
            })

    if employee_cycle:
        for out in employee_cycle.get("agent_outputs") or []:
            name = _display_name({"name": out.get("name"), "role": out.get("role")})
            for call in (out.get("brain") or {}).get("tool_calls") or []:
                if not isinstance(call, dict):
                    continue
                budget = (call.get("payload") or {}).get("budget")
                tool = str(call.get("tool") or "").replace("_", " ")
                if budget and not call.get("approved"):
                    items.append({
                        "id": f"{out.get('employee_id')}_{tool}",
                        "title": f"Approve {_fmt_money(float(budget))} ad spend?",
                        "requester": name,
                        "kind": "budget",
                    })

    if not items:
        return []
    return items[:8]


def build_deliverables(report_id: str, *, limit: int = 20) -> list[dict[str, str]]:
    root = _ARTIFACT_ROOT / str(report_id)
    items: list[dict[str, str]] = []
    if not root.exists():
        return items
    type_map = {
        ".csv": ("CSV", "Lead list"),
        ".json": ("Data", "Campaign config"),
        ".jsonl": ("Log", "Evidence log"),
        ".md": ("Report", "Proposal"),
    }
    for path in sorted(root.rglob("*"), key=lambda p: p.stat().st_mtime, reverse=True):
        if not path.is_file():
            continue
        ext = path.suffix.lower()
        kind, label = type_map.get(ext, ("File", "Artifact"))
        name = path.name
        if "lead" in name.lower():
            label = "Lead export"
        elif "campaign" in name.lower():
            label = "Campaign brief"
        elif "proposal" in name.lower():
            label = "Sales proposal"
        elif "runway" in name.lower() or "pnl" in name.lower():
            label = "Finance report"
        elif "evidence" in name.lower():
            label = "Research evidence"
        items.append({
            "name": name,
            "label": label,
            "kind": kind,
            "path": str(path),
            "size_kb": f"{max(1, path.stat().st_size // 1024)} KB",
        })
        if len(items) >= limit:
            break
    return items


def build_founder_live_workspace(report_id: str, *, employee_cycle: dict | None = None) -> dict[str, Any]:
    """Live founder view: tasks, tool logs, artifacts, comms, meetings, KPIs."""
    tasks = list_tasks(report_id)
    in_progress = [t for t in tasks if str(t.get("status") or "open") in ("open", "in_progress", "pending")]
    exec_logs = list_tool_executions(report_id, limit=30)
    kpis = list_kpi_history(report_id, limit=20)
    verified_kpis = [k for k in kpis if k.get("notes") != "simulated"]

    artifacts: list[dict[str, str]] = []
    emails_sent: list[dict[str, str]] = []
    meetings: list[dict[str, str]] = []
    for row in exec_logs:
        tool = str(row.get("tool_name") or "")
        for path in row.get("artifacts") or []:
            p = Path(str(path))
            if p.exists():
                kind = "PDF" if p.suffix.lower() == ".pdf" else "CSV" if p.suffix.lower() == ".csv" else "Doc"
                artifacts.append({"tool": tool, "name": p.name, "path": str(p), "kind": kind})
        for line in row.get("logs") or []:
            text = str(line)
            if text.startswith("email:ok"):
                emails_sent.append({"tool": tool, "status": "sent", "detail": text})
            if text.startswith("calcom:ok") or text.startswith("calendar:"):
                meetings.append({"tool": tool, "detail": text})

    cycle_kpis = _as_dict((employee_cycle or {}).get("kpi_snapshot"))
    audit = audit_report()

    return {
        "tasks_in_progress": [
            {"task_id": t.get("task_id"), "title": t.get("title"), "owner": t.get("owner_employee_id"), "status": t.get("status")}
            for t in in_progress[:12]
        ],
        "tool_logs": [
            {
                "tool_name": r.get("tool_name"),
                "success": r.get("success"),
                "execution_mode": r.get("execution_mode"),
                "verified": r.get("verified"),
                "created_at": r.get("created_at"),
                "logs": (r.get("logs") or [])[:4],
                "errors": r.get("errors") or [],
            }
            for r in exec_logs[:15]
        ],
        "artifacts": artifacts[:20],
        "emails_sent": emails_sent,
        "meetings_booked": meetings,
        "kpis": verified_kpis[:10],
        "cycle_kpis": cycle_kpis,
        "realism_score": audit.get("realism_score"),
        "tool_matrix_counts": audit.get("counts"),
    }


def build_war_room_debate(report_id: str) -> dict[str, Any]:
    """Customer-safe war room debate payload for UI."""
    shared = load_team_shared_memory(report_id)
    ctx = _as_dict(shared.get("company_context"))
    debate = ctx.get("active_debate") if isinstance(ctx.get("active_debate"), dict) else None
    if not debate:
        return {"active": False, "topic": "", "thread": [], "votes": {}, "consensus": "", "escalation_required": False}

    thread: list[dict[str, str]] = []
    for bucket, label in (
        ("arguments", "Argument"),
        ("objections", "Objection"),
        ("counterarguments", "Response"),
    ):
        for row in debate.get(bucket) or []:
            if not isinstance(row, dict):
                continue
            thread.append({
                "role": str(row.get("role") or "Team"),
                "label": label,
                "text": str(row.get("text") or ""),
                "stance": str(row.get("stance") or label.lower()),
            })

    votes = debate.get("votes") if isinstance(debate.get("votes"), dict) else {}
    vote_rows = [{"role": k, "vote": str(v).replace("_", " ").title()} for k, v in votes.items()]

    return {
        "active": True,
        "debate_id": debate.get("debate_id"),
        "topic": str(debate.get("topic") or ""),
        "trigger": str(debate.get("trigger") or ""),
        "thread": thread,
        "arguments": debate.get("arguments") or [],
        "objections": debate.get("objections") or [],
        "counterarguments": debate.get("counterarguments") or [],
        "consensus": str(debate.get("consensus") or ""),
        "votes": votes,
        "vote_rows": vote_rows,
        "escalation_required": bool(debate.get("escalation_required")),
        "founder_override": debate.get("founder_override"),
    }


def build_employee_os_workspace(
    report_id: str,
    *,
    employee_cycle: dict | None = None,
    report_v3: dict | None = None,
) -> dict[str, Any]:
    """Single customer-safe workspace payload for all UI sections."""
    employees = list_employees(report_id)
    founder = next((e for e in employees if str(e.get("role")) == "Founder"), None)
    return {
        "report_id": report_id,
        "dashboard": build_company_dashboard(report_id, employee_cycle=employee_cycle, report_v3=report_v3),
        "employees": build_employee_cards(report_id, employee_cycle=employee_cycle),
        "activity": build_activity_feed(report_id, employee_cycle=employee_cycle),
        "approvals": build_approval_items(report_id, employee_cycle=employee_cycle),
        "deliverables": build_deliverables(report_id),
        "chat_employees": [
            {
                "employee_id": e["employee_id"],
                "name": _display_name(e),
                "role": _ROLE_DISPLAY.get(str(e.get("role")), str(e.get("role"))),
            }
            for e in employees
            if str(e.get("role")) != "Founder"
        ],
        "founder_id": str(founder["employee_id"]) if founder else None,
        "war_room": build_war_room_debate(report_id),
        "founder_live": build_founder_live_workspace(report_id, employee_cycle=employee_cycle),
    }
