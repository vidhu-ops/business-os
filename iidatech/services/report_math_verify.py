"""Deterministic math checks and TAM reconciliation for Perplexity reports."""
from __future__ import annotations

import re
from typing import Any

MATH_TOLERANCE_RATIO = 1.05  # flag when stated vs computed differs by >5%

_TAM_RE = re.compile(
    r"\b(TAM|SAM|SOM|total addressable|serviceable obtainable|serviceable addressable)\b[^.\n]{0,120}"
    r"([\$₹]|\bRs\.?\b|\bUSD\b|\bINR\b)?\s*([\d,]+(?:\.\d+)?)\s*(billion|million|bn|\bm\b|\bcr\b|crore)?",
    re.I,
)

_PRICING_RE = re.compile(
    r"(?:\[?(?:FACT|DERIVED|ESTIMATE|PRIMARY)\]?\s*)?"
    r"([\$₹]|\bRs\.?\b|\bUSD\b|\bINR\b)?\s*([\d,]+(?:\.\d+)?)\s*(?:/|\s*per\s+)(?:mo(?:nth)?|seat|user|license|year|yr)",
    re.I,
)

_TIER_RE = re.compile(
    r"\b(starter|basic|pro|professional|enterprise|team|business|growth|premium|free|standard)\b"
    r"[^.\n]{0,80}?"
    r"([\$₹]|Rs\.?|USD|INR)?\s*([\d,]+(?:\.\d+)?)",
    re.I,
)

_CHAIN_LINE_RE = re.compile(r"×|\*|x", re.I)
_DERIVED_TAG_RE = re.compile(r"\[DERIVED\]", re.I)
_OPERAND_NUM_RE = re.compile(
    r"([\d,]+(?:\.\d+)?)\s*(billion|million|bn|cr|crore|thousand|k)?",
    re.I,
)
_LATEX_RE = re.compile(r"\$[^$]+\$|\\\(|\\\)|\\\[|\\\]")


def format_display_number(value: float) -> str:
    """Human-readable number for report footnotes (no scientific notation)."""
    n = float(value)
    sign = "-" if n < 0 else ""
    n = abs(n)
    if n >= 1e12:
        return f"{sign}{n / 1e12:.2f} trillion"
    if n >= 1e9:
        return f"{sign}{n / 1e9:.2f} billion"
    if n >= 1e7:
        return f"{sign}{n / 1e7:.2f} crore"
    if n >= 1e6:
        return f"{sign}{n / 1e6:.2f} million"
    if n >= 1e3:
        return f"{sign}{n / 1e3:.2f} thousand"
    if n == int(n):
        return f"{sign}{int(n)}"
    return f"{sign}{n:.2f}"


def _expand_sci_notation(match: re.Match[str]) -> str:
    try:
        return format_display_number(float(match.group(0)))
    except (TypeError, ValueError):
        return match.group(0)


def sanitize_analyst_bullet(text: str) -> str:
    """Strip LaTeX/math artifacts from short analyst bullets (not full section bodies)."""
    s = str(text or "").strip()
    if not s:
        return s
    s = _SCI_NOTATION_RE.sub(_expand_sci_notation, s)
    s = _LATEX_RE.sub(" ", s)
    s = s.replace("$", "")
    s = re.sub(r"\\[a-zA-Z]+", "", s)
    s = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", s)
    s = re.sub(r"(?<=[a-z])(?=\d)", " ", s)
    s = re.sub(r"[ \t]+", " ", s).strip()
    return s


def sanitize_report_text(text: str) -> str:
    """Fix sci-notation and glued tokens without destroying markdown, currency, or line breaks."""
    s = str(text or "")
    if not s.strip():
        return s
    s = _SCI_NOTATION_RE.sub(_expand_sci_notation, s)
    s = re.sub(r"(?<=[<>=])([\d,]+)", r" \1", s)
    s = re.sub(r"([\d,]+)(?=[a-zA-Z]{4,})", r"\1 ", s)
    return s


