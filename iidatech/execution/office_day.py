"""Office day orchestration — arrival, standup, execution, QC, delivery."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from iidatech.execution.chat_engine import send_agent_message
from iidatech.execution.company_loop import end_company_day, run_company_cycle, start_company_day
from iidatech.execution.os2_workflow import _WORKFLOW_ROOT, load_checklist, run_next_task, save_checklist
from iidatech.execution.team_leader_qc import mentor_for_phase
from iidatech.storage.execution_repository import list_employees, list_team_messages


def _office_state_path(report_id: str) -> Path:
    p = _WORKFLOW_ROOT / str(report_id).strip() / "office_day_state.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def team_leader_employee_id(report_id: str) -> str | None:
    for emp in list_employees(report_id):
        if str(emp.get("role") or "") == "COO":
            return str(emp.get("employee_id") or "") or None
    for emp in list_employees(report_id):
        role = str(emp.get("role") or "").lower()
        if "lead" in role or "coo" in role:
            return str(emp.get("employee_id") or "") or None
    return None


def mentor_broadcast(report_id: str, text: str, *, report_context: dict[str, Any] | None = None) -> None:
    tl = team_leader_employee_id(report_id)
    if not tl:
        return
    send_agent_message(report_id, tl, "war_room", text, report_context=report_context)
    from iidatech.execution.task_engine import founder_employee_id

    fid = founder_employee_id(report_id)
    if fid:
        send_agent_message(report_id, tl, fid, text[:500], report_context=report_context)


def load_office_state(st: Any, report_id: str) -> dict[str, Any]:
    key = f"office_day_{report_id}"
    state = st.session_state.get(key)
    if isinstance(state, dict) and state:
        return state
    path = _office_state_path(report_id)
    if path.is_file():
        try:
            import json

            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                st.session_state[key] = data
                return data
        except (json.JSONDecodeError, OSError):
            pass
    return {"phase": "arrival", "log": [], "goals": []}


def save_office_state(st: Any, report_id: str, state: dict[str, Any]) -> None:
    import json

    st.session_state[f"office_day_{report_id}"] = state
    try:
        _office_state_path(report_id).write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    except OSError:
        pass


def _status_display(status: str, qc: dict[str, Any] | None) -> str:
    qc = qc or {}
    if status == "running":
        return "in_progress"
    if status == "completed" and qc.get("passed"):
        return "delivered"
    if status == "qc_failed":
        return "needs_fix"
    if status == "completed":
        return "qc_review"
    if status == "failed":
        return "failed"
    if status == "approved":
        return "assigned"
    if status == "awaiting_approval":
        return "awaiting_approval"
    if status == "skipped":
        return "skipped"
    return status or "pending"


def checklist_board(checklist: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not checklist:
        return []
    rows: list[dict[str, Any]] = []
    for item in sorted(checklist.get("items") or [], key=lambda x: int(x.get("seq") or 0)):
        status = str(item.get("status") or "pending")
        qc = item.get("qc") if isinstance(item.get("qc"), dict) else {}
        rows.append(
            {
                "seq": item.get("seq"),
                "assignee": item.get("assignee"),
                "title": item.get("title"),
                "status": _status_display(status, qc),
                "mentor_note": qc.get("mentor_note") or item.get("result") or "",
                "artifacts": list(item.get("artifacts") or []),
                "id": item.get("id"),
                "harness_id": item.get("harness_id"),
            }
        )
    return rows


def run_office_arrival(report_id: str, *, report_context: dict[str, Any] | None = None) -> dict[str, Any]:
    text = mentor_for_phase("arrival")
    mentor_broadcast(report_id, text, report_context=report_context)
    return {"phase": "arrival", "mentor": text}


def run_office_standup(
    report_id: str,
    goals: list[str],
    *,
    report_v3: dict[str, Any] | None = None,
    report_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    morning = start_company_day(report_id, goals, report_v3=report_v3)
    text = mentor_for_phase("standup")
    if goals:
        text += "\n\n**Today goals:**\n" + "\n".join(f"- {g}" for g in goals[:6])
    mentor_broadcast(report_id, text, report_context=report_context)
    return {"phase": "standup", "mentor": text, "morning": morning}


def run_office_execution_step(
    report_id: str,
    checklist: dict[str, Any],
    *,
    api_keys: dict[str, str] | None = None,
    api_config: dict[str, str] | None = None,
    report_context: dict[str, Any] | None = None,
    extra_harnesses: list[dict[str, Any]] | None = None,
    auto_approve: bool = False,
    harness_ids: set[str] | None = None,
) -> dict[str, Any]:
    # auto_approve is passed per-call; never persisted into the checklist file.
    checklist.pop("auto_approve", None)
    step = run_next_task(
        report_id,
        checklist,
        auto_approve=True,
        auto_approve_external=auto_approve,
        api_keys=api_keys,
        api_config=api_config,
        report_context=report_context,
        extra_harnesses=extra_harnesses,
        harness_ids=harness_ids,
    )
    save_checklist(report_id, checklist)
    item = step.get("item") if isinstance(step.get("item"), dict) else None
    if item:
        title = str(item.get("title") or "Task")
        st = str(item.get("status") or "")
        if st == "completed":
            mentor_broadcast(
                report_id,
                f"Task done: **{title}**. QC approved — passing to your inbox.",
                report_context=report_context,
            )
        elif st == "qc_failed":
            qc = item.get("qc") if isinstance(item.get("qc"), dict) else {}
            mentor_broadcast(
                report_id,
                str(qc.get("mentor_note") or f"**{title}** — QC failed. I'll send it back for fixes."),
                report_context=report_context,
            )
        elif st == "failed":
            mentor_broadcast(
                report_id,
                f"**{title}** hit a blocker: {str(item.get('error') or 'execution failed')[:200]}",
                report_context=report_context,
            )
    return step


def run_office_agent_cycle(
    report_id: str,
    *,
    report_v3: dict[str, Any] | None = None,
    report_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    mentor_broadcast(report_id, mentor_for_phase("execution"), report_context=report_context)
    return run_company_cycle(report_id, report_v3=report_v3)


def run_office_delivery(
    report_id: str,
    *,
    report_v3: dict[str, Any] | None = None,
    report_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    evening = end_company_day(report_id, report_v3=report_v3)
    text = mentor_for_phase("delivery")
    arts: list[str] = []
    cl = load_checklist(report_id)
    if cl:
        for item in cl.get("items") or []:
            if str(item.get("status")) == "completed":
                arts.extend([str(a) for a in (item.get("artifacts") or []) if a])
    if arts:
        text += f"\n\n**{len(arts)} deliverable file(s)** are ready for you below."
    mentor_broadcast(report_id, text, report_context=report_context)
    return {"phase": "delivery", "mentor": text, "evening": evening, "artifacts": arts}


def recent_activity(report_id: str, limit: int = 20) -> list[dict[str, str]]:
    role_by_id = {
        str(e.get("employee_id") or ""): str(e.get("role") or e.get("name") or "Team")
        for e in list_employees(report_id)
    }
    out: list[dict[str, str]] = []
    for m in list_team_messages(report_id, limit=limit):
        out.append(
            {
                "when": str(m.get("created_at") or "")[:19],
                "from": role_by_id.get(str(m.get("sender_id") or ""), "Team"),
                "text": str(m.get("message") or "")[:400],
            }
        )
    return out
