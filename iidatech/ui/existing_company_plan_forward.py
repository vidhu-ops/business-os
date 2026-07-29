"""Existing company plan forward - GAUGE audit + forward business plan tab."""
from __future__ import annotations

from typing import Any

from iidatech.services.existing_business_profile import (
    PLAN_PURPOSE_OPTIONS,
    collect_existing_business_profile,
    profile_to_planning_idea,
    validate_existing_business_profile,
)
from iidatech.services.gauge_audit import run_gauge_audit
from iidatech.services.gauge_intake import (
    GAUGE_BUSINESS_TYPES,
    GAUGE_STEP_LABELS,
    checklist_for_type,
    gauge_checklist_session_key,
    gauge_checklist_value_session_key,
)


def _pf_key(name: str) -> str:
    return f"plan_forward_{name}"


_PLAN_FORWARD_FIELDS = (
    "gauge_type",
    "gauge_type_label",
    "company_name",
    "website",
    "geography",
    "industry",
    "currency",
    "plan_purpose",
    "public_links",
    "description",
    "monthly_revenue",
    "monthly_costs",
    "active_customers",
    "churn_pct",
    "months_in_operation",
    "team_size",
    "competitors",
    "gauge_notes",
    "growth_goal",
    "target_revenue_y3",
    "funding_needed",
    "biggest_bottleneck",
    "priority_12_months",
    "success_12_months",
    "willing_to_invest",
    "stop_doing",
    "why_customers_choose",
    "why_customers_leave",
    "competitive_threat",
)

_PLAN_FORWARD_CHECKLIST_PREFIXES = ("existing_biz_chk_pf_", "existing_biz_chk_val_pf_")


def _plan_forward_session_keys(st: Any) -> list[str]:
    keys = [_pf_key(name) for name in _PLAN_FORWARD_FIELDS]
    keys.append(_pf_key("step"))
    for key in list(getattr(st, "session_state", {}).keys()):
        text = str(key)
        if any(text.startswith(prefix) for prefix in _PLAN_FORWARD_CHECKLIST_PREFIXES):
            keys.append(text)
    return keys


def save_plan_forward_draft(st: Any) -> None:
    """Snapshot wizard fields so back navigation and tab switches keep intake data."""
    draft: dict[str, Any] = {}
    for key in _plan_forward_session_keys(st):
        if key in st.session_state:
            draft[key] = st.session_state[key]
    st.session_state["plan_forward_draft"] = draft


def restore_plan_forward_draft(st: Any) -> None:
    draft = st.session_state.get("plan_forward_draft")
    if not isinstance(draft, dict):
        return
    for key, value in draft.items():
        st.session_state[key] = value


def _hydrate_plan_forward_from_profile(st: Any, profile: dict[str, Any]) -> None:
    if not profile:
        return
    type_id = profile.get("gauge_business_type") or "other"
    st.session_state[_pf_key("gauge_type")] = type_id
    type_label = profile.get("gauge_business_type_label") or next(
        (row["label"] for row in GAUGE_BUSINESS_TYPES if row["id"] == type_id),
        GAUGE_BUSINESS_TYPES[0]["label"],
    )
    st.session_state[_pf_key("gauge_type_label")] = type_label
    field_map = {
        "company_name": "company_name",
        "website": "website",
        "geography": "geography",
        "industry": "industry",
        "currency": "currency",
        "plan_purpose": "plan_purpose",
        "public_links": "public_links",
        "business_description": "description",
        "monthly_revenue": "monthly_revenue",
        "monthly_costs": "monthly_costs",
        "active_customers": "active_customers",
        "customer_churn_pct": "churn_pct",
        "months_in_operation": "months_in_operation",
        "employees_ft": "team_size",
        "main_competitors": "competitors",
        "gauge_notes": "gauge_notes",
        "target_revenue_year_3": "target_revenue_y3",
        "funding_amount_needed": "funding_needed",
        "growth_goal_12_24m": "growth_goal",
    }
    for profile_key, pf_key in field_map.items():
        value = profile.get(profile_key)
        if value is not None and value != "":
            st.session_state[_pf_key(pf_key)] = value
    forward = profile.get("plan_forward") or {}
    for pf_key in (
        "biggest_bottleneck",
        "priority_12_months",
        "success_12_months",
        "willing_to_invest",
        "stop_doing",
        "why_customers_choose",
        "why_customers_leave",
        "competitive_threat",
    ):
        value = forward.get(pf_key)
        if value is not None and value != "":
            st.session_state[_pf_key(pf_key)] = value
    pf_type = f"pf_{type_id}"
    checklist_state = profile.get("gauge_checklist_state") or {}
    for category, items in checklist_for_type(type_id).items():
        entries = checklist_state.get(category) or []
        for index in range(len(items)):
            entry = entries[index] if index < len(entries) else {}
            checked = bool(entry.get("checked")) if isinstance(entry, dict) else bool(entry)
            value = str(entry.get("value") or "").strip() if isinstance(entry, dict) else ""
            chk_key = gauge_checklist_session_key(pf_type, category, index)
            val_key = gauge_checklist_value_session_key(pf_type, category, index)
            st.session_state[chk_key] = checked
            if value:
                st.session_state[val_key] = value


