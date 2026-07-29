"""Workspace scope picker: full office, department(s), or specific employees."""

from __future__ import annotations



from typing import Any



from iidatech.execution.office_scope import (

    OfficeScope,

    SCOPE_MODES,

    department_for_harness,

    departments_for_harnesses,

    load_scope,

    save_scope,

)



_MODE_LABELS = {

    "full_office": "Full office",

    "department": "Department",

    "employee": "Employee / team",

}



_MODE_HELP = {

    "full_office": "All teams, full office day, war room, and command center.",

    "department": "Pick one or more departments — office + tasks + agents scoped to those teams.",

    "employee": "Pick specific people — chat and run tasks for just them.",

}





def render_workspace_mode_tabs(

    st: Any,

    *,

    report_id: str,

    harnesses: list[dict[str, Any]],

    office_state: dict[str, Any] | None = None,

) -> OfficeScope:

    """Top-level 3-way workspace switch. Returns configured OfficeScope."""

    scope = load_scope(st, report_id, office_state=office_state)

    labels = {str(h["id"]): str(h.get("name") or h["id"]) for h in harnesses if h.get("id")}

    dept_options = departments_for_harnesses(harnesses)



    st.markdown("#### Step 1 — Choose your workspace")

    mode_key = f"os2_workspace_mode_{report_id}"

    if mode_key not in st.session_state and scope.mode in SCOPE_MODES:

        st.session_state[mode_key] = scope.mode



    mode = st.segmented_control(

        "Workspace mode",

        options=list(SCOPE_MODES),

        format_func=lambda m: _MODE_LABELS[m],

        key=mode_key,

        label_visibility="collapsed",

    )

    st.caption(_MODE_HELP.get(mode, ""))



    departments: list[str] = []

    harness_ids: list[str] = []



    if mode == "department":

        departments = st.multiselect(

            "Which department(s)?",

            options=dept_options,

            default=[d for d in scope.departments if d in dept_options],

            key=f"os2_scope_depts_{report_id}",

        )

        if departments:

            members = [

                labels[str(h.get("id") or "")]

                for h in harnesses

                if str(h.get("id") or "") in labels and department_for_harness(h) in departments

            ]

            st.info("**Department workspace** — " + (", ".join(members) if members else "no agents yet"))

        else:

            st.warning("Select at least one department to open this workspace.")

    elif mode == "employee":

        harness_ids = st.multiselect(

            "Which employee(s)?",

            options=list(labels.keys()),

            default=[h for h in scope.harness_ids if h in labels],

            format_func=lambda hid: labels.get(hid, hid),

            key=f"os2_scope_employees_{report_id}",

        )

        if harness_ids:

            st.info("**Employee workspace** — " + ", ".join(labels[h] for h in harness_ids))

        else:

            st.warning("Select at least one employee to open their workspace.")

    else:

        st.info("**Full office workspace** — Taylor runs all teams: research → sales → growth → delivery.")



    new_scope = OfficeScope(mode=mode, departments=departments, harness_ids=harness_ids)

    save_scope(st, report_id, new_scope, office_state=office_state)

    return new_scope





# Backward-compatible alias

def render_office_scope_picker(

    st: Any,

    *,

    report_id: str,

    harnesses: list[dict[str, Any]],

    office_state: dict[str, Any] | None = None,

) -> OfficeScope:

    return render_workspace_mode_tabs(

        st, report_id=report_id, harnesses=harnesses, office_state=office_state

    )

