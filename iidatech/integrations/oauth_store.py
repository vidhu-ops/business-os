"""Per-workspace OAuth token storage for Employee OS 2 (file-based, not committed)."""
from __future__ import annotations

import json
import os
import time
import hashlib
import urllib.parse
from pathlib import Path
from typing import Any

try:
    from iidatech.env_bootstrap import ensure_env_loaded

    ensure_env_loaded()
except Exception:
    pass
_OAUTH_ROOT = Path(__file__).resolve().parents[2] / "business_build_outputs" / "employee_os2"

PROVIDER_SCOPES: dict[str, str] = {
    "linkedin": "openid profile email w_member_social",
    "hubspot": "crm.objects.contacts.read crm.objects.contacts.write crm.objects.deals.write",
    "gmail": "https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly",
}

PROVIDER_AUTH_URL: dict[str, str] = {
    "linkedin": "https://www.linkedin.com/oauth/v2/authorization",
    "hubspot": "https://app.hubspot.com/oauth/authorize",
    "gmail": "https://accounts.google.com/o/oauth2/v2/auth",
}

PROVIDER_TOKEN_URL: dict[str, str] = {
    "linkedin": "https://www.linkedin.com/oauth/v2/accessToken",
    "hubspot": "https://api.hubapi.com/oauth/v1/token",
    "gmail": "https://oauth2.googleapis.com/token",
}


def oauth_path(report_id: str) -> Path:
    p = _OAUTH_ROOT / str(report_id).strip() / "oauth_connections.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_connections(report_id: str) -> dict[str, Any]:
    path = oauth_path(report_id)
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def save_connections(report_id: str, data: dict[str, Any]) -> None:
    path = oauth_path(report_id)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_connection(report_id: str, provider: str) -> dict[str, Any]:
    return dict(load_connections(report_id).get(provider) or {})


def set_connection(report_id: str, provider: str, fields: dict[str, Any]) -> dict[str, Any]:
    data = load_connections(report_id)
    merged = dict(data.get(provider) or {})
    merged.update({k: v for k, v in fields.items() if v is not None})
    merged["provider"] = provider
    data[provider] = merged
    save_connections(report_id, data)
    return merged