def _ensure_plan_forward_hydrated(st: Any) -> None:
    if st.session_state.get("plan_forward_hydrated"):
        return
    restore_plan_forward_draft(st)
    if not st.session_state.get(_pf_key("company_name")):
        saved_profile = st.session_state.get("plan_forward_profile")
        if isinstance(saved_profile, dict):
            _hydrate_plan_forward_from_profile(st, saved_profile)
    save_plan_forward_draft(st)
    st.session_state["plan_forward_hydrated"] = True


def _go_to_step(st: Any, step: int) -> None:
    save_plan_forward_draft(st)
    st.session_state[_pf_key("step")] = step
    st.rerun()

def _render_progress(st: Any, step: int) -> None:
    labels = GAUGE_STEP_LABELS + ["Forward", "Report"]
    cols = st.columns(len(labels))
    for idx, label in enumerate(labels, start=1):
        with cols[idx - 1]:
            marker = "●" if idx == step else ("✓" if idx < step else "○")
            st.caption(f"{marker} **{idx}. {label}**")


def _step1_business_type(st: Any) -> None:
    st.markdown("#### Step 1 — What kind of business is this?")
    type_labels = [row["label"] for row in GAUGE_BUSINESS_TYPES]
    type_ids = [row["id"] for row in GAUGE_BUSINESS_TYPES]
    current = st.session_state.get(_pf_key("gauge_type"))
    default_index = type_ids.index(current) if current in type_ids else 0
    picked = st.radio(
        "Business type",
        type_labels,
        index=default_index,
        key=_pf_key("gauge_type_label"),
        label_visibility="collapsed",
    )
    st.session_state[_pf_key("gauge_type")] = type_ids[type_labels.index(picked)]
    if st.button("Next: Checklist →", type="primary", key=_pf_key("to_step2")):
        _go_to_step(st, 2)


def _step2_checklist(st: Any) -> None:
    gauge_type = st.session_state.get(_pf_key("gauge_type")) or "other"
    st.markdown("#### Step 2 — Tick what's actually in place")
    st.caption("When you tick a box, add the actual number if you have it — that feeds the audit directly.")
    pf_type = f"pf_{gauge_type}"
    for category, items in checklist_for_type(gauge_type).items():
        done = 0
        with st.expander(category, expanded=True):
            for index, item in enumerate(items):
                chk_key = gauge_checklist_session_key(pf_type, category, index)
                val_key = gauge_checklist_value_session_key(pf_type, category, index)
                checked = st.checkbox(item, key=chk_key)
                if checked:
                    done += 1
                if checked or str(st.session_state.get(val_key) or "").strip():
                    st.text_input(
                        "Value for this item",
                        key=val_key,
                        placeholder="e.g. 4% churn, 200000 MRR",
                        label_visibility="collapsed",
                    )
            st.caption(f"{done}/{len(items)} in place")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", key=_pf_key("back_step1")):
            _go_to_step(st, 1)
    with c2:
        if st.button("Next: Operating data →", type="primary", key=_pf_key("to_step3")):
            _go_to_step(st, 3)


