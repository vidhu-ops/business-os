from __future__ import annotations

import base64
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.config import settings
from backend.services.user_store import load_users, save_users

security = HTTPBearer(auto_error=False)
LOCAL_AUTH_SALT = "iidatech-local-auth-v1"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def hash_password(password: str) -> str:
    """Hash password with scrypt (new) — verify_password still accepts legacy SHA256."""
    salt = os.urandom(16)
    key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=32,
    )
    return "scrypt$" + base64.b64encode(salt).decode("ascii") + "$" + base64.b64encode(key).decode("ascii")


def _legacy_sha256(password: str) -> str:
    return hashlib.sha256(f"{LOCAL_AUTH_SALT}:{password}".encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    stored = str(password_hash or "")
    if stored.startswith("scrypt$"):
        try:
            _, salt_b64, key_b64 = stored.split("$", 2)
            salt = base64.b64decode(salt_b64.encode("ascii"))
            expected = base64.b64decode(key_b64.encode("ascii"))
            actual = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt,
                n=_SCRYPT_N,
                r=_SCRYPT_R,
                p=_SCRYPT_P,
                dklen=len(expected) or 32,
            )
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False
    # Legacy Flask/Werkzeug: scrypt:N:r:p$salt$hexdigest
    if stored.startswith("scrypt:"):
        try:
            method, salt_s, hex_digest = stored.split("$", 2)
            _label, n_s, r_s, p_s = method.split(":")
            n, r, p = int(n_s), int(r_s), int(p_s)
            expected = bytes.fromhex(hex_digest)
            actual = hashlib.scrypt(
                password.encode("utf-8"),
                salt=salt_s.encode("utf-8"),
                n=n,
                r=r,
                p=p,
                dklen=len(expected) or 64,
            )
            return hmac.compare_digest(actual, expected)
        except Exception:
            return False
    return hmac.compare_digest(stored, _legacy_sha256(password))


def create_token(email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": email.lower().strip(),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=settings.jwt_exp_hours)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        email = str(payload.get("sub") or "").strip().lower()
        if not email:
            raise ValueError("missing subject")
        return email
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired session") from exc


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    token = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    if not token:
        token = request.cookies.get("iida_session")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    return decode_token(token)


def cookie_secure() -> bool:
    public = (
        os.getenv("PUBLIC_APP_URL")
        or os.getenv("FRONTEND_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or ""
    ).lower()
    return public.startswith("https://") or bool(os.getenv("RENDER"))


def admin_emails() -> set[str]:
    raw = (os.getenv("ADMIN_EMAIL") or os.getenv("PARTNER_NOTIFY_EMAIL") or "").strip()
    return {part.strip().lower() for part in raw.split(",") if part.strip()}


def is_admin_email(email: str) -> bool:
    key = (email or "").strip().lower()
    return bool(key) and key in admin_emails()


def require_admin_email(email: str = Depends(get_current_user)) -> str:
    if not is_admin_email(email):
        raise HTTPException(status_code=403, detail="Admin access required")
    return email