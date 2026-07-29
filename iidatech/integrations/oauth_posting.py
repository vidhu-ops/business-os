"""OAuth-backed posting: LinkedIn, Gmail, HubSpot (uses workspace token store)."""
from __future__ import annotations

import base64
import csv
import os
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import requests

from iidatech.integrations.oauth_store import get_connection, get_valid_access_token


def _linkedin_version() -> str:
    return (os.getenv("LINKEDIN_VERSION") or "202605").strip()


def publish_linkedin_post(report_id: str, text: str) -> tuple[bool, str]:
    conn = get_connection(report_id, "linkedin")
    token = get_valid_access_token(report_id, "linkedin") or str(conn.get("access_token") or os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
    author = str(conn.get("author_urn") or os.getenv("LINKEDIN_AUTHOR_URN") or "").strip()
    text = str(text or "").strip()[:3000]
    if not token:
        return False, "LinkedIn not connected — add access token in Integrations."
    if not author:
        return False, "LinkedIn author URN required (urn:li:person:* or urn:li:organization:*)."
    if not text:
        return False, "Post text is empty."
    payload = {
        "author": author,
        "commentary": text,
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Linkedin-Version": _linkedin_version(),
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json",
    }
    try:
        resp = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=payload, timeout=60)
        if 200 <= resp.status_code < 300:
            post_id = resp.headers.get("x-restli-id") or resp.headers.get("X-RestLi-Id") or "accepted"
            return True, f"LinkedIn post published: {post_id}"
        return False, f"LinkedIn HTTP {resp.status_code}: {resp.text[:300]}"
    except Exception as exc:
        return False, str(exc)[:240]


def send_gmail_message(report_id: str, to_email: str, subject: str, body: str) -> tuple[bool, str]:
    conn = get_connection(report_id, "gmail")
    to_email = str(to_email or "").strip()
    subject = str(subject or "").strip()
    body = str(body or "").strip()
    if not to_email or not body:
        return False, "Recipient email and body are required."

    smtp_user = str(conn.get("smtp_user") or os.getenv("GMAIL_SMTP_USER") or os.getenv("GMAIL_USER") or "").strip()
    smtp_pass = str(conn.get("smtp_password") or os.getenv("GMAIL_SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or "").strip()
    if smtp_user and smtp_pass:
        try:
            import smtplib

            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject or "(no subject)"
            msg["From"] = smtp_user
            msg["To"] = to_email
            host = str(conn.get("smtp_host") or os.getenv("GMAIL_SMTP_HOST") or "smtp.gmail.com")
            port = int(conn.get("smtp_port") or os.getenv("GMAIL_SMTP_PORT") or "587")
            with smtplib.SMTP(host, port, timeout=30) as smtp:
                smtp.starttls()
                smtp.login(smtp_user, smtp_pass)
                smtp.sendmail(smtp_user, [to_email], msg.as_string())
            return True, f"Email sent via Gmail SMTP to {to_email}"
        except Exception as exc:
            return False, f"SMTP error: {exc}"[:240]

    token = get_valid_access_token(report_id, "gmail") or str(conn.get("access_token") or "").strip()
    if not token:
        return False, "Gmail not connected — OAuth token or SMTP app password required."
    raw = f"To: {to_email}\r\nSubject: {subject}\r\n\r\n{body}"
    encoded = base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
    try:
        resp = requests.post(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"raw": encoded},
            timeout=45,
        )
        if 200 <= resp.status_code < 300:
            data = resp.json() if resp.content else {}
            return True, f"Email sent via Gmail API: {data.get('id', to_email)}"
        return False, f"Gmail API HTTP {resp.status_code}: {resp.text[:240]}"
    except Exception as exc:
        return False, str(exc)[:240]


def sync_hubspot_contacts(report_id: str, leads_csv_path: str, *, limit: int = 10) -> tuple[bool, str]:
    conn = get_connection(report_id, "hubspot")
    token = get_valid_access_token(report_id, "hubspot") or str(conn.get("access_token") or conn.get("token") or os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or os.getenv("HUBSPOT_ACCESS_TOKEN") or "").strip()
    if not token:
        return False, "HubSpot not connected — add private app token or OAuth access token."
    path = Path(str(leads_csv_path or ""))
    if not path.is_file():
        return False, f"Lead CSV not found: {path}"
    created = 0
    errors: list[str] = []
    try:
        with path.open(encoding="utf-8", errors="ignore", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                if created >= limit:
                    break
                if not isinstance(row, dict):
                    continue
                ok, msg = _hubspot_create_contact(token, row)
                if ok:
                    created += 1
                else:
                    errors.append(msg)
    except OSError as exc:
        return False, str(exc)[:240]
    if created:
        tail = f" ({len(errors)} skipped)" if errors else ""
        return True, f"HubSpot: created {created} contact(s){tail}"
    return False, errors[0] if errors else "No contacts created from CSV"


def fetch_gmail_inbox_summary(report_id: str, *, limit: int = 8) -> tuple[bool, str, list[dict[str, Any]]]:
    """Read recent inbox subjects/snippets (requires gmail.readonly scope)."""
    token = get_valid_access_token(report_id, "gmail")
    if not token:
        conn = get_connection(report_id, "gmail")
        token = str(conn.get("access_token") or "").strip()
    if not token:
        return False, "Gmail not connected — authorize in Employee OS Integrations (read + send).", []
    limit = max(1, min(int(limit or 8), 20))
    headers = {"Authorization": f"Bearer {token}"}
    try:
        list_resp = requests.get(
            "https://gmail.googleapis.com/gmail/v1/users/me/messages",
            headers=headers,
            params={"maxResults": limit, "labelIds": "INBOX"},
            timeout=45,
        )
        if list_resp.status_code != 200:
            return False, f"Gmail list HTTP {list_resp.status_code}: {list_resp.text[:200]}", []
        msg_ids = [m.get("id") for m in (list_resp.json() or {}).get("messages") or [] if m.get("id")]
        rows: list[dict[str, Any]] = []
        for mid in msg_ids[:limit]:
            detail = requests.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{mid}",
                headers=headers,
                params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]},
                timeout=30,
            )
            if detail.status_code != 200:
                continue
            payload = detail.json() or {}
            hdrs = {h.get("name"): h.get("value") for h in payload.get("payload", {}).get("headers") or []}
            rows.append({
                "id": mid,
                "from": str(hdrs.get("From") or ""),
                "subject": str(hdrs.get("Subject") or "(no subject)"),
                "date": str(hdrs.get("Date") or ""),
                "snippet": str(payload.get("snippet") or "")[:200],
            })
        if not rows:
            return True, "Gmail inbox is empty or unreadable with current scopes.", []
        lines = [f"- {r['from'][:40]} | {r['subject'][:60]}" for r in rows[:5]]
        return True, f"Loaded {len(rows)} recent inbox message(s).\n" + "\n".join(lines), rows
    except Exception as exc:
        return False, str(exc)[:240], []


