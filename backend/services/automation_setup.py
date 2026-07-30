from __future__ import annotations

from typing import Any

from iidatech.execution.automation_steps import STEP_BY_ID
from iidatech.execution.os2_api_keys import merge_api_keys
from iidatech.integrations.oauth_store import is_connected


def automation_setup_requirements(step_ids: list[str], report_id: str, workspace_id: str | None = None) -> list[dict[str, Any]]:
    keys = merge_api_keys()
    if workspace_id:
        from backend.services.os2_service import merged_keys_for_workspace

        keys = {**keys, **merged_keys_for_workspace(workspace_id)}
    from iidatech.execution.session_api_keys import has_any_llm_key

    rows: list[dict[str, Any]] = [
        {
            "need": "AI model (OpenAI / Anthropic / Perplexity)",
            "connector": "llm",
            "ok": has_any_llm_key(keys),
            "required": "Add API keys under Employee OS 뿯↽ Integrations, or set server env vars",
        }
    ]
    connectors: set[str] = set()
    for sid in step_ids:
        row = STEP_BY_ID.get(sid)
        if not row:
            continue
        connector = str(row.get("connector") or "").strip()
        if connector:
            connectors.add(connector)
    labels = {
        "perplexity": "Perplexity API key (research & lead steps)",
        "gmail": "Gmail — OAuth connect or SMTP app password",
        "linkedin": "LinkedIn — OAuth connect or access token + author URN",
        "hubspot": "HubSpot — OAuth connect or private app token",
    }
    for connector in sorted(connectors):
        if connector == "perplexity":
            ok = bool(keys.get("perplexity"))
        else:
            ok = is_connected(report_id, connector)
        rows.append(
            {
                "need": connector.replace("_", " ").title(),
                "connector": connector,
                "ok": ok,
                "required": labels.get(connector, f"Connect {connector} before running this step"),
            }
        )
    return rows
