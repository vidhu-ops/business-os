"""Employee OS 2 — session-key-aware LLM calls (OpenAI-compatible + Anthropic)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import requests

from iidatech.execution.session_api_keys import get_config, get_key


def _openai_compatible_chat(*, api_key: str, base_url: str, model: str, prompt: str, system: str) -> str:
    messages: list[dict[str, str]] = []
    if system.strip():
        messages.append({"role": "system", "content": system.strip()})
    messages.append({"role": "user", "content": prompt})
    resp = requests.post(
        base_url.rstrip("/") + "/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 1800},
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    text = str((data.get("choices") or [{}])[0].get("message", {}).get("content") or "").strip()
    if not text:
        raise RuntimeError(f"{model}: empty response")
    return text


def _anthropic_chat(*, api_key: str, model: str, prompt: str, system: str) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "max_tokens": 1800,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system.strip():
        payload["system"] = system.strip()
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    parts = data.get("content") or []
    text = "".join(str(p.get("text") or "") for p in parts if isinstance(p, dict))
    if not text.strip():
        raise RuntimeError(f"{model}: empty response")
    return text.strip()


def _gemini_chat(*, api_key: str, model: str, prompt: str, system: str) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    parts: list[dict[str, Any]] = []
    if system.strip():
        parts.append({"text": system.strip()})
    parts.append({"text": prompt})
    resp = requests.post(
        url,
        params={"key": api_key},
        headers={"Content-Type": "application/json"},
        json={"contents": [{"role": "user", "parts": parts}]},
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates") or []
    text = ""
    if candidates:
        content = candidates[0].get("content") or {}
        text = "".join(str(p.get("text") or "") for p in (content.get("parts") or []) if isinstance(p, dict))
    if not text.strip():
        raise RuntimeError(f"{model}: empty response")
    return text.strip()


def _cohere_chat(*, api_key: str, model: str, prompt: str, system: str) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "message": prompt,
        "temperature": 0.3,
        "max_tokens": 1800,
    }
    if system.strip():
        payload["preamble"] = system.strip()
    resp = requests.post(
        "https://api.cohere.com/v2/chat",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    text = str(data.get("text") or "").strip()
    if not text:
        raise RuntimeError(f"{model}: empty response")
    return text


_OPENAI_COMPAT_PROVIDERS: list[tuple[str, str, str]] = [
    ("openai", "https://api.openai.com/v1", "gpt-4o-mini"),
    ("deepseek", "https://api.deepseek.com/v1", "deepseek-chat"),
    ("groq", "https://api.groq.com/openai/v1", "llama-3.3-70b-versatile"),
    ("openrouter", "https://openrouter.ai/api/v1", "openai/gpt-4o-mini"),
    ("mistral", "https://api.mistral.ai/v1", "mistral-small-latest"),
    ("together", "https://api.together.xyz/v1", "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"),
    ("xai", "https://api.x.ai/v1", "grok-2-latest"),
]


def generate_with_session_keys(prompt: str, system: str = "") -> tuple[str | None, str]:
    """Try session keys in priority order. Returns (text, provider_used)."""
    for prov, base, model in _OPENAI_COMPAT_PROVIDERS:
        key = get_key(prov)
        if not key:
            continue
        try:
            return _openai_compatible_chat(api_key=key, base_url=base, model=model, prompt=prompt, system=system), prov
        except Exception:
            continue

    key = get_key("google")
    if key:
        model = get_config("google_model") or "gemini-2.0-flash"
        try:
            return _gemini_chat(api_key=key, model=model, prompt=prompt, system=system), "google"
        except Exception:
            pass

    key = get_key("cohere")
    if key:
        model = get_config("cohere_model") or "command-r-plus-08-2024"
        try:
            return _cohere_chat(api_key=key, model=model, prompt=prompt, system=system), "cohere"
        except Exception:
            pass

    key = get_key("anthropic")
    if key:
        model = get_config("anthropic_model") or "claude-3-5-haiku-latest"
        try:
            return _anthropic_chat(api_key=key, model=model, prompt=prompt, system=system), "anthropic"
        except Exception:
            pass

    key = get_key("custom")
    if key:
        base = get_config("custom_base_url") or "https://api.openai.com/v1"
        model = get_config("custom_model") or "gpt-4o-mini"
        try:
            return _openai_compatible_chat(api_key=key, base_url=base, model=model, prompt=prompt, system=system), "custom"
        except Exception:
            pass

    return None, ""


def enrich_markdown_artifact(path: str, *, user_request: str, report_context: dict[str, Any] | None = None) -> bool:
    p = Path(path)
    if not p.is_file() or p.suffix.lower() not in {".md", ".txt"}:
        return False
    topic = str((report_context or {}).get("topic") or "the business")
    prompt = (
        f"User task: {user_request}\nTopic: {topic}\n\n"
        f"Rewrite the following draft into a polished, client-ready deliverable. "
        f"Keep facts; do not invent statistics.\n\n---\n{p.read_text(encoding='utf-8', errors='ignore')[:6000]}"
    )
    text, used = generate_with_session_keys(prompt, system="You produce concise, actionable business deliverables.")
    if not text or not used:
        return False
    p.write_text(text.strip() + "\n", encoding="utf-8")
    return True
