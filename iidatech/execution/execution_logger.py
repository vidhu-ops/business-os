"""Persist and query tool execution logs for founder live workspace."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from iidatech.storage.db import ensure_execution_schema, get_connection, row_to_dict, sql_placeholder


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _new_id() -> str:
    return f"tex_{uuid.uuid4().hex[:12]}"


def log_tool_execution(
    *,
    report_id: str,
    tool_name: str,
    outcome: dict[str, Any],
    task_id: str = "",
    employee_id: str = "",
) -> str:
    ensure_execution_schema()
    log_id = _new_id()
    p = sql_placeholder()
    sql = f"""INSERT INTO tool_execution_logs
    (log_id, task_id, report_id, employee_id, tool_name, execution_mode, verified, success,
     artifacts_json, metrics_json, logs_json, errors_json, result_json, created_at)
    VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p},{p})"""
    params = [
        log_id,
        task_id or None,
        report_id,
        employee_id or None,
        tool_name,
        str(outcome.get("execution_mode") or "simulated"),
        1 if outcome.get("verified") else 0,
        1 if outcome.get("success") else 0,
        json.dumps(outcome.get("artifacts") or [], ensure_ascii=False),
        json.dumps(outcome.get("metrics") or {}, ensure_ascii=False),
        json.dumps(outcome.get("logs") or [], ensure_ascii=False),
        json.dumps(outcome.get("errors") or [], ensure_ascii=False),
        json.dumps(outcome.get("result") or {}, ensure_ascii=False),
        _now(),
    ]
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
        finally:
            cur.close()
    return log_id


def list_tool_executions(report_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
    ensure_execution_schema()
    p = sql_placeholder()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT * FROM tool_execution_logs WHERE report_id = {p} ORDER BY created_at DESC LIMIT {p}",
                [report_id, int(limit)],
            )
            rows = cur.fetchall()
        finally:
            cur.close()
    out = []
    for row in rows:
        d = row_to_dict(row)
        for key, default in (
            ("artifacts_json", []),
            ("metrics_json", {}),
            ("logs_json", []),
            ("errors_json", []),
            ("result_json", {}),
        ):
            raw = d.pop(key, None)
            try:
                d[key.replace("_json", "")] = json.loads(raw) if raw else default
            except (json.JSONDecodeError, TypeError):
                d[key.replace("_json", "")] = default
        d["verified"] = bool(d.get("verified"))
        d["success"] = bool(d.get("success"))
        out.append(d)
    return out