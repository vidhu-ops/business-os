"""IIDATECH runtime evidence retrieval."""

from iidatech.retrieval.embedding import EMBEDDING_BACKEND, EMBEDDING_DIM, EMBEDDING_VERSION, embed_text
from iidatech.retrieval.evidence_query import evidence_vector_index_ready, query_evidence_bank
from iidatech.retrieval.report_selection_trace import (
    build_report_selection_trace,
    emit_report_selection_trace,
    get_report_selection_trace,
    report_selection_trace_enabled,
    reset_report_selection_trace,
)
from iidatech.retrieval.record_trace import (
    build_record_acceptance_trace,
    flush_record_acceptance_trace,
    get_record_acceptance_trace,
    record_trace_enabled,
    reset_record_acceptance_trace,
    trace_record_stage,
)
from iidatech.retrieval.industry_planner import (
    build_industry_queries,
    competitor_intelligence_gate,
    get_industry_retrieval_profile,
    industry_query_actions,
    select_section_industry_queries,
)
from iidatech.retrieval.metrics import RetrievalEvent, log_evidence_retrieval_event
from iidatech.retrieval.query_builder import (
    RETRIEVAL_QUERY_TEMPLATES,
    SECTION_RETRIEVAL_FAMILY,
    build_evidence_retrieval_query,
    section_retrieval_family,
)
from iidatech.retrieval.source_trust import (
    annotate_truth_fields,
    apply_truth_weighting,
    compute_source_truth_score,
    data_truth_layer_enabled,
    get_source_trust_tier,
    summarize_truth_quality,
    truth_augmented_rank_score,
)

__all__ = [
    "EMBEDDING_BACKEND",
    "EMBEDDING_DIM",
    "EMBEDDING_VERSION",
    "RETRIEVAL_QUERY_TEMPLATES",
    "SECTION_RETRIEVAL_FAMILY",
    "RetrievalEvent",
    "build_evidence_retrieval_query",
    "build_industry_queries",
    "build_record_acceptance_trace",
    "build_report_selection_trace",
    "emit_report_selection_trace",
    "get_report_selection_trace",
    "report_selection_trace_enabled",
    "reset_report_selection_trace",
    "competitor_intelligence_gate",
    "embed_text",
    "evidence_vector_index_ready",
    "flush_record_acceptance_trace",
    "get_industry_retrieval_profile",
    "get_record_acceptance_trace",
    "industry_query_actions",
    "log_evidence_retrieval_event",
    "query_evidence_bank",
    "record_trace_enabled",
    "reset_record_acceptance_trace",
    "section_retrieval_family",
    "select_section_industry_queries",
    "trace_record_stage",
    "annotate_truth_fields",
    "apply_truth_weighting",
    "compute_source_truth_score",
    "data_truth_layer_enabled",
    "get_source_trust_tier",
    "summarize_truth_quality",
    "truth_augmented_rank_score",
]
