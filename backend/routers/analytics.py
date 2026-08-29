from __future__ import annotations

import time
from typing import Any
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile
from pydantic import BaseModel, Field

from backend.auth import decode_token, require_admin_email
from backend.services import analytics_store
from backend.services.geo_ua import geo_from_request, is_bot_ua, parse_ua, valid_id
from backend.services.lead_import import parse_lead_sheet


def _optional_email(request: Request) -> str:
    token = ""
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1].strip()
    if not token:
        token = request.cookies.get("iida_session") or ""
    if not token:
        return ""
    try:
        return decode_token(token)
    except Exception:
        return ""

public_router = APIRouter(prefix="/analytics", tags=["analytics"])
admin_router = APIRouter(prefix="/admin/analytics", tags=["admin-analytics"])
leads_router = APIRouter(prefix="/admin", tags=["admin-leads"])

_RATE: dict[str, list[float]] = {}
_RATE_LIMIT = 90
_RATE_WINDOW = 60.0


class CollectBody(BaseModel):
    visitor_id: str = Field(min_length=8, max_length=80)
    session_id: str = Field(min_length=8, max_length=80)
    type: str = "pageview"
    path: str = "/"
    title: str = ""
    href: str = ""
    referrer: str = ""
    pageview_id: str = ""
    duration_ms: int = 0
    scroll_pct: int = 0
    event_name: str = ""
    utm: dict[str, Any] | None = None
    click_ids: dict[str, Any] | None = None
    client: dict[str, Any] | None = None
    props: dict[str, Any] | None = None
    user_email: str = ""


def _rate_ok(key: str) -> bool:
    now = time.time()
    bucket = [ts for ts in _RATE.get(key, []) if now - ts < _RATE_WINDOW]
    if len(bucket) >= _RATE_LIMIT:
        _RATE[key] = bucket
        return False
    bucket.append(now)
    _RATE[key] = bucket
    if len(_RATE) > 5000:
        stale = [k for k, v in _RATE.items() if not v or now - v[-1] > _RATE_WINDOW]
        for k in stale[:1000]:
            _RATE.pop(k, None)
    return True


def _utm(body: CollectBody, key: str) -> str:
    blob = body.utm if isinstance(body.utm, dict) else {}
    return str(blob.get(key) or "")[:120]


def _click(body: CollectBody, key: str) -> str:
    blob = body.click_ids if isinstance(body.click_ids, dict) else {}
    return str(blob.get(key) or "")[:120]


def _landing_host(request: Request, href: str) -> str:
    for raw in (
        href,
        str(request.headers.get("origin") or ""),
        str(request.headers.get("x-forwarded-host") or request.headers.get("host") or ""),
    ):
        host = urlparse(raw if "://" in raw else f"https://{raw}").hostname if raw else None
        if host:
            return host.lower().removeprefix("www.")
    return ""


