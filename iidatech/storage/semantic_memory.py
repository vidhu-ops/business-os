"""SQL semantic retrieval memory for IIDATECH proprietary + evidence tables."""
from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from typing import Any

from iidatech.retrieval.embedding import embed_text_with_model
from iidatech.storage.db import get_backend, get_connection, row_to_dict

EMBEDDABLE_TABLES: dict[str, dict[str, Any]] = {
    "competitor_pricing": {
        "id_col": "id",
        "text_cols": ("industry", "company", "product", "plan", "billing_interval", "region"),
        "select": "id, industry, company, product, plan, price, currency, billing_interval, region, source_url, trust_score, embedding_vector, embedding_model",
    },
    "buyer_voice": {
        "id_col": "id",
        "text_cols": ("industry", "source_type", "pain_category", "complaint", "desired_outcome", "willingness_to_pay_signal", "region"),
        "select": "id, industry, source, source_type, pain_category, complaint, desired_outcome, willingness_to_pay_signal, sentiment_score, frequency, region, embedding_vector, embedding_model",
    },
    "supplier_costs": {
        "id_col": "id",
        "text_cols": ("industry", "product", "supplier_name", "region"),
        "select": "id, industry, product, supplier_name, moq, unit_cost, packaging_cost, shipping_cost, region, source_url, trust_score, embedding_vector, embedding_model",
    },
    "industry_benchmarks": {
        "id_col": "id",
        "text_cols": ("industry", "metric", "unit", "geography", "source_type"),
        "select": "id, industry, metric, value, unit, geography, source_type, trust_score, year, embedding_vector, embedding_model",
    },
    "evidence_records": {
        "id_col": "record_id",
        "text_cols": ("topic", "industry", "geography", "region", "company", "title", "claim_type", "evidence_tier"),
        "select": "record_id, topic, industry, geography, region, company, title, url, claim_type, trust_score, evidence_tier, payload, embedding_vector, embedding_model",
    },
    "reports": {
        "id_col": "report_id",
        "text_cols": ("topic", "industry", "geography"),
        "select": "report_id, topic, industry, geography, payload, created_at, embedding_vector, embedding_model",
    },
}

INDUSTRY_SEMANTIC_ALIASES: dict[str, str] = {
    "crm_automation": "crm sales automation lead pipeline messaging workflow software saas hubspot pipedrive",
    "dental_clinics": "dental clinic dentist practice management patient scheduling appointment",
    "clinic_workflow": "clinic workflow practice management outpatient scheduling emr patient appointment software",
    "healthcare_saas": "healthcare saas patient engagement telehealth clinic hospital software dental",
    "d2c_skincare": "skincare beauty cosmetics d2c ecommerce retail",
    "saas": "b2b saas subscription software cloud platform",
    "automotive_retail": "car dealership auto garage vehicle service automotive retail",
}

QUERY_EXPANSION_TERMS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (("whatsapp", "wa automation", "wa bot"), ("messaging automation", "patient communication", "chat automation", "sms reminders")),
    (("dentist", "dental", "dentists"), ("dental clinic", "practice management", "dental_clinics", "patient scheduling")),
    (("automation",), ("workflow automation", "crm_automation", "clinic_workflow", "saas software")),
    (("clinic", "practice"), ("clinic_workflow", "healthcare_saas", "outpatient", "appointment")),
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def expand_query_text(query: str) -> str:
    low = str(query or "").lower()
    extras: list[str] = []
    for triggers, terms in QUERY_EXPANSION_TERMS:
        if any(t in low for t in triggers):
            extras.extend(terms)
    return " ".join(dict.fromkeys(str(query or "").split() + extras))


def build_row_embed_text(table: str, row: dict[str, Any]) -> str:
    spec = EMBEDDABLE_TABLES[table]
    parts: list[str] = []
    industry = str(row.get("industry") or "")
    if industry:
        parts.append(industry.replace("_", " "))
        parts.append(INDUSTRY_SEMANTIC_ALIASES.get(industry, ""))
    for col in spec["text_cols"]:
        val = row.get(col)
        if val not in (None, ""):
            parts.append(str(val))
    if table == "reports":
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        if isinstance(payload, dict):
            parts.append(str(payload.get("summary") or payload.get("idea") or "")[:500])
    if table == "evidence_records":
        payload = row.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        if isinstance(payload, dict):
            parts.append(str(payload.get("text") or payload.get("snippet") or "")[:500])
    return " ".join(p for p in parts if p).strip()


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def _parse_vector(raw: Any) -> list[float] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        return [float(x) for x in raw]
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return [float(x) for x in parsed]
        except json.JSONDecodeError:
            return None
    return None


def _serialize_vector(vec: list[float]) -> str:
    return json.dumps([round(float(x), 8) for x in vec])


def upsert_row_embedding(table: str, row_id: Any, text: str) -> tuple[str, str]:
    vec, model = embed_text_with_model(text)
    payload = _serialize_vector(vec)
    updated = _now_iso()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            id_col = EMBEDDABLE_TABLES[table]["id_col"]
            if get_backend() == "postgres":
                cur.execute(
                    f"UPDATE {table} SET embedding_vector = %s, embedding_model = %s, embedding_updated_at = %s WHERE {id_col} = %s",
                    (payload, model, updated, row_id),
                )
            else:
                cur.execute(
                    f"UPDATE {table} SET embedding_vector = ?, embedding_model = ?, embedding_updated_at = ? WHERE {id_col} = ?",
                    (payload, model, updated, row_id),
                )
        finally:
            cur.close()
    return model, updated


