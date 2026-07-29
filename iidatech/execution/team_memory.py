"""Shared and private team memory accessors (delegates to memory_engine)."""
from __future__ import annotations

from typing import Any

from iidatech.execution.memory_engine import (
    build_agent_context as _build_agent_context,
    load_team_shared_memory,
    update_team_shared_memory,
)


def get_shared_team_memory(report_id: str) -> dict[str, Any]:
    row = load_team_shared_memory(report_id)
    ctx = row.get("company_context") if isinstance(row.get("company_context"), dict) else {}
    return {**ctx, "goals": row.get("goals"), "blockers": row.get("blockers")}


def update_shared_team_memory(report_id: str, patch: dict[str, Any]) -> dict[str, Any]:
    row = update_team_shared_memory(report_id, patch)
    ctx = row.get("company_context") if isinstance(row.get("company_context"), dict) else {}
    return {**ctx, "goals": row.get("goals"), "blockers": row.get("blockers")}


def build_agent_context(report_id: str, employee_id: str, *, report_context=None) -> dict[str, Any]:
    return _build_agent_context(employee_id, report_context=report_context, report_id=report_id)
