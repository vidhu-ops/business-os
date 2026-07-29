"""Communication connectors: email, Slack, WhatsApp."""

from __future__ import annotations

import os
import smtplib
from email.mime.text import MIMEText
from typing import Any

import requests

from iidatech.integrations.registry import _env

_TIMEOUT = float(os.getenv("IIDATECH_INTEGRATION_TIMEOUT", "30"))


def send_email_message(to_email: str, subject: str, body: str, *, provider: str = "auto") -> dict[str, Any]:
    user = _env("GMAIL_SMTP_USER", "GMAIL_USER")
    password = _env("GMAIL_SMTP_PASSWORD", "GMAIL_APP_PASSWORD")
    host = _env("GMAIL_SMTP_HOST") or "smtp.gmail.com"
    port = int(_env("GMAIL_SMTP_PORT") or "587")
    if user and password:
        try:
            msg = MIMEText(body, "plain", "utf-8")
            msg["Subject"] = subject
            msg["From"] = user
            msg["To"] = to_email
            with smtplib.SMTP(host, port, timeout=_TIMEOUT) as smtp:
                smtp.starttls()
                smtp.login(user, password)
                smtp.sendmail(user, [to_email], msg.as_string())
            return {"ok": True, "provider": "gmail_smtp", "message": "Email sent via SMTP", "to": to_email}
        except Exception as exc:
            return {"ok": False, "provider": "gmail_smtp", "message": str(exc)[:240]}
    try:
        from backend_integrations import send_email
        return send_email(to_email, subject, body, provider=provider)
    except ImportError:
        return {"ok": False, "provider": "email", "message": "No email provider configured"}


def send_slack_message(text: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        from backend_integrations import post_slack_message
        return post_slack_message(text, extra=extra)
    except ImportError:
        url = _env("SLACK_WEBHOOK_URL", "SLACK_INCOMING_WEBHOOK_URL")
        if not url:
            return {"ok": False, "provider": "slack", "message": "SLACK_WEBHOOK_URL required"}
        try:
            payload: dict[str, Any] = {"text": text}
            if extra:
                payload.update(extra)
            response = requests.post(url, json=payload, timeout=_TIMEOUT)
            if 200 <= response.status_code < 300:
                return {"ok": True, "provider": "slack", "message": "Slack notification posted"}
            return {"ok": False, "provider": "slack", "message": f"HTTP {response.status_code}"}
        except Exception as exc:
            return {"ok": False, "provider": "slack", "message": str(exc)[:200]}


def send_whatsapp_message(to_number: str, body: str) -> dict[str, Any]:
    sid = _env("TWILIO_ACCOUNT_SID")
    token = _env("TWILIO_AUTH_TOKEN")
    from_num = _env("TWILIO_WHATSAPP_FROM", "TWILIO_WHATSAPP_NUMBER")
    if not (sid and token and from_num):
        return {"ok": False, "provider": "whatsapp", "message": "Twilio WhatsApp not configured"}
    to = to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"
    from_wa = from_num if from_num.startswith("whatsapp:") else f"whatsapp:{from_num}"
    url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json"
    try:
        response = requests.post(
            url,
            auth=(sid, token),
            data={"From": from_wa, "To": to, "Body": body},
            timeout=_TIMEOUT,
        )
        if 200 <= response.status_code < 300:
            data = response.json() if response.content else {}
            return {"ok": True, "provider": "whatsapp", "message": "WhatsApp message queued", "sid": data.get("sid")}
        return {"ok": False, "provider": "whatsapp", "message": response.text[:240]}
    except Exception as exc:
        return {"ok": False, "provider": "whatsapp", "message": str(exc)[:200]}