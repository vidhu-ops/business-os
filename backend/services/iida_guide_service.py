from __future__ import annotations

import re
from typing import Any


PAGE_TOURS: dict[str, dict[str, str]] = {
    "/": {
        "title": "IIDATECH home",
        "blurb": "Research, plan, and run a company from one Business OS — not five disconnected tools.",
        "hook": "Start with the free company audit if you already operate; otherwise scroll and I brief each block with a concrete next move.",
    },
    "/pricing": {
        "title": "Pricing",
        "blurb": "Self-serve tiers, packages, and credit packs — runway for how hard you want the office to work.",
        "hook": "Solo and validating? Free or Starter. Running research + plan + employees weekly? Growth.",
    },
    "/how-it-works": {
        "title": "How it works",
        "blurb": "Six click-steps from project to research to plan to Employee OS.",
        "hook": "Pick the step you have not finished today; one click unlocks the next deliverable.",
    },
    "/login": {
        "title": "Sign in",
        "blurb": "Workspace gate — register, log in, or tour the demo office without a card.",
        "hook": "Continue with demo for a fast office tour; create an account to keep audits and plans.",
    },
    "/checkout": {
        "title": "Checkout",
        "blurb": "Activating a paid plan so credits and the AI office can run for real.",
        "hook": "After payment, spend first credits on one high-value run — audit or scoped research.",
    },
    "/partners": {
        "title": "Partners",
        "blurb": "Service providers discovered when founders need human help beside IIDA.",
        "hook": "Applicants: lead with niche + proof. Founders: browse after an audit names a clear gap.",
    },
    "/app/dashboard": {
        "title": "Command deck",
        "blurb": "Account home — plan, credits, projects, and the shortest path to the next deliverable.",
        "hook": "If a free audit remains, run it first. If research already exists, open Plan or Employee OS — do not start another unfinished workspace.",
    },
    "/app/projects": {
        "title": "Project vault",
        "blurb": "Each idea becomes a workspace that owns research, plan, and the office roster.",
        "hook": "Open the project you will finish this week. Empty shells burn focus and credits later.",
    },
    "/app/audit": {
        "title": "Company Audit (GAUGE)",
        "blurb": "Four honest steps that score an existing business and surface priority gaps.",
        "hook": "Answer what is true today. Weak checklist answers produce sharper priorities than polished guesses.",
    },
    "/app/research": {
        "title": "Market Research",
        "blurb": "Project-scoped market sizing, competitors, and demand — cited so you can defend the story.",
        "hook": "Lock topic, industry, and country before you generate. Vague scope burns credits.",
    },
    "/app/plan": {
        "title": "Business Plan",
        "blurb": "Turns research or a GAUGE audit into a readable plan you can pitch and staff.",
        "hook": "New company from research; existing company via GAUGE forward. Generate once, then staff in Employee OS.",
    },
    "/app/team": {
        "title": "Employee OS",
        "blurb": "Live office floor — Taylor leads research, plan staffing, tasks, and automation; you approve outbound work.",
        "hook": "Ask me to brief Taylor — she can build checklists, run next, approve, retry, run office day, or kick competitor/lead work.",
    },
    "/app/automation": {
        "title": "Automation",
        "blurb": "Multi-step agent workflows that keep shipping after you leave the tab.",
        "hook": "Wire one high-leverage flow after Integrations are connected — empty queues usually mean missing keys.",
    },
    "/app/profile": {
        "title": "Profile",
        "blurb": "Identity and sign-out — thin settings, big effect on what I recommend.",
        "hook": "Tell me validate, raise, or operate and I will route you instead of wandering settings.",
    },
    "/app/saved": {
        "title": "Saved files",
        "blurb": "Exports and deliverables from research, plans, and office runs.",
        "hook": "Open the newest report or plan first — browsing files is not progress.",
    },
}


