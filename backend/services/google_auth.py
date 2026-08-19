"""Google OAuth for founder sign-in / registration."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
import urllib.request
from typing import Any

from backend.config import settings


GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
SCOPES = "openid email profile"


def google_configured() -> bool:
    return bool(google_client_id() and google_client_secret())


def google_client_id() -> str:
    return (os.getenv("GOOGLE_CLIENT_ID") or os.getenv("GMAIL_CLIENT_ID") or "").strip()


def google_client_secret() -> str:
    return (os.getenv("GOOGLE_CLIENT_SECRET") or os.getenv("GMAIL_CLIENT_SECRET") or "").strip()


def public_frontend_origin() -> str:
    for key in ("PUBLIC_APP_URL", "APP_URL", "FRONTEND_URL"):
        base = (os.getenv(key) or "").strip().rstrip("/")
        if base and "127.0.0.1" not in base and "localhost" not in base.lower():
            return base
    base = (settings.frontend_url or "").strip().rstrip("/")
    if base and "127.0.0.1" not in base and "localhost" not in base.lower():
        return base
    if settings.cors_origin_list:
        for origin in settings.cors_origin_list:
            o = origin.strip().rstrip("/")
            if o and "127.0.0.1" not in o and "localhost" not in o.lower():
                return o
    return (settings.frontend_url or "http://localhost:3000").rstrip("/")


def google_redirect_uri() -> str:
    explicit = (os.getenv("GOOGLE_AUTH_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit
    return f"{public_frontend_origin()}/api/v1/auth/google/callback"


def _state_secret() -> bytes:
    raw = (os.getenv("JWT_SECRET") or settings.jwt_secret or "change-me").encode("utf-8")
    return hashlib.sha256(raw + b":google-auth-state").digest()


def encode_oauth_state(*, next_path: str = "/app/dashboard") -> str:
    nxt = next_path if next_path.startswith("/") else "/app/dashboard"
    if not nxt.startswith("/app"):
        nxt = "/app/dashboard"
    payload = {
        "n": nxt,
        "t": int(time.time()),
        "r": secrets.token_urlsafe(8),
    }
    body = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii").rstrip("=")
    sig = hmac.new(_state_secret(), body.encode("ascii"), hashlib.sha256).hexdigest()[:24]
    return f"{body}.{sig}"


def decode_oauth_state(state: str) -> dict[str, Any] | None:
    try:
        body, sig = (state or "").split(".", 1)
    except ValueError:
        return None
    expect = hmac.new(_state_secret(), body.encode("ascii"), hashlib.sha256).hexdigest()[:24]
    if not hmac.compare_digest(expect, sig):
        return None
    pad = "=" * (-len(body) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(body + pad).decode("utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    if int(time.time()) - int(data.get("t") or 0) > 900:
        return None
    return data


def build_google_auth_url(*, next_path: str = "/app/dashboard") -> str:
    params = {
        "client_id": google_client_id(),
        "redirect_uri": google_redirect_uri(),
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "online",
        "include_granted_scopes": "true",
        "prompt": "select_account",
        "state": encode_oauth_state(next_path=next_path),
    }
    return f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"


def _post_form(url: str, data: dict[str, str]) -> dict[str, Any]:
    body = urllib.parse.urlencode(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str, access_token: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def exchange_google_code(code: str) -> dict[str, Any]:
    token = _post_form(
        GOOGLE_TOKEN_URL,
        {
            "code": code,
            "client_id": google_client_id(),
            "client_secret": google_client_secret(),
            "redirect_uri": google_redirect_uri(),
            "grant_type": "authorization_code",
        },
    )
    access = str(token.get("access_token") or "").strip()
    if not access:
        raise ValueError("Google token exchange failed")
    info = _get_json(GOOGLE_USERINFO_URL, access)
    email = str(info.get("email") or "").strip().lower()
    if not email or not info.get("email_verified", True):
        # Google may omit email_verified on some accounts; require email always.
        if not email:
            raise ValueError("Google account has no email")
    return {
        "email": email,
        "name": str(info.get("name") or info.get("given_name") or email.split("@")[0]).strip(),
        "picture": str(info.get("picture") or ""),
        "sub": str(info.get("sub") or ""),
        "email_verified": bool(info.get("email_verified", True)),
    }