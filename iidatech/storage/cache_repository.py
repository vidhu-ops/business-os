"""Search cache and API cost persistence for IIDATECH provider calls."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any

from iidatech.storage.db import get_backend, get_connection, row_to_dict, sql_placeholder


def _ph() -> str:
    return sql_placeholder()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _parse_dt(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def hash_query(query: str, provider: str) -> str:
    payload = f"{provider.strip().lower()}|{query.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def ttl_hours_for_kind(cache_kind: str) -> int:
    mapping = {
        "competitor_search": 720,
        "pricing_pages": 336,
        "local_businesses": 168,
        "news": 24,
    }
    return mapping.get((cache_kind or "").strip().lower(), 168)


def infer_cache_kind(query: str, provider: str) -> str:
    q = (query or "").lower()
    prov = (provider or "").lower()

    news_markers = ("news", "announcement", "funding", "acquisition", "launch", "partnership")
    if any(marker in q for marker in news_markers):
        return "news"

    pricing_markers = ("pricing", "price", "plans", "subscription", "cost", "site:pricing")
    if any(marker in q for marker in pricing_markers):
        return "pricing_pages"

    local_markers = ("near me", "local", "city:", "in india", "in us", "restaurants", "clinic", "garage")
    if any(marker in q for marker in local_markers):
        return "local_businesses"

    competitor_markers = (
        "competitor", "alternatives", " vs ", "comparison", "g2.com", "capterra",
        "software", "platform", "crm", "saas",
    )
    if prov in {"serpapi", "google"} or any(marker in q for marker in competitor_markers):
        return "competitor_search"

    return "competitor_search"


def get_cached_search(query_hash: str, provider: str) -> dict[str, Any] | None:
    p = _ph()
    sql = (
        f"SELECT query_hash, query, provider, result_json, created_at, expires_at, hit_count "
        f"FROM search_cache WHERE query_hash = {p} AND provider = {p} LIMIT 1"
    )
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, [query_hash, provider])
            row = cur.fetchone()
        finally:
            cur.close()
    if not row:
        return None
    data = row_to_dict(row, drop_id=False)
    expires = _parse_dt(data.get("expires_at"))
    if expires is None or expires <= datetime.now(timezone.utc):
        return None
    raw = data.get("result_json")
    if isinstance(raw, str) and raw:
        try:
            data["result_json"] = json.loads(raw)
        except json.JSONDecodeError:
            pass
    elif raw is None:
        data["result_json"] = {}
    return data


def insert_cached_search(
    query: str,
    provider: str,
    result_json: Any,
    ttl_hours: int,
) -> str:
    qhash = hash_query(query, provider)
    expires = datetime.now(timezone.utc) + timedelta(hours=max(1, int(ttl_hours)))
    expires_iso = expires.replace(microsecond=0).isoformat()
    payload = json.dumps(result_json, ensure_ascii=False, default=str)
    p = _ph()
    backend = get_backend()

    if backend == "postgres":
        sql = (
            f"INSERT INTO search_cache (query_hash, query, provider, result_json, expires_at) "
            f"VALUES ({p}, {p}, {p}, {p}::jsonb, {p}) "
            f"ON CONFLICT (query_hash) DO UPDATE SET "
            f"query = EXCLUDED.query, provider = EXCLUDED.provider, result_json = EXCLUDED.result_json, "
            f"expires_at = EXCLUDED.expires_at, created_at = NOW(), hit_count = 0"
        )
        params: list[Any] = [qhash, query, provider, payload, expires_iso]
    else:
        sql = (
            f"INSERT INTO search_cache (query_hash, query, provider, result_json, expires_at) "
            f"VALUES ({p}, {p}, {p}, {p}, {p}) "
            f"ON CONFLICT(query_hash) DO UPDATE SET "
            f"query = excluded.query, provider = excluded.provider, result_json = excluded.result_json, "
            f"expires_at = excluded.expires_at, created_at = datetime('now'), hit_count = 0"
        )
        params = [qhash, query, provider, payload, expires_iso]

    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
        finally:
            cur.close()
    return qhash


def increment_cache_hit(query_hash: str, provider: str) -> None:
    p = _ph()
    sql = (
        f"UPDATE search_cache SET hit_count = COALESCE(hit_count, 0) + 1 "
        f"WHERE query_hash = {p} AND provider = {p}"
    )
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, [query_hash, provider])
        finally:
            cur.close()


def log_api_cost(
    report_id: str,
    provider: str,
    model: str,
    in_tokens: int,
    out_tokens: int,
    cost_usd: float,
) -> None:
    p = _ph()
    sql = (
        f"INSERT INTO api_cost_log (report_id, provider, model, tokens_input, tokens_output, cost_usd) "
        f"VALUES ({p}, {p}, {p}, {p}, {p}, {p})"
    )
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, [
                report_id or "",
                provider,
                model or "",
                int(in_tokens or 0),
                int(out_tokens or 0),
                float(cost_usd or 0.0),
            ])
        finally:
            cur.close()


def update_provider_stats(
    provider: str,
    *,
    cache_hit: bool = False,
    cache_miss: bool = False,
    latency_ms: float = 0,
    cost_usd: float = 0,
) -> None:
    p = _ph()
    backend = get_backend()
    now = _now_iso()

    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT provider, total_calls, cache_hits, cache_misses, avg_latency_ms, total_cost_usd FROM provider_stats WHERE provider = {p}", [provider])
            row = cur.fetchone()
            if row:
                existing = row_to_dict(row, drop_id=False)
                total_calls = int(existing.get("total_calls") or 0) + 1
                cache_hits = int(existing.get("cache_hits") or 0) + (1 if cache_hit else 0)
                cache_misses = int(existing.get("cache_misses") or 0) + (1 if cache_miss else 0)
                prev_avg = float(existing.get("avg_latency_ms") or 0.0)
                miss_count = int(existing.get("cache_misses") or 0) + (1 if cache_miss else 0)
                if cache_miss and miss_count > 0:
                    avg_latency = ((prev_avg * (miss_count - 1)) + float(latency_ms or 0)) / miss_count
                else:
                    avg_latency = prev_avg
                total_cost = float(existing.get("total_cost_usd") or 0.0) + float(cost_usd or 0.0)
                if backend == "postgres":
                    cur.execute(
                        f"UPDATE provider_stats SET total_calls = {p}, cache_hits = {p}, cache_misses = {p}, "
                        f"avg_latency_ms = {p}, total_cost_usd = {p}, updated_at = NOW() WHERE provider = {p}",
                        [total_calls, cache_hits, cache_misses, avg_latency, total_cost, provider],
                    )
                else:
                    cur.execute(
                        f"UPDATE provider_stats SET total_calls = {p}, cache_hits = {p}, cache_misses = {p}, "
                        f"avg_latency_ms = {p}, total_cost_usd = {p}, updated_at = {p} WHERE provider = {p}",
                        [total_calls, cache_hits, cache_misses, avg_latency, total_cost, now, provider],
                    )
            else:
                total_calls = 1
                cache_hits = 1 if cache_hit else 0
                cache_misses = 1 if cache_miss else 0
                avg_latency = float(latency_ms or 0.0) if cache_miss else 0.0
                total_cost = float(cost_usd or 0.0)
                if backend == "postgres":
                    cur.execute(
                        f"INSERT INTO provider_stats (provider, total_calls, cache_hits, cache_misses, avg_latency_ms, total_cost_usd) "
                        f"VALUES ({p}, {p}, {p}, {p}, {p}, {p})",
                        [provider, total_calls, cache_hits, cache_misses, avg_latency, total_cost],
                    )
                else:
                    cur.execute(
                        f"INSERT INTO provider_stats (provider, total_calls, cache_hits, cache_misses, avg_latency_ms, total_cost_usd, updated_at) "
                        f"VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})",
                        [provider, total_calls, cache_hits, cache_misses, avg_latency, total_cost, now],
                    )
        finally:
            cur.close()