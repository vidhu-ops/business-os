from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import settings

logger = logging.getLogger(__name__)

LOGO_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
DOC_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx"}
MAX_LOGO_BYTES = 2 * 1024 * 1024
MAX_DOC_BYTES = 10 * 1024 * 1024


def _providers_path() -> Path:
    return settings.outputs_root / "service_providers.json"


def _notifications_path() -> Path:
    return settings.outputs_root / "partner_notifications.json"


def _uploads_root() -> Path:
    path = settings.outputs_root / "partner_uploads"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_all() -> list[dict[str, Any]]:
    path = _providers_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict) and isinstance(payload.get("providers"), list):
            return payload["providers"]
    except Exception:
        pass
    return []


def _save_all(rows: list[dict[str, Any]]) -> None:
    path = _providers_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"providers": rows, "updated_at": datetime.now(timezone.utc).isoformat()}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return cleaned[:80] or "provider"


def _save_upload(provider_id: str, field: str, filename: str, content: bytes, allowed: set[str], max_bytes: int) -> str:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in allowed:
        raise ValueError(f"Unsupported file type for {field}: {suffix or 'unknown'}")
    if len(content) > max_bytes:
        raise ValueError(f"{field} exceeds maximum size ({max_bytes // (1024 * 1024)} MB)")
    folder = _uploads_root() / provider_id
    folder.mkdir(parents=True, exist_ok=True)
    safe_name = f"{field}{suffix}"
    target = folder / safe_name
    target.write_bytes(content)
    return f"/api/v1/partners/media/{provider_id}/{safe_name}"


