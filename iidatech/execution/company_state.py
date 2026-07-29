"""Company state -- revenue, burn, KPIs, growth metrics, active campaigns."""
from __future__ import annotations

from typing import Any

from iidatech.storage.execution_repository import get_company_state_row, list_kpi_history, upsert_company_state_row

_DEFAULT_STATE: dict[str, Any] = {
    "revenue": 0.0,
    "burn": 0.0,
    "kpis": {},
    "growth_metrics": {},
    "active_campaigns": [],
}


def load_company_state(report_id: str) -> dict[str, Any]:
    """Load persisted company state for a report."""
    report_id = str(report_id or "").strip()
    if not report_id:
        return dict(_DEFAULT_STATE)
    state = get_company_state_row(report_id)
    # Merge latest KPI snapshots into kpis map
    for row in list_kpi_history(report_id, limit=25):
        name = str(row.get("kpi_name") or "").strip()
        if name:
            state.setdefault("kpis", {})[name] = row.get("kpi_value")
    return state


def update_company_state(report_id: str, changes: dict[str, Any] | None) -> dict[str, Any]:
    """Patch company state (revenue, burn, kpis, growth_metrics, active_campaigns)."""
    report_id = str(report_id or "").strip()
    if not report_id:
        return dict(_DEFAULT_STATE)
    changes = changes if isinstance(changes, dict) else {}
    current = load_company_state(report_id)

    if "kpis" in changes and isinstance(changes["kpis"], dict):
        current["kpis"] = {**_as_dict(current.get("kpis")), **changes["kpis"]}
        changes = {k: v for k, v in changes.items() if k != "kpis"}

    if "growth_metrics" in changes and isinstance(changes["growth_metrics"], dict):
        current["growth_metrics"] = {**_as_dict(current.get("growth_metrics")), **changes["growth_metrics"]}
        changes = {k: v for k, v in changes.items() if k != "growth_metrics"}

    if "active_campaigns" in changes:
        campaigns = list(changes["active_campaigns"])
        if changes.get("append_campaigns"):
            campaigns = list(current.get("active_campaigns") or []) + campaigns
        current["active_campaigns"] = campaigns[-50:]
        changes = {k: v for k, v in changes.items() if k not in ("active_campaigns", "append_campaigns")}

    current.update(changes)
    return upsert_company_state_row(report_id, current)


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}