def normalize_path(path: str) -> str:
    raw = (path or "/").split("?")[0] or "/"
    if raw == "/":
        return "/"
    p = raw.rstrip("/") or "/"
    if not p.startswith("/"):
        p = "/" + p
    return p


def tour_for_path(path: str) -> dict[str, str]:
    p = normalize_path(path)
    if p in PAGE_TOURS:
        return PAGE_TOURS[p]
    for key in sorted(PAGE_TOURS.keys(), key=len, reverse=True):
        if key != "/" and (p == key or p.startswith(key + "/")):
            return PAGE_TOURS[key]
    return {
        "title": "IIDATECH workspace",
        "blurb": "You are inside the product. I read the screen and stay one tap away.",
        "hook": "Ask what this page is for, or what one action unlocks the next deliverable.",
    }


def _first_name(name: str, email: str) -> str:
    raw = (name or "").strip() or (email or "").split("@")[0]
    token = re.split(r"[\s._-]+", raw)[0] if raw else "founder"
    return token[:1].upper() + token[1:24]


def _screen_insight(screen_summary: str | None, path: str) -> str:
    """Turn DOM headings into a short, page-relevant cue — not a raw dump."""
    s = (screen_summary or "").strip()
    if not s:
        return ""
    p = normalize_path(path)
    low = s.lower()
    cues: list[tuple[str, str, str]] = [
        ("/app/team", "hiring", "You are near Hiring — staff lean before Full company."),
        ("/app/team", "approval", "Approvals are open — review outbound before Approve all."),
        ("/app/team", "war room", "War Room is for blockers; skip it if one Approve unblocks the queue."),
        ("/app/team", "command center", "Command Center readiness — fix Hiring and Integrations before a full cycle."),
        ("/app/team", "integration", "Integrations decide whether agents can actually send."),
        ("/app/team", "office", "Live floor — set one priority, then let Taylor run."),
        ("/app/audit", "step", "Stay honest on the current GAUGE step; gaps become your focus list."),
        ("/app/audit", "priority", "Read Priority actions before building a forward plan."),
        ("/app/research", "report", "Report is ready to read — extract competitors and demand, then Plan."),
        ("/app/research", "understand", "Tighten topic + industry + country before generating."),
        ("/app/plan", "gauge", "GAUGE forward should attack audit gaps, not restart from zero."),
        ("/app/plan", "readable", "Pull three actions Taylor can own this week from the plan."),
        ("/app/dashboard", "credit", "Credits are runway — spend on scoped research or audit, not tours."),
        ("/app/dashboard", "project", "Finish the hottest project before opening another."),
        ("/pricing", "starter", "Starter fits weekly research; Growth when the office runs as a habit."),
        ("/pricing", "credit", "One deep research run beats five shallow regenerations."),
        ("/", "audit", "Free audit is the highest-signal start if you already operate."),
        ("/", "problem", "Guesswork is the default — your edge is cited research plus execution."),
    ]
    for prefix, needle, tip in cues:
        if (p == prefix or p.startswith(prefix + "/") or (prefix == "/" and p == "/")) and needle in low:
            return tip
    # Keep a short on-screen cue without repeating the whole summary.
    head = s.split("·")[0].strip()[:90]
    return f'On screen: {head}.' if head else ""


def build_proactive_tip(
    *,
    path: str,
    user_name: str,
    email: str,
    plan_name: str | None,
    credits_remaining: int | None,
    screen_summary: str | None,
    is_demo: bool,
) -> dict[str, Any]:
    tour = tour_for_path(path)
    first = _first_name(user_name, email)
    bits = [f"Hey {first} — {tour['title']}.", tour["hook"]]
    screen_bit = _screen_insight(screen_summary, path)
    if screen_bit:
        bits.append(screen_bit)
    if plan_name and normalize_path(path).startswith("/app/"):
        bits.append(f"Plan: {plan_name}.")
    if credits_remaining is not None and normalize_path(path).startswith("/app/"):
        bits.append(f"Credits left: {credits_remaining}.")
    if is_demo:
        bits.append("Demo is browse-first — sign up free when you want real runs saved.")
    if "/app/team" in normalize_path(path):
        bits.append("Team chips chat anyone without scrolling; I can ping Taylor.")
    return {
        "assistant": "IIDA",
        "role": "personal_guide",
        "path": normalize_path(path),
        "tour": tour,
        "message": " ".join(bits),
        "actions": _actions_for_path(path),
    }


