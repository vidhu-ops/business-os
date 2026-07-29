"""SQL persistence for Employee OS."""
from __future__ import annotations
import json, uuid
from datetime import datetime, timezone
from typing import Any
from iidatech.storage.db import ensure_execution_schema, get_connection, row_to_dict, sql_placeholder

def _ph():
    return sql_placeholder()

def _now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def _new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:12]}"

def _json_dumps(v):
    return json.dumps(v if v is not None else [], ensure_ascii=False)

def _json_loads(raw, default):
    if raw is None:
        return default
    if isinstance(raw, (list, dict)):
        return raw
    try:
        return json.loads(str(raw))
    except (json.JSONDecodeError, TypeError):
        return default

def insert_employee(report_id, *, name, role, department="", authority_level=5, skills=None, performance_score=5.0):
    ensure_execution_schema()
    eid = _new_id("emp")
    p = _ph()
    sql = f"INSERT INTO employees (employee_id, report_id, name, role, department, authority_level, skills_json, performance_score, is_active, created_at) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},1,{p})"
    params = [eid, report_id, name, role, department, int(authority_level), _json_dumps(skills or []), float(performance_score), _now()]
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
        finally:
            cur.close()
    return get_employee(eid) or {"employee_id": eid, "name": name, "role": role}

def get_employee(employee_id):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM employees WHERE employee_id = {p} LIMIT 1", [employee_id])
            row = cur.fetchone()
        finally:
            cur.close()
    if not row:
        return None
    d = row_to_dict(row)
    d["skills"] = _json_loads(d.pop("skills_json", None), [])
    d["is_active"] = bool(d.get("is_active", 1))
    return d

def list_employees(report_id, *, active_only=True):
    ensure_execution_schema()
    p = _ph()
    clause = f"report_id = {p}" + (" AND is_active = 1" if active_only else "")
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM employees WHERE {clause} ORDER BY authority_level DESC", [report_id])
            rows = cur.fetchall()
        finally:
            cur.close()
    out = []
    for row in rows:
        d = row_to_dict(row)
        d["skills"] = _json_loads(d.pop("skills_json", None), [])
        d["is_active"] = bool(d.get("is_active", 1))
        out.append(d)
    return out

def deactivate_employee(employee_id):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"UPDATE employees SET is_active = 0 WHERE employee_id = {p}", [employee_id])
            conn.commit()
            return cur.rowcount > 0
        finally:
            cur.close()

def insert_task(report_id, *, title, owner_employee_id=None, status="open", priority="medium", dependencies=None, blockers=None, due_date=None):
    ensure_execution_schema()
    tid = _new_id("task")
    p = _ph()
    sql = f"INSERT INTO tasks (task_id, report_id, title, owner_employee_id, status, priority, dependencies_json, blockers_json, due_date, created_at) VALUES ({p},{p},{p},{p},{p},{p},{p},{p},{p},{p})"
    params = [tid, report_id, title, owner_employee_id, status, priority, _json_dumps(dependencies or []), _json_dumps(blockers or []), due_date, _now()]
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            conn.commit()
        finally:
            cur.close()
    return get_task(tid) or {"task_id": tid, "title": title}

def get_task(task_id):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM tasks WHERE task_id = {p} LIMIT 1", [task_id])
            row = cur.fetchone()
        finally:
            cur.close()
    if not row:
        return None
    d = row_to_dict(row)
    d["dependencies"] = _json_loads(d.pop("dependencies_json", None), [])
    d["blockers"] = _json_loads(d.pop("blockers_json", None), [])
    return d

def list_tasks(report_id, *, status=None):
    ensure_execution_schema()
    p = _ph()
    sql = f"SELECT * FROM tasks WHERE report_id = {p}"
    params = [report_id]
    if status:
        sql += f" AND status = {p}"
        params.append(status)
    sql += " ORDER BY created_at DESC"
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
        finally:
            cur.close()
    out = []
    for row in rows:
        d = row_to_dict(row)
        d["dependencies"] = _json_loads(d.pop("dependencies_json", None), [])
        d["blockers"] = _json_loads(d.pop("blockers_json", None), [])
        out.append(d)
    return out

