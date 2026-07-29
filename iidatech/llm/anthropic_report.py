"""Perplexity-routed Claude passes for report financial + analyst commentary."""
from __future__ import annotations

import os
from typing import Any

from iidatech.evidence_bank.perplexity_client import (
    call_perplexity_agent_json,
    perplexity_enabled,
    report_analyst_model,
    report_financial_model,
)


def anthropic_api_key() -> str:
    """Legacy name — financial/analyst passes bill through Perplexity, not direct Anthropic."""
    return ""


def anthropic_enabled() -> bool:
    return perplexity_enabled()


def financial_model() -> str:
    return report_financial_model()


def analyst_model() -> str:
    return report_analyst_model()


def call_anthropic_json(
    *,
    prompt: str,
    model: str,
    system: str = "",
    max_tokens: int = 4096,
    timeout: int = 180,
) -> dict[str, Any]:
    """Route Opus/Sonnet through Perplexity Agent API (anthropic/* model IDs)."""
    if not perplexity_enabled():
        return {"error": "PERPLEXITY_API_KEY not configured", "enabled": False}
    full_prompt = prompt.strip()
    if system.strip():
        full_prompt = f"{system.strip()}\n\n{full_prompt}"
    return call_perplexity_agent_json(
        full_prompt,
        model=model,
        max_output_tokens=max_tokens,
        timeout=timeout,
    )
