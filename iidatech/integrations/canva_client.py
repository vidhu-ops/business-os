"""Canva Connect API -- OAuth PKCE and design creation."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import time
import urllib.parse
from pathlib import Path
from typing import Any

try:
    from iidatech.env_bootstrap import ensure_env_loaded

    ensure_env_loaded()
except Exception:
    pass

CANVA_AUTH_URL = "https://www.canva.com/api/oauth/authorize"
CANVA_TOKEN_URL = "https://api.canva.com/rest/v1/oauth/token"
CANVA_API_BASE = "https://api.canva.com/rest/v1"

CANVA_SCOPES = " ".join(
    [
        "design:content:read",
        "design:content:write",
        "design:meta:read",
        "asset:read",
        "asset:write",
        "profile:read",
    ]
)

_PENDING_TTL_SEC = 600
_PENDING_PATH = Path(__file__).resolve().parents[2] / "business_build_outputs" / "canva_oauth_pending.json"
_SERVICE_ACCOUNT_PATH = Path(__file__).resolve().parents[2] / "business_build_outputs" / "canva_service_account.json"
_SERVICE_REPORT_ID = "__service__"


def use_service_account() -> bool:
    """When true, all users share the platform Canva tokens (no per-user OAuth)."""
    raw = str(os.getenv("CANVA_USE_SERVICE_ACCOUNT", "true")).strip().lower()
    return raw not in {"0", "false", "no", "off"}


def _service_refresh_token() -> str:
    return str(os.getenv("CANVA_REFRESH_TOKEN") or "").strip()


def _load_service_tokens() -> dict[str, Any]:
    if _service_refresh_token():
        return {
            "refresh_token": _service_refresh_token(),
            "access_token": str(os.getenv("CANVA_ACCESS_TOKEN") or "").strip(),
        }
    if not _SERVICE_ACCOUNT_PATH.is_file():
        return {}
    try:
        data = json.loads(_SERVICE_ACCOUNT_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_service_tokens(fields: dict[str, Any]) -> None:
    _SERVICE_ACCOUNT_PATH.parent.mkdir(parents=True, exist_ok=True)
    merged = {**_load_service_tokens(), **fields}
    _SERVICE_ACCOUNT_PATH.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")


def service_account_status() -> str:
    if not canva_env_ready():
        return "not configured"
    if use_service_account() and get_service_access_token():
        return "connected"
    if use_service_account():
        return "needs one-time admin connect"
    return "per-user oauth"


def service_account_admin_detail() -> dict[str, Any]:
    conn = _load_service_tokens()
    disk_refresh = str(conn.get("refresh_token") or "").strip()
    env_refresh = _service_refresh_token()
    refresh = env_refresh or disk_refresh
    return {
        "has_refresh_token": bool(refresh),
        "refresh_token_in_env": bool(env_refresh),
        "refresh_token_on_disk": bool(disk_refresh),
    }


def save_service_refresh_token(refresh_token: str) -> None:
    token = str(refresh_token or "").strip()
    if token:
        _save_service_tokens({"refresh_token": token})


def export_service_refresh_token() -> str:
    conn = _load_service_tokens()
    return str(conn.get("refresh_token") or _service_refresh_token() or "").strip()


def _pending() -> dict[str, Any]:
    if not _PENDING_PATH.is_file():
        return {}
    try:
        data = json.loads(_PENDING_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def _save_pending(data: dict[str, Any]) -> None:
    _PENDING_PATH.parent.mkdir(parents=True, exist_ok=True)
    _PENDING_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _purge_stale_pending(data: dict[str, Any]) -> dict[str, Any]:
    now = time.time()
    kept = {k: v for k, v in data.items() if isinstance(v, dict) and now - float(v.get("created_at") or 0) < _PENDING_TTL_SEC}
    return kept


def canva_env_ready() -> bool:
    return bool(_client_id() and _client_secret())


def canva_ready_for_users() -> bool:
    if not canva_env_ready():
        return False
    if use_service_account():
        return bool(get_service_access_token())
    return True


def _client_id() -> str:
    return str(os.getenv("CANVA_CLIENT_ID") or "").strip()


def _client_secret() -> str:
    return str(os.getenv("CANVA_CLIENT_SECRET") or "").strip()


def _redirect_uri() -> str:
    explicit = str(os.getenv("CANVA_REDIRECT_URI") or os.getenv("OAUTH_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit
    frontend = str(os.getenv("FRONTEND_URL") or "").strip().rstrip("/")
    if frontend:
        return f"{frontend}/api/v1/oauth/callback"
    return "http://localhost:3000/api/v1/oauth/callback"


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def build_authorize_url(report_id: str) -> tuple[str, str]:
    return _build_authorize_url_for(report_id)


def build_service_authorize_url() -> tuple[str, str]:
    """One-time connect for IIDATECH platform Canva (admin only)."""
    return _build_authorize_url_for(_SERVICE_REPORT_ID)


def _build_authorize_url_for(report_id: str) -> tuple[str, str]:
    client_id = _client_id()
    if not client_id:
        return "", "Set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET in .env"
    state = secrets.token_urlsafe(32)
    verifier, challenge = _pkce_pair()
    pending = _purge_stale_pending(_pending())
    pending[state] = {
        "report_id": str(report_id).strip(),
        "code_verifier": verifier,
        "created_at": time.time(),
    }
    _save_pending(pending)
    params = {
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "scope": CANVA_SCOPES,
        "response_type": "code",
        "client_id": client_id,
        "state": state,
        "redirect_uri": _redirect_uri(),
    }
    return CANVA_AUTH_URL + "?" + urllib.parse.urlencode(params), ""


def pop_pending_state(state: str) -> dict[str, Any] | None:
    pending = _purge_stale_pending(_pending())
    row = pending.pop(str(state or "").strip(), None)
    _save_pending(pending)
    return row if isinstance(row, dict) else None


def _basic_auth_header() -> dict[str, str]:
    raw = f"{_client_id()}:{_client_secret()}".encode("utf-8")
    token = base64.b64encode(raw).decode("ascii")
    return {"Authorization": f"Basic {token}"}


def exchange_authorization_code(*, state: str, code: str) -> tuple[bool, dict[str, Any] | str]:
    import requests

    row = pop_pending_state(state)
    if not row:
        return False, "Canva OAuth session expired -- try connecting again."
    verifier = str(row.get("code_verifier") or "").strip()
    report_id = str(row.get("report_id") or "").strip()
    if not verifier or not report_id:
        return False, "Invalid Canva OAuth state."
    if not canva_env_ready():
        return False, "Canva is not configured on the server."
    data = {
        "grant_type": "authorization_code",
        "code": str(code or "").strip(),
        "redirect_uri": _redirect_uri(),
        "code_verifier": verifier,
    }
    try:
        resp = requests.post(
            CANVA_TOKEN_URL,
            headers={**_basic_auth_header(), "Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            timeout=45,
        )
        if resp.status_code >= 300:
            return False, f"Canva token HTTP {resp.status_code}: {resp.text[:240]}"
        payload = resp.json() if resp.content else {}
        if not isinstance(payload, dict) or not payload.get("access_token"):
            return False, "Canva token response missing access_token"
        payload["report_id"] = report_id
        if report_id == _SERVICE_REPORT_ID:
            fields = _token_fields(payload)
            _save_service_tokens(fields)
            if fields.get("refresh_token"):
                payload["saved"] = "service_account"
        return True, payload
    except Exception as exc:
        return False, str(exc)[:240]


def _token_fields(payload: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    access = str(payload.get("access_token") or "").strip()
    if access:
        fields["access_token"] = access
    refresh = str(payload.get("refresh_token") or "").strip()
    if refresh:
        fields["refresh_token"] = refresh
    expires_in = payload.get("expires_in")
    if expires_in is not None:
        try:
            fields["expires_at"] = time.time() + float(expires_in)
        except (TypeError, ValueError):
            pass
    return fields


def refresh_access_token(refresh_token: str) -> tuple[bool, dict[str, Any] | str]:
    import requests

    refresh_token = str(refresh_token or "").strip()
    if not refresh_token or not canva_env_ready():
        return False, "Canva refresh not available."
    data = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    try:
        resp = requests.post(
            CANVA_TOKEN_URL,
            headers={**_basic_auth_header(), "Content-Type": "application/x-www-form-urlencoded"},
            data=data,
            timeout=45,
        )
        if resp.status_code >= 300:
            return False, f"Canva refresh HTTP {resp.status_code}: {resp.text[:240]}"
        payload = resp.json() if resp.content else {}
        if not isinstance(payload, dict):
            return False, "Invalid Canva refresh response"
        return True, payload
    except Exception as exc:
        return False, str(exc)[:240]


def get_service_access_token() -> str:
    conn = _load_service_tokens()
    token = str(conn.get("access_token") or "").strip()
    expires_at = conn.get("expires_at")
    if token and expires_at:
        try:
            if time.time() < float(expires_at) - 90:
                return token
        except (TypeError, ValueError):
            return token
    refresh = str(conn.get("refresh_token") or _service_refresh_token()).strip()
    if refresh:
        ok, payload = refresh_access_token(refresh)
        if ok and isinstance(payload, dict):
            fields = _token_fields(payload)
            if not fields.get("refresh_token"):
                fields["refresh_token"] = refresh
            _save_service_tokens(fields)
            return str(fields.get("access_token") or token)
    return token


def get_valid_access_token(report_id: str) -> str:
    if use_service_account():
        return get_service_access_token()
    from iidatech.integrations.oauth_store import get_connection, set_connection

    conn = get_connection(report_id, "canva")
    token = str(conn.get("access_token") or "").strip()
    expires_at = conn.get("expires_at")
    if token and expires_at:
        try:
            if time.time() < float(expires_at) - 90:
                return token
        except (TypeError, ValueError):
            return token
    refresh = str(conn.get("refresh_token") or "").strip()
    if refresh:
        ok, payload = refresh_access_token(refresh)
        if ok and isinstance(payload, dict):
            fields = _token_fields(payload)
            if not fields.get("refresh_token"):
                fields["refresh_token"] = refresh
            set_connection(report_id, "canva", fields)
            return str(fields.get("access_token") or token)
    return token


def connection_status(report_id: str) -> str:
    if use_service_account():
        return service_account_status()
    token = get_valid_access_token(report_id)
    if not token:
        return "not connected" if canva_env_ready() else "not configured"
    return "connected"


def infer_design_spec(message: str, *, default_title: str = "IIDATECH Creative") -> dict[str, Any]:
    msg = str(message or "").lower()
    title = default_title[:255]
    if "pitch" in msg or "deck" in msg or "presentation" in msg:
        return {"title": title, "preset": "presentation"}
    if "email" in msg or "newsletter" in msg:
        return {"title": title, "preset": "email"}
    if "whiteboard" in msg:
        return {"title": title, "preset": "whiteboard"}
    if any(k in msg for k in ("instagram story", "story", "reel", "vertical")):
        return {"title": title, "custom": {"width": 1080, "height": 1920}}
    if any(k in msg for k in ("linkedin", "social", "post", "square", "instagram")):
        return {"title": title, "custom": {"width": 1080, "height": 1080}}
    if any(k in msg for k in ("banner", "header", "cover")):
        return {"title": title, "custom": {"width": 1600, "height": 900}}
    return {"title": title, "preset": "doc"}


def create_design(report_id: str, *, title: str, preset: str | None = None, width: int | None = None, height: int | None = None) -> tuple[bool, dict[str, Any] | str]:
    import requests

    token = get_valid_access_token(report_id)
    if not token:
        if use_service_account():
            return False, "Platform Canva is not connected yet -- admin must complete one-time setup."
        return False, "Connect Canva first under Employee OS -> Integrations."
    body: dict[str, Any] = {"title": (title or "IIDATECH Creative")[:255]}
    if preset:
        body["design_type"] = {"type": "preset", "name": preset}
    elif width and height:
        body["design_type"] = {"type": "custom", "width": int(width), "height": int(height)}
    else:
        body["design_type"] = {"type": "preset", "name": "doc"}
    try:
        resp = requests.post(
            f"{CANVA_API_BASE}/designs",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=body,
            timeout=60,
        )
        if resp.status_code >= 300:
            return False, f"Canva design HTTP {resp.status_code}: {resp.text[:300]}"
        payload = resp.json() if resp.content else {}
        if not isinstance(payload, dict):
            return False, "Invalid Canva design response"
        return True, payload
    except Exception as exc:
        return False, str(exc)[:300]


def create_design_from_message(report_id: str, message: str, *, topic: str = "") -> tuple[bool, dict[str, Any] | str]:
    spec = infer_design_spec(message, default_title=(topic or "IIDATECH Creative")[:255])
    custom = spec.get("custom") if isinstance(spec.get("custom"), dict) else None
    if custom:
        return create_design(
            report_id,
            title=str(spec.get("title") or "IIDATECH Creative"),
            width=int(custom.get("width") or 1080),
            height=int(custom.get("height") or 1080),
        )
    return create_design(report_id, title=str(spec.get("title") or "IIDATECH Creative"), preset=str(spec.get("preset") or "doc"))