def update_task(task_id, **fields):
    ensure_execution_schema()
    mapping = {"title": "title", "owner_employee_id": "owner_employee_id", "status": "status", "priority": "priority", "due_date": "due_date"}
    sets, params = [], []
    p = _ph()
    for key, col in mapping.items():
        if key in fields:
            sets.append(f"{col} = {p}")
            params.append(fields[key])
    if "dependencies" in fields:
        sets.append(f"dependencies_json = {p}")
        params.append(_json_dumps(fields["dependencies"]))
    if "blockers" in fields:
        sets.append(f"blockers_json = {p}")
        params.append(_json_dumps(fields["blockers"]))
    if not sets:
        return get_task(task_id)
    params.append(task_id)
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE task_id = {p}", params)
            conn.commit()
        finally:
            cur.close()
    return get_task(task_id)

def ensure_war_room(report_id):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT room_id FROM team_rooms WHERE report_id = {p} AND room_type = {p} LIMIT 1", [report_id, "war_room"])
            row = cur.fetchone()
            if row:
                return str(row_to_dict(row)["room_id"])
            rid = _new_id("room")
            cur.execute(f"INSERT INTO team_rooms (room_id, report_id, name, room_type, created_at) VALUES ({p},{p},{p},{p},{p})", [rid, report_id, "War Room", "war_room", _now()])
            conn.commit()
            return rid
        finally:
            cur.close()

def insert_team_message(report_id, *, sender_id, receiver_id, room_id, mode, message):
    ensure_execution_schema()
    mid = _new_id("msg")
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO team_messages (message_id, report_id, sender_id, receiver_id, room_id, mode, message_text, created_at) VALUES ({p},{p},{p},{p},{p},{p},{p},{p})", [mid, report_id, sender_id, receiver_id, room_id, mode, message, _now()])
            conn.commit()
        finally:
            cur.close()
    return {"message_id": mid, "sender_id": sender_id, "receiver_id": receiver_id, "room_id": room_id, "mode": mode, "message": message}

def list_team_messages(report_id, *, since=None, limit=100):
    ensure_execution_schema()
    p = _ph()
    sql = f"SELECT * FROM team_messages WHERE report_id = {p}"
    params: list[Any] = [report_id]
    if since:
        sql += f" AND created_at >= {p}"
        params.append(since)
    sql += f" ORDER BY created_at ASC LIMIT {int(limit)}"
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
        finally:
            cur.close()
    out = []
    for row in rows:
        d = row_to_dict(row)
        out.append({
            "message_id": d.get("message_id"),
            "sender_id": d.get("sender_id"),
            "receiver_id": d.get("receiver_id"),
            "room_id": d.get("room_id"),
            "mode": d.get("mode"),
            "message": d.get("message_text"),
            "created_at": d.get("created_at"),
        })
    return out

def upsert_employee_memory(report_id, employee_id, scope, content):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT memory_id FROM employee_memory WHERE report_id = {p} AND employee_id = {p} AND scope = {p} LIMIT 1", [report_id, employee_id, scope])
            row = cur.fetchone()
            blob = _json_dumps(content)
            if row:
                d = row_to_dict(row)
                cur.execute(f"UPDATE employee_memory SET memory_json = {p}, updated_at = {p} WHERE memory_id = {p}", [blob, _now(), d["memory_id"]])
            else:
                cur.execute(f"INSERT INTO employee_memory (memory_id, report_id, employee_id, scope, memory_json, updated_at) VALUES ({p},{p},{p},{p},{p},{p})", [_new_id("mem"), report_id, employee_id, scope, blob, _now()])
            conn.commit()
        finally:
            cur.close()

