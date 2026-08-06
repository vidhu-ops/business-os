from __future__ import annotations

import re
from typing import Any


PAGE_TOURS: dict[str, dict[str, str]] = {
    "/app/dashboard": {
        "title": "Command deck",
        "blurb": "This is your home base — credits, projects, and what to do next.",
        "hook": "Pick a project or start a Company Audit. I will stay with you the whole way.",
    },
    "/app/projects": {
        "title": "Project vault",
        "blurb": "Every idea lives here as a workspace you can research, plan, and staff.",
        "hook": "Open one to continue, or create a fresh opportunity.",
    },
    "/app/audit": {
        "title": "Company Audit",
        "blurb": "We stress-test an existing company — gaps, risks, and where to push next.",
        "hook": "Answer honestly; IIDA turns that into a clear diagnosis.",
    },
    "/app/research": {
        "title": "Market Research",
        "blurb": "Evidence-backed market sizing, competitors, and demand signals.",
        "hook": "Run research on the active project — I will narrate what each section means.",
    },
    "/app/plan": {
        "title": "Business Plan",
        "blurb": "From research into an investor-ready plan with actions you can execute.",
        "hook": "Generate or refine the plan, then hand work to Employee OS.",
    },
    "/app/team": {
        "title": "Employee OS — your office",
        "blurb": "Taylor leads the floor. Hire departments, approve work, chat anyone from the Team bar.",
        "hook": "I am your personal aide here. Say the word and I will brief Taylor for you.",
    },
    "/app/automation": {
        "title": "Automation",
        "blurb": "Wire repeatable workflows so the office keeps moving without babysitting.",
        "hook": "Start with one high-leverage automation — I will keep score.",
    },
    "/app/profile": {
        "title": "Your profile",
        "blurb": "Plan, credits, and account details that shape what I recommend.",
        "hook": "Tell me your goal and I will tailor the tour.",
    },
    "/app/saved": {
        "title": "Saved files",
        "blurb": "Deliverables and exports from research, plans, and the office.",
        "hook": "Grab what you need — I can remind you what each file is for.",
    },
    "/app/partners": {
        "title": "Partners",
        "blurb": "Trusted partners who can help you ship faster.",
        "hook": "Browse when you are ready to bring humans into the loop.",
    },
}


def normalize_path(path: str) -> str:
    p = (path or "/app/dashboard").split("?")[0].rstrip("/") or "/app/dashboard"
    if not p.startswith("/"):
        p = "/" + p
    return p


def tour_for_path(path: str) -> dict[str, str]:
    p = normalize_path(path)
    if p in PAGE_TOURS:
        return PAGE_TOURS[p]
    for key, tour in PAGE_TOURS.items():
        if p.startswith(key):
            return tour
    return {
        "title": "IIDATECH workspace",
        "blurb": "You are inside the product. I read the screen and stay one tap away.",
        "hook": "Ask me what this page is for, or what to do next.",
    }


