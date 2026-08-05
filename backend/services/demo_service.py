"""Demo mode: view-only sample workspace, no mutations."""

from __future__ import annotations

from fastapi import HTTPException

DEMO_EMAIL = "demo@local"
DEMO_WORKSPACE_ID = "demo_readonly"


def is_demo_user(email: str) -> bool:
    return str(email or "").strip().lower() == DEMO_EMAIL


def is_readonly_workspace(workspace: dict | None) -> bool:
    if not workspace or not isinstance(workspace, dict):
        return False
    ws_id = str(workspace.get("workspace_id") or "").strip()
    return bool(workspace.get("demo_readonly")) or ws_id == DEMO_WORKSPACE_ID


def block_demo_mutation(email: str, *, action: str = "change") -> None:
    if is_demo_user(email):
        raise HTTPException(
            status_code=403,
            detail={
                "message": f"Demo mode is view-only — you cannot {action}. Sign up for a free account to create projects.",
                "signup_href": "/login?mode=register",
                "demo": True,
            },
        )


def block_workspace_mutation(email: str, workspace: dict | None, *, action: str = "change") -> None:
    block_demo_mutation(email, action=action)
    if is_readonly_workspace(workspace):
        raise HTTPException(
            status_code=403,
            detail={
                "message": f"This sample workspace is read-only — you cannot {action}. Sign up to create your own projects.",
                "signup_href": "/login?mode=register",
                "demo": True,
            },
        )


def demo_workspace_row() -> dict:
    return {
        "workspace_id": DEMO_WORKSPACE_ID,
        "idea": "CRM automation for SMBs (sample)",
        "country": "India",
        "industry": "SaaS / B2B Software",
        "current_path": "Understand your market",
        "updated_at": "2026-03-01T08:30:00Z",
        "path": f"opportunity_workspaces/{DEMO_WORKSPACE_ID}/workspace.json",
        "has_report": True,
        "has_plan": True,
        "demo_readonly": True,
    }


def demo_employee_os_snapshot() -> dict:
    """Pre-hired lean team for the read-only demo office."""
    return {
        "available": True,
        "scope": {"mode": "full_office", "departments": ["sales", "marketing", "research", "operations"], "harness_ids": []},
        "departments": [
            {"id": "sales", "name": "Sales", "headcount": 1},
            {"id": "marketing", "name": "Marketing", "headcount": 1},
            {"id": "research", "name": "Research", "headcount": 1},
            {"id": "operations", "name": "Operations", "headcount": 1},
        ],
        "agents": [
            {"id": "demo_sales", "harness_id": "sales_lead", "name": "Alex — Sales Lead", "role": "Sales Lead", "department": "sales", "tagline": "Pipeline and outreach"},
            {"id": "demo_marketing", "harness_id": "growth_marketer", "name": "Morgan — Growth Marketer", "role": "Growth Marketer", "department": "marketing", "tagline": "Campaigns and brand"},
            {"id": "demo_research", "harness_id": "research_analyst", "name": "Sam — Research Analyst", "role": "Research Analyst", "department": "research", "tagline": "Market intel"},
            {"id": "demo_ops", "harness_id": "ops_manager", "name": "Jordan — Ops Lead", "role": "Ops Lead", "department": "operations", "tagline": "Execution and handoffs"},
        ],
        "humans": [
            {"id": "demo_founder", "name": "You (Founder)", "role": "Founder", "departments": ["executive", "sales", "marketing"]},
        ],
        "collaboration": {
            "summary": {"ai_done": 2, "ai_total": 5, "human_done": 0, "human_total": 2, "agents_active": 4, "humans_on_team": 1},
            "human_queue": [
                {"action": "Approve LinkedIn campaign draft", "status": "awaiting_you"},
                {"action": "Review competitor pricing memo", "status": "awaiting_you"},
            ],
        },
    }


def demo_checklist_snapshot() -> dict:
    return {
        "items": [
            {"id": "demo_t1", "title": "Qualified lead list (CSV)", "status": "completed", "assignee": "Alex — Sales Lead", "assignee_type": "ai", "result": "42 clinic SMB leads in Mumbai/Bangalore with WhatsApp-ready notes."},
            {"id": "demo_t2", "title": "LinkedIn + email campaign draft", "status": "awaiting_approval", "assignee": "Morgan — Growth Marketer", "assignee_type": "ai", "ai_action": "Draft ready for founder approval before posting.", "result": "3-post LinkedIn sequence + email nurture for clinic owners."},
            {"id": "demo_t3", "title": "Competitor and pricing evidence pass", "status": "completed", "assignee": "Sam — Research Analyst", "assignee_type": "ai", "result": "Zoho / Freshsales / Kylas pricing matrix with India SMB positioning."},
            {"id": "demo_t4", "title": "Weekly execution SOP", "status": "pending", "assignee": "Jordan — Ops Lead", "assignee_type": "ai", "ai_action": "Build handoff checklist from research + plan."},
            {"id": "demo_t5", "title": "Approve outreach sequence", "status": "pending", "assignee": "You (Founder)", "assignee_type": "human", "human_action": "Review and approve before agents send email."},
        ]
    }


def demo_office_state_snapshot() -> dict:
    return {
        "phase": "execution",
        "goals": ["Cut churn below 3.5%", "Prove clinic vertical GTM", "Unify CAC by channel"],
        "last_mentor": "Taylor: Demo office is live. Browse The Office, Tasks, and Agents — sign up to hire your own team and run real work.",
        "log": [
            {"from": "Taylor", "text": "Standup complete — Sales and Marketing are executing.", "when": "09:02"},
            {"from": "Alex", "text": "Lead list delivered — 42 qualified clinics.", "when": "09:18"},
            {"from": "Morgan", "text": "Campaign draft waiting on your approval.", "when": "09:41"},
            {"from": "Sam", "text": "Competitor pricing memo is in the task board.", "when": "10:05"},
        ],
        "scope": {"mode": "full_office", "departments": ["sales", "marketing", "research", "operations"], "harness_ids": []},
    }


def ensure_demo_employee_os(workspace: dict) -> dict:
    """Ensure demo workspace returns a browsable office even when disk saves are blocked."""
    if not is_readonly_workspace(workspace):
        os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
        return os2 if isinstance(os2, dict) else {}
    os2 = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    if not (os2.get("departments") or os2.get("agents")):
        os2 = demo_employee_os_snapshot()
        workspace["employee_os"] = os2
    return os2


def ensure_demo_os2_disk(report_id: str) -> None:
    """Seed checklist + office state on disk for demo browsing (idempotent)."""
    try:
        from iidatech.execution.os2_workflow import load_checklist, save_checklist
        from backend.services.os2_service import load_office_state_disk, save_office_state_disk

        if not load_checklist(report_id):
            save_checklist(report_id, demo_checklist_snapshot())
        office = load_office_state_disk(report_id)
        if not office.get("log") and office.get("phase") in (None, "arrival"):
            save_office_state_disk(report_id, demo_office_state_snapshot())
    except Exception:
        pass