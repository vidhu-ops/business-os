from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from backend.auth import get_current_user
from backend.services.workspace_context import workspace_report_id
from backend.services.workspaces import load_workspace
from iidatech.integrations.oauth_store import (
    apply_token_payload,
    build_authorization_url,
    exchange_authorization_code,
    oauth_state,
    parse_oauth_state,
    set_connection,
)

from backend.config import settings

router = APIRouter(prefix="/oauth", tags=["oauth"])


def _frontend(path: str) -> str:
    base = (settings.frontend_url or settings.cors_origin_list[0] if settings.cors_origin_list else "http://localhost:3000").rstrip("/")
    return f"{base}{path}"


class ManualOAuthBody(BaseModel):
    access_token: str = ""
    author_urn: str = ""
    smtp_app_password: str = ""


@router.get("/callback")
def oauth_callback(
    code: str = Query(""),
    state: str = Query(""),
    error: str = Query(""),
) -> RedirectResponse:
    base = _frontend("/app/team/oauth-callback")
    if error:
        return RedirectResponse(url=f"{base}?error={error}", status_code=302)
    if not code or not state:
        return RedirectResponse(url=f"{base}?error=missing_code_or_state", status_code=302)

    if "|" not in state:
        from iidatech.integrations.canva_client import exchange_authorization_code as exchange_canva_code
        from iidatech.integrations.oauth_store import apply_canva_token_payload

        ok, payload = exchange_canva_code(state=state, code=code)
        if not ok or not isinstance(payload, dict):
            msg = str(payload)[:120] if payload else "canva_exchange_failed"
            return RedirectResponse(url=f"{base}?error={msg}", status_code=302)
        if payload.get("saved") != "service_account":
            apply_canva_token_payload(payload)
        mode = "service" if payload.get("saved") == "service_account" else "user"
        return RedirectResponse(url=f"{base}?success=1&provider=canva&mode={mode}", status_code=302)

    report_id, provider = parse_oauth_state(state)
    if provider not in {"linkedin", "gmail", "hubspot"}:
        return RedirectResponse(url=f"{base}?error=invalid_provider", status_code=302)
    ok, payload = exchange_authorization_code(provider, code)
    if not ok or not isinstance(payload, dict):
        msg = str(payload)[:120] if payload else "exchange_failed"
        return RedirectResponse(url=f"{base}?error={msg}&report_id={report_id}", status_code=302)
    apply_token_payload(report_id, provider, payload)
    return RedirectResponse(url=f"{base}?success=1&provider={provider}&report_id={report_id}", status_code=302)


@router.get("/{workspace_id}/{provider}/start")
def oauth_start(
    workspace_id: str,
    provider: str,
    _: str = Depends(get_current_user),
) -> RedirectResponse:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    if provider not in {"linkedin", "gmail", "hubspot", "canva"}:
        raise HTTPException(status_code=400, detail="Invalid provider")
    report_id = workspace_report_id(workspace)
    if provider == "canva":
        from iidatech.integrations.canva_client import build_authorize_url, use_service_account

        if use_service_account():
            raise HTTPException(
                status_code=400,
                detail="Canva uses the IIDATECH platform account. Individual OAuth is disabled — ask your admin to complete one-time setup.",
            )
        auth_url, auth_err = build_authorize_url(report_id)
        if not auth_url:
            raise HTTPException(status_code=503, detail=auth_err or "Canva OAuth is not configured")
        return RedirectResponse(url=auth_url, status_code=302)
    auth_url, auth_err = build_authorization_url(provider, state=oauth_state(report_id, provider))
    if not auth_url:
        raise HTTPException(status_code=503, detail=auth_err or "OAuth is not configured for this provider")
    return RedirectResponse(url=auth_url, status_code=302)


@router.post("/{workspace_id}/{provider}")
def save_manual_oauth(
    workspace_id: str,
    provider: str,
    body: ManualOAuthBody,
    _: str = Depends(get_current_user),
) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    report_id = workspace_report_id(workspace)
    if provider not in {"linkedin", "gmail", "hubspot"}:
        raise HTTPException(status_code=400, detail="Invalid provider")
    fields: dict = {}
    if body.access_token.strip():
        fields["access_token"] = body.access_token.strip()
        fields["token"] = body.access_token.strip()
    if body.author_urn.strip():
        fields["author_urn"] = body.author_urn.strip()
    if body.smtp_app_password.strip():
        fields["smtp_app_password"] = body.smtp_app_password.strip()
    if not fields:
        raise HTTPException(status_code=400, detail="No credentials provided")
    set_connection(report_id, provider, fields)
    return {"ok": True, "provider": provider}
