"""IIDATECH marketing landing — Business OS (PDF + Figma aligned)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import streamlit.components.v1 as components

from iidatech.ui.marketing_theme import FIGMA_DESIGN_URL, MARKETING_CSS, WIX_REFERENCE_URL

NAV_ITEMS = [
    ("Problem", "why"),
    ("Solution", "features"),
    ("Services", "services"),
    ("How", "how"),
    ("Workforce", "automation"),
    ("Work", "work"),
    ("Contact", "contact"),
]

StartFn = Callable[[Any], None]

# Inline SVG icons (stroke style)
_IC = {
    "chart": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M3 3v18h18"/><path d="M7 16l4-8 4 5 5-9"/></svg>',
    "search": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3-3"/></svg>',
    "clock": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>',
    "user": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="8" r="4"/><path d="M4 20c1.5-4 6.5-4 8-4s6.5 0 8 4"/></svg>',
    "globe": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg>',
    "plan": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/></svg>',
    "growth": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M4 18v-6M10 18V8M16 18v-3M22 18V4"/></svg>',
    "auto": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>',
    "tool": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z"/></svg>',
    "service": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>',
    "register": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M19 8v6M22 11h-6"/></svg>',
    "input": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><rect x="3" y="5" width="18" height="14" rx="2"/><path d="M7 15h.01M11 15h6"/></svg>',
    "result": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M9 15l2 2 4-4"/></svg>',
    "mentor": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2zM22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>',
    "brand": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M12 2l3 7h7l-5.5 4.5L18 21l-6-4-6 4 1.5-7.5L2 9h7z"/></svg>',
    "exec": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg>',
    "building": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><rect x="4" y="2" width="16" height="20" rx="1"/><path d="M9 22v-4h6v4M9 6h.01M15 6h.01M9 10h.01M15 10h.01M9 14h.01M15 14h.01"/></svg>',
    "shield": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "cart": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><circle cx="9" cy="21" r="1"/><circle cx="20" cy="21" r="1"/><path d="M1 1h4l2.68 13.39a2 2 0 002 1.61h9.72a2 2 0 002-1.61L23 6H6"/></svg>',
    "heart": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M20.84 4.61a5.5 5.5 0 00-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 00-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 000-7.78z"/></svg>',
    "cloud": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z"/></svg>',
    "factory": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M2 20a2 2 0 002 2h16a2 2 0 002-2V8l-7 5V8l-7 5V4a2 2 0 00-2-2H4a2 2 0 00-2 2z"/></svg>',
    "book": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M4 19.5A2.5 2.5 0 016.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/></svg>',
    "bolt": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>',
    "truck": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><rect x="1" y="3" width="15" height="13"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg>',
    "mail": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M22 6l-10 7L2 6"/></svg>',
    "phone": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M22 16.92v3a2 2 0 01-2.18 2 19.79 19.79 0 01-8.63-3.07 19.5 19.5 0 01-6-6 19.79 19.79 0 01-3.07-8.67A2 2 0 014.11 2h3a2 2 0 012 1.72c.127.96.361 1.903.7 2.81a2 2 0 01-.45 2.11L8.09 9.91a16 16 0 006 6l1.27-1.27a2 2 0 012.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0122 16.92z"/></svg>',
    "pin": '<svg viewBox="0 0 24 24" stroke-width="2" stroke-linecap="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0z"/><circle cx="12" cy="10" r="3"/></svg>',
}


def inject_styles(st: Any) -> None:
    st.markdown(MARKETING_CSS, unsafe_allow_html=True)


def render_nav_bar(st: Any, *, on_start: Callable[[], None]) -> None:
    st.markdown(
        """
        <div class="iid-page">
          <div class="iid-nav-shell">
            <div class="iid-nav">
              <p class="iid-logo">IIDA<span>TECH</span></p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    # Streamlit-safe nav: buttons set a scroll target, then JS scrolls after paint.
    cols = st.columns([1, 1, 1, 1, 1, 1, 1, 1.25])
    for idx, (label, key) in enumerate(NAV_ITEMS):
        with cols[idx]:
            if st.button(label, key=f"mkt_nav_{key}", use_container_width=True):
                st.session_state["iidatech_scroll_to"] = f"iid-{key}"
                st.rerun()
    with cols[7]:
        if st.button("START NOW", type="primary", use_container_width=True, key="mkt_start"):
            on_start()


