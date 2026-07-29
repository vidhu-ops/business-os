"""Shared ChromaDB path resolution for IIDATECH vector collections."""

from __future__ import annotations

import os
from pathlib import Path

try:
    import chromadb
except ImportError:  # pragma: no cover
    chromadb = None

APP_DIR = Path(__file__).resolve().parent

REAL_EVIDENCE_COLLECTION = "iidatech_evidence_records"
SYNTHETIC_MODEL_COLLECTION = "iidatech_synthetic_models"


def chroma_db_path() -> Path:
    path = Path(os.getenv("IIDATECH_CHROMA_PATH", str(APP_DIR / "vectordb")))
    path.mkdir(parents=True, exist_ok=True)
    return path


def chroma_persistent_client() -> "chromadb.PersistentClient":
    if chromadb is None:
        raise ImportError("chromadb is not installed")
    return chromadb.PersistentClient(path=str(chroma_db_path()))
