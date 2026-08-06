"""Taylor pulse — computes what the team leader should tell the founder right now.

Pure logic (no Streamlit): reads checklist + automation queue state and returns
notifications, pending approvals, and suggested next actions for the floating bubble.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_APPROVAL_STATUSES = {"awaiting_approval", "needs_founder"}
_DONE_STATUSES = {"completed"}
_FAILED_STATUSES = {"failed", "qc_failed"}

_ACTION_EXPLANATIONS: dict[str, str] = {
    "linkedin_post": "publish a real post to your LinkedIn",
    "gmail_send": "send a real email to your first qualified lead",
    "hubspot_sync": "create real contacts in your HubSpot CRM",
    "oauth_post": "publish a real post to your LinkedIn",
    "oauth_send": "send a real email to your first qualified lead",
    "oauth_crm": "create real contacts in your HubSpot CRM",
}


def _artifact_names(item: dict[str, Any]) -> list[str]:
    return [Path(str(a)).name for a in (item.get("artifacts") or []) if a]


def _checklist_rows(checklist: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(checklist, dict):
        return []
    return [i for i in (checklist.get("items") or []) if isinstance(i, dict)]


def _queue_rows(queue: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(queue, dict):
        return []
    return [i for i in (queue.get("items") or []) if isinstance(i, dict)]


def _external_explanation(item: dict[str, Any]) -> str:
    key = str(item.get("action") or item.get("task_kind") or "")
    return _ACTION_EXPLANATIONS.get(key, "run an external action")


def build_taylor_pulse(
    report_id: str,
    *,
    checklist: dict[str, Any] | None = None,
    queue: dict[str, Any] | None = None,
    has_api_keys: bool = False,
    has_leads_csv: bool | None = None,
) -> dict[str, Any]:
    """Summarize office state into founder-facing notifications and suggestions."""
    cl_rows = _checklist_rows(checklist)
    q_rows = _queue_rows(queue)

    approvals: list[dict[str, Any]] = []
    for item in cl_rows:
        status = str(item.get("status"))
        if status in _APPROVAL_STATUSES or (
            bool(item.get("external"))
            and not item.get("approved")
            and status == "pending"
        ):
            approvals.append(
                {
                    "source": "checklist",
                    "id": str(item.get("id") or ""),
                    "title": str(item.get("title") or "Task"),
                    "explanation": _external_explanation(item),
                }
            )

    for item in q_rows:
        if str(item.get("status")) in _APPROVAL_STATUSES:
            approvals.append(
                {
                    "source": "queue",
                    "id": str(item.get("id") or ""),
                    "title": str(item.get("label") or "Step"),
                    "explanation": _external_explanation(item),
                }
            )

    done: list[dict[str, Any]] = []
    for item in cl_rows:
        if str(item.get("status")) in _DONE_STATUSES:
            qc = item.get("qc") if isinstance(item.get("qc"), dict) else {}
            done.append(
                {
                    "source": "checklist",
                    "id": str(item.get("id") or ""),
                    "title": str(item.get("title") or "Task"),
                    "artifacts": _artifact_names(item),
                    "qc_note": str((qc or {}).get("mentor_note") or ""),
                }
            )

    for item in q_rows:
        if str(item.get("status")) in _DONE_STATUSES:
            done.append(
                {
                    "source": "queue",
                    "id": str(item.get("id") or ""),
                    "title": str(item.get("label") or "Step"),
                    "artifacts": _artifact_names(item),
                    "qc_note": "",
                }
            )

    failed: list[dict[str, Any]] = []
    for item in cl_rows:
        if str(item.get("status")) in _FAILED_STATUSES:
            failed.append(
                {
                    "source": "checklist",
                    "id": str(item.get("id") or ""),
                    "title": str(item.get("title") or "Task"),
                    "error": str(item.get("error") or "")[:160],
                    "qc_failed": str(item.get("status")) == "qc_failed",
                }
            )

    for item in q_rows:
        if str(item.get("status")) == "failed":
            failed.append(
                {
                    "source": "queue",
                    "id": str(item.get("id") or ""),
                    "title": str(item.get("label") or "Step"),
                    "error": str(item.get("result") or "")[:160],
                    "qc_failed": False,
                }
            )

    qc_failed = [f for f in failed if f.get("qc_failed")]

    total = len(cl_rows)
    done_count = len(
        [i for i in cl_rows if str(i.get("status")) in {"skipped", "completed"}]
    )

    suggestions = _build_suggestions(
        cl_rows,
        approvals=approvals,
        failed=failed,
        has_api_keys=has_api_keys,
        has_leads_csv=has_leads_csv,
    )
    headline = _build_headline(
        approvals=approvals,
        done=done,
        failed=failed,
        qc_failed=qc_failed,
        total=total,
        done_count=done_count,
        has_api_keys=has_api_keys,
    )

    signature = hashlib.sha256(
        json.dumps(
            {
                "a": [(r["source"], r["id"]) for r in approvals],
                "d": [(r["source"], r["id"]) for r in done],
                "f": [(r["source"], r["id"]) for r in failed],
                "q": [(r["source"], r["id"]) for r in qc_failed],
            },
            sort_keys=True,
        ).encode()
    ).hexdigest()[:16]

    notifications: list[str] = []
    if headline:
        notifications.append(headline)
    for f in failed[:2]:
        err = str(f.get("error") or "").strip()
        title = str(f.get("title") or "Task")
        if err:
            notifications.append(f"{title}: {err[:120]}")
        else:
            notifications.append(f"{title} failed — open Tasks, Retry, or check Integrations keys.")
    if not has_api_keys:
        notifications.append("IIDA tip: paste Perplexity under Integrations (research) — server key covers basic runs; paid key for complex work.")

    return {
        "report_id": report_id,
        "headline": headline,
        "notifications": notifications[:5],
        "approvals": approvals,
        "done": done,
        "failed": failed,
        "qc_failed": qc_failed,
        "suggestions": suggestions,
        "progress": {"done": done_count, "total": total},
        "signature": signature,
    }


def _build_headline(
    *,
    approvals: list[dict[str, Any]],
    done: list[dict[str, Any]],
    failed: list[dict[str, Any]],
    qc_failed: list[dict[str, Any]],
    total: int,
    done_count: int,
    has_api_keys: bool,
) -> str:
    if not has_api_keys:
        return "Add a Perplexity or LLM key in Integrations so the team can start (server Perplexity also works for basic research)."
    if qc_failed:
        title = str(qc_failed[0].get("title") or "Task")
        return f"QC failed on {title} — Retry, or open Integrations if the key was rejected."
    if approvals:
        first = approvals[0]
        more = f" (+{len(approvals) - 1} more)" if len(approvals) > 1 else ""
        return f"I need your approval: {first['title']}{more}."
    if failed:
        err = str(failed[0].get("error") or "")
        if "perplexity" in err.lower() or "api key" in err.lower() or "no deliverable" in err.lower():
            return "A research task failed — check Integrations keys, then Retry. Complex work may need a paid Perplexity key."
        return f"{len(failed)} task(s) need attention — Retry or ask me what broke."
    if total and done_count >= total:
        return "All tasks delivered. Review the artifacts or plan the next sprint."
    if done:
        last = done[-1]
        remaining = max(0, total - done_count)
        return f"{last['title']} is done. {remaining} task(s) left."
    if total:
        return f"{total} tasks queued. Say the word and I'll run the next one."
    return "Office is quiet. Pick a suggestion below to get the team moving."


def _build_suggestions(
    cl_rows: list[dict[str, Any]],
    *,
    approvals: list[dict[str, Any]],
    failed: list[dict[str, Any]],
    has_api_keys: bool,
    has_leads_csv: bool | None,
) -> list[dict[str, Any]]:
    """Ordered, founder-friendly next actions. Each has a kind the UI can act on."""
    out: list[dict[str, Any]] = []
    if not has_api_keys:
        out.append({"kind": "open_keys", "label": "Add Perplexity (or LLM) key in Integrations"})
        return out
    if approvals:
        out.append(
            {
                "kind": "review_approvals",
                "label": f"Review {len(approvals)} pending approval(s)",
            }
        )
    if failed:
        out.append(
            {
                "kind": "retry_failed",
                "label": f"Retry {len(failed)} failed task(s)",
            }
        )
        out.append(
            {
                "kind": "open_keys",
                "label": "Check Integrations keys (use paid Perplexity for complex research)",
            }
        )

    titles_done = {
        str(i.get("title") or "").lower()
        for i in cl_rows
        if str(i.get("status")) == "completed"
    }

    if not cl_rows:
        out.append(
            {
                "kind": "run_next",
                "label": "Start the office day — Taylor assigns the first task",
            }
        )
    elif not any("lead" in t for t in titles_done) and has_leads_csv is not True:
        out.append(
            {
                "kind": "employee_prompt",
                "harness_id": "sales_lead",
                "label": "Find 20 qualified leads (CSV)",
                "prompt": (
                    "Find 20 qualified leads. Export real companies with contact names, "
                    "titles, emails or LinkedIn where available."
                ),
            }
        )
    elif not any("outreach" in t for t in titles_done):
        out.append(
            {
                "kind": "employee_prompt",
                "harness_id": "sales_lead",
                "label": "Draft the cold outreach sequence",
                "prompt": "Write a 3-step cold outreach sequence with opt-out language.",
            }
        )
    elif not any("campaign" in t for t in titles_done):
        out.append(
            {
                "kind": "employee_prompt",
                "harness_id": "growth_marketer",
                "label": "Draft the LinkedIn campaign",
                "prompt": "LinkedIn ad campaign with 3 variants.",
            }
        )
    else:
        out.append({"kind": "run_next", "label": "Run the next queued task"})
    return out[:4]