def _scale(token: str) -> float:
    t = str(token or "").strip().lower().replace(",", "")
    if not t:
        return 1.0
    if t.endswith("%"):
        return float(t[:-1] or 0) / 100.0
    mult = 1.0
    if "billion" in t or t.endswith("bn") or (t.endswith("b") and not t.endswith("mb")):
        mult = 1e9
        t = re.sub(r"(billion|bn|b)$", "", t)
    elif "million" in t or (t.endswith("m") and not t.endswith("mm")):
        mult = 1e6
        t = re.sub(r"(million|m)$", "", t)
    elif "crore" in t or t.endswith("cr"):
        mult = 1e7
        t = re.sub(r"(crore|cr)$", "", t)
    elif "thousand" in t or t.endswith("k"):
        mult = 1e3
        t = re.sub(r"(thousand|k)$", "", t)
    try:
        return float(t) * mult
    except ValueError:
        return 1.0


def _line_is_formula(line: str) -> bool:
    return "=" in line and bool(_CHAIN_LINE_RE.search(line))


def _line_is_derived(line: str) -> bool:
    return bool(_DERIVED_TAG_RE.search(line))


def _operand_value(raw: str) -> float | None:
    token = re.sub(r"(?i)\[(?:derived|fact|estimate|primary|assumption)\]", "", str(raw or ""))
    token = re.sub(
        r"(?i)\b(users?|seats?|smbs?|months?|customers?|businesses?|per\s+month|/month)\b",
        "",
        token,
    )
    token = re.sub(r"(?i)\b(rs\.?|inr|usd|₹|\$)\b", "", token)
    m = _OPERAND_NUM_RE.search(token.replace(",", ""))
    if not m:
        return None
    return _scale(f"{m.group(1)}{m.group(2) or ''}")


def _check_chain_line(line: str) -> dict[str, Any] | None:
    if not _line_is_formula(line):
        return None
    if "=" not in line:
        return None
    left, _, right = line.rpartition("=")
    if not _CHAIN_LINE_RE.search(left):
        return None
    operands_raw = re.split(r"\s*(?:×|\*|x)\s*", left, flags=re.I)
    operands: list[float] = []
    for raw in operands_raw:
        val = _operand_value(raw)
        if val is None:
            continue
        operands.append(val)
    if len(operands) < 2:
        return None
    computed = 1.0
    for val in operands:
        computed *= val
    amount_match = re.search(
        r"([\$₹]|\bRs\.?\b|\bUSD\b|\bINR\b)?\s*([\d,]+(?:\.\d+)?)\s*(billion|million|bn|\bm\b|\bcr\b|crore)?",
        right,
        re.I,
    )
    if not amount_match:
        return None
    stated = _scale(f"{amount_match.group(2)}{amount_match.group(3) or ''}")
    if stated <= 0 or computed <= 0:
        return None
    ratio = max(computed, stated) / min(computed, stated)
    if ratio <= MATH_TOLERANCE_RATIO:
        return None
    return {
        "type": "arithmetic_mismatch",
        "chain": left.strip()[:200],
        "computed": round(computed, 4),
        "stated": round(stated, 4),
        "ratio": round(ratio, 2),
        "snippet": line.strip()[:240],
        "derived_tag": _line_is_derived(line),
    }


def verify_derived_chains(text: str) -> list[dict[str, Any]]:
    """Parse [DERIVED] / formula lines, recalc, flag if >5% off stated result."""
    issues: list[dict[str, Any]] = []
    seen_snippets: set[str] = set()
    for line in (text or "").splitlines():
        if not (_line_is_derived(line) or _line_is_formula(line)):
            continue
        issue = _check_chain_line(line)
        if not issue:
            continue
        key = issue["snippet"]
        if key in seen_snippets:
            continue
        seen_snippets.add(key)
        issues.append(issue)
    return issues


def _tam_label_key(label: str) -> str:
    s = str(label or "").strip().lower()
    if "som" in s or "obtainable" in s:
        return "SOM"
    if "sam" in s or "serviceable addressable" in s:
        return "SAM"
    if "tam" in s or "total addressable" in s:
        return "TAM"
    return s.upper()[:12] or "OTHER"


def _tam_numeric(row: dict[str, Any]) -> float | None:
    amount = str(row.get("amount") or "").replace(",", "")
    unit = str(row.get("unit") or "")
    if not amount:
        return None
    try:
        return _scale(f"{amount}{unit}")
    except (TypeError, ValueError):
        return None


