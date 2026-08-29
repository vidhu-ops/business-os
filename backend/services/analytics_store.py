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

_lock = threading.RLock()
_pg_ready: bool | None = None

SESSION_IDLE_MINUTES = 30


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
"""


def _tables() -> dict[str, str]:
    if _use_postgres():
        return {
            "visitors": "analytics_visitors",
            "sessions": "analytics_sessions",
            "page_views": "analytics_page_views",
            "events": "analytics_events",
        }
    return {
        "visitors": "visitors",
        "sessions": "sessions",
        "page_views": "page_views",
        "events": "events",
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
    path = str(payload.get("path") or "/")[:400]
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


@_with_conn
def overview(conn: Any, days: int = 7) -> dict[str, Any]:
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


# Re-export for callers that only need classification at ingest time.
def source_from_payload(payload: dict[str, Any], landing_host: str = "") -> str:
    return classify_source(
        referrer=str(payload.get("referrer") or ""),
        utm_source=str(payload.get("utm_source") or ""),
        utm_medium=str(payload.get("utm_medium") or ""),
        landing_host=landing_host,
    )
