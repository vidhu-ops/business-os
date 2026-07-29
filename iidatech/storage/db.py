"""IIDATECH SQL storage: PostgreSQL with SQLite fallback."""
from __future__ import annotations

import json
import os
import re
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

_APP_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SQLITE = _APP_ROOT / "datasets" / "iidatech_proprietary.sqlite"
_SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"

_SQLITE_DDL = """
CREATE TABLE IF NOT EXISTS competitor_pricing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry TEXT NOT NULL,
    company TEXT,
    product TEXT,
    plan TEXT,
    price REAL,
    currency TEXT,
    billing_interval TEXT,
    region TEXT DEFAULT 'Global',
    source_url TEXT,
    last_verified TEXT,
    trust_score REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS buyer_voice (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry TEXT NOT NULL,
    source TEXT,
    source_type TEXT,
    pain_category TEXT,
    complaint TEXT,
    desired_outcome TEXT,
    willingness_to_pay_signal TEXT,
    sentiment_score REAL,
    frequency INTEGER DEFAULT 0,
    region TEXT DEFAULT 'Global'
);
CREATE TABLE IF NOT EXISTS supplier_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry TEXT NOT NULL,
    product TEXT,
    supplier_name TEXT,
    moq INTEGER,
    unit_cost REAL,
    packaging_cost REAL,
    shipping_cost REAL,
    region TEXT DEFAULT 'Global',
    source_url TEXT,
    trust_score REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS industry_benchmarks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    industry TEXT NOT NULL,
    metric TEXT,
    value REAL,
    unit TEXT,
    geography TEXT DEFAULT 'Global',
    source_type TEXT,
    trust_score REAL DEFAULT 0,
    year INTEGER
);
CREATE TABLE IF NOT EXISTS evidence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id TEXT UNIQUE,
    topic TEXT,
    industry TEXT,
    geography TEXT,
    region TEXT,
    company TEXT,
    title TEXT,
    url TEXT,
    claim_type TEXT,
    trust_score REAL DEFAULT 0,
    evidence_tier TEXT,
    payload TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    last_verified TEXT
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT UNIQUE,
    topic TEXT NOT NULL,
    industry TEXT,
    geography TEXT,
    payload TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS report_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT NOT NULL,
    section TEXT,
    score REAL,
    details TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_industry ON competitor_pricing(industry);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_company ON competitor_pricing(company);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_region ON competitor_pricing(region);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_trust_score ON competitor_pricing(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_competitor_pricing_last_verified ON competitor_pricing(last_verified);
CREATE INDEX IF NOT EXISTS idx_buyer_voice_industry ON buyer_voice(industry);
CREATE INDEX IF NOT EXISTS idx_buyer_voice_region ON buyer_voice(region);
CREATE INDEX IF NOT EXISTS idx_buyer_voice_frequency ON buyer_voice(frequency DESC);
CREATE INDEX IF NOT EXISTS idx_supplier_costs_industry ON supplier_costs(industry);
CREATE INDEX IF NOT EXISTS idx_supplier_costs_region ON supplier_costs(region);
CREATE INDEX IF NOT EXISTS idx_supplier_costs_trust_score ON supplier_costs(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_industry ON industry_benchmarks(industry);
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_geography ON industry_benchmarks(geography);
CREATE INDEX IF NOT EXISTS idx_industry_benchmarks_trust_score ON industry_benchmarks(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_records_topic ON evidence_records(topic);
CREATE INDEX IF NOT EXISTS idx_evidence_records_industry ON evidence_records(industry);
CREATE INDEX IF NOT EXISTS idx_evidence_records_company ON evidence_records(company);
CREATE INDEX IF NOT EXISTS idx_evidence_records_trust_score ON evidence_records(trust_score DESC);
CREATE INDEX IF NOT EXISTS idx_evidence_records_last_verified ON evidence_records(last_verified);
CREATE INDEX IF NOT EXISTS idx_evidence_records_geography ON evidence_records(geography);
CREATE INDEX IF NOT EXISTS idx_evidence_records_region ON evidence_records(region);
CREATE INDEX IF NOT EXISTS idx_reports_topic ON reports(topic);
CREATE INDEX IF NOT EXISTS idx_reports_industry ON reports(industry);
CREATE INDEX IF NOT EXISTS idx_reports_geography ON reports(geography);
CREATE INDEX IF NOT EXISTS idx_report_scores_report_id ON report_scores(report_id);
"""

