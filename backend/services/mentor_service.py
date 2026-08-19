"""Industry mentor — guides founders using live project artifacts."""
from __future__ import annotations

import re
from typing import Any


def _first_name(name: str, email: str) -> str:
    raw = (name or "").strip() or (email or "").split("@")[0]
    token = re.split(r"[\s._-]+", raw)[0] if raw else "founder"
    return token[:1].upper() + token[1:24]


def _clip(text: str, n: int = 900) -> str:
    s = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(s) <= n:
        return s
    return s[: n - 1].rstrip() + "…"


def build_project_brief(workspace: dict[str, Any] | None) -> dict[str, Any]:
    """Summarize research, plan, GAUGE, Employee OS, and automation for the mentor."""
    ws = workspace if isinstance(workspace, dict) else {}
    idea = str(ws.get("idea") or "").strip() or "your venture"
    industry = str(ws.get("industry") or "General").strip() or "General"
    country = str(ws.get("country") or "Global").strip() or "Global"
    areas = str(ws.get("areas") or "").strip()

    research = ws.get("research_report") if isinstance(ws.get("research_report"), dict) else {}
    plan = ws.get("business_plan") if isinstance(ws.get("business_plan"), dict) else {}
    audit = ws.get("gauge_audit") if isinstance(ws.get("gauge_audit"), dict) else {}
    if not audit:
        audit = ws.get("company_audit") if isinstance(ws.get("company_audit"), dict) else {}
    if not audit:
        audit = ws.get("gauge") if isinstance(ws.get("gauge"), dict) else {}
    os2 = ws.get("employee_os") if isinstance(ws.get("employee_os"), dict) else {}
    auto = ws.get("automation") if isinstance(ws.get("automation"), dict) else {}

    org_profile = {}
    org_completeness = {"pct": 0, "missing": []}
    execution_loop = {}
    org_memory_prompt = ""
    try:
        from backend.services import org_memory as om
        org_profile = om.effective_business_profile(ws)
        org_completeness = om.profile_completeness(org_profile)
        execution_loop = om.execution_loop_snapshot(ws, str(ws.get("owner_email") or ""))
        org_memory_prompt = om.profile_prompt_block(org_profile)
    except Exception:
        pass

    research_ready = bool(research.get("available") or research.get("success") or research.get("report_markdown"))
    plan_ready = bool(plan.get("available") or plan.get("plan_json") or plan.get("markdown"))
    audit_ready = bool(audit.get("available") or audit.get("score") is not None or audit.get("result"))

    research_excerpt = _clip(
        str(research.get("report_markdown") or research.get("markdown") or research.get("summary") or ""),
        1200,
    )
    plan_excerpt = ""
    plan_json = plan.get("plan_json") if isinstance(plan.get("plan_json"), dict) else {}
    if plan_json:
        bits = [
            str(plan_json.get("executive_summary") or plan_json.get("summary") or ""),
            str(plan_json.get("go_to_market") or plan_json.get("gtm") or ""),
        ]
        plan_excerpt = _clip(" ".join(b for b in bits if b), 900)
    elif plan.get("markdown"):
        plan_excerpt = _clip(str(plan.get("markdown")), 900)

    audit_score = audit.get("overall_score") or audit.get("score") or (audit.get("result") or {}).get("score")
    audit_priorities = audit.get("priorities") or (audit.get("result") or {}).get("priorities") or []
    if isinstance(audit_priorities, list):
        audit_priorities = [str(p) for p in audit_priorities[:5]]
    else:
        audit_priorities = []

    checklist_status = "not started"
    try:
        from backend.services.workspace_context import workspace_report_id
        from iidatech.execution.os2_workflow import load_checklist

        rid = workspace_report_id(ws)
        cl = load_checklist(rid)
        if cl and isinstance(cl.get("items"), list):
            items = cl["items"]
            done = sum(1 for i in items if str(i.get("status")) in {"done", "completed"})
            pending = sum(1 for i in items if str(i.get("status")) in {"pending", "approved", "queued"})
            failed = sum(1 for i in items if str(i.get("status")) == "failed")
            awaiting = sum(1 for i in items if str(i.get("status")) in {"awaiting_approval", "needs_approval"})
            checklist_status = f"{done}/{len(items)} done; {pending} pending; {awaiting} awaiting approval; {failed} failed"
    except Exception:
        pass

    auto_status = "not built"
    if auto.get("available") or auto.get("active_spec"):
        last = auto.get("last_run") if isinstance(auto.get("last_run"), dict) else {}
        auto_status = str(last.get("status") or last.get("reply") or "built — ready to run")[:200]
        log = auto.get("log") if isinstance(auto.get("log"), list) else []
        if log and isinstance(log[0], dict):
            auto_status = str(log[0].get("reply") or log[0].get("status") or auto_status)[:200]

    next_move = "Create or open a project with a clear idea, industry, and market."
    if org_completeness.get("pct", 0) < 40:
        next_move = "Finish organizational memory — answer What you sell, Who buys, Goals, then connect Gmail/CRM/Drive."
    elif not idea or idea == "your venture":
        next_move = "Start on Projects — lock idea, industry, and country so I can mentor in-market."
    elif not research_ready and not audit_ready:
        next_move = "Run Market Research (or a GAUGE company audit if you already operate) before staffing the office."
    elif research_ready and not plan_ready:
        next_move = "Generate a Business Plan from your research so Employee OS has a real checklist to execute."
    elif plan_ready and "not started" in checklist_status:
        next_move = "Open Employee OS and ask Taylor to build the checklist, then Run next task."
    elif "awaiting" in checklist_status:
        next_move = "Approve external tasks in Employee OS (or ask Taylor to approve), then Run next."
    elif auto.get("available") and "not built" not in auto_status:
        next_move = "On Automation, Run next step — leads/research first; hold send/post until Gmail/LinkedIn are connected."
    elif plan_ready:
        next_move = "Keep draining Employee OS tasks, then wire a daily Automation for leads + outreach drafts."

    return {
        "idea": idea,
        "industry": industry,
        "country": country,
        "areas": areas,
        "market_label": f"{country}" + (f" · {areas}" if areas else ""),
        "research_ready": research_ready,
        "plan_ready": plan_ready,
        "audit_ready": audit_ready,
        "research_excerpt": research_excerpt,
        "plan_excerpt": plan_excerpt,
        "audit_score": audit_score,
        "audit_priorities": audit_priorities,
        "employee_os_available": bool(os2.get("available") or os2),
        "checklist_status": checklist_status,
        "automation_status": auto_status,
        "next_move": next_move,
        "org_profile": org_profile,
        "org_completeness": org_completeness,
        "execution_loop": execution_loop,
        "org_memory_prompt": org_memory_prompt,
    }


