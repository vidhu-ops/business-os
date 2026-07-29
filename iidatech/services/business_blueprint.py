"""Pass 1 - deterministic business blueprint from business context."""
from __future__ import annotations
import re
from typing import Any

_VALIDATION_REQUIRED = {
    "status": "validation_required",
    "verified": False,
    "reason": "insufficient real evidence",
}

def _as_dict(v):
    return v if isinstance(v, dict) else {}

def _as_list(v):
    return v if isinstance(v, list) else []

def _num(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value) if value else None
    text = str(value)
    m = re.search(r"[\d,]+(?:\.\d+)?", text.replace(",", ""))
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None

def _insufficient(label="insufficient evidence"):
    return {"status": label}

def _domain_bucket(domain: str) -> str:
    d = (domain or "").lower()
    if any(x in d for x in ("saas", "crm", "b2b", "automation", "software")):
        return "saas"
    if any(x in d for x in ("ecommerce", "d2c", "retail", "consumer", "fashion", "skincare")):
        return "d2c"
    if any(x in d for x in ("automotive", "garage", "repair", "physical", "service")):
        return "physical_service"
    return "general_b2b"

def _parse_price_band(band):
    if not band:
        return None, None
    text = str(band)
    nums = [float(x.replace(",", "")) for x in re.findall(r"[\d,]+(?:\.\d+)?", text) if x.replace(",", "").replace(".", "").isdigit() or re.match(r"^[\d,]+(?:\.\d+)?$", x)]
    if len(nums) >= 2:
        return nums[0], nums[1]
    if len(nums) == 1:
        return nums[0], nums[0]
    return None, None

def _market_opportunity(context):
    mt = _as_dict(context.get("market_truth"))
    tam, sam, som, cagr = mt.get("tam"), mt.get("sam"), mt.get("som"), mt.get("cagr")
    bottom = _as_dict(mt.get("bottom_up"))
    has_nums = any(_num(x) for x in (tam, sam, som, bottom.get("tam"), bottom.get("sam"), bottom.get("som")))
    if not has_nums and str(mt.get("market_model_status", "")).lower() in {"withheld", "not investor citable", "synthetic"}:
        return {"status": "insufficient evidence", "why_now": _why_now(context), "demand_proof": _demand_proof(context)}
    out = {"tam": tam or bottom.get("tam"), "sam": sam or bottom.get("sam"), "som": som or bottom.get("som"), "cagr": cagr or bottom.get("cagr"), "why_now": _why_now(context), "demand_proof": _demand_proof(context), "evidence_status": "evidence_derived" if has_nums else "partial"}
    if not has_nums:
        out["status"] = "insufficient evidence"
    return out

def _why_now(context):
    signals = []
    brief = _as_dict(_as_dict(context.get("market_truth")).get("topic_intelligence"))
    if brief.get("why_now"):
        signals.append(str(brief.get("why_now"))[:300])
    board = _as_dict(context.get("boardroom_verdict"))
    if board.get("market_timing"):
        signals.append(str(board.get("market_timing"))[:300])
    for row in _as_list(context.get("risks"))[:2]:
        pass
    sections = _as_dict(context.get("market_sections"))
    for sec in list(sections.values())[:2]:
        if isinstance(sec, dict) and sec.get("summary"):
            signals.append(sec["summary"][:200])
    return signals[:5] or ["Validate timing with 10-15 buyer interviews in execution geography."]

def _demand_proof(context):
    eq = _as_dict(context.get("evidence_quality"))
    proof = []
    if eq.get("citation_ledger_count"):
        proof.append(f"{eq['citation_ledger_count']} classified research sources in diligence pack")
    if eq.get("uploaded_evidence_count"):
        proof.append(f"{eq['uploaded_evidence_count']} founder-uploaded evidence files")
    inv = _as_dict(context.get("investment_decision"))
    if inv.get("demand_signal"):
        proof.append(str(inv.get("demand_signal"))[:200])
    return proof or ["No verified demand proof — run customer discovery before scaling."]

