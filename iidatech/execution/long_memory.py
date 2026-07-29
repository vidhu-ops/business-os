"""Long-term memory writes and relationship updates for Employee OS."""
from __future__ import annotations

from typing import Any

from iidatech.storage.execution_repository import (
    get_employee,
    insert_long_memory,
    list_founder_preferences,
    list_long_memory,
    list_relationships_for_employee,
    upsert_founder_preference,
    upsert_relationship,
)

MEMORY_TYPE_FOUNDER_PREFERENCE = "founder_preference"
MEMORY_TYPE_TASK_OUTCOME = "task_outcome"
MEMORY_TYPE_LEARNED_PATTERN = "learned_pattern"
MEMORY_TYPE_MISTAKE = "mistake"
MEMORY_TYPE_CUSTOMER_FEEDBACK = "customer_feedback"
MEMORY_TYPE_TEAM_CONFLICT = "team_conflict"

_SIGNIFICANT_KPI_PCT = 0.2
_SIGNIFICANT_KPI_ABS = 5.0


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _role_label(report_id: str, employee_id: str) -> str:
    emp = get_employee(employee_id)
    if not emp:
        return "team member"
    return str(emp.get("role") or emp.get("name") or "team member")


def _dedupe_recent(report_id: str, employee_id: str, memory_type: str, memory_text: str) -> bool:
    needle = memory_text.strip().lower()[:160]
    for row in list_long_memory(report_id, employee_id, memory_type=memory_type, limit=20):
        if needle in str(row.get("memory_text") or "").lower():
            return True
    return False


def write_long_memory(
    report_id: str,
    employee_id: str,
    memory_type: str,
    memory_text: str,
    *,
    importance_score: float = 0.5,
    dedupe: bool = True,
) -> dict[str, Any]:
    text = str(memory_text or "").strip()
    if not text or not report_id or not employee_id:
        return {}
    if dedupe and _dedupe_recent(report_id, employee_id, memory_type, text):
        return {}
    return insert_long_memory(
        report_id,
        employee_id,
        memory_type,
        text,
        importance_score=importance_score,
    )


def record_founder_preference(
    report_id: str,
    preference_key: str,
    preference_value: str,
    *,
    confidence: float = 0.85,
    observed_by_employee_id: str | None = None,
) -> dict[str, Any]:
    pref = upsert_founder_preference(report_id, preference_key, preference_value, confidence=confidence)
    if observed_by_employee_id:
        write_long_memory(
            report_id,
            observed_by_employee_id,
            MEMORY_TYPE_FOUNDER_PREFERENCE,
            preference_value,
            importance_score=confidence,
        )
    return pref


def on_task_completed(report_id: str, employee_id: str | None, task: dict[str, Any]) -> None:
    eid = str(employee_id or task.get("owner_employee_id") or "")
    if not eid:
        return
    title = str(task.get("title") or "task")
    write_long_memory(
        report_id,
        eid,
        MEMORY_TYPE_TASK_OUTCOME,
        f"Completed: {title}",
        importance_score=0.65,
    )
    if task.get("blockers"):
        write_long_memory(
            report_id,
            eid,
            MEMORY_TYPE_LEARNED_PATTERN,
            f"Resolved blockers on '{title}'",
            importance_score=0.55,
        )


def on_task_blocked(report_id: str, employee_id: str | None, task: dict[str, Any], blocker: str) -> None:
    eid = str(employee_id or task.get("owner_employee_id") or "")
    if not eid:
        return
    title = str(task.get("title") or "task")
    write_long_memory(
        report_id,
        eid,
        MEMORY_TYPE_MISTAKE,
        f"Blocked on '{title}': {blocker}",
        importance_score=0.78,
    )
    write_long_memory(
        report_id,
        eid,
        MEMORY_TYPE_TASK_OUTCOME,
        f"Failed/blocked: {title}",
        importance_score=0.7,
    )