def _step3_operating_data(st: Any) -> None:
    st.markdown("#### Step 3 — Operating numbers and identity")
    c1, c2 = st.columns(2)
    with c1:
        st.text_input("Company name", key=_pf_key("company_name"), placeholder="e.g. Iidatech")
        st.text_input("Website", key=_pf_key("website"), placeholder="e.g. iidatech.com")
        st.text_input("Primary market / geography", key=_pf_key("geography"), placeholder="e.g. India")
        st.text_input("Industry (optional)", key=_pf_key("industry"))
    with c2:
        st.selectbox("Currency", ["USD", "INR", "EUR", "GBP", "AUD", "CAD", "SGD", "AED"], key=_pf_key("currency"))
        st.selectbox("Plan purpose", PLAN_PURPOSE_OPTIONS, key=_pf_key("plan_purpose"))
        st.text_input("Public links (LinkedIn, Crunchbase...)", key=_pf_key("public_links"))
    st.text_area("What does the business do today?", height=70, key=_pf_key("description"))
    m1, m2, m3 = st.columns(3)
    with m1:
        st.text_input("Monthly revenue", key=_pf_key("monthly_revenue"), placeholder="42000")
        st.text_input("Monthly costs", key=_pf_key("monthly_costs"), placeholder="31000")
    with m2:
        st.text_input("Active customers", key=_pf_key("active_customers"), placeholder="310")
        st.text_input("Monthly churn %", key=_pf_key("churn_pct"), placeholder="4")
    with m3:
        st.text_input("Months in operation", key=_pf_key("months_in_operation"), placeholder="18")
        st.text_input("Team size", key=_pf_key("team_size"), placeholder="6")
    st.text_input("Main competitors (comma separated)", key=_pf_key("competitors"))
    st.text_area("Paste P&L, reports, or notes", height=100, key=_pf_key("gauge_notes"))
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", key=_pf_key("back_step2")):
            _go_to_step(st, 2)
    with c2:
        if st.button("Next: Forward plan questions →", type="primary", key=_pf_key("to_step4")):
            _go_to_step(st, 4)


def _step4_forward_questions(st: Any) -> None:
    st.markdown("#### Step 4 — Where you want to go")
    st.caption("These answers shape the forward plan and plain-language guidance.")
    st.text_area("Biggest bottleneck right now", height=70, key=_pf_key("biggest_bottleneck"))
    st.text_area("#1 priority for the next 12 months", height=70, key=_pf_key("priority_12_months"))
    st.text_area("What does success look like in 12 months?", height=70, key=_pf_key("success_12_months"))
    c1, c2 = st.columns(2)
    with c1:
        st.text_area("Time/money you can invest in the next 6 months", height=70, key=_pf_key("willing_to_invest"))
        st.text_area("What you would stop doing to hit the goal", height=70, key=_pf_key("stop_doing"))
    with c2:
        st.text_area("Why customers choose you today", height=70, key=_pf_key("why_customers_choose"))
        st.text_area("Why customers leave or say no", height=70, key=_pf_key("why_customers_leave"))
    st.text_area("Biggest competitive threat or market shift", height=70, key=_pf_key("competitive_threat"))
    st.text_input("Growth goal (12-24 months)", key=_pf_key("growth_goal"))
    st.text_input("Target revenue — Year 3", key=_pf_key("target_revenue_y3"))
    st.text_input("Funding needed (if any)", key=_pf_key("funding_needed"))
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", key=_pf_key("back_step3")):
            _go_to_step(st, 3)
    with c2:
        if st.button("Run GAUGE audit →", type="primary", key=_pf_key("run_audit")):
            save_plan_forward_draft(st)
            st.session_state[_pf_key("step")] = 5
            st.session_state[_pf_key("run_audit_now")] = True
            st.rerun()


