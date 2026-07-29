"""Office workspace scope: full office, department(s), or specific employees."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from iidatech.execution.os2_team_bridge import HARNESS_ROLE_MAP

HARNESS_DEPARTMENTS: dict[str, str] = {
    "research_analyst": "Research",
    "sales_lead": "Sales",
    "growth_marketer": "Marketing",
    "creative_producer": "Marketing",
    "ops_manager": "Operations",
}

_ROLE_DEPARTMENTS: dict[str, str] = {
    "Research Analyst": "Research",
    "Sales Lead": "Sales",
    "Growth Marketer": "Marketing",
    "Operations Manager": "Operations",
    "COO": "Operations",
    "Finance Manager": "Finance",
    "Founder": "Leadership",
    "Product Manager": "Product",
    "Recruiter": "People",
    "Customer Success": "Customer Success",
    "Legal": "Legal",
}

SCOPE_MODES = ("full_office", "department", "employee")


@dataclass
class OfficeScope:
    mode: str = "full_office"
    departments: list[str] = field(default_factory=list)
    harness_ids: list[str] = field(default_factory=list)

    def is_full_office(self) -> bool:
        return self.mode == "full_office"

    def label(self) -> str:
        if self.is_full_office():
            return "Full office"
        if self.mode == "department":
            if not self.departments:
                return "Department (pick below)"
            if len(self.departments) == 1:
                return f"Department: {self.departments[0]}"
            return f"Departments: {', '.join(self.departments)}"
        if self.harness_ids:
            return f"{len(self.harness_ids)} employee(s)"
        return "Employee / team (pick below)"

    def run_button_label(self) -> str:
        if self.is_full_office():
            return "Run full office day"
        if self.mode == "department":
            return "Run department day"
        return "Run team day"

    def active_harness_ids(self, all_harness_ids: list[str]) -> set[str] | None:
        if self.is_full_office():
            return None
        allowed = set(all_harness_ids)
        if self.mode == "department":
            ids = harness_ids_for_departments(self.departments)
            return {hid for hid in ids if hid in allowed}
        return {hid for hid in self.harness_ids if hid in allowed}

    def is_configured(self) -> bool:
        if self.is_full_office():
            return True
        if self.mode == "department":
            return bool(self.departments)
        return bool(self.harness_ids)

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "departments": list(self.departments),
            "harness_ids": list(self.harness_ids),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> OfficeScope:
        if not isinstance(data, dict):
            return cls()
        mode = str(data.get("mode") or "full_office")
        if mode not in SCOPE_MODES:
            mode = "full_office"
        departments = [str(d) for d in (data.get("departments") or []) if str(d).strip()]
        harness_ids = [str(h) for h in (data.get("harness_ids") or []) if str(h).strip()]
        return cls(mode=mode, departments=departments, harness_ids=harness_ids)


def department_for_harness(harness: dict[str, Any]) -> str:
    hid = str(harness.get("id") or "")
    if hid in HARNESS_DEPARTMENTS:
        return HARNESS_DEPARTMENTS[hid]
    role = str(harness.get("role") or HARNESS_ROLE_MAP.get(hid) or "")
    return _ROLE_DEPARTMENTS.get(role, "General")


def departments_for_harnesses(harnesses: list[dict[str, Any]]) -> list[str]:
    depts = {department_for_harness(h) for h in harnesses if isinstance(h, dict) and h.get("id")}
    return sorted(depts)


def harness_ids_for_departments(departments: list[str]) -> list[str]:
    wanted = {str(d).strip() for d in departments if str(d).strip()}
    if not wanted:
        return []
    ids: list[str] = []
    for hid, dept in HARNESS_DEPARTMENTS.items():
        if dept in wanted:
            ids.append(hid)
    return ids


def filter_harnesses(harnesses: list[dict[str, Any]], scope: OfficeScope) -> list[dict[str, Any]]:
    ids = scope.active_harness_ids([str(h.get("id") or "") for h in harnesses])
    if ids is None:
        return list(harnesses)
    return [h for h in harnesses if str(h.get("id") or "") in ids]


def item_in_scope(item: dict[str, Any], harness_ids: set[str] | None) -> bool:
    if harness_ids is None:
        return True
    return str(item.get("harness_id") or "") in harness_ids


def filter_board_rows(rows: list[dict[str, Any]], harness_ids: set[str] | None) -> list[dict[str, Any]]:
    if harness_ids is None:
        return rows
    return [r for r in rows if item_in_scope(r, harness_ids)]


def scope_session_key(report_id: str) -> str:
    return f"office_scope_{report_id}"


def load_scope(st: Any, report_id: str, *, office_state: dict[str, Any] | None = None) -> OfficeScope:
    key = scope_session_key(report_id)
    cached = st.session_state.get(key)
    if isinstance(cached, dict):
        return OfficeScope.from_dict(cached)
    if isinstance(office_state, dict) and isinstance(office_state.get("scope"), dict):
        scope = OfficeScope.from_dict(office_state["scope"])
        st.session_state[key] = scope.to_dict()
        return scope
    return OfficeScope()


def save_scope(st: Any, report_id: str, scope: OfficeScope, *, office_state: dict[str, Any] | None = None) -> None:
    st.session_state[scope_session_key(report_id)] = scope.to_dict()
    if isinstance(office_state, dict):
        office_state["scope"] = scope.to_dict()