_CACHE_DDL = """
CREATE TABLE IF NOT EXISTS search_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_hash TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    provider TEXT NOT NULL,
    result_json TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    expires_at TEXT NOT NULL,
    hit_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS provider_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    provider TEXT UNIQUE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    avg_latency_ms REAL DEFAULT 0,
    total_cost_usd REAL DEFAULT 0,
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS api_cost_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id TEXT,
    provider TEXT,
    model TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd REAL DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_search_cache_query_hash ON search_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_cache_provider ON search_cache(provider);
CREATE INDEX IF NOT EXISTS idx_search_cache_created_at ON search_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_provider_stats_provider ON provider_stats(provider);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_report_id ON api_cost_log(report_id);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_provider ON api_cost_log(provider);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_created_at ON api_cost_log(created_at);
"""


def get_backend() -> str:
    explicit = (os.environ.get("IIDATECH_DB_BACKEND") or "").strip().lower()
    if explicit in {"postgres", "postgresql", "pg"}:
        return "postgres"
    if explicit == "sqlite":
        return "sqlite"
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if url.startswith(("postgres://", "postgresql://")):
        return "postgres"
    return "sqlite"


def sql_placeholder() -> str:
    return "%s" if get_backend() == "postgres" else "?"


def get_database_url() -> str:
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if url:
        return url
    backend = get_backend()
    if backend == "postgres":
        return "postgresql://localhost/iidatech"
    return f"sqlite:///{_DEFAULT_SQLITE.as_posix()}"


def _sqlite_path_from_url(url: str) -> Path:
    if url.startswith("sqlite:///"):
        raw = url[len("sqlite:///"):]
        path = Path(raw)
        if not path.is_absolute():
            path = _APP_ROOT / raw
        return path
    return _DEFAULT_SQLITE


def topic_tokens(topic: str, industry: str = "", target: str = "") -> set[str]:
    stop = {
        "market", "industry", "report", "analysis", "business", "global",
        "country", "service", "services", "platform", "company", "companies",
        "with", "from", "that", "this", "into", "their", "should",
    }
    return {
        token
        for token in re.findall(r"[a-z0-9]+", f"{topic} {industry} {target}".lower())
        if len(token) > 3 and token not in stop
    }


def row_to_dict(row: Any, *, drop_id: bool = True) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, dict):
        out = dict(row)
    elif hasattr(row, "keys"):
        out = {k: row[k] for k in row.keys()}
    else:
        return {}
    if drop_id:
        out.pop("id", None)
    for key in ("payload", "details"):
        val = out.get(key)
        if isinstance(val, str) and val:
            try:
                out[key] = json.loads(val)
            except json.JSONDecodeError:
                pass
    return out


def _import_psycopg():
    try:
        import psycopg
        return psycopg, "psycopg3"
    except ImportError:
        pass
    try:
        import psycopg2 as psycopg
        return psycopg, "psycopg2"
    except ImportError:
        return None, None


@contextmanager
def get_connection() -> Generator[Any, None, None]:
    backend = get_backend()
    if backend == "postgres":
        psycopg, flavor = _import_psycopg()
        if psycopg is None:
            raise RuntimeError("PostgreSQL backend requested but psycopg/psycopg2 is not installed")
        url = get_database_url()
        if flavor == "psycopg3":
            from psycopg.rows import dict_row
            conn = psycopg.connect(url, row_factory=dict_row)
        else:
            from psycopg2.extras import RealDictCursor
            conn = psycopg.connect(url, cursor_factory=RealDictCursor)
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:
        db_path = _sqlite_path_from_url(get_database_url())
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def _execute_script(conn: Any, script: str) -> None:
    statements = [s.strip() for s in script.split(";") if s.strip()]
    cur = conn.cursor()
    try:
        for stmt in statements:
            cur.execute(stmt)
    finally:
        cur.close()


