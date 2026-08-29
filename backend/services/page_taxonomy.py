"""Classify website paths into marketing / demo / app parts."""
from __future__ import annotations

from urllib.parse import parse_qs, urlparse

DEMO_MARKER = "demo_readonly"

APP_PARTS: tuple[tuple[str, str], ...] = (
    ("/app/research", "Research"),
    ("/app/plan", "Plan"),
    ("/app/team", "Employee OS"),
    ("/app/mentor", "Mentor"),
    ("/app/audit", "GAUGE audit"),
    ("/app/onboarding", "Org Memory"),
    ("/app/automation", "Automation"),
    ("/app/dashboard", "Dashboard"),
    ("/app/projects", "Projects"),
    ("/app/saved", "Saved files"),
    ("/app/profile", "Profile"),
    ("/app/workspace", "Workspace"),
    ("/app/crm", "CRM"),
    ("/app/analytics", "Analytics"),
)

MARKETING_PARTS = {
    "/": "Home",
    "/about": "About",
    "/pricing": "Pricing",
    "/how-it-works": "How it works",
    "/partners": "Partners",
    "/login": "Login",
    "/contact": "Contact",
}


def normalize_path(path: str, href: str = "") -> str:
    raw = (path or "/").strip() or "/"
    if not raw.startswith("/"):
        raw = "/" + raw
    query = ""
    if "?" in raw:
        raw, query = raw.split("?", 1)
    raw = raw.split("#")[0] or "/"
    href_query = ""
    if href:
        try:
            parsed = urlparse(href)
            href_query = parsed.query or ""
            if parsed.path and raw == "/":
                raw = parsed.path or raw
        except Exception:
            href_query = ""
    params = parse_qs(query or href_query)
    extras: list[str] = []
    project = (params.get("project") or [""])[0]
    if project == DEMO_MARKER or DEMO_MARKER in (query or "") or DEMO_MARKER in (href or ""):
        extras.append(f"project={DEMO_MARKER}")
    if extras:
        return f"{raw}?{'&'.join(extras)}"
    return raw


def is_demo_hit(path: str, href: str = "", is_demo: bool = False) -> bool:
    if is_demo:
        return True
    blob = f"{path} {href}"
    return DEMO_MARKER in blob or "/login?mode=demo" in blob


def page_part(path: str) -> str:
    base = (path or "/").split("?")[0] or "/"
    if base in MARKETING_PARTS:
        return MARKETING_PARTS[base]
    for prefix, label in APP_PARTS:
        if base == prefix or base.startswith(prefix + "/"):
            return label
    if base.startswith("/app"):
        return "Workspace"
    return base.strip("/") or "Home"


def classify_page(path: str, href: str = "", is_demo: bool = False) -> dict[str, str]:
    norm = normalize_path(path, href)
    demo = is_demo_hit(norm, href, is_demo)
    base = norm.split("?")[0] or "/"
    part = page_part(norm)
    if demo and base.startswith("/app"):
        area = "demo"
        label = f"Demo · {part}"
    elif base.startswith("/app"):
        area = "app"
        label = part
    elif base in MARKETING_PARTS or not base.startswith("/app"):
        area = "marketing"
        label = part
    else:
        area = "other"
        label = part
    return {"path": norm, "area": area, "part": part, "label": label}
