"""Extract API usage and estimate USD cost per provider/model."""
from __future__ import annotations

from typing import Any

_RATE_TABLE: dict[str, tuple[float, float]] = {
    "sonar": (0.25, 2.50),
    "sonar-pro": (3.0, 15.0),
    "perplexity/sonar": (0.25, 2.50),
    "perplexity/glm-5.2": (0.50, 3.00),
    "claude-opus-4-20250514": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "anthropic/claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-sonnet-4-5": (2.0, 10.0),
    "anthropic/claude-sonnet-4-5": (2.0, 10.0),
    "claude-3-5-sonnet-latest": (2.0, 10.0),
}


def _rate(model: str) -> tuple[float, float]:
    m = str(model or "").lower()
    for key, rates in _RATE_TABLE.items():
        if key in m:
            return rates
    if "glm" in m:
        return (0.50, 3.00)
    if "opus" in m:
        return (5.0, 25.0)
    if "sonnet" in m:
        return (2.0, 10.0)
    if "sonar" in m:
        return (0.25, 2.50)
    return (0.0, 0.0)


def estimate_token_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    in_m, out_m = _rate(model)
    return (int(input_tokens or 0) * in_m + int(output_tokens or 0) * out_m) / 1_000_000.0


def perplexity_usage_row(usage: Any, *, model: str, phase: str) -> dict[str, Any]:
    u = usage if isinstance(usage, dict) else {}
    prompt = int(u.get("prompt_tokens") or u.get("input_tokens") or 0)
    completion = int(u.get("completion_tokens") or u.get("output_tokens") or 0)
    total = int(u.get("total_tokens") or (prompt + completion))
    cost_block = u.get("cost") if isinstance(u.get("cost"), dict) else {}
    cost_usd = float(cost_block.get("total_cost") or 0.0)
    if not cost_usd and total:
        cost_usd = estimate_token_cost_usd(model, prompt, completion)
    return {
        "phase": phase,
        "provider": "perplexity",
        "model": model,
        "input_tokens": prompt,
        "output_tokens": completion,
        "total_tokens": total,
        "cost_usd": round(cost_usd, 6),
    }


def anthropic_usage_row(usage: Any, *, model: str, phase: str) -> dict[str, Any]:
    row = perplexity_usage_row(usage, model=model, phase=phase)
    row["provider"] = "perplexity"
    return row


def sum_ledger(rows: list[dict[str, Any]], *, successful_only: bool = True) -> dict[str, Any]:
    usable = rows
    if successful_only:
        usable = [r for r in rows if not r.get("error") and int(r.get("total_tokens") or 0) > 0]
    in_t = sum(int(r.get("input_tokens") or 0) for r in usable)
    out_t = sum(int(r.get("output_tokens") or 0) for r in usable)
    cost = sum(float(r.get("cost_usd") or 0.0) for r in usable)
    return {
        "calls": len(usable),
        "input_tokens": in_t,
        "output_tokens": out_t,
        "total_tokens": in_t + out_t,
        "cost_usd": round(cost, 6),
    }


def project_phase_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    return round(estimate_token_cost_usd(model, input_tokens, output_tokens), 6)
