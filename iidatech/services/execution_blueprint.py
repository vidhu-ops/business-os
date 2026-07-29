"""Pass 3 - execution blueprint with daily tasks and employee mapping."""
from __future__ import annotations
from typing import Any

_VALIDATION_REQUIRED = {
    "status": "validation_required",
    "verified": False,
    "reason": "insufficient real evidence",
}

_GENERIC_BUYER = frozenset({"named buyer profile", "buyer profile", "validated buyer profile"})
_GENERIC_TRIGGER = frozenset({"buyer trigger", "validated buyer trigger", "buyer trigger event"})

def _as_dict(v):
    return v if isinstance(v, dict) else {}

def _as_list(v):
    return v if isinstance(v, list) else []

def _day_task(day, owner, task, kpi="", deliverable="", depends_on=None):
    return {"day": day, "owner": owner, "task": task, "kpi": kpi, "deliverable": deliverable, "depends_on": depends_on or []}

def build_execution_blueprint(plan: dict, *, idea: str = "", geography: str = "") -> dict:
    plan = plan if isinstance(plan, dict) else {}
    gtm = _as_dict(plan.get("go_to_market") or plan.get("go_to_market_strategy"))
    wedge = _as_dict(gtm.get("launch_wedge"))
    buyer = str(wedge.get("buyer") or "").strip()
    trigger = str(wedge.get("trigger") or "").strip()
    geo = wedge.get("geography") or geography
    if not buyer or buyer.lower() in _GENERIC_BUYER or not trigger or trigger.lower() in _GENERIC_TRIGGER:
        return {
            **_VALIDATION_REQUIRED,
            "phase_0_validation": {"days": "1-7", "daily_tasks": []},
            "phase_1_mvp": {"weeks": "2-4", "tasks": []},
            "phase_2_pilot_revenue": {"month": 2, "tasks": []},
            "phase_3_growth": {"months": "3-6", "tasks": []},
            "phase_4_scale": {"months": "6-12", "tasks": []},
            "revenue_fast_path": [],
        }
    phase0 = [
        _day_task(1, "founder", f"Write one-page wedge memo: {idea} for {buyer} in {geo}", "memo complete", "wedge_memo.md"),
        _day_task(2, "founder", "List 20 named target accounts matching ICP filters", "20 accounts", "account_list.csv"),
        _day_task(3, "founder", "Run 5 warm-intro mapping sessions (LinkedIn, advisors, customers)", "5 intro paths", "intro_map"),
        _day_task(4, "sales", f"Draft discovery call script around trigger: {trigger}", "script ready", "discovery_script.md", [1]),
        _day_task(5, "founder", "Book 3 discovery calls", "3 calls booked", "calendar holds", [2, 3]),
        _day_task(6, "market_research", "Document competitor pricing from 3 primary sources", "3 price points", "pricing_sheet", [1]),
        _day_task(7, "founder", "Go/no-go gate: named buyer + pilot metric + geography confirmed", "gate decision", "validation_gate.json", [4, 5, 6]),
    ]
    phase1 = {
        "weeks": "2-4",
        "tasks": [
            {"owner": "product_builder", "task": "Define MVP scope: one use case, one geography, one metric", "deliverable": "mvp_scope.md"},
            {"owner": "systems", "task": "Select stack and integration map for pilot delivery", "deliverable": "stack_decision.md"},
            {"owner": "marketing_manager", "task": "Landing page + outreach sequence for top ICP", "deliverable": "gtm_assets"},
            {"owner": "compliance_officer", "task": "Compliance checklist for launch geography", "deliverable": "compliance_checklist"},
        ],
    }
    phase2 = {
        "month": 2,
        "tasks": [
            {"owner": "sales_lead", "task": "Run 10 discovery calls; capture objections and WTP", "kpi": "10 calls", "deliverable": "call_notes"},
            {"owner": "sales_lead", "task": "Secure 1-2 LOI or paid pilot commitments", "kpi": "1 LOI", "deliverable": "pilot_contract_draft"},
            {"owner": "product_builder", "task": "Deliver 4-6 week MVP for first pilot only", "kpi": "MVP shipped", "deliverable": "pilot_build"},
            {"owner": "customer_success", "task": "Pilot success metric tracking dashboard", "kpi": "metric tracked", "deliverable": "pilot_dashboard"},
        ],
    }
    phase3 = {
        "months": "3-6",
        "tasks": [
            {"owner": "growth_marketer", "task": "Scale winning acquisition channel from phase 2", "kpi": "CAC measured"},
            {"owner": "operations_manager", "task": "Hire/contract first ops or sales support at milestone", "kpi": "role filled"},
            {"owner": "automation_engineer", "task": "Automate repeat delivery workflows", "kpi": "hours saved"},
            {"owner": "finance_analyst", "task": "Update unit economics with live pilot data", "kpi": "LTV/CAC refreshed"},
        ],
    }
    phase4 = {
        "months": "6-12",
        "tasks": [
            {"owner": "ceo_strategy", "task": "Geographic or vertical expansion decision", "deliverable": "expansion_memo"},
            {"owner": "finance_analyst", "task": "Fundraising package if unit economics support raise", "deliverable": "investor_deck"},
            {"owner": "operations_manager", "task": "SOP library for delivery, sales, and support", "deliverable": "sop_index"},
        ],
    }
    return {
        "phase_0_validation": {"days": "1-7", "daily_tasks": phase0},
        "phase_1_mvp": phase1,
        "phase_2_pilot_revenue": phase2,
        "phase_3_growth": phase3,
        "phase_4_scale": phase4,
        "revenue_fast_path": [
            "Sell pilot before full build",
            "Price anchor from evidence-backed pricing row",
            "Founder-led sales until 3 paying customers",
        ],
    }

def execution_tasks_for_employees(execution_blueprint: dict) -> list[dict]:
    """Flatten execution blueprint into employee-assignable tasks."""
    bp = execution_blueprint if isinstance(execution_blueprint, dict) else {}
    flat = []
    for row in _as_list(_as_dict(bp.get("phase_0_validation")).get("daily_tasks")):
        flat.append({**row, "phase": "validation", "workstream": row.get("task", "")[:80]})
    for phase_key, phase_label in (("phase_1_mvp", "mvp"), ("phase_2_pilot_revenue", "pilot"), ("phase_3_growth", "growth"), ("phase_4_scale", "scale")):
        block = _as_dict(bp.get(phase_key))
        for row in _as_list(block.get("tasks")):
            if isinstance(row, dict):
                flat.append({**row, "phase": phase_label, "workstream": str(row.get("task", ""))[:80]})
    return flat

def execution_to_first_90_day_plan(execution_blueprint: dict) -> list[dict]:
    """Legacy list shape for first_90_day_plan consumers."""
    bp = execution_blueprint if isinstance(execution_blueprint, dict) else {}
    rows = []
    for task in _as_list(_as_dict(bp.get("phase_0_validation")).get("daily_tasks")):
        rows.append({"period": f"Day {task.get('day')}", "focus": task.get("task"), "owner": task.get("owner"), "deliverable": task.get("deliverable")})
    rows.append({"period": "Week 2-4", "focus": "MVP build and GTM assets", "owner": "product + marketing", "deliverable": "mvp_scope + landing page"})
    rows.append({"period": "Month 2", "focus": "Pilot revenue and LOI", "owner": "sales", "deliverable": "paid pilot"})
    rows.append({"period": "Month 3-6", "focus": "Scale channel and hire at milestone", "owner": "founder + ops", "deliverable": "repeatable GTM"})
    return rows