_EXECUTION_DDL = """
CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    department TEXT,
    authority_level INTEGER DEFAULT 1,
    skills_json TEXT DEFAULT '[]',
    performance_score REAL DEFAULT 5.0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS tasks (
    task_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    title TEXT NOT NULL,
    owner_employee_id TEXT,
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    dependencies_json TEXT DEFAULT '[]',
    blockers_json TEXT DEFAULT '[]',
    due_date TEXT,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS task_messages (
    message_id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    message_text TEXT NOT NULL,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS team_rooms (
    room_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    name TEXT,
    room_type TEXT DEFAULT 'war_room',
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS team_messages (
    message_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    sender_id TEXT NOT NULL,
    receiver_id TEXT,
    room_id TEXT,
    mode TEXT,
    message_text TEXT NOT NULL,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS employee_memory (
    memory_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    scope TEXT NOT NULL,
    memory_json TEXT DEFAULT '{}',
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS kpi_history (
    kpi_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    kpi_name TEXT NOT NULL,
    kpi_value REAL,
    notes TEXT,
    recorded_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_employees_report ON employees(report_id);
CREATE INDEX IF NOT EXISTS idx_tasks_report ON tasks(report_id);
CREATE INDEX IF NOT EXISTS idx_team_messages_report ON team_messages(report_id);
CREATE INDEX IF NOT EXISTS idx_kpi_report ON kpi_history(report_id);
CREATE TABLE IF NOT EXISTS employee_private_memory (
    memory_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    preferences_json TEXT DEFAULT '{}',
    past_tasks_json TEXT DEFAULT '[]',
    learned_insights_json TEXT DEFAULT '[]',
    updated_at TEXT,
    UNIQUE(report_id, employee_id)
);
CREATE TABLE IF NOT EXISTS team_shared_memory (
    memory_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL UNIQUE,
    goals_json TEXT DEFAULT '[]',
    blockers_json TEXT DEFAULT '[]',
    company_context_json TEXT DEFAULT '{}',
    updated_at TEXT
);
CREATE TABLE IF NOT EXISTS company_state (
    state_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL UNIQUE,
    revenue REAL DEFAULT 0,
    burn REAL DEFAULT 0,
    kpis_json TEXT DEFAULT '{}',
    growth_metrics_json TEXT DEFAULT '{}',
    active_campaigns_json TEXT DEFAULT '[]',
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_emp_private_mem ON employee_private_memory(report_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_team_shared_mem ON team_shared_memory(report_id);
CREATE INDEX IF NOT EXISTS idx_company_state_report ON company_state(report_id);
CREATE TABLE IF NOT EXISTS employee_long_memory (
    memory_id TEXT PRIMARY KEY,
    employee_id TEXT NOT NULL,
    report_id TEXT NOT NULL,
    memory_type TEXT NOT NULL,
    memory_text TEXT NOT NULL,
    importance_score REAL DEFAULT 0.5,
    created_at TEXT,
    last_used_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_long_mem_report_emp ON employee_long_memory(report_id, employee_id);
CREATE INDEX IF NOT EXISTS idx_long_mem_type ON employee_long_memory(memory_type);
CREATE TABLE IF NOT EXISTS employee_relationships (
    relationship_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    employee_a TEXT NOT NULL,
    employee_b TEXT NOT NULL,
    trust_score REAL DEFAULT 0.5,
    conflict_score REAL DEFAULT 0.0,
    collaboration_score REAL DEFAULT 0.5,
    updated_at TEXT,
    UNIQUE(report_id, employee_a, employee_b)
);
CREATE INDEX IF NOT EXISTS idx_relationships_report ON employee_relationships(report_id);
CREATE TABLE IF NOT EXISTS founder_preferences (
    preference_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    preference_key TEXT NOT NULL,
    preference_value TEXT NOT NULL,
    confidence REAL DEFAULT 0.5,
    updated_at TEXT,
    UNIQUE(report_id, preference_key)
);
CREATE INDEX IF NOT EXISTS idx_founder_prefs_report ON founder_preferences(report_id);
CREATE TABLE IF NOT EXISTS pipeline_leads (
    lead_id TEXT PRIMARY KEY,
    report_id TEXT NOT NULL,
    name TEXT,
    email TEXT,
    company TEXT,
    title TEXT,
    source TEXT,
    status TEXT DEFAULT 'new',
    score REAL DEFAULT 0,
    metadata_json TEXT DEFAULT '{}',
    created_at TEXT,
    updated_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_pipeline_leads_report ON pipeline_leads(report_id);
CREATE TABLE IF NOT EXISTS tool_execution_logs (
    log_id TEXT PRIMARY KEY,
    task_id TEXT,
    report_id TEXT NOT NULL,
    employee_id TEXT,
    tool_name TEXT NOT NULL,
    execution_mode TEXT DEFAULT 'simulated',
    verified INTEGER DEFAULT 0,
    success INTEGER DEFAULT 0,
    artifacts_json TEXT DEFAULT '[]',
    metrics_json TEXT DEFAULT '{}',
    logs_json TEXT DEFAULT '[]',
    errors_json TEXT DEFAULT '[]',
    result_json TEXT DEFAULT '{}',
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_tool_exec_report ON tool_execution_logs(report_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tool_exec_task ON tool_execution_logs(task_id);
"""