def get_employee_memory(report_id, employee_id, scope):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT memory_json FROM employee_memory WHERE report_id = {p} AND employee_id = {p} AND scope = {p} LIMIT 1", [report_id, employee_id, scope])
            row = cur.fetchone()
        finally:
            cur.close()
    if not row:
        return {}
    return _json_loads(row_to_dict(row).get("memory_json"), {})

def insert_kpi_snapshot(report_id, kpi_name, kpi_value, notes=""):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"INSERT INTO kpi_history (kpi_id, report_id, kpi_name, kpi_value, notes, recorded_at) VALUES ({p},{p},{p},{p},{p},{p})", [_new_id("kpi"), report_id, kpi_name, float(kpi_value), notes, _now()])
            conn.commit()
        finally:
            cur.close()

def list_kpi_history(report_id, limit=50):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM kpi_history WHERE report_id = {p} ORDER BY recorded_at DESC LIMIT {int(limit)}", [report_id])
            rows = cur.fetchall()
        finally:
            cur.close()
    return [row_to_dict(r) for r in rows]


def get_employee_private_memory(report_id, employee_id):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT preferences_json, past_tasks_json, learned_insights_json, updated_at FROM employee_private_memory WHERE report_id = {p} AND employee_id = {p} LIMIT 1",
                [report_id, employee_id],
            )
            row = cur.fetchone()
        finally:
            cur.close()
    if not row:
        return {"preferences": {}, "past_tasks": [], "learned_insights": []}
    d = row_to_dict(row)
    return {
        "preferences": _json_loads(d.get("preferences_json"), {}),
        "past_tasks": _json_loads(d.get("past_tasks_json"), []),
        "learned_insights": _json_loads(d.get("learned_insights_json"), []),
        "updated_at": d.get("updated_at"),
    }


def upsert_employee_private_memory(report_id, employee_id, *, preferences=None, past_tasks=None, learned_insights=None):
    ensure_execution_schema()
    current = get_employee_private_memory(report_id, employee_id)
    if preferences is not None:
        current["preferences"] = {**_as_dict(current.get("preferences")), **_as_dict(preferences)}
    if past_tasks is not None:
        current["past_tasks"] = list(past_tasks)
    if learned_insights is not None:
        merged = list(current.get("learned_insights") or [])
        for item in learned_insights:
            if item not in merged:
                merged.append(item)
        current["learned_insights"] = merged[-100:]
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT memory_id FROM employee_private_memory WHERE report_id = {p} AND employee_id = {p} LIMIT 1",
                [report_id, employee_id],
            )
            row = cur.fetchone()
            prefs, tasks, insights = _json_dumps(current["preferences"]), _json_dumps(current["past_tasks"]), _json_dumps(current["learned_insights"])
            ts = _now()
            if row:
                mid = row_to_dict(row)["memory_id"]
                cur.execute(
                    f"UPDATE employee_private_memory SET preferences_json = {p}, past_tasks_json = {p}, learned_insights_json = {p}, updated_at = {p} WHERE memory_id = {p}",
                    [prefs, tasks, insights, ts, mid],
                )
            else:
                cur.execute(
                    f"INSERT INTO employee_private_memory (memory_id, report_id, employee_id, preferences_json, past_tasks_json, learned_insights_json, updated_at) VALUES ({p},{p},{p},{p},{p},{p},{p})",
                    [_new_id("epm"), report_id, employee_id, prefs, tasks, insights, ts],
                )
            conn.commit()
        finally:
            cur.close()
    return get_employee_private_memory(report_id, employee_id)


def _as_dict(v):
    return v if isinstance(v, dict) else {}


