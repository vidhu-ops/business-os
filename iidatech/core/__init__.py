"""IIDATECH core -- canonical report compiler, numeric engine, truth arbiter."""
from __future__ import annotations

from iidatech.core.numeric_engine import build_numeric_truth
from iidatech.core.report_compiler import (
    SECTION_BLOCKED,
    SECTION_PARTIAL,
    SECTION_VALID,
    build_canonical_report,
    compile_customer_report,
    compile_execution_report,
    compile_for_mode,
    compile_investor_report,
    validate_canonical_report,
)
from iidatech.core.truth_arbiter import (
    adapt_arbiter_truth_for_compiler,
    build_canonical_truth_object,
    collect_candidate_truths,
    pick_best_truth,
    score_truth_candidates,
    should_block_customer_report,
)

__all__ = [
    "SECTION_BLOCKED",
    "SECTION_PARTIAL",
    "SECTION_VALID",
    "adapt_arbiter_truth_for_compiler",
    "build_canonical_report",
    "build_canonical_truth_object",
    "build_numeric_truth",
    "collect_candidate_truths",
    "compile_customer_report",
    "compile_execution_report",
    "compile_for_mode",
    "compile_investor_report",
    "pick_best_truth",
    "score_truth_candidates",
    "should_block_customer_report",
    "validate_canonical_report",
]
