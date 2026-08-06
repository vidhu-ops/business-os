"""Executable lead -> personalize -> queue-send pipeline for Employee OS / Automation."""
from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from iidatech.execution.team_memory import get_shared_team_memory, update_shared_team_memory

_ARTIFACT_ROOT = Path(__file__).resolve().parents[2] / "business_build_outputs" / "employee_os2"


def _queue_path(report_id: str) -> Path:
    p = _ARTIFACT_ROOT / str(report_id) / "outreach_send_queue.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_send_queue(report_id: str) -> list[dict[str, Any]]:
    path = _queue_path(report_id)
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return list(data.get("items") or []) if isinstance(data, dict) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_send_queue(report_id: str, items: list[dict[str, Any]]) -> Path:
    path = _queue_path(report_id)
    path.write_text(
        json.dumps(
            {"report_id": report_id, "updated_at": datetime.now(timezone.utc).isoformat(), "items": items},
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    update_shared_team_memory(report_id, {"outreach_send_queue": str(path), "outreach_queued": len(items)})
    return path


def _find_leads_csv(report_id: str) -> str:
    mem = get_shared_team_memory(report_id)
    csv_path = str(mem.get("last_leads_csv") or "").strip()
    if csv_path and Path(csv_path).is_file():
        return csv_path
    root = _ARTIFACT_ROOT / str(report_id)
    if root.is_dir():
        candidates = sorted(root.rglob("leads_*.csv"), key=lambda p: p.stat().st_mtime, reverse=True)
        if candidates:
            return str(candidates[0])
    return ""


def load_leads(report_id: str) -> list[dict[str, Any]]:
    csv_path = _find_leads_csv(report_id)
    if not csv_path:
        return []
    rows: list[dict[str, Any]] = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if not isinstance(row, dict):
                continue
            email = str(row.get("email") or "").strip()
            rows.append({**row, "email": email})
    return rows


def _first_name(lead: dict[str, Any]) -> str:
    name = str(lead.get("contact_name") or lead.get("name") or lead.get("first_name") or "").strip()
    if name:
        return name.split()[0]
    email = str(lead.get("email") or "")
    token = email.split("@")[0].split(".")[0] if email else "there"
    return token[:1].upper() + token[1:24]


def _template_email(lead: dict[str, Any], *, idea: str, geography: str) -> tuple[str, str]:
    first = _first_name(lead)
    company = str(lead.get("company") or lead.get("company_name") or "your team").strip()
    subject = f"Quick idea for {company}"
    body = (
        f"Hi {first},\n\n"
        f"I help teams like {company} turn research into executed outreach for {idea or 'growth'} in {geography or 'your market'}.\n\n"
        "Happy to share a short teardown of how similar companies are winning pipeline this quarter — "
        "worth a 15-minute chat?\n\n"
        "Best,\nIIDATECH\n\n"
        "If this is not relevant, reply stop and I will not follow up."
    )
    return subject, body


def personalize_leads(
    report_id: str,
    *,
    idea: str = "",
    industry: str = "",
    geography: str = "",
    max_leads: int = 90,
    use_llm: bool = True,
) -> dict[str, Any]:
    leads = [l for l in load_leads(report_id) if l.get("email")][: max(1, min(90, max_leads))]
    if not leads:
        return {
            "ok": False,
            "drafted": 0,
            "skipped_no_email": len(load_leads(report_id)),
            "message": "No leads with email found. Run Find leads first.",
            "items": [],
        }

    items: list[dict[str, Any]] = []
    provider = ""
    if use_llm:
        try:
            from iidatech.execution.os2_llm import generate_with_session_keys
        except Exception:
            generate_with_session_keys = None  # type: ignore
    else:
        generate_with_session_keys = None  # type: ignore

    for lead in leads:
        first = _first_name(lead)
        company = str(lead.get("company") or lead.get("company_name") or "your team")
        subject, body = _template_email(lead, idea=idea, geography=geography)
        if generate_with_session_keys:
            prompt = (
                f"Write one short personalized cold email.\n"
                f"ICP/business: {idea} | {industry} | {geography}\n"
                f"Lead: {first} at {company}, email {lead.get('email')}\n"
                f"Notes: {str(lead.get('notes') or lead.get('reason') or '')[:240]}\n\n"
                "Return ONLY:\nSUBJECT: ...\nBODY:\n...\n"
                "Max 140 words. Include a soft CTA and opt-out line. No markdown."
            )
            text, provider = generate_with_session_keys(
                prompt,
                system="You write concise personalized B2B cold emails. Never invent fake facts about the lead.",
            )
            if text:
                subj_m = re.search(r"SUBJECT:\s*(.+)", text, re.I)
                body_m = re.search(r"BODY:\s*([\s\S]+)", text, re.I)
                if subj_m:
                    subject = subj_m.group(1).strip()[:180]
                if body_m:
                    body = body_m.group(1).strip()
        items.append(
            {
                "id": f"send_{len(items)+1}_{str(lead.get('email')).lower()}",
                "to_email": lead.get("email"),
                "company": company,
                "contact_name": first,
                "subject": subject,
                "body": body,
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    path = save_send_queue(report_id, items)
    return {
        "ok": True,
        "drafted": len(items),
        "skipped_no_email": max(0, len(load_leads(report_id)) - len(items)),
        "queue_path": str(path),
        "provider": provider or "template",
        "message": f"Personalized {len(items)} emails. Ready to send after approval.",
        "items": items[:5],
    }


def send_pending(
    report_id: str,
    *,
    limit: int = 10,
) -> dict[str, Any]:
    from iidatech.integrations.oauth_posting import send_gmail_message

    items = load_send_queue(report_id)
    pending = [it for it in items if str(it.get("status")) == "pending"]
    if not pending:
        return {"ok": False, "sent": 0, "failed": 0, "message": "No pending personalized emails in the queue."}

    sent = 0
    failed = 0
    logs: list[str] = []
    batch = pending[: max(1, min(25, limit))]
    for it in batch:
        ok, msg = send_gmail_message(
            report_id,
            str(it.get("to_email") or ""),
            str(it.get("subject") or "Hello"),
            str(it.get("body") or ""),
        )
        it["status"] = "sent" if ok else "failed"
        it["result"] = msg
        it["sent_at"] = datetime.now(timezone.utc).isoformat()
        if ok:
            sent += 1
        else:
            failed += 1
        logs.append(f"{it.get('to_email')}: {'ok' if ok else msg}")

    save_send_queue(report_id, items)
    remaining = sum(1 for it in items if str(it.get("status")) == "pending")
    return {
        "ok": sent > 0,
        "sent": sent,
        "failed": failed,
        "remaining": remaining,
        "message": f"Sent {sent}, failed {failed}, {remaining} still pending.",
        "logs": logs[:12],
    }


def parse_lead_target(message: str, default: int = 30) -> int:
    msg = str(message or "").lower()
    m = re.search(r"(\d+)\s*(?:qualified\s+)?leads?", msg)
    n = int(m.group(1)) if m else default
    return max(5, min(90, n))


def is_outreach_pipeline_intent(message: str) -> bool:
    msg = str(message or "").lower()
    wants_leads = "lead" in msg and any(k in msg for k in ("find", "get", "generate", "scrape", "list", "search"))
    wants_email = any(k in msg for k in ("email", "outreach", "cold email", "send", "mail them", "email them"))
    return wants_leads and wants_email