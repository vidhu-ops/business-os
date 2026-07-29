"""IIDATECH LLM usage policy - routing gates, token budgets, context compression."""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Any

class ModelTier:
    NONE = 0
    CHEAP = 1
    PREMIUM = 2

STAGE_TOKEN_BUDGETS: dict[str, tuple[int, int]] = {
    "section_synthesis": (4000, 1000),
    "boardroom": (12000, 2000),
    "business_strategist": (16000, 3000),
    "cheap_formatting": (8000, 1500),
    "cheap_summary": (8000, 1500),
}

REPORT_TOKEN_SOFT_CAP = 100_000
REPORT_TOKEN_HARD_CAP = 150_000
MAX_PREMIUM_CALLS_PER_REPORT = 3

PREMIUM_ALLOWED_STAGES = frozenset({
    "boardroom_strategist", "boardroom", "business_strategist",
    "investor_verdict", "final_business_plan_critique", "final_audit",
})

PREMIUM_BLOCKED_STAGES = frozenset({
    "verification", "scoring", "formatting", "json_repair", "evidence_selection",
    "evidence_ranking", "trust_scoring", "competitor_dedupe", "pricing_extraction",
    "citation_validation", "numeric_verification", "tam_sam_som_math",
    "unit_economics_calc", "schema_validation", "financial_sanity",
    "section_scoring", "contradiction_rules", "audit_scoring",
})

EVIDENCE_PRIORITY = (
    "official_filings", "official_pricing_page", "competitor_intelligence",
    "benchmark_bank", "analyst_report", "review_platform", "reddit_practitioner", "blog",
)


def _extra_premium_allowed() -> bool:
    return os.getenv("IIDATECH_ALLOW_EXTRA_PREMIUM_CALLS", "0").strip().lower() in {"1", "true", "yes", "on"}


def should_use_premium_model(stage: str, *, complexity_score: float = 0.0) -> bool:
    key = (stage or "").strip().lower()
    if key in PREMIUM_BLOCKED_STAGES:
        return False
    if key in PREMIUM_ALLOWED_STAGES:
        return True
    return False


def get_stage_token_budget(stage: str) -> tuple[int, int]:
    return STAGE_TOKEN_BUDGETS.get((stage or "").strip().lower(), STAGE_TOKEN_BUDGETS["cheap_formatting"])


