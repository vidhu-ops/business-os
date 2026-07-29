"""Role-specialized employee brains — deterministic agents, not generic chatbots."""
from __future__ import annotations
from typing import Any

from iidatech.execution.employee_profiles import build_employee_profile, get_tool_access

_BRAIN_KEYS = ("action", "reasoning", "blockers", "sub_tasks", "messages", "confidence", "plan", "tool_calls", "expected_outputs")


def _brain(
    action: str,
    reasoning: str,
    *,
    blockers: list[str] | None = None,
    sub_tasks: list[str] | None = None,
    messages: list[dict[str, str]] | None = None,
    confidence: float = 0.7,
    plan: list[str] | None = None,
    tool_calls: list[dict[str, Any]] | None = None,
    expected_outputs: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "action": action,
        "reasoning": reasoning,
        "blockers": blockers or [],
        "sub_tasks": sub_tasks or [],
        "messages": messages or [],
        "confidence": max(0.0, min(1.0, float(confidence))),
        "plan": plan or [],
        "tool_calls": tool_calls or [],
        "expected_outputs": expected_outputs or [],
    }


def _report_v3(context: dict[str, Any]) -> dict[str, Any]:
    rc = context.get("report_context") or {}
    return rc if rc.get("schema_version") else rc.get("report_v3") or {}


def _memory_brief(context: dict[str, Any]) -> list[str]:
    return list(context.get("context_brief") or [])


def _brief_clause(context: dict[str, Any]) -> str:
    lines = _memory_brief(context)
    for msg in (context.get("inbox_messages") or [])[-4:]:
        if isinstance(msg, dict):
            text = str(msg.get("message") or "").strip()
            role = str(msg.get("from_role") or "teammate")
            if text:
                lines.append(f"{role} said: {text[:120]}")
    if not lines:
        return ""
    return " Prior context: " + "; ".join(lines[:6]) + "."


def _tasks(context: dict[str, Any]) -> list[dict[str, Any]]:
    return list(context.get("assigned_tasks") or context.get("current_tasks") or [])


def _truth_score(v3: dict[str, Any]) -> float:
    raw = v3.get("report_truth_confidence")
    if isinstance(raw, dict):
        raw = raw.get("score") or raw.get("value")
    if raw is None:
        rc = v3.get("report_confidence")
        raw = rc.get("score") if isinstance(rc, dict) else rc
    try:
        val = float(raw or 0)
    except (TypeError, ValueError):
        return 0.0
    return val / 100.0 if val > 1 else val


