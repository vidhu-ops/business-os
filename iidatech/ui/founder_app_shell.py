"""IIDATECH founder web app shell."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

APP_ROOT = Path(__file__).resolve().parents[2]
LOCAL_USER_STORE_PATH = APP_ROOT / "business_build_outputs" / "local_users.json"
BUILD_OUTPUTS_ROOT = APP_ROOT / "business_build_outputs"
FIGMA_DESIGN_URL = "https://www.figma.com/design/2BzVQuE3l29YkGiotdXeau/IIDATECH-Founder-App"

PAGE_LANDING = "Landing"
PAGE_DASHBOARD = "Dashboard"
PAGE_PROJECTS = "Projects"
PAGE_SAVED_FILES = "Saved Files"
PAGE_PROFILE = "Profile"
PAGE_WORKSPACE = "Workspace"
APP_PAGES = {PAGE_DASHBOARD, PAGE_PROJECTS, PAGE_SAVED_FILES, PAGE_PROFILE, PAGE_WORKSPACE}


@dataclass
class FounderAppDeps:
    list_projects: Callable[[int], list[dict]]
    activate_project: Callable[[dict], None]
    save_project: Callable[[dict], Any]
    build_project_payload: Callable[..., dict]
    assess_topic_scope: Callable[[str, str, str], Any]
    stats: dict[str, Any] = field(default_factory=dict)
    workflow_understand: str = "Understand your market"


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def hash_local_password(password: str) -> str:
    salt = "iidatech-local-auth-v1"
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def load_local_users() -> dict:
    users = _read_json(LOCAL_USER_STORE_PATH, {})
    return users if isinstance(users, dict) else {}


def save_local_users(users: dict) -> None:
    _write_json(LOCAL_USER_STORE_PATH, users)


def ensure_app_session_defaults(st: Any) -> None:
    st.session_state.setdefault("iidatech_authenticated", False)
    st.session_state.setdefault("iidatech_user_email", "")
    st.session_state.setdefault("iidatech_app_page", PAGE_LANDING)
    st.session_state.setdefault("iidatech_show_start_form", False)
    legacy = st.session_state.get("iidatech_app_page")
    if legacy in {"Home", "Login", "About"}:
        st.session_state["iidatech_app_page"] = PAGE_LANDING


def navigate(st: Any, page: str) -> None:
    st.session_state["iidatech_app_page"] = page
    st.rerun()


def start_free_now(st: Any, *, target: str = PAGE_WORKSPACE) -> None:
    st.session_state["iidatech_authenticated"] = True
    if not st.session_state.get("iidatech_user_email"):
        st.session_state["iidatech_user_email"] = "demo@local"
    st.session_state["iidatech_app_page"] = target
    st.rerun()


def logout(st: Any) -> None:
    st.session_state["iidatech_authenticated"] = False
    st.session_state["iidatech_user_email"] = ""
    st.session_state["iidatech_app_page"] = PAGE_LANDING
    st.session_state["iidatech_show_start_form"] = False
    st.rerun()


def inject_app_shell_styles(st: Any) -> None:
    from iidatech.ui.marketing_theme import MARKETING_CSS

    st.markdown(MARKETING_CSS, unsafe_allow_html=True)


def render_app_nav(st: Any, current_page: str) -> None:
    st.markdown(
        """
        <div class="iid-nav-wrap"><div class="iid-nav-inner">
        <p class="iid-logo">IIDA<span>TECH</span> · App</p></div></div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns([1.2, 1, 1, 1, 1, 1, 0.8, 0.8])
    with cols[0]:
        if st.button("← Site", key="iid_back_landing"):
            navigate(st, PAGE_LANDING)
    for idx, page in enumerate([PAGE_DASHBOARD, PAGE_PROJECTS, PAGE_WORKSPACE, PAGE_SAVED_FILES, PAGE_PROFILE], 1):
        with cols[idx]:
            btn_type = "primary" if page == current_page else "secondary"
            if st.button(page, key=f"iid_app_nav_{page}", type=btn_type, use_container_width=True):
                navigate(st, page)
    with cols[7]:
        if st.button("Log out", key="iid_app_logout", use_container_width=True):
            logout(st)


def _user_display_name(st: Any) -> str:
    email = str(st.session_state.get("iidatech_user_email") or "").strip().lower()
    if not email:
        return "User"
    record = load_local_users().get(email)
    if isinstance(record, dict) and record.get("name"):
        return str(record["name"])
    return email.split("@")[0].replace(".", " ").title()


