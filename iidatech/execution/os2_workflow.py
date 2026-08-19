"""Team-leader checklist persistence and sequential / auto execution for Employee OS 2."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from iidatech.execution.output_paths import employee_os2_root, employee_runtime_root
from iidatech.execution.team_leader import next_runnable_item
from iidatech.integrations.oauth_posting import publish_linkedin_post, send_gmail_message, sync_hubspot_contacts
from iidatech.integrations.oauth_store import is_connected

_WORKFLOW_ROOT = employee_os2_root()


def _post_task_notify(
    report_id: str,
    item: dict[str, Any],
    result: dict[str, Any],
    *,
    report_context: dict[str, Any] | None = None,
) -> None:
    try:
        from iidatech.execution.os2_team_bridge import notify_task_completion

        notify_task_completion(report_id, item, result, report_context=report_context)
    except Exception:
        pass


def checklist_path(report_id: str) -> Path:
    p = _WORKFLOW_ROOT / str(report_id).strip() / "team_checklist.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def load_checklist(report_id: str) -> dict[str, Any] | None:
    path = checklist_path(report_id)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.pop("auto_approve", None)
            return data
        return None
    except (json.JSONDecodeError, OSError):
        return None


def save_checklist(report_id: str, checklist: dict[str, Any]) -> None:
    checklist.pop("auto_approve", None)
    checklist_path(report_id).write_text(json.dumps(checklist, indent=2, ensure_ascii=False), encoding="utf-8")


def approve_task(checklist: dict[str, Any], task_id: str) -> dict[str, Any]:
    for item in checklist.get("items") or []:
        if str(item.get("id")) == str(task_id):
            item["approved"] = True
            item["status"] = "approved"
            break
    return checklist


def skip_task(checklist: dict[str, Any], task_id: str) -> dict[str, Any]:
    for item in checklist.get("items") or []:
        if str(item.get("id")) == str(task_id):
            item["status"] = "skipped"
            item["approved"] = False
            item.pop("error", None)
            break
    return checklist


def retry_task(checklist: dict[str, Any], task_id: str) -> dict[str, Any]:
    """Reset a failed task so it can be run again."""
    for item in checklist.get("items") or []:
        if str(item.get("id")) == str(task_id):
            item["status"] = "approved"
            item["approved"] = True
            item["result"] = ""
            item["artifacts"] = []
            item.pop("error", None)
            item.pop("qc", None)
            break
    return checklist


def failed_checklist_items(checklist: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not checklist:
        return []
    return [i for i in (checklist.get("items") or []) if str(i.get("status")) == "failed"]


def _find_leads_csv(artifacts: list[str], report_id: str) -> str:
    for art in artifacts:
        p = Path(str(art))
        if p.suffix.lower() == ".csv" and "lead" in p.name.lower() and p.is_file():
            return str(p)
    roots = [
        _WORKFLOW_ROOT / report_id,
        employee_runtime_root() / report_id,
    ]
    for root in roots:
        if root.is_dir():
            csvs = sorted(root.rglob("leads_*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)
            if csvs:
                return str(csvs[0])
    return ""


def _find_text_artifact(artifacts: list[str], hints: tuple[str, ...]) -> str:
    for art in artifacts:
        p = Path(str(art))
        if not p.is_file():
            continue
        name = p.name.lower()
        if p.suffix.lower() in {".md", ".txt"} and any(h in name for h in hints):
            try:
                return p.read_text(encoding="utf-8", errors="ignore")[:3000]
            except OSError:
                continue
    for art in artifacts:
        p = Path(str(art))
        if p.is_file() and p.suffix.lower() in {".md", ".txt"}:
            try:
                return p.read_text(encoding="utf-8", errors="ignore")[:3000]
            except OSError:
                continue
    return ""


def _first_lead_email(report_id: str) -> tuple[str, str]:
    csv_path = _find_leads_csv([], report_id)
    if not csv_path:
        return "", ""
    import csv

    try:
        with open(csv_path, encoding="utf-8", errors="ignore", newline="") as fh:
            for row in csv.DictReader(fh):
                email = str(row.get("email") or "").strip()
                if email and "@" in email:
                    subj = f"Quick question on {row.get('company') or 'your team'}"
                    return email, subj
    except OSError:
        pass
    return "", "Pilot outreach"


def _run_oauth_task(
    report_id: str,
    item: dict[str, Any],
    *,
    checklist: dict[str, Any],
) -> tuple[bool, str]:
    provider = str(item.get("oauth_provider") or "").strip()
    kind = str(item.get("task_kind") or "")
    if not is_connected(report_id, provider):
        return False, f"{provider} not connected — open Integrations tab and connect first."

    all_arts: list[str] = []
    for prev in checklist.get("items") or []:
        if str(prev.get("status")) == "completed":
            all_arts.extend([str(a) for a in (prev.get("artifacts") or [])])

    if kind == "oauth_post" and provider == "linkedin":
        text = _find_text_artifact(all_arts, ("campaign", "linkedin", "ad_copy", "outreach"))
        if not text:
            text = str(item.get("prompt") or "")[:500]
        return publish_linkedin_post(report_id, text)

    if kind == "oauth_send" and provider == "gmail":
        body = _find_text_artifact(all_arts, ("outreach", "email", "sequence"))
        to_email, subject = _first_lead_email(report_id)
        if not to_email:
            return False, "No lead email found in CSV — run lead task first."
        if not body:
            body = str(item.get("prompt") or "Following up on our offer.")
        return send_gmail_message(report_id, to_email, subject, body)

    if kind == "oauth_crm" and provider == "hubspot":
        csv_path = _find_leads_csv(all_arts, report_id)
        if not csv_path:
            return False, "No leads CSV found — run lead task first."
        return sync_hubspot_contacts(report_id, csv_path)

    return False, f"Unsupported OAuth task: {kind}/{provider}"


def run_task(
    report_id: str,
    checklist: dict[str, Any],
    item: dict[str, Any],
    *,
    api_keys: dict[str, str] | None = None,
    api_config: dict[str, str] | None = None,
    report_context: dict[str, Any] | None = None,
    extra_harnesses: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    from iidatech.execution.employee_os2_harness import execute_harness_job

    item["status"] = "running"
    kind = str(item.get("task_kind") or "harness")

    try:
        if kind.startswith("oauth"):
            ok, msg = _run_oauth_task(report_id, item, checklist=checklist)
            item["result"] = msg
            item["status"] = "completed" if ok else "failed"
            if not ok:
                item["error"] = msg
            out = {"success": ok, "reply": msg, "artifacts": list(item.get("artifacts") or [])}
            _post_task_notify(report_id, item, out, report_context=report_context)
            return out

        result = execute_harness_job(
            str(item.get("harness_id") or "growth_marketer"),
            str(item.get("prompt") or ""),
            report_id=report_id,
            api_keys=api_keys or {},
            api_config=api_config or {},
            extra_harnesses=extra_harnesses,
            report_context=report_context or {},
        )
        item["result"] = str(result.get("reply") or "")
        item["artifacts"] = list(result.get("artifacts") or [])
        if result.get("success"):
            from iidatech.execution.team_leader_qc import qc_review_item

            qc = qc_review_item(item, result)
            item["qc"] = qc
            item["status"] = "completed" if qc.get("passed") else "qc_failed"
            if not qc.get("passed"):
                item["error"] = str(qc.get("feedback") or "QC failed")
        else:
            item["status"] = "failed"
            item["error"] = item["result"]
        _post_task_notify(report_id, item, result, report_context=report_context)
        return result
    except Exception as exc:
        item["status"] = "failed"
        item["error"] = str(exc)[:400]
        item["result"] = item["error"]
        return {"success": False, "reply": item["error"], "artifacts": []}


def run_next_task(
    report_id: str,
    checklist: dict[str, Any],
    *,
    auto_approve: bool = False,
    api_keys: dict[str, str] | None = None,
    api_config: dict[str, str] | None = None,
    report_context: dict[str, Any] | None = None,
    extra_harnesses: list[dict[str, Any]] | None = None,
    auto_approve_external: bool = False,
    harness_ids: set[str] | None = None,
) -> dict[str, Any]:
    auto = bool(auto_approve)
    item = next_runnable_item(checklist, auto_approve=auto, harness_ids=harness_ids)
    if not item:
        if harness_ids is not None:
            return {
                "done": True,
                "message": "All in-scope tasks completed or waiting on dependencies.",
                "item": None,
            }
        return {"done": True, "message": "All tasks completed or waiting on dependencies.", "item": None}
    # External (OAuth) actions need explicit founder approval unless the founder
    # deliberately opted in via auto_approve_external for this run.
    external = bool(item.get("external")) or str(item.get("task_kind") or "").startswith("oauth")
    if external and auto_approve_external:
        external = False
    if not item.get("approved") and (not auto or external):
        if str(item.get("status")) == "pending":
            item["status"] = "awaiting_approval"
        return {
            "done": False,
            "needs_approval": True,
            "message": f"Awaiting approval: {item.get('title')}",
            "item": item,
        }
    result = run_task(
        report_id,
        checklist,
        item,
        api_keys=api_keys,
        api_config=api_config,
        report_context=report_context,
        extra_harnesses=extra_harnesses,
    )
    save_checklist(report_id, checklist)
    return {
        "done": False,
        "needs_approval": False,
        "message": str(item.get("title") or "Task"),
        "item": item,
        "result": result,
    }


def run_all_tasks(
    report_id: str,
    checklist: dict[str, Any],
    *,
    api_keys: dict[str, str] | None = None,
    api_config: dict[str, str] | None = None,
    report_context: dict[str, Any] | None = None,
    extra_harnesses: list[dict[str, Any]] | None = None,
    max_steps: int = 25,
    harness_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    # Auto-approve is per-invocation only; never persist it into the checklist,
    # otherwise a single "run all" click disables approval gates forever.
    checklist.pop("auto_approve", None)
    logs: list[dict[str, Any]] = []
    for _ in range(max_steps):
        step = run_next_task(
            report_id,
            checklist,
            auto_approve=True,
            api_keys=api_keys,
            api_config=api_config,
            report_context=report_context,
            extra_harnesses=extra_harnesses,
            harness_ids=harness_ids,
        )
        logs.append(step)
        if step.get("done") or step.get("needs_approval"):
            break
        item = step.get("item")
        if item and str(item.get("status")) == "qc_failed":
            step["qc_blocked"] = True
            break
        if item and str(item.get("status")) == "failed" and str(item.get("task_kind") or "").startswith("oauth"):
            break
    save_checklist(report_id, checklist)
    _maybe_run_agent_sync(report_id, report_context)
    return logs


def _maybe_run_agent_sync(report_id: str, report_context: dict[str, Any] | None) -> None:
    try:
        from iidatech.execution.agent_runtime import run_agent_company_cycle

        v3 = report_context if isinstance(report_context, dict) and report_context.get("schema_version") else None
        if not v3 and isinstance(report_context, dict):
            v3 = report_context.get("report_v3") if isinstance(report_context.get("report_v3"), dict) else report_context
        run_agent_company_cycle(report_id, report_v3=v3)
    except Exception:
        pass


def sync_tasks_to_sql(report_id: str, checklist: dict[str, Any]) -> None:
    from iidatech.execution.task_engine import assign_task, create_task
    from iidatech.storage.execution_repository import list_employees

    employees = list_employees(report_id)
    role_to_id: dict[str, str] = {}
    for emp in employees:
        role = str(emp.get("role") or "").lower()
        if "research" in role:
            role_to_id["research_analyst"] = str(emp.get("employee_id") or "")
        elif "sales" in role:
            role_to_id["sales_lead"] = str(emp.get("employee_id") or "")
        elif "growth" in role or "marketing" in role:
            role_to_id["growth_marketer"] = str(emp.get("employee_id") or "")
            role_to_id["creative_producer"] = role_to_id.get("creative_producer") or str(emp.get("employee_id") or "")
        elif "ops" in role or "coo" in role:
            role_to_id["ops_manager"] = str(emp.get("employee_id") or "")
    for item in checklist.get("items") or []:
        if item.get("sql_task_id"):
            continue
        title = str(item.get("title") or "Task")
        hid = str(item.get("harness_id") or "")
        owner = role_to_id.get(hid)
        task = create_task(report_id, title=title, owner_employee_id=owner)
        tid = str(task.get("task_id") or "")
        item["sql_task_id"] = tid
        if owner and tid:
            assign_task(tid, owner)
