"""Pick-and-choose automation step catalog (deterministic, no LLM routing)."""
from __future__ import annotations

import hashlib
from typing import Any

AUTOMATION_STEP_CATALOG: list[dict[str, Any]] = [
    {"id": "research_competitors", "label": "Research competitors and pricing", "role": "Research Analyst", "harness_id": "research_analyst", "connector": "perplexity", "needs_approval": False, "prompt": "Search competitors and pricing for our topic. Log evidence gaps."},
    {"id": "find_leads", "label": "Find qualified leads (up to 90)", "role": "Sales Lead", "harness_id": "sales_lead", "connector": "perplexity", "needs_approval": False, "prompt": "Find 90 qualified leads with company, contact, and email where available. Export CSV. Batch searches if needed — do not invent emails."},
    {"id": "draft_outreach", "label": "Draft outreach sequence (generic)", "role": "Sales Lead", "harness_id": "sales_lead", "connector": None, "needs_approval": False, "prompt": "Write a 3-step cold outreach sequence with opt-out language."},
    {"id": "draft_outreach_per_lead", "label": "Personalize email for each lead", "role": "Sales Lead", "harness_id": None, "connector": None, "needs_approval": False, "action": "outreach_personalize"},
    {"id": "campaign_draft", "label": "Draft LinkedIn + email campaign", "role": "Growth Marketer", "harness_id": "growth_marketer", "connector": None, "needs_approval": False, "prompt": "Draft a LinkedIn post and email campaign with 3 ad copy variants."},
    {"id": "load_gmail_inbox", "label": "Load recent Gmail inbox (read)", "role": "Sales Lead", "harness_id": None, "connector": "gmail", "needs_approval": False, "action": "gmail_read"},
    {"id": "load_hubspot_contacts", "label": "Load HubSpot contacts", "role": "Sales Lead", "harness_id": None, "connector": "hubspot", "needs_approval": False, "action": "hubspot_read"},
    {"id": "post_linkedin", "label": "Post to LinkedIn", "role": "Growth Marketer", "harness_id": None, "connector": "linkedin", "needs_approval": True, "action": "linkedin_post"},
    {"id": "send_email", "label": "Send email to first lead", "role": "Sales Lead", "harness_id": None, "connector": "gmail", "needs_approval": True, "action": "gmail_send"},
    {"id": "send_email_queue", "label": "Send personalized emails (queued)", "role": "Sales Lead", "harness_id": None, "connector": "gmail", "needs_approval": True, "action": "gmail_send_queue"},
    {"id": "sync_hubspot", "label": "Sync leads to HubSpot CRM", "role": "Sales Lead", "harness_id": None, "connector": "hubspot", "needs_approval": True, "action": "hubspot_sync"},
    {"id": "ops_sop", "label": "Write weekly execution SOP", "role": "Operations Manager", "harness_id": "ops_manager", "connector": None, "needs_approval": False, "prompt": "Write an SOP checklist for weekly sales and marketing execution."},
    {"id": "founder_brief", "label": "Taylor (COO) — founder brief and decisions", "role": "COO", "harness_id": None, "connector": None, "needs_approval": False, "action": "founder_brief"},
]

STEP_BY_ID = {s["id"]: s for s in AUTOMATION_STEP_CATALOG}

# One-click executable daily outreach flow
DAILY_OUTREACH_STEP_IDS = ["find_leads", "draft_outreach_per_lead", "send_email_queue"]


def automation_report_id(idea: str, geography: str) -> str:
    """Stable workspace-aligned id so Automation shares OAuth, queues, and Taylor with Employee OS.

    Historically used an ``auto_`` prefix which split queues from ``os2_*`` Employee OS state.
    Keep the same hash of idea|geography (without the legacy '|automation' suffix) so Integrations
    and run-next operate on one report_id per project.
    """
    topic = str(idea or "").strip()
    geo = str(geography or "Global").strip()
    raw = f"{topic}|{geo}".strip().lower()
    return f"os2_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


def build_spec_from_steps(step_ids: list[str], *, idea: str, industry: str, geography: str, name: str = "Custom automation") -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    for i, sid in enumerate(step_ids, start=1):
        row = STEP_BY_ID.get(sid)
        if not row:
            continue
        steps.append({**row, "seq": i, "status": "queued"})
    return {
        "name": name,
        "kind": "custom_builder",
        "request": f"Custom flow: {', '.join(s['label'] for s in steps)}",
        "picked_steps": steps,
        "steps": [f"{s['seq']}. {s['label']}" + (" [approval]" if s.get('needs_approval') else "") for s in steps],
        "apps": sorted({str(s.get('connector')) for s in steps if s.get('connector')}),
        "business": {"idea": idea, "industry": industry, "geography": geography},
    }


def build_daily_outreach_spec(*, idea: str, industry: str, geography: str, target: int = 90) -> dict[str, Any]:
    spec = build_spec_from_steps(
        DAILY_OUTREACH_STEP_IDS,
        idea=idea,
        industry=industry,
        geography=geography,
        name=f"Daily leads + personalized email ({target})",
    )
    # Stamp target onto find_leads prompt for harness routing
    for step in spec.get("picked_steps") or []:
        if step.get("id") == "find_leads":
            step["prompt"] = (
                f"Find {max(5, min(90, target))} qualified leads with company, contact, and email where available. "
                "Export CSV. Do not invent emails."
            )
            step["target_count"] = max(5, min(90, target))
    return spec