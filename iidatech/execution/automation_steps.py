"""Pick-and-choose automation step catalog (deterministic, no LLM routing)."""
from __future__ import annotations

import hashlib
from typing import Any

AUTOMATION_STEP_CATALOG: list[dict[str, Any]] = [
    {"id": "research_competitors", "label": "Research competitors and pricing", "role": "Research Analyst", "harness_id": "research_analyst", "connector": "perplexity", "needs_approval": False, "prompt": "Search competitors and pricing for our topic. Log evidence gaps."},
    {"id": "find_leads", "label": "Find qualified leads (CSV)", "role": "Sales Lead", "harness_id": "sales_lead", "connector": "perplexity", "needs_approval": False, "prompt": "Find 20 qualified leads with company, contact, and email where available. Export CSV."},
    {"id": "draft_outreach", "label": "Draft outreach sequence", "role": "Sales Lead", "harness_id": "sales_lead", "connector": None, "needs_approval": False, "prompt": "Write a 3-step cold outreach sequence with opt-out language."},
    {"id": "campaign_draft", "label": "Draft LinkedIn + email campaign", "role": "Growth Marketer", "harness_id": "growth_marketer", "connector": None, "needs_approval": False, "prompt": "Draft a LinkedIn post and email campaign with 3 ad copy variants."},
    {"id": "load_gmail_inbox", "label": "Load recent Gmail inbox (read)", "role": "Sales Lead", "harness_id": None, "connector": "gmail", "needs_approval": False, "action": "gmail_read"},
    {"id": "load_hubspot_contacts", "label": "Load HubSpot contacts", "role": "Sales Lead", "harness_id": None, "connector": "hubspot", "needs_approval": False, "action": "hubspot_read"},
    {"id": "post_linkedin", "label": "Post to LinkedIn", "role": "Growth Marketer", "harness_id": None, "connector": "linkedin", "needs_approval": True, "action": "linkedin_post"},
    {"id": "send_email", "label": "Send email to first lead", "role": "Sales Lead", "harness_id": None, "connector": "gmail", "needs_approval": True, "action": "gmail_send"},
    {"id": "sync_hubspot", "label": "Sync leads to HubSpot CRM", "role": "Sales Lead", "harness_id": None, "connector": "hubspot", "needs_approval": True, "action": "hubspot_sync"},
    {"id": "ops_sop", "label": "Write weekly execution SOP", "role": "Operations Manager", "harness_id": "ops_manager", "connector": None, "needs_approval": False, "prompt": "Write an SOP checklist for weekly sales and marketing execution."},
    {"id": "founder_brief", "label": "Taylor (COO) — founder brief and decisions", "role": "COO", "harness_id": None, "connector": None, "needs_approval": False, "action": "founder_brief"},
]

STEP_BY_ID = {s["id"]: s for s in AUTOMATION_STEP_CATALOG}


def automation_report_id(idea: str, geography: str) -> str:
    raw = f"{str(idea or '').strip()}|{str(geography or '').strip()}|automation"
    return f"auto_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


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