def _estimate_tokens(text: str) -> int:
    return max(1, len(str(text or "")) // 4)


def truncate_to_token_budget(text: str, max_tokens: int) -> str:
    max_chars = max(200, int(max_tokens) * 4)
    blob = str(text or "")
    if len(blob) <= max_chars:
        return blob
    return blob[: max_chars - 20] + "\n...[truncated]"


@dataclass
class LLMCallProposal:
    stage: str
    tier: int
    why_llm_needed: str
    why_python_insufficient: str
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0

    def validate(self) -> tuple[bool, str]:
        return validate_llm_call_proposal(
            stage=self.stage, tier=self.tier,
            why_llm_needed=self.why_llm_needed,
            why_python_insufficient=self.why_python_insufficient,
            estimated_input_tokens=self.estimated_input_tokens,
            estimated_output_tokens=self.estimated_output_tokens,
        )


def validate_llm_call_proposal(
    *, stage: str, tier: int, why_llm_needed: str, why_python_insufficient: str,
    estimated_input_tokens: int = 0, estimated_output_tokens: int = 0,
) -> tuple[bool, str]:
    if not str(why_llm_needed or "").strip():
        return False, "LLM call rejected: missing why_llm_needed"
    if not str(why_python_insufficient or "").strip():
        return False, "LLM call rejected: missing why_python_insufficient"
    if tier == ModelTier.NONE:
        return False, "LLM call rejected: tier is NONE - use Python"
    if tier == ModelTier.PREMIUM and not should_use_premium_model(stage):
        return False, f"LLM call rejected: premium blocked for stage={stage!r}"
    max_in, max_out = get_stage_token_budget(stage)
    if estimated_input_tokens > max_in:
        return False, f"LLM call rejected: input budget {estimated_input_tokens} > {max_in}"
    if estimated_output_tokens > max_out:
        return False, f"LLM call rejected: output budget {estimated_output_tokens} > {max_out}"
    return True, "ok"


@dataclass
class ReportTokenLedger:
    used_tokens: int = 0
    premium_calls: int = 0
    calls: list[dict[str, Any]] = field(default_factory=list)

    def can_use_premium(self, stage: str) -> tuple[bool, str]:
        if not should_use_premium_model(stage):
            return False, f"premium not allowed for stage={stage!r}"
        if self.premium_calls >= MAX_PREMIUM_CALLS_PER_REPORT and not _extra_premium_allowed():
            return False, f"premium call cap reached ({MAX_PREMIUM_CALLS_PER_REPORT}/report)"
        if self.used_tokens >= REPORT_TOKEN_HARD_CAP:
            return False, f"report hard token cap reached ({REPORT_TOKEN_HARD_CAP})"
        return True, "ok"

    def record(self, *, stage: str, tier: int, input_text: str = "", output_text: str = "", model: str = "") -> None:
        inp, out = _estimate_tokens(input_text), _estimate_tokens(output_text)
        self.used_tokens += inp + out
        if tier == ModelTier.PREMIUM:
            self.premium_calls += 1
        self.calls.append({"stage": stage, "tier": tier, "model": model, "input_tokens_est": inp, "output_tokens_est": out, "total_used": self.used_tokens})

    def over_soft_cap(self) -> bool:
        return self.used_tokens >= REPORT_TOKEN_SOFT_CAP


def _evidence_key(record: dict[str, Any]) -> str:
    url = str(record.get("url") or record.get("source_url") or "")
    title = str(record.get("title") or record.get("company_name") or "")
    return hashlib.md5(f"{url}|{title}".encode("utf-8", errors="ignore")).hexdigest()


def _evidence_priority_score(record: dict[str, Any]) -> int:
    family = str(record.get("source_family") or record.get("source_type") or "").lower()
    for idx, label in enumerate(EVIDENCE_PRIORITY):
        if label in family or family in label:
            return idx
    return len(EVIDENCE_PRIORITY)


def compress_evidence_for_llm(records: list[dict[str, Any]], *, max_items: int = 24) -> list[dict[str, Any]]:
    if not records:
        return []
    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for row in records:
        if not isinstance(row, dict):
            continue
        key = _evidence_key(row)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    deduped.sort(key=lambda r: (_evidence_priority_score(r), -float(r.get("confidence") or r.get("trust_score") or 0)))
    return [
        {
            "claim": str(r.get("title") or r.get("company_name") or "")[:200],
            "source": str(r.get("url") or (r.get("source_urls") or [""])[0] if isinstance(r.get("source_urls"), list) else "")[:240],
            "family": str(r.get("source_family") or r.get("source_type") or ""),
            "confidence": float(r.get("confidence") or r.get("trust_score") or 0),
            "text": truncate_to_token_budget(str(r.get("text") or r.get("snippet") or ""), 120),
        }
        for r in deduped[:max_items]
    ]


def compress_text_for_llm(text: str, *, stage: str = "cheap_formatting") -> str:
    max_in, _ = get_stage_token_budget(stage)
    return truncate_to_token_budget(text, max_in)


def assert_premium_call_allowed(stage: str, ledger: ReportTokenLedger | None = None) -> None:
    if not should_use_premium_model(stage):
        raise ValueError(f"IIDATECH policy: premium model blocked for stage={stage!r}")
    if ledger is not None:
        ok, reason = ledger.can_use_premium(stage)
        if not ok:
            raise ValueError(f"IIDATECH policy: {reason}")