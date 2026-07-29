"""Pass 2 - LLM strategist audit and repair for business blueprint."""
from __future__ import annotations

import json
import os
import re
from typing import Any

from iidatech.llm.usage_policy import (
    assert_premium_call_allowed,
    compress_text_for_llm,
    get_stage_token_budget,
)
from iidatech.services.llm_client import generate_narrative, llm_last_error


def _parse_json(text: str) -> dict:
    cleaned = str(text or "").strip()
    cleaned = re.sub(r"^\s*```(?:json)?\s*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\s*```\s*$", "", cleaned)
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start >= 0 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def _apply_repairs(blueprint: dict, repaired: dict) -> dict:
    out = dict(blueprint)
    for key in (
        "market_opportunity",
        "competitor_map",
        "business_model",
        "unit_economics",
        "funding_plan",
        "go_to_market",
        "hiring_plan",
    ):
        if key in repaired and repaired[key]:
            out[key] = repaired[key]
    return out


def run_business_strategist_audit(
    blueprint: dict,
    *,
    idea: str = "",
    industry: str = "",
    geography: str = "",
) -> tuple[dict, dict]:
    """Return (repaired_blueprint, audit_payload)."""
    blueprint = blueprint if isinstance(blueprint, dict) else {}
    if not (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")):
        return blueprint, {
            "score_10": None,
            "skipped": True,
            "reason": "No OpenAI API key configured",
            "fatal_flaws": ["Strategist audit skipped — no API key"],
            "recommendations": [],
            "repaired_sections": {},
        }
    try:
        assert_premium_call_allowed("business_strategist")
    except ValueError as exc:
        return blueprint, {
            "score_10": None,
            "skipped": True,
            "reason": str(exc),
            "fatal_flaws": [str(exc)],
            "recommendations": [],
            "repaired_sections": {},
        }

    compact = compress_text_for_llm(
        json.dumps(
            {
                k: blueprint.get(k)
                for k in (
                    "market_opportunity",
                    "competitor_map",
                    "business_model",
                    "unit_economics",
                    "funding_plan",
                    "go_to_market",
                    "hiring_plan",
                )
            },
            ensure_ascii=False,
            default=str,
        ),
        stage="business_strategist",
    )
    prompt = (
        "You are a VC + McKinsey operator + growth strategist auditing a deterministic business blueprint. "
        "Be brutal. Penalize unsupported numbers, weak moat, bad GTM, and template assumptions. "
        "Return JSON only with keys: score_10, thesis_strength, moat_score, financial_risk, fatal_flaws, "
        "recommendations, repaired_sections. "
        "repaired_sections may only patch: market_opportunity, competitor_map, business_model, unit_economics, "
        "funding_plan, go_to_market, hiring_plan. "
        "Never invent TAM without evidence — mark insufficient evidence instead.\n\n"
        f"Topic: {idea}\nIndustry: {industry}\nGeography: {geography}\n\nBlueprint:\n{compact}"
    )
    system = "Return strict JSON only. Act as funding-grade strategist."
    text = generate_narrative(prompt, system)
    if not text:
        err = llm_last_error() or "LLM request failed"
        return blueprint, {
            "score_10": None,
            "llm_ok": False,
            "error": err,
            "fatal_flaws": [err],
            "recommendations": [],
            "repaired_sections": {},
        }
    try:
        audit = _parse_json(text)
        audit["model"] = os.getenv("OPENAI_MODEL", os.getenv("IIDATECH_OPENAI_MODEL", "gpt-4o-mini"))
        audit["llm_ok"] = True
        repaired = _apply_repairs(blueprint, audit.get("repaired_sections") or {})
        repaired["strategist_audit"] = audit
        return repaired, audit
    except Exception as exc:
        err = str(exc)[:240]
        return blueprint, {
            "score_10": None,
            "llm_ok": False,
            "error": err,
            "fatal_flaws": [err],
            "recommendations": [],
            "repaired_sections": {},
        }