def _first_name(name: str, email: str) -> str:
    raw = (name or "").strip() or (email or "").split("@")[0]
    token = re.split(r"[\s._-]+", raw)[0] if raw else "founder"
    return token[:1].upper() + token[1:24]


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
    bits = [f"Hey {first} — you are on **{tour['title']}**.", tour["blurb"], tour["hook"]]
    if screen_summary:
        bits.append(f"On screen I notice: {screen_summary[:220]}")
    if plan_name:
        bits.append(f"Your plan: {plan_name}.")
    if credits_remaining is not None:
        bits.append(f"Credits left: {credits_remaining}.")
    if is_demo:
        bits.append("Demo mode is browse-first — sign up free when you want me to run real work.")
    if "/app/team" in normalize_path(path):
        bits.append("Tip: use the Team chips up top to chat anyone without scrolling. I can also ping Taylor.")
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
                {"id": "open_hiring", "label": "Open Hiring"},
                {"id": "open_approvals", "label": "Check approvals"},
            ]
        )
    elif p.startswith("/app/research"):
        actions.append({"id": "go_team", "label": "Go to Employee OS"})
    elif p.startswith("/app/plan"):
        actions.append({"id": "go_team", "label": "Staff the plan"})
    elif p.startswith("/app/dashboard") or p.startswith("/app/projects"):
        actions.append({"id": "go_audit", "label": "Start Company Audit"})
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

    if any(k in text for k in ("taylor", "team lead", "coo", "brief the lead", "brief taylor")):
        reply = (
            f"On it, {first}. I will open Employee OS with Taylor ready so you can approve, assign, "
            "or ask for a status brief. I stay here as your aide — Taylor runs the floor."
        )
        handoff = {"type": "taylor", "href": "/app/team?agent=taylor"}
    elif any(k in text for k in ("hire", "hiring", "build team", "department")):
        reply = (
            "Hiring lives under the **Hiring** tab — Build your team is a dropdown there so the Office "
            "floor stays clear. Want me to take you straight to Hiring?"
        )
        handoff = {"type": "navigate", "href": "/app/team?tab=hiring"}
    elif any(k in text for k in ("approv", "notification", "pending")):
        reply = "Approvals sit under **Tasks & Approvals**, and the bell in the office chrome jumps there too."
        handoff = {"type": "navigate", "href": "/app/team?tab=tasks"}
    elif any(k in text for k in ("what is this", "where am i", "explain", "tour", "screen")):
        reply = (
            f"You are on **{tour['title']}**. {tour['blurb']} {tour['hook']}"
            + (f" Screen cues: {screen_summary[:280]}" if screen_summary else "")
        )
    elif any(k in text for k in ("next", "what should", "stuck", "help", "do now")):
        reply = (
            f"Next move on **{tour['title']}**: {tour['hook']} "
            "If you want leverage, finish one action here then jump to Employee OS so Taylor can execute."
        )
    elif any(k in text for k in ("credit", "plan", "pricing", "upgrade")):
        plan_bit = f"You are on **{plan_name}**." if plan_name else "Open Profile to see your plan."
        credit_bit = f" About **{credits_remaining}** credits remain." if credits_remaining is not None else ""
        reply = f"{plan_bit}{credit_bit} I will steer you toward high-value steps so nothing is wasted."
    elif any(k in text for k in ("research", "market")):
        reply = "Market Research turns your idea into cited evidence. Run it on the active project, then I will walk the report with you."
        handoff = {"type": "navigate", "href": "/app/research"}
    elif any(k in text for k in ("plan", "business plan")):
        reply = "The Business Plan tab turns research into something you can pitch and staff. After it is ready, we hire in Employee OS."
        handoff = {"type": "navigate", "href": "/app/plan"}
    else:
        reply = (
            f"Got it, {first}. {tour['blurb']} Ask me to explain the screen, pick the next step, "
            "or brief Taylor — I am your always-on office guide."
        )

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
        "Voice: warm, catchy, concise (2-5 short sentences). Never invent financial numbers. "
        "You can see which page they are on and a short screen summary. "
        "Offer one clear next step. If they want the team lead, say you will hand off to Taylor."
    )
    prompt = (
        f"User: {_first_name(user_name, email)} ({email})\n"
        f"Plan: {plan_name or 'unknown'}; credits: {credits_remaining}\n"
        f"Path: {normalize_path(path)}\n"
        f"Page: {tip['tour']['title']} — {tip['tour']['blurb']}\n"
        f"Screen: {screen_summary or 'n/a'}\n"
        f"Demo: {is_demo}\n"
        f"Message: {message}\n"
        "Reply as IIDA only."
    )
    try:
        text, _provider = llm_text_request(prompt, system, max_tokens=400, temperature=0.4)
    except Exception:
        return None
    text = (text or "").strip()
    if not text:
        return None
    handoff = None
    low = message.lower()
    if any(k in low for k in ("taylor", "team lead", "coo")):
        handoff = {"type": "taylor", "href": "/app/team?agent=taylor"}
    return {
        "assistant": "IIDA",
        "role": "personal_guide",
        "reply": text[:1200],
        "tour": tip["tour"],
        "actions": tip["actions"],
        "handoff": handoff,
        "mode": "llm",
    }
