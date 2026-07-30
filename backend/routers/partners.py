from __future__ import annotations

import os

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from backend.services.partner_service import (
    get_provider_media_path,
    list_featured_providers,
    list_notifications,
    list_providers,
    public_provider_card,
    register_provider,
    set_provider_status,
)

router = APIRouter(prefix="/partners", tags=["partners"])


class PartnerStatusBody(BaseModel):
    status: str = Field(pattern="^(pending|active|rejected)$")


def _admin_key() -> str:
    return (os.getenv("PARTNER_ADMIN_KEY") or os.getenv("ADMIN_API_KEY") or "").strip()


def _require_admin(x_admin_key: str | None) -> None:
    expected = _admin_key()
    if not expected:
        raise HTTPException(status_code=503, detail="Partner admin API is not configured (set PARTNER_ADMIN_KEY)")
    if (x_admin_key or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid admin key")


@router.post("/register")
async def register_partner(
    company_name: str = Form(...),
    contact_name: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    location: str = Form(...),
    country: str = Form(...),
    services_offered: str = Form(...),
    service_categories: str = Form(default=""),
    description: str = Form(default=""),
    website: str = Form(default=""),
    years_experience: int | None = Form(default=None),
    partner_type: str = Form(default="service_provider"),
    logo: UploadFile | None = File(default=None),
    registration_doc: UploadFile | None = File(default=None),
) -> dict:
    if len(company_name.strip()) < 2:
        raise HTTPException(status_code=400, detail="Company name is required")
    if not logo:
        raise HTTPException(status_code=400, detail="Company logo is required")
    if not registration_doc:
        raise HTTPException(status_code=400, detail="Company registration document is required")

    logo_bytes = await logo.read()
    doc_bytes = await registration_doc.read()
    payload = {
        "company_name": company_name.strip(),
        "contact_name": contact_name.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "location": location.strip(),
        "country": country.strip(),
        "services_offered": services_offered.strip(),
        "service_categories": service_categories.strip(),
        "description": description.strip(),
        "website": website.strip(),
        "years_experience": years_experience,
        "partner_type": partner_type.strip() or "service_provider",
    }
    try:
        record = register_provider(
            payload,
            logo_bytes=logo_bytes,
            logo_filename=logo.filename or "logo.png",
            registration_doc_bytes=doc_bytes,
            registration_doc_filename=registration_doc.filename or "registration.pdf",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not save partner application: {exc}") from exc

    return {
        "ok": True,
        "id": record["id"],
        "message": "Application received. We will review your details and list you on the homepage once approved.",
        "provider": public_provider_card(record),
    }


@router.get("")
def get_partners(limit: int = 100, status: str = "active") -> dict:
    rows = list_providers(status=status or None, limit=min(limit, 200))
    return {
        "providers": [public_provider_card(r) for r in rows],
        "count": len(rows),
    }


@router.get("/featured")
def get_featured_partners(limit: int = 40) -> dict:
    rows = list_featured_providers(limit=min(limit, 60))
    return {"partners": rows, "count": len(rows)}


@router.get("/media/{provider_id}/{filename}")
def partner_media(provider_id: str, filename: str):
    path = get_provider_media_path(provider_id, filename)
    if not path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)


@router.get("/admin/notifications")
def admin_notifications(
    unread_only: bool = False,
    limit: int = 100,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(x_admin_key)
    rows = list_notifications(unread_only=unread_only, limit=min(limit, 200))
    return {"notifications": rows, "count": len(rows)}


@router.get("/admin/applications")
def admin_applications(
    status: str = "pending",
    limit: int = 100,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(x_admin_key)
    rows = list_providers(status=status or None, limit=min(limit, 200))
    return {"providers": rows, "count": len(rows)}


@router.patch("/admin/{provider_id}")
def admin_update_provider(
    provider_id: str,
    body: PartnerStatusBody,
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(x_admin_key)
    try:
        updated = set_provider_status(provider_id, body.status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not updated:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"ok": True, "provider": public_provider_card(updated)}
