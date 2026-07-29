"""Scheduling: Cal.com, Google Calendar, ICS fallback."""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

from iidatech.integrations.registry import _env

_TIMEOUT = float(os.getenv("IIDATECH_INTEGRATION_TIMEOUT", "30"))


def book_calcom_meeting(*, title: str, attendee_email: str = "", start_iso: str = "") -> dict[str, Any]:
    key = _env("CALCOM_API_KEY")
    event_type = _env("CALCOM_EVENT_TYPE_ID")
    if not key or not event_type:
        return {"ok": False, "provider": "calcom", "message": "CALCOM_API_KEY and CALCOM_EVENT_TYPE_ID required"}
    start = start_iso or (datetime.now(timezone.utc) + timedelta(days=2)).replace(microsecond=0).isoformat()
    payload = {
        "eventTypeId": int(event_type),
        "start": start,
        "responses": {"email": attendee_email, "name": title[:80]},
        "title": title,
    }
    try:
        response = requests.post(
            "https://api.cal.com/v1/bookings",
            params={"apiKey": key},
            json=payload,
            timeout=_TIMEOUT,
        )
        if 200 <= response.status_code < 300:
            data = response.json() if response.content else {}
            return {"ok": True, "provider": "calcom", "booking": data, "start": start}
        return {"ok": False, "provider": "calcom", "message": response.text[:240]}
    except Exception as exc:
        return {"ok": False, "provider": "calcom", "message": str(exc)[:200]}


def create_calendar_event(*, title: str, out_dir: Path, start_iso: str = "", duration_min: int = 30) -> dict[str, Any]:
    creds_path = _env("GOOGLE_CALENDAR_SERVICE_ACCOUNT_JSON", "GOOGLE_APPLICATION_CREDENTIALS")
    start = start_iso or (datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).isoformat()
    if creds_path and Path(creds_path).exists():
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build

            scopes = ["https://www.googleapis.com/auth/calendar"]
            creds = service_account.Credentials.from_service_account_file(creds_path, scopes=scopes)
            service = build("calendar", "v3", credentials=creds, cache_discovery=False)
            end_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) + timedelta(minutes=duration_min)
            event = {
                "summary": title,
                "start": {"dateTime": start, "timeZone": "UTC"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
            }
            cal_id = _env("GOOGLE_CALENDAR_ID") or "primary"
            created = service.events().insert(calendarId=cal_id, body=event).execute()
            return {"ok": True, "provider": "google_calendar", "event_id": created.get("id"), "htmlLink": created.get("htmlLink")}
        except Exception as exc:
            return {"ok": False, "provider": "google_calendar", "message": str(exc)[:200]}
    out_dir.mkdir(parents=True, exist_ok=True)
    ics_path = out_dir / f"meeting_{uuid.uuid4().hex[:8]}.ics"
    end_dt = datetime.fromisoformat(start.replace("Z", "+00:00")) + timedelta(minutes=duration_min)
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "BEGIN:VEVENT",
        f"SUMMARY:{title}",
        f"DTSTART:{start.replace('-', '').replace(':', '').split('+')[0]}Z",
        f"DTEND:{end_dt.isoformat().replace('-', '').replace(':', '').split('+')[0]}Z",
        "END:VEVENT",
        "END:VCALENDAR",
    ]
    ics_path.write_text("\r\n".join(lines) + "\r\n", encoding="utf-8")
    return {"ok": True, "provider": "ics", "ics_path": str(ics_path), "message": "ICS artifact created"}