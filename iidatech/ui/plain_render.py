"""Streamlit render helpers — UI only; import report_text for API-safe helpers."""
from __future__ import annotations

from iidatech.render.report_text import (
    degradation_banner_markdown,
    extract_degradation_context,
    humanize_label,
    is_scalar,
    prepend_degradation_banner,
    sanitize_report_text,
)

__all__ = [
    "degradation_banner_markdown",
    "extract_degradation_context",
    "humanize_label",
    "is_scalar",
    "prepend_degradation_banner",
    "render_plain_value",
    "sanitize_report_text",
]


def render_plain_value(value, level: int = 0, max_items: int = 12):
    """Render nested values inside a parent expander without creating more expanders."""
    import streamlit as st

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
