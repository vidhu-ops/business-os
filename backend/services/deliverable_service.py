from __future__ import annotations

from pathlib import Path
from typing import Any

from backend.config import settings
from iidatech.ui.os2_deliverable_view import (
    build_combined_deliverable,
    clean_harness_reply_for_display,
    deliverable_from_artifact,
    export_deliverable_docx_bytes,
    export_deliverable_pdf_bytes,
)


def _resolve_path(path: str) -> Path:
    p = Path(path)
    if p.is_file():
        return p
    candidate = (settings.app_root / path).resolve()
    if str(candidate).startswith(str(settings.app_root.resolve())) and candidate.is_file():
        return candidate
    candidate2 = (settings.outputs_root / path).resolve()
    if candidate2.is_file():
        return candidate2
    return p


def preview_deliverable(*, title: str, reply: str = "", artifacts: list[str] | None = None) -> dict[str, Any]:
    arts = [_resolve_path(str(a)) for a in (artifacts or []) if str(a).strip()]
    existing = [p for p in arts if p.is_file()]
    doc = build_combined_deliverable(title=title, reply=clean_harness_reply_for_display(reply), artifacts=[str(p) for p in existing])
    return doc


def export_deliverable(doc: dict[str, Any], fmt: str) -> tuple[bytes, str, str]:
    if fmt == "pdf":
        data = export_deliverable_pdf_bytes(doc)
        return data, "application/pdf", f"{doc.get('title', 'deliverable')}.pdf"
    if fmt == "docx":
        data = export_deliverable_docx_bytes(doc)
        return data, "application/vnd.openxmlformats-officedocument.wordprocessingml.document", f"{doc.get('title', 'deliverable')}.docx"
    raise ValueError("format must be pdf or docx")


def artifact_preview(path: str) -> dict[str, Any]:
    p = _resolve_path(path)
    if not p.is_file():
        return {}
    return deliverable_from_artifact(p)