def run_research_agent(employee: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    profile = build_employee_profile(employee)
    v3 = _report_v3(context)
    tools = get_tool_access(profile["role"])
    truth = _truth_score(v3)
    gaps = list(v3.get("market_truth", {}).get("missing_evidence") or []) if isinstance(v3.get("market_truth"), dict) else []
    gaps += [m for m in (v3.get("data_provenance") or {}).get("gaps", []) if isinstance(m, str)][:3]
    if not gaps:
        comp = (v3.get("competitor_strength") or {}).get("competitor_count")
        if comp is None:
            gaps = ["Competitor pricing not corroborated across 2+ sources"]

    if truth and truth < 0.6:
        return _brain(
            "escalate_evidence_gap",
            f"Truth confidence {truth:.0%} below my 60% threshold — cannot recommend scale.{_brief_clause(context)}",
            blockers=["Insufficient corroborated evidence"],
            sub_tasks=[f"Run targeted search via {t}" for t in tools if t in ("serpapi", "exa", "tavily")][:2]
            + ["Cross-check claims against sql_memory prior reports"],
            messages=[{"to": "Founder", "text": f"Evidence gate failed ({truth:.0%}). Hold GTM spend until gap closed."}],
            confidence=0.82,
            plan=["Scan serp for corroboration", "Query team memory", "Log evidence gaps"],
            tool_calls=[
                {"tool": "serp_search", "payload": {"query": gaps[0] if gaps else "competitors", "max_results": 10}},
                {"tool": "sql_memory_query", "payload": {"limit": 15}},
                {"tool": "competitor_lookup", "payload": {}},
                {"tool": "evidence_writer", "payload": {"gaps": gaps[:5]}, "approved": True},
            ],
            expected_outputs=["competitors_found", "evidence_log_path", "result_count"],
        )

    sub = [f"Validate: {g}" for g in gaps[:3]] or ["Run 5 ICP interviews with structured script"]
    return _brain(
        "validate_claims",
        "Evidence-first pass: prioritize corroboration before any growth spend.",
        sub_tasks=sub,
        messages=[{"to": "Growth Marketer", "text": "Do not scale paid until I sign off on evidence ledger."}],
        confidence=0.78 if gaps else 0.88,
        plan=["Lookup competitors", "Verify pricing", "Write evidence ledger"],
        tool_calls=[
            {"tool": "competitor_lookup", "payload": {}},
            {"tool": "serp_search", "payload": {"query": "pricing", "max_results": 8}},
            {"tool": "evidence_writer", "payload": {"gaps": gaps[:5] or sub}, "approved": True},
        ],
        expected_outputs=["competitor_count", "pricing verified", "entries_written"],
    )


def run_growth_agent(employee: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    profile = build_employee_profile(employee)
    v3 = _report_v3(context)
    tools = get_tool_access(profile["role"])
    channel_econ: list[dict[str, Any]] = []
    if "gtm_engine" in tools:
        try:
            from iidatech.services.gtm_engine import build_gtm_channel_economics

            channel_econ = build_gtm_channel_economics(v3) if v3 else []
        except Exception:
            channel_econ = list((v3.get("go_to_market") or {}).get("channel_economics") or [])

    top = channel_econ[0] if channel_econ else {}
    channel = top.get("channel") or (v3.get("go_to_market") or {}).get("first_channel") or "primary channel"
    roi = float(top.get("roi_score") or 0)
    cac = top.get("expected_cac")

    open_tasks = _tasks(context)
    if any(t.get("status") == "blocked" for t in open_tasks):
        return _brain(
            "pause_experiment",
            "Blocked growth task — ROI test invalid until blocker cleared.",
            blockers=["Creative/assets or tracking not ready"],
            messages=[{"to": "COO", "text": "Unblock growth experiment before budget spend."}],
            confidence=0.75,
        )

    if roi < 2.0 and channel_econ:
        return _brain(
            "kill_channel",
            f"{channel} ROI score {roi:.1f} below 2.0 threshold — reallocate test budget.",
            sub_tasks=[f"Test #{i+2} channel: {c.get('channel')}" for i, c in enumerate(channel_econ[1:3])],
            confidence=0.8,
        )

    sub_tasks = [
        f"Launch 72h pilot on {channel}",
        f"Target CAC <= {cac}" if cac else "Set CAC guardrail from benchmark",
    ]
    if "campaign_generator" in tools:
        sub_tasks.append("Draft 2 ad variants + landing headline test")

    return _brain(
        "launch_experiment",
        f"Aggressive test on top ROI channel ({channel}); kill if CAC > 1.3x benchmark in week 1.{_brief_clause(context)}",
        sub_tasks=sub_tasks,
        messages=[{"to": "Sales Lead", "text": f"Expect inbound from {channel} pilot — prep discovery script."}],
        confidence=0.85 if roi >= 3 else 0.72,
        plan=[f"Scrape 50 leads for {channel}", "Build campaign", "Generate ad copy"],
        tool_calls=[
            {"tool": "lead_scraper", "payload": {"target_count": 50, "icp_segment": channel}},
            {"tool": "campaign_builder", "payload": {"channel": channel, "budget": 500}, "approved": True},
            {"tool": "ad_copy_generator", "payload": {"channel": channel, "variants": 2}},
            {"tool": "outreach_writer", "payload": {"sequence_steps": 3}},
        ],
        expected_outputs=["leads_generated", "qualified_leads", "csv_path", "campaign_path"],
    )


def run_sales_agent(employee: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    profile = build_employee_profile(employee)
    v3 = _report_v3(context)
    rc = context.get("report_context") if isinstance(context.get("report_context"), dict) else {}
    icps = list((v3.get("customer_truth") or {}).get("icps") or (v3.get("customer_truth") or {}).get("profiles") or [])
    if not icps:
        icps = v3.get("customer_truth", {}).get("icps") if isinstance(v3.get("customer_truth"), dict) else []
    if not icps:
        plan = rc.get("business_plan") if isinstance(rc.get("business_plan"), dict) else {}
        icp_pack = plan.get("validated_icp") if isinstance(plan.get("validated_icp"), dict) else {}
        profiles = icp_pack.get("named_buyer_profiles") if isinstance(icp_pack.get("named_buyer_profiles"), list) else []
        icps = [p for p in profiles if isinstance(p, dict)]
    if not icps and str(rc.get("topic") or v3.get("topic") or "").strip():
        topic = str(rc.get("topic") or v3.get("topic") or "").strip()
        icps = [{"named_buyer_profile": topic, "segment": topic, "source": "topic_context"}]
    icp_count = len(icps) if isinstance(icps, list) else 0

    cal = v3.get("execution_calendar") or {}
    w1 = cal.get("week_1") or {}
    discovery_goal = 10 if not w1.get("kpi") else 10

    pipeline_tasks = [t for t in _tasks(context) if "outreach" in str(t.get("title", "")).lower() or "pipeline" in str(t.get("title", "")).lower()]
    if icp_count < 1:
        return _brain(
            "request_icp",
            "No validated ICP in report — pipeline work is wasted motion.",
            blockers=["ICP not defined"],
            messages=[{"to": "Research Analyst", "text": "Need ICP evidence before outbound."}],
            confidence=0.9,
        )

    sub = [
        f"Build list of {discovery_goal} qualified prospects",
        "Send 3-touch outbound sequence",
        "Log objections in CRM",
    ]
    if not pipeline_tasks:
        sub.insert(0, "Create pipeline task: outbound to top ICP segment")

    for msg in (context.get("inbox_messages") or []):
        if not isinstance(msg, dict):
            continue
        text = str(msg.get("message") or "").lower()
        if "evidence" in text or "icp" in text or "research" in text:
            messages_out = [{"to": str(msg.get("from_role") or "Research Analyst"), "text": "Acknowledged — adjusting pipeline once ICP is confirmed."}]
            break
    else:
        messages_out = [{"to": "Founder", "text": f"Targeting {discovery_goal} conversations — need approval on outbound angle."}]

    return _brain(
        "build_pipeline",
        f"Pipeline focus: {icp_count} ICP segment(s); book discovery calls this week.",
        sub_tasks=sub,
        messages=messages_out,
        confidence=0.8,
        plan=["Score inbound leads", "Update CRM", "Schedule discovery calls"],
        tool_calls=[
            {"tool": "lead_scoring", "payload": {"threshold": 0.55}},
            {"tool": "crm_update", "payload": {}},
            {"tool": "meeting_scheduler", "payload": {"title": "Discovery call batch"}},
            {"tool": "proposal_builder", "payload": {"account_name": "Top ICP account"}, "approved": True},
        ],
        expected_outputs=["qualified_count", "records_updated", "proposal_path"],
    )


def run_ops_agent(employee: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    profile = build_employee_profile(employee)
    all_team_tasks = list(context.get("team_tasks") or _tasks(context))
    blocked = [t for t in all_team_tasks if t.get("status") == "blocked" or t.get("blockers")]
    unowned = [t for t in all_team_tasks if not t.get("owner_employee_id") and t.get("status") != "completed"]

    if blocked:
        b = blocked[0]
        blockers = list(b.get("blockers") or ["unspecified blocker"])
        return _brain(
            "unblock_task",
            f"Removing blocker on '{b.get('title')}' — ops priority #1.",
            blockers=blockers,
            sub_tasks=[f"Assign owner for: {b.get('title')}", f"Resolve: {blockers[0]}"],
            messages=[{"to": b.get("owner_employee_id") or "Founder", "text": f"Blocker on '{b.get('title')}': {blockers[0]}"}],
            confidence=0.86,
        )

    if unowned:
        t = unowned[0]
        return _brain(
            "assign_owner",
            f"Task '{t.get('title')}' has no owner — assigning via roster match.",
            sub_tasks=[f"Assign {t.get('title')} to best-fit role"],
            messages=[{"to": "Founder", "text": f"Unowned task needs decision: {t.get('title')}"}],
            confidence=0.8,
        )

    return _brain(
        "optimize_wip",
        "No blockers — tighten WIP and confirm weekly operating cadence.",
        sub_tasks=["Review task board", "Schedule weekly ops standup"],
        confidence=0.7,
        plan=["Document workflow", "Schedule tasks", "Write SOP"],
        tool_calls=[
            {"tool": "workflow_builder", "payload": {"workflow_name": "weekly_ops", "steps": ["standup", "blocker_sweep", "assign"]}},
            {"tool": "task_scheduler", "payload": {"tasks": ["Weekly ops standup", "Review task board"]}},
            {"tool": "sop_writer", "payload": {"sop_title": "Weekly operating cadence", "checklist": ["Review WIP", "Clear blockers"]}},
        ],
        expected_outputs=["workflow_path", "tasks_created", "sop_path"],
    )


def run_finance_agent(employee: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    profile = build_employee_profile(employee)
    v3 = _report_v3(context)
    ue = v3.get("unit_economics") or {}
    table = ue.get("table") if isinstance(ue, dict) else []
    ltv_cac = None
    if isinstance(table, list):
        for row in table:
            if isinstance(row, dict) and str(row.get("metric", "")).upper() in ("LTV:CAC", "LTV/CAC"):
                try:
                    ltv_cac = float(str(row.get("value", "")).replace("x", ""))
                except ValueError:
                    pass

    runway_months = None
    for pack in (v3.get("execution_plan") or {}).values():
        if isinstance(pack, dict) and "runway" in str(pack.get("kpi", "")).lower():
            runway_months = 6

    if ltv_cac is not None and ltv_cac < 3:
        return _brain(
            "freeze_spend",
            f"LTV:CAC {ltv_cac:.1f}x below 3x guardrail — freeze discretionary spend.",
            blockers=["Unit economics not fundable"],
            messages=[{"to": "Founder", "text": "Recommend price/COGS rework before scaling."}, {"to": "Growth Marketer", "text": "Pause paid scale until finance clears."}],
            confidence=0.88,
        )

    risks = list(v3.get("risk_heatmap") or [])[:2]
    urgent = [r for r in risks if isinstance(r, dict) and r.get("severity") in ("critical", "high")]
    if urgent:
        return _brain(
            "flag_financial_risk",
            f"Financial risk signal: {urgent[0].get('risk')}",
            sub_tasks=["Model downside scenario", "Update runway forecast"],
            messages=[{"to": "Founder", "text": f"Risk watch: {urgent[0].get('risk')} — review mitigation."}],
            confidence=0.84,
        )

    return _brain(
        "monitor_cashflow",
        "Unit economics within guardrails — continue weekly cash monitoring.",
        sub_tasks=["Log weekly burn", "Reconcile CAC actuals vs model"],
        confidence=0.76,
        plan=["Calculate runway", "Refresh PnL model"],
        tool_calls=[
            # Runway needs founder-verified cash/burn; empty payload surfaces validation_required honestly.
            {"tool": "runway_calculator", "payload": {}},
            {"tool": "pnl_model", "payload": {"months": 12}, "approved": True},
        ],
        expected_outputs=["runway_months", "pnl_path", "gross_margin_pct"],
    )


_ROLE_RUNNERS = {
    "Research Analyst": run_research_agent,
    "Growth Marketer": run_growth_agent,
    "Sales Lead": run_sales_agent,
    "COO": run_ops_agent,
    "Operations Manager": run_ops_agent,
    "Finance Manager": run_finance_agent,
}


def run_employee_brain(employee: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    """Dispatch to role-specialized brain. Founder synthesizes team, not deep work."""
    role = str(employee.get("role") or "")
    if role == "Founder":
        return _brain(
            "review_brief",
            "Synthesize team outputs; decide top 3 priorities for today.",
            sub_tasks=["Read war room updates", "Approve or reject spend requests"],
            confidence=0.75,
        )
    runner = _ROLE_RUNNERS.get(role)
    if runner:
        result = runner(employee, context)
        result["role"] = role
        result["tools_used"] = [str(c.get("tool")) for c in (result.get("tool_calls") or [])[:6]]
        return result
    return _brain(
        "support_team",
        f"No specialized brain for role '{role}' — default support mode.",
        confidence=0.5,
    )
