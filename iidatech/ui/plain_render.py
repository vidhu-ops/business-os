"""Streamlit render helpers extracted from app.py (phase 1)."""
from __future__ import annotations

import re

import streamlit as st

def sanitize_report_text(text: str) -> str:
    """Strip operational/backend language from report content."""
    if text is None:
        return ""
    cleaned = str(text)
    try:
        fixed = cleaned.encode("latin-1").decode("utf-8")
        if fixed.count("\ufffd") <= cleaned.count("\ufffd"):
            cleaned = fixed
    except Exception:
        pass
    cleaned = cleaned.translate({
        ord("\u2014"): "-",
        ord("\u2013"): "-",
        ord("\u2018"): "'",
        ord("\u2019"): "'",
        ord("\u201c"): '"',
        ord("\u201d"): '"',
        ord("\u2022"): "-",
        ord("\u00a0"): " ",
    })
    for bad, replacement in {
        "\u00e2\u20ac\u201d": "-",
        "\u00e2\u20ac\u201c": "-",
        "\u00e2\u20ac\u2122": "'",
        "\u00e2\u20ac\u0153": '"',
        "\u00e2\u20ac\ufffd": '"',
        "\u00e2\u20ac\u00a2": "-",
        "\ufffd": "",
    }.items():
        cleaned = cleaned.replace(bad, replacement)
    cleaned = re.sub(r"\?{2,}", "-", cleaned)
    patterns = [
        r"Cloud synthesis failed(?: or was unavailable)?[^\n]*",
        r"Add or enable Anthropic/DeepSeek credentials[^\n]*",
        r"because the paid/cloud synthesis route was unavailable\.?",
        r"This local draft is based only on retrieved evidence[^\n]*",
        r"backend failures?|API routing|fallback text|debug status|Authentication\s+Fails?",
        r"DeepSeek\s+(?:HTTP|error|request failed)[^\n]*",
        r"Anthropic\s+(?:HTTP|error|request failed|synthesis failed)[^\n]*",
        r"\b(?:401|403)\b[^\n]*",
        r"Unsupported numeric tokens detected:[^\n.]*\.?",
    ]
    for pattern in patterns:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    evidence_gap = "PRIMARY RESEARCH REQUIRED: source-backed value not available"
    placeholder_patterns = [
        r"\[unsupported numeric claim removed\]",
        r"\[source(?: needed| required)?\]",
        r"\[(?:x|xx|xxx|x%|unclear %|tbd|todo|placeholder|insert[^\]]*)\]",
        r"\{\{\s*(?:x|x%|tbd|todo|placeholder|insert[^}]*)\s*\}\}",
        r"<\s*(?:insert|tbd|todo|placeholder)[^>]*>",
        r"source-gated estimate withheld",
        r"masked value(?: appearing)?",
        r"not\s+calculated\s+placeholder",
    ]
    for pattern in placeholder_patterns:
        cleaned = re.sub(pattern, evidence_gap, cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(
        r"\$?\d[\d,]*(?:\.\d+)?\s*(?:%|m|b|k|bn|million|billion|thousand|CAGR)?\s*[-/]\s*"
        r"PRIMARY RESEARCH REQUIRED: source-backed value not available",
        "PRIMARY RESEARCH REQUIRED: source-backed range not validated",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(
        r"PRIMARY RESEARCH REQUIRED: source-backed value not available\s*[-/]\s*"
        r"\$?\d[\d,]*(?:\.\d+)?\s*(?:%|m|b|k|bn|million|billion|thousand|CAGR)?",
        "PRIMARY RESEARCH REQUIRED: source-backed range not validated",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = re.sub(r"(PRIMARY RESEARCH REQUIRED: source-backed value not available)(?:\s*[,;]\s*\1)+", r"\1", cleaned)
    cleaned = re.sub(r"\[\s*\]|\{\s*\}|<\s*>", "", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned or "No publishable synthesis was produced from the available evidence."


def extract_degradation_context(payload: dict | None) -> tuple[bool, str]:
    """Read report_degraded + reason from payload or nested diligence_pack."""
    data = payload if isinstance(payload, dict) else {}
    diligence = data.get("diligence_pack") if isinstance(data.get("diligence_pack"), dict) else {}
    degraded = bool(data.get("report_degraded") or diligence.get("report_degraded"))
    reason = (
        data.get("degradation_reason")
        or data.get("report_degrade_reason")
        or diligence.get("degradation_reason")
        or diligence.get("report_degrade_reason")
        or "unknown"
    )
    return degraded, str(reason)[:240]


def degradation_banner_markdown(reason: str) -> str:
    return (
        f"> ⚠ This report was generated with a partial data failure and may be incomplete. "
        f"Reason: {reason}\n\n"
    )


def prepend_degradation_banner(markdown: str, payload: dict | None) -> str:
    """Prepend visible degradation warning to rendered report markdown."""
    degraded, reason = extract_degradation_context(payload)
    if not degraded:
        return markdown or ""
    banner = degradation_banner_markdown(reason)
    body = markdown or ""
    if banner.strip() in body[:600]:
        return body
    return banner + body

def humanize_label(value: str) -> str:
    return str(value).replace("_", " ").strip().title()


def is_scalar(value) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))

def render_plain_value(value, level: int = 0, max_items: int = 12):
    """Render nested values inside a parent expander without creating more expanders."""
    heading_level = min(6, 4 + level)
    if isinstance(value, dict):
        scalar_rows = []
        nested_items = []
        for key, item in value.items():
            if is_scalar(item):
                scalar_rows.append({
                    "Field": humanize_label(key),
                    "Value": "" if item is None else sanitize_report_text(str(item)),
                })
            else:
                nested_items.append((key, item))
        if scalar_rows:
            st.table(scalar_rows[:max_items])
        for key, item in nested_items[:max_items]:
            st.markdown(f"{'#' * heading_level} {humanize_label(key)}")
            render_plain_value(item, level + 1, max_items=max_items)
    elif isinstance(value, list):
        if not value:
            st.caption("No items available.")
            return
        shown = value[:max_items]
        if all(isinstance(item, dict) for item in shown):
            rows = []
            nested_blocks = []
            for idx, item in enumerate(shown):
                row = {}
                nested = {}
                for key, val in item.items():
                    if is_scalar(val):
                        row[humanize_label(key)] = "" if val is None else sanitize_report_text(str(val))
                    else:
                        nested[humanize_label(key)] = val
                if nested:
                    row["Details"] = "; ".join(nested.keys())
                    nested_blocks.append((idx + 1, item.get("title") or item.get("section") or f"Item {idx + 1}", nested))
                rows.append(row)
            if rows:
                st.table(rows)
            for idx, label, nested in nested_blocks[:4]:
                st.markdown(f"{'#' * heading_level} {sanitize_report_text(str(label))}")
                render_plain_value(nested, level + 1, max_items=max_items)
        else:
            for item in shown:
                if is_scalar(item):
                    st.markdown(f"- {sanitize_report_text(str(item))}")
                else:
                    render_plain_value(item, level + 1, max_items=max_items)
        if len(value) > max_items:
            st.caption(f"Showing {max_items} of {len(value)} items.")
    else:
        st.markdown(sanitize_report_text(str(value)))
