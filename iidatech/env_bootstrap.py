"""Load repo .env into os.environ once (shared by OAuth, Perplexity, harness keys)."""
from __future__ import annotations

import os
from pathlib import Path

_LOADED = False
_ROOT = Path(__file__).resolve().parents[1]


def ensure_env_loaded() -> None:
    global _LOADED
    if _LOADED:
        return
    candidates = (
        _ROOT / ".env",
        _ROOT.parent / "iida" / ".env",
        _ROOT / "research_llm_production" / ".env",
    )
    for path in candidates:
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip().lstrip("\ufeff")
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
        except OSError:
            continue
    _LOADED = True