def _collect_plan_forward_profile(st: Any) -> dict[str, Any]:
    gauge_type = st.session_state.get(_pf_key("gauge_type")) or "other"
    pf_type = f"pf_{gauge_type}"
    field_map = (
        ("existing_biz_gauge_type", "gauge_type"),
        ("existing_biz_company_name", "company_name"),
        ("existing_biz_website", "website"),
        ("existing_biz_geography", "geography"),
        ("existing_biz_industry", "industry"),
        ("existing_biz_currency", "currency"),
        ("existing_biz_plan_purpose", "plan_purpose"),
        ("existing_biz_public_links", "public_links"),
        ("existing_biz_description", "description"),
        ("existing_biz_monthly_revenue", "monthly_revenue"),
        ("existing_biz_monthly_costs", "monthly_costs"),
        ("existing_biz_active_customers", "active_customers"),
        ("existing_biz_churn_pct", "churn_pct"),
        ("existing_biz_months_in_operation", "months_in_operation"),
        ("existing_biz_team_size", "team_size"),
        ("existing_biz_competitors", "competitors"),
        ("existing_biz_gauge_notes", "gauge_notes"),
        ("existing_biz_growth_goal", "growth_goal"),
        ("existing_biz_target_revenue_y3", "target_revenue_y3"),
        ("existing_biz_funding_needed", "funding_needed"),
    )
    for target, source in field_map:
        val = st.session_state.get(_pf_key(source))
        if val is not None and val != "":
            st.session_state[target] = val
    st.session_state["existing_biz_gauge_type"] = gauge_type
    for category, items in checklist_for_type(gauge_type).items():
        for index in range(len(items)):
            chk_pf = gauge_checklist_session_key(pf_type, category, index)
            val_pf = gauge_checklist_value_session_key(pf_type, category, index)
            chk_std = gauge_checklist_session_key(gauge_type, category, index)
            val_std = gauge_checklist_value_session_key(gauge_type, category, index)
            if chk_pf in st.session_state:
                st.session_state[chk_std] = st.session_state[chk_pf]
            if val_pf in st.session_state:
                st.session_state[val_std] = st.session_state[val_pf]
    profile = collect_existing_business_profile(st)
    profile["plan_forward"] = {
        "biggest_bottleneck": st.session_state.get(_pf_key("biggest_bottleneck"), ""),
        "priority_12_months": st.session_state.get(_pf_key("priority_12_months"), ""),
        "success_12_months": st.session_state.get(_pf_key("success_12_months"), ""),
        "willing_to_invest": st.session_state.get(_pf_key("willing_to_invest"), ""),
        "stop_doing": st.session_state.get(_pf_key("stop_doing"), ""),
        "why_customers_choose": st.session_state.get(_pf_key("why_customers_choose"), ""),
        "why_customers_leave": st.session_state.get(_pf_key("why_customers_leave"), ""),
        "competitive_threat": st.session_state.get(_pf_key("competitive_threat"), ""),
    }
    profile["intake_source"] = "existing_company_plan_forward"
    return profile


def _status_emoji(status: str) -> str:
    return {"strong": "🟢", "watch": "🟡", "risk": "🔴"}.get(status, "⚪")


def render_gauge_audit_report(st: Any, audit: dict[str, Any]) -> None:
    score = int(audit.get("overall_score") or 0)
    st.markdown(f"### Overall: **{score}/100** — {audit.get('overall_label', '')}")
    st.write(audit.get("overall_summary") or "")
    st.info(audit.get("plain_english_read") or "No plain-language summary available.")
    st.markdown("#### Where you sit in the market")
    st.write(audit.get("market_position") or audit.get("industry_landscape") or "")
    st.divider()
    st.markdown("#### Category breakdown")
    cols = st.columns(3)
    for idx, cat in enumerate(audit.get("categories") or []):
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"{_status_emoji(cat.get('status', ''))} **{cat.get('name')}** — {cat.get('score')}/100")
                st.caption(cat.get("summary") or "")
    st.markdown("#### Key metrics vs benchmark")
    rows = []
    for m in audit.get("key_metrics") or []:
        if isinstance(m, dict):
            rows.append(
                {
                    "Metric": m.get("label"),
                    "Your value": m.get("value"),
                    "Benchmark": m.get("benchmark"),
                    "Read": m.get("assessment"),
                }
            )
    if rows:
        st.dataframe(rows, width="stretch", hide_index=True)
    st.markdown("#### What to focus on next")
    for action in audit.get("top_actions") or []:
        if isinstance(action, dict):
            st.markdown(f"**{action.get('title')}** — {action.get('why')}")
            st.caption(f"Impact: {action.get('impact')} · Effort: {action.get('effort')}")
    if audit.get("industry_landscape"):
        st.markdown("#### Industry landscape")
        st.write(audit["industry_landscape"])
    if audit.get("risks"):
        st.markdown("#### Risk flags")
        for risk in audit["risks"]:
            st.warning(str(risk))
    if audit.get("sources"):
        st.caption("Sources: " + ", ".join(str(s) for s in audit["sources"]))


