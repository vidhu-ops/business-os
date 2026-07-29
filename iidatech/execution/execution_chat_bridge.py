"""Bridge Execution tab employee chat to real tool runtime (Employee OS 2 harness)."""
from __future__ import annotations

import hashlib
import os
import re
from typing import Any

_ACTION_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(find|get|scrape|search|pull|export)\b.*\bleads?\b", re.I), "sales_lead"),
    (re.compile(r"\b(outreach|cold email|sequence|email)\b", re.I), "sales_lead"),
    (re.compile(r"\b(competitor|pricing|market research|evidence)\b", re.I), "research_analyst"),
    (re.compile(r"\b(campaign|ad copy|linkedin|instagram|google ads)\b", re.I), "growth_marketer"),
    (re.compile(r"\b(sop|workflow|checklist|handoff)\b", re.I), "ops_manager"),
    (re.compile(r"\b(brief|storyboard|creative|landing)\b", re.I), "creative_producer"),
]


def execution_report_id(idea: str, geography: str) -> str:
    raw = f"{idea}|{geography}".strip().lower()
    return f"os2_{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


def map_employee_to_harness(employee: dict[str, Any]) -> str:
    blob = " ".join(
        str(employee.get(k) or "") for k in ("title", "department", "role", "mission", "id", "name")
    ).lower()
    if any(x in blob for x in ("sales", "crm", "pipeline", "outbound")):
        return "sales_lead"
    if any(x in blob for x in ("research", "analyst", "intel", "evidence")):
        return "research_analyst"
    if any(x in blob for x in ("growth", "marketing", "campaign", "content")):
        return "growth_marketer"
    if any(x in blob for x in ("creative", "design", "brand")):
        return "creative_producer"
    if any(x in blob for x in ("ops", "operations", "sop")):
        return "ops_manager"
    return "growth_marketer"


def detect_harness_for_message(message: str, employee: dict[str, Any]) -> str | None:
    msg = str(message or "").strip()
    if not msg:
        return None
    for pattern, harness_id in _ACTION_PATTERNS:
        if pattern.search(msg):
            return harness_id
    if len(msg) > 12 and any(v in msg.lower() for v in ("create", "build", "draft", "write", "generate")):
        return map_employee_to_harness(employee)
    return None


def _api_keys_from_env() -> dict[str, str]:
    keys: dict[str, str] = {}
    pplx = (os.getenv("PERPLEXITY_API_KEY") or os.getenv("PPLX_API_KEY") or "").strip()
    if pplx:
        keys["perplexity"] = pplx
    oai = (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY") or "").strip()
    if oai:
        keys["openai"] = oai
    ant = (os.getenv("ANTHROPIC_API_KEY") or "").strip()
    if ant:
        keys["anthropic"] = ant
    return keys


def _api_keys_from_streamlit() -> dict[str, str]:
    """Pick up keys pasted in Employee OS 2 (same Streamlit session)."""
    try:
        import streamlit as st
        from iidatech.execution.session_api_keys import SUPPORTED_PROVIDERS, normalize_keys

        main_key = str(st.session_state.get("os2_api_key") or "").strip()
        provider = str(st.session_state.get("os2_api_provider") or "auto").strip().lower()
        extra: dict[str, str] = {}
        for prov in SUPPORTED_PROVIDERS:
            val = str(st.session_state.get(f"os2_extra_key_{prov}") or "").strip()
            if val:
                extra[prov] = val
        return normalize_keys(main_key, provider=provider, extra=extra)
    except Exception:
        return {}


def _merged_api_keys(api_keys: dict[str, str] | None = None) -> dict[str, str]:
    from iidatech.execution.os2_api_keys import merge_api_keys

    return merge_api_keys(api_keys)


def try_real_execution_reply(
    employee: dict[str, Any],
    user_message: str,
    *,
    idea: str,
    industry: str,
    geography: str,
    plan: dict | None = None,
    report_context: dict | None = None,
    api_keys: dict[str, str] | None = None,
) -> str | None:
    """Run real tools when message is actionable. Returns None to fall back to templates."""
    harness_id = detect_harness_for_message(user_message, employee)
    if not harness_id:
        return None

    keys = _merged_api_keys(api_keys)
    if not keys:
        return (
            f"I understood your request as **real execution work** ({harness_id.replace('_', ' ')}), "
            "but no API keys are configured.\n\n"
            "**To do actual work (leads, live search, files):**\n"
            "1. Add `PERPLEXITY_API_KEY` to your `.env` for leads/search, **or**\n"
            "2. Open **Employee OS 2** and paste keys in the API keys panel (same session).\n\n"
            "Without keys I can only produce internal draft memos."
        )

    from iidatech.execution.employee_os2_harness import execute_harness_job

    report_id = execution_report_id(idea, geography)
    ctx: dict[str, Any] = dict(report_context or {})
    ctx.setdefault("topic", idea)
    ctx.setdefault("industry", industry)
    ctx.setdefault("geography", geography)
    ctx.setdefault("country", geography)
    if isinstance(plan, dict) and plan:
        ctx.setdefault("business_plan", plan)

    result = execute_harness_job(
        harness_id,
        user_message,
        report_id=report_id,
        api_keys=keys,
        report_context=ctx,
    )
    reply = str(result.get("reply") or "").strip()
    if not reply:
        return None
    prefix = f"**{employee.get('name', 'Employee')}** — ran real tools (not a template memo).\n\n"
    if not result.get("success"):
        return prefix + reply
    arts = result.get("artifacts") or []
    if arts:
        reply += "\n\n**Files:**\n" + "\n".join(f"- `{a}`" for a in arts)
    return prefix + reply
