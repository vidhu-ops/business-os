"""Repository queries for IIDATECH proprietary SQL storage."""
from __future__ import annotations

import json
import uuid
from typing import Any

from iidatech.storage.db import get_backend, get_connection, row_to_dict, sql_placeholder, topic_tokens


def _ph() -> str:
    return sql_placeholder()


def _region_filter(region_col: str, geography: str | None) -> tuple[str, list[Any]]:
    geo = (geography or "Global").strip()
    geo_low = geo.lower()
    if geo_low in {"", "global", "worldwide", "international"}:
        return "1=1", []
    p = _ph()
    clause = (
        f"({region_col} IS NULL OR TRIM({region_col}) = '' OR "
        f"LOWER({region_col}) IN ('global', 'worldwide', 'international') OR "
        f"LOWER({region_col}) LIKE {p} OR {p} LIKE ('%' || LOWER({region_col}) || '%'))"
    )
    return clause, [f"%{geo_low}%", geo_low]


def _fetch_all(sql: str, params: list[Any]) -> list[dict[str, Any]]:
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
            return [row_to_dict(r) for r in rows]
        finally:
            cur.close()


def get_competitor_pricing(
    industry: str,
    geography: str | None = None,
    *,
    limit: int = 40,
) -> list[dict[str, Any]]:
    p = _ph()
    region_clause, region_params = _region_filter("region", geography)
    sql = (
        "SELECT industry, company, product, plan, price, currency, billing_interval, "
        "region, source_url, last_verified, trust_score "
        f"FROM competitor_pricing WHERE industry = {p} AND "
        f"{region_clause} ORDER BY trust_score DESC LIMIT {p}"
    )
    return _fetch_all(sql, [industry, *region_params, limit])


def get_buyer_voice(
    industry: str,
    geography: str | None = None,
    *,
    limit: int = 80,
) -> list[dict[str, Any]]:
    p = _ph()
    region_clause, region_params = _region_filter("region", geography)
    sql = (
        "SELECT industry, source, source_type, pain_category, complaint, desired_outcome, "
        "willingness_to_pay_signal, sentiment_score, frequency, region "
        f"FROM buyer_voice WHERE industry = {p} AND "
        f"{region_clause} ORDER BY frequency DESC LIMIT {p}"
    )
    return _fetch_all(sql, [industry, *region_params, limit])


def get_supplier_costs(
    industry: str,
    geography: str | None = None,
    *,
    limit: int = 30,
) -> list[dict[str, Any]]:
    p = _ph()
    region_clause, region_params = _region_filter("region", geography)
    sql = (
        "SELECT industry, product, supplier_name, moq, unit_cost, packaging_cost, "
        "shipping_cost, region, source_url, trust_score "
        f"FROM supplier_costs WHERE industry = {p} AND "
        f"{region_clause} ORDER BY trust_score DESC LIMIT {p}"
    )
    return _fetch_all(sql, [industry, *region_params, limit])


def get_benchmarks(
    industry: str,
    geography: str | None = None,
    *,
    limit: int = 50,
) -> list[dict[str, Any]]:
    p = _ph()
    region_clause, region_params = _region_filter("geography", geography)
    sql = (
        "SELECT industry, metric, value, unit, geography, source_type, trust_score, year "
        f"FROM industry_benchmarks WHERE industry = {p} AND "
        f"{region_clause} ORDER BY trust_score DESC LIMIT {p}"
    )
    return _fetch_all(sql, [industry, *region_params, limit])


