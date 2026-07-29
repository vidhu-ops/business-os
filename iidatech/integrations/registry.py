"""Connector readiness for Employee OS."""

from __future__ import annotations

import os
from typing import Any


def _env(*names: str) -> str:
    for name in names:
        value = os.getenv(name, "").strip()
        if value:
            return value
    return ""


def is_configured(name: str) -> bool:
    return bool((connector_status().get(name) or {}).get("configured"))


def connector_status() -> dict[str, dict[str, Any]]:
    try:
        from backend_integrations import configured_status as backend_status
        base = dict(backend_status())
    except ImportError:
        base = {}

    extra = {
        "gmail_smtp": {
            "configured": bool(_env("GMAIL_SMTP_USER", "GMAIL_USER") and _env("GMAIL_SMTP_PASSWORD", "GMAIL_APP_PASSWORD")),
            "required": ["GMAIL_SMTP_USER", "GMAIL_SMTP_PASSWORD"],
            "purpose": "outbound email via SMTP",
        },
        "serpapi": {
            "configured": bool(_env("SERPAPI_KEY", "SERP_API_KEY")),
            "required": ["SERPAPI_KEY"],
            "purpose": "live web search",
        },
        "tavily": {
            "configured": bool(_env("TAVILY_API_KEY", "TAVILY_KEY")),
            "required": ["TAVILY_API_KEY"],
            "purpose": "research search API",
        },
        "exa": {
            "configured": bool(_env("EXA_API_KEY", "EXA_KEY")),
            "required": ["EXA_API_KEY"],
            "purpose": "semantic search API",
        },
        "whatsapp": {
            "configured": bool(
                _env("TWILIO_ACCOUNT_SID")
                and _env("TWILIO_AUTH_TOKEN")
                and _env("TWILIO_WHATSAPP_FROM", "TWILIO_WHATSAPP_NUMBER")
            ),
            "required": ["TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_WHATSAPP_FROM"],
            "purpose": "WhatsApp via Twilio",
        },
        "calcom": {
            "configured": bool(_env("CALCOM_API_KEY") and _env("CALCOM_EVENT_TYPE_ID")),
            "required": ["CALCOM_API_KEY", "CALCOM_EVENT_TYPE_ID"],
            "purpose": "Cal.com bookings",
        },
        "google_calendar": {
            "configured": bool(_env("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON", "GOOGLE_APPLICATION_CREDENTIALS")),
            "required": ["GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON"],
            "purpose": "Google Calendar events",
        },
        "razorpay": {
            "configured": bool(_env("RAZORPAY_KEY_ID") and _env("RAZORPAY_KEY_SECRET")),
            "required": ["RAZORPAY_KEY_ID", "RAZORPAY_KEY_SECRET"],
            "purpose": "payment links",
        },
        "local_crm": {"configured": True, "required": [], "purpose": "pipeline_leads SQL store"},
        "runtime_crm": {
            "configured": bool(_env("IIDATECH_RUNTIME_DB")),
            "required": ["IIDATECH_RUNTIME_DB"],
            "purpose": "runtime crm_contacts",
        },
    }
    base.update(extra)
    return base