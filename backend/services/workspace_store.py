"""Durable workspace index — keeps projects across redeploys (SQLite / Postgres)."""
from __future__ import annotations

import json
import os
import sqlite3
import threading
from pathlib import Path
from typing import Any

_lock = threading.RLock()


def _db_path() -> Path:
    explicit = (os.getenv("WORKSPACE_DB_PATH") or os.getenv("USER_DB_PATH") or "").strip()
    if explicit:
        path = Path(explicit)
        # If USER_DB_PATH points at users db, use sibling workspaces db
        if path.name == "iidatech_users.sqlite":
            path = path.with_name("iidatech_workspaces.sqlite")
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    raw = (os.getenv("DATA_DIR") or os.getenv("BUSINESS_OUTPUTS_ROOT") or "").strip()
    if raw:
        root = Path(raw)
    else:
        from backend.config import settings

        root = settings.outputs_root
    root.mkdir(parents=True, exist_ok=True)
    return root / "iidatech_workspaces.sqlite"


def _database_url() -> str:
    return (os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or "").strip()


def _use_postgres() -> bool:
    if not _database_url():
        return False
    try:
        import psycopg  # noqa: F401

        return True
    except Exception:
        return False


def _sqlite() -> sqlite3.Connection:
    conn = sqlite3.connect(str(_db_path()), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS workspaces (
            workspace_id TEXT PRIMARY KEY,
            owner_email TEXT NOT NULL,
            data TEXT NOT NULL,
            updated_at TEXT
        )
        """
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_ws_owner ON workspaces(owner_email)")
    conn.commit()
    return conn


def _pg():
    import psycopg

    url = _database_url()
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    conn = psycopg.connect(url)
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS workspaces (
                workspace_id TEXT PRIMARY KEY,
                owner_email TEXT NOT NULL,
                data JSONB NOT NULL,
                updated_at TEXT
            )
            """
        )
        cur.execute("CREATE INDEX IF NOT EXISTS idx_ws_owner ON workspaces(owner_email)")
    conn.commit()
    return conn


def persist_workspace(payload: dict[str, Any]) -> None:
    if not payload or payload.get("demo_readonly"):
        return
    wid = str(payload.get("workspace_id") or "").strip()
    owner = str(payload.get("owner_email") or "").strip().lower()
    if not wid or not owner:
        return
    updated = str(payload.get("updated_at") or "")
    blob = json.dumps(payload, ensure_ascii=False, default=str)
    with _lock:
        if _use_postgres():
            conn = _pg()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO workspaces(workspace_id, owner_email, data, updated_at)
                        VALUES (%s, %s, %s::jsonb, %s)
                        ON CONFLICT (workspace_id) DO UPDATE SET
                          owner_email = EXCLUDED.owner_email,
                          data = EXCLUDED.data,
                          updated_at = EXCLUDED.updated_at
                        """,
                        (wid, owner, blob, updated),
                    )
                conn.commit()
            finally:
                conn.close()
            return
        conn = _sqlite()
        try:
            conn.execute(
                """
                INSERT INTO workspaces(workspace_id, owner_email, data, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(workspace_id) DO UPDATE SET
                  owner_email = excluded.owner_email,
                  data = excluded.data,
                  updated_at = excluded.updated_at
                """,
                (wid, owner, blob, updated),
            )
            conn.commit()
        finally:
            conn.close()


def fetch_workspace(workspace_id: str) -> dict[str, Any] | None:
    wid = str(workspace_id or "").strip()
    if not wid:
        return None
    with _lock:
        if _use_postgres():
            conn = _pg()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT data FROM workspaces WHERE workspace_id = %s", (wid,))
                    row = cur.fetchone()
                if not row:
                    return None
                data = row[0]
                return data if isinstance(data, dict) else json.loads(data)
            except Exception:
                return None
            finally:
                conn.close()
        conn = _sqlite()
        try:
            row = conn.execute("SELECT data FROM workspaces WHERE workspace_id = ?", (wid,)).fetchone()
            if not row:
                return None
            return json.loads(row["data"])
        except Exception:
            return None
        finally:
            conn.close()


def list_owner_workspaces(owner_email: str, limit: int = 50) -> list[dict[str, Any]]:
    owner = str(owner_email or "").strip().lower()
    if not owner:
        return []
    with _lock:
        rows_out: list[dict[str, Any]] = []
        if _use_postgres():
            conn = _pg()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT data FROM workspaces
                        WHERE owner_email = %s
                        ORDER BY updated_at DESC NULLS LAST
                        LIMIT %s
                        """,
                        (owner, limit),
                    )
                    for (data,) in cur.fetchall():
                        payload = data if isinstance(data, dict) else json.loads(data)
                        if isinstance(payload, dict):
                            rows_out.append(payload)
            except Exception:
                return []
            finally:
                conn.close()
            return rows_out
        conn = _sqlite()
        try:
            rows = conn.execute(
                """
                SELECT data FROM workspaces
                WHERE owner_email = ?
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (owner, limit),
            ).fetchall()
            for row in rows:
                try:
                    payload = json.loads(row["data"])
                except Exception:
                    continue
                if isinstance(payload, dict):
                    rows_out.append(payload)
            return rows_out
        finally:
            conn.close()