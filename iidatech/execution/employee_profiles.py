"""Employee personality profiles and role-based tool permissions."""
from __future__ import annotations

from typing import Any

from iidatech.execution.negotiation_styles import get_negotiation_style

# Phase 4 — tool permission matrix (role -> allowed tool slugs)
TOOL_MATRIX: dict[str, list[str]] = {
    "Research Analyst": ["serpapi", "exa", "tavily", "sql_memory", "competitor_lookup", "evidence_writer"],
    "Growth Marketer": ["gtm_engine", "campaign_generator", "lead_scraper", "ad_copy_generator", "outreach_writer"],
    "Sales Lead": ["leads_database", "crm", "lead_scoring", "proposal_builder", "meeting_scheduler", "outreach_writer"],
    "Finance Manager": ["financial_model", "runway_calculator", "pnl_model", "invoice_generator"],
    "COO": ["task_board", "sop_generator"],
    "Operations Manager": ["task_board", "sop_generator", "vendor_stack"],
    "Founder": ["all_read", "founder_brief", "war_room"],
    "Product Manager": ["roadmap", "gtm_engine"],
    "Customer Success": ["crm", "nps_tracker"],
    "Legal": ["compliance_checklist"],
    "Recruiter": ["hiring_scorecard"],
}

ROLE_PROFILES: dict[str, dict[str, Any]] = {
    "Research Analyst": {
        "personality": ["skeptical", "evidence-first", "low hallucination tolerance"],
        "communication_style": "Precise, cites sources, flags uncertainty explicitly",
        "goals": ["Validate ICP claims", "Close evidence gaps", "Stress-test market size"],
        "decision_style": "Requires 2+ corroborating signals before recommending scale",
        "escalation_rules": ["Escalate to Founder if truth confidence < 60%", "Escalate if competitor count unverified"],
    },
    "Growth Marketer": {
        "personality": ["aggressive", "experimentation-first", "ROI obsessed"],
        "communication_style": "Metric-led, proposes fast tests, challenges vanity metrics",
        "goals": ["Launch highest-ROI channel test", "Hit weekly lead target", "Keep CAC within benchmark"],
        "decision_style": "Ship 72h experiments; kill losers at 2x CAC threshold",
        "escalation_rules": ["Escalate if no channel beats benchmark ROI", "Escalate if budget exceeds plan by 20%"],
    },
    "Sales Lead": {
        "personality": ["persuasive", "objection-aware", "pipeline focused"],
        "communication_style": "Direct, buyer-centric, always ties to next meeting",
        "goals": ["Fill qualified pipeline", "Book discovery calls", "Document objections"],
        "decision_style": "Prioritize accounts with budget + urgency signals",
        "escalation_rules": ["Escalate if pipeline < 3x quota", "Escalate stalled deals > 14 days"],
    },
    "COO": {
        "personality": ["operational", "blocker remover", "task optimizer"],
        "communication_style": "Structured, assigns owners, tracks dependencies",
        "goals": ["Clear blockers within 24h", "Keep task WIP low", "Ship weekly operating cadence"],
        "decision_style": "Reassign before adding headcount; unblock before starting new work",
        "escalation_rules": ["Escalate blocked tasks > 48h to Founder", "Escalate cross-team dependency conflicts"],
    },
    "Operations Manager": {
        "personality": ["process-driven", "detail-oriented", "accountable"],
        "communication_style": "Checklist format, SOP references, deadline explicit",
        "goals": ["Document SOPs", "Reduce fulfillment errors", "Maintain vendor SLAs"],
        "decision_style": "Standardize before scaling volume",
        "escalation_rules": ["Escalate SLA breaches", "Escalate missing vendor contracts"],
    },
    "Finance Manager": {
        "personality": ["conservative", "cashflow obsessed"],
        "communication_style": "Numbers-first, scenario ranges, runway warnings early",
        "goals": ["Protect runway", "Validate unit economics", "Flag burn anomalies"],
        "decision_style": "No scale spend until LTV:CAC > 3 on cohort",
        "escalation_rules": ["Escalate if runway < 6 months", "Escalate if gross margin compresses > 5pts"],
    },
    "Founder": {
        "personality": ["decisive", "risk-aware", "vision-holder"],
        "communication_style": "Concise decisions, asks for options not essays",
        "goals": ["Maintain strategic focus", "Unblock team", "Prepare investor narrative"],
        "decision_style": "Decide with 70% information; revisit weekly",
        "escalation_rules": ["Self-escalate to board/investors only for existential risks"],
    },
    "Product Manager": {
        "personality": ["user-centric", "prioritization-focused"],
        "communication_style": "Problem statements, acceptance criteria, trade-off tables",
        "goals": ["Ship MVP scope", "Reduce scope creep", "Align roadmap to ICP pain"],
        "decision_style": "RICE scoring for backlog",
        "escalation_rules": ["Escalate scope conflicts to Founder"],
    },
}

_DEFAULT_PROFILE: dict[str, Any] = {
    "personality": ["professional", "collaborative"],
    "communication_style": "Clear and actionable",
    "goals": ["Support team objectives"],
    "decision_style": "Consult lead before major changes",
    "escalation_rules": ["Escalate blockers to COO"],
}


def get_tool_access(role: str) -> list[str]:
    return list(TOOL_MATRIX.get(role, ["task_board"]))


def build_employee_profile(employee: dict[str, Any]) -> dict[str, Any]:
    """Merge SQL employee row with role personality profile."""
    role = str(employee.get("role") or "Team Member")
    spec = ROLE_PROFILES.get(role, _DEFAULT_PROFILE)
    neg = get_negotiation_style(role)
    return {
        "employee_id": employee.get("employee_id"),
        "name": employee.get("name"),
        "role": role,
        "department": employee.get("department") or "",
        "authority_level": int(employee.get("authority_level") or 5),
        "personality": list(spec.get("personality") or []),
        "communication_style": spec.get("communication_style", ""),
        "goals": list(spec.get("goals") or []),
        "tool_access": get_tool_access(role),
        "decision_style": spec.get("decision_style", ""),
        "escalation_rules": list(spec.get("escalation_rules") or []),
        "negotiation_style": neg.get("style"),
        "negotiation_traits": list(neg.get("traits") or []),
        "risk_tolerance": neg.get("risk_tolerance"),
        "skills": list(employee.get("skills") or []),
        "performance_score": employee.get("performance_score"),
        "is_active": employee.get("is_active", True),
    }


def profiles_for_team(employees: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [build_employee_profile(e) for e in employees if e.get("is_active", True)]