def get_team_shared_memory_row(report_id):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT goals_json, blockers_json, company_context_json, updated_at FROM team_shared_memory WHERE report_id = {p} LIMIT 1",
                [report_id],
            )
            row = cur.fetchone()
        finally:
            cur.close()
    if not row:
        return {"goals": [], "blockers": [], "company_context": {}}
    d = row_to_dict(row)
    return {
        "goals": _json_loads(d.get("goals_json"), []),
        "blockers": _json_loads(d.get("blockers_json"), []),
        "company_context": _json_loads(d.get("company_context_json"), {}),
        "updated_at": d.get("updated_at"),
    }


def upsert_team_shared_memory_row(report_id, *, goals=None, blockers=None, company_context=None):
    ensure_execution_schema()
    current = get_team_shared_memory_row(report_id)
    if goals is not None:
        current["goals"] = list(goals)
    if blockers is not None:
        current["blockers"] = list(blockers)
    if company_context is not None:
        current["company_context"] = {**_as_dict(current.get("company_context")), **_as_dict(company_context)}
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT memory_id FROM team_shared_memory WHERE report_id = {p} LIMIT 1", [report_id])
            row = cur.fetchone()
            g, b, c = _json_dumps(current["goals"]), _json_dumps(current["blockers"]), _json_dumps(current["company_context"])
            ts = _now()
            if row:
                mid = row_to_dict(row)["memory_id"]
                cur.execute(
                    f"UPDATE team_shared_memory SET goals_json = {p}, blockers_json = {p}, company_context_json = {p}, updated_at = {p} WHERE memory_id = {p}",
                    [g, b, c, ts, mid],
                )
            else:
                cur.execute(
                    f"INSERT INTO team_shared_memory (memory_id, report_id, goals_json, blockers_json, company_context_json, updated_at) VALUES ({p},{p},{p},{p},{p},{p})",
                    [_new_id("tsm"), report_id, g, b, c, ts],
                )
            conn.commit()
        finally:
            cur.close()
    return get_team_shared_memory_row(report_id)


def get_company_state_row(report_id):
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT revenue, burn, kpis_json, growth_metrics_json, active_campaigns_json, updated_at FROM company_state WHERE report_id = {p} LIMIT 1",
                [report_id],
            )
            row = cur.fetchone()
        finally:
            cur.close()
    if not row:
        return {
            "revenue": 0.0,
            "burn": 0.0,
            "kpis": {},
            "growth_metrics": {},
            "active_campaigns": [],
        }
    d = row_to_dict(row)
    return {
        "revenue": float(d.get("revenue") or 0),
        "burn": float(d.get("burn") or 0),
        "kpis": _json_loads(d.get("kpis_json"), {}),
        "growth_metrics": _json_loads(d.get("growth_metrics_json"), {}),
        "active_campaigns": _json_loads(d.get("active_campaigns_json"), []),
        "updated_at": d.get("updated_at"),
    }


def upsert_company_state_row(report_id, state: dict):
    ensure_execution_schema()
    current = get_company_state_row(report_id)
    merged = {**current, **(state if isinstance(state, dict) else {})}
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT state_id FROM company_state WHERE report_id = {p} LIMIT 1", [report_id])
            row = cur.fetchone()
            rev, burn = float(merged.get("revenue") or 0), float(merged.get("burn") or 0)
            kpis = _json_dumps(merged.get("kpis") or {})
            growth = _json_dumps(merged.get("growth_metrics") or {})
            campaigns = _json_dumps(merged.get("active_campaigns") or [])
            ts = _now()
            if row:
                sid = row_to_dict(row)["state_id"]
                cur.execute(
                    f"UPDATE company_state SET revenue = {p}, burn = {p}, kpis_json = {p}, growth_metrics_json = {p}, active_campaigns_json = {p}, updated_at = {p} WHERE state_id = {p}",
                    [rev, burn, kpis, growth, campaigns, ts, sid],
                )
            else:
                cur.execute(
                    f"INSERT INTO company_state (state_id, report_id, revenue, burn, kpis_json, growth_metrics_json, active_campaigns_json, updated_at) VALUES ({p},{p},{p},{p},{p},{p},{p},{p})",
                    [_new_id("cst"), report_id, rev, burn, kpis, growth, campaigns, ts],
                )
            conn.commit()
        finally:
            cur.close()
    return get_company_state_row(report_id)


