"""Trace helpers for IIDATECH synthesis overload debugging."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger("iidatech.synthesis")

_TRACE: list[dict[str, Any]] = []
_ENABLED: bool | None = None


def synthesis_trace_enabled() -> bool:
    global _ENABLED
    if _ENABLED is None:
        _ENABLED = os.getenv("IIDATECH_SYNTHESIS_TRACE", "").strip() in {"1", "true", "True", "yes", "YES"}
    return bool(_ENABLED)


def reset_synthesis_trace() -> None:
    _TRACE.clear()


def get_synthesis_trace() -> list[dict[str, Any]]:
    return list(_TRACE)


def emit_synthesis_trace(
    *,
    section: str,
    evidence_rows_count: int,
    claims_before_merge: int,
    claims_after_merge: int,
    payload_chars: int,
    claim_types: list[str],
) -> None:
    if not synthesis_trace_enabled():
        return
    row = {
        "section": section,
        "evidence_rows_count": evidence_rows_count,
        "claims_before_merge": claims_before_merge,
        "claims_after_merge": claims_after_merge,
        "payload_chars": payload_chars,
        "claim_types": claim_types,
    }
    _TRACE.append(row)
    log.info(json.dumps(row, ensure_ascii=False))