def on_founder_decision(
    report_id: str,
    *,
    approved: bool,
    title: str,
    requester_employee_id: str | None = None,
) -> None:
    key = title.strip().lower()[:80] or "decision"
    if approved:
        record_founder_preference(
            report_id,
            f"approved:{key}",
            f"Founder approved: {title}",
            confidence=0.88,
            observed_by_employee_id=requester_employee_id,
        )
    else:
        record_founder_preference(
            report_id,
            f"rejected:{key}",
            f"Founder rejected: {title}",
            confidence=0.92,
            observed_by_employee_id=requester_employee_id,
        )
        if requester_employee_id:
            write_long_memory(
                report_id,
                requester_employee_id,
                MEMORY_TYPE_FOUNDER_PREFERENCE,
                f"Founder rejected request: {title}",
                importance_score=0.9,
            )


def on_team_conflict(
    report_id: str,
    employee_id: str,
    other_employee_id: str,
    description: str,
    *,
    severity: float = 0.6,
) -> None:
    write_long_memory(
        report_id,
        employee_id,
        MEMORY_TYPE_TEAM_CONFLICT,
        description,
        importance_score=min(0.95, 0.5 + severity),
    )
    upsert_relationship(
        report_id,
        employee_id,
        other_employee_id,
        conflict_delta=0.15 * severity,
        trust_delta=-0.08 * severity,
    )


def on_collaboration(report_id: str, employee_a: str, employee_b: str, note: str = "") -> None:
    upsert_relationship(
        report_id,
        employee_a,
        employee_b,
        trust_delta=0.04,
        collaboration_delta=0.06,
        conflict_delta=-0.02,
    )
    if note:
        write_long_memory(report_id, employee_a, MEMORY_TYPE_LEARNED_PATTERN, note, importance_score=0.5)


def on_kpi_change(
    report_id: str,
    employee_id: str | None,
    kpi_name: str,
    old_value: float,
    new_value: float,
) -> None:
    if old_value == new_value:
        return
    base = abs(old_value) if old_value else 1.0
    delta = abs(new_value - old_value)
    if delta < _SIGNIFICANT_KPI_ABS and (delta / base) < _SIGNIFICANT_KPI_PCT:
        return
    direction = "rose" if new_value > old_value else "fell"
    text = f"KPI {kpi_name} {direction} from {old_value} to {new_value}"
    target = employee_id or _founder_proxy_id(report_id)
    if target:
        write_long_memory(
            report_id,
            target,
            MEMORY_TYPE_LEARNED_PATTERN,
            text,
            importance_score=0.72,
        )


def _founder_proxy_id(report_id: str) -> str | None:
    from iidatech.execution.task_engine import founder_employee_id

    return founder_employee_id(report_id)


def on_escalation_ignored(
    report_id: str,
    escalator_id: str,
    ignorer_id: str,
    *,
    issue: str,
) -> None:
    esc_role = _role_label(report_id, escalator_id)
    ign_role = _role_label(report_id, ignorer_id)
    on_team_conflict(
        report_id,
        escalator_id,
        ignorer_id,
        f"{ign_role} ignored {esc_role} warning: {issue}",
        severity=0.75,
    )


def relationship_narratives(report_id: str, employee_id: str, roster: list[dict]) -> list[str]:
    role_by_id = {str(e["employee_id"]): str(e.get("role") or e.get("name") or "") for e in roster}
    lines: list[str] = []
    for rel in list_relationships_for_employee(report_id, employee_id):
        other = str(rel.get("other_employee_id") or "")
        label = role_by_id.get(other, "teammate")
        trust = float(rel.get("trust_score") or 0.5)
        conflict = float(rel.get("conflict_score") or 0)
        if trust >= 0.72 and conflict < 0.25:
            lines.append(f"{label} is reliable (trust {trust:.0%})")
        elif conflict >= 0.45:
            lines.append(f"Tension with {label} — conflict {conflict:.0%}")
        elif trust < 0.4:
            lines.append(f"Low trust with {label} ({trust:.0%})")
    return lines[:8]