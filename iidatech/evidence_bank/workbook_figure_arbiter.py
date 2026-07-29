"""Cross-verify Perplexity/report figures against CRM verification workbook."""
from __future__ import annotations

import re
from typing import Any

from iidatech.evidence_bank.crm_verification_workbook import (
    is_crm_workbook_topic,
    load_workbook_records,
    records_for_geography,
    search_records,
    verified_records,
)
from iidatech.evidence_bank.report_postprocess import has_parseable_figure

_MONEY_RE = re.compile(
    r"(?:USD|US\$|INR|Rs\.?|[$\u20b9])\s?[\d.,]+(?:\s?(?:billion|million|mn|bn|crore|lakh|b))?",
    re.I,
)
_PCT_RE = re.compile(r"[\d.]+\s*%")
_NUM_RE = re.compile(r"[\d.,]+(?:\s?(?:million|billion|crore|lakh|bn|mn))?", re.I)


def _normalize_num(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").lower().replace(",", "").strip())


def _figures_in_text(text: str) -> list[str]:
    blob = str(text or "")
    found = _MONEY_RE.findall(blob) + _PCT_RE.findall(blob)
    return list(dict.fromkeys(f.strip() for f in found if f.strip()))


def _token_overlap(a: str, b: str) -> float:
    ta = {t for t in re.findall(r"[a-z0-9]{3,}", a.lower())}
    tb = {t for t in re.findall(r"[a-z0-9]{3,}", b.lower())}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _row_matches_section(rec: dict[str, Any], section_text: str) -> bool:
    blob = section_text.lower()
    dp = str(rec.get("data_point") or "").lower()
    ent = str(rec.get("entity") or "").lower()
    vert = str(rec.get("vertical") or "").lower()
    if ent and ent in blob:
        return True
    if vert and vert in blob:
        return True
    if dp and _token_overlap(dp, blob) >= 0.25:
        return True
    for token in re.findall(r"[a-z]{4,}", dp):
        if token in blob:
            return True
    for token in re.findall(r"[a-z]{4,}", vert):
        if token in blob:
            return True
    return False


def _values_conflict(report_val: str, sheet_val: str) -> bool:
    a = _normalize_num(report_val)
    b = _normalize_num(sheet_val)
    if not a or not b:
        return False
    if a == b:
        return False
    nums_a = _NUM_RE.findall(a)
    nums_b = _NUM_RE.findall(b)
    if nums_a and nums_b and nums_a[0] == nums_b[0]:
        return False
    return True


def arbiter_report_sections(
    sections: list[dict[str, Any]],
    *,
    topic: str,
    industry: str,
    geography: str,
) -> dict[str, Any]:
    """Compare report sections to workbook; return corrections and additions."""
    if not is_crm_workbook_topic(topic, industry):
        return {"applied": False, "reason": "topic_not_crm_workbook", "corrections": [], "additions": []}
    if not load_workbook_records():
        return {"applied": False, "reason": "workbook_missing", "corrections": [], "additions": []}

    corrections: list[dict[str, Any]] = []
    additions: list[dict[str, Any]] = []
    perplexity_only: list[dict[str, Any]] = []
    matched_sheet_ids: set[str] = set()

    sheet_rows = records_for_geography(geography)
    verified = [r for r in sheet_rows if r.get("verified_bool")]

    for sec in sections:
        if not isinstance(sec, dict):
            continue
        body = str(sec.get("body_markdown") or "")
        title = str(sec.get("title") or "")
        section_blob = f"{title}\n{body}"
        metrics = sec.get("key_metrics") if isinstance(sec.get("key_metrics"), dict) else {}

        for rec in sheet_rows:
            rid = f"{rec.get('sheet')}|{rec.get('data_point')}|{rec.get('value')}"
            if not _row_matches_section(rec, section_blob):
                continue
            matched_sheet_ids.add(rid)
            sheet_val = str(rec.get("value") or "").strip()
            if not sheet_val:
                continue

            report_vals = list(metrics.values()) + _figures_in_text(section_blob)
            report_vals = [str(v) for v in report_vals if has_parseable_figure(str(v)) or _NUM_RE.search(str(v))]

            if rec.get("verified_bool"):
                conflict = any(_values_conflict(rv, sheet_val) for rv in report_vals)
                if conflict and report_vals:
                    corrections.append(
                        {
                            "action": "correct_to_workbook",
                            "section_id": sec.get("id"),
                            "section_title": title,
                            "data_point": rec.get("data_point"),
                            "entity": rec.get("entity"),
                            "perplexity_value": report_vals[0],
                            "workbook_value": sheet_val,
                            "verified": True,
                            "source": rec.get("publisher"),
                            "url": rec.get("url"),
                            "notes": rec.get("notes"),
                        }
                    )
                elif sheet_val not in body and _token_overlap(sheet_val, body) < 0.1:
                    additions.append(
                        {
                            "action": "add_verified_workbook",
                            "section_id": sec.get("id"),
                            "data_point": rec.get("data_point"),
                            "workbook_value": sheet_val,
                            "entity": rec.get("entity"),
                            "vertical": rec.get("vertical"),
                            "url": rec.get("url"),
                            "notes": rec.get("notes"),
                        }
                    )
            else:
                if report_vals:
                    perplexity_only.append(
                        {
                            "data_point": rec.get("data_point"),
                            "perplexity_value": report_vals[0],
                            "workbook_status": rec.get("verified"),
                            "note": "Perplexity figure kept — workbook row NOT YET VERIFIED",
                        }
                    )

    for rec in verified:
        rid = f"{rec.get('sheet')}|{rec.get('data_point')}|{rec.get('value')}"
        if rid in matched_sheet_ids:
            continue
        q = f"{rec.get('data_point')} {rec.get('entity')}"
        if search_records(q, geography, limit=1):
            additions.append(
                {
                    "action": "add_verified_workbook",
                    "section_id": None,
                    "data_point": rec.get("data_point"),
                    "workbook_value": rec.get("value"),
                    "entity": rec.get("entity"),
                    "vertical": rec.get("vertical"),
                    "url": rec.get("url"),
                    "notes": rec.get("notes"),
                }
            )

    return {
        "applied": True,
        "topic": topic,
        "geography": geography,
        "workbook_path": str(__import__("iidatech.evidence_bank.crm_verification_workbook", fromlist=["workbook_path"]).workbook_path()),
        "verified_row_count": len(verified),
        "corrections": corrections,
        "additions": additions,
        "perplexity_only": perplexity_only,
    }


def apply_workbook_arbiter_to_sections(
    sections: list[dict[str, Any]],
    arbiter: dict[str, Any],
) -> list[dict[str, Any]]:
    """Apply corrections and additions into section bodies (deterministic)."""
    if not arbiter.get("applied"):
        return sections

    by_id: dict[Any, dict[str, Any]] = {}
    for sec in sections:
        if isinstance(sec, dict):
            by_id[sec.get("id")] = sec

    for fix in arbiter.get("corrections") or []:
        if not isinstance(fix, dict):
            continue
        sec = by_id.get(fix.get("section_id"))
        if not sec:
            continue
        body = str(sec.get("body_markdown") or "")
        old = str(fix.get("perplexity_value") or "")
        new = str(fix.get("workbook_value") or "")
        note = (
            f"\n\n> **Workbook correction (verified):** {fix.get('data_point')} — "
            f"replaced `{old}` with **{new}** per IIDATECH CRM verification sheet "
            f"({fix.get('source') or 'reference workbook'})."
        )
        if old and old in body:
            body = body.replace(old, new, 1)
        sec["body_markdown"] = body + note
        km = dict(sec.get("key_metrics") or {})
        if fix.get("data_point"):
            km[str(fix["data_point"])] = new
        sec["key_metrics"] = km

    appendix_lines = [
        "## CRM market data — workbook cross-check",
        "",
        "Figures below are cross-checked against the IIDATECH CRM Automation verification workbook.",
        "",
    ]
    for add in arbiter.get("additions") or []:
        if not isinstance(add, dict):
            continue
        line = (
            f"- **{add.get('data_point')}** ({add.get('entity') or 'reference'}): "
            f"{add.get('workbook_value')} — *verified workbook*"
        )
        if add.get("vertical"):
            line = f"- **{add.get('vertical')}** — {add.get('workbook_value')} ({add.get('entity') or 'reference'}) — *verified workbook*"
        if add.get("url"):
            line += f" [{add.get('url')}]"
        appendix_lines.append(line)
        sid = add.get("section_id")
        if sid and sid in by_id:
            sec = by_id[sid]
            sec["body_markdown"] = str(sec.get("body_markdown") or "") + f"\n\n{line}"

    for po in arbiter.get("perplexity_only") or []:
        if isinstance(po, dict) and po.get("perplexity_value"):
            appendix_lines.append(
                f"- {po.get('data_point')}: {po.get('perplexity_value')} "
                f"*(Perplexity — {po.get('workbook_status') or 'sheet not verified'})*"
            )

    if len(appendix_lines) > 4:
        max_id = max((int(s.get("id") or 0) for s in sections if isinstance(s, dict)), default=0)
        sections = list(sections) + [
            {
                "id": max_id + 1,
                "title": "CRM verification workbook cross-check",
                "body_markdown": "\n".join(appendix_lines),
                "sources": [],
                "key_metrics": {},
            }
        ]
    return sections


def arbiter_and_apply_sections(
    sections: list[dict[str, Any]],
    *,
    topic: str,
    industry: str,
    geography: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    arb = arbiter_report_sections(sections, topic=topic, industry=industry, geography=geography)
    if arb.get("applied"):
        sections = apply_workbook_arbiter_to_sections(sections, arb)
    return sections, arb