def _business_model(context, domain, top_icp, geography):
    anchors = _as_list(context.get("pricing_anchor"))
    low, high = None, None
    primary_package = None
    for row in anchors:
        lo, hi = _parse_price_band(row.get("price_band"))
        if lo is not None:
            low, high = lo, hi
            primary_package = row.get("package")
            break
    grounding = _as_dict(_as_dict(context.get("market_truth")).get("unit_economics_grounding"))
    setup = _num(grounding.get("setup_fee"))
    monthly = _num(grounding.get("monthly_fee") or grounding.get("arpu"))
    is_india = "india" in str(geography).lower()
    currency = "INR" if is_india else "USD"
    if setup is None and monthly is None and not anchors:
        return {
            **_VALIDATION_REQUIRED,
            "currency": currency,
            "revenue_streams": [],
            "pricing_model": _VALIDATION_REQUIRED,
            "gross_margin": _VALIDATION_REQUIRED,
            "contribution_margin": _VALIDATION_REQUIRED,
            "break_even": _VALIDATION_REQUIRED,
        }
    gross_margin_pct = _num(grounding.get("gross_margin_pct"))
    if gross_margin_pct is None:
        return {
            **_VALIDATION_REQUIRED,
            "currency": currency,
            "pricing_model": {"evidence_source": anchors[0].get("source_status") if anchors else None},
            "gross_margin": _VALIDATION_REQUIRED,
        }
    variable_cost = (monthly or 0) * (1 - gross_margin_pct) if monthly else None
    contribution = (monthly or 0) - variable_cost if monthly and variable_cost is not None else None
    burn_evidence = _num(grounding.get("monthly_burn"))
    bucket = _domain_bucket(domain)
    streams = ["subscription"] if bucket == "saas" else (["product_sales", "repeat_purchase"] if bucket == "d2c" else ["project_fee", "retainer"])
    break_even = _VALIDATION_REQUIRED if not (burn_evidence and contribution) else {
        "monthly_fixed_burn_assumption": burn_evidence,
        "customers_to_break_even": round(burn_evidence / max(contribution or 1, 1), 0),
        "verified": True,
    }
    return {"currency": currency, "pricing_model": {"primary_package": primary_package, "setup_or_upfront": setup, "recurring_or_unit_price": monthly, "evidence_source": anchors[0].get("source_status") if anchors else "evidence_required", "assumption_level": "evidence_derived" if anchors else "hypothesis"}, "revenue_streams": streams, "gross_margin": {"target_pct": gross_margin_pct, "basis": grounding.get("basis") or "evidence grounding"}, "contribution_margin": {"per_customer": round(contribution, 2) if contribution else None, "assumption_level": "derived" if anchors else "hypothesis"}, "break_even": break_even}

def _unit_economics(context, business_model):
    bm = _as_dict(business_model)
    if bm.get("status") == "validation_required" or bm.get("status") == "insufficient evidence":
        return {**_VALIDATION_REQUIRED, "assumption_level": "hypothesis"}
    pricing = _as_dict(bm.get("pricing_model"))
    monthly = _num(pricing.get("recurring_or_unit_price"))
    gross = _as_dict(bm.get("gross_margin")).get("target_pct")
    grounding = _as_dict(_as_dict(context.get("market_truth")).get("unit_economics_grounding"))
    cac = _num(grounding.get("cac"))
    ltv = _num(grounding.get("ltv"))
    if not any(x is not None for x in (monthly, gross, cac, ltv)):
        return {**_VALIDATION_REQUIRED, "validation_steps": ["Provide CAC/LTV from verified channel spend and retention data"]}
    payback = round(cac / max((monthly or 0) * (gross or 0), 1), 1) if cac and monthly and gross else None
    return {"cac": cac, "ltv": ltv, "arpu": monthly, "gross_margin_pct": gross, "payback_months": payback, "assumption_level": pricing.get("assumption_level", "hypothesis"), "validation_steps": ["Replace CAC with channel-specific spend / customers acquired", "Replace LTV with observed retention after 90 days"]}

def _gtm_strategy(context, domain, top_icp, geography):
    bucket = _domain_bucket(domain)
    buyer = top_icp.get("named_buyer_profile") or "named buyer profile"
    trigger = top_icp.get("buyer_trigger") or "validated buyer trigger"
    if bucket == "saas":
        channels = ["founder-led LinkedIn outreach", "niche community posts", "partner intros", "product-led trial"]
        motion = "founder_sales"
    elif bucket == "d2c":
        channels = ["Instagram/Meta test ads", "marketplace listing", "influencer micro-seeding", "WhatsApp community"]
        motion = "performance_marketing"
    elif bucket == "physical_service":
        channels = ["local SEO", "Google Maps", "referral from adjacent businesses", "B2B fleet contracts"]
        motion = "local_field_sales"
    else:
        channels = ["warm intros", "industry events", "niche outbound", "content proof assets"]
        motion = "founder_sales"
    gaps = []
    for row in _as_list(context.get("competitor_map"))[:3]:
        for g in _as_list(row.get("gaps")):
            if g:
                gaps.append(str(g)[:120])
    return {"acquisition_channels": channels, "funnel_stages": ["awareness", "discovery_call", "pilot", "paid_conversion", "expansion"], "conversion_assumptions": {"discovery_to_pilot": "10-20% (validate)", "pilot_to_paid": "30-50% (validate)"}, "sales_motion": motion, "launch_wedge": {"buyer": buyer, "trigger": trigger, "geography": geography, "differentiation_gaps": gaps[:5] or ["Define wedge after 10 buyer interviews"]}, "competitor_positioning": _as_list(context.get("competitor_map"))[:5]}

