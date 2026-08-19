from __future__ import annotations

from typing import Any

# Baseline: Quick Research tool price / credits used in app.
CREDIT_BASELINE_INR = 200

# Section counts must match iidatech.services.report_section_plans.SIMPLE_SECTION_COUNTS
RESEARCH_TIERS: dict[int, dict[str, Any]] = {
    3: {
        "tier_id": "quick",
        "label": "Quick Research",
        "sections_label": "3–5 sections",
        "credits": 5,
        "tool_inr": 999,
        "service_inr": 2000,
        "user_stage": "validate",
    },
    8: {
        "tier_id": "standard",
        "label": "Standard Research",
        "sections_label": "6–10 sections",
        "credits": 8,
        "tool_inr": 1999,
        "service_inr": 3500,
        "user_stage": "build",
    },
    16: {
        "tier_id": "professional",
        "label": "Professional Research",
        "sections_label": "10–15 sections",
        "credits": 15,
        "tool_inr": 3500,
        "service_inr": 5000,
        "user_stage": "scale",
    },
    25: {
        "tier_id": "enterprise",
        "label": "Enterprise Research",
        "sections_label": "20+ sections",
        "credits": 20,
        "tool_inr": 4500,
        "service_inr": 6000,
        "user_stage": "scale",
    },
}

PLAN_DEFINITIONS: dict[str, dict[str, Any]] = {
    # Backend plan id "starter" = marketing Free tier (credit-based).
    "starter": {
        "id": "starter",
        "display_name": "Free",
        "stage": "validate",
        "user_type": "solo_founder_exploring",
        "billing_model": "credits",
        "price_label": "Free",
        "period": "",
        "amount_paise": 0,
        "signup_credits": 30,
        "unlimited_usage": False,
        "billable": False,
        "checkout_aliases": [],
        "perks": [
            "30 credits on signup",
            "Pay per research depth, plan, Employee OS, and automation",
            "Reference hub and demo workspace",
            "Community support",
        ],
        "entitlements": {
            "unlimited_research": False,
            "unlimited_plans": False,
            "unlimited_automation": False,
            "employee_os": True,
            "oauth_integrations": True,
            "branded_exports": True,
            "priority_support": False,
            "dedicated_onboarding": False,
        },
    },
    # Backend plan id "growth" = marketing Starter tool subscription (₹4,999/mo).
    "growth": {
        "id": "growth",
        "display_name": "Starter",
        "stage": "self_serve",
        "user_type": "early_stage_startup",
        "billing_model": "subscription",
        "price_label": "₹4,999",
        "period": "/ month",
        "amount_paise": 499_900,
        "signup_credits": None,
        "unlimited_usage": True,
        "billable": True,
        "checkout_aliases": ["starter", "starter_tool"],
        "perks": [
            "Unlimited research and business plans in app",
            "Employee OS with AI agents",
            "OAuth integrations",
            "Branded PDF exports",
            "Priority email support",
        ],
        "entitlements": {
            "unlimited_research": True,
            "unlimited_plans": True,
            "unlimited_automation": False,
            "employee_os": True,
            "oauth_integrations": True,
            "branded_exports": True,
            "priority_support": True,
            "dedicated_onboarding": False,
        },
    },
    "growth_plus": {
        "id": "growth_plus",
        "display_name": "Growth",
        "stage": "scale_team",
        "user_type": "scaling_team",
        "billing_model": "subscription",
        "price_label": "₹8,999",
        "period": "/ month",
        "amount_paise": 899_900,
        "signup_credits": None,
        "unlimited_usage": True,
        "billable": False,
        "checkout_aliases": ["growth_team"],
        "perks": [
            "Everything in Starter",
            "Advanced research modules",
            "AI employee and automation builders",
            "Dedicated onboarding",
            "Priority support",
        ],
        "entitlements": {
            "unlimited_research": True,
            "unlimited_plans": True,
            "unlimited_automation": True,
            "employee_os": True,
            "oauth_integrations": True,
            "branded_exports": True,
            "priority_support": True,
            "dedicated_onboarding": True,
        },
    },
    "business": {
        "id": "business",
        "display_name": "Business",
        "stage": "growth",
        "user_type": "growing_business",
        "billing_model": "subscription",
        "price_label": "₹12,999",
        "period": "/ month",
        "amount_paise": 1_299_900,
        "signup_credits": None,
        "unlimited_usage": True,
        "billable": False,
        "checkout_aliases": [],
        "perks": [
            "Full platform access",
            "Automation templates and workflows",
            "Team-ready workspace features",
            "Priority support",
            "Custom onboarding",
        ],
        "entitlements": {
            "unlimited_research": True,
            "unlimited_plans": True,
            "unlimited_automation": True,
            "employee_os": True,
            "oauth_integrations": True,
            "branded_exports": True,
            "priority_support": True,
            "dedicated_onboarding": True,
        },
    },
    "enterprise": {
        "id": "enterprise",
        "display_name": "Enterprise",
        "stage": "enterprise",
        "user_type": "large_organization",
        "billing_model": "custom",
        "price_label": "Custom",
        "period": "",
        "amount_paise": 0,
        "signup_credits": None,
        "unlimited_usage": True,
        "billable": False,
        "checkout_aliases": [],
        "perks": [
            "Complete platform access",
            "Custom integrations",
            "Dedicated account manager",
            "SLA-backed support",
        ],
        "entitlements": {
            "unlimited_research": True,
            "unlimited_plans": True,
            "unlimited_automation": True,
            "employee_os": True,
            "oauth_integrations": True,
            "branded_exports": True,
            "priority_support": True,
            "dedicated_onboarding": True,
        },
    },
}