def extract_tam_mentions(text: str, *, section_id: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in _TAM_RE.finditer(text or ""):
        label = match.group(1)
        amount = match.group(3)
        unit = match.group(4) or ""
        rows.append(
            {
                "section_id": section_id,
                "label": label,
                "label_key": _tam_label_key(label),
                "amount": amount,
                "unit": unit,
                "numeric": _tam_numeric({"amount": amount, "unit": unit}),
                "snippet": match.group(0)[:180],
            }
        )
    return rows


def extract_pricing_mentions(text: str, *, section_id: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for match in _PRICING_RE.finditer(text or ""):
        amount = match.group(2)
        rows.append(
            {
                "section_id": section_id,
                "tier": "per-unit",
                "amount": amount,
                "snippet": match.group(0)[:120],
                "numeric": _scale(amount),
            }
        )
    for match in _TIER_RE.finditer(text or ""):
        tier = match.group(1)
        amount = match.group(3)
        rows.append(
            {
                "section_id": section_id,
                "tier": tier,
                "amount": amount,
                "snippet": match.group(0)[:120],
                "numeric": _scale(amount),
            }
        )
    return rows


def _tam_conflicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if row.get("numeric") is None:
            continue
        by_key.setdefault(str(row.get("label_key") or "OTHER"), []).append(row)
    conflicts: list[dict[str, Any]] = []
    for key, group in by_key.items():
        if len(group) < 2:
            continue
        nums = [float(r["numeric"]) for r in group if r.get("numeric")]
        if len(nums) < 2:
            continue
        lo, hi = min(nums), max(nums)
        if lo <= 0:
            continue
        ratio = hi / lo
        if ratio > MATH_TOLERANCE_RATIO:
            conflicts.append(
                {
                    "label_key": key,
                    "low": lo,
                    "high": hi,
                    "ratio": round(ratio, 2),
                    "rows": group,
                }
            )
    return conflicts


def _pricing_conflicts(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_tier: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        tier = str(row.get("tier") or "general").lower()
        if row.get("numeric") is None:
            continue
        by_tier.setdefault(tier, []).append(row)
    conflicts: list[dict[str, Any]] = []
    for tier, group in by_tier.items():
        if len(group) < 2:
            continue
        nums = [float(r["numeric"]) for r in group]
        lo, hi = min(nums), max(nums)
        if lo <= 0:
            continue
        ratio = hi / lo
        if ratio > MATH_TOLERANCE_RATIO:
            conflicts.append({"tier": tier, "low": lo, "high": hi, "ratio": round(ratio, 2), "rows": group})
    return conflicts


def audit_sections(sections: list[dict[str, Any]]) -> dict[str, Any]:
    math_issues: list[dict[str, Any]] = []
    tam_rows: list[dict[str, Any]] = []
    pricing_rows: list[dict[str, Any]] = []
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        sid = int(sec.get("id") or 0)
        body = str(sec.get("body_markdown") or "")
        for issue in verify_derived_chains(body):
            issue["section_id"] = sid
            issue["section_title"] = sec.get("title")
            math_issues.append(issue)
        tam_rows.extend(extract_tam_mentions(body, section_id=sid))
        pricing_rows.extend(extract_pricing_mentions(body, section_id=sid))
        km = sec.get("key_metrics") if isinstance(sec.get("key_metrics"), dict) else {}
        for key, val in km.items():
            if "pric" in str(key).lower():
                pricing_rows.extend(extract_pricing_mentions(f"{key}: {val}", section_id=sid))
    return {
        "math_issues": math_issues,
        "tam_mentions": tam_rows,
        "tam_conflicts": _tam_conflicts(tam_rows),
        "pricing_mentions": pricing_rows,
        "pricing_conflicts": _pricing_conflicts(pricing_rows),
    }


def build_financial_ledger_summary(audit: dict[str, Any]) -> str:
    """Structured TAM ledger for the Opus financial pass."""
    tam_rows = audit.get("tam_mentions") or []
    conflicts = audit.get("tam_conflicts") or []
    if not tam_rows:
        return ""
    lines = ["FINANCIAL LEDGER (from draft pass — reconcile or emit bridge/conflict rows):", ""]
    for row in tam_rows[:12]:
        lines.append(
            f"- §{row.get('section_id')} {row.get('label_key')}: "
            f"{row.get('amount')} {row.get('unit') or ''} — {row.get('snippet', '')[:80]}"
        )
    if conflicts:
        lines.append("")
        lines.append("CONFLICTS DETECTED (>5% spread on same metric):")
        for c in conflicts:
            lines.append(
                f"- {c['label_key']}: {c['low']:.2g} vs {c['high']:.2g} (×{c['ratio']}) — "
                "financial table MUST include a bridge/conflict row explaining the difference."
            )
    return "\n".join(lines)


def _math_warning_block(issues: list[dict[str, Any]]) -> str:
    if not issues:
        return ""
    lines = [
        "",
        "> **⚠️ Math verification flag** — deterministic check found arithmetic that does not reconcile (>5% error). "
        "Treat headline TAM/SAM figures below as **[REVIEW REQUIRED]** until corrected.",
        "",
    ]
    for row in issues[:6]:
        tag = " [DERIVED]" if row.get("derived_tag") else ""
        stated = format_display_number(float(row.get("stated") or 0))
        computed = format_display_number(float(row.get("computed") or 0))
        lines.append(
            f"- Section {row.get('section_id')}: stated **{stated}** vs computed **{computed}** "
            f"(×{row.get('ratio')}){tag} — `{row.get('chain', '')[:120]}`"
        )
    return "\n".join(lines) + "\n"


def _downgrade_failed_derived_labels(body: str, issues: list[dict[str, Any]]) -> str:
    out = body
    for issue in issues:
        snippet = str(issue.get("snippet") or "")
        if not snippet or "[DERIVED]" not in snippet:
            continue
        fixed = snippet.replace("[DERIVED]", "[REVIEW REQUIRED — math check failed]", 1)
        out = out.replace(snippet, fixed, 1)
    return out


def _apply_math_warnings(row: dict[str, Any], sec_issues: list[dict[str, Any]]) -> dict[str, Any]:
    if not sec_issues:
        return row
    body = _downgrade_failed_derived_labels(str(row.get("body_markdown") or ""), sec_issues)
    row["body_markdown"] = body + _math_warning_block(sec_issues)
    row.pop("self_check", None)
    return row


def apply_math_audit(sections: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Annotate sections with deterministic math warnings (no model self-grading)."""
    audit = audit_sections(sections)
    issues_by_section: dict[int, list[dict[str, Any]]] = {}
    for issue in audit.get("math_issues") or []:
        sid = int(issue.get("section_id") or 0)
        issues_by_section.setdefault(sid, []).append(issue)

    out: list[dict[str, Any]] = []
    for sec in sections:
        row = dict(sec)
        sid = int(row.get("id") or 0)
        sec_issues = issues_by_section.get(sid) or []
        if sec_issues:
            row = _apply_math_warnings(row, sec_issues)
        else:
            row.pop("self_check", None)
        out.append(row)
    return out, audit


# Word-boundary on Rs/USD/INR — case-insensitive Rs must not match the tail of "founders"/"competitors".
_CURRENCY_PREFIX = r"(?:[\$₹]|\bRs\.?\b|\bUSD\b|\bINR\b)"
_SCALE_SUFFIX = r"(?:billion|million|bn|\bm\b|\bcr\b|crore)"
_NUMERIC_SPAN_RE = re.compile(
    r"(?:\[(?:FACT|DERIVED|ESTIMATE|PRIMARY|ASSUMPTION|OPINION|NOT FOUND)\]\s*)?"
    rf"{_CURRENCY_PREFIX}\s*[\d,]+(?:\.\d+)?(?:\s*{_SCALE_SUFFIX})?"
    r"(?:\s*/\s*(?:mo(?:nth)?|seat|user|license|year|yr))?"
    r"|[\d,]+(?:\.\d+)?\s*(?:%|percent|CAGR|cagr)"
    rf"|\b[\d,]+(?:\.\d+)?\s*{_SCALE_SUFFIX}\b",
    re.I,
)
_SCI_NOTATION_RE = re.compile(r"\b\d+(?:\.\d+)?[eE][+-]?\d+\b")


def _normalize_figure_token(text: str) -> str:
    s = re.sub(r"\s+", " ", str(text or "").lower())
    s = re.sub(r"[\$₹,]", "", s)
    s = s.replace("rs.", "").replace("usd", "").replace("inr", "")
    s = re.sub(r"\[(?:fact|derived|estimate|primary|assumption|opinion|not found)\]\s*", "", s)
    return s.strip()


def merge_structured_ledger(
    ledger: dict[str, Any],
    structured_entries: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    """Merge Opus financial_ledger JSON rows into allowed figure tokens."""
    out = dict(ledger or {})
    allowed = set(out.get("allowed_tokens") or [])
    for entry in structured_entries or []:
        if not isinstance(entry, dict):
            continue
        val = str(entry.get("value") or "").strip()
        if not val:
            continue
        token = _normalize_figure_token(val)
        if token:
            allowed.add(token)
    out["allowed_tokens"] = sorted(allowed)
    out["figure_count"] = len(allowed)
    return out


def build_figure_ledger(sections: list[dict[str, Any]]) -> dict[str, Any]:
    """Collect allowed numeric tokens from Claude-owned financial sections."""
    allowed: set[str] = set()
    entries: list[dict[str, Any]] = []
    source_urls: set[str] = set()
    for sec in sections:
        if not isinstance(sec, dict):
            continue
        body = str(sec.get("body_markdown") or "")
        for url in sec.get("sources") or []:
            u = str(url).strip()
            if u.startswith("http"):
                source_urls.add(u)
        for match in _NUMERIC_SPAN_RE.finditer(body):
            token = _normalize_figure_token(match.group(0))
            if len(token) >= 2:
                allowed.add(token)
        km = sec.get("key_metrics") if isinstance(sec.get("key_metrics"), dict) else {}
        for val in km.values():
            for match in _NUMERIC_SPAN_RE.finditer(str(val or "")):
                token = _normalize_figure_token(match.group(0))
                if len(token) >= 2:
                    allowed.add(token)
    return {
        "allowed_tokens": sorted(allowed),
        "entries": entries,
        "source_urls": sorted(source_urls),
        "figure_count": len(allowed),
    }


def _figure_allowed(span: str, allowed: set[str]) -> bool:
    token = _normalize_figure_token(span)
    if not token or len(token) < 2:
        return True
    if token in allowed:
        return True
    for entry in allowed:
        if entry in token or token in entry:
            return True
    return False


_NOT_FOUND_REPLACEMENT = "[NOT FOUND — no verified source]"


def apply_number_gate(
    sections: list[dict[str, Any]],
    *,
    ledger: dict[str, Any] | None = None,
    protected_section_ids: frozenset[int] | set[int] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Strip uncited numeric spans from narrative sections (Claude financial ledger is source of truth)."""
    allowed = set(ledger.get("allowed_tokens") or []) if ledger else set()
    protected = protected_section_ids or frozenset()
    stripped: list[dict[str, Any]] = []
    out: list[dict[str, Any]] = []

    for sec in sections:
        row = dict(sec)
        sid = int(row.get("id") or 0)
        if sid in protected:
            row.pop("self_check", None)
            out.append(row)
            continue
        body = str(row.get("body_markdown") or "")
        km = dict(row.get("key_metrics") or {}) if isinstance(row.get("key_metrics"), dict) else {}

        def _replace(match: re.Match[str]) -> str:
            span = match.group(0)
            if _figure_allowed(span, allowed):
                return span
            stripped.append({"section_id": sid, "span": span[:120]})
            return _NOT_FOUND_REPLACEMENT

        row["body_markdown"] = _NUMERIC_SPAN_RE.sub(_replace, body)
        new_km: dict[str, Any] = {}
        for key, val in km.items():
            val_s = str(val or "")

            def _replace_km(match: re.Match[str], _val=val_s) -> str:
                span = match.group(0)
                if _figure_allowed(span, allowed):
                    return span
                stripped.append({"section_id": sid, "span": span[:120], "field": key})
                return _NOT_FOUND_REPLACEMENT

            new_km[key] = _NUMERIC_SPAN_RE.sub(_replace_km, val_s)
        row["key_metrics"] = new_km
        row.pop("self_check", None)
        out.append(row)

    audit = {
        "stripped_count": len(stripped),
        "stripped_spans": stripped[:40],
        "ledger_figure_count": len(allowed),
        "protected_section_ids": sorted(int(x) for x in protected),
    }
    return out, audit


def build_tam_reconciliation_markdown(
    draft_sections: list[dict[str, Any]],
    financial_section: dict[str, Any] | None,
    *,
    audit: dict[str, Any] | None = None,
) -> str:
    """Bridge / conflict table when multiple TAM methodologies appear."""
    draft_tams = []
    for sec in draft_sections:
        draft_tams.extend(extract_tam_mentions(str(sec.get("body_markdown") or ""), section_id=int(sec.get("id") or 0)))
    fin_tams = []
    if financial_section:
        fin_tams = extract_tam_mentions(str(financial_section.get("body_markdown") or ""), section_id=62)

    all_tams = draft_tams + fin_tams
    if len(all_tams) < 2:
        return ""

    conflicts = (audit or {}).get("tam_conflicts") or _tam_conflicts(all_tams)
    conflict_keys = {c["label_key"] for c in conflicts}

    lines = [
        "",
        "### Financial ledger — TAM reconciliation (cross-pass)",
        "",
        "| Status | Source | Metric | Stated figure | Notes |",
        "|---|---|---|---|---|",
    ]
    for row in draft_tams[:8]:
        key = row.get("label_key")
        status = "**CONFLICT**" if key in conflict_keys else "bridge"
        lines.append(
            f"| {status} | §{row.get('section_id')} draft | {row.get('label_key')} | "
            f"{row.get('amount')} {row.get('unit') or ''} | Sonar draft pass |"
        )
    for row in fin_tams[:8]:
        key = row.get("label_key")
        status = "**CONFLICT**" if key in conflict_keys else "align"
        lines.append(
            f"| {status} | §62 financial | {row.get('label_key')} | "
            f"{row.get('amount')} {row.get('unit') or ''} | Opus financial table pass |"
        )
    for c in conflicts:
        lines.append(
            f"| **bridge** | cross-pass | {c['label_key']} | "
            f"{format_display_number(float(c['low']))} – {format_display_number(float(c['high']))} | "
            "Methodology differs (>5%); pick one for investor deck |"
        )
    lines.extend(
        [
            "",
            "**How to read this:** `bridge` = different methodology, not necessarily wrong. "
            "`CONFLICT` = same metric label with >5% numeric spread — reconcile before citing externally. "
            "Prefer **[DERIVED]** bottom-up math only when the formula line passes the 5% check.",
            "",
        ]
    )
    return "\n".join(lines)


def build_pricing_footnote(sections: list[dict[str, Any]], *, audit: dict[str, Any] | None = None) -> str:
    """Cross-section footnote when pricing tiers differ by source."""
    pricing_rows: list[dict[str, Any]] = []
    if audit and audit.get("pricing_mentions"):
        pricing_rows = list(audit["pricing_mentions"])
    else:
        for sec in sections:
            sid = int(sec.get("id") or 0)
            body = str(sec.get("body_markdown") or "")
            pricing_rows.extend(extract_pricing_mentions(body, section_id=sid))
    conflicts = (audit or {}).get("pricing_conflicts") or _pricing_conflicts(pricing_rows)
    if not conflicts:
        return ""

    lines = [
        "",
        "### Pricing note (cross-section)",
        "",
        "The report cites **different price points for the same tier** depending on source section:",
        "",
    ]
    for c in conflicts:
        tier = c.get("tier", "tier")
        sources = ", ".join(f"§{r.get('section_id')}" for r in c.get("rows") or [])
        lines.append(
            f"- **{tier}**: {c['low']:.2g} – {c['high']:.2g} (×{c['ratio']}) across {sources or 'sections'}. "
            "Verify against official pricing pages before quoting."
        )
    lines.append("")
    return "\n".join(lines)


def apply_pricing_footnotes(sections: list[dict[str, Any]], *, audit: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Append pricing footnote to the first section that mentions conflicting pricing."""
    footnote = build_pricing_footnote(sections, audit=audit)
    if not footnote:
        return sections
    out: list[dict[str, Any]] = []
    placed = False
    conflict_sids = {
        int(r.get("section_id") or 0)
        for c in (audit or {}).get("pricing_conflicts") or []
        for r in c.get("rows") or []
    }
    for sec in sections:
        row = dict(sec)
        sid = int(row.get("id") or 0)
        if not placed and sid in conflict_sids:
            row["body_markdown"] = str(row.get("body_markdown") or "") + footnote
            placed = True
        out.append(row)
    if not placed and out:
        out[-1]["body_markdown"] = str(out[-1].get("body_markdown") or "") + footnote
    return out


def sanitize_section_commentary(section: dict[str, Any]) -> dict[str, Any]:
    row = dict(section)
    for key in ("what_this_means", "how_to_use", "key_insights"):
        vals = row.get(key)
        if isinstance(vals, list):
            row[key] = [sanitize_analyst_bullet(str(v)) for v in vals if str(v).strip()]
    return row
