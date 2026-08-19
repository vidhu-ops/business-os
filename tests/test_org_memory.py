from pathlib import Path

from backend.services import org_memory as om
from backend.services.workspace_context import workspace_report_context
from backend.services.mentor_service import build_project_brief


def _isolate(monkeypatch, root: Path):
    monkeypatch.setenv("BUSINESS_OUTPUTS_ROOT", str(root))
    from iidatech.execution.output_paths import business_outputs_root

    business_outputs_root.cache_clear()
    root.mkdir(parents=True, exist_ok=True)


def test_profile_fields_complete():
    assert len(om.PROFILE_FIELDS) == 9
    ids = {f["id"] for f in om.PROFILE_FIELDS}
    assert {"sell", "buyers", "goals", "brand", "processes"} <= ids


def test_integration_catalog():
    ids = {i["id"] for i in om.INTEGRATION_CATALOG}
    for need in ("google_drive", "gmail", "calendar", "notion", "slack", "crm", "website", "documents"):
        assert need in ids


def test_effective_profile_project_overrides_account(monkeypatch):
    root = Path("business_build_outputs") / "_test_org_memory_a"
    _isolate(monkeypatch, root)
    om.save_account_org("founder@test.com", {"business_profile": {"sell": "Account product", "buyers": "SMBs"}})
    ws = {
        "owner_email": "founder@test.com",
        "idea": "X",
        "industry": "SaaS",
        "country": "India",
        "business_profile": {"answers": {"sell": "Project product", "goals": "Hit 10 customers"}},
    }
    eff = om.effective_business_profile(ws, "founder@test.com")
    assert eff["sell"] == "Project product"
    assert eff["buyers"] == "SMBs"
    assert "10 customers" in eff["goals"]


def test_workspace_context_includes_org_memory(monkeypatch):
    root = Path("business_build_outputs") / "_test_org_memory_b"
    _isolate(monkeypatch, root)
    ws = {
        "owner_email": "a@b.com",
        "idea": "Warehousing SaaS",
        "industry": "Logistics",
        "country": "India",
        "business_profile": {"answers": {"sell": "WMS", "buyers": "3PLs"}},
    }
    ctx = workspace_report_context(ws)
    assert "org_memory_prompt" in ctx
    assert "WMS" in ctx["org_memory_prompt"]
    assert ctx["business_profile"]["sell"] == "WMS"


def test_execution_loop_advance():
    ws = {"execution_loop": {"phase": "intake", "events": [], "pending_approvals": []}}
    ws = om.advance_execution_loop(ws, phase="research", event="go", approval={"request": "Send email"})
    snap = om.execution_loop_snapshot(ws, "x@y.com")
    assert snap["phase"] == "research"
    assert len(snap["pending_approvals"]) == 1
    rid = snap["pending_approvals"][0]["id"]
    ws = om.advance_execution_loop(ws, approval={"resolve_id": rid})
    assert om.execution_loop_snapshot(ws, "x@y.com")["pending_approvals"] == []


def test_automation_report_id_matches_os2():
    from iidatech.execution.automation_steps import automation_report_id
    from backend.services.workspace_context import workspace_report_id

    assert automation_report_id("Idea", "India") == workspace_report_id({"idea": "Idea", "country": "India"})


def test_mentor_brief_includes_org():
    ws = {
        "idea": "CRM for clinics",
        "industry": "Healthcare",
        "country": "India",
        "owner_email": "doc@test.com",
        "business_profile": {"answers": {"sell": "Clinic CRM", "buyers": "Doctors", "goals": "50 clinics"}},
    }
    brief = build_project_brief(ws)
    assert "org_profile" in brief
    assert brief["org_profile"]["sell"] == "Clinic CRM"
    assert "org_memory_prompt" in brief