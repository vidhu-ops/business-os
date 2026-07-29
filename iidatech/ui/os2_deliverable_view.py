"""Human-readable deliverable preview + PDF/Word export for Employee OS."""
from __future__ import annotations

import csv
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

from iidatech.render.report_text import humanize_label, sanitize_report_text


def clean_harness_reply_for_display(reply: str) -> str:
    """Strip internal file-path bullets; keep narrative for the founder."""
    lines: list[str] = []
    for line in str(reply or "").splitlines():
        stripped = line.strip()
        if re.match(r"^- [`'].+\.(md|json|csv|txt|jsonl)[`']\.?$", stripped, re.I):
            continue
        if re.match(r"^- .+business_build_outputs.+", stripped, re.I):
            continue
        lines.append(line)
    text = "\n".join(lines).strip()
    return sanitize_report_text(text) if text else ""


def _read_artifact_text(path: Path, *, limit: int = 120_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _json_to_sections(raw: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    sections: list[dict[str, Any]] = []
    if isinstance(data, list) and data and all(isinstance(x, dict) for x in data):
        rows = []
        for row in data[:40]:
            rows.append({humanize_label(k): _scalar_text(v) for k, v in row.items()})
        sections.append({"kind": "table", "title": "Summary table", "rows": rows})
        return sections
    if isinstance(data, dict):
        scalar_rows = []
        nested: list[tuple[str, Any]] = []
        for key, val in data.items():
            if _is_scalar(val):
                scalar_rows.append({"Field": humanize_label(key), "Value": _scalar_text(val)})
            else:
                nested.append((key, val))
        if scalar_rows:
            sections.append({"kind": "table", "title": "Key details", "rows": scalar_rows})
        for key, val in nested[:8]:
            sections.append({"kind": "text", "title": humanize_label(key), "body": _nested_to_text(val)})
        return sections
    return [{"kind": "text", "title": "Content", "body": _scalar_text(data)}]


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _scalar_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return sanitize_report_text(str(value))


def _nested_to_text(value: Any, *, depth: int = 0) -> str:
    if _is_scalar(value):
        return _scalar_text(value)
    if isinstance(value, list):
        lines = []
        for item in value[:20]:
            if _is_scalar(item):
                lines.append(f"- {_scalar_text(item)}")
            else:
                lines.append(f"- {_nested_to_text(item, depth=depth + 1)}")
        return "\n".join(lines)
    if isinstance(value, dict):
        lines = []
        for k, v in list(value.items())[:24]:
            lines.append(f"**{humanize_label(k)}:** {_scalar_text(v) if _is_scalar(v) else _nested_to_text(v, depth=depth + 1)}")
        return "\n".join(lines)
    return _scalar_text(value)


def _csv_to_rows(raw: str) -> list[dict[str, str]]:
    try:
        reader = csv.DictReader(io.StringIO(raw))
        return [{k: str(v or "") for k, v in row.items()} for row in reader][:50]
    except Exception:
        return []


def deliverable_from_artifact(path: Path) -> dict[str, Any]:
    """Parse an artifact file into a founder-readable deliverable."""
    if not path.is_file():
        return {}
    suffix = path.suffix.lower()
    name = path.stem.replace("_", " ").title()
    raw = _read_artifact_text(path)
    if not raw.strip():
        return {}
    doc: dict[str, Any] = {"title": name, "source": path.name, "sections": []}
    if suffix == ".json":
        doc["sections"] = _json_to_sections(raw)
    elif suffix == ".csv":
        rows = _csv_to_rows(raw)
        if rows:
            doc["sections"] = [{"kind": "table", "title": "Data", "rows": rows}]
    elif suffix in {".md", ".txt"}:
        doc["sections"] = [{"kind": "markdown", "title": name, "body": sanitize_report_text(raw)}]
    elif suffix == ".jsonl":
        rows = []
        for line in raw.splitlines()[:30]:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append({humanize_label(k): _scalar_text(v) for k, v in obj.items()})
            except json.JSONDecodeError:
                continue
        if rows:
            doc["sections"] = [{"kind": "table", "title": "Log entries", "rows": rows}]
    else:
        doc["sections"] = [{"kind": "text", "title": name, "body": sanitize_report_text(raw[:8000])}]
    return doc


def build_combined_deliverable(
    *,
    title: str,
    reply: str = "",
    artifacts: list[str] | None = None,
) -> dict[str, Any]:
    sections: list[dict[str, Any]] = []
    narrative = clean_harness_reply_for_display(reply)
    if narrative:
        sections.append({"kind": "markdown", "title": "Summary", "body": narrative})
    for art in artifacts or []:
        doc = deliverable_from_artifact(Path(str(art)))
        for sec in doc.get("sections") or []:
            if isinstance(sec, dict):
                sections.append(sec)
    return {"title": title or "Team deliverable", "sections": sections}


def deliverable_plain_text(doc: dict[str, Any]) -> str:
    parts = [str(doc.get("title") or "Deliverable"), ""]
    for sec in doc.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        title = str(sec.get("title") or "").strip()
        if title:
            parts.append(title)
            parts.append("-" * min(len(title), 60))
        kind = sec.get("kind")
        if kind == "table":
            for row in sec.get("rows") or []:
                if isinstance(row, dict):
                    parts.append(" | ".join(f"{k}: {v}" for k, v in row.items()))
        else:
            parts.append(str(sec.get("body") or ""))
        parts.append("")
    return sanitize_report_text("\n".join(parts))


def export_deliverable_pdf_bytes(doc: dict[str, Any]) -> bytes:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=42, leftMargin=42, topMargin=42, bottomMargin=42)
    styles = getSampleStyleSheet()
    story = [Paragraph(escape(str(doc.get("title") or "Deliverable")), styles["Title"]), Spacer(1, 12)]
    for sec in doc.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        title = str(sec.get("title") or "").strip()
        if title:
            story.append(Paragraph(escape(title), styles["Heading2"]))
            story.append(Spacer(1, 6))
        if sec.get("kind") == "table":
            for row in sec.get("rows") or []:
                if isinstance(row, dict):
                    line = " | ".join(f"{k}: {v}" for k, v in row.items())
                    story.append(Paragraph(escape(line), styles["BodyText"]))
            story.append(Spacer(1, 8))
        else:
            for raw_line in str(sec.get("body") or "").splitlines():
                line = sanitize_report_text(raw_line.strip())
                if not line:
                    story.append(Spacer(1, 6))
                    continue
                if line.startswith("## "):
                    story.append(Paragraph(escape(line[3:]), styles["Heading2"]))
                elif line.startswith("# "):
                    story.append(Paragraph(escape(line[2:]), styles["Heading1"]))
                elif line.startswith("- "):
                    story.append(Paragraph(escape(line), styles["BodyText"]))
                else:
                    story.append(Paragraph(escape(line), styles["BodyText"]))
            story.append(Spacer(1, 8))
    pdf.build(story)
    return buffer.getvalue()


def export_deliverable_docx_bytes(doc: dict[str, Any]) -> bytes:
    """Minimal Word document (stdlib only)."""
    paragraphs: list[str] = [str(doc.get("title") or "Deliverable"), ""]
    for sec in doc.get("sections") or []:
        if not isinstance(sec, dict):
            continue
        title = str(sec.get("title") or "").strip()
        if title:
            paragraphs.append(title)
        if sec.get("kind") == "table":
            for row in sec.get("rows") or []:
                if isinstance(row, dict):
                    paragraphs.append(" | ".join(f"{k}: {v}" for k, v in row.items()))
        else:
            paragraphs.extend(str(sec.get("body") or "").splitlines())
        paragraphs.append("")

    body_xml = []
    for para in paragraphs:
        text = escape(sanitize_report_text(para))
        if not text:
            body_xml.append("<w:p/>")
        else:
            body_xml.append(f"<w:p><w:r><w:t xml:space=\"preserve\">{text}</w:t></w:r></w:p>")
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        f"<w:body>{''.join(body_xml)}</w:body></w:document>"
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/word/document.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        "</Types>"
    )
    rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        'Target="word/document.xml"/>'
        "</Relationships>"
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("word/document.xml", document_xml)
    return buffer.getvalue()