def opening_message(*, user_name: str, email: str, brief: dict[str, Any]) -> str:
    first = _first_name(user_name, email)
    industry = brief.get("industry") or "your industry"
    market = brief.get("market_label") or brief.get("country") or "your market"
    idea = brief.get("idea") or "your venture"
    return (
        f"Hi {first} — I'm your Mentor for **{industry}** in **{market}**. "
        f"I already see the project around *{idea}*. "
        f"Right now I'd push you to: {brief.get('next_move')} "
        "Tell me what you're trying to finish this week and I'll sequence the exact clicks."
    )


def _heuristic_reply(message: str, brief: dict[str, Any], *, first: str) -> str:
    msg = (message or "").strip().lower()
    industry = brief.get("industry") or "this industry"
    market = brief.get("market_label") or brief.get("country") or "this market"
    next_move = brief.get("next_move") or "Open your project and pick one deliverable."

    if any(k in msg for k in ("what should i do", "next", "stuck", "help", "where do i start", "guide me")):
        return (
            f"{first}, in {industry} ({market}) the shortest path is: {next_move} "
            "Reply with validate / raise / operate and I'll narrow the sequence."
        )
    if any(k in msg for k in ("research", "tam", "market", "competitor")):
        if brief.get("research_ready"):
            excerpt = brief.get("research_excerpt") or "Your research is ready."
            return (
                f"Research is already on file for {market}. Snapshot: {_clip(excerpt, 420)} "
                "Use that as the source of truth — don't regenerate unless scope changed. "
                f"Next: {next_move}"
            )
        return (
            f"You don't have research yet. For {industry} in {market}, lock topic + geography on Research, "
            "then generate once. Vague scope burns credits and gives weak competitor lists."
        )
    if any(k in msg for k in ("plan", "pitch", "gtm", "business plan")):
        if brief.get("plan_ready"):
            return (
                f"Business plan is ready. {_clip(brief.get('plan_excerpt') or '', 360)} "
                "Staff it in Employee OS so Taylor turns sections into tasks. "
                f"Suggested next: {next_move}"
            )
        return "Generate the Business Plan from research (or GAUGE forward). Without a plan, agents invent busywork."
    if any(k in msg for k in ("gauge", "audit", "score")):
        if brief.get("audit_ready"):
            score = brief.get("audit_score")
            pri = ", ".join(brief.get("audit_priorities") or []) or "priority gaps on file"
            return (
                f"GAUGE is in. Score: {score if score is not None else 'recorded'}. Focus: {pri}. "
                "Forward into Plan, then hire the office against those gaps — not generic SaaS playbooks."
            )
        return "Run the free Company Audit if you already operate. Answer what's true today; polished guesses produce soft priorities."
    if any(k in msg for k in ("employee", "taylor", "office", "agent", "team", "checklist")):
        return (
            f"Employee OS status: {brief.get('checklist_status')}. "
            "Ask Taylor to build checklist → Run next. Approve outbound (email/LinkedIn) before send. "
            "Agents need server Perplexity/LLM keys (or keys under Integrations) to produce real files."
        )
    if any(k in msg for k in ("automat", "lead", "outreach", "email", "workflow")):
        return (
            f"Automation status: {brief.get('automation_status')}. "
            "Build a flow with find leads + draft outreach first; leave send/post until Gmail/LinkedIn are connected. "
            "Run next step one at a time and check Saved Files for CSVs."
        )
    if any(k in msg for k in ("credit", "pricing", "cost")):
        return (
            "Spend credits on one high-value run at a time: research OR plan OR a short Employee OS burst. "
            "Don't burn automation runs on send steps that still need OAuth."
        )
    return (
        f"Got it. As your {industry} mentor for {market}: {next_move} "
        "Ask me about research, plan, GAUGE, Employee OS, or automation and I'll answer from what's already on this project."
    )


