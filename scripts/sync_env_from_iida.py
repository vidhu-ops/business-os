"""Copy research/API keys from sibling iida/.env into this repo's .env."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IIDA_ENV = ROOT.parent / "iida" / ".env"
LOCAL_ENV = ROOT / ".env"

KEYS = (
    "PERPLEXITY_API_KEY",
    "PPLX_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "DEEPSEEK_API_KEY",
    "GROQ_API_KEY",
    "PERPLEXITY_REPORT_MODEL",
    "PERPLEXITY_FINANCIAL_MODEL",
    "PERPLEXITY_ANALYST_MODEL",
    "PERPLEXITY_SEARCH_MODEL",
)


def load_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    raw = path.read_bytes()
    for enc in ("utf-8-sig", "utf-16", "utf-16-le", "latin-1"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    else:
        return {}
    out: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip().lstrip("\ufeff")
        value = value.strip().strip('"').strip("'")
        if key:
            out[key] = value
    return out


def main() -> None:
    src = load_env(IIDA_ENV)
    if not src:
        print("No iida/.env found; skipping sync")
        return
    lines = LOCAL_ENV.read_text(encoding="utf-8", errors="ignore").splitlines() if LOCAL_ENV.is_file() else []
    existing = {
        ln.split("=", 1)[0].strip()
        for ln in lines
        if "=" in ln and not ln.strip().startswith("#")
    }
    updated: list[str] = []
    for key in KEYS:
        value = src.get(key, "").strip()
        if value and key not in existing:
            lines.append(f"{key}={value}")
            existing.add(key)
            updated.append(key)
    if updated:
        LOCAL_ENV.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    print("synced:", ", ".join(updated) if updated else "already present")
    merged = load_env(LOCAL_ENV)
    print(
        "perplexity_configured:",
        bool(merged.get("PERPLEXITY_API_KEY") or merged.get("PPLX_API_KEY") or src.get("PERPLEXITY_API_KEY") or src.get("PPLX_API_KEY")),
    )


if __name__ == "__main__":
    main()
