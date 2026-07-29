"""Provider-agnostic narrative LLM client for IIDATECH."""
from __future__ import annotations

import os
from typing import Any

DEFAULT_OPENAI_MODEL = os.getenv("OPENAI_MODEL", os.getenv("IIDATECH_OPENAI_MODEL", "gpt-4o-mini"))

_last_failure: str | None = None


def llm_last_error() -> str | None:
    """Human-readable reason for the most recent generate_narrative() failure."""
    return _last_failure


def llm_generation_failed() -> bool:
    """True when the last generate_narrative() call returned None."""
    return _last_failure is not None


def _set_failure(reason: str) -> None:
    global _last_failure
    _last_failure = reason[:240] if reason else "unknown_error"


def _clear_failure() -> None:
    global _last_failure
    _last_failure = None


def llm_provider() -> str:
    raw = (os.getenv("LLM_PROVIDER") or os.getenv("IIDATECH_LLM_PROVIDER") or "openai").strip().lower()
    if raw in {"openai", "anthropic"}:
        return raw
    return "openai"


def _openai_narrative(prompt: str, system: str) -> str:
    from openai import OpenAI

    try:
        from iidatech.execution.session_api_keys import get_key

        key = get_key("openai") or get_key("anthropic") or get_key("deepseek") or get_key("groq") or get_key("openrouter") or get_key("custom")
    except ImportError:
        key = ""
    if not key:
        key = (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY") or "").strip()
    if not key:
        raise RuntimeError("OPENAI_API_KEY not configured")

    model = DEFAULT_OPENAI_MODEL
    client = OpenAI(api_key=key)
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        max_tokens=900,
    )
    text = str((response.choices or [None])[0].message.content or "").strip()  # type: ignore[union-attr]
    if not text:
        raise RuntimeError(f"{model}: empty response")
    return text


def _anthropic_narrative(prompt: str, system: str) -> str:
    raise NotImplementedError("Claude support not yet wired — see llm_client.py")


def generate_narrative(prompt: str, system: str = "") -> str | None:
    """Generate analyst narrative text. Returns None on failure; check llm_generation_failed()."""
    _clear_failure()
    provider = llm_provider()
    try:
        if provider == "openai":
            return _openai_narrative(prompt, system)
        if provider == "anthropic":
            return _anthropic_narrative(prompt, system)
        _set_failure(f"unsupported_provider:{provider}")
        return None
    except NotImplementedError as exc:
        _set_failure(str(exc))
        return None
    except Exception as exc:
        _set_failure(str(exc))
        return None
