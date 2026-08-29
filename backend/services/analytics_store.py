"""First-party visitor analytics store (SQLite by default, Postgres when DATABASE_URL is set)."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from backend.services.geo_ua import classify_source, host_from_url
from backend.services.page_taxonomy import DEMO_MARKER, classify_page, is_demo_hit

_lock = threading.RLock()
_pg_ready: bool | None = None

SESSION_IDLE_MINUTES = 30
_SKIP_LEAD_PATHS = {
    "/app/analytics",
    "/app/crm",
    "/analytics",
    "/analystics",
    "/app/analystics",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_ts(value: str) -> datetime | None:
    raw = (value or "").strip()
    if not raw:
        return None
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None


def _data_dir() -> Path:
    raw = (os.getenv("DATA_DIR") or os.getenv("BUSINESS_OUTPUTS_ROOT") or "").strip()
    if raw:
        path = Path(raw)
    else:
        from backend.config import settings

        path = settings.outputs_root
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sqlite_path() -> Path:
    explicit = (os.getenv("ANALYTICS_DB_PATH") or "").strip()
    if explicit:
        path = Path(explicit)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return _data_dir() / "iidatech_analytics.sqlite"


def _database_url() -> str:
    return (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()


def _use_postgres() -> bool:
    global _pg_ready
    if not _database_url():
        return False
    if _pg_ready is None:
        try:
            import psycopg  # noqa: F401

            _pg_ready = True
        except Exception:
            _pg_ready = False
    return bool(_pg_ready)


def _q(sql: str) -> str:
    return sql.replace("?", "%s") if _use_postgres() else sql


def _json_ph() -> str:
    return "%s::jsonb" if _use_postgres() else "?"


_SCHEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS visitors (
    visitor_id TEXT PRIMARY KEY,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    user_email TEXT,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    visitor_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS page_views (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    path TEXT NOT NULL,
    at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    name TEXT NOT NULL,
    at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analytics_sessions_last ON sessions(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_analytics_sessions_visitor ON sessions(visitor_id);
CREATE INDEX IF NOT EXISTS idx_analytics_page_views_at ON page_views(at);
CREATE INDEX IF NOT EXISTS idx_analytics_page_views_session ON page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_name_at ON events(name, at);
CREATE INDEX IF NOT EXISTS idx_analytics_visitors_email ON visitors(user_email);
CREATE TABLE IF NOT EXISTS leads (
    lead_id TEXT PRIMARY KEY,
    visitor_id TEXT,
    email TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    data TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analytics_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_analytics_leads_visitor ON leads(visitor_id);
CREATE INDEX IF NOT EXISTS idx_analytics_leads_updated ON leads(updated_at);
"""

_SCHEMA_PG = """
CREATE TABLE IF NOT EXISTS analytics_visitors (
    visitor_id TEXT PRIMARY KEY,
    first_seen_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    user_email TEXT,
    data JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics_sessions (
    session_id TEXT PRIMARY KEY,
    visitor_id TEXT NOT NULL,
    started_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL,
    data JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics_page_views (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    path TEXT NOT NULL,
    at TEXT NOT NULL,
    data JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS analytics_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    visitor_id TEXT NOT NULL,
    name TEXT NOT NULL,
    at TEXT NOT NULL,
    data JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analytics_sessions_last ON analytics_sessions(last_seen_at);
CREATE INDEX IF NOT EXISTS idx_analytics_sessions_visitor ON analytics_sessions(visitor_id);
CREATE INDEX IF NOT EXISTS idx_analytics_page_views_at ON analytics_page_views(at);
CREATE INDEX IF NOT EXISTS idx_analytics_page_views_session ON analytics_page_views(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_name_at ON analytics_events(name, at);
CREATE INDEX IF NOT EXISTS idx_analytics_visitors_email ON analytics_visitors(user_email);
CREATE TABLE IF NOT EXISTS analytics_leads (
    lead_id TEXT PRIMARY KEY,
    visitor_id TEXT,
    email TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    data JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analytics_leads_email ON analytics_leads(email);
CREATE INDEX IF NOT EXISTS idx_analytics_leads_visitor ON analytics_leads(visitor_id);
CREATE INDEX IF NOT EXISTS idx_analytics_leads_updated ON analytics_leads(updated_at);
"""


def _tables() -> dict[str, str]:
    if _use_postgres():
        return {
            "visitors": "analytics_visitors",
            "sessions": "analytics_sessions",
            "page_views": "analytics_page_views",
            "events": "analytics_events",
            "leads": "analytics_leads",
        }
    return {
        "visitors": "visitors",
        "sessions": "sessions",
        "page_views": "page_views",
        "events": "events",
        "leads": "leads",
    }


def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_sqlite_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(_SCHEMA_SQLITE)
    conn.commit()
    return conn


def _pg_connect():
    import psycopg
    from psycopg.rows import dict_row

    url = _database_url()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    conn = psycopg.connect(url, row_factory=dict_row)
    with conn.cursor() as cur:
        cur.execute(_SCHEMA_PG)
    conn.commit()
    return conn


def _dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, default=str)


