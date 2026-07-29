"""FastAPI-facing report handler — thin wrapper over report_engine."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]
_ENV_LOADED = False


def _ensure_repo_env() -> None:
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    env_path = _REPO_ROOT / ".env"
    if env_path.exists():
        for raw in env_path.read_text(encoding="utf-8-sig", errors="ignore").splitlines():
            if "=" in raw and not raw.strip().startswith("#"):
                key, value = raw.split("=", 1)
                key = key.strip()
                if key and not os.getenv(key):
                    os.environ[key] = value.strip().strip('"').strip("'")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "1")
    os.environ.setdefault("IIDATECH_LLM_PROVIDER", "auto")
    _ENV_LOADED = True


def _build_options(body: dict[str, Any]) -> dict[str, Any]:
    mode = str(body.get("mode") or "standard").strip().lower()
    extra = dict(body.get("options") or {})
    options: dict[str, Any] = {
        "report_mode": mode,
        "use_cloud_synthesis": bool(body.get("use_cloud_synthesis", True)),
        "iidatech_v2_section_engine": bool(extra.get("iidatech_v2_section_engine", True)),
        "enable_final_audit": bool(extra.get("enable_final_audit", mode == "institutional")),
        "enable_claude_section_audit": bool(extra.get("enable_claude_section_audit", False)),
        "funding_ready_mode": bool(extra.get("funding_ready_mode", mode == "institutional")),
        "enable_auto_topic_research": bool(extra.get("enable_auto_topic_research", True)),
        "quiet_import": True,
    }
    for key, value in extra.items():
        if key != "report_mode":
            options[key] = value
    if mode == "lite":
        options.setdefault("section_range", (1, 2))
        options["funding_ready_mode"] = False
        options["enable_final_audit"] = False
    if body.get("manual_preview"):
        options["manual_preview"] = True
    return options


def enqueue_report_job(body: dict[str, Any], *, project_id: str | None = None) -> str:
    """Enqueue a durable generate_report job; returns job_id."""
    from production_runtime import enqueue_job

    return enqueue_job(
        "generate_report",
        project_id=project_id,
        payload={"report_request": dict(body)},
        priority=35,
        max_attempts=1,
    )


def format_report_job_response(job: dict[str, Any], *, include_html: bool = False) -> dict[str, Any]:
    """Normalize a job_queue row for report polling clients."""
    status = str(job.get("status") or "unknown")
    out: dict[str, Any] = {
        "job_id": job.get("id"),
        "status": status,
        "job_type": job.get("job_type"),
        "error": job.get("error"),
        "created_at": job.get("created_at"),
        "started_at": job.get("started_at"),
        "finished_at": job.get("finished_at"),
    }
    if status != "completed":
        return out
    result = job.get("result") if isinstance(job.get("result"), dict) else {}
    out["success"] = bool(result.get("success"))
    out["summary"] = result.get("summary") if isinstance(result.get("summary"), dict) else {}
    out["report_markdown"] = result.get("report_markdown") or ""
    out["metadata"] = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    out["sources"] = result.get("sources") if isinstance(result.get("sources"), list) else []
    if include_html:
        out["report_html"] = result.get("report_html") or ""
    if result.get("error"):
        out["report_error"] = result.get("error")
    if result.get("v3_guard"):
        out["v3_guard"] = result.get("v3_guard")
    return out


def run_report_api(body: dict[str, Any]) -> dict[str, Any]:
    """Run headless report generation and normalize API response."""
    _ensure_repo_env()
    topic = str(body.get("topic") or "").strip()
    if not topic:
        return {
            "success": False,
            "error": "topic is required",
            "summary": {},
            "report_markdown": "",
            "report_html": "",
            "metadata": {},
            "sources": [],
        }

    from iidatech.services.report_engine import generate_report
    from iidatech.ui.headless_preview import build_preview_summary, render_preview_html

    industry = str(body.get("industry") or "General").strip() or "General"
    geography = str(body.get("geography") or "Global").strip() or "Global"
    report_type = str(body.get("report_type") or "institutional").strip() or "institutional"
    options = _build_options(body)

    if body.get("manual_preview"):
        os.environ["IIDATECH_MANUAL_PREVIEW"] = "1"

    result = generate_report(
        topic,
        industry=industry,
        geography=geography,
        report_type=report_type,
        options=options,
    )

    if body.get("apply_v3_guard", True):
        payload = result.get("payload")
        if isinstance(payload, dict):
            try:
                from iidatech.validation.v3_render_guard import apply_v3_guard_to_payload

                guard = apply_v3_guard_to_payload(payload)
                if isinstance(guard, dict):
                    result["v3_guard"] = guard
                    result["payload"] = payload
            except Exception:
                pass

    summary = build_preview_summary(result)
    report_html = render_preview_html(result)
    metadata = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
    response: dict[str, Any] = {
        "success": bool(result.get("success")),
        "summary": summary,
        "report_markdown": str(result.get("report") or ""),
        "report_html": report_html,
        "metadata": metadata,
        "sources": result.get("sources") if isinstance(result.get("sources"), list) else [],
    }
    if body.get("include_payload"):
        response["payload"] = result.get("payload")
    if result.get("v3_guard"):
        response["v3_guard"] = result.get("v3_guard")
    if not response["success"]:
        errors = metadata.get("errors") if isinstance(metadata.get("errors"), list) else []
        response["error"] = errors[0] if errors else "report generation failed"
    return response