def list_hubspot_contacts(report_id: str, *, limit: int = 10) -> tuple[bool, str, list[dict[str, Any]]]:
    """List CRM contacts from HubSpot (private app token or OAuth)."""
    conn = get_connection(report_id, "hubspot")
    token = get_valid_access_token(report_id, "hubspot") or str(
        conn.get("access_token") or conn.get("token") or os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or os.getenv("HUBSPOT_ACCESS_TOKEN") or ""
    ).strip()
    if not token:
        return False, "HubSpot not connected — add private app token or OAuth in Integrations.", []
    limit = max(1, min(int(limit or 10), 50))
    try:
        resp = requests.get(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {token}"},
            params={
                "limit": limit,
                "properties": "email,firstname,lastname,company,jobtitle,lifecyclestage",
            },
            timeout=45,
        )
        if resp.status_code != 200:
            return False, f"HubSpot HTTP {resp.status_code}: {resp.text[:200]}", []
        results = (resp.json() or {}).get("results") or []
        rows: list[dict[str, Any]] = []
        for item in results:
            props = item.get("properties") or {}
            name = " ".join(p for p in [props.get("firstname"), props.get("lastname")] if p).strip()
            rows.append({
                "id": item.get("id"),
                "name": name,
                "email": props.get("email") or "",
                "company": props.get("company") or "",
                "title": props.get("jobtitle") or "",
                "stage": props.get("lifecyclestage") or "",
            })
        if not rows:
            return True, "HubSpot connected but no contacts returned.", []
        lines = [f"- {r.get('name') or r.get('email') or 'contact'} @ {r.get('company', '')}" for r in rows[:5]]
        return True, f"Loaded {len(rows)} HubSpot contact(s).\n" + "\n".join(lines), rows
    except Exception as exc:
        return False, str(exc)[:240], []


def _hubspot_create_contact(token: str, lead: dict[str, Any]) -> tuple[bool, str]:
    email = str(lead.get("email") or "").strip()
    company = str(lead.get("company") or lead.get("company_name") or "").strip()
    name = str(lead.get("contact_name") or lead.get("name") or "").strip()
    parts = name.split(None, 1) if name else ["", ""]
    first = parts[0] if parts else ""
    last = parts[1] if len(parts) > 1 else ""
    if not any([email, company, name]):
        return False, "Row missing email/company/name"
    properties = {
        "email": email,
        "firstname": first,
        "lastname": last,
        "company": company,
        "jobtitle": str(lead.get("title") or lead.get("job_title") or "").strip(),
        "website": str(lead.get("website") or "").strip(),
        "lifecyclestage": "lead",
    }
    properties = {k: v for k, v in properties.items() if v}
    try:
        resp = requests.post(
            "https://api.hubapi.com/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={"properties": properties},
            timeout=45,
        )
        if 200 <= resp.status_code < 300:
            data = resp.json() if resp.content else {}
            return True, str(data.get("id") or email or company)
        return False, f"HTTP {resp.status_code}"
    except Exception as exc:
        return False, str(exc)[:80]