def render_deliverable_preview(
    st: Any,
    *,
    title: str,
    reply: str = "",
    artifacts: list[str] | None = None,
    key_prefix: str = "os2_del",
) -> None:
    """Claude-style readable preview with PDF/Word download."""
    doc = build_combined_deliverable(title=title, reply=reply, artifacts=artifacts)
    if not doc.get("sections"):
        return
    safe_title = re.sub(r"[^\w\s-]", "", str(title or "deliverable")).strip().replace(" ", "_") or "deliverable"
    with st.container(border=True):
        st.markdown(f"**Deliverable preview** — {title}")
        st.caption("Readable summary for you. Raw JSON/CSV files stay in the background for the team.")
        for sec in doc.get("sections") or []:
            if not isinstance(sec, dict):
                continue
            sec_title = str(sec.get("title") or "").strip()
            if sec_title:
                st.markdown(f"#### {sec_title}")
            kind = sec.get("kind")
            if kind == "table":
                rows = sec.get("rows") or []
                if rows:
                    st.dataframe(rows, width="stretch", hide_index=True)
            elif kind == "markdown":
                st.markdown(str(sec.get("body") or ""))
            else:
                st.markdown(str(sec.get("body") or ""))
        exp1, exp2 = st.columns(2)
        with exp1:
            st.download_button(
                "Download PDF",
                data=export_deliverable_pdf_bytes(doc),
                file_name=f"{safe_title}.pdf",
                mime="application/pdf",
                key=f"{key_prefix}_pdf_{hash(safe_title) % 10**6}",
                width="stretch",
            )
        with exp2:
            st.download_button(
                "Download Word",
                data=export_deliverable_docx_bytes(doc),
                file_name=f"{safe_title}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"{key_prefix}_docx_{hash(safe_title) % 10**6}",
                width="stretch",
            )


def render_artifact_downloads(st: Any, artifacts: list[str], *, key_prefix: str = "os2_raw") -> None:
    """Background raw files — collapsed, for power users only."""
    paths = [Path(str(a)) for a in artifacts if Path(str(a)).is_file()]
    if not paths:
        return
    with st.expander("Source files (JSON / CSV / MD)", expanded=False):
        st.caption("Internal formats used by the team. Use the deliverable preview above for reading.")
        for fp in paths:
            try:
                st.download_button(
                    f"Download {fp.name}",
                    data=fp.read_bytes(),
                    file_name=fp.name,
                    key=f"{key_prefix}_{fp.name}_{hash(str(fp)) % 10**6}",
                )
            except OSError:
                st.caption(str(fp))
