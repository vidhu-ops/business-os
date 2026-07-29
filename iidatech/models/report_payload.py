"""Explicit contract for institutional report output from ``run_report_generation``.

The legacy runner stores a dict at ``st.session_state["last_iidatech_report"]``.
These types document that schema without changing ``app.py``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


# Top-level keys written to st.session_state["last_iidatech_report"] (app.py ~27242-27268).
SESSION_REPORT_REQUIRED_KEYS: tuple[str, ...] = (
    "topic",
    "industry",
    "geography",
    "horizon",
    "depth",
    "application_purpose",
    "application_readiness_pack",
    "selected_sections",
    "evidence_completeness",
    "quantitative_model",
    "topic_intelligence_brief",
    "diligence_pack",
    "sections",
)

# Added on the second session write, after build_report_audit completes.
SESSION_REPORT_AUDIT_KEY = "final_report_audit"

# Keys present on disk checkpoint payloads (write_report_checkpoint), not in session report dict.
CHECKPOINT_FILE_KEYS: tuple[str, ...] = (
    "topic",
    "industry",
    "geography",
    "horizon",
    "depth",
    "checkpoint_schema_version",
    "completed_sections",
    "sections",
    "quality_scores",
    "updated_at",
)

# Derived exports built after session write; never stored in last_iidatech_report.
DERIVED_EXPORT_KEYS: tuple[str, ...] = (
    "report_markdown",
    "report_html",
    "market_by_market_markdown",
    "quality_scores_json",
)


@dataclass
class ReportCheckpointInfo:
    """Checkpoint metadata available outside the core session payload."""

    last_checkpoint_path: str | None = None
    checkpoint_payload: dict[str, Any] | None = None
    quality_scores: dict[str, Any] = field(default_factory=dict)
    completed_sections: list[Any] = field(default_factory=list)
    checkpoint_schema_version: int | None = None
    updated_at: str | None = None


@dataclass
class ReportCorePayload:
    """Mirror of the legacy ``full_report_payload`` dict stored in session state."""

    topic: str = ""
    industry: str = ""
    geography: str = ""
    horizon: str = ""
    depth: str = ""
    application_purpose: str = ""
    application_readiness_pack: dict[str, Any] = field(default_factory=dict)
    selected_sections: list[dict[str, Any]] = field(default_factory=list)
    evidence_completeness: dict[str, Any] = field(default_factory=dict)
    quantitative_model: dict[str, Any] = field(default_factory=dict)
    topic_intelligence_brief: dict[str, Any] = field(default_factory=dict)
    diligence_pack: dict[str, Any] = field(default_factory=dict)
    sections: dict[Any, str] = field(default_factory=dict)
    final_report_audit: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> ReportCorePayload:
        sections = raw.get("sections") if isinstance(raw.get("sections"), dict) else {}
        return cls(
            topic=str(raw.get("topic") or ""),
            industry=str(raw.get("industry") or ""),
            geography=str(raw.get("geography") or ""),
            horizon=str(raw.get("horizon") or ""),
            depth=str(raw.get("depth") or ""),
            application_purpose=str(raw.get("application_purpose") or ""),
            application_readiness_pack=(
                raw.get("application_readiness_pack")
                if isinstance(raw.get("application_readiness_pack"), dict)
                else {}
            ),
            selected_sections=list(raw.get("selected_sections") or []),
            evidence_completeness=(
                raw.get("evidence_completeness") if isinstance(raw.get("evidence_completeness"), dict) else {}
            ),
            quantitative_model=(
                raw.get("quantitative_model") if isinstance(raw.get("quantitative_model"), dict) else {}
            ),
            topic_intelligence_brief=(
                raw.get("topic_intelligence_brief")
                if isinstance(raw.get("topic_intelligence_brief"), dict)
                else {}
            ),
            diligence_pack=raw.get("diligence_pack") if isinstance(raw.get("diligence_pack"), dict) else {},
            sections={key: value for key, value in sections.items()},
            final_report_audit=(
                raw.get(SESSION_REPORT_AUDIT_KEY)
                if isinstance(raw.get(SESSION_REPORT_AUDIT_KEY), dict)
                else {}
            ),
            raw=dict(raw),
        )

    def missing_required_keys(self) -> list[str]:
        return [key for key in SESSION_REPORT_REQUIRED_KEYS if key not in self.raw]


@dataclass
class ReportPayload:
    """Explicit report output contract for service-layer consumers."""

    report_markdown: str = ""
    report_html: str = ""
    market_by_market_markdown: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    sources: list[dict[str, Any]] = field(default_factory=list)
    audit: dict[str, Any] = field(default_factory=dict)
    checkpoints: ReportCheckpointInfo = field(default_factory=ReportCheckpointInfo)
    quality_scores: dict[str, Any] = field(default_factory=dict)
    core: ReportCorePayload = field(default_factory=ReportCorePayload)
    raw: dict[str, Any] = field(default_factory=dict)
    missing_fields: list[str] = field(default_factory=list)
    unstable_fields: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return bool(self.raw) and bool(self.core.topic) and bool(self.core.sections)

    def to_service_dict(self) -> dict[str, Any]:
        """Shape aligned with ``generate_report`` response fields."""
        return {
            "success": self.success,
            "report": self.report_markdown,
            "metadata": {
                **self.metadata,
                "audit": self.audit,
                "quality_scores": self.quality_scores,
                "checkpoints": {
                    "last_checkpoint_path": self.checkpoints.last_checkpoint_path,
                    "completed_sections": self.checkpoints.completed_sections,
                    "checkpoint_schema_version": self.checkpoints.checkpoint_schema_version,
                    "updated_at": self.checkpoints.updated_at,
                },
                "missing_fields": self.missing_fields,
                "unstable_fields": self.unstable_fields,
            },
            "sources": self.sources,
            "report_html": self.report_html,
            "market_by_market_markdown": self.market_by_market_markdown,
            "raw": self.raw,
        }


def extract_sources_from_raw(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Collect citation ledger rows and section URL mentions from a legacy payload."""
    sources: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add_source(row: dict[str, Any]) -> None:
        if not isinstance(row, dict):
            return
        url = str(row.get("url") or row.get("source_url") or "").strip()
        title = str(row.get("title") or row.get("publisher") or row.get("name") or "").strip()
        key = url or title
        if not key or key in seen:
            return
        seen.add(key)
        sources.append(row)

    diligence = payload.get("diligence_pack") if isinstance(payload.get("diligence_pack"), dict) else {}
    for row in diligence.get("citation_ledger", []) or []:
        add_source(row)

    for row in payload.get("source_ledger", []) or []:
        add_source(row)

    sections = payload.get("sections") if isinstance(payload.get("sections"), dict) else {}
    for section_output in sections.values():
        text = section_output if isinstance(section_output, str) else json.dumps(section_output, ensure_ascii=False)
        for url in re.findall(r"https?://[^\s\]|)\"']+", text):
            add_source({"url": url.rstrip(".,;"), "title": url.rstrip(".,;"), "source_family": "section_citation"})

    return sources


