"""Immutable payload identity guard — user topic is source of truth."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

_IDENTITY_FIELDS = ("topic", "idea", "industry", "geography", "target", "routed_domain")


def _norm(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def snapshot_payload_identity(payload: dict[str, Any], *, source: str = "user") -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    return {
        "source": source,
        "stamped_at": datetime.now(timezone.utc).isoformat(),
        "topic": str(payload.get("topic") or payload.get("idea") or ""),
        "idea": str(payload.get("idea") or payload.get("topic") or ""),
        "industry": str(payload.get("industry") or ""),
        "geography": str(payload.get("geography") or payload.get("target") or ""),
        "target": str(payload.get("target") or payload.get("geography") or ""),
        "routed_domain": str(payload.get("routed_domain") or ""),
    }


def stamp_payload_identity(payload: dict[str, Any], *, source: str = "user", force: bool = False) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return snapshot_payload_identity({}, source=source)
    if payload.get("_identity_snapshot") and not force:
        return dict(payload["_identity_snapshot"])
    snap = snapshot_payload_identity(payload, source=source)
    payload["_identity_snapshot"] = snap
    payload["_identity_source"] = source
    return snap


def assert_topic_not_overwritten(payload: dict[str, Any], snapshot: dict[str, Any]) -> list[str]:
    violations: list[str] = []
    if not snapshot:
        return violations
    cur_topic = _norm(payload.get("topic") or payload.get("idea"))
    snap_topic = _norm(snapshot.get("topic") or snapshot.get("idea"))
    if snap_topic and cur_topic and cur_topic != snap_topic:
        violations.append(f"topic_overwritten:{snapshot.get('topic')!r}->{payload.get('topic')!r}")
    return violations


def validate_payload_integrity(payload: dict[str, Any], snapshot: dict[str, Any] | None) -> dict[str, Any]:
    payload = payload if isinstance(payload, dict) else {}
    snapshot = snapshot or payload.get("_identity_snapshot") or {}
    violations: list[str] = []
    violations.extend(assert_topic_not_overwritten(payload, snapshot))

    pairs = (
        ("industry", "industry"),
        ("geography", "geography"),
        ("target", "target"),
        ("routed_domain", "routed_domain"),
    )
    for field, snap_key in pairs:
        expected = _norm(snapshot.get(snap_key))
        actual = _norm(payload.get(field))
        if expected and actual and expected != actual:
            violations.append(f"{field}_drift:{snapshot.get(snap_key)!r}->{payload.get(field)!r}")

    idea_expected = _norm(snapshot.get("idea"))
    idea_actual = _norm(payload.get("idea"))
    if idea_expected and idea_actual and idea_expected != idea_actual:
        violations.append(f"idea_overwritten:{snapshot.get('idea')!r}->{payload.get('idea')!r}")

    corruption = None
    if violations:
        corruption = "; ".join(violations)
        payload["payload_corruption_error"] = corruption

    return {
        "ok": not violations,
        "violations": violations,
        "payload_corruption_error": corruption,
        "snapshot": snapshot,
    }


def export_integrity_trace(payload: dict[str, Any], integrity: dict[str, Any]) -> dict[str, Any]:
    trace = {
        "identity_snapshot": integrity.get("snapshot") or payload.get("_identity_snapshot"),
        "current_identity": snapshot_payload_identity(payload, source="current"),
        "violations": integrity.get("violations") or [],
        "payload_corruption_error": integrity.get("payload_corruption_error"),
    }
    payload["integrity_trace"] = trace
    return trace