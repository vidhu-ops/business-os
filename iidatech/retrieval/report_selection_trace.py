"""Debug trace for report evidence selection."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

log = logging.getLogger("iidatech.retrieval.report_selection")

_TRACE: list[dict[str, Any]] = []
_ENABLED: bool | None = None


def report_selection_trace_enabled() -> bool:
    global _ENABLED
    if _ENABLED is None:
        _ENABLED = os.getenv("IIDATECH_REPORT_SELECTION_TRACE", "").strip() in {"1", "true", "True", "yes", "YES"}
    return bool(_ENABLED)


def reset_report_selection_trace() -> None:
    _TRACE.clear()


def get_report_selection_trace() -> list[dict]:
    return list(_TRACE)


def build_report_selection_trace(section: str, candidate_records: list[dict], selected_records: list[dict]) -> list[dict]:
    selected_ids = {str(r.get("record_id") or r.get("id") or "") for r in selected_records}
    rows = []
    for record in candidate_records:
        rid = str(record.get("record_id") or record.get("id") or "")
        rows.append({
            "record_id": rid,
            "topic": str(record.get("_selection_topic") or ""),
            "section": section,
            "source_url": str(record.get("url") or record.get("source_url") or ""),
            "source_family": str(record.get("source_family") or ""),
            "record_type": str(record.get("_selection_record_type") or record.get("record_type") or record.get("claim_type") or ""),
            "domain_tags": list(record.get("topic_tags") or [])[:8],
            "geography": str(record.get("geography") or ""),
            "quality_score": record.get("quality_score") or record.get("confidence"),
            "relevance_score": record.get("_selection_relevance_score"),
            "selected": rid in selected_ids and rid != "",
            "rejection_reason": str(record.get("_selection_rejection_reason") or ""),
        })
    return rows


def emit_report_selection_trace(section: str, candidate_records: list[dict], selected_records: list[dict]) -> None:
    if not report_selection_trace_enabled():
        return
    rows = build_report_selection_trace(section, candidate_records, selected_records)
    _TRACE.extend(rows)
    for row in rows:
        log.debug(json.dumps(row, ensure_ascii=False))