def _actions_for_path(path: str) -> list[dict[str, str]]:
    p = normalize_path(path)
    actions: list[dict[str, str]] = [
        {"id": "what_is_this", "label": "What is this page?"},
        {"id": "what_next", "label": "What should I do next?"},
    ]
    if p.startswith("/app/team"):
        actions.extend(
            [
                {"id": "brief_taylor", "label": "Brief Taylor"},
                {"id": "taylor_run_next", "label": "Taylor: run next"},
                {"id": "taylor_checklist", "label": "Taylor: build checklist"},
                {"id": "open_approvals", "label": "Check approvals"},
                {"id": "open_hiring", "label": "Open Hiring"},
            ]
        )
    elif p.startswith("/app/research"):
        actions.append({"id": "go_team", "label": "Go to Employee OS"})
    elif p.startswith("/app/plan"):
        actions.append({"id": "go_team", "label": "Staff the plan"})
    elif p.startswith("/app/dashboard") or p.startswith("/app/projects"):
        actions.append({"id": "go_audit", "label": "Start Company Audit"})
    elif p in ("/", "/pricing", "/how-it-works"):
        actions.append({"id": "go_demo", "label": "Try demo"})
    return actions


def heuristic_reply(
    *,
    message: str,
    path: str,
    user_name: str,
    email: str,
    plan_name: str | None,
    credits_remaining: int | None,
    screen_summary: str | None,
    is_demo: bool,
    project_id: str | None = None,
) -> dict[str, Any]:
    tip = build_proactive_tip(
        path=path,
        user_name=user_name,
        email=email,
        plan_name=plan_name,
        credits_remaining=credits_remaining,
        screen_summary=screen_summary,
        is_demo=is_demo,
    )
    text = (message or "").strip().lower()
    first = _first_name(user_name, email)
    tour = tip["tour"]
    reply = ""
    handoff = None
    screen_bit = _screen_insight(screen_summary, path)
    pid = (project_id or "").strip()
    team_href = "/app/team" + (f"?project={pid}" if pid else "")

    def _taylor(action: str | None = None, taylor_message: str | None = None, tab: str | None = None) -> dict[str, Any]:
        href = team_href
        if tab:
            href += ("&" if "?" in href else "?") + f"tab={tab}&agent=taylor"
        else:
            href += ("&" if "?" in href else "?") + "agent=taylor"
        out: dict[str, Any] = {"type": "taylor", "href": href}
        if action:
            out["action"] = action
        if taylor_message:
            out["taylor_message"] = taylor_message
        return out

    if any(k in text for k in ("run next", "next task", "keep going", "run the next")):
        reply = f"Got it, {first}. I am telling Taylor to run the next task and opening the office so you can watch."
        handoff = _taylor("run_next", "run next task")
    elif any(k in text for k in ("approve all", "approve pending")) or (
        "approve" in text and any(k in text for k in ("taylor", "task", "all"))
    ):
        reply = f"I will have Taylor approve pending items, {first}. Review outbound before anything sends."
        handoff = _taylor("approve_all", "approve all", tab="tasks")
    elif any(k in text for k in ("retry failed", "retry the", "retry task")):
        reply = "Briefing Taylor to retry failed tasks and keep the floor moving."
        handoff = _taylor("retry_failed", "retry failed")
    elif any(k in text for k in ("build checklist", "staff the plan", "create checklist")):
        reply = "I am asking Taylor to build the task checklist from your plan."
        handoff = _taylor("build_checklist", "build checklist from the plan")
    elif any(k in text for k in ("office day", "run the office", "full day")):
        reply = "Taylor will run an office day — I am opening Employee OS so you can see the floor."
        handoff = _taylor("full_day", "run office day")
    elif any(k in text for k in ("find leads", "daily outreach", "email them", "leads and email")):
        reply = "I will brief Taylor to find leads and queue personalized email — you still approve sends."
        handoff = _taylor(None, "find leads and email them")
    elif any(k in text for k in ("competitor", "pricing pass", "ask sam")):
        reply = "I am asking Taylor to put Sam on a competitor and pricing pass."
        handoff = _taylor(None, "run competitor and pricing evidence pass")
    elif any(k in text for k in ("taylor", "team lead", "coo", "brief the lead", "brief taylor")):
        reply = (
            f"On it, {first}. Opening Employee OS with Taylor ready — I already brief her with your ask. "
            "She can build checklists, run next, approve, retry, and kick research or outreach."
        )
        handoff = _taylor(None, message.strip()[:400] or "status brief")
    elif any(k in text for k in ("play", "game", "unstick", "bored")):
        reply = (
            f"Yes, {first} — let's play a 20-second decision game. Use the Let's play chip — friend first, then we ship."
        )
    elif any(k in text for k in ("hire", "hiring", "build team", "department")):
        reply = (
            "Hiring lives under the Hiring tab — staff Lean before Full company until Integrations "
            "and approval habits exist. Opening Hiring for you."
        )
        handoff = {"type": "navigate", "href": f"{team_href}{'&' if '?' in team_href else '?'}tab=hiring"}
    elif any(k in text for k in ("integration", "api key", "perplexity key")):
        reply = "Opening Integrations — Perplexity for research/leads, LLM for copy, OAuth for outbound."
        handoff = {"type": "navigate", "href": f"{team_href}{'&' if '?' in team_href else '?'}tab=integrations"}
    elif any(k in text for k in ("approv", "notification", "pending")):
        reply = (
            "Tasks and Approvals is your control gate for email, LinkedIn, and CRM. "
            "Review before Approve all — that keeps the office safe."
        )
        handoff = {"type": "navigate", "href": f"{team_href}{'&' if '?' in team_href else '?'}tab=tasks"}
    elif any(k in text for k in ("automation", "workflow queue")):
        reply = "Automation composes multi-step agent flows. I will take you there — wire one flow, then let Taylor drain the queue."
        href = "/app/automation" + (f"?project={pid}" if pid else "")
        handoff = {"type": "navigate", "href": href}
    elif any(k in text for k in ("what is this", "where am i", "explain", "tour", "screen")):
        reply = f"You are on **{tour['title']}**. {tour['blurb']} {tour['hook']}"
        if screen_bit:
            reply += f" {screen_bit}"
    elif any(k in text for k in ("next", "what should", "stuck", "help", "do now")):
        reply = f"Next on **{tour['title']}**: {tour['hook']}"
        if screen_bit:
            reply += f" {screen_bit}"
        if normalize_path(path).startswith("/app/team"):
            reply += " I can tell Taylor to **run next** or **build checklist** if you want me to act."
            tip["actions"] = list(tip["actions"]) + [
                {"id": "taylor_run_next", "label": "Tell Taylor: run next"},
                {"id": "brief_taylor", "label": "Brief Taylor"},
            ]
    elif any(k in text for k in ("credit", "pricing", "upgrade")) and "plan" not in text:
        plan_bit = f"You are on **{plan_name}**." if plan_name else "Open Profile to see your plan."
        credit_bit = f" About **{credits_remaining}** credits remain." if credits_remaining is not None else ""
        reply = f"{plan_bit}{credit_bit} Protect credits for scoped research and plans — one deep run beats five regenerations."
    elif any(k in text for k in ("research", "market")):
        reply = (
            "Market Research turns a tight scope into cited evidence. "
            "Lock topic, industry, and country, generate once, then move to Plan — or ask Taylor to run a competitor pass."
        )
        handoff = {"type": "navigate", "href": "/app/research" + (f"?project={pid}" if pid else "")}
    elif any(k in text for k in ("audit", "gauge")):
        reply = (
            "Company Audit (GAUGE) scores an existing business in four honest steps. "
            "Answer what is true today, then attack Priority actions in a forward plan."
        )
        handoff = {"type": "navigate", "href": "/app/audit"}
    elif any(k in text for k in ("business plan",)) or text.strip() in ("plan", "the plan"):
        reply = (
            "Business Plan packages research or a GAUGE audit into something you can pitch and staff. "
            "After it is readable, hand owners to Employee OS — I can ask Taylor to build the checklist."
        )
        handoff = {"type": "navigate", "href": "/app/plan" + (f"?project={pid}" if pid else "")}
    else:
        reply = f"Got it, {first}. {tour['hook']}"
        if screen_bit:
            reply += f" {screen_bit}"

    return {
        "assistant": "IIDA",
        "role": "personal_guide",
        "reply": reply,
        "tour": tour,
        "actions": tip["actions"],
        "handoff": handoff,
        "mode": "heuristic",
    }