def seed_workspace_from_env(report_id: str) -> dict[str, str]:
    """Copy .env tokens into workspace OAuth store so automations use them without UI paste."""
    seeded: list[str] = []
    hs = str(os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or os.getenv("HUBSPOT_ACCESS_TOKEN") or "").strip()
    if hs and not str(get_connection(report_id, "hubspot").get("access_token") or "").strip():
        set_connection(report_id, "hubspot", {"access_token": hs, "token": hs, "source": "env"})
        seeded.append("hubspot")

    li_tok = str(os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
    li_urn = str(os.getenv("LINKEDIN_AUTHOR_URN") or "").strip()
    conn_li = get_connection(report_id, "linkedin")
    if li_tok and not str(conn_li.get("access_token") or "").strip():
        fields: dict[str, Any] = {"access_token": li_tok, "source": "env"}
        if li_urn:
            fields["author_urn"] = li_urn
        set_connection(report_id, "linkedin", fields)
        seeded.append("linkedin")

    gm_tok = str(os.getenv("GMAIL_ACCESS_TOKEN") or "").strip()
    if gm_tok and not str(get_connection(report_id, "gmail").get("access_token") or "").strip():
        set_connection(report_id, "gmail", {"access_token": gm_tok, "source": "env"})
        seeded.append("gmail")

    smtp_user = str(os.getenv("GMAIL_SMTP_USER") or os.getenv("GMAIL_USER") or "").strip()
    smtp_pass = str(os.getenv("GMAIL_SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or "").strip()
    if smtp_user and smtp_pass:
        conn_gm = get_connection(report_id, "gmail")
        if not str(conn_gm.get("smtp_user") or "").strip():
            set_connection(
                report_id,
                "gmail",
                {
                    "smtp_user": smtp_user,
                    "smtp_password": smtp_pass,
                    "smtp_host": os.getenv("GMAIL_SMTP_HOST") or "smtp.gmail.com",
                    "smtp_port": os.getenv("GMAIL_SMTP_PORT") or "587",
                    "source": "env_smtp",
                },
            )
            seeded.append("gmail_smtp")

    return {"seeded": ",".join(seeded) if seeded else "none"}


_VALIDATION_CACHE: dict[str, tuple[float, str]] = {}
_VALIDATION_TTL = 90.0


def _validation_cache_key(provider: str, secret: str) -> str:
    return f"{provider}:{hashlib.sha256(secret.encode('utf-8', errors='ignore')).hexdigest()[:16]}"


def _live_provider_status(
    provider: str,
    *,
    token: str = "",
    smtp_user: str = "",
    smtp_pass: str = "",
    linkedin_urn: str = "",
) -> str:
    """Live check — only report connected when the API accepts credentials."""
    if provider == "gmail":
        if smtp_user and smtp_pass:
            return "connected"
        if not token:
            return "not connected"
    elif provider == "linkedin":
        if not token or not linkedin_urn:
            return "not connected"
    elif not token:
        return "not connected"

    cache_secret = token or f"{smtp_user}:{smtp_pass}"
    ck = _validation_cache_key(provider, cache_secret)
    cached = _VALIDATION_CACHE.get(ck)
    if cached and (time.time() - cached[0]) < _VALIDATION_TTL:
        return cached[1]

    status = "not connected"
    try:
        import requests

        if provider == "hubspot":
            resp = requests.get(
                "https://api.hubapi.com/crm/v3/objects/contacts?limit=1",
                headers={"Authorization": f"Bearer {token}"},
                timeout=12,
            )
            if resp.status_code == 200:
                status = "connected"
            elif resp.status_code == 401:
                status = "connected but token invalid — reconnect"
        elif provider == "linkedin":
            resp = requests.get(
                "https://api.linkedin.com/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
                timeout=12,
            )
            if resp.status_code == 200:
                status = "connected"
            elif resp.status_code == 401:
                status = "connected but token invalid — reconnect"
        elif provider == "gmail":
            resp = requests.get(
                "https://oauth2.googleapis.com/tokeninfo",
                params={"access_token": token},
                timeout=12,
            )
            if resp.status_code == 200:
                status = "connected"
            elif resp.status_code in {400, 401}:
                status = "connected but token invalid — reconnect"
    except Exception:
        status = "not connected"

    _VALIDATION_CACHE[ck] = (time.time(), status)
    return status


def oauth_env_ready(provider: str) -> bool:
    """True when OAuth app credentials exist in .env (authorization URL can be built)."""
    if provider == "linkedin":
        cid = str(os.getenv("LINKEDIN_CLIENT_ID") or "").strip()
        secret = str(os.getenv("LINKEDIN_CLIENT_SECRET") or "").strip()
        return bool(cid and secret)
    if provider == "hubspot":
        return bool(str(os.getenv("HUBSPOT_CLIENT_ID") or "").strip() and str(os.getenv("HUBSPOT_CLIENT_SECRET") or "").strip())
    if provider == "gmail":
        cid = str(os.getenv("GMAIL_CLIENT_ID") or os.getenv("GOOGLE_CLIENT_ID") or "").strip()
        secret = str(os.getenv("GMAIL_CLIENT_SECRET") or os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
        return bool(cid and secret)
    return False


def is_connected(report_id: str, provider: str) -> bool:
    return connection_label(report_id, provider) == "connected"


def connection_label(report_id: str, provider: str) -> str:
    seed_workspace_from_env(report_id)
    conn = get_connection(report_id, provider)
    if provider == "linkedin":
        token = str(conn.get("access_token") or os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
        urn = str(conn.get("author_urn") or os.getenv("LINKEDIN_AUTHOR_URN") or "").strip()
        return _live_provider_status("linkedin", token=token, linkedin_urn=urn)
    if provider == "hubspot":
        token = str(
            conn.get("access_token") or conn.get("token") or os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or os.getenv("HUBSPOT_ACCESS_TOKEN") or ""
        ).strip()
        return _live_provider_status("hubspot", token=token)
    if provider == "gmail":
        token = str(conn.get("access_token") or os.getenv("GMAIL_ACCESS_TOKEN") or "").strip()
        smtp_user = str(conn.get("smtp_user") or os.getenv("GMAIL_SMTP_USER") or os.getenv("GMAIL_USER") or "").strip()
        smtp_pass = str(conn.get("smtp_password") or os.getenv("GMAIL_SMTP_PASSWORD") or os.getenv("GMAIL_APP_PASSWORD") or "").strip()
        return _live_provider_status("gmail", token=token, smtp_user=smtp_user, smtp_pass=smtp_pass)
    token = str(conn.get("access_token") or "").strip()
    return _live_provider_status(provider, token=token) if token else "not connected"


def connection_status_rows(report_id: str) -> list[dict[str, str]]:
    seed_workspace_from_env(report_id)
    rows: list[dict[str, str]] = []
    for provider in ("gmail", "linkedin", "hubspot"):
        rows.append({
            "App": provider.capitalize(),
            "Status": connection_label(report_id, provider),
            "Use in automations": {
                "gmail": "Read inbox, send email (approval)",
                "linkedin": "Post updates (approval)",
                "hubspot": "Load contacts, sync leads (approval)",
            }.get(provider, ""),
        })
    perplexity = "connected" if str(os.getenv("PERPLEXITY_API_KEY") or "").strip() else "not connected"
    rows.append({"App": "Perplexity", "Status": perplexity, "Use in automations": "Research steps, market reports"})
    return rows


def _default_oauth_redirect_uri() -> str:
    """Public callback URL for OAuth providers (must be reachable from the internet)."""
    explicit = (os.getenv("OAUTH_REDIRECT_URI") or "").strip()
    if explicit:
        return explicit

    frontend = (os.getenv("FRONTEND_URL") or "").strip().rstrip("/")
    if frontend:
        return f"{frontend}/api/v1/oauth/callback"

    for env_name in ("PUBLIC_API_URL", "BACKEND_URL", "RENDER_EXTERNAL_URL", "API_URL"):
        base = (os.getenv(env_name) or "").strip().rstrip("/")
        if not base:
            continue
        if "127.0.0.1" in base or "localhost" in base:
            continue
        return f"{base}/api/v1/oauth/callback"

    # Local combined dev: Next.js proxies /api/v1 → FastAPI
    return "http://localhost:3000/api/v1/oauth/callback"


def _env_client(provider: str) -> tuple[str, str, str]:
    prefix = provider.upper()
    client_id = (os.getenv(f"{prefix}_CLIENT_ID") or os.getenv(f"OAUTH_{prefix}_CLIENT_ID") or "").strip()
    client_secret = (os.getenv(f"{prefix}_CLIENT_SECRET") or os.getenv(f"OAUTH_{prefix}_CLIENT_SECRET") or "").strip()
    if provider == "gmail" and not client_id:
        client_id = (os.getenv("GOOGLE_CLIENT_ID") or "").strip()
    if provider == "gmail" and not client_secret:
        client_secret = (os.getenv("GOOGLE_CLIENT_SECRET") or "").strip()
    redirect_uri = (
        os.getenv(f"{prefix}_REDIRECT_URI")
        or os.getenv("OAUTH_REDIRECT_URI")
        or _default_oauth_redirect_uri()
    ).strip()
    return client_id, client_secret, redirect_uri


def build_authorization_url(provider: str, *, state: str = "") -> tuple[str, str]:
    client_id, _, redirect_uri = _env_client(provider)
    if not client_id:
        return "", f"Set {provider.upper()}_CLIENT_ID (and CLIENT_SECRET) in .env to use OAuth URL flow."
    scope = PROVIDER_SCOPES.get(provider, "")
    params: dict[str, str] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
    }
    if state:
        params["state"] = state
    if provider == "gmail":
        params["access_type"] = "offline"
        params["prompt"] = "consent"
    url = PROVIDER_AUTH_URL[provider] + "?" + urllib.parse.urlencode(params)
    return url, ""


def oauth_state(report_id: str, provider: str) -> str:
    return f"{str(report_id).strip()}|{provider}"


def parse_oauth_state(state: str) -> tuple[str, str]:
    parts = str(state or "").split("|", 1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return str(state or "").strip(), ""


def _token_fields_from_payload(provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    access = str(payload.get("access_token") or payload.get("token") or "").strip()
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
    if provider == "hubspot" and payload.get("hub_id"):
        fields["hub_id"] = payload.get("hub_id")
    return fields


def refresh_access_token(provider: str, refresh_token: str) -> tuple[bool, dict[str, Any] | str]:
    import requests

    refresh_token = str(refresh_token or "").strip()
    if not refresh_token:
        return False, "No refresh token stored."
    client_id, client_secret, redirect_uri = _env_client(provider)
    if not client_id or not client_secret:
        return False, f"Missing {provider.upper()}_CLIENT_ID or CLIENT_SECRET in .env"
    token_url = PROVIDER_TOKEN_URL.get(provider)
    if not token_url:
        return False, f"Unknown provider: {provider}"
    data: dict[str, str] = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if provider == "gmail":
        data["redirect_uri"] = redirect_uri
    try:
        resp = requests.post(token_url, data=data, timeout=45)
        if resp.status_code >= 300:
            return False, f"Refresh HTTP {resp.status_code}: {resp.text[:240]}"
        payload = resp.json() if resp.content else {}
        if not isinstance(payload, dict):
            return False, "Invalid refresh response"
        return True, payload
    except Exception as exc:
        return False, str(exc)[:240]


def get_valid_access_token(report_id: str, provider: str) -> str:
    seed_workspace_from_env(report_id)
    conn = get_connection(report_id, provider)
    token = str(conn.get("access_token") or conn.get("token") or "").strip()
    if not token and provider == "hubspot":
        token = str(os.getenv("HUBSPOT_PRIVATE_APP_TOKEN") or os.getenv("HUBSPOT_ACCESS_TOKEN") or "").strip()
    if not token and provider == "linkedin":
        token = str(os.getenv("LINKEDIN_ACCESS_TOKEN") or "").strip()
    if not token and provider == "gmail":
        token = str(os.getenv("GMAIL_ACCESS_TOKEN") or "").strip()
    expires_at = conn.get("expires_at")
    if token and expires_at:
        try:
            if time.time() < float(expires_at) - 90:
                return token
        except (TypeError, ValueError):
            return token
    refresh = str(conn.get("refresh_token") or "").strip()
    if refresh:
        ok, payload = refresh_access_token(provider, refresh)
        if ok and isinstance(payload, dict):
            fields = _token_fields_from_payload(provider, payload)
            if not fields.get("refresh_token"):
                fields["refresh_token"] = refresh
            set_connection(report_id, provider, fields)
            return str(fields.get("access_token") or token)
    return token


def fetch_linkedin_author_urn(access_token: str) -> tuple[bool, str]:
    import requests

    token = str(access_token or "").strip()
    if not token:
        return False, "No access token"
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=30)
        if resp.status_code >= 300:
            return False, f"LinkedIn profile HTTP {resp.status_code}"
        data = resp.json() if resp.content else {}
        sub = str(data.get("sub") or "").strip()
        if sub.startswith("urn:li:"):
            return True, sub
        if sub:
            return True, f"urn:li:person:{sub}"
        return False, "Could not resolve LinkedIn member id"
    except Exception as exc:
        return False, str(exc)[:200]


def apply_canva_token_payload(payload: dict[str, Any]) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or "").strip()
    fields = _token_fields_from_payload("canva", payload)
    return set_connection(report_id, "canva", fields)


def apply_token_payload(report_id: str, provider: str, payload: dict[str, Any]) -> dict[str, Any]:
    fields = _token_fields_from_payload(provider, payload)
    if provider == "linkedin" and fields.get("access_token") and not fields.get("author_urn"):
        ok, urn = fetch_linkedin_author_urn(str(fields["access_token"]))
        if ok:
            fields["author_urn"] = urn
    return set_connection(report_id, provider, fields)


def exchange_authorization_code(provider: str, code: str) -> tuple[bool, dict[str, Any] | str]:
    import requests

    code = str(code or "").strip()
    if not code:
        return False, "Authorization code is required."
    client_id, client_secret, redirect_uri = _env_client(provider)
    if not client_id or not client_secret:
        return False, f"Missing {provider.upper()}_CLIENT_ID or CLIENT_SECRET in .env"
    token_url = PROVIDER_TOKEN_URL.get(provider)
    if not token_url:
        return False, f"Unknown provider: {provider}"
    data: dict[str, str] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    if provider == "hubspot":
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    try:
        resp = requests.post(token_url, data=data, timeout=45)
        if resp.status_code >= 300:
            return False, f"Token exchange HTTP {resp.status_code}: {resp.text[:240]}"
        payload = resp.json() if resp.content else {}
        if not isinstance(payload, dict):
            return False, "Invalid token response"
        return True, payload
    except Exception as exc:
        return False, str(exc)[:240]
