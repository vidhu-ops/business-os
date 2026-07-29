"""Runtime vector query over the IIDATECH evidence bank."""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

from chroma_config import REAL_EVIDENCE_COLLECTION, chroma_db_path, chroma_persistent_client
from iidatech.integrity.evidence_namespace import REAL_EVIDENCE_NAMESPACE
from iidatech.retrieval.embedding import EMBEDDING_BACKEND, EMBEDDING_VERSION, embed_text

log = logging.getLogger("iidatech.retrieval")

VECTOR_QUERY_TIMEOUT_MS = int(os.getenv("IIDATECH_VECTOR_QUERY_TIMEOUT_MS", "250"))
VECTOR_TOP_K_DEFAULT = int(os.getenv("IIDATECH_EVIDENCE_VECTOR_TOP_K", "24"))
EVIDENCE_COLLECTION = REAL_EVIDENCE_COLLECTION

_INDEX_LOOKUP_LOCK = threading.Lock()
_INDEX_LOOKUP: dict[str, dict[str, Any]] | None = None
_INDEX_LOOKUP_MTIME: float | None = None

APP_DIR = Path(__file__).resolve().parents[2]
QUALITY_INDEX_JSONL_PATH = APP_DIR / "datasets" / "evidence_quality_index.jsonl"
VECTOR_MANIFEST_PATH = APP_DIR / "datasets" / "evidence_vector_manifest.json"


def load_vector_manifest() -> dict[str, Any]:
    if not VECTOR_MANIFEST_PATH.exists():
        return {}
    try:
        return json.loads(VECTOR_MANIFEST_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def evidence_vector_index_ready() -> bool:
    manifest = load_vector_manifest()
    return (
        manifest.get("status") == "ready"
        and int(manifest.get("record_count", 0) or 0) > 0
    )


def _evidence_quality_lookup() -> dict[str, dict[str, Any]]:
    global _INDEX_LOOKUP, _INDEX_LOOKUP_MTIME
    if not QUALITY_INDEX_JSONL_PATH.exists():
        return {}
    try:
        mtime = QUALITY_INDEX_JSONL_PATH.stat().st_mtime
    except OSError:
        return {}
    with _INDEX_LOOKUP_LOCK:
        if _INDEX_LOOKUP is not None and _INDEX_LOOKUP_MTIME == mtime:
            return _INDEX_LOOKUP
        lookup: dict[str, dict[str, Any]] = {}
        try:
            with QUALITY_INDEX_JSONL_PATH.open("r", encoding="utf-8-sig", errors="ignore") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    record_id = str(row.get("record_id", "")).strip()
                    if record_id:
                        lookup[record_id] = row
        except OSError:
            return {}
        _INDEX_LOOKUP = lookup
        _INDEX_LOOKUP_MTIME = mtime
        return lookup


def _chroma_query_inner(
    query: str,
    top_k: int,
    min_quality_score: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    timing: dict[str, float] = {}
    t0 = time.perf_counter()
    client = chroma_persistent_client()
    try:
        collection = client.get_collection(EVIDENCE_COLLECTION)
    except Exception as exc:
        return [], {
            "collection_count": 0,
            "timing_ms": {"total": round((time.perf_counter() - t0) * 1000, 2)},
            "error_detail": str(exc),
        }
    count = collection.count()
    if count == 0:
        return [], {"collection_count": 0, "timing_ms": {"total": 0.0}}

    t_embed = time.perf_counter()
    query_vector = embed_text(query)
    timing["query_embed"] = round((time.perf_counter() - t_embed) * 1000, 2)

    t_query = time.perf_counter()
    n_results = min(top_k, count)
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=n_results,
        include=["metadatas", "documents", "distances"],
        where={"quality_score": {"$gte": min_quality_score}},
    )
    timing["chroma_query"] = round((time.perf_counter() - t_query) * 1000, 2)

    lookup = _evidence_quality_lookup()
    t_hydrate = time.perf_counter()
    rows: list[dict[str, Any]] = []
    ids = results.get("ids", [[]])[0]
    distances = results.get("distances", [[]])[0]
    for record_id, distance in zip(ids, distances):
        row = dict(lookup.get(str(record_id), {}))
        if not row:
            continue
        if row.get("is_route_only") or row.get("is_synthetic"):
            continue
        if row.get("evidence_namespace") and row.get("evidence_namespace") != REAL_EVIDENCE_NAMESPACE:
            continue
        distance_value = float(distance or 1.0)
        row["_vector_distance"] = distance_value
        row["_vector_similarity"] = max(0.0, 1.0 - distance_value)
        rows.append(row)
    timing["hydrate"] = round((time.perf_counter() - t_hydrate) * 1000, 2)
    timing["total"] = round((time.perf_counter() - t0) * 1000, 2)
    return rows, {
        "collection_count": count,
        "vector_candidates": len(ids),
        "after_hydrate": len(rows),
        "timing_ms": timing,
    }


def query_evidence_bank(
    query: str,
    *,
    top_k: int | None = None,
    min_quality_score: int = 38,
    target: str = "",
    domain: str = "",
    timeout_ms: int | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Vector recall with timeout kill switch. Returns (rows, meta). Fails open with []."""
    del target
    effective_top_k = top_k if top_k is not None else VECTOR_TOP_K_DEFAULT
    effective_timeout_ms = timeout_ms if timeout_ms is not None else VECTOR_QUERY_TIMEOUT_MS
    manifest = load_vector_manifest()
    meta: dict[str, Any] = {
        "ok": False,
        "error": None,
        "timed_out": False,
        "embedding_backend": manifest.get("embedding_backend", EMBEDDING_BACKEND),
        "embedding_version": manifest.get("embedding_version", EMBEDDING_VERSION),
        "chroma_path": str(chroma_db_path()),
        "index": {
            "ready": evidence_vector_index_ready(),
            "manifest_generated_at": manifest.get("generated_at"),
            "collection_count": int(manifest.get("record_count", 0) or 0),
        },
    }
    if not evidence_vector_index_ready():
        meta["error"] = "index_not_ready"
        return [], meta

    t0 = time.perf_counter()
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_chroma_query_inner, query, effective_top_k, min_quality_score)
    try:
        rows, inner_meta = future.result(timeout=effective_timeout_ms / 1000.0)
        meta.update(inner_meta)
        if domain:
            domain_l = domain.strip().lower()
            rows = [row for row in rows if domain_l in [str(d).lower() for d in row.get("domains", [])]]
            meta["after_domain_filter"] = len(rows)
        meta["ok"] = True
        meta["error"] = None
        return rows, meta
    except FuturesTimeoutError:
        meta["timed_out"] = True
        meta["error"] = "vector_timeout"
        meta["timing_ms"] = {"total": round((time.perf_counter() - t0) * 1000, 2)}
        log.warning("Evidence vector query timed out after %sms", effective_timeout_ms)
        return [], meta
    except Exception as exc:
        meta["error"] = "vector_error"
        meta["error_detail"] = str(exc)
        meta["timing_ms"] = {"total": round((time.perf_counter() - t0) * 1000, 2)}
        log.warning("Evidence vector query failed: %s", exc)
        return [], meta
    finally:
        executor.shutdown(wait=False)
