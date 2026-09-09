from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.audit_service import audit_status, save_audit_record
from backend.services.demo_service import is_demo_user
from backend.services.workspaces import _workspace_row, ensure_audit_workspace, save_workspace

router = APIRouter(prefix="/audit", tags=["audit"])


class MiniGaugeDraftBody(BaseModel):
    draft: dict[str, Any] = Field(default_factory=dict)


@router.get("/status")
def get_audit_status(email: str = Depends(get_current_user)) -> dict:
    return audit_status(email)


@router.get("/workspace")
def get_audit_workspace(email: str = Depends(get_current_user)) -> dict:
    """Return the user's dedicated GAUGE audit workspace, creating it if needed."""
    workspace = ensure_audit_workspace(email)
    ws_dir = Path(str(workspace.get("workspace_dir") or ""))
    row = _workspace_row(workspace, ws_dir / "workspace.json")
    return {
        "workspace_id": workspace.get("workspace_id"),
        "project": row,
        "is_demo": is_demo_user(email),
    }


@router.get("/mini/metadata")
def get_mini_metadata(email: str = Depends(get_current_user)) -> dict:
    from backend.services.mini_gauge_service import mini_metadata

    _ = email
    return mini_metadata()


@router.get("/mini")
def get_mini_gauge(email: str = Depends(get_current_user)) -> dict:
    workspace = ensure_audit_workspace(email)
    draft = workspace.get("mini_gauge_intake") if isinstance(workspace.get("mini_gauge_intake"), dict) else {}
    audit = workspace.get("mini_gauge_audit") if isinstance(workspace.get("mini_gauge_audit"), dict) else None
    urls_fetched = []
    if isinstance(audit, dict):
        urls_fetched = list(audit.get("_urls_fetched") or [])
    return {
        "workspace_id": workspace.get("workspace_id"),
        "draft": draft,
        "audit": audit,
        "urls_fetched": urls_fetched,
        "status": audit_status(email),
        "is_demo": is_demo_user(email),
        "upgrade_href": "/app/audit",
    }


@router.patch("/mini")
def save_mini_gauge(body: MiniGaugeDraftBody, email: str = Depends(get_current_user)) -> dict:
    from backend.services.demo_service import block_workspace_mutation

    workspace = ensure_audit_workspace(email)
    block_workspace_mutation(email, workspace, action="edit mini gauge")
    workspace["mini_gauge_intake"] = body.draft
    save_workspace(workspace)
    return {"draft": body.draft}


@router.delete("/mini")
def reset_mini_gauge(email: str = Depends(get_current_user)) -> dict:
    from backend.services.demo_service import block_workspace_mutation

    workspace = ensure_audit_workspace(email)
    block_workspace_mutation(email, workspace, action="reset mini gauge")
    workspace.pop("mini_gauge_intake", None)
    workspace.pop("mini_gauge_audit", None)
    workspace.pop("mini_gauge_profile", None)
    save_workspace(workspace)
    return {"ok": True}


@router.post("/mini/run")
def run_mini_gauge(body: MiniGaugeDraftBody | None = None, email: str = Depends(get_current_user)) -> dict:
    from backend.services.demo_service import block_workspace_mutation
    from backend.services.mini_gauge_service import run_mini_audit, validate_mini_draft
    from iidatech.services.gauge_audit import merge_gauge_audit_into_profile

    workspace = ensure_audit_workspace(email)
    block_workspace_mutation(email, workspace, action="run mini gauge")

    draft = body.draft if body and isinstance(body.draft, dict) and body.draft else None
    if not draft:
        draft = workspace.get("mini_gauge_intake") if isinstance(workspace.get("mini_gauge_intake"), dict) else {}
    errors = validate_mini_draft(draft)
    if errors:
        raise HTTPException(status_code=400, detail=errors)

    audit, profile, url_context = run_mini_audit(draft)
    profile_with_audit = merge_gauge_audit_into_profile(profile, audit)

    workspace["mini_gauge_intake"] = draft
    workspace["mini_gauge_audit"] = audit
    workspace["mini_gauge_profile"] = profile_with_audit
    save_workspace(workspace)

    # Mini does not consume the free full-audit credit.
    company_name = str(profile.get("company_name") or "Company")
    try:
        save_audit_record(
            email,
            company_name=f"[mini] {company_name}",
            payload={"audit": audit, "mode": "mini", "urls": url_context.get("urls") or []},
        )
    except Exception:
        pass

    return {
        "audit": audit,
        "profile": profile_with_audit,
        "urls": url_context.get("urls") or [],
        "urls_fetched": [
            {"label": s.get("label"), "url": s.get("url"), "fetched": s.get("fetched")}
            for s in (url_context.get("snippets") or [])
        ],
        "upgrade_href": "/app/audit",
        "upgrade_label": "Unlock full GAUGE audit",
        "full_audit_status": audit_status(email),
    }