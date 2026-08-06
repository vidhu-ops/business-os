"""Employee OS 2 harnesses."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from iidatech.execution.session_api_keys import active_providers, has_any_llm_key, provider_label, session_api_keys
from iidatech.execution.tool_runtime import run_tool_calls

_ARTIFACT_ROOT = Path(__file__).resolve().parents[2] / "business_build_outputs" / "employee_os2"

OS2_HARNESSES: list[dict[str, Any]] = [
    {"id": "research_analyst", "name": "Sam — Research", "role": "Research Analyst", "tagline": "Search and evidence",
     "starters": ["Search competitors and pricing", "Pull competitors from report", "Log evidence gaps"]},
    {"id": "sales_lead", "name": "Alex — Sales Lead", "role": "Sales Lead", "tagline": "Leads, outreach, proposals",
     "starters": ["Find 20 qualified leads and export CSV", "Write a 3-step cold outreach sequence", "Score leads and flag top prospects"]},
    {"id": "growth_marketer", "name": "Morgan — Growth", "role": "Growth Marketer", "tagline": "Campaigns and ad copy",
     "starters": ["LinkedIn ad campaign with 3 variants", "Email campaign draft", "Launch week outreach"]},
    {"id": "creative_producer", "name": "Riley — Creative", "role": "Growth Marketer", "tagline": "Briefs and storyboards",
     "starters": ["Instagram ad copy 3 variants", "Creative brief for landing hero", "Video storyboard for demo"]},
    {"id": "ops_manager", "name": "Jordan — Ops", "role": "Operations Manager", "tagline": "SOPs and workflows",
     "starters": ["SOP for weekly sales standup", "Lead handoff checklist"]},
]

_SEARCH_TOOLS = frozenset({"lead_scraper", "serp_search"})


def merged_harnesses(extra: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    out = list(OS2_HARNESSES)
    for h in extra or []:
        if isinstance(h, dict) and h.get("id"):
            out.append(h)
    return out


def _route_id(harness_id: str, extra: list[dict[str, Any]] | None = None) -> str:
    h = harness_by_id(harness_id, extra)
    return str(h.get("base_harness_id") or harness_id) if h else harness_id


def harness_by_id(harness_id: str, extra: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
    return next((r for r in merged_harnesses(extra) if r["id"] == harness_id), None)


def _topic_from_context(rc: dict[str, Any]) -> str:
    return str(rc.get("topic") or rc.get("idea") or "target market").strip()


def route_message_to_tools(harness_id: str, message: str, *, report_context: dict[str, Any] | None = None, extra_harnesses: list[dict[str, Any]] | None = None):
    msg = str(message or "").strip().lower()
    rc = report_context if isinstance(report_context, dict) else {}
    topic, geo = _topic_from_context(rc), str(rc.get("geography") or rc.get("country") or "Global")
    harness_id = _route_id(harness_id, extra_harnesses)
    if harness_id == "sales_lead":
        from iidatech.execution.outreach_pipeline import is_outreach_pipeline_intent, parse_lead_target
        if is_outreach_pipeline_intent(msg):
            target = parse_lead_target(msg, default=30)
            return (
                [
                    {"tool": "lead_scraper", "payload": {"target_count": target, "icp_segment": topic, "geography": geo}, "approved": True},
                    {"tool": "outreach_personalizer", "payload": {"max_leads": target}, "approved": True},
                ],
                f"Find ~{target} leads then personalize emails.",
            )
        # Lead-finding intent wins over outreach keywords: prompts like
        # "find 20 qualified leads ... with emails" must run the scraper, not the writer.
        lead_intent = "lead" in msg and any(
            k in msg for k in ("find", "scrape", "generate", "list", "export", "qualified", "csv", "search")
        )
        if lead_intent:
            target = int(m.group(1)) if (m := re.search(r"(\d+)\s*(?:qualified\s+)?lead", msg)) else 20
            return ([{"tool": "lead_scraper", "payload": {"target_count": max(5, min(90, target)), "icp_segment": topic, "geography": geo}, "approved": True}], f"Lead search (~{target}).")
        if any(k in msg for k in ("meeting", "book a call", "schedule a call", "demo call", "book a demo")):
            return ([{"tool": "meeting_scheduler", "payload": {"title": str(message or "Discovery call")[:240]}, "approved": True}], "Meeting scheduling.")
        if any(k in msg for k in ("outreach", "email", "sequence", "message", "cold")):
            steps = int(m.group(1)) if (m := re.search(r"(\d+)\s*step", msg)) else 3
            return ([{"tool": "outreach_writer", "payload": {"sequence_steps": max(1, min(7, steps))}, "approved": True}], "Outreach sequence.")
        if any(k in msg for k in ("score", "rank")):
            return ([{"tool": "lead_scoring", "payload": {}, "approved": True}], "Lead scoring.")
        if "proposal" in msg:
            return ([{"tool": "proposal_builder", "payload": {"client_name": "Prospect"}, "approved": True}], "Proposal draft.")
        target = int(m.group(1)) if (m := re.search(r"(\d+)\s*lead", msg)) else 20
        return ([{"tool": "lead_scraper", "payload": {"target_count": max(5, min(90, target)), "icp_segment": topic, "geography": geo}, "approved": True}], f"Lead search (~{target}).")
    if harness_id == "growth_marketer":
        if "campaign" in msg:
            ch = "linkedin" if "linkedin" in msg else "email"
            return (
                [
                    {"tool": "campaign_builder", "payload": {"channel": ch}, "approved": True},
                    {"tool": "ad_copy_generator", "payload": {"channel": ch, "variants": 3}, "approved": True},
                ],
                "Campaign plan + ad copy.",
            )
        ch = next((c for c in ("instagram", "google", "email", "twitter") if c in msg), "linkedin")
        if "outreach" in msg:
            return ([{"tool": "outreach_writer", "payload": {"sequence_steps": 3}, "approved": True}], "Outreach.")
        return ([{"tool": "ad_copy_generator", "payload": {"channel": ch, "variants": 3}, "approved": True}], f"Ad copy ({ch}).")
    if harness_id == "research_analyst":
        if any(k in msg for k in ("competitor", "pricing")):
            return ([{"tool": "competitor_lookup", "payload": {}, "approved": True}, {"tool": "serp_search", "payload": {"query": f"{topic} competitors {geo}", "max_results": 10}, "approved": True}], "Competitor pass.")
        if any(k in msg for k in ("gap", "evidence", "log")):
            gaps = list(rc.get("evidence_gaps") or [])[:8] or [f"Evidence for {topic}"]
            return ([{"tool": "evidence_writer", "payload": {"gaps": gaps}, "approved": True}], "Evidence log.")
        q = str(message or "").strip() or f"{topic} {geo}"
        return ([{"tool": "serp_search", "payload": {"query": q, "max_results": 12}, "approved": True}], "Live search.")
    if harness_id == "creative_producer":
        if any(k in msg for k in ("canva", "create design", "open in canva")) or (
            any(k in msg for k in ("visual", "creative", "design", "deck", "pitch", "social post", "banner"))
            and any(k in msg for k in ("create", "make", "build", "generate"))
        ):
            return ([{"tool": "canva_design", "payload": {"brief": message, "topic": topic}, "approved": True}], "Canva design.")
        if any(k in msg for k in ("storyboard", "video")):
            return ([{"tool": "creative_storyboard", "payload": {"brief": message, "topic": topic}, "approved": True}], "Storyboard.")
        if any(k in msg for k in ("brief", "landing", "visual", "design")):
            return ([{"tool": "creative_brief", "payload": {"brief": message, "topic": topic}, "approved": True}], "Creative brief.")
        ch = "instagram" if "instagram" in msg else "linkedin"
        return ([{"tool": "ad_copy_generator", "payload": {"channel": ch, "variants": 3}, "approved": True}], "Creative copy.")
    if harness_id == "ops_manager":
        if any(k in msg for k in ("workflow", "automation", "pipeline", "process map")):
            return ([{"tool": "workflow_builder", "payload": {"workflow_name": str(message or "workflow")[:120]}, "approved": True}], "Workflow build.")
        if any(k in msg for k in ("task", "todo", "remind")):
            return ([{"tool": "task_scheduler", "payload": {"tasks": [str(message or "Task")[:240]]}, "approved": True}], "Task scheduling.")
        return ([{"tool": "sop_writer", "payload": {"title": "SOP", "topic": topic}, "approved": True}], "SOP draft.")
    return ([], "Ask for leads, outreach, campaign, brief, or SOP.")


def _artifact_dir(report_id: str, harness_id: str) -> Path:
    p = _ARTIFACT_ROOT / str(report_id) / str(harness_id)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _tool_creative_brief(payload: dict, context: dict) -> dict[str, Any]:
    from iidatech.execution.tool_outcomes import execution_result
    from iidatech.integrations.files import write_document
    rid = str(payload.get("report_id") or context.get("report_id") or "os2")
    out = _artifact_dir(rid, str(context.get("harness_id") or "creative"))
    doc = write_document(out, filename=f"creative_brief_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md", title="Creative brief", sections=["Objective", str(payload.get("brief") or "")[:500], "Visuals", "Deliverables"])
    return execution_result(success=True, result={"creative_brief_path": doc["path"]}, artifacts=[doc["path"]], execution_mode="real", verified=False)


def _tool_creative_storyboard(payload: dict, context: dict) -> dict[str, Any]:
    from iidatech.execution.tool_outcomes import execution_result
    rid = str(payload.get("report_id") or context.get("report_id") or "os2")
    path = _artifact_dir(rid, str(context.get("harness_id") or "creative")) / f"storyboard_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(f"# Storyboard\n\n{payload.get('brief', '')}\n", encoding="utf-8")
    return execution_result(success=True, result={"storyboard_path": str(path)}, artifacts=[str(path)], execution_mode="real", verified=False)


def _tool_canva_design(payload: dict, context: dict) -> dict[str, Any]:
    from iidatech.execution.tool_outcomes import execution_result
    from iidatech.integrations.canva_client import create_design_from_message

    rid = str(payload.get("report_id") or context.get("report_id") or "os2")
    brief = str(payload.get("brief") or context.get("message") or "")
    topic = str(payload.get("topic") or "")
    ok, result = create_design_from_message(rid, brief, topic=topic)
    if not ok:
        return execution_result(success=False, result={"error": str(result)}, artifacts=[], execution_mode="real", verified=False)
    design = (result or {}).get("design") if isinstance(result, dict) else {}
    urls = design.get("urls") if isinstance(design, dict) else {}
    edit_url = str((urls or {}).get("edit_url") or "")
    view_url = str((urls or {}).get("view_url") or "")
    artifacts = [u for u in (edit_url, view_url) if u]
    return execution_result(
        success=True,
        result={"design_id": design.get("id"), "edit_url": edit_url, "view_url": view_url, "title": design.get("title")},
        artifacts=artifacts,
        execution_mode="real",
        verified=True,
    )


_EXTRA = {"creative_brief": _tool_creative_brief, "creative_storyboard": _tool_creative_storyboard, "canva_design": _tool_canva_design}


def _run_extra(employee_id: str, role: str, calls: list, context: dict) -> dict[str, Any]:
    from iidatech.execution.action_executor import execute_tool
    outputs, artifacts, ok = [], [], True
    for call in calls:
        tool = str(call.get("tool") or "")
        if tool in _EXTRA:
            pl = dict(call.get("payload") or {}); pl.setdefault("report_id", context.get("report_id"))
            out = _EXTRA[tool](pl, context)
        else:
            out = execute_tool(tool, call.get("payload") or {}, context=context, approved=True)
        outputs.append(out); ok = ok and bool(out.get("success"))
        artifacts.extend(str(a) for a in (out.get("artifacts") or []) if a)
    return {"success": ok, "result": {"outputs": outputs}, "artifacts": list(dict.fromkeys(artifacts))}


def _needs_perplexity(tool_calls: list[dict[str, Any]]) -> bool:
    return any(str(c.get("tool") or "") in _SEARCH_TOOLS for c in tool_calls)


def _enrich_artifacts(artifacts: list[str], message: str, report_context: dict[str, Any]) -> list[str]:
    try:
        from iidatech.execution.os2_llm import enrich_markdown_artifact
    except ImportError:
        return artifacts
    if not has_any_llm_key():
        return artifacts
    for path in artifacts:
        if str(path).lower().endswith((".md", ".txt")):
            enrich_markdown_artifact(path, user_request=message, report_context=report_context)
    return artifacts


def execute_harness_job(
    harness_id: str,
    message: str,
    *,
    report_id: str,
    api_keys: dict[str, str] | None = None,
    api_config: dict[str, str] | None = None,
    extra_harnesses: list[dict[str, Any]] | None = None,
    report_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    harness = harness_by_id(harness_id, extra_harnesses)
    keys = {k: v for k, v in (api_keys or {}).items() if str(v or "").strip()}
    if not harness:
        return {"success": False, "reply": "Unknown employee.", "artifacts": []}
    if not keys:
        return {
            "success": False,
            "reply": (
                "No API keys configured. Add OPENAI_API_KEY or PERPLEXITY_API_KEY on your server, "
                "or enter keys under Team → Integrations → API keys."
            ),
            "artifacts": [],
        }

    tool_calls, reasoning = route_message_to_tools(harness_id, message, report_context=report_context, extra_harnesses=extra_harnesses)
    if not tool_calls:
        return {"success": False, "reply": reasoning, "artifacts": []}

    if _needs_perplexity(tool_calls) and not keys.get("perplexity"):
        return {
            "success": False,
            "reply": (
                f"**{harness['name']}** — this task needs a **Perplexity** key for live search/leads. "
                f"You can still use OpenAI/Anthropic/DeepSeek keys for copy and documents — add a Perplexity key "
                f"under additional keys, or ask for outreach/creative/SOP work instead."
            ),
            "artifacts": [],
        }

    eid, role = f"os2_{harness_id}", str(harness["role"])
    try:
        from iidatech.execution.os2_team_bridge import employee_id_for_harness

        sql_eid = employee_id_for_harness(report_id, harness_id)
        if sql_eid:
            eid = sql_eid
    except Exception:
        pass
    ctx = {"report_id": report_id, "employee_id": eid, "harness_id": harness_id, "report_context": report_context or {}}
    reg = [c for c in tool_calls if str(c.get("tool")) not in _EXTRA]
    extra = [c for c in tool_calls if str(c.get("tool")) in _EXTRA]

    with session_api_keys(keys, config=api_config):
        execution: dict[str, Any] = {"success": True, "artifacts": [], "result": {"outputs": []}}
        if reg:
            execution = run_tool_calls(eid, role, reg, context=ctx)
        if extra:
            ex = _run_extra(eid, role, extra, ctx)
            execution["artifacts"] = list(dict.fromkeys((execution.get("artifacts") or []) + ex.get("artifacts", [])))
            execution["success"] = bool(execution.get("success")) and bool(ex.get("success"))

        arts = _enrich_artifacts(list(execution.get("artifacts") or []), message, report_context or {})

    prov_note = ", ".join(provider_label(p) for p in active_providers(keys)) or "session keys"
    reply = f"**{harness['name']}** — {reasoning}\n\n*Using: {prov_note}*\n\n"
    if execution.get("error"):
        reply += f"⚠️ {execution['error']}\n\n"
    preview = ""
    template_fallback = False
    for out in (execution.get("result") or {}).get("outputs") or []:
        if not isinstance(out, dict):
            continue
        res = out.get("result") if isinstance(out.get("result"), dict) else out
        if isinstance(res, dict) and "provider" in res and not res.get("provider"):
            template_fallback = True
        if isinstance(res, dict) and res.get("preview_markdown") and not preview:
            preview = str(res.get("preview_markdown") or "")
            count = res.get("leads_generated")
            if count:
                reply += f"**{count} live leads** (company, contact, website in CSV)\n\n{preview}\n\n"
    if template_fallback:
        reply += (
            "⚠️ **Heads up:** no AI provider responded, so this deliverable is a labeled template draft. "
            "Check your API keys and re-run for tailored output.\n\n"
        )
    if arts:
        reply += "\n\nYour deliverable is ready in the preview below. You can download it as PDF or Word."
    elif not preview:
        reply += "No deliverable was produced yet."
    return {"success": bool(execution.get("success")), "reply": reply, "artifacts": arts, "tool_calls": tool_calls, "execution": execution}