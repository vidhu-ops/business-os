"""Evidence namespace helpers for IIDATECH PR1-B.

The real evidence namespace can support investor retrieval, citation, and
numeric evidence subject to trust/relevance gates. The synthetic model
namespace is reserved for planning and forecasts and must never be treated as
verified investor evidence.

All functions are pure. No Streamlit. No app.py imports. No side effects.
"""
from __future__ import annotations

from typing import Any

REAL_EVIDENCE_NAMESPACE = "real_evidence"
SYNTHETIC_MODEL_NAMESPACE = "synthetic_model"

SOURCE_TYPE_REAL_EVIDENCE = "real_evidence"
SOURCE_TYPE_SYNTHETIC_MODEL = "synthetic_model"

SYNTHETIC_MODEL_FAMILIES: frozenset[str] = frozenset({
    "iidatech_2026_financial_model_bank",
    "financial_model_bank",
    "synthetic_model",
    "primary_research_plan",
    "industry_pack_primary_research",
    "industry_pack_benchmark",
})


def evidence_namespace_for_record(record: dict[str, Any]) -> str:
    """Return the canonical evidence namespace for a record."""
    explicit = str(record.get("evidence_namespace") or "").strip().lower()
    if explicit in {REAL_EVIDENCE_NAMESPACE, SYNTHETIC_MODEL_NAMESPACE}:
        return explicit

    family = str(
        record.get("source_family")
        or record.get("source_type")
        or record.get("family")
        or ""
    ).lower()
    url = str(record.get("url") or record.get("source_url") or "").strip().lower()
    if family in SYNTHETIC_MODEL_FAMILIES or url.startswith("internal://"):
        return SYNTHETIC_MODEL_NAMESPACE
    return REAL_EVIDENCE_NAMESPACE


def namespace_permissions(namespace: str) -> dict[str, bool]:
    """Return immutable-style permission flags for an evidence namespace."""
    if namespace == SYNTHETIC_MODEL_NAMESPACE:
        return {
            "retrieval_allowed": False,
            "citation_allowed": False,
            "numeric_evidence_allowed": False,
            "scenario_planning_allowed": True,
            "forecasting_allowed": True,
            "verified_allowed": False,
            "investor_evidence_allowed": False,
        }
    return {
        "retrieval_allowed": True,
        "citation_allowed": True,
        "numeric_evidence_allowed": True,
        "scenario_planning_allowed": False,
        "forecasting_allowed": False,
        "verified_allowed": True,
        "investor_evidence_allowed": True,
    }


def namespace_schema_fields(record: dict[str, Any]) -> dict[str, Any]:
    """Return namespace fields to stamp onto index rows."""
    namespace = evidence_namespace_for_record(record)
    permissions = namespace_permissions(namespace)
    return {
        "evidence_namespace": namespace,
        "source_type": (
            SOURCE_TYPE_SYNTHETIC_MODEL
            if namespace == SYNTHETIC_MODEL_NAMESPACE
            else SOURCE_TYPE_REAL_EVIDENCE
        ),
        **permissions,
    }


def is_synthetic_namespace(record: dict[str, Any]) -> bool:
    """Return True when a record belongs to the synthetic model namespace."""
    return evidence_namespace_for_record(record) == SYNTHETIC_MODEL_NAMESPACE
