from __future__ import annotations

from typing import Any

from backend.services.workspace_context import workspace_report_context
from iidatech.services.existing_business_profile import existing_business_prompt_section
from iidatech.services.report_engine import generate_report


def build_business_plan(workspace: dict[str, Any]) -> dict[str, Any]:
    idea = str(workspace.get("idea") or "").strip()
    industry = str(workspace.get("industry") or "General").strip()
    geography = str(workspace.get("country") or "Global").strip()
    report_context = workspace.get("_report_context_override") or workspace_report_context(workspace)
    existing_profile = workspace.get("existing_business_profile") if isinstance(workspace.get("existing_business_profile"), dict) else None
    if existing_profile:
        report_context = dict(report_context)
        report_context["existing_business_profile"] = existing_profile
        extra = existing_business_prompt_section(existing_profile)
        if extra:
            report_context["existing_business_prompt"] = extra

    result = generate_report(
        query=idea,
        industry=industry,
        geography=geography,
        report_type="business_intelligence",
        options={
            "evidence_items": [],
            "report_context": report_context or None,
            "application_purpose": str(workspace.get("application_purpose") or "General market research"),
            "founder_readable": True,
            "quiet_import": True,
        },
    )

    markdown = str(result.get("report") or "")
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    payload = metadata.get("payload") if isinstance(metadata.get("payload"), dict) else {}
    plan_json = payload.get("business_plan") if isinstance(payload.get("business_plan"), dict) else {}
    founder_plan = payload.get("founder_readable_plan")

    return {
        "success": bool(result.get("success")),
        "markdown": markdown,
        "report_markdown": markdown,
        "plan_json": plan_json,
        "founder_readable_plan": founder_plan,
        "grounded_in_research": bool(report_context.get("report_markdown")),
        "metadata": metadata,
        "error": (metadata.get("errors") or [None])[0] if not result.get("success") else None,
    }
