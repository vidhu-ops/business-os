"""Persistent store for verified evidence rows fetched from official/trusted APIs."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STORE_ROOT = Path(__file__).resolve().parent / "data" / "verified_stores"


def _cache_key(topic: str, industry: str, geography: str) -> str:
    raw = f"{topic.strip().lower()}|{industry.strip().lower()}|{geography.strip().lower()}"
    slug = re.sub(r"[^a-z0-9]+", "_", f"{topic}_{geography}"[:48].lower()).strip("_")
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]
    return f"{slug or 'market'}_{digest}"


def store_path(topic: str, industry: str, geography: str) -> Path:
    STORE_ROOT.mkdir(parents=True, exist_ok=True)
    return STORE_ROOT / f"{_cache_key(topic, industry, geography)}.jsonl"


def _row_fingerprint(row: dict[str, Any]) -> str:
    parts = [
        str(row.get("url") or ""),
        str(row.get("record_type") or ""),
        str(row.get("metric_name") or ""),
        str(row.get("metric_value") or row.get("verified_price") or ""),
        str(row.get("name") or ""),
    ]
    return hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:20]


def _normalize_stored_row(row: dict[str, Any], *, topic: str, industry: str, geography: str) -> dict[str, Any]:
    out = dict(row)
    out.setdefault("stored_at", datetime.now(timezone.utc).isoformat())
    out.setdefault("topic", topic)
    out.setdefault("industry", industry)
    out.setdefault("geography", geography)
    return out


def load_stored_rows(topic: str, industry: str, geography: str) -> list[dict[str, Any]]:
    path = store_path(topic, industry, geography)
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            if isinstance(row, dict):
                rows.append(row)
        except json.JSONDecodeError:
            continue
    return rows


def persist_rows(
    topic: str,
    industry: str,
    geography: str,
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Append new verified rows; dedupe by fingerprint. Returns store metadata."""
    path = store_path(topic, industry, geography)
    existing = load_stored_rows(topic, industry, geography)
    seen = {_row_fingerprint(r) for r in existing}
    added = 0
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        for raw in rows:
            if not isinstance(raw, dict):
                continue
            fp = _row_fingerprint(raw)
            if fp in seen:
                continue
            seen.add(fp)
            fh.write(json.dumps(_normalize_stored_row(raw, topic=topic, industry=industry, geography=geography), ensure_ascii=False))
            fh.write("\n")
            added += 1
    total = len(load_stored_rows(topic, industry, geography))
    return {"store_id": path.name, "rows_added": added, "rows_total": total}


def merge_harvest_into_store(
    topic: str,
    industry: str,
    geography: str,
    harvest_rows: list[dict[str, Any]],
    bank_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Persist both raw harvest payloads and normalised bank rows."""
    to_store: list[dict[str, Any]] = []
    for r in harvest_rows:
        if isinstance(r, dict) and r.get("url"):
            to_store.append({
                "name": r.get("name"),
                "record_type": r.get("record_type"),
                "publisher": r.get("publisher"),
                "url": r.get("url"),
                "metric_name": (r.get("extracted_metrics") or [{}])[0].get("metric") if r.get("extracted_metrics") else "source_reference",
                "metric_value": (r.get("extracted_metrics") or [{}])[0].get("value") if r.get("extracted_metrics") else r.get("snippet", "")[:180],
                "verification_status": r.get("verification_status"),
                "source_tier": r.get("source_tier"),
                "retrieval_provider": r.get("retrieval_provider"),
                "tier": "tier1_verified",
            })
    for r in bank_rows:
        if isinstance(r, dict) and r.get("url"):
            to_store.append(dict(r))
    return persist_rows(topic, industry, geography, to_store)