def mentor_reply(
    *,
    message: str,
    user_name: str,
    email: str,
    brief: dict[str, Any],
    history: list[dict[str, str]] | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    first = _first_name(user_name, email)
    industry = brief.get("industry") or "General"
    market = brief.get("market_label") or brief.get("country") or "Global"
    msg_l = (message or "").strip().lower()

    # Mentor can hand work to Taylor when the founder asks to execute.
    handoff = None
    taylor_actions = {
        "build checklist": "build_checklist",
        "run next": "run_next",
        "approve all": "approve_all",
        "retry failed": "retry_failed",
        "office day": "full_day",
    }
    acted = None
    if workspace_id and any(k in msg_l for k in ("taylor", "run next", "build checklist", "approve all", "execute", "staff the plan", "office day")):
        try:
            from backend.services.os2_service import run_agent_chat, run_taylor_action, run_office_action

            if "office day" in msg_l or "full day" in msg_l:
                run_office_action(workspace_id, "full_day", goals=[], auto_approve=False, billing_email=email)
                acted = "full_day"
            elif "approve" in msg_l:
                run_taylor_action(workspace_id, "approve_all", billing_email=email)
                acted = "approve_all"
            elif "retry" in msg_l:
                run_taylor_action(workspace_id, "retry_failed", billing_email=email)
                acted = "retry_failed"
            elif "checklist" in msg_l or "staff" in msg_l:
                # Prefer natural language so Taylor builds from plan
                out = run_agent_chat(workspace_id, "taylor", "Build checklist from the plan", billing_email=email)
                acted = "build_checklist"
                handoff = {"type": "taylor", "result": out}
            elif "run next" in msg_l or "execute" in msg_l or "keep going" in msg_l:
                out = run_taylor_action(workspace_id, "run_next", billing_email=email)
                acted = "run_next"
                handoff = {"type": "taylor", "result": out}
                # Nudge goal progress when work ships
                try:
                    from backend.services import org_memory as om

                    org = om.load_account_org(email)
                    goals = list(org.get("goals") or [])
                    if goals:
                        g0 = goals[0]
                        pct = min(100, int(g0.get("progress_pct") or 0) + 5)
                        om.update_goal_progress(email, str(g0.get("id")), progress_pct=pct, current=f"Taylor advanced task ({pct}%)")
                except Exception:
                    pass
            if acted:
                try:
                    from backend.services import org_memory as om
                    from backend.services.workspaces import load_workspace, save_workspace

                    ws = load_workspace(workspace_id)
                    if ws:
                        ws = om.advance_execution_loop(ws, phase="execute", event=f"Mentor handed work to Taylor: {acted}")
                        save_workspace(ws)
                        brief = build_project_brief(ws)
                except Exception:
                    pass
        except Exception as exc:
            handoff = {"type": "taylor", "error": str(exc)[:240]}

    llm_text = None
    try:
        from iidatech.llm.text_request import cloud_llm_configured, llm_text_request

        if cloud_llm_configured():
            hist = ""
            for turn in (history or [])[-6:]:
                role = str(turn.get("role") or "user")
                hist += f"{role}: {turn.get('content') or ''}\n"
            system = (
                f"You are the IIDATECH Mentor — a seasoned {industry} operator and advisor for {market}. "
                "You know organizational memory (sell, buyers, competitors, pricing, team, revenue, goals, brand, processes) "
                "plus research, plan, GAUGE, Employee OS, and automation. "
                "Guide step-by-step: intake → GAUGE (if existing) → research → plan → Employee OS → measure goals → readjust with approval. "
                "When the founder wants execution, say you are briefing Taylor. Never invent TAM/SAM not in the brief. "
                "Voice: expert coach, concise (3-6 sentences)."
            )
            prompt = (
                f"Founder: {first} ({email})\n"
                f"Idea: {brief.get('idea')}\n"
                f"Industry: {industry}; Market: {market}\n"
                f"Org memory:\n{brief.get('org_memory_prompt') or 'n/a'}\n"
                f"Loop phase: {(brief.get('execution_loop') or {}).get('phase')}; "
                f"goal progress avg={(brief.get('execution_loop') or {}).get('goal_progress_avg')}\n"
                f"Research ready: {brief.get('research_ready')}; excerpt: {brief.get('research_excerpt') or 'n/a'}\n"
                f"Plan ready: {brief.get('plan_ready')}; excerpt: {brief.get('plan_excerpt') or 'n/a'}\n"
                f"Audit ready: {brief.get('audit_ready')}; score: {brief.get('audit_score')}\n"
                f"Employee OS: {brief.get('checklist_status')}\n"
                f"Automation: {brief.get('automation_status')}\n"
                f"Recommended next move: {brief.get('next_move')}\n"
                f"Taylor acted: {acted or 'none'}\n"
                f"Recent chat:\n{hist or '(none)'}\n"
                f"User message: {message}\n"
                "Reply as the Mentor only."
            )
            text, _ = llm_text_request(prompt, system, max_tokens=500, temperature=0.35)
            llm_text = (text or "").strip() or None
    except Exception:
        llm_text = None

    if acted and not llm_text:
        reply = (
            f"{first}, I briefed Taylor to **{acted.replace('_', ' ')}**. "
            f"Watch Employee OS for live work and approve anything external. Next: {brief.get('next_move')}"
        )
    else:
        reply = llm_text or _heuristic_reply(message, brief, first=first)

    actions = [
        {"id": "onboarding", "label": "Org memory", "href": "/app/onboarding"},
        {"id": "research", "label": "Open Research", "href": "/app/research"},
        {"id": "plan", "label": "Open Plan", "href": "/app/plan"},
        {"id": "team", "label": "Employee OS", "href": "/app/team"},
        {"id": "automation", "label": "Automation", "href": "/app/automation"},
    ]
    return {
        "assistant": "Mentor",
        "role": "industry_mentor",
        "industry": industry,
        "market": market,
        "reply": reply,
        "brief": brief,
        "actions": actions,
        "handoff": handoff,
        "acted": acted,
        "mode": "llm" if llm_text else ("taylor" if acted else "heuristic"),
    }
