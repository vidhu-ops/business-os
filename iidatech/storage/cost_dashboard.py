"""Cost dashboard helpers for IIDATECH provider usage."""
from __future__ import annotations

from typing import Any

from iidatech.storage.db import get_connection, row_to_dict, sql_placeholder


def _ph() -> str:
    return sql_placeholder()


def build_cost_summary(report_id: str | None = None) -> dict[str, Any]:
    p = _ph()
    params: list[Any] = []
    where = ""
    if report_id:
        where = f" WHERE report_id = {p}"
        params.append(report_id)

    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT provider, SUM(cost_usd) AS cost_usd, COUNT(*) AS calls "
                f"FROM api_cost_log{where} GROUP BY provider ORDER BY cost_usd DESC",
                params,
            )
            provider_rows = [row_to_dict(r, drop_id=False) for r in cur.fetchall()]

            cur.execute(f"SELECT COALESCE(SUM(cost_usd), 0) AS total FROM api_cost_log{where}", params)
            total_row = cur.fetchone()
            total_cost = float((row_to_dict(total_row, drop_id=False).get("total") or 0.0))

            cur.execute(
                "SELECT provider, cache_hits, cache_misses, total_cost_usd, total_calls FROM provider_stats"
            )
            stats_rows = [row_to_dict(r, drop_id=False) for r in cur.fetchall()]
        finally:
            cur.close()

    provider_breakdown = {
        str(row.get("provider") or "unknown"): {
            "cost_usd": float(row.get("cost_usd") or 0.0),
            "calls": int(row.get("calls") or 0),
        }
        for row in provider_rows
    }

    cache_saved_calls = sum(int(row.get("cache_hits") or 0) for row in stats_rows)
    total_calls_logged = sum(int(row.get("calls") or 0) for row in provider_breakdown.values()) or 1
    avg_call_cost = total_cost / max(total_calls_logged, 1)
    estimated_saved_cost = round(cache_saved_calls * avg_call_cost, 6)

    return {
        "total_cost_usd": round(total_cost, 6),
        "provider_breakdown": provider_breakdown,
        "cache_saved_calls": cache_saved_calls,
        "estimated_saved_cost": estimated_saved_cost,
    }