CREDIT_ACTIONS: dict[str, dict[str, Any]] = {
    "research": {
        "label": "Market research report",
        "credits": 5,
        "variable_by": "research_section_count",
        "tool_inr_from": 999,
        "tool_inr_to": 4500,
    },
    "business_plan": {
        "label": "Business plan generation",
        "credits": 5,
        "tool_inr_from": 1999,
        "tool_inr_to": 4999,
        "plan_tiers": {
            "startup": {"label": "Startup plan", "service_inr": 1999, "credits": 5},
            "growth": {"label": "Growth plan", "service_inr": 2999, "credits": 8},
            "investor": {"label": "Investor plan", "tool_inr": 4999, "service_inr": 4999, "credits": 10},
            "enterprise": {"label": "Enterprise strategic", "service_inr": 6999, "credits": 15},
        },
    },
    "employee_work": {
        "label": "Employee OS — one task / agent work unit",
        "credits": 1,
        "tool_inr_from": 200,
    },
    "mentor": {
        "label": "Mentor conversation turn",
        "credits": 1,
        "tool_inr_from": 200,
    },
    "department_week": {
        "label": "Employee OS — one department (legacy weekly pass)",
        "credits": 10,
        "tool_inr_from": 2000,
    },
    "full_office_week": {
        "label": "Employee OS — full office (legacy weekly pass)",
        "credits": 50,
        "tool_inr_from": 25000,
    },
    "automation_build": {
        "label": "Automation workflow build",
        "credits": 8,
        "tool_inr_from": 3500,
    },
    "automation_run": {
        "label": "Automation step run",
        "credits": 8,
        "tool_inr_from": 3500,
    },
}

CREDIT_PACKS: list[dict[str, Any]] = [
    {
        "id": "pack_50",
        "credits": 50,
        "amount_paise": 999_900,
        "price_label": "₹9,999",
        "per_credit_inr": 200,
        "blurb": "~25 Quick research runs or 6 Standard runs",
    },
    {
        "id": "pack_100",
        "credits": 100,
        "amount_paise": 1_799_900,
        "price_label": "₹17,999",
        "per_credit_inr": 180,
        "blurb": "Best for teams iterating weekly",
    },
    {
        "id": "pack_250",
        "credits": 250,
        "amount_paise": 3_999_900,
        "price_label": "₹39,999",
        "per_credit_inr": 160,
        "blurb": "Volume pack for agencies and operators",
    },
]