def render_existing_company_plan_forward_tab(
    st: Any,
    *,
    text_request: Any = None,
    generate_plan_fn: Any = None,
    resolve_report_fn: Any = None,
    normalize_application_purpose_fn: Any = None,
    render_plan_output_fn: Any = None,
) -> None:
    st.markdown("### Existing company plan forward")
    st.caption(
        "Run the GAUGE health audit on your real numbers, see where you stand in the market in plain language, "
        "then build a forward-looking business plan from that read."
    )
    if _pf_key("step") not in st.session_state:
        st.session_state[_pf_key("step")] = 1
    _ensure_plan_forward_hydrated(st)
    step = int(st.session_state.get(_pf_key("step")) or 1)
    _render_progress(st, step)
    st.divider()
    if step <= 1:
        _step1_business_type(st)
        save_plan_forward_draft(st)
        return
    if step == 2:
        _step2_checklist(st)
        save_plan_forward_draft(st)
        return
    if step == 3:
        _step3_operating_data(st)
        save_plan_forward_draft(st)
        return
    if step == 4:
        _step4_forward_questions(st)
        save_plan_forward_draft(st)
        return

    profile = _collect_plan_forward_profile(st)
    save_plan_forward_draft(st)
    for err in validate_existing_business_profile(profile):
        st.error(err)
        if st.button("← Fix intake", key=_pf_key("fix_intake")):
            _go_to_step(st, 3)
        return

    if st.session_state.pop(_pf_key("run_audit_now"), False) or not st.session_state.get("gauge_audit_result"):
        with st.spinner("Running GAUGE audit — scoring categories, benchmarks, and market position..."):
            audit = run_gauge_audit(profile, text_request)
            st.session_state["gauge_audit_result"] = audit
            st.session_state["plan_forward_profile"] = profile
    else:
        audit = st.session_state.get("gauge_audit_result") or {}

    render_gauge_audit_report(st, audit)
    st.divider()

    idea = profile_to_planning_idea(profile)
    st.session_state["business_builder_idea"] = idea
    st.session_state["business_builder_industry"] = profile.get("industry", "")
    st.session_state["business_builder_geo"] = profile.get("geography", "")
    profile_with_audit = dict(profile)
    profile_with_audit["gauge_audit"] = audit
    st.session_state["existing_business_profile"] = profile_with_audit
    st.session_state["business_builder_is_existing"] = True

    if st.button("Build forward business plan from this audit", type="primary", key=_pf_key("build_plan")):
        if not generate_plan_fn:
            st.error("Plan generator is not wired.")
            return
        evidence = st.session_state.get("business_builder_current_evidence") or st.session_state.get("business_builder_evidence") or []
        report_ctx = resolve_report_fn(idea, profile.get("industry", ""), profile.get("geography", ""), use_latest=True) if resolve_report_fn else None
        app_purpose = profile.get("plan_purpose") or "Internal strategy"
        if normalize_application_purpose_fn:
            app_purpose = normalize_application_purpose_fn(st.session_state.get("business_application_purpose") or app_purpose)
        with st.spinner("Building forward business plan from GAUGE audit and your operating data..."):
            plan = generate_plan_fn(
                idea,
                profile.get("industry", ""),
                profile.get("geography", ""),
                evidence,
                report_ctx,
                app_purpose,
                profile_with_audit,
            )
            from iidatech.execution.plan_ingest import set_session_business_plan

            set_session_business_plan(st, plan)
            plan["gauge_audit"] = audit
            plan["plan_forward_profile"] = profile_with_audit
            st.session_state["business_builder_plan"] = plan
        st.success("Forward business plan created. Review it below.")

    if render_plan_output_fn and st.session_state.get("business_builder_plan"):
        render_plan_output_fn()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("← Edit checklist", key=_pf_key("edit_checklist")):
            _go_to_step(st, 2)
    with c2:
        if st.button("← Edit operating data", key=_pf_key("edit_operating")):
            _go_to_step(st, 3)
    with c3:
        if st.button("← Edit forward questions", key=_pf_key("edit_forward")):
            _go_to_step(st, 4)
    with c4:
        if st.button("Re-run GAUGE audit", key=_pf_key("rerun_audit")):
            save_plan_forward_draft(st)
            st.session_state.pop("gauge_audit_result", None)
            st.session_state[_pf_key("run_audit_now")] = True
            st.rerun()
