"""IIDATECH proprietary evidence datasets."""
from iidatech.proprietary_data.industry_map import resolve_vertical, VERTICALS
from iidatech.proprietary_data.loader import (
    bank_row_counts,
    load_proprietary_context,
    query_benchmarks,
    query_buyer_voice,
    query_competitor_pricing,
    query_supplier_costs,
)

__all__ = [
    "VERTICALS",
    "bank_row_counts",
    "load_proprietary_context",
    "query_benchmarks",
    "query_buyer_voice",
    "query_competitor_pricing",
    "query_supplier_costs",
    "resolve_vertical",
]
