"""Human-AI collaboration: task splitting and progress tracking."""
from __future__ import annotations

import re
from typing import Any

_HUMAN_KEYWORDS = re.compile(
    r"\b(approve|sign|review|meet|interview|negotiate|legal|contract|hire|onboard|"
    r"present|demo|call|visit|partner|board|investor|founder|manual|human)\b",
    re.I,
)


def _task_needs_human(item: dict[str, Any]) -> bool:
    blob = f"{item.get('title') or ''} {item.get('prompt') or ''}"
    if bool(item.get("external")):
        return True
    if str(item.get("oauth_provider") or "").strip():
        return True
    return bool(_HUMAN_KEYWORDS.search(blob))


def annotate_checklist_items(
    items: list[dict[str, Any]],
    humans: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Tag each checklist item with assignee_type ai|human."""
    default_human = humans[0] if humans else None
    out: list[dict[str, Any]] = []
    for item in items:
        tagged = dict(item)
        if _task_needs_human(item):
            tagged["assignee_type"] = "human"
            who = str((default_human or {}).get("name") or "You")
            tagged["human_action"] = f"{who}: {item.get('title') or 'Review and approve'}"
            tagged["ai_action"] = ""
            tagged["ai_will_do"] = ""
        else:
            tagged["assignee_type"] = "ai"
            harness = str(item.get("harness_id") or item.get("assignee") or "AI agent")
            tagged["ai_action"] = f"AI ({harness}): {item.get('title') or 'Execute task'}"
            tagged["ai_will_do"] = tagged["ai_action"]
            tagged["human_action"] = f"You: review output when ready" if item.get("external") else ""
        if humans:
            tagged["human_observer"] = ", ".join(str(h.get("name") or "") for h in humans[:3] if h.get("name"))
        out.append(tagged)
    return out


def build_collaboration_plan(
    checklist: dict[str, Any] | None,
    *,
    agents: list[dict[str, Any]] | None = None,
    humans: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    items = list((checklist or {}).get("items") or [])
    tagged = annotate_checklist_items(items, humans)
    ai_items = [i for i in tagged if i.get("assignee_type") == "ai"]
    human_items = [i for i in tagged if i.get("assignee_type") == "human"]
    done_ai = sum(1 for i in ai_items if str(i.get("status")) in ("completed", "approved"))
    done_human = sum(1 for i in human_items if str(i.get("status")) in ("completed", "approved"))
    return {
        "items": [
            {
                "id": i.get("id"),
                "title": i.get("title"),
                "status": i.get("status"),
                "assignee_type": i.get("assignee_type"),
                "human_action": i.get("human_action"),
                "ai_action": i.get("ai_action"),
                "harness_id": i.get("harness_id"),
            }
            for i in tagged
        ],
        "summary": {
            "ai_total": len(ai_items),
            "ai_done": done_ai,
            "human_total": len(human_items),
            "human_done": done_human,
            "agents_active": len(agents or []),
            "humans_on_team": len(humans or []),
        },
        "human_queue": [
            {"id": i.get("id"), "action": i.get("human_action") or i.get("title"), "status": i.get("status")}
            for i in human_items
            if str(i.get("status")) not in ("completed", "approved", "skipped")
        ][:15],
        "ai_queue": [
            {"id": i.get("id"), "action": i.get("ai_action") or i.get("title"), "status": i.get("status")}
            for i in ai_items
            if str(i.get("status")) not in ("completed", "approved", "skipped")
        ][:15],
    }


def merge_collaboration_into_checklist(
    checklist: dict[str, Any],
    collaboration: dict[str, Any] | None,
) -> dict[str, Any]:
    if not collaboration or not isinstance(checklist, dict):
        return checklist
    by_id = {str(i.get("id")): i for i in collaboration.get("items") or []}
    items = []
    for item in checklist.get("items") or []:
        merged = dict(item)
        extra = by_id.get(str(item.get("id")))
        if extra:
            merged.update({k: v for k, v in extra.items() if k not in ("id",) and v})
        items.append(merged)
    out = dict(checklist)
    out["items"] = items
    return out
