from __future__ import annotations

import pytest
from fastapi import HTTPException

from backend.services.demo_service import (
    DEMO_EMAIL,
    DEMO_WORKSPACE_ID,
    block_demo_mutation,
    demo_workspace_row,
    is_demo_user,
    is_readonly_workspace,
)
from backend.services.workspaces import build_project_payload, ensure_audit_workspace, list_workspaces_for_user


def test_is_demo_user():
    assert is_demo_user("demo@local")
    assert not is_demo_user("user@example.com")


def test_block_demo_mutation_raises():
    with pytest.raises(HTTPException) as exc:
        block_demo_mutation(DEMO_EMAIL, action="create projects")
    assert exc.value.status_code == 403


def test_readonly_workspace_detection():
    assert is_readonly_workspace({"workspace_id": DEMO_WORKSPACE_ID, "demo_readonly": True})


def test_build_project_payload_sets_owner_email():
    payload = build_project_payload("AI CRM", "India", "SaaS", owner_email="Founder@Example.com")
    assert payload["owner_email"] == "founder@example.com"


def test_list_workspaces_for_demo_user_only_sample():
    rows = list_workspaces_for_user(DEMO_EMAIL)
    assert len(rows) == 1
    assert rows[0]["workspace_id"] == DEMO_WORKSPACE_ID


def test_ensure_audit_workspace_creates_for_user(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.services.workspaces.settings.workspaces_root", tmp_path)
    ws = ensure_audit_workspace("founder@example.com")
    assert ws["workspace_id"].startswith("audit_")
    assert ws["owner_email"] == "founder@example.com"
    assert ws.get("is_audit_workspace") is True
    again = ensure_audit_workspace("founder@example.com")
    assert again["workspace_id"] == ws["workspace_id"]