# --- Long-term employee memory, relationships, founder preferences ---

MEMORY_TYPES = frozenset({
    "founder_preference",
    "task_outcome",
    "learned_pattern",
    "mistake",
    "customer_feedback",
    "team_conflict",
})


def insert_long_memory(
    report_id: str,
    employee_id: str,
    memory_type: str,
    memory_text: str,
    *,
    importance_score: float = 0.5,
) -> dict[str, Any]:
    ensure_execution_schema()
    text = str(memory_text or "").strip()
    if not text:
        return {}
    mid = _new_id("lmem")
    score = max(0.0, min(1.0, float(importance_score)))
    ts = _now()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"INSERT INTO employee_long_memory (memory_id, employee_id, report_id, memory_type, memory_text, importance_score, created_at, last_used_at) VALUES ({p},{p},{p},{p},{p},{p},{p},{p})",
                [mid, employee_id, report_id, memory_type, text[:2000], score, ts, ts],
            )
            conn.commit()
        finally:
            cur.close()
    return {
        "memory_id": mid,
        "employee_id": employee_id,
        "report_id": report_id,
        "memory_type": memory_type,
        "memory_text": text,
        "importance_score": score,
        "created_at": ts,
        "last_used_at": ts,
    }


def list_long_memory(
    report_id: str,
    employee_id: str | None = None,
    *,
    memory_type: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    ensure_execution_schema()
    p = _ph()
    sql = f"SELECT * FROM employee_long_memory WHERE report_id = {p}"
    params: list[Any] = [report_id]
    if employee_id:
        sql += f" AND employee_id = {p}"
        params.append(employee_id)
    if memory_type:
        sql += f" AND memory_type = {p}"
        params.append(memory_type)
    sql += f" ORDER BY importance_score DESC, last_used_at DESC LIMIT {int(limit)}"
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            rows = cur.fetchall()
        finally:
            cur.close()
    return [row_to_dict(r) for r in rows]


def touch_long_memory(memory_ids: list[str]) -> None:
    if not memory_ids:
        return
    ensure_execution_schema()
    p = _ph()
    ts = _now()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            for mid in memory_ids:
                cur.execute(f"UPDATE employee_long_memory SET last_used_at = {p} WHERE memory_id = {p}", [ts, mid])
            conn.commit()
        finally:
            cur.close()


def upsert_relationship(
    report_id: str,
    employee_a: str,
    employee_b: str,
    *,
    trust_delta: float = 0.0,
    conflict_delta: float = 0.0,
    collaboration_delta: float = 0.0,
) -> dict[str, Any]:
    ensure_execution_schema()
    a, b = sorted([str(employee_a), str(employee_b)])
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT relationship_id, trust_score, conflict_score, collaboration_score FROM employee_relationships WHERE report_id = {p} AND employee_a = {p} AND employee_b = {p} LIMIT 1",
                [report_id, a, b],
            )
            row = cur.fetchone()
            ts = _now()
            if row:
                d = row_to_dict(row)
                trust = max(0.0, min(1.0, float(d.get("trust_score") or 0.5) + trust_delta))
                conflict = max(0.0, min(1.0, float(d.get("conflict_score") or 0) + conflict_delta))
                collab = max(0.0, min(1.0, float(d.get("collaboration_score") or 0.5) + collaboration_delta))
                cur.execute(
                    f"UPDATE employee_relationships SET trust_score = {p}, conflict_score = {p}, collaboration_score = {p}, updated_at = {p} WHERE relationship_id = {p}",
                    [trust, conflict, collab, ts, d["relationship_id"]],
                )
                rid = d["relationship_id"]
            else:
                rid = _new_id("rel")
                trust = max(0.0, min(1.0, 0.5 + trust_delta))
                conflict = max(0.0, min(1.0, conflict_delta))
                collab = max(0.0, min(1.0, 0.5 + collaboration_delta))
                cur.execute(
                    f"INSERT INTO employee_relationships (relationship_id, report_id, employee_a, employee_b, trust_score, conflict_score, collaboration_score, updated_at) VALUES ({p},{p},{p},{p},{p},{p},{p},{p})",
                    [rid, report_id, a, b, trust, conflict, collab, ts],
                )
            conn.commit()
        finally:
            cur.close()
    return get_relationship(report_id, employee_a, employee_b) or {}


