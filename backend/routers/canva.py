from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.workspace_context import workspace_report_id
from backend.services.workspaces import load_workspace
from iidatech.integrations.canva_client import (
    build_service_authorize_url,
    canva_env_ready,
    canva_ready_for_users,
    connection_status,
    create_design,
    create_design_from_message,
    exchange_authorization_code,
    export_service_refresh_token,
    infer_design_spec,
    save_service_refresh_token,
    service_account_admin_detail,
    service_account_status,
    use_service_account,
)

router = APIRouter(prefix="/canva", tags=["canva"])


def _admin_key_ok(key: str | None) -> bool:
    import os

    expected = (os.getenv("PARTNER_ADMIN_KEY") or os.getenv("ADMIN_API_KEY") or "").strip()
    return bool(expected) and str(key or "").strip() == expected


class CreateDesignBody(BaseModel):
    title: str = Field(default="IIDATECH Creative", max_length=255)
    preset: str | None = Field(default=None, description="doc, presentation, email, whiteboard")
    width: int | None = Field(default=None, ge=40, le=8000)
    height: int | None = Field(default=None, ge=40, le=8000)
    brief: str = ""


class CreateFromBriefBody(BaseModel):
    message: str = Field(min_length=3)
    topic: str = ""


class AdminCompleteBody(BaseModel):
    code: str = Field(min_length=3)
    state: str = Field(min_length=3)


class AdminRefreshTokenBody(BaseModel):
    refresh_token: str = Field(min_length=10)


def _admin_key_from(key: str = "", x_admin_key: str | None = None) -> str:
    return (x_admin_key or key or "").strip()


def _require_admin(key: str = "", x_admin_key: str | None = None) -> str:
    admin_key = _admin_key_from(key, x_admin_key)
    if not _admin_key_ok(admin_key):
        raise HTTPException(status_code=403, detail="Admin key required (?key= or X-Admin-Key header)")
    return admin_key