def _notify_admin(record: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    notification = {
        "id": f"pn_{uuid.uuid4().hex[:12]}",
        "type": "partner_application",
        "provider_id": record.get("id"),
        "company_name": record.get("company_name"),
        "email": record.get("email"),
        "phone": record.get("phone"),
        "status": record.get("status"),
        "created_at": now,
        "read": False,
    }
    path = _notifications_path()
    rows: list[dict[str, Any]] = []
    if path.exists():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                rows = payload
            elif isinstance(payload, dict) and isinstance(payload.get("notifications"), list):
                rows = payload["notifications"]
        except Exception:
            rows = []
    rows.insert(0, notification)
    path.write_text(json.dumps({"notifications": rows[:500], "updated_at": now}, indent=2), encoding="utf-8")

    message = (
        f"New IIDATECH service provider application\n\n"
        f"Company: {record.get('company_name')}\n"
        f"Contact: {record.get('contact_name')} <{record.get('email')}>\n"
        f"Phone: {record.get('phone')}\n"
        f"Location: {record.get('location')}, {record.get('country')}\n"
        f"Services: {record.get('services_offered')}\n"
        f"ID: {record.get('id')}\n"
        f"Status: {record.get('status')}\n"
    )
    admin_email = (os.getenv("ADMIN_EMAIL") or os.getenv("PARTNER_NOTIFY_EMAIL") or "").strip()
    email_result: dict[str, Any] | None = None
    if admin_email:
        try:
            from iidatech.integrations.comms import send_email_message

            email_result = send_email_message(
                admin_email,
                f"[IIDATECH] New partner application — {record.get('company_name')}",
                message,
            )
        except Exception as exc:
            logger.warning("Partner admin email failed: %s", exc)
            email_result = {"ok": False, "message": str(exc)[:200]}

    slack_result: dict[str, Any] | None = None
    try:
        from iidatech.integrations.comms import send_slack_message

        slack_result = send_slack_message(message)
    except Exception as exc:
        logger.debug("Partner slack notify skipped: %s", exc)

    logger.info("Partner application received: %s (%s)", record.get("company_name"), record.get("id"))
    return {"notification": notification, "email": email_result, "slack": slack_result}


def register_provider(
    payload: dict[str, Any],
    *,
    logo_bytes: bytes | None = None,
    logo_filename: str = "",
    registration_doc_bytes: bytes | None = None,
    registration_doc_filename: str = "",
) -> dict[str, Any]:
    rows = _load_all()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    company = str(payload.get("company_name") or "").strip()
    services = str(payload.get("services_offered") or "").strip()
    provider_id = f"sp_{uuid.uuid4().hex[:12]}"
    record: dict[str, Any] = {
        "id": provider_id,
        "slug": _slug(company or services),
        "status": "pending",
        "company_name": company,
        "contact_name": str(payload.get("contact_name") or "").strip(),
        "email": str(payload.get("email") or "").strip().lower(),
        "phone": str(payload.get("phone") or "").strip(),
        "website": str(payload.get("website") or "").strip(),
        "location": str(payload.get("location") or "").strip(),
        "country": str(payload.get("country") or "").strip(),
        "services_offered": services,
        "service_categories": [c.strip() for c in str(payload.get("service_categories") or "").split(",") if c.strip()],
        "description": str(payload.get("description") or "").strip(),
        "years_experience": payload.get("years_experience"),
        "partner_type": str(payload.get("partner_type") or "service_provider").strip(),
        "logo_url": "",
        "registration_doc_url": "",
        "created_at": now,
        "updated_at": now,
    }

    if logo_bytes:
        record["logo_url"] = _save_upload(provider_id, "logo", logo_filename, logo_bytes, LOGO_SUFFIXES, MAX_LOGO_BYTES)
    if registration_doc_bytes:
        record["registration_doc_url"] = _save_upload(
            provider_id,
            "registration",
            registration_doc_filename,
            registration_doc_bytes,
            DOC_SUFFIXES,
            MAX_DOC_BYTES,
        )

    rows.append(record)
    _save_all(rows)
    _notify_admin(record)
    return record


def list_providers(*, status: str | None = "active", limit: int = 200) -> list[dict[str, Any]]:
    rows = _load_all()
    if status:
        rows = [r for r in rows if str(r.get("status") or "active") == status]
    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    return rows[:limit]


def list_featured_providers(limit: int = 40) -> list[dict[str, Any]]:
    rows = [r for r in _load_all() if str(r.get("status")) == "active"]
    rows.sort(key=lambda r: str(r.get("created_at") or ""), reverse=True)
    featured = [r for r in rows if str(r.get("logo_url") or "").strip()]
    if not featured:
        featured = rows
    return [
        {
            "id": r.get("id"),
            "company_name": r.get("company_name"),
            "logo_url": r.get("logo_url"),
            "website": r.get("website"),
            "location": r.get("location"),
            "country": r.get("country"),
        }
        for r in featured[:limit]
    ]


def get_provider_media_path(provider_id: str, filename: str) -> Path | None:
    if not re.fullmatch(r"sp_[a-f0-9]{12}", provider_id or ""):
        return None
    if not re.fullmatch(r"(logo|registration)\.[a-z0-9]+", filename or "", re.I):
        return None
    path = (_uploads_root() / provider_id / filename).resolve()
    if not str(path).startswith(str(_uploads_root().resolve())):
        return None
    return path if path.is_file() else None


def list_notifications(*, unread_only: bool = False, limit: int = 100) -> list[dict[str, Any]]:
    path = _notifications_path()
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        rows = payload.get("notifications") if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            return []
        if unread_only:
            rows = [r for r in rows if not r.get("read")]
        return rows[:limit]
    except Exception:
        return []


def set_provider_status(provider_id: str, status: str) -> dict[str, Any] | None:
    allowed = {"pending", "active", "rejected"}
    if status not in allowed:
        raise ValueError(f"Invalid status: {status}")
    rows = _load_all()
    updated: dict[str, Any] | None = None
    for row in rows:
        if str(row.get("id")) == provider_id:
            row["status"] = status
            row["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            updated = row
            break
    if not updated:
        return None
    _save_all(rows)
    return updated


def public_provider_card(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": record.get("id"),
        "company_name": record.get("company_name"),
        "services_offered": record.get("services_offered"),
        "location": record.get("location"),
        "country": record.get("country"),
        "status": record.get("status"),
        "logo_url": record.get("logo_url"),
        "website": record.get("website"),
        "service_categories": record.get("service_categories") or [],
    }