def backfill_embeddings(*, tables: list[str] | None = None, limit_per_table: int | None = None) -> dict[str, int]:
    targets = tables or list(EMBEDDABLE_TABLES.keys())
    counts: dict[str, int] = {}
    for table in targets:
        spec = EMBEDDABLE_TABLES[table]
        id_col = spec["id_col"]
        sql = f"SELECT {spec['select']} FROM {table} WHERE embedding_vector IS NULL OR TRIM(embedding_vector) = ''"
        if limit_per_table:
            sql += f" LIMIT {int(limit_per_table)}"
        with get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute(sql)
                rows = [row_to_dict(r, drop_id=False) for r in cur.fetchall()]
            finally:
                cur.close()
        updated = 0
        for row in rows:
            text = build_row_embed_text(table, row)
            if not text:
                continue
            upsert_row_embedding(table, row.get(id_col), text)
            updated += 1
        counts[table] = updated
    return counts


def _score_table_rows(table: str, query_vec: list[float], *, limit: int) -> list[dict[str, Any]]:
    spec = EMBEDDABLE_TABLES[table]
    id_col = spec["id_col"]
    sql = f"SELECT {spec['select']} FROM {table} WHERE embedding_vector IS NOT NULL AND TRIM(embedding_vector) != ''"
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql)
            rows = [row_to_dict(r, drop_id=False) for r in cur.fetchall()]
        finally:
            cur.close()
    scored: list[dict[str, Any]] = []
    for row in rows:
        vec = _parse_vector(row.get("embedding_vector"))
        if not vec:
            continue
        sim = cosine_similarity(query_vec, vec)
        if sim <= 0.02:
            continue
        hit = dict(row)
        hit.pop("embedding_vector", None)
        hit["source_table"] = table
        hit["similarity_score"] = round(sim, 6)
        hit["record_key"] = str(hit.get(id_col) or "")
        scored.append(hit)
    scored.sort(key=lambda r: float(r.get("similarity_score") or 0), reverse=True)
    return scored[:limit]


def _merge_scored_hits(query_vec: list[float], *, per_table: int = 40, min_sim: float = 0.03) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for table in ("competitor_pricing", "buyer_voice", "supplier_costs", "industry_benchmarks", "evidence_records"):
        for hit in _score_table_rows(table, query_vec, limit=per_table):
            if float(hit.get("similarity_score") or 0) >= min_sim:
                merged.append(hit)
    merged.sort(key=lambda r: float(r.get("similarity_score") or 0), reverse=True)
    return merged


def search_semantic_records(query: str, limit: int = 20) -> list[dict[str, Any]]:
    expanded = expand_query_text(query)
    query_vec, _model = embed_text_with_model(expanded)
    return _merge_scored_hits(query_vec, per_table=max(8, limit))[:limit]


def search_similar_reports(query: str, limit: int = 10) -> list[dict[str, Any]]:
    expanded = expand_query_text(query)
    query_vec, _model = embed_text_with_model(expanded)
    return _score_table_rows("reports", query_vec, limit=limit)


def search_cross_industry_patterns(query: str, limit: int = 15) -> list[dict[str, Any]]:
    expanded = expand_query_text(query)
    query_vec, _ = embed_text_with_model(expanded)
    merged = _merge_scored_hits(query_vec, per_table=60, min_sim=0.02)

    # Pull at least one strong row per related vertical for cross-domain recall.
    seed_industries = (
        "crm_automation",
        "dental_clinics",
        "clinic_workflow",
        "healthcare_saas",
        "saas",
    )
    low = expanded.lower()
    if any(t in low for t in ("dental", "dentist", "clinic", "whatsapp", "patient")):
        seed_industries = (
            "dental_clinics",
            "clinic_workflow",
            "healthcare_saas",
            "crm_automation",
            "saas",
        )
    for industry in seed_industries:
        alias = INDUSTRY_SEMANTIC_ALIASES.get(industry, industry.replace("_", " "))
        seed_vec, _ = embed_text_with_model(f"{expanded} {alias}")
        for hit in _merge_scored_hits(seed_vec, per_table=12, min_sim=0.01):
            if str(hit.get("industry") or "") == industry:
                merged.append(hit)

    merged.sort(key=lambda r: float(r.get("similarity_score") or 0), reverse=True)
    by_industry: dict[str, dict[str, Any]] = {}
    for hit in merged:
        industry = str(hit.get("industry") or "unknown")
        prev = by_industry.get(industry)
        if prev is None or float(hit.get("similarity_score") or 0) > float(prev.get("similarity_score") or 0):
            by_industry[industry] = hit
    ranked = sorted(by_industry.values(), key=lambda r: float(r.get("similarity_score") or 0), reverse=True)
    return ranked[:limit]


def semantic_memory_ready() -> bool:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT embedding_vector FROM competitor_pricing WHERE embedding_vector IS NOT NULL LIMIT 1")
                return cur.fetchone() is not None
            finally:
                cur.close()
    except Exception:
        return False