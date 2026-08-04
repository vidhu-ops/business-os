"""Durable user account store (SQLite by default, Postgres when DATABASE_URL is set)."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

_lock = threading.RLock()
_pg_ready: bool | None = None


def _data_dir() -> Path:
    raw = (
        os.getenv("DATA_DIR")
        or os.getenv("BUSINESS_OUTPUTS_ROOT")
        or ""
    ).strip()
    if raw:
        path = Path(raw)
    else:
        from backend.config import settings

        path = settings.outputs_root
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sqlite_path() -> Path:
    explicit = (os.getenv("USER_DB_PATH") or "").strip()
    if explicit:
        path = Path(explicit)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    return _data_dir() / "iidatech_users.sqlite"


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


def _sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_sqlite_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY,
            data TEXT NOT NULL
        )
        """
    )
    conn.commit()
    return conn


def _pg_connect():
    import psycopg

    url = _database_url()
    # Render/Neon sometimes provide postgres://
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    conn = psycopg.connect(url)
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                data JSONB NOT NULL
            )
            """
        )
    conn.commit()
    return conn


def _migrate_json_into_sqlite_if_needed(conn: sqlite3.Connection) -> None:
    row = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    if row and int(row["c"] or 0) > 0:
        return
    from backend.config import settings

    path = settings.local_users_path
    if not path.is_file():
        return
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    if not isinstance(payload, dict):
        return
    for email, record in payload.items():
        if not isinstance(record, dict):
            continue
        key = str(email or "").strip().lower()
        if not key:
            continue
        data = dict(record)
        data["email"] = key
        conn.execute(
            "INSERT OR REPLACE INTO users(email, data) VALUES (?, ?)",
            (key, json.dumps(data, ensure_ascii=False, default=str)),
        )
    conn.commit()


def load_users() -> dict[str, Any]:
    with _lock:
        if _use_postgres():
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT email, data FROM users")
                    rows = cur.fetchall()
                out: dict[str, Any] = {}
                for email, data in rows:
                    if isinstance(data, dict):
                        out[str(email).lower()] = data
                    else:
                        parsed = json.loads(data) if isinstance(data, str) else {}
                        if isinstance(parsed, dict):
                            out[str(email).lower()] = parsed
                return out
            finally:
                conn.close()

        conn = _sqlite_conn()
        try:
            _migrate_json_into_sqlite_if_needed(conn)
            rows = conn.execute("SELECT email, data FROM users").fetchall()
            out = {}
            for row in rows:
                try:
                    data = json.loads(row["data"])
                except Exception:
                    continue
                if isinstance(data, dict):
                    out[str(row["email"]).lower()] = data
            return out
        finally:
            conn.close()


def save_users(users: dict[str, Any]) -> None:
    with _lock:
        # Always keep a JSON backup for local/debug and older tooling.
        try:
            from backend.config import settings

            path = settings.local_users_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(users, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        except Exception:
            pass

        if _use_postgres():
            conn = _pg_connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM users")
                    for email, record in users.items():
                        key = str(email or "").strip().lower()
                        if not key or not isinstance(record, dict):
                            continue
                        data = dict(record)
                        data["email"] = key
                        cur.execute(
                            "INSERT INTO users(email, data) VALUES (%s, %s::jsonb)",
                            (key, json.dumps(data, ensure_ascii=False, default=str)),
                        )
                conn.commit()
            finally:
                conn.close()
            return

        conn = _sqlite_conn()
        try:
            conn.execute("DELETE FROM users")
            for email, record in users.items():
                key = str(email or "").strip().lower()
                if not key or not isinstance(record, dict):
                    continue
                data = dict(record)
                data["email"] = key
                conn.execute(
                    "INSERT INTO users(email, data) VALUES (?, ?)",
                    (key, json.dumps(data, ensure_ascii=False, default=str)),
                )
            conn.commit()
        finally:
            conn.close()


def upsert_user(email: str, record: dict[str, Any]) -> dict[str, Any]:
    key = str(email or "").strip().lower()
    users = load_users()
    data = dict(record)
    data["email"] = key
    users[key] = data
    save_users(users)
    return data