"""Agent chat: founder, peer, and war room modes."""
from __future__ import annotations
from iidatech.execution.team_memory import build_agent_context
from iidatech.storage.execution_repository import ensure_war_room, get_employee, insert_team_message, upsert_employee_memory

def _resolve_mode(sender, receiver):
    r = (receiver or "").lower()
    if r in {"war_room", "warroom", "team"}:
        return "war_room"
    s = get_employee(sender)
    r_emp = get_employee(receiver) if receiver else None
    if s and str(s.get("role", "")).lower() == "founder":
        return "founder_employee"
    if r_emp and str(r_emp.get("role", "")).lower() == "founder":
        return "founder_employee"
    return "employee_peer"

def send_agent_message(report_id, sender, receiver, message, *, report_context=None):
    mode = _resolve_mode(sender, receiver)
    room_id = None
    receiver_id = receiver
    if mode == "war_room":
        room_id = ensure_war_room(report_id)
        receiver_id = None
    text = str(message or "").strip()
    if text:
        from iidatech.storage.execution_repository import list_team_messages

        for recent in reversed(list_team_messages(report_id, limit=5)):
            if str(recent.get("message") or "").strip() != text:
                continue
            if str(recent.get("sender_id") or "") != str(sender):
                continue
            if mode == "war_room" and recent.get("room_id"):
                return recent
            if str(recent.get("receiver_id") or "") == str(receiver_id or ""):
                return recent
    ctx = build_agent_context(report_id, sender, report_context=report_context)
    record = insert_team_message(report_id, sender_id=sender, receiver_id=receiver_id, room_id=room_id, mode=mode, message=message)
    mem = {"last_message": message, "mode": mode, "context_keys": list((report_context or {}).keys())[:12], "open_tasks": len(ctx.get("assigned_tasks") or [])}
    upsert_employee_memory(report_id, sender, "private", mem)
    if receiver_id:
        upsert_employee_memory(report_id, receiver_id, "inbox", {"last_from": sender, "preview": message[:240]})
    record["agent_context"] = ctx
    return record