def _admin_setup_html(*, key: str, authorize_url: str, status: dict) -> str:
    ready = "yes" if status.get("ready_for_users") else "no"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>IIDATECH Canva setup</title>
  <style>
    body {{ font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    h1 {{ font-size: 1.4rem; }}
    .card {{ border: 1px solid #ccc; border-radius: 8px; padding: 1rem; margin: 1rem 0; }}
    textarea, input[type=text] {{ width: 100%; box-sizing: border-box; font-family: monospace; font-size: 12px; }}
    button {{ padding: 0.5rem 1rem; cursor: pointer; margin: 0.25rem 0.25rem 0.25rem 0; }}
    .ok {{ color: #0a7; }} .err {{ color: #c00; }} .muted {{ color: #666; font-size: 0.9rem; }}
    ol li {{ margin-bottom: 0.5rem; }}
  </style>
</head>
<body>
  <h1>IIDATECH platform Canva setup</h1>
  <p class="muted">Use this page if Canva shows &ldquo;update your browser&rdquo; on your PC. Status: <strong id="st">{status.get("status", "")}</strong> &middot; ready: <strong>{ready}</strong></p>

  <div class="card">
    <h2>Option A &mdash; phone or another computer (recommended)</h2>
    <ol>
      <li>Copy the Canva link below.</li>
      <li>Paste it into <strong>Chrome on your phone</strong> (or another PC).</li>
      <li>Sign in with the IIDATECH Canva account and tap <strong>Allow</strong>.</li>
      <li>When you see &ldquo;IIDATECH platform Canva is connected&rdquo;, you are done.</li>
    </ol>
    <textarea id="authUrl" rows="4" readonly>{authorize_url}</textarea>
    <p><button type="button" onclick="copyAuth()">Copy Canva link</button></p>
    <p id="copyMsg" class="muted"></p>
  </div>

  <div class="card">
    <h2>Option B &mdash; paste callback URL</h2>
    <p class="muted">If you completed Allow on another device, paste the full redirect URL (contains <code>code=</code> and <code>state=</code>).</p>
    <input type="text" id="callbackUrl" placeholder="https://iidatech.biz/api/v1/oauth/callback?code=...&state=..." />
    <p><button type="button" onclick="submitCallback()">Complete setup</button></p>
    <p id="completeMsg"></p>
  </div>

  <div class="card">
    <h2>Option C &mdash; paste refresh token</h2>
    <p class="muted">If you already have a Canva refresh token, paste it here (saved on server; add to Render as CANVA_REFRESH_TOKEN for redeploys).</p>
    <input type="text" id="refreshToken" placeholder="refresh token" />
    <p><button type="button" onclick="saveRefresh()">Save refresh token</button>
       <button type="button" onclick="loadRefresh()">Show saved token for Render</button></p>
    <textarea id="refreshOut" rows="3" readonly placeholder="Saved refresh token appears here"></textarea>
    <p id="refreshMsg"></p>
  </div>

  <script>
    const adminKey = {json.dumps(key)};
    function copyAuth() {{
      const el = document.getElementById('authUrl');
      el.select();
      navigator.clipboard.writeText(el.value).then(() => {{
        document.getElementById('copyMsg').textContent = 'Copied. Open Chrome on your phone and paste in the address bar.';
      }});
    }}
    function parseCallback(raw) {{
      try {{
        const u = new URL(raw.trim());
        return {{ code: u.searchParams.get('code') || '', state: u.searchParams.get('state') || '' }};
      }} catch (e) {{ return {{ code: '', state: '' }}; }}
    }}
    async function submitCallback() {{
      const msg = document.getElementById('completeMsg');
      const {{ code, state }} = parseCallback(document.getElementById('callbackUrl').value);
      if (!code || !state) {{ msg.innerHTML = '<span class="err">Paste the full callback URL with code and state.</span>'; return; }}
      msg.textContent = 'Exchanging...';
      const res = await fetch('/api/v1/canva/admin/complete?key=' + encodeURIComponent(adminKey), {{
        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ code, state }})
      }});
      const data = await res.json().catch(() => ({{}}));
      if (!res.ok) {{ msg.innerHTML = '<span class="err">' + (data.detail || res.status) + '</span>'; return; }}
      msg.innerHTML = '<span class="ok">Connected. Add CANVA_REFRESH_TOKEN to Render if shown below.</span>';
      if (data.refresh_token_for_render) {{
        document.getElementById('refreshOut').value = data.refresh_token_for_render;
      }}
      document.getElementById('st').textContent = 'connected';
    }}
    async function saveRefresh() {{
      const msg = document.getElementById('refreshMsg');
      const token = document.getElementById('refreshToken').value.trim();
      if (!token) {{ msg.innerHTML = '<span class="err">Enter a refresh token.</span>'; return; }}
      const res = await fetch('/api/v1/canva/admin/save-refresh-token?key=' + encodeURIComponent(adminKey), {{
        method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ refresh_token: token }})
      }});
      const data = await res.json().catch(() => ({{}}));
      if (!res.ok) {{ msg.innerHTML = '<span class="err">' + (data.detail || res.status) + '</span>'; return; }}
      msg.innerHTML = '<span class="ok">Saved. ready_for_users: ' + data.ready_for_users + '</span>';
      document.getElementById('st').textContent = 'connected';
    }}
    async function loadRefresh() {{
      const res = await fetch('/api/v1/canva/admin/export-refresh-token?key=' + encodeURIComponent(adminKey));
      const data = await res.json().catch(() => ({{}}));
      document.getElementById('refreshOut').value = data.refresh_token || '';
      document.getElementById('refreshMsg').innerHTML = data.refresh_token
        ? '<span class="ok">Copy this into Render as CANVA_REFRESH_TOKEN</span>'
        : '<span class="err">No refresh token saved yet.</span>';
    }}
  </script>