def insert_evidence_record(record: dict[str, Any]) -> str:
    row = dict(record or {})
    record_id = str(row.get("record_id") or row.get("id") or uuid.uuid4().hex)
    payload = {k: v for k, v in row.items() if k not in {
        "record_id", "topic", "industry", "geography", "region", "company",
        "title", "url", "claim_type", "trust_score", "evidence_tier", "last_verified",
    }}
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            if get_backend() == "postgres":
                cur.execute(
                    """
                    INSERT INTO evidence_records (
                        record_id, topic, industry, geography, region, company, title, url,
                        claim_type, trust_score, evidence_tier, payload, last_verified
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    ON CONFLICT (record_id) DO UPDATE SET
                        topic = EXCLUDED.topic,
                        industry = EXCLUDED.industry,
                        geography = EXCLUDED.geography,
                        region = EXCLUDED.region,
                        company = EXCLUDED.company,
                        title = EXCLUDED.title,
                        url = EXCLUDED.url,
                        claim_type = EXCLUDED.claim_type,
                        trust_score = EXCLUDED.trust_score,
                        evidence_tier = EXCLUDED.evidence_tier,
                        payload = EXCLUDED.payload,
                        last_verified = EXCLUDED.last_verified
                    """,
                    (
                        record_id,
                        row.get("topic"),
                        row.get("industry"),
                        row.get("geography"),
                        row.get("region"),
                        row.get("company"),
                        row.get("title"),
                        row.get("url"),
                        row.get("claim_type"),
                        float(row.get("trust_score") or 0),
                        row.get("evidence_tier"),
                        json.dumps(payload, ensure_ascii=False),
                        row.get("last_verified"),
                    ),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO evidence_records (
                        record_id, topic, industry, geography, region, company, title, url,
                        claim_type, trust_score, evidence_tier, payload, last_verified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(record_id) DO UPDATE SET
                        topic = excluded.topic,
                        industry = excluded.industry,
                        geography = excluded.geography,
                        region = excluded.region,
                        company = excluded.company,
                        title = excluded.title,
                        url = excluded.url,
                        claim_type = excluded.claim_type,
                        trust_score = excluded.trust_score,
                        evidence_tier = excluded.evidence_tier,
                        payload = excluded.payload,
                        last_verified = excluded.last_verified
                    """,
                    (
                        record_id,
                        row.get("topic"),
                        row.get("industry"),
                        row.get("geography"),
                        row.get("region"),
                        row.get("company"),
                        row.get("title"),
                        row.get("url"),
                        row.get("claim_type"),
                        float(row.get("trust_score") or 0),
                        row.get("evidence_tier"),
                        json.dumps(payload, ensure_ascii=False),
                        row.get("last_verified"),
                    ),
                )
        finally:
            cur.close()
    return record_id


def insert_report(report: dict[str, Any]) -> str:
    row = dict(report or {})
    report_id = str(row.get("report_id") or row.get("id") or uuid.uuid4().hex)
    topic = str(row.get("topic") or "")
    industry = str(row.get("industry") or "")
    geography = str(row.get("geography") or row.get("target") or "Global")
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else row
    scores = row.get("scores") if isinstance(row.get("scores"), list) else []

    with get_connection() as conn:
        cur = conn.cursor()
        try:
            if get_backend() == "postgres":
                cur.execute(
                    """
                    INSERT INTO reports (report_id, topic, industry, geography, payload)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT (report_id) DO UPDATE SET
                        topic = EXCLUDED.topic,
                        industry = EXCLUDED.industry,
                        geography = EXCLUDED.geography,
                        payload = EXCLUDED.payload
                    """,
                    (report_id, topic, industry, geography, json.dumps(payload, ensure_ascii=False)),
                )
            else:
                cur.execute(
                    """
                    INSERT INTO reports (report_id, topic, industry, geography, payload)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(report_id) DO UPDATE SET
                        topic = excluded.topic,
                        industry = excluded.industry,
                        geography = excluded.geography,
                        payload = excluded.payload
                    """,
                    (report_id, topic, industry, geography, json.dumps(payload, ensure_ascii=False)),
                )

            for score_row in scores:
                if not isinstance(score_row, dict):
                    continue
                section = str(score_row.get("section") or "")
                score_val = float(score_row.get("score") or 0)
                details = score_row.get("details") if isinstance(score_row.get("details"), dict) else score_row
                if get_backend() == "postgres":
                    cur.execute(
                        """
                        INSERT INTO report_scores (report_id, section, score, details)
                        VALUES (%s, %s, %s, %s::jsonb)
                        """,
                        (report_id, section, score_val, json.dumps(details, ensure_ascii=False)),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO report_scores (report_id, section, score, details)
                        VALUES (?, ?, ?, ?)
                        """,
                        (report_id, section, score_val, json.dumps(details, ensure_ascii=False)),
                    )
        finally:
            cur.close()
    return report_id


def search_similar_records(topic: str, *, limit: int = 20) -> list[dict[str, Any]]:
    tokens = sorted(topic_tokens(topic))
    if not tokens:
        return []

    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "SELECT record_id, topic, industry, geography, region, company, title, url, "
                "claim_type, trust_score, evidence_tier, payload, last_verified "
                "FROM evidence_records ORDER BY trust_score DESC LIMIT 500"
            )
            rows = cur.fetchall()
        finally:
            cur.close()

    scored: list[tuple[float, dict[str, Any]]] = []
    for raw in rows:
        row = row_to_dict(raw, drop_id=True)
        payload = row.pop("payload", None)
        if isinstance(payload, dict):
            row.update(payload)
        hay = " ".join(
            str(row.get(k) or "")
            for k in ("topic", "industry", "title", "company", "claim_type", "geography", "region")
        ).lower()
        hits = sum(1 for t in tokens if t in hay)
        if hits == 0:
            continue
        score = hits / max(1, len(tokens)) + float(row.get("trust_score") or 0) * 0.1
        scored.append((score, row))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [row for _, row in scored[:limit]]


def bank_row_counts() -> dict[str, int]:
    tables = {
        "competitor_pricing": "competitor_pricing",
        "buyer_voice": "buyer_voice",
        "supplier_cost": "supplier_costs",
        "benchmark": "industry_benchmarks",
    }
    counts: dict[str, int] = {}
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            for key, table in tables.items():
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                row = cur.fetchone()
                if isinstance(row, dict):
                    counts[key] = int(list(row.values())[0])
                elif hasattr(row, "__getitem__"):
                    counts[key] = int(row[0])
                else:
                    counts[key] = 0
        finally:
            cur.close()
    return counts