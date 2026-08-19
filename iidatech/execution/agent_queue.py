"""Sequential agent queue."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from iidatech.execution.chat_engine import send_agent_message
from iidatech.execution.employees import hire_default_team, infer_business_type
from iidatech.execution.output_paths import automation_queues_root
from iidatech.execution.task_engine import founder_employee_id
from iidatech.storage.execution_repository import list_employees


def _queue_path(report_id: str) -> Path:
    p = automation_queues_root() / f"{str(report_id).strip()}.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_queue(report_id: str) -> dict[str, Any]:
    path = _queue_path(report_id)
    if not path.is_file():
        return {"report_id": report_id, "items": [], "status": "idle"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"report_id": report_id, "items": [], "status": "idle"}
    except (json.JSONDecodeError, OSError):
        return {"report_id": report_id, "items": [], "status": "idle"}


def save_queue(report_id: str, queue: dict[str, Any]) -> None:
    _queue_path(report_id).write_text(json.dumps(queue, indent=2, ensure_ascii=False), encoding="utf-8")


def ensure_automation_team(report_id: str, *, topic: str, industry: str, geography: str) -> list[dict[str, Any]]:
    from iidatech.integrations.oauth_store import seed_workspace_from_env

    seed_workspace_from_env(report_id)
    roster = list_employees(report_id, active_only=False)
    if roster:
        return roster
    bt = infer_business_type(industry=industry, topic=topic)
    return hire_default_team(report_id, business_type=bt)


def init_queue_from_spec(report_id: str, spec: dict[str, Any]) -> dict[str, Any]:
    from iidatech.execution.automation_steps import STEP_BY_ID

    items: list[dict[str, Any]] = []
    for row in spec.get("picked_steps") or []:
        if not isinstance(row, dict):
            continue
        # Backfill execution fields from the catalog so headless runs never see
        # "Unknown step"; only include keys that have real values (None values
        # would shadow catalog defaults during the merge in process_next_queue_item).
        catalog = STEP_BY_ID.get(str(row.get("id") or "")) or {}
        item: dict[str, Any] = {
            "id": row.get("id"),
            "label": row.get("label") or catalog.get("label"),
            "role": row.get("role") or catalog.get("role"),
            "status": "queued",
            "needs_approval": bool(row.get("needs_approval", catalog.get("needs_approval"))),
            "result": "",
            "artifacts": [],
        }
        for key in ("harness_id", "prompt", "action"):
            val = row.get(key) or catalog.get(key)
            if val:
                item[key] = val
        items.append(item)
    queue = {"report_id": report_id, "items": items, "status": "ready" if items else "idle"}
    save_queue(report_id, queue)
    return queue


def _employee_for_role(report_id: str, role: str) -> str | None:
    for emp in list_employees(report_id):
        if str(emp.get("role") or "") == str(role or ""):
            return str(emp.get("employee_id") or "") or None
    return None


def _coo_id(report_id: str) -> str | None:
    return _employee_for_role(report_id, "COO")


def _announce(report_id: str, sender_id: str, text: str, *, report_context: dict[str, Any] | None = None) -> None:
    send_agent_message(report_id, sender_id, "war_room", text[:500], report_context=report_context)
    fid = founder_employee_id(report_id)
    if fid and fid != sender_id:
        send_agent_message(report_id, sender_id, fid, text[:500], report_context=report_context)


def _completed_artifacts(report_id: str) -> list[str]:
    """Artifact paths from all completed items in this queue."""
    queue = load_queue(report_id)
    out: list[str] = []
    for item in queue.get("items") or []:
        if str(item.get("status")) == "completed":
            out.extend(str(a) for a in (item.get("artifacts") or []) if a)
    return out


def _execute_step(report_id: str, step: dict[str, Any], *, idea: str, industry: str, geography: str, api_keys: dict[str, str] | None, report_context: dict[str, Any] | None) -> dict[str, Any]:
    from iidatech.execution.employee_os2_harness import execute_harness_job
    from iidatech.integrations.oauth_posting import fetch_gmail_inbox_summary, list_hubspot_contacts, publish_linkedin_post

    action = str(step.get("action") or "")
    harness_id = step.get("harness_id")
    ctx = dict(report_context or {})
    ctx.update({"topic": idea, "industry": industry, "geography": geography, "report_id": report_id})

    if harness_id:
        result = execute_harness_job(str(harness_id), str(step.get("prompt") or step.get("label") or ""), report_id=report_id, api_keys=api_keys or {}, report_context=ctx)
        return {"success": bool(result.get("success")), "reply": str(result.get("reply") or ""), "artifacts": list(result.get("artifacts") or [])}

    if action == "gmail_read":
        ok, summary, rows = fetch_gmail_inbox_summary(report_id, limit=8)
        return {"success": ok, "reply": summary, "artifacts": [], "inbox_rows": rows}

    if action == "hubspot_read":
        ok, summary, rows = list_hubspot_contacts(report_id, limit=10)
        return {"success": ok, "reply": summary, "artifacts": [], "crm_rows": rows}

    if action == "linkedin_post":
        from iidatech.integrations.oauth_store import is_connected
        if not is_connected(report_id, "linkedin"):
            return {"success": False, "reply": "LinkedIn not connected — complete OAuth in Employee OS Integrations (client id/secret already in .env)."}
        from iidatech.execution.os2_workflow import _find_text_artifact
        post_text = str(step.get("post_text") or "").strip()
        if not post_text:
            post_text = _find_text_artifact(_completed_artifacts(report_id), ("campaign", "linkedin", "ad_copy"))
        if not post_text:
            post_text = f"Update on {idea}."
        ok, msg = publish_linkedin_post(report_id, post_text[:2900])
        return {"success": ok, "reply": msg, "artifacts": []}

    if action == "outreach_personalize":
        from iidatech.execution.outreach_pipeline import personalize_leads
        out = personalize_leads(
            report_id,
            idea=idea,
            industry=industry,
            geography=geography,
            max_leads=90,
            use_llm=True,
        )
        return {
            "success": bool(out.get("ok")),
            "reply": str(out.get("message") or ""),
            "artifacts": [str(out.get("queue_path") or "")] if out.get("queue_path") else [],
            "drafted": out.get("drafted", 0),
        }

    if action == "gmail_send":
        from iidatech.execution.os2_workflow import _find_text_artifact, _first_lead_email
        from iidatech.integrations.oauth_posting import send_gmail_message
        to_email, subject = _first_lead_email(report_id)
        if not to_email:
            return {"success": False, "reply": "No lead email found — run the 'Find qualified leads' step first."}
        body = _find_text_artifact(_completed_artifacts(report_id), ("outreach", "email", "sequence"))
        if not body:
            return {"success": False, "reply": "No outreach draft found — run the 'Draft outreach sequence' step first."}
        ok, msg = send_gmail_message(report_id, to_email, subject, body)
        return {"success": ok, "reply": msg, "artifacts": []}

    if action == "gmail_send_queue":
        from iidatech.execution.outreach_pipeline import send_pending
        # After founder approval, drain the personalized queue (cap 90 / run).
        limit = int(step.get("batch_size") or 90)
        out = send_pending(report_id, limit=max(1, min(90, limit)))
        return {
            "success": bool(out.get("ok")) or int(out.get("sent") or 0) > 0,
            "reply": str(out.get("message") or ""),
            "artifacts": [],
            "sent": out.get("sent", 0),
            "remaining": out.get("remaining", 0),
        }

    if action == "hubspot_sync":
        from iidatech.execution.os2_workflow import _find_leads_csv
        from iidatech.integrations.oauth_posting import sync_hubspot_contacts
        csv_path = _find_leads_csv(_completed_artifacts(report_id), report_id)
        if not csv_path:
            return {"success": False, "reply": "No leads CSV found — run the 'Find qualified leads' step first."}
        ok, msg = sync_hubspot_contacts(report_id, csv_path)
        return {"success": ok, "reply": msg, "artifacts": []}

    if action == "founder_brief":
        from iidatech.execution.agent_runtime import run_agent_company_cycle
        cycle = run_agent_company_cycle(report_id, report_v3=report_context if isinstance(report_context, dict) else None)
        recs = (cycle.get("founder_brief") or {}).get("recommendations") or []
        return {"success": True, "reply": recs[0] if recs else "Team cycle complete.", "artifacts": []}

    return {"success": False, "reply": f"Unknown step: {action or harness_id}"}


def process_next_queue_item(report_id: str, *, idea: str, industry: str, geography: str, api_keys: dict[str, str] | None = None, report_context: dict[str, Any] | None = None, auto_approve_external: bool = False) -> dict[str, Any]:
    queue = load_queue(report_id)
    items = queue.get("items") or []
    # Recover items stranded in "running" by a previous crash so they retry
    # instead of silently blocking the queue forever.
    for it in items:
        if str(it.get("status")) == "running":
            it["status"] = "queued"
            it["result"] = "Recovered after interrupted run — retrying."
    next_item = next((it for it in items if str(it.get("status")) == "queued"), None)
    if not next_item:
        pending_approval = [it for it in items if str(it.get("status")) == "needs_founder"]
        queue["status"] = "waiting_founder" if pending_approval else "completed"
        save_queue(report_id, queue)
        if pending_approval:
            return {"done": False, "needs_approval": True, "message": f"{len(pending_approval)} step(s) waiting for founder approval.", "item": pending_approval[0]}
        return {"done": True, "message": "Queue empty."}

    role = str(next_item.get("role") or "Team")
    eid = _employee_for_role(report_id, role) or _coo_id(report_id) or founder_employee_id(report_id)
    if not eid:
        return {"done": True, "message": "No employees on roster."}

    waiting = [it for it in items if str(it.get("status")) == "queued" and it is not next_item]
    msg = f"**{role}** is up: {next_item.get('label')}."
    if waiting:
        msg += f" ({len(waiting)} waiting in line.)"
    _announce(report_id, eid, msg, report_context=report_context)

    step_def = next((s for s in (report_context or {}).get("_step_defs") or [] if s.get("id") == next_item.get("id")), {})
    # None/empty values in the queue item must not shadow catalog step fields.
    merged_step = {**step_def, **{k: v for k, v in next_item.items() if v not in (None, "")}}
    next_item["status"] = "running"
    save_queue(report_id, queue)

    if merged_step.get("needs_approval") and not auto_approve_external:
        next_item["status"] = "needs_founder"
        next_item["result"] = "Waiting for founder approval."
        action_desc = {
            "linkedin_post": "This will publish a real post to your LinkedIn profile.",
            "gmail_send": "This will send a real email to the first qualified lead.",
            "gmail_send_queue": "This will send personalized emails from the queued lead list.",
            "hubspot_sync": "This will create real contacts in your HubSpot CRM.",
        }.get(str(merged_step.get("action") or ""), "This step performs an external action.")
        fid = founder_employee_id(report_id)
        if fid:
            send_agent_message(
                report_id, eid, fid,
                f"Approve: **{next_item.get('label')}** — {action_desc}",
                report_context=report_context,
            )
        queue["status"] = "waiting_founder"
        save_queue(report_id, queue)
        return {"done": False, "needs_approval": True, "item": next_item}

    try:
        result = _execute_step(report_id, merged_step, idea=idea, industry=industry, geography=geography, api_keys=api_keys, report_context=report_context)
    except Exception as exc:
        result = {"success": False, "reply": f"Step crashed: {str(exc)[:300]}", "artifacts": []}
    next_item["status"] = "completed" if result.get("success") else "failed"
    next_item["result"] = str(result.get("reply") or "")
    next_item["artifacts"] = list(result.get("artifacts") or [])
    queue["status"] = "running"
    save_queue(report_id, queue)

    coo = _coo_id(report_id) or eid
    _announce(report_id, coo, f"**{role}** finished {next_item.get('label')}: {str(result.get('reply') or '')[:180]}", report_context=report_context)
    return {"done": False, "item": next_item, "result": result}


def approve_pending_queue_items(report_id: str) -> int:
    """Re-queue items waiting on founder approval. Returns count approved."""
    queue = load_queue(report_id)
    count = 0
    for item in queue.get("items") or []:
        if str(item.get("status")) == "needs_founder":
            item["status"] = "queued"
            count += 1
    if count:
        queue["status"] = "running"
        save_queue(report_id, queue)
    return count


def run_full_queue(report_id: str, *, idea: str, industry: str, geography: str, api_keys: dict[str, str] | None = None, report_context: dict[str, Any] | None = None, max_steps: int = 15) -> list[dict[str, Any]]:
    logs: list[dict[str, Any]] = []
    for _ in range(max_steps):
        step = process_next_queue_item(report_id, idea=idea, industry=industry, geography=geography, api_keys=api_keys, report_context=report_context)
        logs.append(step)
        if step.get("done") or step.get("needs_approval"):
            break
        if step.get("item") and str(step["item"].get("status")) == "failed":
            break
    return logs