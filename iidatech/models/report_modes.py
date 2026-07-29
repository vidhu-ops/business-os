"""Report section taxonomy and runtime modes (Lite / Standard / Institutional)."""

from __future__ import annotations

from typing import Any

# All 33 legacy section ids from app.SECTIONS
SECTION_CLASSIFICATION: dict[int, str] = {
    1: "mandatory",
    2: "mandatory",
    3: "mandatory",
    4: "optional",
    5: "optional",
    6: "mandatory",
    7: "optional",
    8: "optional",
    9: "optional",
    10: "optional",
    11: "optional",
    12: "optional",
    13: "optional",
    14: "optional",
    15: "optional",
    16: "optional",
    17: "mandatory",
    18: "optional",
    19: "institutional_only",
    20: "institutional_only",
    21: "optional",
    22: "mandatory",
    23: "optional",
    24: "optional",
    25: "optional",
    26: "optional",
    27: "optional",
    28: "optional",
    29: "institutional_only",
    30: "institutional_only",
    31: "institutional_only",
    32: "institutional_only",
    33: "institutional_only",
}

LITE_SECTION_IDS: tuple[int, ...] = (1, 2, 3, 6, 17, 22)
STANDARD_SECTION_IDS: tuple[int, ...] = (1, 2, 3, 6, 7, 17, 18, 21, 22, 26, 30)
INSTITUTIONAL_SECTION_IDS: tuple[int, ...] = (
    1, 2, 3, 6, 7, 17, 18, 19, 21, 22, 23, 29, 30, 31, 32, 33,
)

MODE_RUNTIME_TARGETS_SEC: dict[str, int] = {
    "lite": 240,
    "standard": 480,
    "institutional": 900,
}


def normalize_report_mode(mode: str | None) -> str:
    m = str(mode or "standard").strip().lower()
    if m in {"lite", "light", "quick"}:
        return "lite"
    if m in {"institutional", "full", "funding"}:
        return "institutional"
    return "standard"


def section_ids_for_mode(mode: str | None) -> list[int]:
    key = normalize_report_mode(mode)
    if key == "lite":
        return list(LITE_SECTION_IDS)
    if key == "institutional":
        return list(INSTITUTIONAL_SECTION_IDS)
    return list(STANDARD_SECTION_IDS)


def sections_for_mode(mode: str | None, sections_catalog: list[dict[str, Any]], *, purpose: str | None = None) -> list[dict[str, Any]]:
    """Resolve section dicts for a report mode from app.SECTIONS catalog."""
    _ = purpose  # application extras handled by caller if needed
    wanted = set(section_ids_for_mode(mode))
    return [s for s in sections_catalog if int(s.get("id", 0)) in wanted]


def funding_ready_mode_for_report_mode(mode: str | None) -> bool:
    return normalize_report_mode(mode) == "institutional"