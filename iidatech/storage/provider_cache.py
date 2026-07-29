"""Cached wrapper for external provider API calls."""
from __future__ import annotations

import time
from typing import Any, Callable

from iidatech.storage.cache_repository import (
    get_cached_search,
    hash_query,
    increment_cache_hit,
    insert_cached_search,
    log_api_cost,
    ttl_hours_for_kind,
    update_provider_stats,
)


def cached_provider_call(
    provider: str,
    query: str,
    cache_kind: str,
    report_id: str,
    fn: Callable[[], Any],
    *,
    model: str = "",
    estimated_cost: float = 0.01,
) -> Any:
    qhash = hash_query(query, provider)
    cached = get_cached_search(qhash, provider)
    if cached is not None:
        increment_cache_hit(qhash, provider)
        update_provider_stats(provider, cache_hit=True)
        return cached.get("result_json")

    started = time.perf_counter()
    result = fn()
    latency_ms = (time.perf_counter() - started) * 1000.0

    ttl = ttl_hours_for_kind(cache_kind)
    insert_cached_search(query, provider, result, ttl)
    log_api_cost(report_id or "", provider, model, 0, 0, estimated_cost)
    update_provider_stats(
        provider,
        cache_miss=True,
        latency_ms=latency_ms,
        cost_usd=estimated_cost,
    )
    return result