"""Merge OS2 session keys with .env for harness execution."""
from __future__ import annotations

import os
from typing import Any

try:
    from iidatech.env_bootstrap import ensure_env_loaded

    ensure_env_loaded()
except Exception:
    pass

def api_keys_from_env() -> dict[str, str]:
    keys: dict[str, str] = {}
    mapping = {
        "perplexity": ("PERPLEXITY_API_KEY", "PPLX_API_KEY"),
        "openai": ("OPENAI_API_KEY", "OPENAI_KEY"),
        "anthropic": ("ANTHROPIC_API_KEY",),
        "deepseek": ("DEEPSEEK_API_KEY",),
        "groq": ("GROQ_API_KEY",),
    }
    for provider, env_names in mapping.items():
        for name in env_names:
            val = (os.getenv(name) or "").strip()
            if val:
                keys[provider] = val
                break
    return keys


def merge_api_keys(session_keys: dict[str, str] | None = None) -> dict[str, str]:
    merged = api_keys_from_env()
    if session_keys:
        merged.update({k: str(v or "").strip() for k, v in session_keys.items() if str(v or "").strip()})
    return merged


def collect_os2_api_keys(st: Any) -> tuple[dict[str, str], dict[str, str]]:
    """Return (merged keys, api_config) from Streamlit session + .env."""
    from iidatech.execution.session_api_keys import SUPPORTED_PROVIDERS, normalize_keys

    main_key = str(st.session_state.get("os2_api_key") or "").strip()
    provider = str(st.session_state.get("os2_api_provider") or "auto").strip().lower()
    extra: dict[str, str] = {}
    for prov in SUPPORTED_PROVIDERS:
        val = str(st.session_state.get(f"os2_extra_key_{prov}") or "").strip()
        if val:
            extra[prov] = val
    keys = merge_api_keys(normalize_keys(main_key, provider=provider, extra=extra))
    config: dict[str, str] = {}
    custom_base = str(st.session_state.get("os2_custom_base_url") or "").strip()
    custom_model = str(st.session_state.get("os2_custom_model") or "").strip()
    if custom_base:
        config["custom_base_url"] = custom_base
    if custom_model:
        config["custom_model"] = custom_model
    return keys, config
