"""GAUGE business health audit - score, market read, and plain-language guidance."""
from __future__ import annotations

import json
import re
from typing import Any, Callable

from iidatech.services.gauge_intake import (
    gauge_category_scores,
    gauge_checklist_prompt_lines,
    gauge_type_label,
)

TextRequestFn = Callable[[str, str, int, float], tuple[str, str]]

GAUGE_CATEGORY_NAMES = [
    "Financials",
    "Customers",
    "Sales & Marketing",
    "Operations",
    "Product & Team",
    "Competitive Position",
]

GAUGE_AUDIT_SYSTEM = (
    "You are a business analyst producing a diagnostic audit for an operating company. "
    "Be direct and specific. If data is thin, say so plainly rather than inventing numbers. "
    "Return ONLY one valid JSON object - no markdown fences, no commentary outside JSON."
)


def salvage_json_object(raw: str) -> dict[str, Any] | None:
    text = str(raw or "").strip()
    if not text:
        return None
    stack: list[str] = []
    in_str = False
    esc = False
    for ch in text:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]" and stack:
            stack.pop()
    repaired = text
    if in_str:
        repaired += '"'
    repaired = re.sub(r",\s*$", "", repaired)
    for ch in reversed(stack):
        repaired += "}" if ch == "{" else "]"
    try:
        parsed = json.loads(repaired)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def extract_json_object(raw: str) -> str:
    text = str(raw or "").strip()
    text = re.sub(r"^```json\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    first = text.find("{")
    last = text.rfind("}")
    if first >= 0 and last > first:
        return text[first : last + 1]
    if first >= 0:
        return text[first:]
    return text


def build_gauge_audit_user_prompt(profile: dict[str, Any], *, market_context: str = "") -> str:
    checklist_prompt = profile.get("gauge_checklist_prompt") or gauge_checklist_prompt_lines(
        profile.get("gauge_business_type") or "other",
        profile.get("gauge_checklist_state") or {},
    )
    identity_lines = []
    for label, key in (
        ("Company name", "company_name"),
        ("Website", "website"),
        ("Other public links", "public_links"),
    ):
        value = str(profile.get(key) or "").strip()
        if value:
            identity_lines.append(f"{label}: {value}")
    identity_block = "\n".join(identity_lines) or (
        "Not provided - rely on internal data and general industry knowledge only."
    )
    metrics = {
        "Monthly revenue": profile.get("monthly_revenue"),
        "Monthly costs": profile.get("monthly_costs"),
        "Active customers": profile.get("active_customers"),
        "Monthly churn %": profile.get("customer_churn_pct"),
        "Months in operation": profile.get("months_in_operation"),
        "Team size": profile.get("employees_ft"),
        "Main competitors": profile.get("main_competitors"),
        "Geography": profile.get("geography"),
        "Currency": profile.get("currency"),
    }
    metrics_lines = "\n".join(f"{k}: {v}" for k, v in metrics.items() if v) or "None provided"
    forward = profile.get("plan_forward") or {}
    forward_lines = "\n".join(
        f"{k.replace('_', ' ').title()}: {v}"
        for k, v in forward.items()
        if v and k != "business_stage"
    )
    notes = str(profile.get("gauge_notes") or "")[:8000]
    market_block = f"\n\nMARKET / WEB CONTEXT (if any):\n{market_context[:6000]}\n" if market_context else ""
    return (
        f"Business type: {profile.get('gauge_business_type_label') or gauge_type_label(profile.get('gauge_business_type') or 'other')}\n\n"
        f"COMPANY IDENTITY:\n{identity_block}\n\n"
        f"CHECKLIST (what the owner says is / isn't in place):\n{checklist_prompt}\n\n"
        f"QUICK METRICS:\n{metrics_lines}\n\n"
        f"FORWARD PLAN CONTEXT:\n{forward_lines or 'Not provided'}\n\n"
        f"FREE-FORM NOTES / PASTED DATA:\n{notes}"
        f"{market_block}\n\n"
        "Return JSON with keys: overall_score, overall_label, overall_summary, plain_english_read, "
        "market_position, categories (6 items with name/score/status/summary), key_metrics (5), "
        "top_actions (4), industry_landscape, risks (3), sources."
    )


def _status_from_score(score: int) -> str:
    if score >= 70:
        return "strong"
    if score < 40:
        return "risk"
    return "watch"


def _safe_float(value: Any) -> float | None:
    try:
        cleaned = re.sub(r"[^\d.\-]", "", str(value or "").replace(",", ""))
        if not cleaned:
            return None
        return float(cleaned)
    except (TypeError, ValueError):
        return None


def fallback_gauge_audit(profile: dict[str, Any]) -> dict[str, Any]:
    type_id = profile.get("gauge_business_type") or "other"
    checklist_state = profile.get("gauge_checklist_state") or {}
    cat_scores = gauge_category_scores(type_id, checklist_state)
    categories = []
    for name in GAUGE_CATEGORY_NAMES:
        score = int(cat_scores.get(name, 50))
        categories.append(
            {
                "name": name,
                "score": score,
                "status": _status_from_score(score),
                "summary": "Based on checklist items you marked in place.",
            }
        )
    overall = int(round(sum(c["score"] for c in categories) / max(len(categories), 1)))
    rev = _safe_float(profile.get("monthly_revenue"))
    cost = _safe_float(profile.get("monthly_costs"))
    margin_pct = round(100 * (rev - cost) / rev, 1) if rev and cost and rev > 0 else None
    churn = _safe_float(profile.get("customer_churn_pct"))
    company = profile.get("company_name") or "Your business"
    geo = profile.get("geography") or "your market"
    if overall >= 70:
        label, summary = "Solid operating base", f"{company} has most fundamentals tracked; focus on growth levers."
    elif overall >= 40:
        label, summary = "Work in progress", f"{company} runs but has gaps to close before scaling in {geo}."
    else:
        label, summary = "Needs fundamentals first", f"{company} is operating with thin visibility - fix tracking before big bets."
    plain = (
        f"You are at {overall}/100 overall. Strengthen the categories marked as gaps in your checklist, "
        f"then pursue your stated growth goal. Start with the highest-impact missing item."
    )
    market_position = f"In {geo}, you compete on execution and clarity of offer."
    if profile.get("main_competitors"):
        market_position = (
            f"You named competitors ({profile.get('main_competitors')}). "
            "Your position depends on differentiation and win/loss tracking."
        )
    key_metrics: list[dict[str, str]] = []
    if rev is not None:
        key_metrics.append({"label": "Monthly revenue", "value": str(rev), "benchmark": "Varies by stage", "assessment": "unknown"})
    if margin_pct is not None:
        assess = "above" if margin_pct >= 30 else "below" if margin_pct < 15 else "inline"
        key_metrics.append({"label": "Gross margin est.", "value": f"{margin_pct}%", "benchmark": "15-40% typical", "assessment": assess})
    if churn is not None:
        assess = "below" if churn > 5 else "above" if churn < 3 else "inline"
        key_metrics.append({"label": "Monthly churn", "value": f"{churn}%", "benchmark": "3-5% SMB SaaS", "assessment": assess})
    while len(key_metrics) < 5:
        key_metrics.append({"label": "Data gap", "value": "not provided", "benchmark": "Add operating metrics", "assessment": "unknown"})
    missing_cats = sorted(categories, key=lambda c: c["score"])[:2]
    top_actions = [
        {
            "title": f"Close {cat['name']} gaps",
            "why": f"Only {cat['score']}/100 on checklist - limits confident decisions.",
            "impact": "high",
            "effort": "medium",
        }
        for cat in missing_cats
    ]
    forward = profile.get("plan_forward") or {}
    if forward.get("priority_12_months"):
        top_actions.append(
            {
                "title": "Execute 12-month priority",
                "why": str(forward.get("priority_12_months"))[:120],
                "impact": "high",
                "effort": "medium",
            }
        )
    while len(top_actions) < 4:
        top_actions.append(
            {"title": "Review unit economics monthly", "why": "Prevents surprise cash or churn issues.", "impact": "medium", "effort": "low"}
        )
    return {
        "overall_score": overall,
        "overall_label": label,
        "overall_summary": summary,
        "plain_english_read": plain,
        "market_position": market_position,
        "categories": categories,
        "key_metrics": key_metrics[:5],
        "top_actions": top_actions[:4],
        "industry_landscape": (
            f"{profile.get('industry') or gauge_type_label(type_id)} in {geo} - "
            "buyers expect reliability; operators who measure win/loss grow faster."
        ),
        "risks": ["Thin operating data", "Unclear competitive edge", "Cash runway not tracked"],
        "sources": [],
        "_fallback": True,
    }


def normalize_gauge_audit(raw: dict[str, Any]) -> dict[str, Any]:
    categories = []
    for item in raw.get("categories") or []:
        if not isinstance(item, dict):
            continue
        score = max(0, min(100, int(item.get("score") or 0)))
        status = str(item.get("status") or _status_from_score(score))
        if status not in {"strong", "watch", "risk"}:
            status = _status_from_score(score)
        categories.append(
            {"name": str(item.get("name") or "Category"), "score": score, "status": status, "summary": str(item.get("summary") or "")[:200]}
        )
    while len(categories) < 6:
        categories.append(
            {"name": GAUGE_CATEGORY_NAMES[len(categories)], "score": 50, "status": "watch", "summary": "Insufficient detail to score precisely."}
        )
    overall = max(0, min(100, int(raw.get("overall_score") or 0)))
    if not raw.get("overall_score") and categories:
        overall = int(round(sum(c["score"] for c in categories) / len(categories)))
    return {
        "overall_score": overall,
        "overall_label": str(raw.get("overall_label") or "Business health read")[:80],
        "overall_summary": str(raw.get("overall_summary") or "")[:300],
        "plain_english_read": str(raw.get("plain_english_read") or raw.get("overall_summary") or "")[:600],
        "market_position": str(raw.get("market_position") or "")[:400],
        "categories": categories[:6],
        "key_metrics": list(raw.get("key_metrics") or [])[:5],
        "top_actions": list(raw.get("top_actions") or [])[:4],
        "industry_landscape": str(raw.get("industry_landscape") or "")[:500],
        "risks": [str(x)[:120] for x in (raw.get("risks") or [])[:5]],
        "sources": [str(x)[:120] for x in (raw.get("sources") or [])[:8]],
        "_fallback": bool(raw.get("_fallback")),
    }


def fetch_market_context_for_audit(profile: dict[str, Any]) -> str:
    company = str(profile.get("company_name") or "").strip()
    website = str(profile.get("website") or "").strip()
    if not company and not website:
        return ""
    try:
        from iidatech.evidence_bank.perplexity_client import call_perplexity_json, perplexity_enabled

        if not perplexity_enabled():
            return ""
        prompt = (
            f"Brief market snapshot for business audit.\nCompany: {company}\nWebsite: {website}\n"
            f"Industry: {profile.get('industry') or profile.get('gauge_business_type_label')}\n"
            f"Geography: {profile.get('geography') or ''}\n"
            f"Competitors: {profile.get('main_competitors') or 'unknown'}\n"
            'Return JSON: {"company_summary":"...","competitors":["..."],"market_trend":"...","positioning_note":"..."}'
        )
        api = call_perplexity_json(prompt, timeout=90)
        if api.get("error"):
            return ""
        parsed = api.get("parsed") or api.get("json")
        if isinstance(parsed, dict):
            return json.dumps(parsed, ensure_ascii=False)[:6000]
        return str(api.get("text") or api.get("content") or "")[:6000]
    except Exception:
        return ""


def run_gauge_audit(
    profile: dict[str, Any],
    text_request: TextRequestFn | None = None,
    *,
    include_market_search: bool = True,
) -> dict[str, Any]:
    market_context = fetch_market_context_for_audit(profile) if include_market_search else ""
    prompt = build_gauge_audit_user_prompt(profile, market_context=market_context)
    if not text_request:
        audit = fallback_gauge_audit(profile)
        audit["_route"] = "deterministic_fallback"
        return audit
    try:
        text, route = text_request(prompt, GAUGE_AUDIT_SYSTEM, 2048, 0.1)
        clean = extract_json_object(text)
        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            parsed = salvage_json_object(clean)
        if not isinstance(parsed, dict):
            raise ValueError("GAUGE audit response was not a JSON object")
        audit = normalize_gauge_audit(parsed)
        audit["_route"] = route
        if market_context:
            audit["_market_context_used"] = True
        return audit
    except Exception as exc:
        audit = fallback_gauge_audit(profile)
        audit["_route"] = f"deterministic_fallback_after_error: {str(exc)[:120]}"
        return audit


def gauge_audit_prompt_section(audit: dict[str, Any] | None) -> str:
    if not audit:
        return ""
    return (
        "GAUGE BUSINESS HEALTH AUDIT (mandatory context for this forward plan):\n"
        f"- Overall score: {audit.get('overall_score')}/100 - {audit.get('overall_label')}\n"
        f"- Summary: {audit.get('overall_summary')}\n"
        f"- Plain-language read for the founder: {audit.get('plain_english_read')}\n"
        f"- Market position: {audit.get('market_position')}\n"
        f"- Industry landscape: {audit.get('industry_landscape')}\n"
        f"- Priority actions from audit: {json.dumps(audit.get('top_actions') or [], ensure_ascii=False)[:2000]}\n"
        f"- Risk flags: {', '.join(audit.get('risks') or [])}\n"
        f"- Category scores: {json.dumps(audit.get('categories') or [], ensure_ascii=False)[:2500]}\n"
        "The business plan must address audit gaps, respect the score, and sequence the first_90_day_plan "
        "around top_actions while pursuing the founder's forward goals.\n\n"
    )


def merge_gauge_audit_into_profile(profile: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    merged = dict(profile)
    merged["gauge_audit"] = audit
    return merged
