"""Ensure legacy IIDATECH spreadsheet users exist with original password hashes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _seed_path() -> Path:
    return Path(__file__).resolve().parents[2] / "business_build_outputs" / "legacy_iidatech_users_seed.json"


def ensure_legacy_users_seeded() -> dict[str, int]:
    path = _seed_path()
    if not path.is_file():
        return {"created": 0, "password_restored": 0, "unchanged": 0}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"created": 0, "password_restored": 0, "unchanged": 0}
    if not isinstance(payload, dict) or not payload:
        return {"created": 0, "password_restored": 0, "unchanged": 0}

    from backend.services.user_store import load_users, save_users

    users = load_users()
    created = password_restored = unchanged = 0
    changed = False

    for email, seed in payload.items():
        key = str(email or "").strip().lower()
        if not key or not isinstance(seed, dict):
            continue
        seed_pw = str(seed.get("password_hash") or "").strip()
        existing = users.get(key) if isinstance(users.get(key), dict) else None
        if existing is None:
            record = dict(seed)
            record["email"] = key
            users[key] = record
            created += 1
            changed = True
            continue

        # Restore original Werkzeug password hash when seed has one.
        if seed_pw and existing.get("password_hash") != seed_pw:
            existing["password_hash"] = seed_pw
            existing["source"] = str(seed.get("source") or "legacy_iidatech_users_xlsx")
            if seed.get("legacy_flags") and not existing.get("legacy_flags"):
                existing["legacy_flags"] = seed.get("legacy_flags")
            if seed.get("username") and not existing.get("username"):
                existing["username"] = seed.get("username")
            if seed.get("imported_at"):
                existing["imported_at"] = seed.get("imported_at")
            users[key] = existing
            password_restored += 1
            changed = True
        else:
            unchanged += 1

    if changed:
        save_users(users)
    return {"created": created, "password_restored": password_restored, "unchanged": unchanged}
