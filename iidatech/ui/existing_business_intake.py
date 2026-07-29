"""GAUGE-aligned 3-step intake for existing operating businesses."""

from __future__ import annotations



from typing import Any



from iidatech.services.existing_business_profile import (

    PLAN_PURPOSE_OPTIONS,

    collect_existing_business_profile,

    profile_to_planning_idea,

)

from iidatech.services.gauge_intake import (
    GAUGE_BUSINESS_TYPES,
    GAUGE_STEP_LABELS,
    checklist_for_type,
    gauge_checklist_session_key,
    gauge_checklist_value_session_key,
)





def _render_progress(st: Any, step: int) -> None:

    cols = st.columns(len(GAUGE_STEP_LABELS))

    for idx, label in enumerate(GAUGE_STEP_LABELS, start=1):

        with cols[idx - 1]:

            marker = "●" if idx == step else ("✓" if idx < step else "○")

            st.caption(f"{marker} **{idx}. {label}**")





def _step1_business_type(st: Any) -> None:

    st.markdown("#### Step 1 — What kind of business is this?")

    st.caption("The checklist and benchmarks adapt to the type you pick.")

    type_labels = [row["label"] for row in GAUGE_BUSINESS_TYPES]

    type_ids = [row["id"] for row in GAUGE_BUSINESS_TYPES]

    current = st.session_state.get("existing_biz_gauge_type")

    default_index = type_ids.index(current) if current in type_ids else 0

    picked = st.radio(

        "Business type",

        type_labels,

        index=default_index,

        key="existing_biz_gauge_type_label",

        label_visibility="collapsed",

    )

    st.session_state["existing_biz_gauge_type"] = type_ids[type_labels.index(picked)]

    _nav1, nav2 = st.columns([1, 1])

    with nav2:

        if st.button("Next: Checklist →", type="primary", width="stretch", key="gauge_to_step2"):

            st.session_state["existing_biz_gauge_step"] = 2

            st.rerun()





def _step2_checklist(st: Any) -> None:

    gauge_type = st.session_state.get("existing_biz_gauge_type") or "other"

    st.markdown("#### Step 2 — Tick what's actually in place")

    st.caption(
        "Leave a box unticked if you don't track it or don't have it — that's useful signal too. "
        "When you tick a box, add the actual number so the plan can use it directly."
    )
    for category, items in checklist_for_type(gauge_type).items():
        done = 0
        with st.expander(category, expanded=True):
            for index, item in enumerate(items):
                key = gauge_checklist_session_key(gauge_type, category, index)
                val_key = gauge_checklist_value_session_key(gauge_type, category, index)
                if st.checkbox(item, key=key):
                    done += 1
                    st.text_input(
                        "Value for this item",
                        key=val_key,
                        placeholder="add the number",
                        label_visibility="collapsed",
                    )
            st.caption(f"{done}/{len(items)} in place")

    nav1, nav2 = st.columns(2)

    with nav1:

        if st.button("← Back", width="stretch", key="gauge_back_step1"):

            st.session_state["existing_biz_gauge_step"] = 1

            st.rerun()

    with nav2:

        if st.button("Next: Add data →", type="primary", width="stretch", key="gauge_to_step3"):

            st.session_state["existing_biz_gauge_step"] = 3

            st.rerun()





def _step3_data(st: Any) -> dict[str, Any]:

    st.markdown("#### Step 3 — Give it the numbers")

    st.caption(

        "Fill in what you know (blank is fine). Paste P&L text, reports, or notes below. "

        "If you add a website, the builder can weigh public context against your numbers."

    )

    c1, c2 = st.columns(2)

    with c1:

        st.text_input("Company name", key="existing_biz_company_name", placeholder="e.g. Iidatech")

        st.text_input("Website", key="existing_biz_website", placeholder="e.g. iidatech.com")

        st.text_input("Primary market / geography", key="existing_biz_geography", placeholder="e.g. India, US")

        st.text_input("Industry (optional — defaults from business type)", key="existing_biz_industry")

    with c2:

        st.selectbox(

            "Currency",

            ["USD", "INR", "EUR", "GBP", "AUD", "CAD", "SGD", "AED"],

            key="existing_biz_currency",

        )

        st.selectbox("Plan purpose", PLAN_PURPOSE_OPTIONS, key="existing_biz_plan_purpose")

        st.text_input(

            "Other public links (LinkedIn, Crunchbase, app store, press...)",

            key="existing_biz_public_links",

            placeholder="comma separated URLs",

        )



    st.text_area(

        "What does your business do today? (optional if company name is clear)",

        height=80,

        key="existing_biz_description",

    )



    m1, m2, m3 = st.columns(3)

    with m1:

        st.text_input("Monthly revenue", key="existing_biz_monthly_revenue", placeholder="e.g. 42000")

        st.text_input("Monthly costs", key="existing_biz_monthly_costs", placeholder="e.g. 31000")

    with m2:

        st.text_input("Active customers", key="existing_biz_active_customers", placeholder="e.g. 310")

        st.text_input("Monthly churn %", key="existing_biz_churn_pct", placeholder="e.g. 4")

    with m3:

        st.text_input("Months in operation", key="existing_biz_months_in_operation", placeholder="e.g. 18")

        st.text_input("Team size", key="existing_biz_team_size", placeholder="e.g. 6")



    st.text_input(

        "Main competitors (comma separated)",

        key="existing_biz_competitors",

        placeholder="e.g. Acme Co, Northstar",

    )



    g1, g2 = st.columns(2)

    with g1:

        st.text_area("Growth goal (12–24 months)", height=70, key="existing_biz_growth_goal")

        st.text_input("Target revenue — Year 3", key="existing_biz_target_revenue_y3")

    with g2:

        st.text_input("Funding amount needed (if any)", key="existing_biz_funding_needed")

        st.text_area(

            "Anything else — paste financials, reports, notes",

            height=130,

            key="existing_biz_gauge_notes",

            placeholder="Paste P&L text, ad performance, customer feedback...",

        )



    nav1, _nav2 = st.columns(2)

    with nav1:

        if st.button("← Back", width="stretch", key="gauge_back_step2"):

            st.session_state["existing_biz_gauge_step"] = 2

            st.rerun()



    profile = collect_existing_business_profile(st)

    planning_idea = profile_to_planning_idea(profile)

    st.session_state["business_builder_idea"] = planning_idea

    st.session_state["business_builder_industry"] = profile.get("industry", "")

    st.session_state["business_builder_geo"] = profile.get("geography", "")

    return profile





def render_existing_business_intake_form(st: Any) -> dict[str, Any]:

    """Render GAUGE-style intake and return the collected profile."""

    st.markdown("### GAUGE — Business health intake")

    st.caption("Three steps: business type → capability checklist → operating metrics.")

    if "existing_biz_gauge_step" not in st.session_state:

        st.session_state["existing_biz_gauge_step"] = 1

    step = int(st.session_state.get("existing_biz_gauge_step") or 1)

    _render_progress(st, step)

    st.divider()



    if step <= 1:

        _step1_business_type(st)

        return collect_existing_business_profile(st)

    if step == 2:

        _step2_checklist(st)

        return collect_existing_business_profile(st)

    return _step3_data(st)