def render_start_form(
    st: Any,
    *,
    on_workspace: StartFn,
    hash_password: Callable[[str], str],
    load_users: Callable[[], dict],
    save_users: Callable[[dict], None],
) -> None:
    if not st.session_state.get("iidatech_show_start_form"):
        return
    with st.container(border=True):
        st.markdown("#### Get started free")
        st.caption("30 free credits — no card required.")
        tab_login, tab_register, tab_demo = st.tabs(["Log in", "Register", "Demo"])
        with tab_login:
            email = st.text_input("Email", key="shell_login_email")
            password = st.text_input("Password", type="password", key="shell_login_password")
            if st.button("Log in", type="primary", key="shell_login_button", use_container_width=True):
                record = load_users().get(email.strip().lower())
                if record and record.get("password_hash") == hash_password(password):
                    st.session_state["iidatech_authenticated"] = True
                    st.session_state["iidatech_user_email"] = email.strip().lower()
                    st.session_state["iidatech_show_start_form"] = False
                    on_workspace(st)
                else:
                    st.error("Invalid email or password.")
        with tab_register:
            reg_email = st.text_input("Work email", key="shell_register_email")
            reg_name = st.text_input("Name", key="shell_register_name")
            reg_password = st.text_input("Password", type="password", key="shell_register_password")
            if st.button("Create account", type="primary", key="shell_register_button", use_container_width=True):
                if "@" not in reg_email or len(reg_password) < 6:
                    st.error("Valid email and 6+ character password required.")
                else:
                    users = load_users()
                    key = reg_email.strip().lower()
                    if key in users:
                        st.warning("Account exists — log in instead.")
                    else:
                        users[key] = {
                            "name": reg_name.strip() or key.split("@")[0],
                            "email": key,
                            "password_hash": hash_password(reg_password),
                            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        }
                        save_users(users)
                        st.session_state["iidatech_authenticated"] = True
                        st.session_state["iidatech_user_email"] = key
                        st.session_state["iidatech_show_start_form"] = False
                        on_workspace(st)
        with tab_demo:
            if st.button("SEE DEMO", type="primary", key="shell_demo_button", use_container_width=True):
                st.session_state["iidatech_show_start_form"] = False
                on_workspace(st)


