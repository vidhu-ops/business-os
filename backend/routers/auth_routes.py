from __future__ import annotations

import secrets
from datetime import datetime, timezone
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from backend.auth import (
    cookie_secure,
    create_token,
    get_current_user,
    hash_password,
    is_admin_email,
    load_users,
    save_users,
    verify_password,
)
from backend.services.account_service import ensure_account, get_plan_snapshot
from backend.services.audit_service import audit_status, grant_signup_free_audit
from backend.services.demo_service import is_demo_user
from backend.services.google_auth import (
    build_google_auth_url,
    decode_oauth_state,
    exchange_google_code,
    google_configured,
    google_redirect_uri,
    public_frontend_origin,
)
from backend.services.pricing_catalog import signup_credits_for_plan

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)
    name: str = ""


class LoginBody(BaseModel):
    email: str = Field(min_length=3)
    password: str


class DemoLoginBody(BaseModel):
    email: str | None = None


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key="iida_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=cookie_secure(),
        max_age=72 * 3600,
        path="/",
    )


@router.post("/register")
def register(body: RegisterBody, response: Response) -> dict:
    email = body.email.strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(status_code=400, detail="Enter a valid email address")
    users = load_users()
    if email in users:
        raise HTTPException(status_code=409, detail="Account already exists — please sign in")
    signup_credits = signup_credits_for_plan("starter")
    user_record = {
        "email": email,
        "name": body.name.strip() or email.split("@")[0],
        "password_hash": hash_password(body.password),
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "plan": "starter",
        "credits_remaining": signup_credits,
        "credits_total": signup_credits,
    }
    grant_signup_free_audit(user_record)
    users[email] = user_record
    save_users(users)
    token = create_token(email)
    _set_session_cookie(response, token)
    return {"email": email, "name": users[email]["name"], "token": token}


@router.post("/login")
def login(body: LoginBody, response: Response) -> dict:
    email = body.email.strip().lower()
    users = load_users()
    record = users.get(email)
    if not record or not verify_password(body.password, str(record.get("password_hash") or "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    # Upgrade legacy SHA256 hashes to scrypt on successful login.
    stored = str(record.get("password_hash") or "")
    if not stored.startswith("scrypt$"):
        record["password_hash"] = hash_password(body.password)
        users[email] = record
        save_users(users)
    ensure_account(email, record.get("name"))
    token = create_token(email)
    _set_session_cookie(response, token)
    return {"email": email, "name": record.get("name", email), "token": token}


@router.post("/demo")
def demo_login(body: DemoLoginBody, response: Response) -> dict:
    email = (body.email or "demo@local").strip().lower()
    users = load_users()
    is_new = email not in users
    record = ensure_account(email, "Demo User")
    if is_new or not record.get("password_hash"):
        users = load_users()
        users[email]["password_hash"] = hash_password("demo")
        save_users(users)
        record = users[email]
    token = create_token(email)
    _set_session_cookie(response, token)
    return {"email": email, "name": record.get("name", "Demo User"), "token": token, "is_demo": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie("iida_session", path="/")
    return {"ok": True}


@router.get("/me")
def me(email: str = Depends(get_current_user)) -> dict:
    record = ensure_account(email)
    plan = get_plan_snapshot(record)
    return {
        "email": email,
        "name": record.get("name") or email.split("@")[0],
        "member_since": record.get("created_at", ""),
        "plan": plan,
        "audit": audit_status(email),
        "is_demo": is_demo_user(email),
        "is_admin": is_admin_email(email),
    }


@router.get("/google/status")
def google_auth_status() -> dict:
    return {
        "enabled": google_configured(),
        "redirect_uri": google_redirect_uri() if google_configured() else None,
    }


@router.get("/google/start")
def google_auth_start(next: str = Query("/app/dashboard")) -> RedirectResponse:
    if not google_configured():
        raise HTTPException(status_code=503, detail="Google sign-in is not configured on this server")
    url = build_google_auth_url(next_path=next or "/app/dashboard")
    return RedirectResponse(url=url, status_code=302)


def _upsert_google_user(*, email: str, name: str, picture: str, sub: str) -> dict:
    users = load_users()
    key = email.strip().lower()
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    if key in users and isinstance(users[key], dict):
        record = users[key]
        record["auth_provider"] = "google"
        if sub:
            record["google_sub"] = sub
        if picture:
            record["picture"] = picture
        if name and not str(record.get("name") or "").strip():
            record["name"] = name
        if not record.get("password_hash"):
            record["password_hash"] = hash_password(secrets.token_urlsafe(32))
        users[key] = record
        save_users(users)
        ensure_account(key, record.get("name"))
        return record

    signup_credits = signup_credits_for_plan("starter")
    user_record = {
        "email": key,
        "name": (name or key.split("@")[0]).strip(),
        "password_hash": hash_password(secrets.token_urlsafe(32)),
        "created_at": now,
        "plan": "starter",
        "credits_remaining": signup_credits,
        "credits_total": signup_credits,
        "auth_provider": "google",
        "google_sub": sub,
        "picture": picture,
    }
    grant_signup_free_audit(user_record)
    users[key] = user_record
    save_users(users)
    return user_record


@router.get("/google/callback")
def google_auth_callback(
    response: Response,
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
) -> RedirectResponse:
    front = public_frontend_origin()
    fail = f"{front}/login?error="
    if error:
        return RedirectResponse(url=f"{fail}{quote(error)}", status_code=302)
    if not google_configured():
        return RedirectResponse(url=f"{fail}google_not_configured", status_code=302)
    if not code or not state:
        return RedirectResponse(url=f"{fail}missing_code", status_code=302)
    parsed = decode_oauth_state(state)
    if not parsed:
        return RedirectResponse(url=f"{fail}invalid_state", status_code=302)
    next_path = str(parsed.get("n") or "/app/dashboard")
    try:
        profile = exchange_google_code(code)
        record = _upsert_google_user(
            email=profile["email"],
            name=profile.get("name") or "",
            picture=profile.get("picture") or "",
            sub=profile.get("sub") or "",
        )
        email = str(record.get("email") or profile["email"]).strip().lower()
        token = create_token(email)
        _set_session_cookie(response, token)
        dest = (
            f"{front}/login/callback"
            f"?token={quote(token)}"
            f"&next={quote(next_path)}"
            f"&email={quote(email)}"
            f"&name={quote(str(record.get('name') or email))}"
        )
        return RedirectResponse(url=dest, status_code=302)
    except Exception as exc:
        return RedirectResponse(url=f"{fail}{quote(str(exc)[:120])}", status_code=302)