@public_router.post("/collect")
def collect(body: CollectBody, request: Request) -> dict:
    ua = request.headers.get("user-agent") or str((body.client or {}).get("user_agent") or "")
    if is_bot_ua(ua):
        return {"ok": True, "ignored": "bot"}
    if not valid_id(body.visitor_id) or not valid_id(body.session_id):
        raise HTTPException(status_code=400, detail="Invalid visitor or session id")
    path = (body.path or "/").strip() or "/"
    if not path.startswith("/"):
        path = "/" + path
    if path.startswith("/api/") or path.startswith("/_next"):
        return {"ok": True, "ignored": "asset"}

    client = body.client if isinstance(body.client, dict) else {}
    geo = geo_from_request(request, client)
    rate_key = geo.get("ip_hash") or body.visitor_id
    if not _rate_ok(rate_key):
        return {"ok": True, "ignored": "rate"}

    ua_meta = parse_ua(ua)
    screen_w = client.get("screen_w")
    screen_h = client.get("screen_h")
    viewport_w = client.get("viewport_w")
    viewport_h = client.get("viewport_h")
    screen = ""
    if screen_w and screen_h:
        screen = f"{int(screen_w)}x{int(screen_h)}"
    viewport = ""
    if viewport_w and viewport_h:
        viewport = f"{int(viewport_w)}x{int(viewport_h)}"

    kind = (body.type or "pageview").strip().lower()
    if kind not in {"pageview", "heartbeat", "event", "identify"}:
        kind = "pageview"

    payload: dict[str, Any] = {
        "type": kind,
        "visitor_id": body.visitor_id.strip(),
        "session_id": body.session_id.strip(),
        "pageview_id": (body.pageview_id or "").strip(),
        "path": path[:400],
        "title": (body.title or "")[:200],
        "href": (body.href or "")[:600],
        "referrer": (body.referrer or "")[:600],
        "duration_ms": max(0, min(int(body.duration_ms or 0), 24 * 60 * 60 * 1000)),
        "scroll_pct": max(0, min(int(body.scroll_pct or 0), 100)),
        "event_name": (body.event_name or kind)[:80],
        "props": body.props if isinstance(body.props, dict) else {},
        "utm_source": _utm(body, "source"),
        "utm_medium": _utm(body, "medium"),
        "utm_campaign": _utm(body, "campaign"),
        "utm_term": _utm(body, "term"),
        "utm_content": _utm(body, "content"),
        "gclid": _click(body, "gclid"),
        "fbclid": _click(body, "fbclid"),
        "msclkid": _click(body, "msclkid"),
        "user_agent": ua[:400],
        "device": ua_meta["device"],
        "os": ua_meta["os"],
        "browser": ua_meta["browser"],
        "screen": screen,
        "viewport": viewport,
        "timezone": str(client.get("timezone") or geo.get("timezone") or "")[:64],
        "language": str(client.get("language") or geo.get("language") or "")[:32],
        **geo,
    }
    payload["source"] = analytics_store.source_from_payload(payload, _landing_host(request, body.href))
    if kind == "identify":
        payload["user_email"] = _optional_email(request)
        payload["event_name"] = (body.event_name or "identify")[:80]
        if not payload["user_email"]:
            return {"ok": True, "ignored": "no_session"}
    return analytics_store.ingest(payload)


@admin_router.get("/overview")
def admin_overview(days: int = Query(7, ge=1, le=90), _: str = Depends(require_admin_email)) -> dict:
    return analytics_store.overview(days)


@admin_router.get("/sessions")
def admin_sessions(
    days: int = Query(7, ge=1, le=90),
    q: str = Query(""),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0, le=10_000),
    _: str = Depends(require_admin_email),
) -> dict:
    return analytics_store.list_sessions(days=days, q=q, limit=limit, offset=offset)


@admin_router.get("/sessions/{session_id}")
def admin_session_detail(session_id: str, _: str = Depends(require_admin_email)) -> dict:
    detail = analytics_store.session_detail(session_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Session not found")
    return detail


@admin_router.get("/pages/people")
def admin_page_people(
    path: str = Query("/", min_length=1, max_length=400),
    days: int = Query(7, ge=1, le=90),
    _: str = Depends(require_admin_email),
) -> dict:
    return analytics_store.page_people(path, days)


@admin_router.get("/visitors/{visitor_id}")
def admin_visitor_journey(visitor_id: str, _: str = Depends(require_admin_email)) -> dict:
    detail = analytics_store.visitor_journey(visitor_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Visitor not found")
    return detail


@leads_router.get("/leads")
def admin_leads(
    q: str = Query(""),
    status: str = Query(""),
    limit: int = Query(80, ge=1, le=300),
    offset: int = Query(0, ge=0, le=10_000),
    _: str = Depends(require_admin_email),
) -> dict:
    return analytics_store.list_leads(q=q, status=status, limit=limit, offset=offset)


@leads_router.post("/leads/import")
async def admin_import_leads(
    file: UploadFile = File(...),
    admin: str = Depends(require_admin_email),
) -> dict:
    filename = file.filename or "leads.csv"
    suffix = filename.lower()
    if not suffix.endswith((".csv", ".tsv", ".txt", ".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Upload a CSV or Excel (.xlsx) sheet")
    content = await file.read()
    if len(content) > 4 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File is larger than 4 MB")
    try:
        rows = parse_lead_sheet(content, filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not rows:
        raise HTTPException(status_code=400, detail="No lead rows found. Include a header row with email, name, phone, or company.")
    result = analytics_store.import_leads(rows, imported_by=admin)
    return {"filename": filename, "parsed": len(rows), **result}
