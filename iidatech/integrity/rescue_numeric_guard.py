"""Claude full-report rescue numeric guard (P0.3)."""
from __future__ import annotations

import json
import re
from typing import Any

NUMERIC_CLAIM_RE = re.compile(
    r"\$?\d+(?:\.\d+)?\s*(?:percent|percentage points|CAGR|customers|users|seats|licenses|"
    r"thousand|million|billion|bn|%|m(?=\W|$)|b(?=\W|$)|k(?=\W|$))"
    r"(?:\s*(?:CAGR|customers|users|seats|licenses))?",
    flags=re.IGNORECASE,
)

_HARD_FINANCIAL_RE = re.compile(
    r"(?:billion|million|bn|cagr|%|\d+b(?=\W|$)|\d+m(?=\W|$))",
    flags=re.IGNORECASE,
)

_ALLOWED_AUDIT_DECISIONS = {"VERIFIED HARD FIGURE"}
_ESTIMATED_AUDIT_DECISION = "ESTIMATED / USE WITH LIMITATION"
_REDACTION_TEXT = "PRIMARY RESEARCH REQUIRED: source-backed value not available"


def normalize_numeric_claim(token: str) -> str:
    normalized = token.lower().replace(" ", "").replace(",", "")
    normalized = normalized.replace("billion", "b")
    normalized = normalized.replace("million", "m")
    normalized = normalized.replace("thousand", "k")
    normalized = normalized.replace("percent", "%")
    normalized = normalized.replace("percentagepoints", "pp")
    normalized = normalized.replace("customers", "users")
    normalized = normalized.replace("licenses", "seats")
    return normalized


def _token_key(token: str) -> str:
    return normalize_numeric_claim(token).lower().replace(" ", "")


def is_hard_financial_token(normalized_key: str) -> bool:
    if not normalized_key or re.fullmatch(r"20\d\d", normalized_key):
        return False
    return bool(_HARD_FINANCIAL_RE.search(normalized_key))


def _extract_prompt_json_block(prompt: str, label: str) -> dict[str, Any]:
    match = re.search(
        rf"=== {re.escape(label)} ===\n(.+?)\n=== END {re.escape(label)} ===",
        prompt,
        flags=re.DOTALL,
    )
    if not match:
        return {}
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def _extract_prompt_block_text(prompt: str, labels: list[str]) -> str:
    chunks: list[str] = []
    for label in labels:
        match = re.search(
            rf"=== {re.escape(label)} ===\n(.+?)\n=== END {re.escape(label)} ===",
            prompt,
            flags=re.DOTALL,
        )
        if match:
            chunks.append(match.group(1))
    return "\n".join(chunks)


def _numbers_from_text(text: str) -> set[str]:
    return {_token_key(match.group(0)) for match in NUMERIC_CLAIM_RE.finditer(text or "")}


def _numbers_from_metric_string(metric: str) -> set[str]:
    return _numbers_from_text(metric)


def _allowlist_from_database_brief(brief: dict[str, Any]) -> set[str]:
    allowed: set[str] = set()
    if not isinstance(brief, dict):
        return allowed
    rows = brief.get("top_records")
    if not isinstance(rows, list):
        deterministic = brief.get("deterministic")
        if isinstance(deterministic, dict):
            rows = deterministic.get("top_records")
    if not isinstance(rows, list):
        return allowed
    for row in rows:
        if not isinstance(row, dict):
            continue
        allowed |= _numbers_from_metric_string(str(row.get("metric") or ""))
        for point in row.get("data_points") or []:
            allowed |= _numbers_from_text(str(point))
    return allowed


def _allowlist_from_strict_pack(pack: dict[str, Any], *, allow_estimated: bool) -> set[str]:
    allowed: set[str] = set()
    if not isinstance(pack, dict):
        return allowed
    decisions = set(_ALLOWED_AUDIT_DECISIONS)
    if allow_estimated:
        decisions.add(_ESTIMATED_AUDIT_DECISION)
    for table_key in ("numeric_audit_table", "ten_check_details"):
        rows = pack.get(table_key)
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict):
                continue
            if str(row.get("decision") or "") not in decisions:
                continue
            allowed |= _numbers_from_metric_string(str(row.get("metric") or ""))
    return allowed


def build_rescue_numeric_allowlist(prompt: str, *, allow_estimated: bool = True) -> set[str]:
    allowed: set[str] = set()
    allowed |= _numbers_from_text(
        _extract_prompt_block_text(prompt, ["RESEARCH DATA", "RETRIEVED RESEARCH DATA"])
    )
    allowed |= _numbers_from_text(
        _extract_prompt_block_text(prompt, ["QUANTITATIVE MODEL", "STRICT MARKET MODEL"])
    )
    for label in ("DATABASE EVIDENCE BRIEF", "DATABASE EVIDENCE ANALYST BRIEF"):
        allowed |= _allowlist_from_database_brief(_extract_prompt_json_block(prompt, label))
    strict_pack = _extract_prompt_json_block(prompt, "STRICT VERIFICATION PACK")
    allowed |= _allowlist_from_strict_pack(strict_pack, allow_estimated=allow_estimated)
    diligence = _extract_prompt_json_block(prompt, "INVESTMENT DILIGENCE PACK")
    nested = diligence.get("strict_verification_pack") if isinstance(diligence, dict) else {}
    if isinstance(nested, dict):
        allowed |= _allowlist_from_strict_pack(nested, allow_estimated=allow_estimated)
    return {token for token in allowed if token}


def build_rescue_strict_allowlist(prompt: str, *, allow_estimated: bool = True) -> set[str]:
    allowed: set[str] = set()
    for label in ("DATABASE EVIDENCE BRIEF", "DATABASE EVIDENCE ANALYST BRIEF"):
        allowed |= _allowlist_from_database_brief(_extract_prompt_json_block(prompt, label))
    strict_pack = _extract_prompt_json_block(prompt, "STRICT VERIFICATION PACK")
    allowed |= _allowlist_from_strict_pack(strict_pack, allow_estimated=allow_estimated)
    diligence = _extract_prompt_json_block(prompt, "INVESTMENT DILIGENCE PACK")
    nested = diligence.get("strict_verification_pack") if isinstance(diligence, dict) else {}
    if isinstance(nested, dict):
        allowed |= _allowlist_from_strict_pack(nested, allow_estimated=allow_estimated)
    return {token for token in allowed if token}


def apply_rescue_funding_strict_redaction(
    text: str,
    strict_allowed: set[str],
) -> tuple[str, int]:
    redacted = 0

    def repl(match: re.Match[str]) -> str:
        nonlocal redacted
        token = match.group(0)
        key = _token_key(token)
        if not is_hard_financial_token(key):
            return token
        if key in strict_allowed:
            return token
        redacted += 1
        return _REDACTION_TEXT

    return NUMERIC_CLAIM_RE.sub(repl, text), redacted


def build_rescue_guard_status(
    *,
    allowed_count: int,
    strict_allowed_count: int,
    numeric_redaction_applied: bool,
    funding_strict_applied: bool,
    funding_strict_redacted: int,
) -> dict[str, Any]:
    return {
        "schema_version": "rescue_numeric_guard.v1",
        "allowed_token_count": allowed_count,
        "strict_allowed_token_count": strict_allowed_count,
        "numeric_redaction_applied": bool(numeric_redaction_applied),
        "funding_strict_applied": bool(funding_strict_applied),
        "funding_strict_redacted": int(funding_strict_redacted),
    }