"""Account + project organizational memory (business profile, integrations, goals)."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROFILE_FIELDS: list[dict[str, str]] = [
    {"id": "sell", "label": "What do you sell?", "hint": "Product/service and the core offer"},
    {"id": "buyers", "label": "Who buys?", "hint": "ICP, buyer persona, segments"},
    {"id": "competitors", "label": "Competitors?", "hint": "Direct and adjacent competitors"},
    {"id": "pricing", "label": "Pricing?", "hint": "Price points, packages, billing model"},
    {"id": "team", "label": "Team?", "hint": "Founders, roles, headcount"},
    {"id": "revenue_model", "label": "Revenue model?", "hint": "How money is made"},
    {"id": "goals", "label": "Goals?", "hint": "90-day and 12-month outcomes"},
    {"id": "brand", "label": "Brand?", "hint": "Positioning, voice, visual identity notes"},
    {"id": "processes", "label": "Processes?", "hint": "Sales, delivery, ops processes that matter"},
]

INTEGRATION_CATALOG: list[dict[str, str]] = [
    {"id": "google_drive", "label": "Google Drive", "kind": "files"},
    {"id": "gmail", "label": "Gmail", "kind": "email"},
    {"id": "calendar", "label": "Calendar", "kind": "calendar"},
    {"id": "notion", "label": "Notion", "kind": "docs"},
    {"id": "slack", "label": "Slack", "kind": "comms"},
    {"id": "crm", "label": "CRM (HubSpot)", "kind": "crm", "oauth_provider": "hubspot"},
    {"id": "website", "label": "Website", "kind": "url"},
    {"id": "documents", "label": "Documents / Drive links", "kind": "docs"},
    {"id": "linkedin", "label": "LinkedIn", "kind": "social", "oauth_provider": "linkedin"},
]

EMPTY_PROFILE = {f["id"]: "" for f in PROFILE_FIELDS}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _email_slug(email: str) -> str:
    raw = (email or "anon").strip().lower()
    return re.sub(r"[^a-z0-9._-]+", "_", raw)[:80] or "anon"


def _accounts_root() -> Path:
    try:
        from iidatech.execution.output_paths import business_outputs_root

        root = business_outputs_root() / "accounts"
    except Exception:
        from backend.config import settings

        root = settings.outputs_root / "accounts"
    root.mkdir(parents=True, exist_ok=True)
    return root


def account_dir(email: str) -> Path:
    path = _accounts_root() / _email_slug(email)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path, default: Any) -> Any:
    if not path.is_file():
        return default
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if data is not None else default
    except (json.JSONDecodeError, OSError):
        return default


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def load_account_org(email: str) -> dict[str, Any]:
    path = account_dir(email) / "org_memory.json"
    data = _read_json(path, {})
    if not isinstance(data, dict):
        data = {}
    profile = dict(EMPTY_PROFILE)
    raw = data.get("business_profile") if isinstance(data.get("business_profile"), dict) else {}
    for key in EMPTY_PROFILE:
        profile[key] = str(raw.get(key) or "").strip()
    integrations = data.get("integrations") if isinstance(data.get("integrations"), dict) else {}
    goals = data.get("goals") if isinstance(data.get("goals"), list) else []
    return {
        "email": email.strip().lower(),
        "business_profile": profile,
        "integrations": integrations,
        "goals": goals,
        "updated_at": str(data.get("updated_at") or ""),
        "onboarding_complete": bool(data.get("onboarding_complete")),
    }


def save_account_org(email: str, payload: dict[str, Any]) -> dict[str, Any]:
    current = load_account_org(email)
    if isinstance(payload.get("business_profile"), dict):
        for key in EMPTY_PROFILE:
            if key in payload["business_profile"]:
                current["business_profile"][key] = str(payload["business_profile"].get(key) or "").strip()
    if isinstance(payload.get("integrations"), dict):
        merged = dict(current.get("integrations") or {})
        for k, v in payload["integrations"].items():
            if isinstance(v, dict):
                row = dict(merged.get(k) or {})
                row.update({kk: vv for kk, vv in v.items() if vv is not None})
                row["updated_at"] = _now()
                merged[k] = row
            elif v is None:
                merged.pop(str(k), None)
        current["integrations"] = merged
    if isinstance(payload.get("goals"), list):
        current["goals"] = [g for g in payload["goals"] if isinstance(g, dict)]
    if "onboarding_complete" in payload and payload.get("onboarding_complete") is not None:
        current["onboarding_complete"] = bool(payload["onboarding_complete"])
    current["updated_at"] = _now()
    _write_json(account_dir(email) / "org_memory.json", current)
    return current


def profile_completeness(profile: dict[str, Any]) -> dict[str, Any]:
    filled = [k for k in EMPTY_PROFILE if str(profile.get(k) or "").strip()]
    total = len(EMPTY_PROFILE)
    return {
        "filled": len(filled),
        "total": total,
        "pct": int(round(100 * len(filled) / total)) if total else 0,
        "missing": [k for k in EMPTY_PROFILE if k not in filled],
    }


def empty_workspace_profile(*, mode: str = "new") -> dict[str, Any]:
    return {
        "mode": mode if mode in {"new", "existing"} else "new",
        "answers": dict(EMPTY_PROFILE),
        "onboarding_step": "profile",
        "onboarding_complete": False,
        "updated_at": _now(),
    }


def effective_business_profile(workspace: dict[str, Any] | None, email: str | None = None) -> dict[str, Any]:
    """Account profile merged with project overrides (project wins)."""
    base = dict(EMPTY_PROFILE)
    owner = (email or (workspace or {}).get("owner_email") or "").strip().lower()
    if owner:
        acct = load_account_org(owner)
        base.update({k: v for k, v in (acct.get("business_profile") or {}).items() if str(v or "").strip()})
    ws = workspace if isinstance(workspace, dict) else {}
    bp = ws.get("business_profile") if isinstance(ws.get("business_profile"), dict) else {}
    answers = bp.get("answers") if isinstance(bp.get("answers"), dict) else bp
    if isinstance(answers, dict):
        for k in EMPTY_PROFILE:
            val = str(answers.get(k) or "").strip()
            if val:
                base[k] = val
    # GAUGE / existing business enrichments
    ebp = ws.get("existing_business_profile") if isinstance(ws.get("existing_business_profile"), dict) else {}
    if ebp:
        if not base.get("sell") and ebp.get("company_name"):
            base["sell"] = str(ebp.get("description") or ebp.get("company_name") or "")[:800]
        if not base.get("team") and ebp.get("team_size"):
            base["team"] = str(ebp.get("team_size"))
        if not base.get("revenue_model") and (ebp.get("revenue") or ebp.get("business_model")):
            base["revenue_model"] = str(ebp.get("business_model") or ebp.get("revenue") or "")[:800]
        if not base.get("competitors") and ebp.get("competitors"):
            base["competitors"] = str(ebp.get("competitors"))[:800]
        if not base.get("goals") and ebp.get("goals"):
            base["goals"] = str(ebp.get("goals"))[:800]
    return base


def effective_integrations(workspace: dict[str, Any] | None, email: str | None = None) -> dict[str, Any]:
    owner = (email or (workspace or {}).get("owner_email") or "").strip().lower()
    merged: dict[str, Any] = {}
    if owner:
        merged.update(load_account_org(owner).get("integrations") or {})
    ws = workspace if isinstance(workspace, dict) else {}
    local = ws.get("integrations") if isinstance(ws.get("integrations"), dict) else {}
    for k, v in local.items():
        if isinstance(v, dict):
            row = dict(merged.get(k) or {})
            row.update(v)
            merged[k] = row
    return merged


def profile_prompt_block(profile: dict[str, Any]) -> str:
    lines = ["## Organizational memory (founder business context)"]
    for field in PROFILE_FIELDS:
        val = str(profile.get(field["id"]) or "").strip()
        if val:
            lines.append(f"- {field['label']} {val}")
    if len(lines) == 1:
        lines.append("- (not filled yet — ask the founder to complete onboarding)")
    return "\n".join(lines)


def parse_goals_from_text(text: str) -> list[dict[str, Any]]:
    goals: list[dict[str, Any]] = []
    for i, line in enumerate(re.split(r"[\n;]+", text or "")):
        label = line.strip(" -*\t")
        if len(label) < 3:
            continue
        goals.append(
            {
                "id": f"g{i+1}",
                "label": label[:240],
                "target": "",
                "current": "",
                "unit": "",
                "status": "active",
                "progress_pct": 0,
            }
        )
    return goals[:12]


def sync_goals_from_profile(email: str, profile: dict[str, Any]) -> list[dict[str, Any]]:
    org = load_account_org(email)
    existing = list(org.get("goals") or [])
    if existing:
        return existing
    goals = parse_goals_from_text(str(profile.get("goals") or ""))
    if goals:
        save_account_org(email, {"goals": goals})
    return goals


def update_goal_progress(email: str, goal_id: str, *, current: str = "", progress_pct: int | None = None, status: str | None = None) -> dict[str, Any]:
    org = load_account_org(email)
    goals = list(org.get("goals") or [])
    found = False
    for g in goals:
        if str(g.get("id")) != str(goal_id):
            continue
        found = True
        if current != "":
            g["current"] = current
        if progress_pct is not None:
            g["progress_pct"] = max(0, min(100, int(progress_pct)))
        if status:
            g["status"] = status
        g["updated_at"] = _now()
    if not found:
        raise ValueError("Goal not found")
    save_account_org(email, {"goals": goals})
    return {"goals": goals}


def apply_profile_to_workspace(workspace: dict[str, Any], answers: dict[str, Any], *, mode: str | None = None, complete: bool | None = None) -> dict[str, Any]:
    bp = workspace.get("business_profile") if isinstance(workspace.get("business_profile"), dict) else empty_workspace_profile()
    ans = dict(bp.get("answers") or EMPTY_PROFILE)
    for key in EMPTY_PROFILE:
        if key in answers:
            ans[key] = str(answers.get(key) or "").strip()
    bp["answers"] = ans
    if mode in {"new", "existing"}:
        bp["mode"] = mode
    if complete is not None:
        bp["onboarding_complete"] = bool(complete)
        if complete:
            bp["onboarding_step"] = "done"
    bp["updated_at"] = _now()
    workspace["business_profile"] = bp
    return workspace


def seed_workspace_from_account(workspace: dict[str, Any], email: str) -> dict[str, Any]:
    org = load_account_org(email)
    if not isinstance(workspace.get("business_profile"), dict):
        workspace["business_profile"] = empty_workspace_profile()
    answers = dict(workspace["business_profile"].get("answers") or EMPTY_PROFILE)
    for k, v in (org.get("business_profile") or {}).items():
        if k in EMPTY_PROFILE and str(v or "").strip() and not str(answers.get(k) or "").strip():
            answers[k] = str(v).strip()
    workspace["business_profile"]["answers"] = answers
    # Copy account integrations into project as linked refs (no secret duplication of tokens unless present)
    if org.get("integrations") and not workspace.get("integrations"):
        workspace["integrations"] = {
            k: {
                "connected": bool(v.get("connected") or v.get("access_token") or v.get("url") or v.get("credential")),
                "label": next((c["label"] for c in INTEGRATION_CATALOG if c["id"] == k), k),
                "from_account": True,
                "url": v.get("url") or "",
                "notes": v.get("notes") or "",
            }
            for k, v in org["integrations"].items()
            if isinstance(v, dict)
        }
    return workspace


def execution_loop_snapshot(workspace: dict[str, Any], email: str) -> dict[str, Any]:
    """Taylor/Mentor closed-loop state: plan → approve → execute → measure → readjust."""
    profile = effective_business_profile(workspace, email)
    goals = load_account_org(email).get("goals") or parse_goals_from_text(profile.get("goals") or "")
    loop = workspace.get("execution_loop") if isinstance(workspace.get("execution_loop"), dict) else {}
    phase = str(loop.get("phase") or "intake")
    events = list(loop.get("events") or [])[-20:]
    avg = 0
    if goals:
        avg = int(sum(int(g.get("progress_pct") or 0) for g in goals) / max(1, len(goals)))
    return {
        "phase": phase,
        "phases": ["intake", "gauge", "research", "plan", "staff", "execute", "measure", "readjust"],
        "profile_completeness": profile_completeness(profile),
        "goals": goals,
        "goal_progress_avg": avg,
        "pending_approvals": list(loop.get("pending_approvals") or []),
        "last_adjustment": loop.get("last_adjustment"),
        "events": events,
        "mentor_brief": (
            f"Mode={profile and (workspace.get('business_profile') or {}).get('mode') or 'new'}; "
            f"phase={phase}; goals avg progress={avg}%. "
            f"Drive the founder step-by-step; never skip approval for external actions."
        ),
    }


def advance_execution_loop(workspace: dict[str, Any], *, phase: str | None = None, event: str | None = None, approval: dict[str, Any] | None = None) -> dict[str, Any]:
    loop = workspace.get("execution_loop") if isinstance(workspace.get("execution_loop"), dict) else {"phase": "intake", "events": [], "pending_approvals": []}
    if phase:
        loop["phase"] = phase
    events = list(loop.get("events") or [])
    if event:
        events.append({"at": _now(), "text": event[:500]})
    loop["events"] = events[-40:]
    if approval:
        pending = list(loop.get("pending_approvals") or [])
        if approval.get("resolve_id"):
            pending = [p for p in pending if str(p.get("id")) != str(approval.get("resolve_id"))]
        elif approval.get("request"):
            pending.append(
                {
                    "id": f"ap-{len(pending)+1}-{int(datetime.now(timezone.utc).timestamp())}",
                    "title": str(approval.get("request"))[:200],
                    "detail": str(approval.get("detail") or "")[:500],
                    "at": _now(),
                }
            )
        loop["pending_approvals"] = pending[-20:]
    if approval and approval.get("adjustment"):
        loop["last_adjustment"] = {"at": _now(), "text": str(approval.get("adjustment"))[:800]}
    workspace["execution_loop"] = loop
    return workspace


def catalog() -> dict[str, Any]:
    return {"profile_fields": PROFILE_FIELDS, "integrations": INTEGRATION_CATALOG}