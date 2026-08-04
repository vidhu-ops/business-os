from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from backend.auth import (
    cookie_secure,
    create_token,
    get_current_user,
    hash_password,
    load_users,
    save_users,
    verify_password,
)
from backend.services.account_service import ensure_account, get_plan_snapshot
from backend.services.audit_service import audit_status, grant_signup_free_audit
from backend.services.demo_service import is_demo_user
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
    }