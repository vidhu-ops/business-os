"""Ensure legacy IIDATECH spreadsheet users exist with original password hashes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _seed_candidates() -> list[Path]:
    root = Path(__file__).resolve().parents[2]
    return [
        # Shipped with the API image (not dockerignored).
        Path(__file__).resolve().parents[1] / "data" / "legacy_iidatech_users_seed.json",
        root / "backend" / "data" / "legacy_iidatech_users_seed.json",
        root / "business_build_outputs" / "legacy_iidatech_users_seed.json",
    ]


def _seed_path() -> Path | None:
    for path in _seed_candidates():
        if path.is_file():
            return path
    return None


def ensure_legacy_users_seeded() -> dict[str, Any]:
    path = _seed_path()
    if path is None:
        return {"created": 0, "password_restored": 0, "unchanged": 0, "seed_found": False}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {
            "created": 0,
            "password_restored": 0,
            "unchanged": 0,
            "seed_found": False,
            "seed_path": str(path),
        }
    if not isinstance(payload, dict) or not payload:
        return {
            "created": 0,
            "password_restored": 0,
            "unchanged": 0,
            "seed_found": True,
            "seed_path": str(path),
        }

    from backend.services.user_store import load_users, save_users

    users = load_users()
    created = password_restored = unchanged = 0
    changed = False

    for email, seed in payload.items():
        key = str(email or "").strip().lower()
        if not key or not isinstance(seed, dict):
            continue
        seed_pw = str(seed.get("password_hash") or "").strip()
        desired_source = str(seed.get("source") or "legacy_iidatech_users_xlsx")
        existing = users.get(key) if isinstance(users.get(key), dict) else None
        if existing is None:
            record = dict(seed)
            record["email"] = key
            record["source"] = desired_source
            users[key] = record
            created += 1
            changed = True
            continue

        touched = False
        if seed_pw and existing.get("password_hash") != seed_pw:
            existing["password_hash"] = seed_pw
            password_restored += 1
            touched = True
        if existing.get("source") != desired_source:
            existing["source"] = desired_source
            touched = True
        if seed.get("legacy_flags") and not existing.get("legacy_flags"):
            existing["legacy_flags"] = seed.get("legacy_flags")
            touched = True
        if seed.get("username") and not existing.get("username"):
            existing["username"] = seed.get("username")
            touched = True
        if seed.get("imported_at") and not existing.get("imported_at"):
            existing["imported_at"] = seed.get("imported_at")
            touched = True

        if touched:
            users[key] = existing
            changed = True
        else:
            unchanged += 1

    if changed:
        save_users(users)
    return {
        "created": created,
        "password_restored": password_restored,
        "unchanged": unchanged,
        "seed_found": True,
        "seed_path": str(path),
        "seed_count": len(payload),
    }
