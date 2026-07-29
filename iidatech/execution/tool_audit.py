"""Tool audit matrix: REAL / PARTIAL / SIMULATED / BLOCKED."""

from __future__ import annotations

from typing import Any

from iidatech.integrations.registry import connector_status, is_configured

Classification = str  # REAL | PARTIAL | SIMULATED | BLOCKED

TOOL_MATRIX: dict[str, dict[str, Any]] = {
    "serp_search": {
        "classification": "PARTIAL",
        "department": "research",
        "connectors": ["serpapi", "tavily", "exa"],
        "notes": "Live search when API keys set; verified report fallback otherwise",
    },
    "sql_memory_query": {
        "classification": "REAL",
        "department": "research",
        "connectors": ["local_crm"],
        "notes": "Reads execution SQL memory and verified KPI history",
    },
    "competitor_lookup": {
        "classification": "REAL",
        "department": "research",
        "connectors": [],
        "notes": "Verified competitor rows from report v3 only",
    },
    "evidence_writer": {
        "classification": "REAL",
        "department": "research",
        "connectors": [],
        "notes": "Writes evidence log JSONL artifact",
    },
    "lead_scraper": {
        "classification": "PARTIAL",
        "department": "growth",
        "connectors": ["serpapi", "tavily", "exa", "local_crm", "runtime_crm"],
        "notes": "Live search to CSV + pipeline_leads when search configured",
    },
    "campaign_builder": {
        "classification": "PARTIAL",
        "department": "growth",
        "connectors": [],
        "notes": "Writes campaign JSON artifact; launch blocked without approval",
    },
    "ad_copy_generator": {
        "classification": "PARTIAL",
        "department": "growth",
        "connectors": [],
        "notes": "Writes ad copy markdown artifact",
    },
    "outreach_writer": {
        "classification": "PARTIAL",
        "department": "growth",
        "connectors": ["gmail_smtp", "resend", "sendgrid", "slack", "whatsapp"],
        "notes": "Writes sequence file; optional Slack notify when configured",
    },
    "crm_update": {
        "classification": "REAL",
        "department": "sales",
        "connectors": ["nocodb", "runtime_crm", "local_crm"],
        "notes": "NocoDB, runtime CRM, or local pipeline_leads",
    },
    "lead_scoring": {
        "classification": "REAL",
        "department": "sales",
        "connectors": [],
        "notes": "Scores CSV from lead_scraper output",
    },
    "proposal_builder": {
        "classification": "REAL",
        "department": "sales",
        "connectors": [],
        "notes": "Writes proposal markdown (approval gated)",
    },
    "meeting_scheduler": {
        "classification": "PARTIAL",
        "department": "sales",
        "connectors": ["calcom", "google_calendar"],
        "notes": "Task + Cal.com / Google Calendar / ICS artifact",
    },
    "workflow_builder": {
        "classification": "PARTIAL",
        "department": "ops",
        "connectors": ["n8n"],
        "notes": "Writes workflow JSON; optional n8n webhook",
    },
    "task_scheduler": {
        "classification": "REAL",
        "department": "ops",
        "connectors": [],
        "notes": "Creates real tasks in execution SQL",
    },
    "sop_writer": {
        "classification": "REAL",
        "department": "ops",
        "connectors": [],
        "notes": "Writes SOP markdown artifact",
    },
    "runway_calculator": {
        "classification": "REAL",
        "department": "finance",
        "connectors": [],
        "notes": "Requires founder-verified financials",
    },
    "pnl_model": {
        "classification": "PARTIAL",
        "department": "finance",
        "connectors": [],
        "notes": "Writes PnL JSON artifact when approved",
    },
    "invoice_generator": {
        "classification": "REAL",
        "department": "finance",
        "connectors": ["stripe", "razorpay"],
        "notes": "PDF invoice + optional payment link",
    },
}

# Connectors that promote PARTIAL -> REAL (exclude always-on local stores).
_PROMOTION_CONNECTORS: dict[str, list[str]] = {
    "serp_search": ["serpapi", "tavily", "exa"],
    "lead_scraper": ["serpapi", "tavily", "exa"],
    "outreach_writer": ["gmail_smtp", "resend", "sendgrid", "slack", "whatsapp"],
    "meeting_scheduler": ["calcom", "google_calendar"],
    "workflow_builder": ["n8n"],
    "campaign_builder": ["n8n"],
    "invoice_generator": ["stripe", "razorpay"],
}


def classify_tool(tool_name: str) -> Classification:
    row = TOOL_MATRIX.get(tool_name) or {}
    base = str(row.get("classification") or "BLOCKED")
    if base == "BLOCKED":
        return base
    connectors = _PROMOTION_CONNECTORS.get(tool_name) or row.get("connectors") or []
    if not connectors:
        return base
    status = connector_status()
    any_live = any(status.get(c, {}).get("configured") for c in connectors)
    if base == "PARTIAL" and any_live:
        return "REAL"
    if base == "PARTIAL" and not any_live:
        return "PARTIAL"
    return base


def audit_report() -> dict[str, Any]:
    rows = []
    counts = {"REAL": 0, "PARTIAL": 0, "SIMULATED": 0, "BLOCKED": 0}
    for name, meta in TOOL_MATRIX.items():
        effective = classify_tool(name)
        counts[effective] = counts.get(effective, 0) + 1
        rows.append({
            "tool_name": name,
            "classification": effective,
            "base_classification": meta.get("classification"),
            "department": meta.get("department"),
            "connectors": meta.get("connectors"),
            "connector_status": {c: is_configured(c) for c in (meta.get("connectors") or [])},
            "notes": meta.get("notes"),
        })
    total = len(rows)
    realism = round((counts["REAL"] * 1.0 + counts["PARTIAL"] * 0.6) / max(total, 1) * 10, 1)
    return {"tools": rows, "counts": counts, "realism_score": realism, "connector_status": connector_status()}


def realism_score() -> float:
    return float(audit_report().get("realism_score") or 0)