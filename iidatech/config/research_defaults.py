"""Defaults tuned for ~7/10 research quality (truth depth + section substance)."""
from __future__ import annotations

QUICK_SECTION_RANGE: tuple[int, int] = (1, 3)
STANDARD_SECTION_RANGE: tuple[int, int] = (1, 6)
FULL_SECTION_RANGE: tuple[int, int] = (1, 12)

DEFAULT_SECTION_RANGE = STANDARD_SECTION_RANGE
DEFAULT_LOCAL_QUALITY_TARGET = 7.0
DEFAULT_LOCAL_QUALITY_RETRIES = 2
DEFAULT_CLOUD_SECTION_LIMIT = 6

INVESTOR_READY_SECTION_TARGET = 7.0
INVESTOR_READY_REPORT_TARGET = 7.0
INSTITUTIONAL_SECTION_TARGET = 10.0


def section_range_for_depth(depth: str | None) -> tuple[int, int]:
    key = str(depth or "standard").strip().lower()
    if key in {"quick", "lite", "light", "3"}:
        return QUICK_SECTION_RANGE
    if key in {"full", "deep", "12"}:
        return FULL_SECTION_RANGE
    return STANDARD_SECTION_RANGE


def section_quality_target_for_mode(report_mode: str | None) -> float:
    mode = str(report_mode or "").strip().lower().replace("-", "_").replace(" ", "_")
    if mode in {"investor_memo", "investor", "institutional", "funding"}:
        return INSTITUTIONAL_SECTION_TARGET
    return INVESTOR_READY_SECTION_TARGET


def effective_funding_ready_mode(
    application_purpose: str | None,
    report_mode: str | None = None,
) -> bool:
    """Strict funding gates only for visa/loan packages and investor memo mode."""
    purpose = str(application_purpose or "").strip().lower()
    if any(token in purpose for token in ("visa", "loan", "msme", "sme", "grant", "funding package")):
        return True
    mode = str(report_mode or "").strip().lower().replace("-", "_").replace(" ", "_")
    return mode in {"investor_memo", "investor", "institutional", "funding"}