def render_dashboard_page(st: Any, deps: FounderAppDeps) -> None:
    st.markdown(f"## Welcome back, {_user_display_name(st)}")
    projects = deps.list_projects(limit=5)
    active_id = st.session_state.get("active_opportunity_project_id")
    active = next((p for p in projects if p.get("workspace_id") == active_id), projects[0] if projects else None)
    metrics = st.columns(4)
    metrics[0].metric("Projects", len(projects))
    metrics[1].metric("Active", ((active or {}).get("idea") or "None")[:28])
    metrics[2].metric("Industry", ((active or {}).get("industry") or "—")[:20])
    metrics[3].metric("Market", ((active or {}).get("country") or "—")[:20])
    actions = st.columns(4)
    if actions[0].button("Open workspace", type="primary", use_container_width=True):
        navigate(st, PAGE_WORKSPACE)
    if actions[1].button("Manage projects", use_container_width=True):
        navigate(st, PAGE_PROJECTS)
    if actions[2].button("Saved files", use_container_width=True):
        navigate(st, PAGE_SAVED_FILES)
    if actions[3].button("Profile", use_container_width=True):
        navigate(st, PAGE_PROFILE)
    st.markdown("---")
    st.markdown("### Full research + team engine")
    st.caption("Opens the complete IIDATECH workspace (research, business plan, Employee OS). First load may take a minute.")
    if st.button("Open full workspace engine", type="primary", use_container_width=True, key="open_full_engine"):
        import os
        import subprocess
        import sys
        from pathlib import Path

        root = Path(__file__).resolve().parents[2]
        port = os.environ.get("IIDATECH_WORKSPACE_PORT", "8503")
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(root / "app.py"),
                "--server.port",
                port,
                "--server.headless",
                "true",
            ],
            cwd=str(root),
        )
        st.success(f"Starting full engine on http://127.0.0.1:{port}")
        st.link_button("Open workspace", f"http://127.0.0.1:{port}", type="primary")
    steps = [
        ("Define idea", "Topic, country, industry"),
        ("Check evidence", "Source readiness"),
        ("Generate research", "Market report"),
        ("Build business plan", "ICP, GTM, financials"),
        ("GTM and outreach", "Leads and messaging"),
        ("Execute with team", "Tasks and approvals"),
        ("Automate", "Workflows and logs"),
    ]
    st.dataframe(
        [{"Step": f"{idx}. {title}", "Output": detail} for idx, (title, detail) in enumerate(steps, 1)],
        use_container_width=True,
        hide_index=True,
    )
    if projects:
        st.dataframe(projects, use_container_width=True, hide_index=True)


def render_projects_page(st: Any, deps: FounderAppDeps) -> None:
    st.markdown("## Projects")
    create_tab, open_tab = st.tabs(["Create project", "Open existing"])
    with create_tab:
        idea = st.text_area("Project idea / topic", height=110, key="shell_new_project_idea")
        cols = st.columns(2)
        industry = cols[0].text_input("Industry", key="shell_new_project_industry")
        country = cols[1].text_input("Country / market", value="Global", key="shell_new_project_country")
        if st.button("Create project", type="primary", use_container_width=True, key="shell_create_project"):
            if not idea.strip() or not industry.strip() or not country.strip():
                st.error("Add idea, industry, and market.")
            else:
                scope = deps.assess_topic_scope(idea, industry, country)
                payload = deps.build_project_payload(
                    idea.strip(),
                    country.strip(),
                    industry.strip(),
                    deps.workflow_understand,
                    [],
                    [],
                    scope,
                )
                path = deps.save_project(payload)
                if path:
                    payload["path"] = str(path)
                deps.activate_project(payload)
                st.session_state.pop("founder_workflow_choice_value", None)
                st.success("Project created.")
                st.rerun()
    with open_tab:
        rows = deps.list_projects(limit=50)
        if not rows:
            st.info("No saved projects yet.")
            return
        selected_id = st.selectbox(
            "Saved projects",
            [row["workspace_id"] for row in rows],
            format_func=lambda workspace_id: next(
                (f"{row['idea'][:70]} | {row['country']} | {row['industry']}" for row in rows if row["workspace_id"] == workspace_id),
                workspace_id,
            ),
            key="shell_open_project_select",
        )
        selected = next((row for row in rows if row["workspace_id"] == selected_id), None)
        if selected:
            st.dataframe([selected], use_container_width=True, hide_index=True)
        if selected and st.button("Open project", type="primary", use_container_width=True, key="shell_open_project"):
            payload = _read_json(Path(selected["path"]), {})
            if isinstance(payload, dict):
                payload["path"] = selected["path"]
                deps.activate_project(payload)
                st.session_state.pop("founder_workflow_choice_value", None)
                st.session_state["iidatech_app_page"] = PAGE_WORKSPACE
                st.rerun()
            else:
                st.error("Could not read project file.")


