from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from backend.auth import create_token, get_current_user, hash_password, load_users, save_users
from backend.services.account_service import ensure_account, get_plan_snapshot
from backend.services.audit_service import audit_status, grant_signup_free_audit
from backend.services.demo_service import is_demo_user

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


@router.post("/register")
def register(body: RegisterBody, response: Response) -> dict:
    email = body.email.strip().lower()
    users = load_users()
    if email in users:
        raise HTTPException(status_code=409, detail="Account already exists")
    user_record = {
        "email": email,
        "name": body.name.strip() or email.split("@")[0],
        "password_hash": hash_password(body.password),
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "plan": "starter",
        "credits_remaining": 30,
        "credits_total": 30,
    }
    grant_signup_free_audit(user_record)
    users[email] = user_record
    save_users(users)
    token = create_token(email)
    response.set_cookie(
        key="iida_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=72 * 3600,
    )
    return {"email": email, "name": users[email]["name"], "token": token}


@router.post("/login")
def login(body: LoginBody, response: Response) -> dict:
    email = body.email.strip().lower()
    users = load_users()
    record = users.get(email)
    if not record or record.get("password_hash") != hash_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    ensure_account(email, record.get("name"))
    token = create_token(email)
    response.set_cookie(
        key="iida_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=72 * 3600,
    )
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
    response.set_cookie(
        key="iida_session",
        value=token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=72 * 3600,
    )
    return {"email": email, "name": record.get("name", "Demo User"), "token": token, "is_demo": True}


@router.post("/logout")
def logout(response: Response) -> dict:
    response.delete_cookie("iida_session")
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