def get_relationship(report_id: str, employee_a: str, employee_b: str) -> dict[str, Any] | None:
    ensure_execution_schema()
    a, b = sorted([str(employee_a), str(employee_b)])
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT * FROM employee_relationships WHERE report_id = {p} AND employee_a = {p} AND employee_b = {p} LIMIT 1",
                [report_id, a, b],
            )
            row = cur.fetchone()
        finally:
            cur.close()
    return row_to_dict(row) if row else None


def list_relationships_for_employee(report_id: str, employee_id: str) -> list[dict[str, Any]]:
    ensure_execution_schema()
    p = _ph()
    eid = str(employee_id)
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT * FROM employee_relationships WHERE report_id = {p} AND (employee_a = {p} OR employee_b = {p})",
                [report_id, eid, eid],
            )
            rows = cur.fetchall()
        finally:
            cur.close()
    out = []
    for row in rows:
        d = row_to_dict(row)
        other = d["employee_b"] if d["employee_a"] == eid else d["employee_a"]
        d["other_employee_id"] = other
        out.append(d)
    return out


def upsert_founder_preference(report_id: str, preference_key: str, preference_value: str, *, confidence: float = 0.5) -> dict[str, Any]:
    ensure_execution_schema()
    key = str(preference_key or "").strip()[:120]
    val = str(preference_value or "").strip()[:2000]
    if not key or not val:
        return {}
    conf = max(0.0, min(1.0, float(confidence)))
    p = _ph()
    ts = _now()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT preference_id, confidence FROM founder_preferences WHERE report_id = {p} AND preference_key = {p} LIMIT 1", [report_id, key])
            row = cur.fetchone()
            if row:
                d = row_to_dict(row)
                merged_conf = max(conf, float(d.get("confidence") or 0))
                cur.execute(
                    f"UPDATE founder_preferences SET preference_value = {p}, confidence = {p}, updated_at = {p} WHERE preference_id = {p}",
                    [val, merged_conf, ts, d["preference_id"]],
                )
                pid = d["preference_id"]
            else:
                pid = _new_id("fpref")
                cur.execute(
                    f"INSERT INTO founder_preferences (preference_id, report_id, preference_key, preference_value, confidence, updated_at) VALUES ({p},{p},{p},{p},{p},{p})",
                    [pid, report_id, key, val, conf, ts],
                )
            conn.commit()
        finally:
            cur.close()
    return get_founder_preference(report_id, key) or {"preference_key": key, "preference_value": val, "confidence": conf}


def get_founder_preference(report_id: str, preference_key: str) -> dict[str, Any] | None:
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f"SELECT * FROM founder_preferences WHERE report_id = {p} AND preference_key = {p} LIMIT 1", [report_id, preference_key])
            row = cur.fetchone()
        finally:
            cur.close()
    return row_to_dict(row) if row else None


def list_founder_preferences(report_id: str, *, limit: int = 30) -> list[dict[str, Any]]:
    ensure_execution_schema()
    p = _ph()
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                f"SELECT * FROM founder_preferences WHERE report_id = {p} ORDER BY confidence DESC, updated_at DESC LIMIT {int(limit)}",
                [report_id],
            )
            rows = cur.fetchall()
        finally:
            cur.close()
    return [row_to_dict(r) for r in rows]
