"""Embedding backend for IIDATECH retrieval (hash trigrams + optional OpenAI)."""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.error
import urllib.request

EMBEDDING_BACKEND = "hash_trigram"
EMBEDDING_VERSION = "hash-v1"
EMBEDDING_DIM = 384
OPENAI_EMBED_MODEL = "text-embedding-3-small"


def _clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _hash_embed(text: str, *, dim: int = EMBEDDING_DIM) -> list[float]:
    """MD5 character trigram hash embedding (384-dim, L2-normalized)."""
    normalized = _clean_text(text).lower()[:4000]
    vec = [0.0] * dim
    if len(normalized) < 3:
        return vec
    for i in range(len(normalized) - 2):
        digest = hashlib.md5(normalized[i : i + 3].encode("utf-8", errors="ignore")).hexdigest()
        vec[int(digest, 16) % dim] += 1.0
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def _openai_embed(text: str) -> list[float] | None:
    key = os.getenv("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    payload = json.dumps({"model": OPENAI_EMBED_MODEL, "input": _clean_text(text)[:8000]}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8", errors="ignore"))
        vec = data.get("data", [{}])[0].get("embedding")
        if not isinstance(vec, list) or not vec:
            return None
        # Project OpenAI vector into fixed dim for SQL storage consistency.
        out = [0.0] * EMBEDDING_DIM
        for i, val in enumerate(vec):
            out[i % EMBEDDING_DIM] += float(val)
        norm = math.sqrt(sum(v * v for v in out)) or 1.0
        return [v / norm for v in out]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, ValueError):
        return None


def embed_text(text: str, *, dim: int = EMBEDDING_DIM) -> list[float]:
    vec, _ = embed_text_with_model(text, dim=dim)
    return vec


def embed_text_with_model(text: str, *, dim: int = EMBEDDING_DIM) -> tuple[list[float], str]:
    openai_vec = _openai_embed(text)
    if openai_vec:
        return openai_vec, OPENAI_EMBED_MODEL
    return _hash_embed(text, dim=dim), EMBEDDING_VERSION