</body>
</html>"""


@router.get("/admin/connect/start")
def admin_connect_canva(
    key: str = "",
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> RedirectResponse:
    _require_admin(key, x_admin_key)
    # Send admins to the setup wizard (avoids broken Canva browser gate on some desktops).
    return RedirectResponse(url=f"/api/v1/canva/admin/setup?key={_admin_key_from(key, x_admin_key)}", status_code=302)


@router.get("/admin/setup", response_class=HTMLResponse)
def admin_canva_setup(key: str = "") -> HTMLResponse:
    _require_admin(key)
    if not canva_env_ready():
        raise HTTPException(status_code=503, detail="Set CANVA_CLIENT_ID and CANVA_CLIENT_SECRET on the server.")
    authorize_url, err = build_service_authorize_url()
    if not authorize_url:
        raise HTTPException(status_code=503, detail=err or "Canva not configured")
    status = {
        "status": service_account_status(),
        "ready_for_users": canva_ready_for_users(),
        **service_account_admin_detail(),
    }
    return HTMLResponse(_admin_setup_html(key=key, authorize_url=authorize_url, status=status))


@router.get("/admin/authorize-url")
def admin_canva_authorize_url(
    key: str = "",
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(key, x_admin_key)
    authorize_url, err = build_service_authorize_url()
    if not authorize_url:
        raise HTTPException(status_code=503, detail=err or "Canva not configured")
    return {
        "authorize_url": authorize_url,
        "instructions": "Open this URL in Chrome on your phone or another computer. Do not use Cursor or embedded browsers.",
        "setup_page": f"/api/v1/canva/admin/setup?key={_admin_key_from(key, x_admin_key)}",
    }


@router.post("/admin/complete")
def admin_canva_complete(
    body: AdminCompleteBody,
    key: str = "",
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(key, x_admin_key)
    ok, payload = exchange_authorization_code(state=body.state, code=body.code)
    if not ok or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail=str(payload) if payload else "Canva exchange failed")
    refresh = export_service_refresh_token()
    return {
        "success": True,
        "ready_for_users": canva_ready_for_users(),
        "status": service_account_status(),
        "refresh_token_for_render": refresh or None,
        "render_hint": "Add refresh_token_for_render to Render as CANVA_REFRESH_TOKEN to survive redeploys.",
    }


@router.post("/admin/save-refresh-token")
def admin_save_refresh_token(
    body: AdminRefreshTokenBody,
    key: str = "",
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(key, x_admin_key)
    save_service_refresh_token(body.refresh_token)
    return {
        "success": True,
        "ready_for_users": canva_ready_for_users(),
        "status": service_account_status(),
        **service_account_admin_detail(),
    }


@router.get("/admin/export-refresh-token")
def admin_export_refresh_token(
    key: str = "",
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    _require_admin(key, x_admin_key)
    token = export_service_refresh_token()
    if not token:
        raise HTTPException(status_code=404, detail="No refresh token saved yet.")
    return {"refresh_token": token, "render_env_var": "CANVA_REFRESH_TOKEN"}


@router.get("/admin/status")
def admin_canva_status(
    key: str = "",
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
) -> dict:
    admin_key = (x_admin_key or key or "").strip()
    if not _admin_key_ok(admin_key):
        raise HTTPException(status_code=403, detail="Admin key required (?key= or X-Admin-Key header)")
    return {
        "configured": canva_env_ready(),
        "service_account": use_service_account(),
        "status": service_account_status(),
        "ready_for_users": canva_ready_for_users(),
        "setup_page": f"/api/v1/canva/admin/setup?key={admin_key}",
        **service_account_admin_detail(),
    }


@router.get("/{workspace_id}/status")
def canva_status(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    report_id = workspace_report_id(workspace)
    return {
        "configured": canva_env_ready(),
        "service_account": use_service_account(),
        "status": connection_status(report_id),
        "connected": canva_ready_for_users() if use_service_account() else connection_status(report_id) == "connected",
    }


@router.post("/{workspace_id}/designs")
def create_workspace_design(workspace_id: str, body: CreateDesignBody, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    report_id = workspace_report_id(workspace)
    ok, result = create_design(
        report_id,
        title=body.title,
        preset=body.preset,
        width=body.width,
        height=body.height,
    )
    if not ok:
        raise HTTPException(status_code=400, detail=str(result))
    design = (result or {}).get("design") if isinstance(result, dict) else {}
    urls = design.get("urls") if isinstance(design, dict) else {}
    return {
        "success": True,
        "design": design,
        "edit_url": (urls or {}).get("edit_url"),
        "view_url": (urls or {}).get("view_url"),
    }


@router.post("/{workspace_id}/designs/from-brief")
def create_design_from_brief(workspace_id: str, body: CreateFromBriefBody, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    report_id = workspace_report_id(workspace)
    topic = body.topic or str(workspace.get("idea") or "")
    ok, result = create_design_from_message(report_id, body.message, topic=topic)
    if not ok:
        raise HTTPException(status_code=400, detail=str(result))
    design = (result or {}).get("design") if isinstance(result, dict) else {}
    urls = design.get("urls") if isinstance(design, dict) else {}
    spec = infer_design_spec(body.message, default_title=topic[:255] or "IIDATECH Creative")
    return {
        "success": True,
        "spec": spec,
        "design": design,
        "edit_url": (urls or {}).get("edit_url"),
        "view_url": (urls or {}).get("view_url"),
    }