def build_report_metadata(core: ReportCorePayload) -> dict[str, Any]:
    """Stable summary metadata extracted from the legacy payload."""
    diligence = core.diligence_pack if isinstance(core.diligence_pack, dict) else {}
    return {
        "topic": core.topic,
        "industry": core.industry,
        "geography": core.geography,
        "horizon": core.horizon,
        "depth": core.depth,
        "application_purpose": core.application_purpose,
        "section_count": len(core.sections),
        "selected_section_count": len(core.selected_sections),
        "evidence_completeness": core.evidence_completeness,
        "topic_intelligence_brief": core.topic_intelligence_brief,
        "quantitative_model": core.quantitative_model,
        "application_readiness_pack": core.application_readiness_pack,
        "diligence_readiness": (diligence.get("readiness") or {}) if isinstance(diligence, dict) else {},
        "markets_report_gate": (diligence.get("markets_report_gate") or {}) if isinstance(diligence, dict) else {},
        "strict_verification_summary": (
            (diligence.get("strict_verification_pack") or {}).get("summary")
            if isinstance(diligence.get("strict_verification_pack"), dict)
            else None
        ),
    }


def load_checkpoint_info(session_state: Any, app_module: Any | None = None) -> ReportCheckpointInfo:
    """Load checkpoint file referenced by session, if present."""
    path_value = None
    if isinstance(session_state, dict):
        path_value = session_state.get("last_report_checkpoint")
    else:
        path_value = session_state.get("last_report_checkpoint")

    info = ReportCheckpointInfo(last_checkpoint_path=str(path_value) if path_value else None)
    if not path_value:
        return info

    path = Path(str(path_value))
    if not path.exists() and app_module is not None:
        loader = getattr(app_module, "load_report_checkpoint", None)
        topic = ""
        geography = ""
        if isinstance(session_state, dict):
            report = session_state.get("last_iidatech_report") or {}
        else:
            report = session_state.get("last_iidatech_report") or {}
        if isinstance(report, dict):
            topic = str(report.get("topic") or "")
            geography = str(report.get("geography") or "")
        if callable(loader) and topic:
            payload = loader(topic, geography)
            if isinstance(payload, dict):
                info.checkpoint_payload = payload
    if info.checkpoint_payload is None and path.exists():
        try:
            info.checkpoint_payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            info.checkpoint_payload = None

    payload = info.checkpoint_payload if isinstance(info.checkpoint_payload, dict) else {}
    quality_scores = payload.get("quality_scores") if isinstance(payload.get("quality_scores"), dict) else {}
    info.quality_scores = dict(quality_scores)
    info.completed_sections = list(payload.get("completed_sections") or [])
    schema_version = payload.get("checkpoint_schema_version")
    info.checkpoint_schema_version = int(schema_version) if schema_version is not None else None
    info.updated_at = str(payload.get("updated_at") or "") or None
    return info


def classify_payload_gaps(core: ReportCorePayload, checkpoints: ReportCheckpointInfo) -> tuple[list[str], list[str]]:
    """Return (missing_fields, unstable_fields) for documentation and callers."""
    missing = core.missing_required_keys()
    if not core.final_report_audit:
        missing.append(SESSION_REPORT_AUDIT_KEY)
    if not checkpoints.quality_scores:
        missing.append("quality_scores")

    unstable: list[str] = []
    if core.final_report_audit and not core.final_report_audit.get("audit_route"):
        unstable.append("audit.audit_route")
    if not checkpoints.last_checkpoint_path:
        unstable.append("checkpoints.last_checkpoint_path")
    unstable.extend(
        [
            "diligence_pack.strict_verification_pack",
            "diligence_pack.funding_readiness_pack",
            "sections.* (JSON strings, schema varies by section)",
            "quality_scores (only on checkpoint file, not session report)",
            "derived report_html / market_by_market_markdown (computed post-session-write)",
        ]
    )
    return missing, unstable