def _collect_saved_files(limit: int = 80) -> list[dict]:
    rows: list[dict] = []
    extensions = {".md", ".json", ".csv", ".pdf", ".docx", ".xlsx", ".html", ".jsonl"}
    if not BUILD_OUTPUTS_ROOT.exists():
        return rows
    files = [
        path
        for path in BUILD_OUTPUTS_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in extensions and "__pycache__" not in path.parts
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    for path in files[:limit]:
        stat = path.stat()
        rows.append(
            {
                "name": path.name,
                "folder": path.parent.name,
                "type": path.suffix.lower().lstrip("."),
                "size_kb": round(stat.st_size / 1024, 1),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                "path": str(path.relative_to(APP_ROOT)),
            }
        )
    return rows


def render_saved_files_page(st: Any) -> None:
    st.markdown("## Saved files")
    rows = _collect_saved_files()
    if not rows:
        st.info("No saved files yet.")
        return
    st.dataframe(rows, use_container_width=True, hide_index=True)
    pick = st.selectbox(
        "Preview file",
        range(len(rows)),
        format_func=lambda index: rows[index]["path"],
        key="shell_saved_file_pick",
    )
    file_path = APP_ROOT / rows[pick]["path"]
    if file_path.suffix.lower() in {".md", ".json", ".csv", ".html", ".jsonl"}:
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if len(content) > 12000:
                content = content[:12000] + "\n… (truncated)"
            st.text_area("Preview", value=content, height=320)
        except Exception as exc:
            st.warning(str(exc))
    st.download_button(
        "Download",
        data=file_path.read_bytes(),
        file_name=file_path.name,
        mime="application/octet-stream",
        use_container_width=True,
    )


def render_profile_page(st: Any) -> None:
    st.markdown("## Profile")
    email = str(st.session_state.get("iidatech_user_email") or "")
    users = load_local_users()
    record = users.get(email.strip().lower(), {})
    name = record.get("name") if isinstance(record, dict) else _user_display_name(st)
    with st.container(border=True):
        st.markdown(f"**Name:** {name}")
        st.markdown(f"**Email:** {email or 'demo@local'}")
        st.markdown(f"**Account type:** {'Registered' if email in users else 'Demo / local'}")
        if isinstance(record, dict) and record.get("created_at"):
            st.markdown(f"**Member since:** {record['created_at'][:10]}")
    st.checkbox("Email me when team tasks need approval", value=False, key="shell_pref_approval_email")


def render_app_shell(st: Any, deps: FounderAppDeps) -> str:
    from iidatech.ui.marketing_landing import render_marketing_landing_page

    try:
        ensure_app_session_defaults(st)
        inject_app_shell_styles(st)
        page = str(st.session_state.get("iidatech_app_page") or PAGE_LANDING)

        def _open_workspace(st_ref: Any) -> None:
            # Open dashboard immediately (fast). User can launch full engine from there.
            start_free_now(st_ref, target=PAGE_DASHBOARD)

        if page == PAGE_LANDING:
            render_marketing_landing_page(
                st,
                on_workspace=_open_workspace,
                hash_password=hash_local_password,
                load_users=load_local_users,
                save_users=save_local_users,
            )
            return page

        if page in APP_PAGES:
            if not st.session_state.get("iidatech_authenticated"):
                start_free_now(st, target=page)
            render_app_nav(st, page)
            if page == PAGE_DASHBOARD:
                render_dashboard_page(st, deps)
            elif page == PAGE_PROJECTS:
                render_projects_page(st, deps)
            elif page == PAGE_SAVED_FILES:
                render_saved_files_page(st)
            elif page == PAGE_PROFILE:
                render_profile_page(st)
            return page

        st.session_state["iidatech_app_page"] = PAGE_LANDING
        render_marketing_landing_page(
            st,
            on_workspace=_open_workspace,
            hash_password=hash_local_password,
            load_users=load_local_users,
            save_users=save_local_users,
        )
        return PAGE_LANDING
    except Exception as exc:
        st.error("Something went wrong loading this page.")
        st.exception(exc)
        return PAGE_LANDING