def _hero(st: Any, *, on_workspace: StartFn, on_start: Callable[[], None]) -> None:
    st.markdown(
        """
        <div class="iid-hero">
          <div class="iid-hero-grid">
            <div>
              <p class="eyebrow">IIDATECH · BUSINESS OS</p>
              <h1>
                <span class="os">The operating system for</span>
                <em>BUSINESSES</em>
              </h1>
              <div class="pipe">
                <span>RESEARCH</span><i>→</i><span>PLAN</span><i>→</i><span>EXECUTE</span><i>→</i><span>AUTOMATE</span>
              </div>
              <p class="lead">A market-intelligence and business-execution platform for India's founders, SMEs, and enterprise teams — run it yourself as a Tool, or hand the work to an on-demand AI workforce as a Service.</p>
            </div>
            <div>
              <div class="iid-hero-mockup">
                <div class="iid-mockup-chrome">
                  <span class="iid-mockup-dot r"></span>
                  <span class="iid-mockup-dot y"></span>
                  <span class="iid-mockup-dot g"></span>
                </div>
                <div class="iid-mockup-body">
                  <div class="iid-mockup-row"><div class="iid-mockup-bar mid"></div></div>
                  <div class="iid-mockup-row"><div class="iid-mockup-bar long"></div></div>
                  <div class="iid-mockup-row"><div class="iid-mockup-bar short"></div><div class="iid-mockup-bar mid" style="flex:1"></div></div>
                  <div class="iid-mockup-chart">
                    <span style="height:45%"></span><span style="height:70%"></span>
                    <span style="height:55%"></span><span style="height:90%"></span>
                    <span style="height:65%"></span><span style="height:80%"></span>
                  </div>
                  <div class="iid-mockup-tags">
                    <span class="iid-mockup-tag">TAM/SAM</span>
                    <span class="iid-mockup-tag">COMPETITORS</span>
                    <span class="iid-mockup-tag">SOURCES</span>
                  </div>
                </div>
              </div>
              <div class="iid-hero-panel" style="margin-top:0.85rem">
                <div class="stat"><strong>6</strong><span>AI employees on day one</span></div>
                <div class="stat"><strong>40+</strong><span>Page reports in minutes</span></div>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="iid-cta-row">', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("START FREE NOW", type="primary", use_container_width=True, key="hero_start"):
        on_start()
    if c2.button("SEE DEMO", use_container_width=True, key="hero_demo"):
        on_workspace(st)
    st.markdown("</div>", unsafe_allow_html=True)


def _section_trust(st: Any) -> None:
    st.markdown(
        f"""
        <div class="iid-trust-bar">
          <span>Trusted across India</span>
          <div class="iid-trust-logos">
            <span class="iid-trust-chip">{_IC["shield"]} FinTech</span>
            <span class="iid-trust-chip">{_IC["heart"]} Healthcare</span>
            <span class="iid-trust-chip">{_IC["cloud"]} SaaS</span>
            <span class="iid-trust-chip">{_IC["cart"]} D2C</span>
            <span class="iid-trust-chip">{_IC["building"]} Real Estate</span>
            <span class="iid-trust-chip">{_IC["factory"]} Manufacturing</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _section_problem(st: Any) -> None:
    st.markdown('<a id="iid-why"></a><div id="iid-why-wrap" class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="iid-manifesto">
          <span class="iid-label">01 / The Problem</span>
          <h2>Good decisions in market still run on guesswork.</h2>
          <p>7.86 Cr MSMEs employ 34.6 crore people — nearly all without a dedicated research or strategy function. Analyst teams cost lakhs and take weeks. Global tools barely cover Indian sectors, regulation, or buyer behaviour.</p>
          <div class="iid-stat-row">
            <div class="iid-stat-box"><strong>7.86 Cr</strong><span>MSMEs in India</span></div>
            <div class="iid-stat-box"><strong>34.6 Cr</strong><span>People employed</span></div>
            <div class="iid-stat-box"><strong>&lt;5%</strong><span>Have research teams</span></div>
          </div>
          <div class="iid-pain-row">
            <div class="iid-pain-tile"><div class="icon">{_IC["search"]}</div><strong>No dedicated research function</strong></div>
            <div class="iid-pain-tile"><div class="icon">{_IC["clock"]}</div><strong>Consulting is slow & expensive</strong></div>
            <div class="iid-pain-tile"><div class="icon">{_IC["user"]}</div><strong>Founders do everything alone</strong></div>
            <div class="iid-pain-tile"><div class="icon">{_IC["globe"]}</div><strong>Global tools miss India</strong></div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _section_solution(st: Any, *, on_workspace: StartFn) -> None:
    st.markdown('<a id="iid-features"></a><div id="iid-features-wrap" class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">02 / The Solution</span>'
        '<p class="iid-h2">One operating system.<br>Four functions your business is missing.</p>'
        '<p class="iid-sub">IIDATECH unifies research, planning, growth, and automation — every function ships as Tool and Service.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="iid-grid-4">
          <div class="iid-card"><div class="iid-svg-icon">{_IC["chart"]}</div><span class="tag">RESEARCH</span><h3>Market Intelligence</h3>
          <p>Multi-source reports, competitor maps, and TAM/SAM/SOM for Indian verticals.</p></div>
          <div class="iid-card"><div class="iid-svg-icon">{_IC["plan"]}</div><span class="tag">STRATEGY</span><h3>Business Planning</h3>
          <p>Business plans, GTM strategy, and financial models from your inputs.</p></div>
          <div class="iid-card"><div class="iid-svg-icon">{_IC["growth"]}</div><span class="tag">GROWTH</span><h3>Employees — BD & CRM</h3>
          <p>Lead lists, CRM enrichment, and outreach on the same data as research.</p></div>
          <div class="iid-card"><div class="iid-svg-icon">{_IC["auto"]}</div><span class="tag">AUTOMATION</span><h3>Workflow Automation</h3>
          <p>Agent-built automations connecting CRM, inbox, and reporting.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    b = st.columns(4)
    labels = ["Try Research", "Try Plan", "Try Growth", "Try Auto"]
    keys = ["try_research", "try_plan", "try_growth", "try_auto"]
    for i, k in enumerate(keys):
        if b[i].button(labels[i], key=k, use_container_width=True):
            on_workspace(st)
    st.markdown("</div>", unsafe_allow_html=True)


def _section_reviews(st: Any) -> None:
    st.markdown('<div class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">What founders say</span>'
        '<p class="iid-h2">Shipped in hours,<br>not weeks.</p>'
        '<p class="iid-sub">Teams use IIDATECH to replace slow consulting cycles with sourced research and execution they can act on immediately.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="iid-reviews-grid">
          <div class="iid-review-card">
            <div class="iid-stars">★★★★★</div>
            <p class="iid-review-quote">"We replaced a two-lakh consulting sprint with a 40-page market report in one afternoon. The sourcing alone saved us weeks."</p>
            <div class="iid-reviewer">
              <div class="av">AK</div>
              <div><strong>Arjun K.</strong><span>SaaS Founder · Bengaluru</span></div>
            </div>
          </div>
          <div class="iid-review-card">
            <div class="iid-stars">★★★★★</div>
            <p class="iid-review-quote">"Finally something built for Indian MSMEs. Competitor maps, pricing, and regulation — all in one place. Our bank loan deck was ready the same day."</p>
            <div class="iid-reviewer">
              <div class="av" style="background:linear-gradient(135deg,#7c3aed,#5b21b6)">PS</div>
              <div><strong>Priya S.</strong><span>MSME Owner · Pune</span></div>
            </div>
          </div>
          <div class="iid-review-card">
            <div class="iid-stars">★★★★★</div>
            <p class="iid-review-quote">"The AI workforce handled research and outreach while we focused on product. Felt like hiring a team we could not afford yet."</p>
            <div class="iid-reviewer">
              <div class="av" style="background:linear-gradient(135deg,#059669,#047857)">RM</div>
              <div><strong>Rahul M.</strong><span>D2C Founder · Mumbai</span></div>
            </div>
          </div>
        </div>
        <div class="iid-metrics-strip">
          <div class="iid-metric-tile"><strong>4.9</strong><span>Avg. founder rating</span></div>
          <div class="iid-metric-tile"><strong>40+</strong><span>Page reports in minutes</span></div>
          <div class="iid-metric-tile"><strong>₹1L+</strong><span>Saved vs consulting</span></div>
          <div class="iid-metric-tile"><strong>6</strong><span>AI employees on day one</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)


def _section_buy(st: Any, *, on_workspace: StartFn) -> None:
    st.markdown('<div class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">05 / How You Buy It</span>'
        '<p class="iid-h2">Two ways to work with IIDATECH.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="iid-buy-grid">
          <div class="iid-buy-card">
            <div class="buy-icon">{_IC["tool"]}</div>
            <div class="mode">AS A TOOL</div>
            <h3>Self-serve platform</h3>
            <p>Generate reports, plans, and decks yourself. Dashboard access to research, planning & CRM modules.</p>
            <ul>
              <li>Usage-based or subscription</li>
              <li>Best for teams who run it themselves</li>
              <li>On-demand reports & templates</li>
            </ul>
          </div>
          <div class="iid-buy-card">
            <div class="buy-icon">{_IC["service"]}</div>
            <div class="mode">AS A SERVICE</div>
            <h3>Done-for-you delivery</h3>
            <p>IIDATECH agents, checked by reviewers, deliver research, plans, BD, and automation as engagements.</p>
            <ul>
              <li>Priced per sprint or retainer</li>
              <li>Best for founders who want output</li>
              <li>Managed research & outreach</li>
            </ul>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("OPEN WORKSPACE", type="primary", key="buy_start", use_container_width=True):
        on_workspace(st)
    st.markdown("</div>", unsafe_allow_html=True)


def _section_services(st: Any, *, on_workspace: StartFn, on_start) -> None:
    st.markdown('<a id="iid-services"></a><div id="iid-services-wrap" class="iid-section-dark">', unsafe_allow_html=True)
    st.markdown('<div class="iid-wrap">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">Services</span>'
        '<p class="iid-h2">Six tools. One platform.</p>'
        '<p class="iid-sub">Show proof, not pitch decks. Generate what you need, then act on it.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    services = [
        ("RESEARCH", "Research", "40-page market report for your idea, location, and currency.", _IC["search"]),
        ("BUSINESS PLAN", "Business Plan", "30-page tailored report with market assessment and expenses.", _IC["plan"]),
        ("EXECUTION", "Execution Plan", "35-page checklist with deliverables, vendors, hiring, legal.", _IC["exec"]),
        ("MENTORSHIP", "Mentorship", "AI or real mentor — location and industry specific overview.", _IC["mentor"]),
        ("AUTOMATION", "Automation", "Workflows, AI automation, dashboard and CRM for your team.", _IC["auto"]),
        ("BRAND", "Brand Building", "Website, branding, packaging, and digital media from research.", _IC["brand"]),
    ]
    cards = '<div class="iid-services-grid">'
    for tag, title, body, icon in services:
        cards += f'<div class="iid-service"><div class="svc-icon">{icon}</div><span class="tag">{tag}</span><h3>{title}</h3><p>{body}</p></div>'
    cards += "</div>"
    st.markdown(cards, unsafe_allow_html=True)
    st.markdown('<div class="iid-svc-actions">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("TRY RESEARCH", key="svc_quick_research", use_container_width=True):
        on_workspace(st)
    if c2.button("TRY BUSINESS PLAN", key="svc_quick_plan", use_container_width=True):
        on_workspace(st)
    if c3.button("OPEN WORKSPACE", type="primary", key="svc_quick_ws", use_container_width=True):
        on_start()
    st.markdown("</div></div></div>", unsafe_allow_html=True)


def _section_how(st: Any, *, on_workspace: StartFn, on_start) -> None:
    st.markdown('<a id="iid-how"></a><div id="iid-how-wrap" class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">How it works</span>'
        '<p class="iid-h2">Three steps. One minute.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""<div class="iid-process">
      <div class="iid-process-step"><div class="step-icon">{_IC["register"]}</div><p class="iid-step-big">01</p><h4>Register</h4><p>Name and email — get 30 free credits.</p></div>
      <div class="iid-process-step"><div class="step-icon">{_IC["input"]}</div><p class="iid-step-big">02</p><h4>Input</h4><p>Idea + up to 4 fields. Press generate.</p></div>
      <div class="iid-process-step"><div class="step-icon">{_IC["result"]}</div><p class="iid-step-big">03</p><h4>Result</h4><p>Report ready at your fingertips.</p></div>
    </div>""",
        unsafe_allow_html=True,
    )
    steps = [
        ("Create account", "Register or use demo — 30 free credits.", _IC["register"]),
        ("Create a project", "Enter idea, industry, and target market.", _IC["input"]),
        ("Pick a tool", "Research, Business Plan, Execution, Team, or Automations.", _IC["tool"]),
        ("Generate", "IIDATECH produces sourced reports and plans in minutes.", _IC["bolt"]),
        ("Review & export", "Download PDF/CSV or open in the full workspace.", _IC["result"]),
        ("Execute", "Use Team & Execution for tasks, leads, and automations.", _IC["exec"]),
    ]
    st.markdown('<p class="iid-h2" style="margin-top:2rem;font-size:1.25rem">Full workflow</p>', unsafe_allow_html=True)
    for i, (title, body, icon) in enumerate(steps, 1):
        st.markdown(
            f'<div class="iid-how-row"><div class="iid-how-icon">{icon}</div>'
            f'<div><strong style="color:var(--iid-text)">{title}</strong><br>'
            f'<span style="color:var(--iid-muted);font-size:0.88rem">{body}</span></div></div>',
            unsafe_allow_html=True,
        )
    if st.button("Start now — open dashboard", type="primary", key="how_start", use_container_width=True):
        on_start()
    st.markdown("</div>", unsafe_allow_html=True)


def _section_workforce(st: Any, *, on_workspace: StartFn) -> None:
    st.markdown('<a id="iid-automation"></a><div id="iid-automation-wrap" class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">04 / The AI Workforce</span>'
        '<p class="iid-h2">Hire the team you cannot afford to hire.</p>'
        '<p class="iid-sub">Each employee is a specialized AI agent — use one, or the whole team, as a dashboard seat or delivered engagement.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="iid-grid-3">
          <div class="iid-card"><div class="iid-agent-head"><div class="iid-agent-avatar c1">RA</div><span class="tag">AG·01</span></div><h3>Research Analyst</h3><p>Multi-source market and competitor research with sourcing shown.</p></div>
          <div class="iid-card"><div class="iid-agent-head"><div class="iid-agent-avatar c2">SA</div><span class="tag">AG·02</span></div><h3>Strategy Associate</h3><p>Business plans, GTM, and TAM/SAM/SOM from your inputs.</p></div>
          <div class="iid-card"><div class="iid-agent-head"><div class="iid-agent-avatar c3">RW</div><span class="tag">AG·03</span></div><h3>Report Writer</h3><p>Board- and investor-ready documents — formatted, not just drafted.</p></div>
          <div class="iid-card"><div class="iid-agent-head"><div class="iid-agent-avatar c4">BD</div><span class="tag">AG·04</span></div><h3>BD & Outreach</h3><p>Lead lists, CRM enrichment, and outreach sequencing.</p></div>
          <div class="iid-card"><div class="iid-agent-head"><div class="iid-agent-avatar c5">AE</div><span class="tag">AG·05</span></div><h3>Automation Engineer</h3><p>Workflows across CRM, email, and reporting pipelines.</p></div>
          <div class="iid-card"><div class="iid-agent-head"><div class="iid-agent-avatar c6">DD</div><span class="tag">AG·06</span></div><h3>Deck Designer</h3><p>Investor decks, one-pagers, and financial narratives.</p></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("OPEN WORKSPACE", type="primary", key="auto_start", use_container_width=True):
        on_workspace(st)
    st.markdown("</div>", unsafe_allow_html=True)


def _section_samples(st: Any, *, on_workspace: StartFn) -> None:
    st.markdown('<div class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">Take a look</span>'
        '<p class="iid-h2">Sample deliverables<br>you can generate today.</p>'
        '<p class="iid-sub">Real outputs — sourced reports, investor-ready plans, and execution checklists. Not slide decks.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="iid-samples-grid">
          <div class="iid-sample-card">
            <div class="iid-sample-preview">
              <div class="iid-sample-doc">
                <div class="line title"></div>
                <div class="line w80"></div>
                <div class="line w60"></div>
                <div class="mini-chart">
                  <span style="height:55%"></span><span style="height:80%"></span>
                  <span style="height:45%"></span><span style="height:90%"></span>
                  <span style="height:65%"></span>
                </div>
                <div class="line w40"></div>
              </div>
            </div>
            <div class="iid-sample-body">
              <span class="tag">RESEARCH</span>
              <h3>Market Research Report</h3>
              <p>40+ pages across 18 topics: TAM/SAM/SOM, competitors, pricing, regulation, and buyer segments.</p>
              <div class="iid-sample-meta">
                <span>40 pages</span><span>24 sources</span><span>PDF export</span>
              </div>
            </div>
          </div>
          <div class="iid-sample-card">
            <div class="iid-sample-preview">
              <div class="iid-sample-doc">
                <div class="line title"></div>
                <div class="line w60"></div>
                <div class="line w80"></div>
                <div class="line w80"></div>
                <div class="line w60"></div>
                <div class="line w40"></div>
                <div class="line w80"></div>
              </div>
            </div>
            <div class="iid-sample-body">
              <span class="tag">BUSINESS PLAN</span>
              <h3>Investor-Ready Plan</h3>
              <p>30-page document with financial projections, expense breakdown, and submission-ready structure.</p>
              <div class="iid-sample-meta">
                <span>30 pages</span><span>Financials</span><span>Bank-ready</span>
              </div>
            </div>
          </div>
          <div class="iid-sample-card">
            <div class="iid-sample-preview">
              <div class="iid-sample-doc">
                <div class="line title"></div>
                <div class="line w80"></div>
                <div class="line w60" style="background:#c8f0d8"></div>
                <div class="line w80" style="background:#c8f0d8"></div>
                <div class="line w60"></div>
                <div class="line w80" style="background:#c8f0d8"></div>
              </div>
            </div>
            <div class="iid-sample-body">
              <span class="tag">EXECUTION</span>
              <h3>Execution Roadmap</h3>
              <p>35-page checklist with phase deliverables, hiring plan, vendor options, and go-to-market steps.</p>
              <div class="iid-sample-meta">
                <span>35 pages</span><span>Checklist</span><span>Actionable</span>
              </div>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("Generate your own report", type="primary", key="sample_start", use_container_width=True):
        on_workspace(st)
    st.markdown("</div>", unsafe_allow_html=True)


def _section_work(st: Any, *, on_workspace: StartFn) -> None:
    st.markdown('<a id="iid-work"></a><div id="iid-work-wrap" class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">Our work</span>'
        '<p class="iid-h2">Built for Indian verticals</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    industries = [
        ("Real Estate", _IC["building"]),
        ("CyberTech", _IC["shield"]),
        ("FinTech", _IC["chart"]),
        ("Healthcare", _IC["heart"]),
        ("SaaS", _IC["cloud"]),
        ("E-commerce", _IC["cart"]),
        ("Manufacturing", _IC["factory"]),
        ("Education", _IC["book"]),
        ("Energy", _IC["bolt"]),
        ("Logistics", _IC["truck"]),
    ]
    tiles = '<div class="iid-industry-grid">'
    for name, icon in industries:
        tiles += f'<div class="iid-industry-tile"><div class="ico">{icon}</div><span>{name}</span></div>'
    tiles += "</div>"
    st.markdown(tiles, unsafe_allow_html=True)
    if st.button("Get Started", type="primary", key="work_start", use_container_width=True):
        on_workspace(st)
    st.markdown("</div>", unsafe_allow_html=True)


def _section_cta_banner(st: Any, *, on_start: Callable[[], None], on_workspace: StartFn) -> None:
    st.markdown(
        """
        <div class="iid-cta-banner">
          <div class="iid-cta-banner-inner">
            <div>
              <span class="iid-label">Ready to ship?</span>
              <p class="iid-h2" style="margin-bottom:0.5rem">Start with 30 free credits.</p>
              <p class="iid-sub" style="margin:0">No card required. Generate your first report in under a minute.</p>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns(2)
    if c1.button("START FREE NOW", type="primary", use_container_width=True, key="cta_banner_start"):
        on_start()
    if c2.button("SEE DEMO", use_container_width=True, key="cta_banner_demo"):
        on_workspace(st)


def _section_contact(st: Any) -> None:
    st.markdown('<a id="iid-contact"></a><div id="iid-contact-wrap" class="iid-section">', unsafe_allow_html=True)
    st.markdown(
        '<div class="iid-section-head">'
        '<span class="iid-label">Get in touch</span>'
        '<p class="iid-h2">Your company does not need more dashboards.<br>It needs a team that ships.</p>'
        '<p class="iid-sub">Fill the form and we will personally contact you.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    left, right = st.columns([0.9, 1.1])
    with left:
        st.markdown(
            f"""
            <div class="iid-contact-cards">
              <div class="iid-contact-card">
                <div class="ico">{_IC["mail"]}</div>
                <div><strong>Email us</strong>
                <a href="mailto:vidhugupta1996@gmail.com">vidhugupta1996@gmail.com</a></div>
              </div>
              <div class="iid-contact-card">
                <div class="ico">{_IC["phone"]}</div>
                <div><strong>Call us</strong>
                <a href="tel:+919545403431">+91 95454 03431</a></div>
              </div>
              <div class="iid-contact-card">
                <div class="ico">{_IC["pin"]}</div>
                <div><strong>Based in</strong>
                <span>India · Serving founders globally</span></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with right:
        with st.container(border=True):
            with st.form("contact_form"):
                c1, c2 = st.columns(2)
                c1.text_input("First name")
                c2.text_input("Last name")
                st.text_input("Email*")
                st.text_input("Phone")
                st.text_area("Message*")
                st.checkbox("Subscribe to newsletter")
                if st.form_submit_button("Submit", type="primary", use_container_width=True):
                    st.success("Thanks — we will contact you soon.")
    st.markdown(
        f"""
    <div class="iid-footer-dark">
      <div class="iid-footer-grid">
        <div><h4>Product</h4>
          <p><a href="#iid-features">Solution</a><br>
          <a href="#iid-services">Services</a><br>
          <a href="#iid-automation">Workforce</a><br>
          <a href="#iid-work">Our Work</a></p></div>
        <div><h4>Company</h4>
          <p><a href="{WIX_REFERENCE_URL}">Terms</a><br>
          <a href="{WIX_REFERENCE_URL}">Privacy</a><br>
          <a href="{WIX_REFERENCE_URL}">Refund</a><br>
          <a href="{WIX_REFERENCE_URL}">Accessibility</a></p></div>
        <div><h4>Contact</h4>
          <p><a href="mailto:vidhugupta1996@gmail.com">vidhugupta1996@gmail.com</a><br>
          <a href="mailto:vidhu@pronto.me">vidhu@pronto.me</a><br>
          <a href="tel:+919545403431">+91 95454 03431</a></p></div>
      </div>
      <p class="iid-footer-copy">IIDATECH — Business Operating System · India ·
      <a href="{FIGMA_DESIGN_URL}">Design</a></p>
    </div>""",
        unsafe_allow_html=True,
    )
    st.markdown("</div>", unsafe_allow_html=True)



def _inject_smooth_scroll(st: Any) -> None:
    """Scroll to section after nav click. Uses parent document (Streamlit main pane)."""
    target = st.session_state.pop("iidatech_scroll_to", None)
    if not target:
        return
    # Escape for JS string
    safe = str(target).replace("\\", "\\\\").replace("'", "")
    components.html(
        f"""
        <script>
        (function() {{
          const id = '{safe}';
          const doc = window.parent.document;
          function go(attempt) {{
            const el = doc.getElementById(id) || doc.getElementById(id + '-wrap');
            if (el) {{
              el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
              return;
            }}
            if (attempt < 20) setTimeout(() => go(attempt + 1), 120);
          }}
          go(0);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def render_marketing_landing_page(
    st: Any,
    *,
    on_workspace: StartFn,
    hash_password: Callable[[str], str],
    load_users: Callable[[], dict],
    save_users: Callable[[dict], None],
) -> None:
    def _show_start() -> None:
        st.session_state["iidatech_show_start_form"] = True
        st.rerun()

    inject_styles(st)
    render_nav_bar(st, on_start=_show_start)
    _inject_smooth_scroll(st)
    render_start_form(
        st,
        on_workspace=on_workspace,
        hash_password=hash_password,
        load_users=load_users,
        save_users=save_users,
    )
    _hero(st, on_workspace=on_workspace, on_start=_show_start)
    _section_trust(st)
    _section_problem(st)
    _section_solution(st, on_workspace=on_workspace)
    _section_reviews(st)
    _section_buy(st, on_workspace=on_workspace)
    _section_services(st, on_workspace=on_workspace, on_start=_show_start)
    _section_how(st, on_workspace=on_workspace, on_start=_show_start)
    _section_workforce(st, on_workspace=on_workspace)
    _section_samples(st, on_workspace=on_workspace)
    _section_work(st, on_workspace=on_workspace)
    _section_cta_banner(st, on_start=_show_start, on_workspace=on_workspace)
    _section_contact(st)