SERVICE_PACKAGES: list[dict[str, Any]] = [
    {
        "id": "startup_package",
        "name": "Startup Package",
        "service_inr": 24999,
        "price_label": "₹24,999",
        "user_type": "early_stage_startup",
        "stage": "launch",
        "includes": [
            "Quick Research (3–5 sections)",
            "Startup Business Plan",
            "1 AI Employee",
            "1 Automation workflow",
            "IIDATECH team delivery",
        ],
    },
    {
        "id": "scale_package",
        "name": "Scale Package",
        "service_inr": 74999,
        "price_label": "₹74,999",
        "user_type": "growing_business",
        "stage": "scale",
        "includes": [
            "Standard Research (6–10 sections)",
            "Growth Business Plan",
            "Department AI pack (5 employees)",
            "Department automation",
            "Business OS setup",
        ],
    },
]

A_LA_CARTE: list[dict[str, Any]] = [
    {
        "category": "Research",
        "items": [
            {"name": "Quick (3–5 sections)", "tool_inr": 999, "service_inr": 2000, "credits": 5},
            {"name": "Standard (6–10 sections)", "tool_inr": 1999, "service_inr": 3500, "credits": 8},
            {"name": "Professional (10–15 sections)", "tool_inr": 3500, "service_inr": 5000, "credits": 15},
            {"name": "Enterprise (20+ sections)", "tool_inr": 4500, "service_inr": 6000, "credits": 20},
        ],
    },
    {
        "category": "Business plans",
        "items": [
            {"name": "Startup plan", "tool_inr": None, "service_inr": 1999, "credits": 5},
            {"name": "Growth plan", "tool_inr": None, "service_inr": 2999, "credits": 8},
            {"name": "Investor plan", "tool_inr": 4999, "service_inr": 4999, "credits": 10},
            {"name": "Enterprise strategic", "tool_inr": None, "service_inr": 6999, "credits": 15},
        ],
    },
    {
        "category": "AI employees",
        "items": [
            {"name": "Single employee", "tool_inr": 2000, "service_inr": 3000, "credits": 10},
            {"name": "Department pack (5)", "tool_inr": 8000, "service_inr": 12000, "credits": 40},
            {"name": "Complete workforce (20–30)", "tool_inr": 25000, "service_inr": 32000, "credits": 125},
        ],
    },
    {
        "category": "Automations",
        "items": [
            {"name": "Single workflow", "tool_inr": 3500, "service_inr": 4500, "credits": 8},
            {"name": "Department suite", "tool_inr": 18000, "service_inr": 22000, "credits": 40},
            {"name": "Company-wide", "tool_inr": 50000, "service_inr": 70000, "credits": 100},
        ],
    },
]

USER_STAGES: list[dict[str, str]] = [
    {"id": "validate", "label": "Validate", "description": "Solo founders testing ideas with credits"},
    {"id": "self_serve", "label": "Self-serve", "description": "Early startups subscribing for unlimited core tools"},
    {"id": "scale_team", "label": "Scale", "description": "Teams adding AI employees and automation"},
    {"id": "growth", "label": "Growth", "description": "Businesses on full-suite subscriptions"},
    {"id": "enterprise", "label": "Enterprise", "description": "Custom deployments with SLA"},
    {"id": "launch", "label": "Launch (service)", "description": "Done-for-you startup package"},
]


def normalize_plan_id(plan_id: str | None) -> str:
    raw = str(plan_id or "starter").strip().lower()
    for pid, plan in PLAN_DEFINITIONS.items():
        aliases = plan.get("checkout_aliases") or []
        if raw == pid or raw in aliases:
            return pid
    return raw if raw in PLAN_DEFINITIONS else "starter"


