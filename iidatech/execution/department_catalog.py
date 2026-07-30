"""Comprehensive department catalog for Employee OS."""
from __future__ import annotations

import re
import uuid
from typing import Any

# Root -> divisions -> departments
DEPARTMENT_CATALOG: list[dict[str, Any]] = [
    {"id": "executive", "name": "Executive", "parent": None, "description": "Leadership and strategy"},
    {"id": "operations", "name": "Operations", "parent": "executive", "description": "Day-to-day company operations"},
    {"id": "finance", "name": "Finance", "parent": "executive", "description": "Accounting, budgeting, and reporting"},
    {"id": "legal", "name": "Legal", "parent": "executive", "description": "Contracts, compliance, and IP"},
    {"id": "hr", "name": "Human Resources", "parent": "executive", "description": "Hiring, culture, and people ops"},
    {"id": "admin", "name": "Administration", "parent": "executive", "description": "Office admin and vendor management"},
    {"id": "sales", "name": "Sales", "parent": "operations", "description": "Pipeline, outreach, and revenue"},
    {"id": "marketing", "name": "Marketing", "parent": "operations", "description": "Growth, campaigns, and brand"},
    {"id": "product", "name": "Product", "parent": "operations", "description": "Roadmap, UX, and prioritization"},
    {"id": "engineering", "name": "Engineering", "parent": "operations", "description": "Build, ship, and maintain product"},
    {"id": "customer_success", "name": "Customer Success", "parent": "operations", "description": "Onboarding, retention, and support"},
    {"id": "research", "name": "Research", "parent": "operations", "description": "Market intel and competitive analysis"},
    {"id": "support", "name": "Support", "parent": "customer_success", "description": "Tickets and customer help"},
    {"id": "design", "name": "Design", "parent": "product", "description": "Visual design and creative assets"},
]

DEPARTMENT_ROLES: dict[str, list[dict[str, Any]]] = {
    "executive": [{"role": "CEO", "harness_id": "ops_manager", "authority": 10}],
    "operations": [{"role": "COO", "harness_id": "ops_manager", "authority": 9}],
    "finance": [{"role": "Finance Manager", "harness_id": "ops_manager", "authority": 7}],
    "legal": [{"role": "Legal Counsel", "harness_id": "ops_manager", "authority": 7}],
    "hr": [{"role": "HR Manager", "harness_id": "ops_manager", "authority": 6}],
    "admin": [{"role": "Office Manager", "harness_id": "ops_manager", "authority": 5}],
    "sales": [{"role": "Sales Lead", "harness_id": "sales_lead", "authority": 7}],
    "marketing": [
        {"role": "Growth Marketer", "harness_id": "growth_marketer", "authority": 6},
        {"role": "Creative Producer", "harness_id": "creative_producer", "authority": 5},
    ],
    "product": [{"role": "Product Manager", "harness_id": "ops_manager", "authority": 7}],
    "engineering": [{"role": "Engineering Lead", "harness_id": "ops_manager", "authority": 7}],
    "customer_success": [{"role": "Customer Success", "harness_id": "ops_manager", "authority": 6}],
    "research": [{"role": "Research Analyst", "harness_id": "research_analyst", "authority": 6}],
    "support": [{"role": "Support Specialist", "harness_id": "ops_manager", "authority": 5}],
    "design": [{"role": "Designer", "harness_id": "creative_producer", "authority": 5}],
}

_AGENT_NAMES = {
    "sales": ["Alex", "Sam", "Jordan", "Casey", "Riley"],
    "marketing": ["Morgan", "Taylor", "Avery", "Quinn", "Blake"],
    "research": ["Sam", "Drew", "Jamie", "Skyler", "Reese"],
    "engineering": ["Dev", "Kai", "Noah", "Ellis", "Rowan"],
    "product": ["Priya", "Maya", "Lena", "Sofia", "Nina"],
    "finance": ["Finn", "Grace", "Henry", "Ivy", "Leo"],
    "operations": ["Jordan", "Cameron", "Dakota", "Emery", "Frankie"],
    "customer_success": ["Chris", "Dana", "Evan", "Faye", "Glen"],
    "hr": ["Hana", "Isla", "Jude", "Kira", "Liam"],
    "legal": ["Max", "Nora", "Owen", "Paige", "Quinn"],
    "admin": ["Robin", "Sage", "Tess", "Uma", "Vera"],
    "executive": ["Alex", "Jordan", "Morgan"],
    "support": ["Wren", "Xander", "Yara", "Zoe", "Ash"],
    "design": ["Riley", "Sage", "Blair", "Cruz", "Dell"],
}


def catalog_list() -> list[dict[str, Any]]:
    return [dict(d) for d in DEPARTMENT_CATALOG]