def ensure_cache_schema() -> None:
    backend = get_backend()
    with get_connection() as conn:
        if backend == "postgres":
            cache_script = """
CREATE TABLE IF NOT EXISTS search_cache (
    id SERIAL PRIMARY KEY,
    query_hash TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    provider TEXT NOT NULL,
    result_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    hit_count INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS provider_stats (
    id SERIAL PRIMARY KEY,
    provider TEXT UNIQUE NOT NULL,
    total_calls INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    cache_misses INTEGER DEFAULT 0,
    avg_latency_ms DOUBLE PRECISION DEFAULT 0,
    total_cost_usd DOUBLE PRECISION DEFAULT 0,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE TABLE IF NOT EXISTS api_cost_log (
    id SERIAL PRIMARY KEY,
    report_id TEXT,
    provider TEXT,
    model TEXT,
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    cost_usd DOUBLE PRECISION DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_search_cache_query_hash ON search_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_cache_provider ON search_cache(provider);
CREATE INDEX IF NOT EXISTS idx_search_cache_created_at ON search_cache(created_at);
CREATE INDEX IF NOT EXISTS idx_provider_stats_provider ON provider_stats(provider);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_report_id ON api_cost_log(report_id);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_provider ON api_cost_log(provider);
CREATE INDEX IF NOT EXISTS idx_api_cost_log_created_at ON api_cost_log(created_at);
"""
            _execute_script(conn, cache_script)
        else:
            _execute_script(conn, _CACHE_DDL)




_SEMANTIC_TABLES = (
    "competitor_pricing",
    "buyer_voice",
    "supplier_costs",
    "industry_benchmarks",
    "evidence_records",
    "reports",
)


def _table_has_column(conn, table: str, column: str) -> bool:
    backend = get_backend()
    cur = conn.cursor()
    try:
        if backend == "postgres":
            cur.execute(
                "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s LIMIT 1",
                (table, column),
            )
            return cur.fetchone() is not None
        cur.execute(f"PRAGMA table_info({table})")
        for row in cur.fetchall():
            name = row[1] if not isinstance(row, dict) else row.get("name")
            if str(name) == column:
                return True
        return False
    finally:
        cur.close()


def ensure_semantic_schema() -> None:
    with get_connection() as conn:
        for table in _SEMANTIC_TABLES:
            for col, col_type in (
                ("embedding_vector", "TEXT"),
                ("embedding_model", "TEXT"),
                ("embedding_updated_at", "TEXT"),
            ):
                if _table_has_column(conn, table, col):
                    continue
                if get_backend() == "postgres":
                    pg_type = "JSONB" if col == "embedding_vector" else "TEXT"
                    if col == "embedding_updated_at":
                        pg_type = "TIMESTAMPTZ"
                    _execute_script(conn, f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {pg_type}")
                else:
                    _execute_script(conn, f"ALTER TABLE {table} ADD COLUMN {col} {col_type}")


def ensure_execution_schema() -> None:
    """Create Employee OS tables (employees, tasks, chat, memory, KPIs)."""
    with get_connection() as conn:
        _execute_script(conn, _EXECUTION_DDL)


def init_schema() -> None:
    backend = get_backend()
    with get_connection() as conn:
        if backend == "postgres":
            script = _SCHEMA_PATH.read_text(encoding="utf-8")
            _execute_script(conn, script)
        else:
            combined = _SQLITE_DDL + _CACHE_DDL
            _execute_script(conn, combined)
    ensure_cache_schema()
    ensure_semantic_schema()


def sql_storage_ready() -> bool:
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            try:
                cur.execute("SELECT 1 FROM competitor_pricing LIMIT 1")
                cur.fetchone()
                return True
            except Exception:
                return False
            finally:
                cur.close()
    except Exception:
        return False