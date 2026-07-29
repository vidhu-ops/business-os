"""Session-scoped API key overrides for Employee OS 2 (never persisted)."""

from __future__ import annotations



import contextvars

import re

from contextlib import contextmanager

from typing import Iterator



_KEYS: contextvars.ContextVar[dict[str, str]] = contextvars.ContextVar("os2_api_keys", default={})

_CONFIG: contextvars.ContextVar[dict[str, str]] = contextvars.ContextVar("os2_api_config", default={})



SUPPORTED_PROVIDERS: tuple[str, ...] = (

    "openai",

    "anthropic",

    "perplexity",

    "deepseek",

    "groq",

    "openrouter",

    "google",

    "mistral",

    "together",

    "xai",

    "cohere",

    "custom",

)



LLM_PROVIDERS: tuple[str, ...] = tuple(p for p in SUPPORTED_PROVIDERS if p not in {"perplexity"})



_PROVIDER_LABELS: dict[str, str] = {

    "openai": "OpenAI",

    "anthropic": "Anthropic (Claude)",

    "perplexity": "Perplexity",

    "deepseek": "DeepSeek",

    "groq": "Groq",

    "openrouter": "OpenRouter",

    "google": "Google (Gemini)",

    "mistral": "Mistral",

    "together": "Together AI",

    "xai": "xAI (Grok)",

    "cohere": "Cohere",

    "custom": "Custom (OpenAI-compatible)",

}



_PROVIDER_PORTAL_URLS: dict[str, str] = {

    "openai": "https://platform.openai.com/api-keys",

    "anthropic": "https://console.anthropic.com/settings/keys",

    "perplexity": "https://www.perplexity.ai/settings/api",

    "deepseek": "https://platform.deepseek.com/api_keys",

    "groq": "https://console.groq.com/keys",

    "openrouter": "https://openrouter.ai/keys",

    "google": "https://aistudio.google.com/apikey",

    "mistral": "https://console.mistral.ai/api-keys/",

    "together": "https://api.together.xyz/settings/api-keys",

    "xai": "https://console.x.ai/",

    "cohere": "https://dashboard.cohere.com/api-keys",

    "custom": "https://platform.openai.com/docs/api-reference",

}





def provider_label(provider: str) -> str:

    return _PROVIDER_LABELS.get(str(provider or "").strip().lower(), str(provider or "API"))





def provider_portal_url(provider: str) -> str:

    return str(_PROVIDER_PORTAL_URLS.get(str(provider or "").strip().lower()) or "").strip()





def detect_provider(api_key: str) -> str:

    k = str(api_key or "").strip()

    if not k:

        return ""

    low = k.lower()

    if low.startswith("sk-ant-"):

        return "anthropic"

    if low.startswith("pplx-"):

        return "perplexity"

    if low.startswith("gsk_"):

        return "groq"

    if low.startswith("sk-or-"):

        return "openrouter"

    if low.startswith("sk-"):

        return "openai"

    if low.startswith("aiza") or low.startswith("AIza") or low.startswith("ya29."):

        return "google"

    if low.startswith("mistral-") or low.startswith("mistral_"):

        return "mistral"

    if low.startswith("together-"):

        return "together"

    if low.startswith("xai-"):

        return "xai"

    if low.startswith("cohere-"):

        return "cohere"

    if re.match(r"^[a-z0-9_\-]{12,}$", low):

        return "custom"

    return "custom"





def normalize_keys(

    api_key: str = "",

    *,

    provider: str = "auto",

    extra: dict[str, str] | None = None,

) -> dict[str, str]:

    out: dict[str, str] = {}

    for name, val in (extra or {}).items():

        v = str(val or "").strip()

        if v:

            out[str(name).strip().lower()] = v

    main = str(api_key or "").strip()

    if not main:

        return out

    prov_choice = str(provider or "auto").strip().lower()

    if prov_choice in {"", "auto"}:

        prov = detect_provider(main) or "custom"

    else:

        prov = prov_choice

    out[prov] = main

    return out





def get_key(provider: str) -> str:

    return str(_KEYS.get().get(str(provider or "").strip().lower()) or "").strip()





def get_config(name: str) -> str:

    return str(_CONFIG.get().get(str(name or "").strip().lower()) or "").strip()





def get_perplexity_override() -> str:

    return get_key("perplexity")





def has_any_llm_key(keys: dict[str, str] | None = None) -> bool:

    source = keys if keys is not None else _KEYS.get()

    return any(str(source.get(p) or "").strip() for p in LLM_PROVIDERS)





def active_providers(keys: dict[str, str] | None = None) -> list[str]:

    source = keys if keys is not None else _KEYS.get()

    ordered: list[str] = []

    seen: set[str] = set()

    for p in SUPPORTED_PROVIDERS:

        if str(source.get(p) or "").strip() and p not in seen:

            ordered.append(p)

            seen.add(p)

    for p, v in source.items():

        if str(v or "").strip() and p not in seen:

            ordered.append(p)

            seen.add(p)

    return ordered





@contextmanager

def session_api_keys(

    keys: dict[str, str],

    *,

    config: dict[str, str] | None = None,

) -> Iterator[None]:

    clean = {str(k).strip().lower(): str(v).strip() for k, v in (keys or {}).items() if str(v or "").strip()}

    cfg = {str(k).strip().lower(): str(v).strip() for k, v in (config or {}).items() if str(v or "").strip()}

    key_token = _KEYS.set(clean)

    cfg_token = _CONFIG.set(cfg)

    try:

        yield

    finally:

        _CONFIG.reset(cfg_token)

        _KEYS.reset(key_token)





@contextmanager

def perplexity_key_override(api_key: str) -> Iterator[None]:

    with session_api_keys({"perplexity": str(api_key or "").strip()}):

        yield

