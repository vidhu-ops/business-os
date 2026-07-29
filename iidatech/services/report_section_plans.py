"""Section plans for the primary Perplexity + Claude market research report."""
from __future__ import annotations

from typing import Any

from iidatech.services.perplexity_report_engine import SECTION_CATALOG

SIMPLE_SECTION_COUNTS: tuple[int, ...] = (3, 8, 16, 25)

SIMPLE_SECTION_PRESETS: dict[int, list[int]] = {
    3: [1, 3, 7],
    8: [1, 2, 3, 7, 10, 12, 17, 22],
    16: list(range(1, 17)),
    25: list(range(1, 26)),
}

_CATALOG_BY_ID: dict[int, dict[str, Any]] = {int(s["id"]): s for s in SECTION_CATALOG}

def normalize_section_count(section_count: int | None) -> int:
    try:
        count = int(section_count or 3)
    except (TypeError, ValueError):
        return 3
    return count if count in SIMPLE_SECTION_PRESETS else 3

def section_plan(section_count: int) -> list[dict[str, Any]]:
    count = normalize_section_count(section_count)
    return [_CATALOG_BY_ID[i] for i in SIMPLE_SECTION_PRESETS[count] if i in _CATALOG_BY_ID]

def section_titles(section_count: int) -> list[str]:
    return [str(s.get("title") or "") for s in section_plan(section_count)]

def format_section_outline(plan: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for idx, sec in enumerate(plan, 1):
        title = str(sec.get("title") or f"Section {idx}")
        subs = ", ".join(str(s) for s in (sec.get("sub") or [])[:6])
        lines.append(f"{idx}. ## {title}" + (f" — cover: {subs}" if subs else ""))
    return "\n".join(lines)

def sonnet_max_tokens(section_count: int) -> int:
    return {3: 4500, 8: 6500, 16: 9000, 25: 12000}[normalize_section_count(section_count)]

def budget_for_sections(section_count: int, *, base_budget: float) -> float:
    """Scale budget cap slightly for longer reports (same harvest passes, larger write-up)."""
    extra = {3: 0.0, 8: 0.05, 16: 0.15, 25: 0.30}
    return round(base_budget + extra.get(normalize_section_count(section_count), 0.0), 2)