def _hiring_plan(domain, unit_economics):
    return [
        {"milestone": "0-10 customers", "headcount": "founder only", "roles": ["founder: sales + delivery"], "trigger": "pre-revenue validation"},
        {"milestone": "10-50 customers", "headcount": "founder + 1", "roles": ["founder", "sales/ops contractor or first hire"], "trigger": "repeatable pilot conversion"},
        {"milestone": "50-200 customers", "headcount": "3-8", "roles": ["sales", "delivery/ops", "customer success"], "trigger": "delivery bottleneck or CAC payback < 12 months"},
        {"milestone": "200+ customers", "headcount": "8+", "roles": ["GTM lead", "ops manager", "finance"], "trigger": "proven unit economics and runway for payroll"},
    ]

def _funding_plan(context, business_model, unit_economics):
    bm, ue = _as_dict(business_model), _as_dict(unit_economics)
    if ue.get("status") == "validation_required" or bm.get("status") == "validation_required":
        return {**_VALIDATION_REQUIRED, "currency": bm.get("currency", "USD")}
    burn = _num(_as_dict(bm.get("break_even")).get("monthly_fixed_burn_assumption"))
    if not burn:
        return {**_VALIDATION_REQUIRED, "currency": bm.get("currency", "USD")}
    inv = _as_dict(context.get("investment_decision"))
    raise_when = inv.get("funding_recommendation") or "After verified unit economics and paying customers"
    return {"currency": bm.get("currency", "USD"), "bootstrap_budget": round(burn * 6, 0), "seed_budget": round(burn * 18, 0), "monthly_burn": burn, "use_of_funds": ["customer discovery", "MVP delivery", "initial GTM tests", "compliance/legal buffer"], "raise_when": raise_when, "evidence_status": "derived_from_verified_burn"}

def _blueprint_from_canonical(canonical, *, idea: str = "", industry: str = "", geography: str = "", domain: str = "") -> dict:
    """Read-only blueprint slice from canonical report (no synthetic metric writers)."""
    canonical = canonical if isinstance(canonical, dict) else {}
    numeric = _as_dict(canonical.get("numeric_truth"))
    nm = _as_dict(numeric.get("metrics"))
    mo_status = "insufficient evidence" if numeric.get("status") == "BLOCKED" else "evidence-derived"
    mo = {
        "tam": (nm.get("tam") or {}).get("value"),
        "sam": (nm.get("sam") or {}).get("value"),
        "som": (nm.get("som") or {}).get("value"),
        "status": mo_status,
    }
    ue = {
        "cac": (nm.get("cac") or {}).get("value"),
        "ltv": (nm.get("ltv") or {}).get("value"),
        "payback_months": (nm.get("payback_months") or {}).get("value"),
        "status": numeric.get("status") or "BLOCKED",
        "evidence_status": "canonical_readonly",
    }
    comp = _as_dict(canonical.get("competitor_truth"))
    gtm = _as_dict(canonical.get("gtm_truth"))
    return {
        "market_opportunity": mo,
        "competitor_map": comp.get("matrix") or [],
        "business_model": {"status": mo_status, "pricing_model": _as_dict(canonical.get("pricing_truth")).get("bands")},
        "unit_economics": ue,
        "funding_plan": _insufficient("canonical — funding from boardroom only"),
        "go_to_market": {
            "acquisition_channels": gtm.get("acquisition_channels") or [],
            "status": gtm.get("status") or "BLOCKED",
        },
        "hiring_plan": [],
        "meta": {
            "engine": "canonical_readonly_blueprint",
            "idea": idea,
            "industry": industry,
            "geography": geography,
            "domain": domain,
        },
    }