def _loads(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _fetchone(conn: Any, sql: str, params: tuple[Any, ...]) -> Any:
    if _use_postgres():
        with conn.cursor() as cur:
            cur.execute(_q(sql), params)
            return cur.fetchone()
    return conn.execute(sql, params).fetchone()


def _fetchall(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
    if _use_postgres():
        with conn.cursor() as cur:
            cur.execute(_q(sql), params)
            return list(cur.fetchall())
    return list(conn.execute(sql, params).fetchall())


def _execute(conn: Any, sql: str, params: tuple[Any, ...] = ()) -> None:
    if _use_postgres():
        with conn.cursor() as cur:
            cur.execute(_q(sql), params)
        return
    conn.execute(sql, params)


def _row_get(row: Any, key: str) -> Any:
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    try:
        return row[key]
    except Exception:
        return None


def _with_conn(fn):
    def wrapped(*args: Any, **kwargs: Any):
        with _lock:
            conn = _pg_connect() if _use_postgres() else _sqlite_conn()
            try:
                result = fn(conn, *args, **kwargs)
                conn.commit()
                return result
            finally:
                conn.close()

    return wrapped


def _sticky(existing: dict[str, Any], key: str, incoming: str) -> str:
    current = str(existing.get(key) or "").strip()
    value = (incoming or "").strip()
    return current or value


def _merge_visitor(existing: dict[str, Any] | None, incoming: dict[str, Any], now: str) -> dict[str, Any]:
    base = dict(existing or {})
    if not base:
        base = {
            "visitor_id": incoming["visitor_id"],
            "first_seen_at": now,
            "landing_path": incoming.get("path") or "/",
            "landing_url": incoming.get("href") or "",
            "referrer": incoming.get("referrer") or "",
            "referrer_host": host_from_url(str(incoming.get("referrer") or "")),
            "utm_source": incoming.get("utm_source") or "",
            "utm_medium": incoming.get("utm_medium") or "",
            "utm_campaign": incoming.get("utm_campaign") or "",
            "utm_term": incoming.get("utm_term") or "",
            "utm_content": incoming.get("utm_content") or "",
            "gclid": incoming.get("gclid") or "",
            "fbclid": incoming.get("fbclid") or "",
            "msclkid": incoming.get("msclkid") or "",
            "source": incoming.get("source") or "direct",
        }
    else:
        for key in (
            "landing_path",
            "landing_url",
            "referrer",
            "referrer_host",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_term",
            "utm_content",
            "gclid",
            "fbclid",
            "msclkid",
            "source",
        ):
            base[key] = _sticky(base, key, str(incoming.get(key) or ""))
    for key in ("country", "country_name", "city", "region", "place", "timezone", "language", "ip_masked"):
        if incoming.get(key):
            base[key] = incoming[key]
    if incoming.get("ip_hash"):
        base["ip_hash"] = incoming["ip_hash"]
    for key in ("device", "os", "browser", "user_agent"):
        if incoming.get(key):
            base[key] = incoming[key]
    if incoming.get("user_email"):
        base["user_email"] = incoming["user_email"]
    if incoming.get("signed_up_at"):
        base["signed_up_at"] = incoming["signed_up_at"]
    screens = base.get("screens")
    if not isinstance(screens, list):
        screens = []
    screen = str(incoming.get("screen") or "").strip()
    if screen and screen not in screens:
        screens = (screens + [screen])[-8:]
    base["screens"] = screens
    base["last_seen_at"] = now
    base["last_path"] = incoming.get("path") or base.get("last_path") or "/"
    base["session_count"] = int(base.get("session_count") or 0)
    base["pageview_count"] = int(base.get("pageview_count") or 0)
    return base


@_with_conn
def ingest(conn: Any, payload: dict[str, Any]) -> dict[str, Any]:
    now = str(payload.get("at") or _now())
    visitor_id = str(payload.get("visitor_id") or "").strip()
    session_id = str(payload.get("session_id") or "").strip()
    kind = str(payload.get("type") or "pageview").strip().lower()
    props = payload.get("props") if isinstance(payload.get("props"), dict) else {}
    is_demo = bool(props.get("is_demo") or payload.get("is_demo") or is_demo_hit(str(payload.get("path") or ""), str(payload.get("href") or "")))
    classified = classify_page(str(payload.get("path") or "/"), str(payload.get("href") or ""), is_demo)
    path = classified["path"][:400]
    payload["path"] = path
    payload["page_area"] = classified["area"]
    payload["page_part"] = classified["part"]
    payload["page_label"] = classified["label"]
    payload["is_demo"] = classified["area"] == "demo" or is_demo
    tables = _tables()

    visitor_row = _fetchone(
        conn,
        f"SELECT data, user_email FROM {tables['visitors']} WHERE visitor_id = ?",
        (visitor_id,),
    )
    visitor = _loads(_row_get(visitor_row, "data")) if visitor_row else {}
    visitor = _merge_visitor(visitor or None, payload, now)

    session_row = _fetchone(
        conn,
        f"SELECT data FROM {tables['sessions']} WHERE session_id = ?",
        (session_id,),
    )
    session = _loads(_row_get(session_row, "data")) if session_row else {}
    is_new_session = not session
    if is_new_session:
        session = {
            "session_id": session_id,
            "visitor_id": visitor_id,
            "started_at": now,
            "landing_path": path,
            "referrer": payload.get("referrer") or "",
            "referrer_host": host_from_url(str(payload.get("referrer") or "")),
            "utm_source": payload.get("utm_source") or "",
            "utm_medium": payload.get("utm_medium") or "",
            "utm_campaign": payload.get("utm_campaign") or "",
            "utm_term": payload.get("utm_term") or "",
            "utm_content": payload.get("utm_content") or "",
            "gclid": payload.get("gclid") or "",
            "fbclid": payload.get("fbclid") or "",
            "source": payload.get("source") or "direct",
            "country": payload.get("country") or "",
            "country_name": payload.get("country_name") or "",
            "city": payload.get("city") or "",
            "region": payload.get("region") or "",
            "place": payload.get("place") or "",
            "timezone": payload.get("timezone") or "",
            "language": payload.get("language") or "",
            "device": payload.get("device") or "",
            "os": payload.get("os") or "",
            "browser": payload.get("browser") or "",
            "user_agent": payload.get("user_agent") or "",
            "screen": payload.get("screen") or "",
            "page_count": 0,
            "duration_ms": 0,
            "paths": [],
            "demo_parts": [],
            "saw_demo": False,
        }
        visitor["session_count"] = int(visitor.get("session_count") or 0) + 1
    for key in ("country", "country_name", "city", "region", "place", "timezone", "language", "device", "os", "browser"):
        if payload.get(key):
            session[key] = payload[key]
    if payload.get("user_email"):
        session["user_email"] = payload["user_email"]
        visitor["user_email"] = payload["user_email"]
    session["last_seen_at"] = now
    session["exit_path"] = path
    started = _parse_ts(str(session.get("started_at") or now))
    current = _parse_ts(now)
    if started and current:
        session["duration_ms"] = max(0, int((current - started).total_seconds() * 1000))

    pageview_id = str(payload.get("pageview_id") or "").strip()
    if kind == "pageview":
        pageview_id = pageview_id or uuid.uuid4().hex
        page_data = {
            "id": pageview_id,
            "title": str(payload.get("title") or "")[:200],
            "href": str(payload.get("href") or "")[:600],
            "referrer": payload.get("referrer") or "",
            "duration_ms": int(payload.get("duration_ms") or 0),
            "scroll_pct": int(payload.get("scroll_pct") or 0),
            "viewport": payload.get("viewport") or "",
            "area": classified["area"],
            "part": classified["part"],
            "label": classified["label"],
            "is_demo": bool(payload.get("is_demo")),
        }
        _execute(
            conn,
            f"INSERT INTO {tables['page_views']}(id, session_id, visitor_id, path, at, data) VALUES (?, ?, ?, ?, ?, {_json_ph()})",
            (pageview_id, session_id, visitor_id, path, now, _dumps(page_data)),
        )
        visitor["pageview_count"] = int(visitor.get("pageview_count") or 0) + 1
        session["page_count"] = int(session.get("page_count") or 0) + 1
        paths = session.get("paths")
        if not isinstance(paths, list):
            paths = []
        if path not in paths:
            paths.append(path)
        session["paths"] = paths[:80]
        if payload.get("is_demo") or classified["area"] == "demo":
            session["saw_demo"] = True
            visitor["saw_demo"] = True
            parts = session.get("demo_parts")
            if not isinstance(parts, list):
                parts = []
            if classified["part"] not in parts:
                parts.append(classified["part"])
            session["demo_parts"] = parts[:20]
            vparts = visitor.get("demo_parts")
            if not isinstance(vparts, list):
                vparts = []
            if classified["part"] not in vparts:
                vparts.append(classified["part"])
            visitor["demo_parts"] = vparts[:20]
    elif kind == "heartbeat" and pageview_id:
        row = _fetchone(conn, f"SELECT data FROM {tables['page_views']} WHERE id = ?", (pageview_id,))
        if row:
            data = _loads(_row_get(row, "data"))
            data["duration_ms"] = max(int(data.get("duration_ms") or 0), int(payload.get("duration_ms") or 0))
            data["scroll_pct"] = max(int(data.get("scroll_pct") or 0), int(payload.get("scroll_pct") or 0))
            _execute(conn, f"UPDATE {tables['page_views']} SET data = {_json_ph()} WHERE id = ?", (_dumps(data), pageview_id))
    elif kind in {"event", "identify"}:
        event_id = uuid.uuid4().hex
        name = str(payload.get("event_name") or kind)[:80]
        event_data = {
            "path": path,
            "props": payload.get("props") if isinstance(payload.get("props"), dict) else {},
            "href": str(payload.get("href") or "")[:600],
        }
        _execute(
            conn,
            f"INSERT INTO {tables['events']}(id, session_id, visitor_id, name, at, data) VALUES (?, ?, ?, ?, ?, {_json_ph()})",
            (event_id, session_id, visitor_id, name, now, _dumps(event_data)),
        )
        if name in {"signup", "register"}:
            visitor["signed_up_at"] = visitor.get("signed_up_at") or now
            visitor["user_email"] = payload.get("user_email") or visitor.get("user_email")
            session["signed_up"] = True
        if name == "login":
            session["logged_in"] = True
        if name in {"demo_start", "demo_part"} or payload.get("is_demo"):
            session["saw_demo"] = True
            visitor["saw_demo"] = True

    visitor["visitor_id"] = visitor_id
    session["visitor_id"] = visitor_id
    email = str(visitor.get("user_email") or "").strip().lower() or None

    if visitor_row:
        _execute(
            conn,
            f"UPDATE {tables['visitors']} SET last_seen_at = ?, user_email = ?, data = {_json_ph()} WHERE visitor_id = ?",
            (now, email, _dumps(visitor), visitor_id),
        )
    else:
        _execute(
            conn,
            f"INSERT INTO {tables['visitors']}(visitor_id, first_seen_at, last_seen_at, user_email, data) VALUES (?, ?, ?, ?, {_json_ph()})",
            (visitor_id, str(visitor.get("first_seen_at") or now), now, email, _dumps(visitor)),
        )
    if session_row:
        _execute(
            conn,
            f"UPDATE {tables['sessions']} SET last_seen_at = ?, data = {_json_ph()} WHERE session_id = ?",
            (now, _dumps(session), session_id),
        )
    else:
        _execute(
            conn,
            f"INSERT INTO {tables['sessions']}(session_id, visitor_id, started_at, last_seen_at, data) VALUES (?, ?, ?, ?, {_json_ph()})",
            (session_id, visitor_id, str(session.get("started_at") or now), now, _dumps(session)),
        )

    if kind != "heartbeat" and path.split("?")[0] not in _SKIP_LEAD_PATHS:
        try:
            _upsert_lead_conn(
                conn,
                visitor_id=visitor_id,
                session=session,
                visitor=visitor,
                path=path,
                classified=classified,
                event_name=str(payload.get("event_name") or kind),
                now=now,
            )
        except Exception:
            pass

    return {"ok": True, "visitor_id": visitor_id, "session_id": session_id, "pageview_id": pageview_id}


def identify(visitor_id: str, session_id: str, email: str, event_name: str = "identify", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    vid = (visitor_id or "").strip()
    sid = (session_id or "").strip()
    mail = (email or "").strip().lower()
    if not vid or not mail:
        return {"ok": False, "ignored": "missing"}
    payload = {
        "type": "identify",
        "visitor_id": vid,
        "session_id": sid or f"auth-{uuid.uuid4().hex[:16]}",
        "user_email": mail,
        "event_name": event_name,
        "path": (extra or {}).get("path") or "/login",
        "at": _now(),
        "props": extra or {},
    }
    if extra:
        payload.update({k: v for k, v in extra.items() if k not in payload})
    return ingest(payload)


def _since_iso(days: int) -> str:
    days = max(1, min(int(days or 7), 365))
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


def _day_key(ts: str) -> str:
    parsed = _parse_ts(ts)
    if not parsed:
        return (ts or "")[:10]
    return parsed.astimezone(timezone.utc).date().isoformat()


def _registered_accounts() -> list[tuple[str, dict[str, Any]]]:
    try:
        from backend.services.user_store import load_users

        users = load_users()
    except Exception:
        return []
    out: list[tuple[str, dict[str, Any]]] = []
    for email, record in users.items():
        key = str(email or "").strip().lower()
        if not key or key == "demo@local" or not isinstance(record, dict):
            continue
        out.append((key, record))
    return out


def _backfill_users_as_leads_conn(conn: Any) -> dict[str, int]:
    """Copy existing registered accounts into the leads table so they are not hidden."""
    tables = _tables()
    now = _now()
    created = 0
    updated = 0
    accounts = _registered_accounts()
    for email, record in accounts:
        existing = _fetchone(conn, f"SELECT lead_id, data, created_at FROM {tables['leads']} WHERE email = ?", (email,))
        data = _loads(_row_get(existing, "data")) if existing else {}
        lead_id = str(_row_get(existing, "lead_id") or email)
        created_at = str(
            _row_get(existing, "created_at") or record.get("created_at") or data.get("created_at") or now
        )
        name = str(record.get("name") or data.get("name") or "").strip() or email.split("@")[0]
        attr = record.get("signup_attribution") if isinstance(record.get("signup_attribution"), dict) else {}
        visitor_id = str(data.get("visitor_id") or record.get("analytics_visitor_id") or attr.get("visitor_id") or "")
        already_linked = bool(
            existing and (data.get("from_account") or data.get("signed_up") or str(data.get("email") or "") == email)
        )
        stamp = now if not already_linked else str(_row_get(existing, "updated_at") or data.get("updated_at") or now)
        data["email"] = email
        data["name"] = name[:240]
        data["lead_id"] = lead_id
        data["from_account"] = True
        data["signed_up"] = True
        data["status"] = "signed_up"
        if visitor_id:
            data["visitor_id"] = visitor_id
        data["source"] = data.get("source") or str(attr.get("source") or "") or "account"
        data["place"] = data.get("place") or str(attr.get("place") or "")
        data["city"] = data.get("city") or str(attr.get("city") or "")
        data["country"] = data.get("country") or str(attr.get("country") or "")
        data["referrer"] = data.get("referrer") or str(attr.get("referrer") or "")
        data["landing_path"] = data.get("landing_path") or str(attr.get("landing_path") or "")
        data["utm_source"] = data.get("utm_source") or str(attr.get("utm_source") or "")
        data["utm_campaign"] = data.get("utm_campaign") or str(attr.get("utm_campaign") or "")
        data["device"] = data.get("device") or str(attr.get("device") or "")
        data["created_at"] = created_at
        data["updated_at"] = stamp
        if existing:
            _execute(
                conn,
                f"UPDATE {tables['leads']} SET email = ?, visitor_id = ?, updated_at = ?, data = {_json_ph()} WHERE lead_id = ?",
                (email, visitor_id or None, stamp, _dumps(data), lead_id),
            )
            updated += 1
        else:
            _execute(
                conn,
                f"INSERT INTO {tables['leads']}(lead_id, visitor_id, email, created_at, updated_at, data) VALUES (?, ?, ?, ?, ?, {_json_ph()})",
                (lead_id, visitor_id or None, email, created_at, now, _dumps(data)),
            )
            created += 1
    return {"created": created, "updated": updated, "accounts": len(accounts)}


@_with_conn
def overview(conn: Any, days: int = 7) -> dict[str, Any]:
    backfill = _backfill_users_as_leads_conn(conn)
    since = _since_iso(days)
    tables = _tables()
    sessions = _fetchall(
        conn,
        f"SELECT session_id, visitor_id, started_at, last_seen_at, data FROM {tables['sessions']} WHERE last_seen_at >= ?",
        (since,),
    )
    page_views = _fetchall(
        conn,
        f"SELECT id, session_id, visitor_id, path, at, data FROM {tables['page_views']} WHERE at >= ?",
        (since,),
    )
    events = _fetchall(
        conn,
        f"SELECT id, session_id, visitor_id, name, at, data FROM {tables['events']} WHERE at >= ?",
        (since,),
    )

    visitor_ids: set[str] = set()
    series_map: dict[str, dict[str, int]] = {}
    countries: dict[str, int] = {}
    cities: dict[str, int] = {}
    devices: dict[str, int] = {}
    browsers: dict[str, int] = {}
    sources: dict[str, int] = {}
    referrers: dict[str, int] = {}
    utm: dict[str, int] = {}
    pages: dict[str, dict[str, Any]] = {}
    signed_up_sessions = 0
    login_events = 0
    signup_events = 0
    demo_sessions = 0
    demo_parts: dict[str, int] = {}

    def bucket(day: str) -> dict[str, int]:
        row = series_map.setdefault(day, {"date": day, "visitors": 0, "sessions": 0, "pageviews": 0, "signups": 0})
        return row

    visitor_first_day: dict[str, str] = {}
    recent_sessions: list[dict[str, Any]] = []

    for row in sessions:
        data = _loads(_row_get(row, "data"))
        vid = str(_row_get(row, "visitor_id") or "")
        visitor_ids.add(vid)
        started = str(_row_get(row, "started_at") or data.get("started_at") or "")
        day = _day_key(started)
        bucket(day)["sessions"] += 1
        if vid and vid not in visitor_first_day:
            visitor_first_day[vid] = day
            bucket(day)["visitors"] += 1
        place = str(data.get("place") or data.get("country_name") or data.get("country") or "Unknown")
        country_key = str(data.get("country_name") or data.get("country") or "Unknown") or "Unknown"
        countries[country_key] = countries.get(country_key, 0) + 1
        city_key = place or "Unknown"
        cities[city_key] = cities.get(city_key, 0) + 1
        devices[str(data.get("device") or "Unknown")] = devices.get(str(data.get("device") or "Unknown"), 0) + 1
        browsers[str(data.get("browser") or "Unknown")] = browsers.get(str(data.get("browser") or "Unknown"), 0) + 1
        src = str(data.get("source") or "direct") or "direct"
        sources[src] = sources.get(src, 0) + 1
        host = str(data.get("referrer_host") or "") or ("direct" if src == "direct" else src)
        referrers[host] = referrers.get(host, 0) + 1
        utm_key = " / ".join(
            part
            for part in (
                str(data.get("utm_source") or "").strip(),
                str(data.get("utm_medium") or "").strip(),
                str(data.get("utm_campaign") or "").strip(),
            )
            if part
        )
        if utm_key:
            utm[utm_key] = utm.get(utm_key, 0) + 1
        if data.get("signed_up") or data.get("user_email"):
            signed_up_sessions += 1
        if data.get("saw_demo") or any(DEMO_MARKER in str(p) for p in (data.get("paths") or [])):
            demo_sessions += 1
            for part in data.get("demo_parts") or []:
                label = str(part)
                demo_parts[label] = demo_parts.get(label, 0) + 1
        recent_sessions.append(
            {
                "session_id": _row_get(row, "session_id"),
                "visitor_id": vid,
                "started_at": started,
                "last_seen_at": _row_get(row, "last_seen_at"),
                "duration_ms": int(data.get("duration_ms") or 0),
                "page_count": int(data.get("page_count") or 0),
                "landing_path": data.get("landing_path") or "",
                "exit_path": data.get("exit_path") or "",
                "paths": data.get("paths") if isinstance(data.get("paths"), list) else [],
                "referrer": data.get("referrer") or "",
                "referrer_host": data.get("referrer_host") or "",
                "source": src,
                "utm_source": data.get("utm_source") or "",
                "utm_medium": data.get("utm_medium") or "",
                "utm_campaign": data.get("utm_campaign") or "",
                "place": data.get("place") or "",
                "country": data.get("country") or "",
                "country_name": data.get("country_name") or "",
                "city": data.get("city") or "",
                "device": data.get("device") or "",
                "browser": data.get("browser") or "",
                "os": data.get("os") or "",
                "user_email": data.get("user_email") or "",
                "signed_up": bool(data.get("signed_up")),
            }
        )

    for row in page_views:
        path = str(_row_get(row, "path") or "/")
        at = str(_row_get(row, "at") or "")
        data = _loads(_row_get(row, "data"))
        bucket(_day_key(at))["pageviews"] += 1
        entry = pages.setdefault(path, {"path": path, "views": 0, "visitors": set(), "duration_ms": 0, "scroll_pct": 0})
        entry["views"] += 1
        entry["visitors"].add(_row_get(row, "visitor_id"))
        entry["duration_ms"] += int(data.get("duration_ms") or 0)
        entry["scroll_pct"] += int(data.get("scroll_pct") or 0)

    for row in events:
        name = str(_row_get(row, "name") or "")
        at = str(_row_get(row, "at") or "")
        if name in {"signup", "register"}:
            signup_events += 1
            bucket(_day_key(at))["signups"] += 1
        elif name == "login":
            login_events += 1

    funnel_paths = {"landed": 0, "pricing": 0, "login": 0, "signup": 0, "app": 0}
    for item in recent_sessions:
        paths = [str(p) for p in (item.get("paths") or [])]
        funnel_paths["landed"] += 1
        if any(p.startswith("/pricing") for p in paths) or item.get("landing_path") == "/pricing":
            funnel_paths["pricing"] += 1
        if any(p.startswith("/login") for p in paths):
            funnel_paths["login"] += 1
        if item.get("signed_up") or item.get("user_email"):
            funnel_paths["signup"] += 1
        if any(str(p).startswith("/app") for p in paths):
            funnel_paths["app"] += 1

    def top_map(src: dict[str, int], limit: int = 12) -> list[dict[str, Any]]:
        return [{"label": k, "count": v} for k, v in sorted(src.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]

    page_rows = []
    for path, entry in pages.items():
        views = int(entry["views"])
        unique = len(entry["visitors"])
        page_rows.append(
            {
                "path": path,
                "views": views,
                "unique_visitors": unique,
                "avg_duration_ms": int(entry["duration_ms"] / views) if views else 0,
                "avg_scroll_pct": int(entry["scroll_pct"] / views) if views else 0,
            }
        )
    page_rows.sort(key=lambda row: (-int(row["views"]), str(row["path"])))

    recent_sessions.sort(key=lambda row: str(row.get("last_seen_at") or ""), reverse=True)
    start = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 365)))
    series = []
    cursor = start.date()
    end = datetime.now(timezone.utc).date()
    while cursor <= end:
        key = cursor.isoformat()
        row = series_map.get(key) or {"date": key, "visitors": 0, "sessions": 0, "pageviews": 0, "signups": 0}
        series.append(row)
        cursor = cursor + timedelta(days=1)

    visitors = len(visitor_ids)
    session_count = len(sessions)
    conversion = round((signup_events / visitors) * 100, 1) if visitors else 0.0

    return {
        "range": {"days": days, "since": since, "until": _now()},
        "totals": {
            "visitors": visitors,
            "sessions": session_count,
            "pageviews": len(page_views),
            "signups": signup_events,
            "logins": login_events,
            "identified_sessions": signed_up_sessions,
            "signup_rate_pct": conversion,
            "demo_starts": demo_sessions,
            "registered_users": int(backfill.get("accounts") or 0),
        },
        "demo": {
            "started": demo_sessions,
            "parts": [{"label": k, "count": v} for k, v in sorted(demo_parts.items(), key=lambda kv: (-kv[1], kv[0]))],
        },
        "series": series,
        "top_pages": page_rows[:30],
        "top_countries": top_map(countries),
        "top_cities": top_map(cities),
        "top_devices": top_map(devices),
        "top_browsers": top_map(browsers),
        "top_sources": top_map(sources),
        "top_referrers": top_map(referrers),
        "top_campaigns": top_map(utm),
        "funnel": funnel_paths,
        "recent_sessions": recent_sessions[:80],
    }


@_with_conn
def list_sessions(conn: Any, days: int = 7, q: str = "", limit: int = 50, offset: int = 0) -> dict[str, Any]:
    since = _since_iso(days)
    tables = _tables()
    rows = _fetchall(
        conn,
        f"SELECT session_id, visitor_id, started_at, last_seen_at, data FROM {tables['sessions']} WHERE last_seen_at >= ? ORDER BY last_seen_at DESC",
        (since,),
    )
    needle = (q or "").strip().lower()
    items: list[dict[str, Any]] = []
    for row in rows:
        data = _loads(_row_get(row, "data"))
        item = {
            "session_id": _row_get(row, "session_id"),
            "visitor_id": _row_get(row, "visitor_id"),
            "started_at": _row_get(row, "started_at"),
            "last_seen_at": _row_get(row, "last_seen_at"),
            "duration_ms": int(data.get("duration_ms") or 0),
            "page_count": int(data.get("page_count") or 0),
            "landing_path": data.get("landing_path") or "",
            "exit_path": data.get("exit_path") or "",
            "paths": data.get("paths") if isinstance(data.get("paths"), list) else [],
            "referrer": data.get("referrer") or "",
            "referrer_host": data.get("referrer_host") or "",
            "source": data.get("source") or "direct",
            "utm_source": data.get("utm_source") or "",
            "utm_medium": data.get("utm_medium") or "",
            "utm_campaign": data.get("utm_campaign") or "",
            "place": data.get("place") or "",
            "country": data.get("country") or "",
            "country_name": data.get("country_name") or "",
            "city": data.get("city") or "",
            "region": data.get("region") or "",
            "timezone": data.get("timezone") or "",
            "language": data.get("language") or "",
            "device": data.get("device") or "",
            "browser": data.get("browser") or "",
            "os": data.get("os") or "",
            "screen": data.get("screen") or "",
            "user_email": data.get("user_email") or "",
            "signed_up": bool(data.get("signed_up")),
        }
        blob = " ".join(
            str(item.get(k) or "")
            for k in ("user_email", "place", "country_name", "city", "landing_path", "referrer_host", "source", "device", "visitor_id")
        ).lower()
        if needle and needle not in blob:
            continue
        items.append(item)
    total = len(items)
    sliced = items[max(0, offset) : max(0, offset) + max(1, min(limit, 200))]
    return {"sessions": sliced, "total": total}


@_with_conn
def session_detail(conn: Any, session_id: str) -> dict[str, Any] | None:
    tables = _tables()
    row = _fetchone(
        conn,
        f"SELECT session_id, visitor_id, started_at, last_seen_at, data FROM {tables['sessions']} WHERE session_id = ?",
        (session_id,),
    )
    if not row:
        return None
    data = _loads(_row_get(row, "data"))
    visitor_id = str(_row_get(row, "visitor_id") or "")
    visitor_row = _fetchone(conn, f"SELECT data, user_email, first_seen_at FROM {tables['visitors']} WHERE visitor_id = ?", (visitor_id,))
    visitor = _loads(_row_get(visitor_row, "data")) if visitor_row else {}
    pages = _fetchall(
        conn,
        f"SELECT id, path, at, data FROM {tables['page_views']} WHERE session_id = ? ORDER BY at ASC",
        (session_id,),
    )
    events = _fetchall(
        conn,
        f"SELECT id, name, at, data FROM {tables['events']} WHERE session_id = ? ORDER BY at ASC",
        (session_id,),
    )
    page_rows = []
    for page in pages:
        pdata = _loads(_row_get(page, "data"))
        page_rows.append(
            {
                "id": _row_get(page, "id"),
                "path": _row_get(page, "path"),
                "at": _row_get(page, "at"),
                "title": pdata.get("title") or "",
                "href": pdata.get("href") or "",
                "duration_ms": int(pdata.get("duration_ms") or 0),
                "scroll_pct": int(pdata.get("scroll_pct") or 0),
                "label": pdata.get("label") or "",
                "part": pdata.get("part") or "",
                "is_demo": bool(pdata.get("is_demo")),
            }
        )
    event_rows = []
    for event in events:
        edata = _loads(_row_get(event, "data"))
        event_rows.append(
            {
                "id": _row_get(event, "id"),
                "name": _row_get(event, "name"),
                "at": _row_get(event, "at"),
                "path": edata.get("path") or "",
                "props": edata.get("props") if isinstance(edata.get("props"), dict) else {},
            }
        )
    return {
        "session": {
            "session_id": _row_get(row, "session_id"),
            "visitor_id": visitor_id,
            "started_at": _row_get(row, "started_at"),
            "last_seen_at": _row_get(row, "last_seen_at"),
            **data,
        },
        "visitor": visitor,
        "pages": page_rows,
        "events": event_rows,
    }


def attribution_for_visitor(visitor_id: str) -> dict[str, Any]:
    if not visitor_id:
        return {}

    @_with_conn
    def _read(conn: Any) -> dict[str, Any]:
        tables = _tables()
        row = _fetchone(conn, f"SELECT data, user_email, first_seen_at FROM {tables['visitors']} WHERE visitor_id = ?", (visitor_id,))
        if not row:
            return {}
        data = _loads(_row_get(row, "data"))
        return {
            "visitor_id": visitor_id,
            "first_seen_at": _row_get(row, "first_seen_at") or data.get("first_seen_at") or "",
            "landing_path": data.get("landing_path") or "",
            "referrer": data.get("referrer") or "",
            "referrer_host": data.get("referrer_host") or "",
            "source": data.get("source") or "",
            "utm_source": data.get("utm_source") or "",
            "utm_medium": data.get("utm_medium") or "",
            "utm_campaign": data.get("utm_campaign") or "",
            "utm_term": data.get("utm_term") or "",
            "utm_content": data.get("utm_content") or "",
            "place": data.get("place") or "",
            "country": data.get("country") or "",
            "city": data.get("city") or "",
            "device": data.get("device") or "",
        }

    return _read()


def _lead_public(lead_id: str, data: dict[str, Any], created_at: str = "", updated_at: str = "") -> dict[str, Any]:
    email = str(data.get("email") or "").strip().lower()
    name = str(data.get("name") or "").strip()
    if not name:
        place = str(data.get("place") or data.get("city") or "")
        name = email or (f"Visitor in {place}" if place else f"Visitor {lead_id[:8]}")
    return {
        "lead_id": lead_id,
        "visitor_id": data.get("visitor_id") or "",
        "email": email,
        "name": name,
        "phone": data.get("phone") or "",
        "company": data.get("company") or "",
        "status": data.get("status") or "visitor",
        "source": data.get("source") or "direct",
        "place": data.get("place") or "",
        "country": data.get("country") or "",
        "city": data.get("city") or "",
        "landing_path": data.get("landing_path") or "",
        "last_path": data.get("last_path") or "",
        "journey": data.get("journey") if isinstance(data.get("journey"), list) else [],
        "demo_parts": data.get("demo_parts") if isinstance(data.get("demo_parts"), list) else [],
        "saw_demo": bool(data.get("saw_demo")),
        "page_count": int(data.get("page_count") or len(data.get("journey") or [])),
        "notes": data.get("notes") or "",
        "created_at": created_at or data.get("created_at") or "",
        "updated_at": updated_at or data.get("updated_at") or "",
        "imported": bool(data.get("imported")),
        "signed_up": bool(data.get("signed_up") or data.get("status") == "signed_up"),
        "utm_source": data.get("utm_source") or "",
        "utm_campaign": data.get("utm_campaign") or "",
        "referrer": data.get("referrer") or "",
        "device": data.get("device") or "",
    }


def _upsert_lead_conn(
    conn: Any,
    *,
    visitor_id: str,
    session: dict[str, Any],
    visitor: dict[str, Any],
    path: str,
    classified: dict[str, str],
    event_name: str,
    now: str,
) -> None:
    tables = _tables()
    email = str(visitor.get("user_email") or session.get("user_email") or "").strip().lower()
    if email == "demo@local":
        email = ""
    row = None
    if email:
        row = _fetchone(conn, f"SELECT lead_id, data, created_at FROM {tables['leads']} WHERE email = ?", (email,))
    if not row and visitor_id:
        row = _fetchone(conn, f"SELECT lead_id, data, created_at FROM {tables['leads']} WHERE visitor_id = ?", (visitor_id,))
    data = _loads(_row_get(row, "data")) if row else {}
    lead_id = str(_row_get(row, "lead_id") or "") if row else (email or visitor_id or uuid.uuid4().hex)
    created_at = str(_row_get(row, "created_at") or now) if row else now
    journey = data.get("journey") if isinstance(data.get("journey"), list) else []
    if path and (not journey or journey[-1] != path):
        journey.append(path)
    demo_parts = data.get("demo_parts") if isinstance(data.get("demo_parts"), list) else []
    if classified.get("area") == "demo" and classified.get("part") and classified["part"] not in demo_parts:
        demo_parts.append(classified["part"])
    status = str(data.get("status") or "visitor")
    if event_name in {"signup", "register"} or (email and status in {"visitor", "demo"}):
        status = "signed_up" if event_name in {"signup", "register"} else status
    if classified.get("area") == "demo" or event_name in {"demo_start", "demo_part"}:
        if status == "visitor":
            status = "demo"
    if event_name in {"signup", "register"}:
        status = "signed_up"
    if data.get("imported") and status == "visitor":
        status = "imported"
    merged = dict(data)
    merged.update(
        {
            "lead_id": lead_id,
            "visitor_id": visitor_id or data.get("visitor_id") or "",
            "email": email or data.get("email") or "",
            "name": data.get("name") or "",
            "status": status,
            "source": data.get("source") or session.get("source") or visitor.get("source") or "direct",
            "place": session.get("place") or visitor.get("place") or data.get("place") or "",
            "country": session.get("country") or visitor.get("country") or data.get("country") or "",
            "city": session.get("city") or visitor.get("city") or data.get("city") or "",
            "landing_path": data.get("landing_path") or visitor.get("landing_path") or session.get("landing_path") or path,
            "last_path": path,
            "journey": journey[-80:],
            "demo_parts": demo_parts[:20],
            "saw_demo": bool(data.get("saw_demo") or session.get("saw_demo") or classified.get("area") == "demo"),
            "page_count": len(journey[-80:]),
            "utm_source": data.get("utm_source") or session.get("utm_source") or visitor.get("utm_source") or "",
            "utm_campaign": data.get("utm_campaign") or session.get("utm_campaign") or "",
            "referrer": data.get("referrer") or session.get("referrer") or visitor.get("referrer") or "",
            "device": session.get("device") or visitor.get("device") or data.get("device") or "",
            "signed_up": status == "signed_up",
            "updated_at": now,
            "created_at": created_at,
        }
    )
    if row:
        _execute(
            conn,
            f"UPDATE {tables['leads']} SET visitor_id = ?, email = ?, updated_at = ?, data = {_json_ph()} WHERE lead_id = ?",
            (visitor_id or _row_get(row, "visitor_id"), email or None, now, _dumps(merged), lead_id),
        )
    else:
        _execute(
            conn,
            f"INSERT INTO {tables['leads']}(lead_id, visitor_id, email, created_at, updated_at, data) VALUES (?, ?, ?, ?, ?, {_json_ph()})",
            (lead_id, visitor_id or None, email or None, created_at, now, _dumps(merged)),
        )


@_with_conn
def page_people(conn: Any, path: str, days: int = 7) -> dict[str, Any]:
    since = _since_iso(days)
    tables = _tables()
    wanted = (path or "").strip() or "/"
    base_wanted = wanted.split("?")[0] or "/"
    rows = _fetchall(
        conn,
        f"SELECT visitor_id, session_id, path, at, data FROM {tables['page_views']} WHERE at >= ? ORDER BY at DESC",
        (since,),
    )
    people: dict[str, dict[str, Any]] = {}
    views = 0
    for row in rows:
        p = str(_row_get(row, "path") or "")
        if p != wanted and p.split("?")[0] != base_wanted:
            continue
        views += 1
        vid = str(_row_get(row, "visitor_id") or "")
        entry = people.setdefault(
            vid,
            {"visitor_id": vid, "views": 0, "last_seen_at": "", "first_seen_at": str(_row_get(row, "at") or "")},
        )
        entry["views"] += 1
        entry["last_seen_at"] = entry["last_seen_at"] or str(_row_get(row, "at") or "")
        pdata = _loads(_row_get(row, "data"))
        entry["duration_ms"] = int(entry.get("duration_ms") or 0) + int(pdata.get("duration_ms") or 0)
        entry["label"] = pdata.get("label") or wanted
    visitors = []
    for vid, entry in people.items():
        vrow = _fetchone(conn, f"SELECT data, user_email FROM {tables['visitors']} WHERE visitor_id = ?", (vid,))
        vdata = _loads(_row_get(vrow, "data")) if vrow else {}
        lrow = _fetchone(conn, f"SELECT lead_id, data FROM {tables['leads']} WHERE visitor_id = ?", (vid,))
        ldata = _loads(_row_get(lrow, "data")) if lrow else {}
        email = str(_row_get(vrow, "user_email") or vdata.get("user_email") or ldata.get("email") or "")
        visitors.append(
            {
                **entry,
                "email": email if email != "demo@local" else "",
                "name": ldata.get("name") or email or f"Visitor {vid[:8]}",
                "place": vdata.get("place") or ldata.get("place") or "",
                "source": vdata.get("source") or ldata.get("source") or "",
                "lead_id": _row_get(lrow, "lead_id") if lrow else vid,
                "journey": vdata.get("last_path") or "",
            }
        )
    visitors.sort(key=lambda row: str(row.get("last_seen_at") or ""), reverse=True)
    return {"path": wanted, "views": views, "unique_visitors": len(visitors), "people": visitors[:200]}


@_with_conn
def visitor_journey(conn: Any, visitor_id: str) -> dict[str, Any] | None:
    tables = _tables()
    row = _fetchone(conn, f"SELECT data, user_email, first_seen_at, last_seen_at FROM {tables['visitors']} WHERE visitor_id = ?", (visitor_id,))
    if not row:
        return None
    visitor = _loads(_row_get(row, "data"))
    sessions = _fetchall(
        conn,
        f"SELECT session_id, started_at, last_seen_at, data FROM {tables['sessions']} WHERE visitor_id = ? ORDER BY started_at ASC",
        (visitor_id,),
    )
    pages = _fetchall(
        conn,
        f"SELECT id, session_id, path, at, data FROM {tables['page_views']} WHERE visitor_id = ? ORDER BY at ASC",
        (visitor_id,),
    )
    lead = _fetchone(conn, f"SELECT lead_id, data FROM {tables['leads']} WHERE visitor_id = ?", (visitor_id,))
    journey = []
    for page in pages:
        pdata = _loads(_row_get(page, "data"))
        journey.append(
            {
                "id": _row_get(page, "id"),
                "session_id": _row_get(page, "session_id"),
                "path": _row_get(page, "path"),
                "at": _row_get(page, "at"),
                "title": pdata.get("title") or "",
                "duration_ms": int(pdata.get("duration_ms") or 0),
                "scroll_pct": int(pdata.get("scroll_pct") or 0),
                "label": pdata.get("label") or "",
                "part": pdata.get("part") or "",
                "is_demo": bool(pdata.get("is_demo")),
            }
        )
    return {
        "visitor_id": visitor_id,
        "email": _row_get(row, "user_email") or visitor.get("user_email") or "",
        "first_seen_at": _row_get(row, "first_seen_at"),
        "last_seen_at": _row_get(row, "last_seen_at"),
        "visitor": visitor,
        "lead": _lead_public(_row_get(lead, "lead_id"), _loads(_row_get(lead, "data"))) if lead else None,
        "sessions": [
            {
                "session_id": _row_get(s, "session_id"),
                "started_at": _row_get(s, "started_at"),
                "last_seen_at": _row_get(s, "last_seen_at"),
                "paths": _loads(_row_get(s, "data")).get("paths") or [],
                "demo_parts": _loads(_row_get(s, "data")).get("demo_parts") or [],
                "duration_ms": int(_loads(_row_get(s, "data")).get("duration_ms") or 0),
            }
            for s in sessions
        ],
        "journey": journey,
    }


@_with_conn
def list_leads(conn: Any, q: str = "", status: str = "", limit: int = 80, offset: int = 0) -> dict[str, Any]:
    _backfill_users_as_leads_conn(conn)
    tables = _tables()
    rows = _fetchall(
        conn,
        f"SELECT lead_id, visitor_id, email, created_at, updated_at, data FROM {tables['leads']} ORDER BY updated_at DESC",
        (),
    )
    needle = (q or "").strip().lower()
    wanted = (status or "").strip().lower()
    items = []
    for row in rows:
        data = _loads(_row_get(row, "data"))
        item = _lead_public(
            str(_row_get(row, "lead_id") or ""),
            data,
            created_at=str(_row_get(row, "created_at") or ""),
            updated_at=str(_row_get(row, "updated_at") or ""),
        )
        if wanted and item["status"] != wanted:
            continue
        blob = " ".join(str(item.get(k) or "") for k in ("email", "name", "company", "place", "source", "last_path", "status")).lower()
        if needle and needle not in blob:
            continue
        items.append(item)
    totals = {
        "leads": len(items),
        "visitors": sum(1 for i in items if i["status"] == "visitor"),
        "demo": sum(1 for i in items if i["status"] == "demo" or i["saw_demo"]),
        "signed_up": sum(1 for i in items if i["signed_up"]),
        "imported": sum(1 for i in items if i["imported"] or i["status"] == "imported"),
    }
    sliced = items[max(0, offset) : max(0, offset) + max(1, min(limit, 300))]
    return {"leads": sliced, "total": len(items), "totals": totals}


@_with_conn
def import_leads(conn: Any, rows: list[dict[str, Any]], imported_by: str = "") -> dict[str, Any]:
    tables = _tables()
    now = _now()
    created = 0
    updated = 0
    skipped = 0
    for raw in rows[:2000]:
        email = str(raw.get("email") or "").strip().lower()
        phone = str(raw.get("phone") or "").strip()
        name = str(raw.get("name") or "").strip()
        if not email and not phone and not name:
            skipped += 1
            continue
        existing = None
        if email:
            existing = _fetchone(conn, f"SELECT lead_id, data, created_at FROM {tables['leads']} WHERE email = ?", (email,))
        lead_id = str(_row_get(existing, "lead_id") or email or uuid.uuid4().hex)
        data = _loads(_row_get(existing, "data")) if existing else {}
        created_at = str(_row_get(existing, "created_at") or now) if existing else now
        for key in ("name", "phone", "company", "source", "place", "city", "country", "notes", "website"):
            val = str(raw.get(key) or "").strip()
            if val:
                data[key] = val[:240]
        if email:
            data["email"] = email
        data["status"] = data.get("status") if data.get("status") in {"signed_up"} else "imported"
        data["imported"] = True
        data["imported_by"] = imported_by
        data["imported_at"] = now
        data["source"] = data.get("source") or str(raw.get("source") or "sheet") or "sheet"
        data["updated_at"] = now
        data["created_at"] = created_at
        data["lead_id"] = lead_id
        if existing:
            _execute(
                conn,
                f"UPDATE {tables['leads']} SET email = ?, updated_at = ?, data = {_json_ph()} WHERE lead_id = ?",
                (email or None, now, _dumps(data), lead_id),
            )
            updated += 1
        else:
            _execute(
                conn,
                f"INSERT INTO {tables['leads']}(lead_id, visitor_id, email, created_at, updated_at, data) VALUES (?, ?, ?, ?, ?, {_json_ph()})",
                (lead_id, data.get("visitor_id") or None, email or None, created_at, now, _dumps(data)),
            )
            created += 1
    return {"ok": True, "created": created, "updated": updated, "skipped": skipped}


# Re-export for callers that only need classification at ingest time.
def source_from_payload(payload: dict[str, Any], landing_host: str = "") -> str:
    return classify_source(
        referrer=str(payload.get("referrer") or ""),
        utm_source=str(payload.get("utm_source") or ""),
        utm_medium=str(payload.get("utm_medium") or ""),
        landing_host=landing_host,
    )
