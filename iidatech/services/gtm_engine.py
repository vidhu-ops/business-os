"""Vertical-specific GTM channel economics engine."""
from __future__ import annotations

from typing import Any

_VALIDATION = "VALIDATION REQUIRED"
_VALIDATION_REQUIRED = {
    "status": "validation_required",
    "verified": False,
    "reason": "insufficient real evidence",
}

_VERTICALS = ("saas", "d2c", "local_business", "agency", "retail", "healthcare")

# difficulty -> launch friction multiplier for roi_score
_DIFFICULTY_MULT = {"low": 1.0, "medium": 0.82, "high": 0.62}


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _num(v: Any) -> float | None:
    if v in (None, "", _VALIDATION):
        return None
    if isinstance(v, dict):
        v = v.get("value") or v.get("display")
    try:
        return float(str(v).replace(",", "").replace("$", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def _text(v: Any) -> str:
    if v in (None, "", _VALIDATION):
        return _VALIDATION
    return str(v).strip()


def _resolve_vertical(v3_report: dict, business_plan: dict) -> str:
    plan = _as_dict(business_plan)
    v3 = _as_dict(v3_report)
    concept = _as_dict(plan.get("business_concept"))
    domain = str(
        concept.get("domain")
        or plan.get("domain")
        or v3.get("domain")
        or ""
    ).lower()
    industry = str(v3.get("industry") or plan.get("industry") or concept.get("industry") or "").lower()
    topic = str(v3.get("topic") or plan.get("idea") or concept.get("idea") or "").lower()
    hay = f"{domain} {industry} {topic}"

    if any(t in hay for t in ("healthcare", "clinic", "hospital", "patient", "physician", "medical", "pharma")):
        return "healthcare"
    if any(t in hay for t in ("agency", "consulting", "services firm", "professional services", "boutique")):
        return "agency"
    if domain in {"ecommerce_retail", "consumer", "fashion", "d2c_skincare"} or any(
        t in hay for t in ("d2c", "ecommerce", "e-commerce", "direct to consumer", "shopify", "dtc")
    ):
        return "d2c"
    if any(t in hay for t in ("retail store", "brick and mortar", "festive", "kirana", "wholesale", "retail")):
        if "saas" not in hay and "software" not in hay:
            return "retail"
    if any(t in hay for t in ("local business", "justdial", "apartment", "society", "neighborhood", "garage", "salon", "restaurant")):
        return "local_business"
    if domain in {"crm_automation", "b2b_saas", "saas_software", "ai_workflow_automation"} or any(
        t in hay for t in ("saas", "subscription software", "b2b software", "workflow software")
    ):
        return "saas"
    if "retail" in industry:
        return "retail"
    if "health" in industry:
        return "healthcare"
    return "saas"


def _channel_templates(vertical: str) -> list[dict[str, Any]]:
    templates: dict[str, list[dict[str, Any]]] = {
        "saas": [
            {"channel": "Founder-led LinkedIn ABM", "difficulty": "medium", "expected_cac": 420, "conversion_rate": 0.03, "sales_cycle_days": 42},
            {"channel": "High-intent Google Search", "difficulty": "medium", "expected_cac": 680, "conversion_rate": 0.045, "sales_cycle_days": 21},
            {"channel": "Integration / marketplace partners", "difficulty": "medium", "expected_cac": 310, "conversion_rate": 0.04, "sales_cycle_days": 38},
            {"channel": "Niche SEO + comparison content", "difficulty": "high", "expected_cac": 165, "conversion_rate": 0.018, "sales_cycle_days": 75},
            {"channel": "Product-led free trial funnel", "difficulty": "high", "expected_cac": 140, "conversion_rate": 0.07, "sales_cycle_days": 18},
        ],
        "d2c": [
            {"channel": "Meta / Instagram paid", "difficulty": "low", "expected_cac": 32, "conversion_rate": 0.025, "sales_cycle_days": 1},
            {"channel": "WhatsApp referral loop", "difficulty": "low", "expected_cac": 14, "conversion_rate": 0.04, "sales_cycle_days": 2},
            {"channel": "Marketplace (Amazon / Flipkart)", "difficulty": "medium", "expected_cac": 58, "conversion_rate": 0.03, "sales_cycle_days": 1},
            {"channel": "Micro-influencer seeding", "difficulty": "medium", "expected_cac": 24, "conversion_rate": 0.02, "sales_cycle_days": 4},
            {"channel": "Google Shopping", "difficulty": "medium", "expected_cac": 41, "conversion_rate": 0.022, "sales_cycle_days": 1},
        ],
        "local_business": [
            {"channel": "Google Maps / Local Services Ads", "difficulty": "low", "expected_cac": 72, "conversion_rate": 0.08, "sales_cycle_days": 3},
            {"channel": "JustDial / IndiaMART lead listings", "difficulty": "low", "expected_cac": 48, "conversion_rate": 0.05, "sales_cycle_days": 5},
            {"channel": "Apartment / society field outreach", "difficulty": "medium", "expected_cac": 28, "conversion_rate": 0.12, "sales_cycle_days": 7},
            {"channel": "Local partnership (schools, clubs, vendors)", "difficulty": "medium", "expected_cac": 38, "conversion_rate": 0.1, "sales_cycle_days": 12},
            {"channel": "Walk-in + storefront signage", "difficulty": "low", "expected_cac": 18, "conversion_rate": 0.15, "sales_cycle_days": 0},
        ],
        "agency": [
            {"channel": "Case-study outbound to named accounts", "difficulty": "medium", "expected_cac": 1050, "conversion_rate": 0.02, "sales_cycle_days": 55},
            {"channel": "Agency / vendor referral partners", "difficulty": "low", "expected_cac": 520, "conversion_rate": 0.05, "sales_cycle_days": 40},
            {"channel": "LinkedIn authority + targeted DM", "difficulty": "medium", "expected_cac": 880, "conversion_rate": 0.025, "sales_cycle_days": 48},
            {"channel": "Paid audit / workshop lead magnet", "difficulty": "high", "expected_cac": 460, "conversion_rate": 0.04, "sales_cycle_days": 28},
            {"channel": "Niche operator community presence", "difficulty": "medium", "expected_cac": 290, "conversion_rate": 0.03, "sales_cycle_days": 32},
        ],
        "retail": [
            {"channel": "In-store bundle / upsell", "difficulty": "low", "expected_cac": 9, "conversion_rate": 0.2, "sales_cycle_days": 0},
            {"channel": "Festive pop-up / stall", "difficulty": "medium", "expected_cac": 38, "conversion_rate": 0.08, "sales_cycle_days": 1},
            {"channel": "B2B wholesale distributor outreach", "difficulty": "medium", "expected_cac": 185, "conversion_rate": 0.04, "sales_cycle_days": 21},
            {"channel": "Marketplace listing", "difficulty": "low", "expected_cac": 52, "conversion_rate": 0.03, "sales_cycle_days": 2},
            {"channel": "Local flyer / newspaper drop", "difficulty": "medium", "expected_cac": 65, "conversion_rate": 0.02, "sales_cycle_days": 3},
        ],
        "healthcare": [
            {"channel": "Physician referral network", "difficulty": "medium", "expected_cac": 240, "conversion_rate": 0.06, "sales_cycle_days": 28},
            {"channel": "Google Local + reputation management", "difficulty": "low", "expected_cac": 165, "conversion_rate": 0.07, "sales_cycle_days": 6},
            {"channel": "Community health camp events", "difficulty": "medium", "expected_cac": 120, "conversion_rate": 0.05, "sales_cycle_days": 14},
            {"channel": "Insurance panel / TPA partnership", "difficulty": "high", "expected_cac": 380, "conversion_rate": 0.035, "sales_cycle_days": 75},
            {"channel": "Hospital OPD routing tie-up", "difficulty": "high", "expected_cac": 450, "conversion_rate": 0.03, "sales_cycle_days": 90},
        ],
    }
    return [dict(row) for row in templates.get(vertical, templates["saas"])]


def _anchor_cac(v3_report: dict, business_plan: dict) -> float | None:
    v3 = _as_dict(v3_report)
    ue = _as_dict(v3.get("unit_economics"))
    table = _as_list(ue.get("table"))
    for row in table:
        if isinstance(row, dict) and str(row.get("metric", "")).lower() == "cac":
            n = _num(row.get("value"))
            if n is not None:
                return n
    for src in (
        _as_dict(ue.get("grounding")).get("known"),
        _as_dict(business_plan.get("financial_model")),
        _as_dict(business_plan.get("founder_financial_breakdown")),
    ):
        if isinstance(src, dict):
            n = _num(src.get("cac") or src.get("CAC") or src.get("median_cac"))
            if n is not None:
                return n
    return None


def _roi_score(
    *,
    expected_cac: float,
    conversion_rate: float,
    sales_cycle_days: int,
    difficulty: str,
    ltv: float | None = None,
) -> float:
    diff_mult = _DIFFICULTY_MULT.get(difficulty, 0.75)
    cycle_factor = min(1.2, 30 / max(sales_cycle_days, 1))
    conv_pct = conversion_rate * 100
    cac_efficiency = (ltv / expected_cac) if ltv and expected_cac > 0 else (conv_pct * cycle_factor) / max(expected_cac / 100, 0.5)
    raw = cac_efficiency * diff_mult * 2.2
    return round(min(10.0, max(0.5, raw)), 1)


def _ltv_from_v3(v3_report: dict, business_plan: dict) -> float | None:
    v3 = _as_dict(v3_report)
    ue = _as_dict(v3.get("unit_economics"))
    for row in _as_list(ue.get("table")):
        if isinstance(row, dict) and str(row.get("metric", "")).lower() == "ltv":
            return _num(row.get("value"))
    fm = _as_dict(business_plan.get("financial_model"))
    return _num(fm.get("ltv") or fm.get("LTV") or fm.get("customer_lifetime_value"))


def _plan_channel_names(business_plan: dict) -> list[str]:
    plan = _as_dict(business_plan)
    names: list[str] = []
    gtm = _as_dict(plan.get("go_to_market_strategy") or plan.get("go_to_market"))
    for row in _as_list(gtm.get("channels")):
        if isinstance(row, dict) and row.get("channel"):
            names.append(str(row["channel"]))
        elif isinstance(row, str):
            names.append(row)
    mkt = _as_dict(plan.get("marketing_work_pack"))
    for row in _as_list(mkt.get("channel_order")):
        if isinstance(row, dict) and row.get("channel"):
            names.append(str(row["channel"]))
    cas = _as_dict(plan.get("customer_acquisition_strategy"))
    for row in _as_list(cas.get("channel_plan")):
        if isinstance(row, dict) and row.get("channel"):
            names.append(str(row["channel"]))
    return names


def _v3_channel_hints(v3_report: dict) -> dict[str, dict[str, Any]]:
    gtm = _as_dict(_as_dict(v3_report).get("go_to_market"))
    hints: dict[str, dict[str, Any]] = {}
    for row in _as_list(gtm.get("channels")):
        if not isinstance(row, dict):
            continue
        key = str(row.get("channel") or row.get("name") or "").strip().lower()
        if key:
            hints[key] = row
    return hints


_BENCH_VERTICAL = {
    "saas": "saas",
    "d2c": "d2c",
    "local_business": "general",
    "agency": "services_agency",
    "retail": "ecommerce_retail",
    "healthcare": "healthcare",
}


def _scale_cac_templates(channels: list[dict[str, Any]], anchor: float | None, vertical: str) -> None:
    if anchor is None or not channels:
        return
    template_median = sorted(c["expected_cac"] for c in channels)[len(channels) // 2]
    if template_median <= 0:
        return
    ratio = anchor / template_median
    if ratio < 0.55 or ratio > 2.2:
        return
    ratio = max(0.75, min(1.35, ratio))
    for ch in channels:
        ch["expected_cac"] = round(ch["expected_cac"] * ratio, 2)
        ch["cac_source"] = "scaled_from_validated_cac"


def _merge_plan_channel(channels: list[dict[str, Any]], plan_name: str, vertical: str, ltv: float | None) -> dict[str, Any] | None:
    name = plan_name.strip()
    if not name:
        return None
    base = _channel_templates(vertical)[0]
    row = {
        "channel": name,
        "difficulty": "medium",
        "expected_cac": base["expected_cac"],
        "conversion_rate": base["conversion_rate"],
        "sales_cycle_days": base["sales_cycle_days"],
        "source": "business_plan",
    }
    row["roi_score"] = _roi_score(
        expected_cac=row["expected_cac"],
        conversion_rate=row["conversion_rate"],
        sales_cycle_days=row["sales_cycle_days"],
        difficulty=row["difficulty"],
        ltv=ltv,
    )
    return row


def _has_verified_channel_economics(v3_report: dict, business_plan: dict) -> bool:
    if _anchor_cac(v3_report, business_plan) is not None:
        return True
    v3 = _as_dict(v3_report)
    for row in _as_list(_as_dict(v3.get("go_to_market")).get("channels")):
        if isinstance(row, dict) and row.get("evidence_backed") and _num(row.get("cac") or row.get("expected_cac")):
            return True
    ue = _as_dict(v3.get("unit_economics"))
    for row in _as_list(ue.get("table")):
        if isinstance(row, dict) and str(row.get("metric", "")).lower() == "cac" and row.get("evidence_backed"):
            return True
    return False


def build_gtm_engine(v3_report: dict[str, Any] | None, business_plan: dict[str, Any] | None) -> dict[str, Any]:
    """Build channel-level GTM economics from V3 report + business plan."""
    v3 = _as_dict(v3_report)
    plan = _as_dict(business_plan)
    vertical = _resolve_vertical(v3, plan)
    if not _has_verified_channel_economics(v3, plan):
        return {
            **_VALIDATION_REQUIRED,
            "vertical": vertical,
            "acquisition_channels": [],
            "recommended_launch_sequence": [],
            "first_channel": _VALIDATION,
            "scale_channel": _VALIDATION,
            "economics_note": "Channel economics require verified CAC from evidence",
        }
    ltv = _ltv_from_v3(v3, plan)
    anchor_cac = _anchor_cac(v3, plan)

    channels = _channel_templates(vertical)
    _scale_cac_templates(channels, anchor_cac, vertical)

    hints = _v3_channel_hints(v3)
    for ch in channels:
        hint = hints.get(ch["channel"].lower())
        if not hint:
            for hk, hv in hints.items():
                if hk in ch["channel"].lower() or ch["channel"].lower() in hk:
                    hint = hv
                    break
        if hint:
            cac = _num(hint.get("cac") or hint.get("expected_cac") or hint.get("cac_estimate"))
            if cac is not None:
                ch["expected_cac"] = round(cac, 2)
                ch["cac_source"] = "v3_evidence"
            conv = _num(hint.get("conversion_rate"))
            if conv is not None:
                ch["conversion_rate"] = conv / 100 if conv > 1 else conv
            cycle = _num(hint.get("sales_cycle_days") or hint.get("speed"))
            if cycle is not None:
                ch["sales_cycle_days"] = int(cycle)
            diff = _text(hint.get("difficulty"))
            if diff != _VALIDATION:
                ch["difficulty"] = diff.lower()

        ch["expected_leads_per_month"] = None

        ch["roi_score"] = _roi_score(
            expected_cac=float(ch["expected_cac"]),
            conversion_rate=float(ch["conversion_rate"]),
            sales_cycle_days=int(ch["sales_cycle_days"]),
            difficulty=str(ch["difficulty"]),
            ltv=ltv,
        )

    existing = {c["channel"].lower() for c in channels}
    for plan_name in _plan_channel_names(plan):
        if plan_name.lower() not in existing and plan_name.lower() not in {"validation interviews"}:
            extra = _merge_plan_channel(channels, plan_name, vertical, ltv)
            if extra:
                channels.append(extra)
                existing.add(extra["channel"].lower())

    channels.sort(key=lambda c: c.get("roi_score", 0), reverse=True)

    launch_sorted = sorted(
        channels,
        key=lambda c: (
            {"low": 0, "medium": 1, "high": 2}.get(str(c.get("difficulty")), 1),
            -float(c.get("roi_score", 0)),
            float(c.get("expected_cac", 9999)),
        ),
    )

    recommended = [c["channel"] for c in launch_sorted[:4]]
    first = launch_sorted[0]["channel"] if launch_sorted else _VALIDATION
    scale = channels[0]["channel"] if channels else _VALIDATION

    return {
        "vertical": vertical,
        "acquisition_channels": channels,
        "recommended_launch_sequence": recommended,
        "first_channel": first,
        "scale_channel": scale,
        "economics_note": (
            f"Benchmark-scaled {vertical} channel model"
            + (f"; CAC anchored to validated {_anchor_cac(v3, plan):.0f}" if anchor_cac else "; CAC from vertical benchmarks")
            + (f"; LTV {_ltv_from_v3(v3, plan):.0f} used in ROI" if ltv else "")
        ),
    }
_LEADS_BASE = {"saas": 55, "d2c": 380, "local_business": 95, "agency": 28, "retail": 220, "healthcare": 42}


def _expected_leads_per_month(vertical: str, channel: dict) -> int:
    if channel.get("expected_leads_per_month") is not None:
        return int(channel["expected_leads_per_month"])
    base = _LEADS_BASE.get(vertical, 50)
    diff = str(channel.get("difficulty", "medium")).lower()
    mult = {"low": 1.35, "medium": 1.0, "high": 0.7}.get(diff, 1.0)
    cycle = max(int(channel.get("sales_cycle_days", 14) or 14), 1)
    cycle_factor = min(2.2, 28 / cycle)
    conv = float(channel.get("conversion_rate") or 0.03)
    conv_factor = min(1.8, max(0.6, conv * 25))
    return max(8, int(base * mult * cycle_factor * conv_factor))


def build_gtm_channel_economics(report_v3: dict) -> list:
    gtm = report_v3.get("go_to_market", {}) if isinstance(report_v3, dict) else {}
    engine = gtm.get("gtm_engine") if isinstance(gtm.get("gtm_engine"), dict) else {}
    if engine.get("status") == "validation_required":
        return []
    channels = engine.get("acquisition_channels") or gtm.get("channels") or []
    vertical = str(engine.get("vertical") or gtm.get("vertical") or "saas")
    if not channels:
        engine = build_gtm_engine(report_v3 if isinstance(report_v3, dict) else {}, {})
        if engine.get("status") == "validation_required":
            return []
        channels = engine.get("acquisition_channels", [])
        vertical = str(engine.get("vertical") or vertical)
    rows = []
    for ch in channels:
        if not isinstance(ch, dict):
            continue
        leads = ch.get("expected_leads_per_month")
        rows.append({
            "channel": ch.get("channel"),
            "expected_cac": ch.get("expected_cac") or ch.get("cac"),
            "expected_leads_per_month": int(leads) if leads is not None else None,
            "conversion_rate": ch.get("conversion_rate"),
            "sales_cycle_days": ch.get("sales_cycle_days"),
            "roi_score": ch.get("roi_score"),
        })
    rows.sort(key=lambda r: float(r.get("roi_score") or 0), reverse=True)
    return rows
