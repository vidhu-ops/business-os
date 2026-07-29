"""Team leader quality check + mentor guidance (deterministic, no LLM)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

MENTOR_ARRIVAL = (
    "Welcome to the office. I am Taylor, your Team Leader. "
    "I will assign work, review deliverables, and guide you through each step. "
    "Start with Clock in when you are ready."
)
MENTOR_STANDUP = (
    "Morning standup: here is what the team will tackle today. "
    "Research validates evidence first, Sales builds pipeline, Growth runs pilots, Ops keeps us on cadence."
)
MENTOR_EXECUTION = (
    "Team is executing. Each task moves Assigned -> In progress -> QC review -> Delivered."
)
MENTOR_QC_PASS = "Quality check passed. Deliverable meets our bar."
MENTOR_DELIVERY = "End-of-day delivery: approved work is packaged below."


def mentor_for_phase(phase: str) -> str:
    return {
        "arrival": MENTOR_ARRIVAL,
        "standup": MENTOR_STANDUP,
        "execution": MENTOR_EXECUTION,
        "qc": "I am reviewing each deliverable before it reaches you.",
        "delivery": MENTOR_DELIVERY,
        "closed": "Office closed for today.",
    }.get(phase, MENTOR_STANDUP)


_PLACEHOLDER_MARKERS = (
    "headline and body for",
    "step 1: follow-up message",
    "lorem ipsum",
    "[insert",
    "<placeholder",
    "tbd tbd",
)


def _looks_like_placeholder(body: str) -> bool:
    low = body.lower()
    return any(m in low for m in _PLACEHOLDER_MARKERS)


def qc_review_item(item: dict[str, Any], result: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or "Task")
    kind = str(item.get("task_kind") or "harness")
    if not result.get("success"):
        err = str(item.get("error") or result.get("reply") or "Execution failed")[:300]
        return {
            "passed": False,
            "score": 0,
            "feedback": err,
            "mentor_note": f"{title} needs a retry: {err}",
            "fixes": ["Check API keys.", "Connect OAuth under Integrations."],
        }
    if kind.startswith("oauth"):
        return {
            "passed": True,
            "score": 1.0,
            "feedback": str(item.get("result") or "done"),
            "mentor_note": f"{title} verified.",
            "fixes": [],
        }
    artifacts = [str(a) for a in (item.get("artifacts") or result.get("artifacts") or []) if a]
    if not artifacts:
        return {
            "passed": False,
            "score": 0.2,
            "feedback": "No output file.",
            "mentor_note": f"{title} - empty work.",
            "fixes": ["Re-run from Office tab."],
        }
    issues: list[str] = []
    ok_files = 0
    for art in artifacts:
        p = Path(art)
        if not p.is_file():
            issues.append(f"Missing file: {p.name}")
            continue
        if p.stat().st_size < 40:
            issues.append(f"File too small: {p.name}")
            continue
        if p.suffix.lower() in {".md", ".txt"}:
            try:
                body = p.read_text(encoding="utf-8", errors="ignore").strip()
                if len(body) < 80:
                    issues.append(f"Draft looks empty: {p.name}")
                    continue
                if "Template draft — no AI provider responded" in body:
                    issues.append(f"Template fallback (no AI provider): {p.name} — add an API key and retry")
                    continue
                if _looks_like_placeholder(body):
                    issues.append(f"Placeholder content: {p.name}")
                    continue
            except OSError:
                issues.append(f"Unreadable: {p.name}")
                continue
        ok_files += 1
    if ok_files == 0:
        return {
            "passed": False,
            "score": 0.3,
            "feedback": "; ".join(issues),
            "mentor_note": f"{title} QC failed.",
            "fixes": issues[:3] or ["Re-run task."],
        }
    return {
        "passed": True,
        "score": round(min(1.0, 0.6 + 0.15 * ok_files), 2),
        "feedback": f"{ok_files} file(s) validated.",
        "mentor_note": f"{title} - {MENTOR_QC_PASS}",
        "fixes": [],
    }
