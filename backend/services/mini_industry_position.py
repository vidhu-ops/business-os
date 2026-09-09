"""Industry standing block for Mini GAUGE reports."""

from __future__ import annotations

from typing import Any

MINI_INDUSTRY_VERTICALS: list[dict[str, str]] = [
    {"id": "b2b_saas", "label": "B2B SaaS / Software"},
    {"id": "ecommerce", "label": "E-commerce / D2C"},
    {"id": "fintech", "label": "Fintech / Financial services"},
    {"id": "healthcare", "label": "Healthcare / Clinics"},
    {"id": "edtech", "label": "EdTech / Training"},
    {"id": "agency", "label": "Agency / Professional services"},
    {"id": "retail", "label": "Retail / Brick & mortar"},
    {"id": "food_hospitality", "label": "Food & hospitality"},
    {"id": "logistics", "label": "Logistics / Operations"},
    {"id": "manufacturing", "label": "Manufacturing / Industrial"},
    {"id": "other", "label": "Other / mixed"},
]

_STANDING_ORDER = ("below", "inline", "above")


def industry_vertical_label(vertical_id: str) -> str:
    for row in MINI_INDUSTRY_VERTICALS:
        if row.get("id") == vertical_id:
            return str(row.get("label") or vertical_id)
    return vertical_id.replace("_", " ").title() if vertical_id else ""


def resolve_industry_from_draft(draft: dict[str, Any], *, fallback_type_label: str = "") -> str:
    custom = str(draft.get("industry") or "").strip()
    vertical = str(draft.get("industry_vertical") or "").strip().lower()
    if vertical and vertical != "other":
        return industry_vertical_label(vertical)
    if custom:
        return custom
    return fallback_type_label or "General"


def industry_json_schema_hint() -> str:
    return (
        'industry_position (required object): {"industry_label":"...", "geography":"...", '
        '"standing_tier":"Emerging|Below peer median|Competitive|Strong industry signal", '
        '"percentile_estimate":"e.g. 35th-45th percentile among similar-stage peers in this industry", '
        '"standing_summary":"2-4 sentences on where this company sits in the selected industry", '
        '"vs_industry":[{"dimension":"...","your_read":"...","industry_typical":"...","standing":"below|inline|above"}] '
        '(4-6 rows covering presence, traction, differentiation, ops maturity), '
        '"industry_gaps":["gap vs typical player in this industry"], '
        '"momentum":"building|scaling|plateau|unclear"}. '
        "Benchmark explicitly against the user's selected industry and geography — not generic advice."
    )


def _tier_from_score(overall: int, stage: str) -> str:
    if overall >= 72:
        return "Strong industry signal"
    if overall >= 58:
        return "Competitive for stage"
    if overall >= 42:
        return "Below peer median"
    return "Emerging / early in industry"


def _percentile_band(overall: int) -> str:
    if overall >= 80:
        return "75th+ percentile among similar-stage peers"
    if overall >= 65:
        return "60th-75th percentile among similar-stage peers"
    if overall >= 50:
        return "45th-60th percentile among similar-stage peers"
    if overall >= 35:
        return "30th-45th percentile among similar-stage peers"
    return "10th-30th percentile among similar-stage peers"


def _standing_flag(yours: int, typical: int) -> str:
    if yours >= typical + 8:
        return "above"
    if yours <= typical - 8:
        return "below"
    return "inline"


