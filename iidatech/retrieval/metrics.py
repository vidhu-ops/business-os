"""Structured logging for evidence retrieval."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger("iidatech.retrieval")


@dataclass
class RetrievalEvent:
    section_title: str
    path_taken: str
    retrieval_family: str = "general"
    section_id: int | None = None
    topic: str = ""
    industry: str = ""
    target: str = ""
    phase: str = "A"
    embedding_backend: str = "hash_trigram"
    embedding_version: str = "hash-v1"
    chroma_path: str = ""
    fallback_reason: str | None = None
    query_text: str = ""
    top_k_requested: int = 24
    vector_candidates: int = 0
    after_hydrate: int = 0
    after_precision_exclude: int = 0
    selected_count: int = 0
    max_records: int = 18
    vector_weight: float = 0.15
    business_weight: float = 0.85
    timed_out: bool = False
    error: str | None = None
    timing_ms: dict[str, float] = field(default_factory=dict)
    feature_flags: dict[str, bool] = field(default_factory=dict)
    index: dict[str, Any] = field(default_factory=dict)
    event: str = "evidence_retrieval.v1"
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def log_evidence_retrieval_event(retrieval_event: RetrievalEvent, *, debug: bool = False) -> None:
    payload = asdict(retrieval_event)
    log.info(json.dumps(payload, ensure_ascii=False))
    if not debug:
        return
    try:
        import streamlit as st

        session = getattr(st, "session_state", None)
        if session is None or not hasattr(session, "setdefault"):
            return
        buffer = session.setdefault("iidatech_retrieval_debug", [])
        if isinstance(buffer, list):
            buffer.append(payload)
    except (ImportError, AttributeError, RuntimeError):
        pass