def build_deterministic_business_blueprint(context, *, domain: str = "", icp_block: dict | None = None, idea: str = "", industry: str = "", geography: str = "") -> dict:
    context = context if isinstance(context, dict) else {}
    canonical = _as_dict(context.get("canonical_report"))
    if canonical:
        meta = _as_dict(context.get("meta"))
        return _blueprint_from_canonical(
            canonical,
            idea=idea or meta.get("idea", ""),
            industry=industry or meta.get("industry", ""),
            geography=geography or meta.get("geography", ""),
            domain=domain,
        )
    meta = _as_dict(context.get("meta"))
    idea = idea or meta.get("idea", "")
    industry = industry or meta.get("industry", "")
    geography = geography or meta.get("geography", "")
    icp_block = _as_dict(icp_block)
    profiles = _as_list(icp_block.get("named_buyer_profiles"))
    top_icp = profiles[0] if profiles and isinstance(profiles[0], dict) else {}
    return {
        "market_opportunity": _market_opportunity(context),
        "competitor_map": _as_list(context.get("competitor_map")),
        "business_model": _business_model(context, domain, top_icp, geography),
        "unit_economics": _unit_economics(context, _business_model(context, domain, top_icp, geography)),
        "funding_plan": _funding_plan(context, _business_model(context, domain, top_icp, geography), {}),
        "go_to_market": _gtm_strategy(context, domain, top_icp, geography),
        "hiring_plan": _hiring_plan(domain, {}),
        "meta": {"engine": "deterministic_blueprint_v2", "idea": idea, "industry": industry, "geography": geography, "domain": domain},
    }

def merge_blueprint_to_legacy_plan(blueprint, *, idea, industry, geography, domain, icp_block, application_pack=None):
    """Map V2 blueprint keys onto legacy business plan schema for UI compatibility."""
    bp = blueprint if isinstance(bp := blueprint, dict) else {}
    mo = _as_dict(bp.get("market_opportunity"))
    bm = _as_dict(bp.get("business_model"))
    ue = _as_dict(bp.get("unit_economics"))
    gtm = _as_dict(bp.get("go_to_market"))
    funding = _as_dict(bp.get("funding_plan"))
    hiring = _as_list(bp.get("hiring_plan"))
    pricing = _as_dict(bm.get("pricing_model"))
    profiles = _as_list(_as_dict(icp_block).get("named_buyer_profiles"))
    top_icp = profiles[0] if profiles and isinstance(profiles[0], dict) else {}
    currency = bm.get("currency", "USD")
    return {
        "business_concept": {"idea": idea, "industry": industry, "geography": geography, "domain": domain, "category": industry, "wedge": gtm.get("launch_wedge", {})},
        "validated_icp": icp_block,
        "market_opportunity": mo,
        "competitor_map": bp.get("competitor_map", []),
        "business_model": bm,
        "unit_economics": ue,
        "funding_plan": funding,
        "go_to_market": gtm,
        "hiring_plan": hiring,
        "execution_blueprint": bp.get("execution_blueprint", {}),
        "strategist_audit": bp.get("strategist_audit", {}),
        "customer_and_market": {"tam": mo.get("tam"), "sam": mo.get("sam"), "som": mo.get("som"), "why_now": mo.get("why_now"), "demand_proof": mo.get("demand_proof"), "status": mo.get("status")},
        "market_assessment": {
            "plain_english_verdict": "Evidence-derived blueprint" if mo.get("status") != "insufficient evidence" else "Market sizing insufficient — complete primary research",
            "market_readiness": _VALIDATION_REQUIRED if mo.get("status") == "insufficient evidence" else {"status": "evidence_derived", "verified": True},
        },
        "go_to_market_strategy": gtm,
        "marketing_work_pack": {"targeting": {"primary_icp": top_icp.get("named_buyer_profile")}, "channel_order": gtm.get("acquisition_channels", []), "competitor_battlecards": bp.get("competitor_map", []), "positioning": {"wedge": gtm.get("launch_wedge")}},
        "financial_model": {"currency": currency, "core_assumptions": pricing, "model_status": bm.get("status") or "evidence-derived v2 blueprint", "break_even": bm.get("break_even", {})},
        "founder_financial_breakdown": {"currency": currency, "unit_economics_per_customer": ue, "plain_english": f"CAC {ue.get('cac')} | LTV {ue.get('ltv')} | Payback {ue.get('payback_months')} months"},
        "startup_budget": {"bootstrap_budget": funding.get("bootstrap_budget"), "currency": currency, "use_of_funds": funding.get("use_of_funds")},
        "revenue_required": {"break_even_customers": _as_dict(bm.get("break_even")).get("customers_to_break_even")},
        "operating_model": {"sales_motion": gtm.get("sales_motion"), "delivery": "founder-led until 10 customers"},
        "product_to_build": {"mvp_scope": "one use case, one geography, one metric — from execution blueprint"},
        "application_readiness_pack": application_pack or {},
        "_business_builder_engine": "v2_deterministic",
    }