def try_llm_reply(
    *,
    message: str,
    path: str,
    user_name: str,
    email: str,
    plan_name: str | None,
    credits_remaining: int | None,
    screen_summary: str | None,
    is_demo: bool,
    project_id: str | None = None,
) -> dict[str, Any] | None:
    try:
        from iidatech.llm.text_request import cloud_llm_configured, llm_text_request
    except Exception:
        return None
    if not cloud_llm_configured():
        return None
    tip = build_proactive_tip(
        path=path,
        user_name=user_name,
        email=email,
        plan_name=plan_name,
        credits_remaining=credits_remaining,
        screen_summary=screen_summary,
        is_demo=is_demo,
    )
    system = (
        "You are IIDA, the user's personal assistant and tour guide inside the IIDATECH founder product. "
        "Voice: warm friend + sharp business partner, concise (2-5 short sentences). Never invent financial numbers. "
        "Every reply must be relevant to the current page and give one personal insight or next move — "
        "do not repeat generic marketing fluff. You can hand work to Taylor (Employee OS COO) who runs checklists, "
        "next tasks, approvals, office day, research, and outreach — say when you are doing that. "
        "When the screen summary includes vibe:stuck or stuckSignals, gently offer a 20-second decision game. "
        "Use the session trail to sound continuous, not amnesiac."
    )
    prompt = (
        f"User: {_first_name(user_name, email)} ({email})\n"
        f"Plan: {plan_name or 'unknown'}; credits: {credits_remaining}\n"
        f"Path: {normalize_path(path)}\n"
        f"Page: {tip['tour']['title']} — {tip['tour']['blurb']}\n"
        f"Hook: {tip['tour']['hook']}\n"
        f"Screen: {screen_summary or 'n/a'}\n"
        f"Screen insight: {_screen_insight(screen_summary, path) or 'n/a'}\n"
        f"Demo: {is_demo}\n"
        f"Message: {message}\n"
        "Reply as IIDA only with a distinct, actionable insight for this page."
    )
    try:
        text, _provider = llm_text_request(prompt, system, max_tokens=400, temperature=0.4)
    except Exception:
        return None
    text = (text or "").strip()
    if not text:
        return None
    # Prefer structured handoffs from the heuristic layer for actionable asks.
    structured = heuristic_reply(
        message=message,
        path=path,
        user_name=user_name,
        email=email,
        plan_name=plan_name,
        credits_remaining=credits_remaining,
        screen_summary=screen_summary,
        is_demo=is_demo,
        project_id=project_id,
    )
    handoff = structured.get("handoff")
    return {
        "assistant": "IIDA",
        "role": "personal_guide",
        "reply": text[:1200],
        "tour": tip["tour"],
        "actions": tip["actions"],
        "handoff": handoff,
        "mode": "llm",
    }
