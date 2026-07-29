"""IIDATECH proprietary competitor intelligence bank API."""
from __future__ import annotations
from typing import Any
from iidatech.evidence_bank.bank_store import (
    BANK_DIR,
    DOMAIN_BANK_FILES,
    bank_row_to_learned_record,
    load_jsonl_bank,
    resolve_bank_file,
    search_competitor_bank,
)

COMPETITOR_ROW_FIELDS = (
    "industry", "company_name", "country", "category", "positioning", "pricing", "metrics",
    "strengths", "weaknesses", "complaints", "gtm_model", "trust_score", "source_urls", "source_type", "last_verified",
)


def validate_competitor_row(row: dict[str, Any]) -> list[str]:
    missing = [f for f in COMPETITOR_ROW_FIELDS if f not in row or row.get(f) in (None, "", [])]
    return missing


def get_competitor_bank(domain: str) -> list[dict[str, Any]]:
    return load_jsonl_bank(resolve_bank_file(domain))


def build_competitor_bank_hits(domain: str, topic: str, target: str, limit: int = 12) -> list[dict[str, Any]]:
    return search_competitor_bank(domain, topic, target, limit=limit)