def build_industry_position_fallback(profile: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    industry = str(profile.get("industry") or profile.get("gauge_business_type_label") or "your industry")
    geo = str(profile.get("geography") or "your market")
    company = str(profile.get("company_name") or "This company")
    stage = str(profile.get("business_stage_label") or profile.get("operating_stage") or "early")
    overall = int(audit.get("overall_score") or 50)
    categories = {str(c.get("name")): int(c.get("score") or 0) for c in (audit.get("categories") or []) if isinstance(c, dict)}

    presence = categories.get("Sales & Marketing", 45)
    traction = categories.get("Financials", 40)
    customers = categories.get("Customers", 40)
    competitive = categories.get("Competitive Position", 40)
    operations = categories.get("Operations", 40)

    competitors = str(profile.get("main_competitors") or "")
    differentiation = str((profile.get("plan_forward") or {}).get("why_customers_choose") or "")
    target = str(profile.get("target_customer") or "")

    tier = _tier_from_score(overall, stage)
    percentile = _percentile_band(overall)

    standing_summary = (
        f"{company} reads as a {tier.lower()} in {industry} ({geo}) at the {stage} stage. "
        f"On this Mini GAUGE snapshot ({overall}/100 overall), you appear around the {percentile} "
        f"for operators with similar public signal and stated metrics."
    )
    if competitors:
        standing_summary += f" Named competitors ({competitors[:80]}) anchor the competitive read."
    elif differentiation:
        standing_summary += " Differentiation is stated but competitor benchmarks would sharpen placement."

    vs_industry = [
        {
            "dimension": "Public presence & credibility",
            "your_read": "Website/social footprint and clarity of offer",
            "industry_typical": f"Established {industry} players maintain polished sites and active LinkedIn",
            "standing": _standing_flag(presence, 55),
        },
        {
            "dimension": "Traction / revenue signal",
            "your_read": "Stated revenue and growth metrics" if profile.get("monthly_revenue") else "Revenue not stated in mini intake",
            "industry_typical": "Peers at your stage usually track monthly revenue and unit economics",
            "standing": _standing_flag(traction, 50),
        },
        {
            "dimension": "Customer proof",
            "your_read": f"ICP: {target[:80]}" if target else "Target customer not sharply defined",
            "industry_typical": f"{industry} winners show ICP focus plus retention or case proof",
            "standing": _standing_flag(customers, 52),
        },
        {
            "dimension": "Differentiation vs alternatives",
            "your_read": differentiation[:100] if differentiation else "Positioning vs alternatives is thin",
            "industry_typical": "Clear wedge vs 2-3 named alternatives",
            "standing": _standing_flag(competitive, 54),
        },
        {
            "dimension": "Operating maturity",
            "your_read": f"Team/process signal (ops score {operations}/100)",
            "industry_typical": "Scaling peers document delivery, support, and hiring cadence",
            "standing": _standing_flag(operations, 50),
        },
    ]

    gaps: list[str] = []
    if _standing_flag(presence, 55) == "below":
        gaps.append("Strengthen public presence to match credible players in " + industry)
    if not profile.get("monthly_revenue"):
        gaps.append("Add revenue traction to compare against typical " + industry + " benchmarks")
    if not competitors:
        gaps.append("Name 2-3 direct competitors to benchmark positioning")
    if not differentiation:
        gaps.append("Articulate a sharper wedge vs alternatives in " + industry)
    if _standing_flag(operations, 50) == "below":
        gaps.append("Tighten operating basics before scaling GTM in " + industry)
    while len(gaps) < 3:
        gaps.append("Run full GAUGE for checklist-level gaps vs industry norms")

    momentum = "building"
    if str(profile.get("operating_stage") or "") in {"scaling", "mature"}:
        momentum = "scaling"
    if overall < 35:
        momentum = "unclear"

    return {
        "industry_label": industry,
        "geography": geo,
        "standing_tier": tier,
        "percentile_estimate": percentile,
        "standing_summary": standing_summary[:900],
        "vs_industry": vs_industry[:6],
        "industry_gaps": gaps[:5],
        "momentum": momentum,
    }


def _normalize_vs_row(item: Any) -> dict[str, str] | None:
    if not isinstance(item, dict):
        return None
    standing = str(item.get("standing") or "inline").lower()
    if standing not in _STANDING_ORDER:
        standing = "inline"
    return {
        "dimension": str(item.get("dimension") or "Dimension")[:120],
        "your_read": str(item.get("your_read") or "")[:280],
        "industry_typical": str(item.get("industry_typical") or item.get("typical") or "")[:280],
        "standing": standing,
    }


def normalize_industry_position(raw: Any, profile: dict[str, Any]) -> dict[str, Any]:
    if isinstance(raw, dict) and raw.get("standing_summary"):
        vs_rows = []
        for item in raw.get("vs_industry") or raw.get("vs_peers") or []:
            row = _normalize_vs_row(item)
            if row:
                vs_rows.append(row)
        gaps = [str(x)[:200] for x in (raw.get("industry_gaps") or raw.get("gaps") or []) if str(x).strip()][:5]
        momentum = str(raw.get("momentum") or "building").lower()
        if momentum not in {"building", "scaling", "plateau", "unclear"}:
            momentum = "building"
        return {
            "industry_label": str(raw.get("industry_label") or profile.get("industry") or "")[:120],
            "geography": str(raw.get("geography") or profile.get("geography") or "")[:120],
            "standing_tier": str(raw.get("standing_tier") or raw.get("tier") or "Competitive for stage")[:80],
            "percentile_estimate": str(raw.get("percentile_estimate") or raw.get("percentile") or "")[:120],
            "standing_summary": str(raw.get("standing_summary") or "")[:900],
            "vs_industry": vs_rows[:6],
            "industry_gaps": gaps,
            "momentum": momentum,
        }
    return build_industry_position_fallback(profile, {"overall_score": 50, "categories": []})


def enrich_audit_with_industry_position(audit: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    pos = audit.get("industry_position")
    if isinstance(pos, dict) and pos.get("standing_summary"):
        audit["industry_position"] = normalize_industry_position(pos, profile)
    else:
        audit["industry_position"] = build_industry_position_fallback(profile, audit)

    ip = audit["industry_position"]
    if ip.get("standing_summary") and (not audit.get("market_position") or len(str(audit.get("market_position"))) < 50):
        audit["market_position"] = str(ip["standing_summary"])[:400]
    if ip.get("industry_label") and (not audit.get("industry_landscape") or len(str(audit.get("industry_landscape"))) < 60):
        audit["industry_landscape"] = (
            f"{ip['industry_label']} in {ip.get('geography') or profile.get('geography')}: "
            f"typical winners combine clear ICP, proof, and disciplined unit economics. "
            f"Momentum signal: {ip.get('momentum', 'building')}."
        )[:500]
    audit["industry_selected"] = str(ip.get("industry_label") or profile.get("industry") or "")
    return audit
