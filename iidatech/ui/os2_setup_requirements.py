"""What users need to connect for agents, research, and automations."""
from __future__ import annotations

from typing import Any

from iidatech.execution.session_api_keys import provider_label, provider_portal_url
from iidatech.integrations.oauth_store import connection_label, is_connected


def _llm_ready(keys: dict[str, str]) -> bool:
    return any(k for k in keys if k not in {"perplexity"})


def render_setup_requirements(
    st: Any,
    *,
    report_id: str,
    keys: dict[str, str],
    expanded: bool | None = None,
) -> None:
    if expanded is None:
        expanded = not (_llm_ready(keys) or keys.get("perplexity"))

    rows = [
        {
            "need": "Run agents & write copy",
            "get": "OpenAI, Anthropic, or another LLM API key",
            "where": provider_portal_url("openai") or "https://platform.openai.com/api-keys",
            "ok": _llm_ready(keys),
            "required": "Yes — at least one LLM",
        },
        {
            "need": "Live research & lead search",
            "get": "Perplexity API key (sonar)",
            "where": provider_portal_url("perplexity") or "https://www.perplexity.ai/settings/api",
            "ok": bool(keys.get("perplexity")),
            "required": "Recommended for Sam (research)",
        },
        {
            "need": "Send emails from agents",
            "get": "Gmail OAuth or SMTP app password",
            "where": "https://console.cloud.google.com/apis/credentials",
            "ok": is_connected(report_id, "gmail"),
            "required": "Only if tasks send email",
        },
        {
            "need": "Post to LinkedIn",
            "get": "LinkedIn Developer app + OAuth token + author URN",
            "where": "https://www.linkedin.com/developers/",
            "ok": is_connected(report_id, "linkedin"),
            "required": "Only if tasks post to LinkedIn",
        },
        {
            "need": "Update CRM / deals",
            "get": "HubSpot private app token or OAuth",
            "where": "https://developers.hubspot.com/",
            "ok": is_connected(report_id, "hubspot"),
            "required": "Only if tasks touch HubSpot",
        },
        {
            "need": "Business plan for task queue",
            "get": "Plan from Business Builder or upload JSON/Markdown",
            "where": "Turn idea into business plan workflow",
            "ok": True,
            "required": "Yes — Taylor builds the checklist from your plan",
        },
    ]

    with st.expander("What you need to get started", expanded=expanded):
        st.caption(
            "Agents can draft work with just an LLM key. External actions (email, LinkedIn, CRM) "
            "pause until you connect the matching account in **Integrations**."
        )
        for row in rows:
            icon = "✅" if row["ok"] else "⬜"
            st.markdown(f"{icon} **{row['need']}** — {row['required']}")
            st.markdown(f"   - Get: {row['get']}")
            st.markdown(f"   - Where: [{row['where'].split('/')[-1] or 'link'}]({row['where']})")
        if keys:
            st.success("Connected LLM keys: " + ", ".join(provider_label(k) for k in keys.keys()))
        else:
            st.warning("No LLM API key yet — add one below or in `.env` (`OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, …).")
        oauth_bits = []
        for pid, label in [("gmail", "Gmail"), ("linkedin", "LinkedIn"), ("hubspot", "HubSpot")]:
            oauth_bits.append(f"{label}: {connection_label(report_id, pid)}")
        st.caption("OAuth status — " + " | ".join(oauth_bits))