def resolve_checkout_plan_id(plan_id: str) -> str:
    """Map marketing checkout ids (e.g. starter) to stored plan ids (e.g. growth)."""
    normalized = normalize_plan_id(plan_id)
    if normalized in PLAN_DEFINITIONS and PLAN_DEFINITIONS[normalized].get("billable"):
        return normalized
    raw = str(plan_id or "").strip().lower()
    for pid, plan in PLAN_DEFINITIONS.items():
        if raw in (plan.get("checkout_aliases") or []) and plan.get("billable"):
            return pid
    return raw


def get_plan(plan_id: str | None) -> dict[str, Any]:
    return dict(PLAN_DEFINITIONS.get(normalize_plan_id(plan_id), PLAN_DEFINITIONS["starter"]))


def is_unlimited_plan(plan_id: str | None) -> bool:
    return bool(get_plan(plan_id).get("unlimited_usage"))


def signup_credits_for_plan(plan_id: str | None = None) -> int:
    plan = get_plan(plan_id or "starter")
    value = plan.get("signup_credits")
    return int(value) if value is not None else 0


def research_credit_cost(section_count: int) -> int:
    tier = RESEARCH_TIERS.get(int(section_count))
    if tier:
        return int(tier["credits"])
    return int(CREDIT_ACTIONS["research"]["credits"])


def credit_cost_for_action(action: str, *, section_count: int | None = None) -> int:
    if action == "research":
        if section_count is not None:
            return research_credit_cost(section_count)
        return int(CREDIT_ACTIONS["research"]["credits"])
    spec = CREDIT_ACTIONS.get(action)
    if not spec:
        raise ValueError(f"Unknown credit action: {action}")
    return int(spec["credits"])


def credit_costs_map() -> dict[str, int]:
    return {key: int(val["credits"]) for key, val in CREDIT_ACTIONS.items()}


def credit_labels_map() -> dict[str, str]:
    return {key: str(val["label"]) for key, val in CREDIT_ACTIONS.items()}


def list_subscription_plans(*, public_only: bool = True) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for plan in PLAN_DEFINITIONS.values():
        if public_only and plan["id"] not in {"starter", "growth", "growth_plus", "business", "enterprise"}:
            continue
        rows.append(public_plan_row(plan))
    return rows


def public_plan_row(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": plan["id"],
        "display_name": plan["display_name"],
        "stage": plan["stage"],
        "user_type": plan["user_type"],
        "billing_model": plan["billing_model"],
        "price_label": plan["price_label"],
        "period": plan.get("period", ""),
        "amount_paise": plan.get("amount_paise", 0),
        "signup_credits": plan.get("signup_credits"),
        "unlimited_usage": plan.get("unlimited_usage", False),
        "billable": plan.get("billable", False),
        "perks": list(plan.get("perks") or []),
        "entitlements": dict(plan.get("entitlements") or {}),
        "checkout_href": f"/checkout?plan={plan['id']}" if plan.get("billable") else None,
    }


def list_billable_plans() -> list[dict[str, Any]]:
    return [public_plan_row(p) for p in PLAN_DEFINITIONS.values() if p.get("billable")]


def list_checkout_plans() -> list[dict[str, Any]]:
    """Plans shown on checkout — includes free tier for comparison."""
    starter = public_plan_row(PLAN_DEFINITIONS["starter"])
    return [starter, *list_billable_plans()]


def full_catalog() -> dict[str, Any]:
    return {
        "credit_baseline_inr": CREDIT_BASELINE_INR,
        "user_stages": USER_STAGES,
        "plans": list_subscription_plans(),
        "credit_actions": {
            key: {
                "action": key,
                "label": val["label"],
                "credits": val["credits"],
                **{k: v for k, v in val.items() if k not in {"label", "credits"}},
            }
            for key, val in CREDIT_ACTIONS.items()
        },
        "research_tiers": [
            {"section_count": count, **tier} for count, tier in sorted(RESEARCH_TIERS.items())
        ],
        "credit_packs": CREDIT_PACKS,
        "service_packages": SERVICE_PACKAGES,
        "a_la_carte": A_LA_CARTE,
        "signup_credits": signup_credits_for_plan("starter"),
    }
