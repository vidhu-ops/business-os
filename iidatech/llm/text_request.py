"""Provider-agnostic text completion for report synthesis (OpenAI via llm_client)."""
from __future__ import annotations

import os

from iidatech.services.llm_client import DEFAULT_OPENAI_MODEL, generate_narrative, llm_last_error, llm_provider

API_TIMEOUT = float(os.getenv("IIDATECH_API_TIMEOUT", "75"))


def _env_key(*names: str) -> str:
    for name in names:
        value = (os.getenv(name) or "").strip()
        if value:
            return value
    return ""


def preferred_llm_provider() -> str:
    return llm_provider()


def cloud_llm_configured() -> bool:
    return bool(_env_key("OPENAI_API_KEY", "OPENAI_KEY"))


def _resolve_openai_model(candidates: list[str] | None) -> str:
    joined = " ".join(candidates or []).lower()
    analyst = os.getenv("IIDATECH_OPENAI_ANALYST_MODEL", "gpt-4o")
    verifier = os.getenv("IIDATECH_OPENAI_VERIFIER_MODEL", analyst)
    if any(token in joined for token in ("sonnet", "opus", "analyst", "boardroom")):
        return analyst
    if "verifier" in joined:
        return verifier
    return DEFAULT_OPENAI_MODEL


def llm_text_request(
    prompt: str,
    system: str,
    candidates: list[str] | None = None,
    max_tokens: int = 4096,
    temperature: float = 0.1,
    *,
    anthropic_fallback_models: list[str] | None = None,
) -> tuple[str, str]:
    """Route synthesis to the configured cloud provider (OpenAI implemented)."""
    del max_tokens, temperature, anthropic_fallback_models  # narrative client uses fixed safe defaults

    provider = llm_provider()
    if provider == "anthropic":
        raise RuntimeError("Claude support not yet wired — set LLM_PROVIDER=openai")

    if not cloud_llm_configured():
        raise RuntimeError("No cloud LLM key configured (set OPENAI_API_KEY).")

    model = _resolve_openai_model(candidates)
    prior_model = os.environ.get("OPENAI_MODEL")
    prior_iidatech = os.environ.get("IIDATECH_OPENAI_MODEL")
    try:
        os.environ["OPENAI_MODEL"] = model
        os.environ["IIDATECH_OPENAI_MODEL"] = model
        text = generate_narrative(prompt, system)
    finally:
        if prior_model is None:
            os.environ.pop("OPENAI_MODEL", None)
        else:
            os.environ["OPENAI_MODEL"] = prior_model
        if prior_iidatech is None:
            os.environ.pop("IIDATECH_OPENAI_MODEL", None)
        else:
            os.environ["IIDATECH_OPENAI_MODEL"] = prior_iidatech

    if not text:
        raise RuntimeError(llm_last_error() or "LLM request failed")
    return text, f"openai:{model}"


def cloud_synthesis_label() -> str:
    provider = llm_provider()
    if provider == "openai":
        return "OpenAI"
    if provider == "anthropic":
        return "Claude (deferred)"
    return "Cloud LLM"


def format_llm_route(route: str) -> str:
    raw = str(route or "").strip()
    if not raw:
        return cloud_synthesis_label()
    label, _, model = raw.partition(":")
    if label.lower() == "openai":
        return f"OpenAI ({model or DEFAULT_OPENAI_MODEL})"
    if label.lower() == "anthropic":
        return f"Claude ({model or 'deferred'})"
    return raw
