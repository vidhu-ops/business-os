"""Mini GAUGE â short intake + public URL context + scored health snapshot."""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from backend.services.mini_industry_position import (
    MINI_INDUSTRY_VERTICALS,
    enrich_audit_with_industry_position,
    industry_json_schema_hint,
    resolve_industry_from_draft,
)
from iidatech.services.gauge_intake import GAUGE_BUSINESS_TYPES, gauge_type_label

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SCRIPT_RE = re.compile(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>")


def _clean(value: Any, *, limit: int = 4000) -> str:
    return _WS_RE.sub(" ", str(value or "")).strip()[:limit]


def _num(value: Any) -> str:
    text = _clean(value, limit=80)
    if not text:
        return ""
    digits = re.sub(r"[^\d.\-]", "", text.replace(",", ""))
    return digits or text


def _safe_float(value: Any) -> float | None:
    try:
        cleaned = re.sub(r"[^\d.\-]", "", str(value or "").replace(",", ""))
        if not cleaned:
            return None
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def _normalize_url(raw: str) -> str:
    text = _clean(raw, limit=500)
    if not text:
        return ""
    if not re.match(r"^https?://", text, re.I):
        text = "https://" + text
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return text


def collect_public_urls(draft: dict[str, Any]) -> list[tuple[str, str]]:
    """Return labeled URLs from mini draft (website + social + other)."""
    items: list[tuple[str, str]] = []
    website = _normalize_url(str(draft.get("website") or ""))
    if website:
        items.append(("Website", website))
    linkedin = _normalize_url(str(draft.get("linkedin_url") or ""))
    if linkedin:
        items.append(("LinkedIn", linkedin))
    instagram = _normalize_url(str(draft.get("instagram_url") or ""))
    if instagram:
        items.append(("Instagram", instagram))
    other_raw = str(draft.get("other_urls") or "")
    for line in other_raw.replace(",", "\n").splitlines():
        url = _normalize_url(line)
        if url and url not in {u for _, u in items}:
            items.append(("Other", url))
    return items[:8]


def fetch_url_snippet(url: str, *, limit: int = 2800) -> str:
    """Best-effort public page text for LLM context (no JS rendering)."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            raw = resp.read(220_000)
            charset = "utf-8"
            ctype = str(resp.headers.get("Content-Type") or "")
            if "charset=" in ctype.lower():
                charset = ctype.lower().split("charset=", 1)[1].split(";")[0].strip() or "utf-8"
            text = raw.decode(charset, errors="ignore")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return ""
    except Exception:
        return ""

    text = _SCRIPT_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def gather_url_context(draft: dict[str, Any]) -> dict[str, Any]:
    urls = collect_public_urls(draft)
    snippets: list[dict[str, str]] = []
    for label, url in urls:
        snippet = fetch_url_snippet(url)
        snippets.append(
            {
                "label": label,
                "url": url,
                "snippet": snippet,
                "fetched": "yes" if snippet else "no",
            }
        )
    lines = []
    for row in snippets:
        if row["snippet"]:
            lines.append(f"[{row['label']}] {row['url']}\n{row['snippet']}")
        else:
            lines.append(
                f"[{row['label']}] {row['url']}\n"
                "(Could not fetch page text â research this URL from public web knowledge.)"
            )
    return {
        "urls": [{"label": l, "url": u} for l, u in urls],
        "snippets": snippets,
        "context_text": "\n\n".join(lines)[:14000],
        "fetched_count": sum(1 for s in snippets if s.get("fetched") == "yes"),
    }


MINI_BUSINESS_STAGES: list[dict[str, str]] = [
    {"id": "pre_revenue", "label": "Pre-revenue / validating"},
    {"id": "early", "label": "Early revenue (< ₹10L / $12k MRR)"},
    {"id": "growing", "label": "Growing (traction, not yet scaled)"},
    {"id": "scaling", "label": "Scaling (repeatable GTM)"},
    {"id": "mature", "label": "Mature / established"},
]

MINI_REVENUE_MODELS: list[dict[str, str]] = [
    {"id": "subscription", "label": "Subscription / SaaS"},
    {"id": "transaction", "label": "Transaction / marketplace"},
    {"id": "services", "label": "Services / project fees"},
    {"id": "product", "label": "Product / D2C sales"},
    {"id": "hybrid", "label": "Hybrid"},
    {"id": "other", "label": "Other"},
]


def _stage_label(stage_id: str) -> str:
    for row in MINI_BUSINESS_STAGES:
        if row.get("id") == stage_id:
            return str(row.get("label") or stage_id)
    return stage_id.replace("_", " ").title() if stage_id else ""


def _revenue_model_label(model_id: str) -> str:
    for row in MINI_REVENUE_MODELS:
        if row.get("id") == model_id:
            return str(row.get("label") or model_id)
    return model_id.replace("_", " ").title() if model_id else ""


def _build_mini_intake_context(draft: dict[str, Any]) -> str:
    lines: list[str] = []
    mapping: list[tuple[str, Any]] = [
        ("Target customer / ICP", "target_customer"),
        ("Business stage", lambda d: _stage_label(_clean(d.get("business_stage"), limit=40))),
        ("Years operating", "years_operating"),
        ("Revenue model", lambda d: _revenue_model_label(_clean(d.get("revenue_model"), limit=40))),
        ("Main competitors", "competitors"),
        ("Differentiation", "differentiation"),
        ("Biggest challenge", "biggest_challenge"),
        ("12-month growth priority", "growth_goal_12m"),
    ]
    for label, key in mapping:
        if callable(key):
            value = key(draft)
        else:
            value = _clean(draft.get(key), limit=2000)
        if value:
            lines.append(f"- {label}: {value}")
    return "\n".join(lines)


def validate_mini_draft(draft: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _clean(draft.get("company_name"), limit=200):
        errors.append("Enter your company name.")
    if not _clean(draft.get("geography"), limit=200):
        errors.append("Enter your primary market / geography.")
    vertical = _clean(draft.get("industry_vertical"), limit=40)
    custom_industry = _clean(draft.get("industry"), limit=200)
    if not vertical and not custom_industry:
        errors.append("Select your industry so we can benchmark you against peers.")
    elif vertical == "other" and not custom_industry:
        errors.append("Describe your industry when selecting Other.")
    urls = collect_public_urls(draft)
    has_signal = bool(
        urls
        or _clean(draft.get("description"), limit=100)
        or _num(draft.get("monthly_revenue"))
        or _num(draft.get("active_customers"))
        or _clean(draft.get("target_customer"), limit=40)
        or _clean(draft.get("competitors"), limit=40)
        or _clean(draft.get("differentiation"), limit=40)
    )
    if not has_signal:
        errors.append(
            "Add a website, LinkedIn, Instagram, other URL, short description, or a quick metric."
        )
    gauge_type = _clean(draft.get("gauge_type") or "other", limit=40).lower()
    allowed = {t.get("id") for t in GAUGE_BUSINESS_TYPES if isinstance(t, dict)}
    if allowed and gauge_type not in allowed:
        errors.append("Select a valid business type.")
    return errors


def profile_from_mini_draft(
    draft: dict[str, Any], *, url_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    gauge_type = _clean(draft.get("gauge_type") or "other", limit=40).lower() or "other"
    company_name = _clean(draft.get("company_name"), limit=200)
    website = ""
    for label, url in collect_public_urls(draft):
        if label == "Website":
            website = url
            break
    if not website:
        website = _normalize_url(str(draft.get("website") or ""))

    public_links = "; ".join(f"{label}: {url}" for label, url in collect_public_urls(draft))
    description = _clean(draft.get("description"), limit=4000)
    if not description and company_name:
        description = f"{gauge_type_label(gauge_type)} business operating as {company_name}."

    founder_context = _build_mini_intake_context(draft)
    notes_parts = [
        "MINI GAUGE intake (short form).",
        _clean(draft.get("gauge_notes"), limit=4000),
    ]
    if founder_context:
        notes_parts.append("Founder context (industry & positioning):\n" + founder_context)
    ctx = url_context or {}
    if ctx.get("context_text"):
        notes_parts.append("Public URL / social reads:\n" + str(ctx["context_text"]))

    monthly_rev = _num(draft.get("monthly_revenue"))
    monthly_cost = _num(draft.get("monthly_costs"))
    annual = ""
    if monthly_rev:
        try:
            annual = str(round(float(monthly_rev) * 12, 2))
        except (TypeError, ValueError):
            annual = ""

    months = _num(draft.get("months_in_operation"))
    years = _num(draft.get("years_operating"))
    if not months and years:
        try:
            months = str(round(float(years) * 12, 1))
        except (TypeError, ValueError):
            months = years
    years_operating = years
    if not years_operating and months:
        try:
            years_operating = str(round(float(months) / 12, 1))
        except (TypeError, ValueError):
            years_operating = ""

    plan_forward = {
        "biggest_bottleneck": _clean(draft.get("biggest_challenge"), limit=2000),
        "priority_12_months": _clean(draft.get("growth_goal_12m"), limit=2000),
        "why_customers_choose": _clean(draft.get("differentiation"), limit=2000),
        "competitive_threat": _clean(draft.get("competitors"), limit=2000),
    }

    return {
        "business_stage": "existing",
        "gauge_business_type": gauge_type,
        "gauge_business_type_label": gauge_type_label(gauge_type),
        "company_name": company_name,
        "website": website,
        "public_links": public_links[:2000],
        "business_description": description,
        "industry": resolve_industry_from_draft(draft, fallback_type_label=gauge_type_label(gauge_type)),
        "industry_vertical": _clean(draft.get("industry_vertical"), limit=40),
        "geography": _clean(draft.get("geography"), limit=200),
        "months_in_operation": months,
        "years_operating": years_operating,
        "target_customer": _clean(draft.get("target_customer"), limit=1000),
        "operating_stage": _clean(draft.get("business_stage"), limit=80),
        "business_stage_label": _stage_label(_clean(draft.get("business_stage"), limit=40)),
        "revenue_model": _revenue_model_label(_clean(draft.get("revenue_model"), limit=40)),
        "currency": _clean(draft.get("currency") or "USD", limit=12) or "USD",
        "monthly_revenue": monthly_rev,
        "monthly_costs": monthly_cost,
        "annual_revenue": annual,
        "monthly_opex": monthly_cost,
        "active_customers": _num(draft.get("active_customers")),
        "customer_churn_pct": "",
        "employees_ft": _num(draft.get("team_size")),
        "main_competitors": _clean(draft.get("competitors"), limit=1000),
        "gauge_notes": "\n\n".join(p for p in notes_parts if p).strip()[:12000],
        "plan_purpose": "Internal strategy",
        "target_revenue_year_3": "",
        "funding_amount_needed": "",
        "growth_goal_12_24m": _clean(draft.get("growth_goal_12m"), limit=2000),
        "gauge_checklist_state": {},
        "gauge_checklist_summary": "Mini Gauge â checklist skipped (upgrade for full GAUGE).",
        "gauge_checklist_prompt": (
            "Mini Gauge mode: no full checklist. Score from founder context (ICP, stage, competitors, "
            "differentiation, growth priority), optional metrics, and public URL/social reads. "
            "Benchmark against named competitors and industry norms in the stated geography."
        ),
        "plan_forward": plan_forward,
        "intake_source": "mini_gauge",
        "mini_gauge": True,
    }


def _audit_json_schema_hint() -> str:
    return (
        "Return ONLY one JSON object with keys: "
        "overall_score (0-100 int), overall_label, overall_summary, plain_english_read, "
        "market_position, categories (exactly 6 objects with name/score/status/summary for "
        "Financials, Customers, Sales & Marketing, Operations, Product & Team, Competitive Position), "
        "key_metrics (5 objects with label/value/benchmark/assessment), top_actions "
        "(4 objects with title/why/impact/effort), industry_landscape, risks (3-5 strings), "
        "sources (urls or publication names used). "
        + industry_json_schema_hint()
        + " status must be strong|watch|risk. Do not invent precise financials that were not provided; "
        "infer directional health from public presence + stated metrics. Never return all zeros "
        "unless the company truly has no usable signal."
    )


def _build_mini_research_prompt(profile: dict[str, Any], url_context: dict[str, Any]) -> str:
    company = profile.get("company_name") or "Company"
    links = profile.get("public_links") or ""
    fetched = url_context.get("context_text") or ""
    return (
        f"You are producing a Mini GAUGE business health audit for {company}.\n"
        f"Geography: {profile.get('geography')}\n"
        f"Industry / type: {profile.get('industry')} / {profile.get('gauge_business_type_label')}\n"
        f"Website: {profile.get('website')}\n"
        f"Public links: {links}\n"
        f"Description: {profile.get('business_description')}\n"
        f"Monthly revenue (if given): {profile.get('monthly_revenue') or 'not provided'}\n"
        f"Active customers (if given): {profile.get('active_customers') or 'not provided'}\n"
        f"Team size (if given): {profile.get('employees_ft') or 'not provided'}\n"
        f"Years operating: {profile.get('years_operating') or 'not provided'}\n"
        f"Target customer / ICP: {profile.get('target_customer') or 'not provided'}\n"
        f"Business stage: {profile.get('business_stage_label') or profile.get('operating_stage') or 'not provided'}\n"
        f"Revenue model: {profile.get('revenue_model') or 'not provided'}\n"
        f"Main competitors: {profile.get('main_competitors') or 'not provided'}\n"
        f"Differentiation: {(profile.get('plan_forward') or {}).get('why_customers_choose') or 'not provided'}\n"
        f"Biggest challenge: {(profile.get('plan_forward') or {}).get('biggest_bottleneck') or 'not provided'}\n"
        f"12-month growth priority: {profile.get('growth_goal_12_24m') or 'not provided'}\n"
        f"Currency: {profile.get('currency')}\n\n"
        f"FETCHED PAGE TEXT (may be partial; social sites often block):\n{fetched[:9000]}\n\n"
        "Research the company from the open web using the name and URLs above. "
        f"SELECTED INDUSTRY FOR BENCHMARKING (mandatory): {profile.get('industry')}\n\n"
        "Compare this company vs named competitors AND typical players in the selected industry/geography. "
        "The industry_position block must state clearly where they stand (tier + percentile band + vs_industry table). "
        "Write a real diagnostic: what the company appears to do, where it sits in the market, "
        "how strong the public presence looks, what is missing, and scored categories.\n\n"
        + _audit_json_schema_hint()
    )


def _parse_audit_payload(raw: Any, profile: dict[str, Any] | None = None) -> dict[str, Any] | None:
    from iidatech.services.gauge_audit import (
        extract_json_object,
        normalize_gauge_audit,
        salvage_json_object,
    )

    parsed = raw
    if isinstance(raw, str):
        clean = extract_json_object(raw)
        try:
            parsed = json.loads(clean)
        except Exception:
            parsed = salvage_json_object(clean)
    if not isinstance(parsed, dict):
        return None
    audit = normalize_gauge_audit(parsed)
    # Reject worthless all-zero checklist-style dumps when we clearly had company identity.
    scores = [int(c.get("score") or 0) for c in (audit.get("categories") or [])]
    if scores and max(scores) == 0 and sum(scores) == 0:
        return None
    if isinstance(parsed, dict) and parsed.get("industry_position"):
        audit["industry_position"] = parsed.get("industry_position")
    if profile:
        audit = enrich_audit_with_industry_position(audit, profile)
    return audit


def run_mini_audit_via_perplexity(
    profile: dict[str, Any], url_context: dict[str, Any]
) -> dict[str, Any] | None:
    try:
        from iidatech.evidence_bank.perplexity_client import call_perplexity_json, perplexity_enabled

        if not perplexity_enabled():
            return None
        prompt = _build_mini_research_prompt(profile, url_context)
        api = call_perplexity_json(prompt, timeout=90)
        if api.get("error"):
            return None
        parsed = api.get("parsed") or api.get("json")
        if not isinstance(parsed, dict):
            content = api.get("raw_content") or api.get("text") or ""
            audit = _parse_audit_payload(content, profile)
        else:
            audit = _parse_audit_payload(parsed, profile)
        if not audit:
            return None
        audit["_route"] = f"perplexity:{api.get('model') or 'sonar'}"
        audit["_mini"] = True
        audit["_market_context_used"] = True
        citations = list(api.get("citations") or [])
        if citations:
            existing = list(audit.get("sources") or [])
            for c in citations[:8]:
                s = str(c)[:120]
                if s and s not in existing:
                    existing.append(s)
            audit["sources"] = existing[:8]
        return audit
    except Exception:
        return None


def run_mini_audit_via_llm(
    profile: dict[str, Any], url_context: dict[str, Any], market_context: str
) -> dict[str, Any] | None:
    from iidatech.services.gauge_audit import GAUGE_AUDIT_SYSTEM, build_gauge_audit_user_prompt

    try:
        from iidatech.llm.text_request import llm_text_request

        prompt = build_gauge_audit_user_prompt(profile, market_context=market_context)
        prompt = (
            "MODE: Mini GAUGE. Use company identity + public URLs + any fetched text. "
            "Produce a real scored audit. Do not return all-zero checklist scores.\n\n"
            + prompt
            + "\n\n"
            + _audit_json_schema_hint()
        )
        text, route = llm_text_request(prompt, GAUGE_AUDIT_SYSTEM, max_tokens=4096, temperature=0.15)
        if not text or not str(text).strip():
            return None
        audit = _parse_audit_payload(text, profile)
        if not audit:
            return None
        audit["_route"] = route
        audit["_mini"] = True
        if market_context:
            audit["_market_context_used"] = True
        return audit
    except Exception:
        return None


def _status_from_score(score: int) -> str:
    if score >= 70:
        return "strong"
    if score < 40:
        return "risk"
    return "watch"


def mini_signal_fallback(
    profile: dict[str, Any], url_context: dict[str, Any]
) -> dict[str, Any]:
    """Signal-based mini audit when LLM/Perplexity are unavailable â never checklist zeros."""
    company = profile.get("company_name") or "Your business"
    geo = profile.get("geography") or "your market"
    industry = profile.get("industry") or profile.get("gauge_business_type_label") or "business"
    desc = str(profile.get("business_description") or "")
    urls = url_context.get("urls") or []
    snippets = url_context.get("snippets") or []
    fetched_count = int(url_context.get("fetched_count") or 0)
    has_site = any(u.get("label") == "Website" for u in urls)
    has_li = any(u.get("label") == "LinkedIn" for u in urls)
    has_ig = any(u.get("label") == "Instagram" for u in urls)
    rev = _safe_float(profile.get("monthly_revenue"))
    customers = _safe_float(profile.get("active_customers"))
    team = _safe_float(profile.get("employees_ft"))
    costs = _safe_float(profile.get("monthly_costs"))
    target_customer = str(profile.get("target_customer") or "")
    competitors = str(profile.get("main_competitors") or "")
    differentiation = str((profile.get("plan_forward") or {}).get("why_customers_choose") or "")
    growth_goal = str(profile.get("growth_goal_12_24m") or "")

    blob = " ".join(str(s.get("snippet") or "") for s in snippets).lower()
    blob += " " + desc.lower() + " " + target_customer.lower() + " " + competitors.lower() + " " + differentiation.lower()

    def clamp(n: int) -> int:
        return max(18, min(88, int(n)))

    financials = 28
    if rev is not None:
        financials += 28
        if rev >= 10000:
            financials += 8
        if rev >= 50000:
            financials += 6
    if costs is not None:
        financials += 10
    if rev and costs and rev > 0:
        margin = (rev - costs) / rev
        if margin >= 0.2:
            financials += 8
        elif margin < 0:
            financials -= 10

    customers_score = 26
    if customers is not None:
        customers_score += 30
        if customers >= 50:
            customers_score += 8
        if customers >= 200:
            customers_score += 6
    if len(target_customer) > 12:
        customers_score += 10
    if any(k in blob for k in ("customer", "client", "user", "subscriber", "buyer")):
        customers_score += 8

    sales = 24
    if has_site:
        sales += 18
    if has_li:
        sales += 12
    if has_ig:
        sales += 8
    if fetched_count:
        sales += min(16, fetched_count * 8)
    if any(k in blob for k in ("pricing", "book a demo", "get started", "contact", "signup", "sign up")):
        sales += 10

    operations = 30
    if team is not None:
        operations += 18
        if team >= 3:
            operations += 6
    if profile.get("months_in_operation"):
        operations += 8
    if any(k in blob for k in ("process", "workflow", "support", "onboarding", "delivery")):
        operations += 8

    product = 28
    if len(desc) > 40:
        product += 16
    if len(desc) > 120:
        product += 8
    if any(k in blob for k in ("product", "platform", "solution", "service", "feature", "research", "plan")):
        product += 12
    if team is not None:
        product += 6

    competitive = 26
    if has_site or has_li:
        competitive += 14
    if fetched_count:
        competitive += 10
    if profile.get("main_competitors"):
        competitive += 16
    if len(differentiation) > 20:
        competitive += 12
    if growth_goal:
        competitive += 6
    if any(k in blob for k in ("competitor", "versus", "alternative", "market", "industry")):
        competitive += 8
    if len(urls) >= 2:
        competitive += 8

    categories = [
        {"name": "Financials", "score": clamp(financials), "status": "", "summary": ""},
        {"name": "Customers", "score": clamp(customers_score), "status": "", "summary": ""},
        {"name": "Sales & Marketing", "score": clamp(sales), "status": "", "summary": ""},
        {"name": "Operations", "score": clamp(operations), "status": "", "summary": ""},
        {"name": "Product & Team", "score": clamp(product), "status": "", "summary": ""},
        {"name": "Competitive Position", "score": clamp(competitive), "status": "", "summary": ""},
    ]
    summaries = {
        "Financials": (
            f"Monthly revenue {'stated at ' + str(rev) if rev is not None else 'not stated'}; "
            f"{'costs provided' if costs is not None else 'costs unknown'}."
        ),
        "Customers": (
            (f"ICP: {target_customer[:100]}." if target_customer else "Target customer not stated.")
            + f" Active customers {'stated at ' + str(int(customers)) if customers is not None else 'not stated'}."
        ),
        "Sales & Marketing": (
            f"Public presence: website={'yes' if has_site else 'no'}, LinkedIn={'yes' if has_li else 'no'}, "
            f"Instagram={'yes' if has_ig else 'no'}; fetched {fetched_count}/{len(urls)} URLs."
        ),
        "Operations": (
            f"Team size {'= ' + str(int(team)) if team is not None else 'unknown'}; "
            "operating cadence not fully documented in mini intake."
        ),
        "Product & Team": (
            "Offer description "
            + ("looks usable for positioning." if len(desc) > 40 else "is thin â add sharper product/service detail.")
        ),
        "Competitive Position": (
            (f"Competitors named: {competitors[:120]}." if competitors else f"In {geo}, competitor names were not provided.")
            + (" Differentiation stated." if differentiation else " Add sharper differentiation for a tighter industry read.")
        ),
    }
    for cat in categories:
        cat["status"] = _status_from_score(cat["score"])
        cat["summary"] = summaries[cat["name"]]

    overall = int(round(sum(c["score"] for c in categories) / len(categories)))
    if overall >= 70:
        label = "Promising public signal"
        summary = f"{company} shows enough public + metric signal for a constructive mini read in {geo}."
    elif overall >= 45:
        label = "Early but actionable"
        summary = f"{company} has a usable footprint; tighten tracking and proof points before scaling bets."
    else:
        label = "Thin but directional"
        summary = f"{company} needs stronger public proof and operating metrics â this mini score is a starting baseline."

    plain = (
        f"{company} scores about {overall}/100 on this Mini GAUGE snapshot for {industry} in {geo}. "
        f"We used {len(urls)} public link(s) ({fetched_count} fetched) plus any metrics you entered. "
        "Full GAUGE adds checklist depth, forward questions, and a plan build."
    )

    key_metrics: list[dict[str, str]] = []
    if rev is not None:
        key_metrics.append(
            {
                "label": "Monthly revenue",
                "value": str(rev),
                "benchmark": "Stage-dependent",
                "assessment": "stated",
            }
        )
    if customers is not None:
        key_metrics.append(
            {
                "label": "Active customers",
                "value": str(int(customers)),
                "benchmark": "Track retention next",
                "assessment": "stated",
            }
        )
    if team is not None:
        key_metrics.append(
            {
                "label": "Team size",
                "value": str(int(team)),
                "benchmark": "Role clarity matters more than headcount",
                "assessment": "stated",
            }
        )
    key_metrics.append(
        {
            "label": "Public URLs reviewed",
            "value": str(len(urls)),
            "benchmark": "Website + LinkedIn recommended",
            "assessment": "above" if len(urls) >= 2 else "below",
        }
    )
    key_metrics.append(
        {
            "label": "Pages fetched",
            "value": f"{fetched_count}/{len(urls)}",
            "benchmark": "Social sites often block bots",
            "assessment": "inline" if fetched_count else "below",
        }
    )
    while len(key_metrics) < 5:
        key_metrics.append(
            {
                "label": "Full GAUGE unlock",
                "value": "checklist + forward plan",
                "benchmark": "Upgrade path",
                "assessment": "unknown",
            }
        )

    weakest = sorted(categories, key=lambda c: c["score"])[:2]
    top_actions = [
        {
            "title": f"Strengthen {cat['name']}",
            "why": cat["summary"][:160],
            "impact": "high",
            "effort": "medium",
        }
        for cat in weakest
    ]
    if not has_site:
        top_actions.append(
            {
                "title": "Publish a clear company website",
                "why": "Buyers and partners need a durable public explanation of what you sell.",
                "impact": "high",
                "effort": "medium",
            }
        )
    if rev is None:
        top_actions.append(
            {
                "title": "Track monthly revenue and contribution margin",
                "why": "Without a revenue pulse, category scores stay directional only.",
                "impact": "high",
                "effort": "low",
            }
        )
    while len(top_actions) < 4:
        top_actions.append(
            {
                "title": "Run full GAUGE with checklist",
                "why": "Mini is a snapshot; the full instrument maps operating gaps item-by-item.",
                "impact": "medium",
                "effort": "medium",
            }
        )

    sources = [u.get("url") for u in urls if u.get("url")]
    return {
        "overall_score": overall,
        "overall_label": label,
        "overall_summary": summary,
        "plain_english_read": plain,
        "market_position": (
            f"{company} in {geo} â public presence and stated metrics drive this mini read; "
            "named competitor intel would sharpen positioning."
        ),
        "categories": categories,
        "key_metrics": key_metrics[:5],
        "top_actions": top_actions[:4],
        "industry_landscape": (
            f"{industry} in {geo}: buyers reward clear offer, proof, and measurable operating discipline."
        ),
        "risks": [
            "Mini intake lacks full operating checklist",
            "Social/profile pages may not yield fetchable text",
            "Scores are directional until full GAUGE metrics are added",
        ],
        "sources": sources[:8],
        "_fallback": True,
        "_route": "mini_signal_fallback",
        "_mini": True,
    }


def enrich_market_context_with_urls(profile: dict[str, Any]) -> str:
    """Extend Perplexity snapshot with social / public links when available."""
    from iidatech.services.gauge_audit import fetch_market_context_for_audit

    base = fetch_market_context_for_audit(profile)
    links = _clean(profile.get("public_links"), limit=1500)
    if not links:
        return base
    try:
        from iidatech.evidence_bank.perplexity_client import call_perplexity_json, perplexity_enabled

        if not perplexity_enabled():
            return base
        prompt = (
            "Quick public presence read for a mini business health audit.\n"
            f"Company: {profile.get('company_name')}\n"
            f"Website: {profile.get('website')}\n"
            f"Public links: {links}\n"
            f"Industry: {profile.get('industry')}\n"
            f"Geography: {profile.get('geography')}\n"
            'Return JSON: {"presence_summary":"...","positioning_clues":["..."],'
            '"risks_or_gaps":["..."],"what_to_verify":["..."]}'
        )
        api = call_perplexity_json(prompt, timeout=45)
        if api.get("error"):
            return base
        parsed = api.get("parsed") or api.get("json")
        extra = (
            json.dumps(parsed, ensure_ascii=False)[:4000]
            if isinstance(parsed, dict)
            else str(api.get("text") or "")[:4000]
        )
        if not extra:
            return base
        if base:
            return (base + "\n\nPUBLIC_PRESENCE:\n" + extra)[:9000]
        return extra[:6000]
    except Exception:
        return base


def _attach_url_meta(audit: dict[str, Any], url_context: dict[str, Any]) -> dict[str, Any]:
    if url_context.get("urls"):
        audit["_urls_considered"] = url_context["urls"]
        audit["_urls_fetched"] = [
            {"label": s["label"], "url": s["url"], "fetched": s["fetched"]}
            for s in url_context.get("snippets") or []
        ]
        sources = list(audit.get("sources") or [])
        for u in url_context["urls"]:
            url = str(u.get("url") or "")
            if url and url not in sources:
                sources.append(url)
        audit["sources"] = sources[:8]
    return audit


def run_mini_audit(draft: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    url_context = gather_url_context(draft)
    profile = profile_from_mini_draft(draft, url_context=url_context)

    # 1) Perplexity web research audit (best for URL-led mini)
    audit = run_mini_audit_via_perplexity(profile, url_context)

    # 2) OpenAI / configured LLM
    if not audit:
        market_context = enrich_market_context_with_urls(profile)
        audit = run_mini_audit_via_llm(profile, url_context, market_context)

    # 3) Signal fallback â never checklist zeros
    if not audit:
        audit = mini_signal_fallback(profile, url_context)

    audit = enrich_audit_with_industry_position(audit, profile)
    audit = _attach_url_meta(audit, url_context)
    audit["_mini"] = True
    return audit, profile, url_context


def mini_metadata() -> dict[str, Any]:
    return {
        "business_types": GAUGE_BUSINESS_TYPES,
        "fields": [
            "company_name",
            "geography",
            "gauge_type",
            "industry",
            "description",
            "target_customer",
            "business_stage",
            "years_operating",
            "revenue_model",
            "competitors",
            "differentiation",
            "biggest_challenge",
            "growth_goal_12m",
            "website",
            "linkedin_url",
            "instagram_url",
            "other_urls",
            "monthly_revenue",
            "active_customers",
            "team_size",
        ],
        "business_stages": MINI_BUSINESS_STAGES,
        "revenue_models": MINI_REVENUE_MODELS,
        "industry_verticals": MINI_INDUSTRY_VERTICALS,
        "upgrade_href": "/app/audit",
        "upgrade_label": "Unlock full GAUGE audit",
    }