def department_by_id(dept_id: str) -> dict[str, Any] | None:
    return next((d for d in DEPARTMENT_CATALOG if d["id"] == dept_id), None)


def roles_for_department(dept_id: str) -> list[dict[str, Any]]:
    return [dict(r) for r in DEPARTMENT_ROLES.get(dept_id, [])]


def default_role_for_department(dept_id: str) -> dict[str, Any]:
    roles = roles_for_department(dept_id)
    if roles:
        return roles[0]
    return {"role": "Team Member", "harness_id": "ops_manager", "authority": 5}


def department_display_name(dept_id: str) -> str:
    dept = department_by_id(dept_id)
    return str(dept["name"]) if dept else dept_id.replace("_", " ").title()


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:20]


def agent_display_name(dept_id: str, index: int, role: str) -> str:
    pool = _AGENT_NAMES.get(dept_id, ["Agent"])
    first = pool[index % len(pool)]
    dept_name = department_display_name(dept_id)
    return f"{first} — {role or dept_name}"


def build_org_tree(
    hired: list[dict[str, Any]],
    agents: list[dict[str, Any]],
    humans: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    hired_ids = {str(h.get("id") or "") for h in hired}
    hired_map = {str(h.get("id") or ""): h for h in hired}

    def node_for(dept_id: str) -> dict[str, Any] | None:
        if dept_id not in hired_ids and not _has_hired_descendant(dept_id, hired_ids):
            return None
        dept = department_by_id(dept_id) or {"id": dept_id, "name": dept_id, "parent": None}
        hire = hired_map.get(dept_id, {})
        dept_agents = [a for a in agents if str(a.get("department") or "") == dept_id]
        dept_humans = [h for h in (humans or []) if dept_id in (h.get("departments") or [])]
        children = []
        for child in DEPARTMENT_CATALOG:
            if str(child.get("parent") or "") == dept_id:
                cn = node_for(child["id"])
                if cn:
                    children.append(cn)
        return {
            "id": dept_id,
            "name": dept.get("name") or dept_id,
            "headcount": int(hire.get("headcount") or 0),
            "agents": dept_agents,
            "humans": dept_humans,
            "children": children,
        }

    def _has_hired_descendant(dept_id: str, ids: set[str]) -> bool:
        for d in DEPARTMENT_CATALOG:
            if str(d.get("parent") or "") == dept_id:
                if d["id"] in ids or _has_hired_descendant(d["id"], ids):
                    return True
        return False

    roots = []
    for d in DEPARTMENT_CATALOG:
        if not d.get("parent"):
            n = node_for(d["id"])
            if n:
                roots.append(n)
    return {"roots": roots, "total_agents": len(agents), "total_humans": len(humans or [])}


def provision_agent_specs(dept_id: str, headcount: int, existing: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Build agent records up to headcount for a department."""
    role_spec = default_role_for_department(dept_id)
    role = str(role_spec.get("role") or "Team Member")
    base_harness = str(role_spec.get("harness_id") or "ops_manager")
    dept_name = department_display_name(dept_id)
    current = [a for a in existing if str(a.get("department") or "") == dept_id]
    specs: list[dict[str, Any]] = []
    for i in range(headcount):
        if i < len(current):
            specs.append(dict(current[i]))
            continue
        idx = i + 1
        agent_id = f"{dept_id}_{idx}"
        harness_id = base_harness if idx == 1 and not any(a.get("harness_id") == base_harness for a in current) else f"agent_{dept_id}_{idx}"
        specs.append({
            "id": agent_id,
            "name": agent_display_name(dept_id, i, role),
            "department": dept_id,
            "role": role,
            "harness_id": harness_id,
            "base_harness_id": base_harness,
        })
    return specs[:headcount]


def custom_harness_for_agent(agent: dict[str, Any]) -> dict[str, Any] | None:
    from iidatech.execution.employee_os2_harness import OS2_HARNESSES

    hid = str(agent.get("harness_id") or "")
    base = str(agent.get("base_harness_id") or hid)
    if hid == base or not hid.startswith("agent_"):
        return None
    base_row = next((h for h in OS2_HARNESSES if h.get("id") == base), None)
    return {
        "id": hid,
        "name": str(agent.get("name") or hid),
        "role": str(agent.get("role") or "Team Member"),
        "base_harness_id": base,
        "tagline": (base_row or {}).get("tagline") or f"{department_display_name(str(agent.get('department') or ''))} workflows",
        "starters": list((base_row or {}).get("starters") or [])[:3],
        "department": str(agent.get("department") or ""),
    }


def new_human_id() -> str:
    return f"human_{uuid.uuid4().hex[:10]}"
