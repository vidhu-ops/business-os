"""Cluster and deduplicate evidence records for retrieval."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

_TOKEN_RE = re.compile(r"[a-z0-9]{3,}")


def _norm_url(url: str) -> str:
    raw = str(url or "").strip().lower()
    if not raw:
        return ""
    if not raw.startswith("http"):
        return raw
    parsed = urlparse(raw)
    host = parsed.netloc.lower().removeprefix("www.")
    path = parsed.path.rstrip("/")
    return f"{host}{path}"


def _title_tokens(record: dict[str, Any]) -> set[str]:
    title = str(record.get("title") or record.get("publisher") or "")
    return set(_TOKEN_RE.findall(title.lower()))


def _token_overlap(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


def _confidence(record: dict[str, Any]) -> float:
    for key in ("confidence", "quality_score", "source_truth_score", "truth_augmented_score"):
        val = record.get(key)
        if val is not None:
            try:
                score = float(val)
                return score / 100.0 if score > 1.5 else score
            except (TypeError, ValueError):
                continue
    return 0.5


def _same_cluster(a: dict[str, Any], b: dict[str, Any]) -> bool:
    url_a, url_b = _norm_url(a.get("url") or ""), _norm_url(b.get("url") or "")
    if url_a and url_b and url_a == url_b:
        return True
    overlap = _token_overlap(_title_tokens(a), _title_tokens(b))
    return overlap >= 0.55


def cluster_evidence_records(records: list[dict[str, Any]], max_items: int = 12) -> list[dict[str, Any]]:
    """Dedupe by URL/title overlap; keep highest-confidence record per cluster."""
    clusters: list[list[dict[str, Any]]] = []
    for row in records or []:
        if not isinstance(row, dict):
            continue
        placed = False
        for cluster in clusters:
            if _same_cluster(cluster[0], row):
                cluster.append(row)
                placed = True
                break
        if not placed:
            clusters.append([row])

    ranked: list[dict[str, Any]] = []
    for cluster in clusters:
        best = max(cluster, key=_confidence)
        best = dict(best)
        best["_cluster_size"] = len(cluster)
        best["_cluster_confidence"] = round(_confidence(best), 4)
        ranked.append(best)

    ranked.sort(key=lambda r: float(r.get("_cluster_confidence") or 0), reverse=True)
    return ranked[: max(1, int(max_items))]