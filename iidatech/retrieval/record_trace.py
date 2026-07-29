"""Debug trace for evidence record acceptance through the research pipeline."""

from __future__ import annotations

import json
import logging
import os
from typing import Any
from urllib.parse import urlparse

log = logging.getLogger("iidatech.retrieval.record_trace")

_TRACE: list[dict[str, Any]] = []
_ENABLED: bool | None = None


def record_trace_enabled() -> bool:
    global _ENABLED
    if _ENABLED is None:
        _ENABLED = os.getenv("IIDATECH_RECORD_TRACE", "").strip() in {"1", "true", "True", "yes", "YES"}
    return bool(_ENABLED)


def reset_record_acceptance_trace() -> None:
    _TRACE.clear()


def get_record_acceptance_trace() -> list[dict[str, Any]]:
    return list(_TRACE)


def flush_record_acceptance_trace() -> list[dict[str, Any]]:
    rows = list(_TRACE)
    reset_record_acceptance_trace()
    return rows


def _record_url(record: dict[str, Any]) -> str:
    for key in ("url", "source_url", "link", "source"):
        val = record.get(key)
        if val:
            return str(val)
    return ""


def _record_domain(record: dict[str, Any]) -> str:
    url = _record_url(record)
    if url:
        try:
            host = urlparse(url).netloc.lower()
            if host.startswith("www."):
                host = host[4:]
            return host
        except Exception:
            pass
    publisher = str(record.get("publisher", "") or "").strip().lower()
    return publisher


def build_record_acceptance_trace(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_url": _record_url(record),
        "domain": _record_domain(record),
        "source_family": str(record.get("source_family", "") or ""),
        "detected_record_type": str(record.get("record_type", "") or record.get("source_type", "") or ""),
        "extracted_fields": {
            k: record.get(k)
            for k in (
                "entity_name",
                "metric_name",
                "metric_value",
                "price_value",
                "billing_model",
                "complaint",
                "evidence_text",
                "confidence",
            )
            if record.get(k) not in (None, "")
        },
        "quality_score": record.get("quality_score"),
        "accepted": None,
        "rejection_reason": "",
        "stage": "",
    }


def trace_record_stage(
    record: dict[str, Any],
    *,
    stage: str,
    accepted: bool | None = None,
    rejection_reason: str = "",
    quality_score: float | int | None = None,
    detected_record_type: str = "",
    extracted_fields: dict[str, Any] | None = None,
) -> None:
    if not record_trace_enabled():
        return
    row = build_record_acceptance_trace(record)
    row["stage"] = stage
    if accepted is not None:
        row["accepted"] = accepted
    if rejection_reason:
        row["rejection_reason"] = rejection_reason
    if quality_score is not None:
        row["quality_score"] = quality_score
    if detected_record_type:
        row["detected_record_type"] = detected_record_type
    if extracted_fields:
        row["extracted_fields"] = {**row.get("extracted_fields", {}), **extracted_fields}
    _TRACE.append(row)
    log.debug(json.dumps(row, ensure_ascii=False))