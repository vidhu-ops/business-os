"""
Quantitative market modeling utilities for IIDATECH reports.

The model is intentionally transparent: every number is derived from named
assumptions so the report can show forecast logic, scenario trees, sensitivity
tables, and churn/unit-economics impacts without inventing vendor disclosures.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass
class MarketModelInputs:
    start_year: int = 2026
    end_year: int = 2031
    reachable_smbs_m: float = 30.0
    base_acv: float = 2400.0
    conservative_acv: float = 600.0
    upside_acv: float = 6000.0
    sam_share: float = 0.30
    som_low_share: float = 0.01
    som_high_share: float = 0.03
    annual_churn: float = 0.30
    base_monthly_price: float = 200.0
    model_cost_per_run: float = 0.033
    web_search_cost_per_call: float = 0.01
    web_search_share: float = 0.10


def classify_model_domain(topic: str, industry: str) -> str:
    text = f"{topic} {industry}".lower()
    def has(term: str) -> bool:
        term = term.lower().strip()
        if " " in term or "_" in term or "/" in term or "-" in term or "." in term:
            return term in text
        import re
        return re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) is not None

    def has_any(terms: tuple[str, ...]) -> bool:
        return any(has(term) for term in terms)

    extended = {
        "real_estate": ("real estate", "construction", "proptech", "housing", "property", "contractor", "building", "project management"),
        "logistics": ("logistics", "transport", "warehousing", "warehouse", "fleet", "freight", "trucking", "3pl", "cold chain", "supply chain"),
        "education": ("education", "edtech", "tutoring", "school", "university", "vocational", "workforce training", "learning", "apprenticeship"),
        "consumer": ("consumer", "retail", "ecommerce", "e-commerce", "personal care", "brand", "subscription", "marketplace", "fmcg"),
        "manufacturing": ("manufacturing", "industrial", "factory", "predictive maintenance", "industry 4.0", "smart factory", "machine", "plant operations"),
        "climate": ("climate", "carbon", "sustainability", "circular", "emissions", "esg", "decarbonization", "unfccc", "carbon accounting"),
        "hospitality": ("hospitality", "hotel", "travel", "tourism", "lodging", "guest", "revpar", "airbnb", "booking", "restaurant"),
        "cybersecurity": ("cybersecurity", "cyber", "privacy", "nist", "cisa", "breach", "managed security", "vulnerability", "security compliance"),
        "telecom": ("telecom", "telecommunications", "broadband", "connectivity", "data center", "5g", "tower", "gsma", "fiber", "edge"),
        "automotive": ("automotive", "vehicle", "ev", "electric vehicle", "mobility", "charging", "fleet management", "nhtsa", "oica", "adas"),
        "semiconductors": ("semiconductor", "semiconductors", "chip", "electronics", "fab", "wafer", "foundry", "tsmc", "nvidia", "asml", "wsts"),
        "mining": ("mining", "metals", "critical minerals", "minerals", "materials", "usgs", "bhp", "rio tinto", "mine operations"),
        "aerospace_defense": ("aerospace", "defense", "defence", "space", "aviation", "aircraft", "procurement", "nasa", "easa", "boeing", "airbus", "sipri", "faa"),
        "media": ("media", "entertainment", "gaming", "creator", "streaming", "music", "film", "spotify", "netflix", "disney", "roblox"),
        "sports": ("sports", "sport", "fitness", "recreation", "youth sports", "club management", "team management", "fan engagement", "sports academy", "league", "coach", "athlete", "gym", "facility booking", "ticketing", "sportsbook"),
    }
    if has_any(("water treatment", "wastewater", "desalination", "water purification", "effluent", "sewage", "filtration")):
        return "water_environment"
    if has_any(("finance", "bank", "insurance", "fintech", "credit", "payments", "invoice financing", "lending", "loan", "underwriting")):
        return "finance"
    if has_any(extended["sports"]):
        return "sports"
    if has_any(extended["hospitality"]):
        return "hospitality"
    if has_any(("health", "healthcare", "medical", "pharma", "clinical", "hospital", "disease", "clinic", "dermatology", "patient", "payer", "provider", "diagnostic")):
        return "healthcare"
    if has_any(("energy", "solar", "wind", "battery", "oil", "gas", "grid", "storage", "renewable", "power")):
        return "energy"
    if has_any(("fashion", "apparel", "clothing", "luxury", "textile", "garment", "footwear", "jewelry", "beauty")):
        return "fashion"
    if has_any(("agriculture", "agri", "farmer", "crop", "apeda", "nabard", "fao", "organic", "mandi")):
        return "agriculture"
    if ("ai" in text or "agent" in text or "llm" in text) and ("workflow" in text or "automation" in text or "small business" in text or "smb" in text):
        return "ai_workflow_automation"
    for domain, terms in extended.items():
        if has_any(terms):
            return domain
    return "general_market"


def money(value: float) -> str:
    abs_value = abs(value)
    if abs_value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.2f}B"
    if abs_value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if abs_value >= 1_000:
        return f"${value / 1_000:.1f}K"
    return f"${value:.0f}"


def cagr(start: float, end: float, years: int) -> float:
    if start <= 0 or years <= 0:
        return 0.0
    return (end / start) ** (1 / years) - 1


def evidence_metric(label: str, value: str, source: str, confidence: str, note: str) -> dict[str, str]:
    return {
        "label": label,
        "value": value,
        "source": source,
        "confidence": confidence,
        "note": note,
    }


def build_evidence_first_model(topic: str, industry: str, target: str, horizon: str, domain: str) -> dict[str, Any]:
    """Return a domain-specific dashboard that refuses unsupported TAM/CAGR precision."""
    target_l = (target or "").lower()
    topic_l = (topic or "").lower()

    common = {
        "topic": topic,
        "industry": industry,
        "target": target,
        "horizon": horizon,
        "domain": domain,
        "dashboard_mode": "evidence_first",
        "headline": {
            "tam_base": None,
            "tam_base_fmt": "Not validated",
            "tam_range": "Requires domain-matched source",
            "sam": None,
            "sam_fmt": "Not validated",
            "som_range": "Requires wedge definition",
            "forecast_cagr_2026_2031": None,
            "forecast_cagr_2026_2031_fmt": "Source-gated",
        },
    }

    if domain == "fashion":
        category = "luxury/premium" if any(x in topic_l for x in ("luxury", "premium", "designer")) else "category-specific"
        common.update({
            "industry_model_name": "Fashion / Apparel Evidence Model",
            "assumptions": {
                "model_status": "No generic fashion TAM applied.",
                "required_scope": "product category + price band + buyer segment + channel + geography",
                "sizing_rule": "TAM = reachable buyers x purchase frequency x average order value, cross-checked against retail/trade/company evidence.",
            },
            "executive_metrics": [
                evidence_metric(
                    "Outlook",
                    "Low single-digit growth",
                    "McKinsey / Business of Fashion State of Fashion 2026",
                    "Medium",
                    "Applies to global fashion context; use as backdrop, not as topic TAM.",
                ),
                evidence_metric(
                    "Demand proxy",
                    "Official clothing/accessories retail-sales series",
                    "U.S. Census Monthly Retail Trade Survey",
                    "High",
                    "Use only for U.S. demand validation or as a benchmark, not for India/global TAM.",
                ),
                evidence_metric(
                    "Trade proxy",
                    "HS apparel, footwear, textiles, accessories",
                    "UN Comtrade / OTEXA / USDA ERS",
                    "High",
                    "Use for sourcing, import/export exposure, and country trade-flow benchmarking.",
                ),
                evidence_metric(
                    "Model status",
                    f"{category} wedge required",
                    "IIDATECH validation gate",
                    "High",
                    "Final TAM/CAGR withheld until category, geography, and channel map to traceable datasets.",
                ),
            ],
            "formula_rows": [
                {"model_part": "Demand TAM", "formula": "reachable target customers x purchase frequency x AOV", "required_data": "customer count, income/occasion segment, AOV, repeat rate"},
                {"model_part": "Net revenue", "formula": "gross sales - returns - discounts - marketplace/processor fees", "required_data": "return rate, markdown rate, channel commission, payment/logistics fees"},
                {"model_part": "Contribution margin", "formula": "net revenue - COGS - freight - packaging - CAC", "required_data": "landed cost, shipping subsidy, CAC, paid/organic mix"},
                {"model_part": "Inventory cash need", "formula": "initial units x landed cost + safety stock + returns reserve", "required_data": "MOQ, lead time, sell-through, reorder cadence"},
            ],
            "scenario_rows": [
                {"scenario": "Bear", "model_output": "Slow sell-through", "logic": "Demand validation weak; returns/markdowns compress margin; inventory cash tied up.", "source_status": "Requires SKU/customer cohort data."},
                {"scenario": "Base", "model_output": "Focused wedge", "logic": "One category and channel achieve repeatable CAC, sell-through, and contribution margin.", "source_status": "Requires first-cohort sales and competitor price audit."},
                {"scenario": "Bull", "model_output": "Repeatable brand engine", "logic": "Strong repeat purchase, low return rate, and sourcing discipline support category expansion.", "source_status": "Requires 2-3 replenishment cycles."},
            ],
            "driver_rows": [
                {"driver": "AOV", "why_it_matters": "Revenue per order sets gross sales and marketing payback ceiling."},
                {"driver": "Return rate", "why_it_matters": "High apparel returns can erase contribution margin."},
                {"driver": "Markdown rate", "why_it_matters": "Weak sell-through converts gross margin into clearance economics."},
                {"driver": "Inventory turns", "why_it_matters": "Slow turns create working-capital stress."},
                {"driver": "CAC payback", "why_it_matters": "D2C fashion fails when paid acquisition exceeds repeat-purchase economics."},
            ],
            "source_gate_rows": [
                {"claim_type": "TAM", "minimum_evidence": "official retail/trade dataset plus bottom-up customer model", "allowed_output": "range only until category is validated"},
                {"claim_type": "CAGR", "minimum_evidence": "category-specific analyst/official time series", "allowed_output": "cite source or mark as scenario assumption"},
                {"claim_type": "Competitor economics", "minimum_evidence": "annual reports, filings, marketplace checks, price/SKU audit", "allowed_output": "benchmark matrix, not exact share unless disclosed"},
            ],
            "methodology_notes": [
                "Fashion dashboard is source-gated and category-specific.",
                "Do not reuse AI automation, agriculture, or generic SaaS metrics for fashion.",
                "Final market size requires a product/category and geography that map to official retail, trade, or company data.",
            ],
        })
        return common

    if domain == "agriculture":
        is_india = "india" in target_l or "bharat" in target_l
        metrics = [
            evidence_metric(
                "Primary source family",
                "FAOSTAT / official ministry statistics",
                "FAO and national agriculture statistics",
                "High",
                "Use for crop, livestock, production, land use, and trade baselines.",
            ),
            evidence_metric(
                "Primary research gate",
                "12 farmers; 6 dealers; 5 buyers; 3 experts; 3 competitors",
                "IIDATECH agriculture diligence design",
                "Medium",
                "Investor-grade conclusions require field interviews and channel checks.",
            ),
        ]
        if is_india:
            metrics = [
                evidence_metric(
                    "India agri exports",
                    "$51.913B in 2024-25",
                    "APEDA Annual Administrative Report 2024-25",
                    "High",
                    "Useful for India agri-export sizing, not for every crop TAM.",
                ),
                evidence_metric(
                    "APEDA export subset",
                    "$28.590B in 2024-25",
                    "APEDA Annual Administrative Report 2024-25",
                    "High",
                    "Use for APEDA-covered product export context.",
                ),
                evidence_metric(
                    "Farmer ID base",
                    "20,559,196 farmer IDs",
                    "Ministry of Agriculture / PIB, 07.02.2024 status",
                    "High",
                    "Digital farmer ID count is a public-infrastructure proxy, not total farmer universe.",
                ),
                evidence_metric(
                    "Rural survey base",
                    "100,000 households",
                    "NABARD NAFIS 2.0",
                    "High",
                    "Use for rural finance/income context where relevant.",
                ),
            ]
        common.update({
            "industry_model_name": "Agriculture / Agribusiness Evidence Model",
            "assumptions": {
                "model_status": "No generic agriculture TAM applied.",
                "required_scope": "crop/value chain + farmer or buyer segment + region + channel",
                "sizing_rule": "TAM = production or buyer volume x realized price, cross-checked against trade/procurement/channel data.",
            },
            "executive_metrics": metrics,
            "formula_rows": [
                {"model_part": "Production TAM", "formula": "addressable production volume x farmgate/wholesale price", "required_data": "crop output, price series, geography, seasonality"},
                {"model_part": "Procurement revenue", "formula": "procured volume x take rate or gross margin", "required_data": "farmer participation, buyer contracts, wastage, quality grade"},
                {"model_part": "Export opportunity", "formula": "eligible export volume x FOB price x reachable buyer share", "required_data": "APEDA/Comtrade data, certifications, destination demand"},
                {"model_part": "Working capital", "formula": "procurement value x cash-conversion cycle", "required_data": "payment terms, inventory days, buyer receivables"},
            ],
            "scenario_rows": [
                {"scenario": "Bear", "model_output": "Commodity margin squeeze", "logic": "Price volatility, low farmer adoption, quality failures, or buyer concentration reduce margin.", "source_status": "Requires mandi/procurement price series."},
                {"scenario": "Base", "model_output": "Verified value chain", "logic": "One crop/region/channel achieves repeatable procurement and buyer demand.", "source_status": "Requires farmer/dealer/buyer interviews."},
                {"scenario": "Bull", "model_output": "Export or processing scale", "logic": "Certification, aggregation, and buyer contracts support premium pricing and repeat volume.", "source_status": "Requires export and buyer evidence."},
            ],
            "driver_rows": [
                {"driver": "Yield/volume", "why_it_matters": "Sets physical market capacity."},
                {"driver": "Farmgate and wholesale price", "why_it_matters": "Determines TAM and gross spread."},
                {"driver": "Quality grade/rejection", "why_it_matters": "Controls export eligibility and processing yield."},
                {"driver": "Procurement working capital", "why_it_matters": "Agribusiness can fail despite demand if cash cycle is underfunded."},
                {"driver": "Certification/logistics", "why_it_matters": "Required for higher-value export and organized-buyer channels."},
            ],
            "source_gate_rows": [
                {"claim_type": "Crop TAM", "minimum_evidence": "official production and price series", "allowed_output": "bottom-up calculation with geography and season stated"},
                {"claim_type": "Export opportunity", "minimum_evidence": "APEDA/Comtrade destination data and product code", "allowed_output": "commodity/channel-specific range"},
                {"claim_type": "Farmer economics", "minimum_evidence": "field interviews plus input/output price checks", "allowed_output": "validated unit economics table"},
            ],
            "methodology_notes": [
                "Agriculture dashboard is crop/value-chain specific.",
                "India export figures are not reused as TAM unless the topic is India agri-export relevant.",
                "Primary fieldwork is required before investor-grade farmer/channel economics.",
            ],
        })
        return common

    if domain == "healthcare":
        if any(x in topic_l for x in ("diagnostic", "lab", "laboratory", "clia", "clfs", "ivd")):
            wedge = "diagnostic lab billing / reimbursement"
            sizing_rule = "TAM = addressable tests or labs x reimbursed price or billing fee, filtered by CLFS/CPT/test menu, payer mix, CLIA status, and lab workflow scope."
        elif any(x in topic_l for x in ("registry", "quality reporting", "nhsn", "measure reporting")):
            wedge = "clinical registry and compliance reporting"
            sizing_rule = "TAM = reporting facilities x annual software/service fee, filtered by required measures, abstraction burden, audit risk, and CMS/registry mandate."
        elif any(x in topic_l for x in ("samd", "clinical decision support", "medical device", "fda", "mdr", "cdsco", "diagnosis", "treatment")):
            wedge = "regulated CDS / SaMD"
            sizing_rule = "TAM = cleared/approved eligible sites x license/usage price, gated by regulatory classification, clinical evidence, QMS, reimbursement, and post-market obligations."
        elif any(x in topic_l for x in ("practice", "coding", "payer portal", "physician")):
            wedge = "physician-practice billing"
            sizing_rule = "TAM = addressable practices x claims/month x fee per claim or billing fee percent, filtered by specialty, payer mix, PM/EHR integration, and staff workflow."
        else:
            wedge = "hospital revenue cycle"
            sizing_rule = "TAM = addressable hospitals x net patient revenue affected x denial/recovery opportunity x vendor take rate or ACV, filtered by payer mix, EHR integration, procurement, and RCM workflow."
        common.update({
            "industry_model_name": "Healthcare Billing / RCM Evidence Model",
            "assumptions": {
                "model_status": "No blended healthcare TAM applied.",
                "required_scope": "one wedge: hospital RCM, physician-practice billing, clinical registry compliance, diagnostic lab reimbursement, or regulated CDS/SaMD",
                "selected_wedge": wedge,
                "sizing_rule": sizing_rule,
            },
            "executive_metrics": [
                evidence_metric("Hospital denominator", "6,093 U.S. hospitals; 5,112 community hospitals", "American Hospital Association Fast Facts 2025", "High", "Use for hospital RCM account-count filters, not whole-market TAM."),
                evidence_metric("Hospital spending denominator", "$1,634.7B U.S. hospital expenditures in 2024", "CMS National Health Expenditure Accounts", "High", "Use only as a denominator before applying denial/workflow/software spend filters."),
                evidence_metric("RCM pain survey", "48.2% cite commercial denial volume as greatest revenue-cycle threat", "HFMA / Knowtion Health 2025 survey", "Medium-High", "Use as hospital RCM buyer-pain evidence with sponsor/sample disclosure."),
                evidence_metric("Practice denial survey", "8% first-submission denial rate; 60% report higher denial rates", "MGMA 2024 Stat poll", "Medium-High", "Use for physician-practice billing, not hospital CFO validation."),
                evidence_metric("Diagnostic lab reimbursement source", "2026 Q2 CLFS file has 2,179 records", "CMS Clinical Laboratory Fee Schedule", "High", "Use for diagnostic lab reimbursement/test-menu analysis."),
                evidence_metric("Regulatory gate", "510(k) goal 90 FDA days after submission; pathway may require QMS and validation before submission", "FDA 510(k) / CDS guidance", "High", "Use as a launch gate only when product is regulated CDS/SaMD or diagnostic software."),
            ],
            "formula_rows": [
                {"model_part": "Hospital RCM", "formula": "eligible hospitals x net patient revenue affected x denial/recovery opportunity x ACV or recovery fee", "required_data": "hospital count, NPR, denial rate/category, recoverable amount, price model, implementation capacity"},
                {"model_part": "Practice billing", "formula": "eligible practices x claims/month x fee/claim or billing fee %", "required_data": "specialty/practice count, claim volume, denial rate, payer portal burden, billing fee"},
                {"model_part": "Clinical registry", "formula": "reporting facilities x annual registry/compliance software or service fee", "required_data": "registry mandate, facility count, abstraction hours, audit/compliance cost"},
                {"model_part": "Diagnostic lab", "formula": "tests or labs x reimbursed price x billing/recovery fee or workflow ACV", "required_data": "CLFS/CPT/test menu, test volume, payer mix, CLIA status, denial categories"},
                {"model_part": "Regulated software", "formula": "eligible approved sites x license/usage price after regulatory clearance", "required_data": "FDA/EU/CDSCO classification, QMS cost, validation evidence, sales cycle, post-market cost"},
            ],
            "scenario_rows": [
                {"scenario": "Bear", "model_output": "Admin workflow only", "logic": "Product avoids clinical claims but buyer pain or budget is not validated; procurement and integration slow adoption.", "source_status": "Requires CFO/RCM director calls and implementation quotes."},
                {"scenario": "Base", "model_output": "One RCM/lab/registry wedge validated", "logic": "One buyer type, workflow, price model, and source-backed pain point support a bottom-up model.", "source_status": "Requires completed interviews, source-matched denominator, and pilot ROI."},
                {"scenario": "Bull", "model_output": "Regulated moat or network workflow", "logic": "Regulatory capability, payer/provider integration, and repeatable implementation create defensibility.", "source_status": "Requires regulatory memo, QMS/validation budget, and retention proof."},
            ],
            "driver_rows": [
                {"driver": "Wedge definition", "why_it_matters": "Hospital RCM, practice billing, registries, labs, and SaMD have different buyers and economics."},
                {"driver": "Denial/recovery dollars or reimbursed test volume", "why_it_matters": "Sets revenue pool and ROI, not generic healthcare spend."},
                {"driver": "Integration and implementation weeks", "why_it_matters": "Controls gross margin, sales cycle, and capacity to scale."},
                {"driver": "Regulatory pathway", "why_it_matters": "Can become an existential launch and capital-burn gate."},
                {"driver": "Buyer validation", "why_it_matters": "Funding-ready models require CFO/RCM/lab/registry/payer interviews, not unrelated ecommerce or SMB proxies."},
            ],
            "source_gate_rows": [
                {"claim_type": "TAM", "minimum_evidence": "source-backed denominator plus wedge-specific price or recovery formula", "allowed_output": "wedge-specific range only"},
                {"claim_type": "Regulatory timeline", "minimum_evidence": "FDA/EU/CDSCO/CMS source plus product classification memo", "allowed_output": "pathway and burn model, not generic timeline"},
                {"claim_type": "Willingness to pay", "minimum_evidence": "completed buyer interviews or signed pilot/quote evidence", "allowed_output": "hypothesis until buyer validation exists"},
            ],
            "methodology_notes": [
                "The model refuses a single medical billing TAM.",
                "Public surveys can validate pain but do not replace completed buyer interviews.",
                "Regulatory scope is modeled as a launch gate and burn driver whenever product claims affect clinical decisions, diagnostics, or device pathways.",
            ],
        })
        return common

    profile_map = {
        "healthcare": {
            "name": "Healthcare Evidence Model",
            "required_scope": "condition/service + patient/provider buyer + care setting + geography",
            "metrics": [
                evidence_metric("Sizing status", "Source-gated", "official health statistics / regulator data", "High", "Use disease prevalence, procedure volume, or provider spend only when matched to topic."),
                evidence_metric("Regulatory gate", "Required", "FDA/EMA/local regulator and payer rules", "High", "Healthcare forecasts must include approval, reimbursement, privacy, and clinical workflow constraints."),
                evidence_metric("Economic basis", "patient volume x reimbursed price or provider spend", "IIDATECH formula gate", "Medium", "Do not substitute generic digital-health market figures."),
                evidence_metric("Evidence gap", "Clinical/provider validation needed", "primary interviews", "Medium", "Needs clinician, payer, and patient workflow evidence."),
            ],
        },
        "finance": {
            "name": "Finance / Fintech Evidence Model",
            "required_scope": "financial product + customer segment + regulatory market + distribution channel",
            "metrics": [
                evidence_metric("Sizing status", "Source-gated", "central bank/regulator/company filings", "High", "Use transaction volume, AUM, loan book, or fee pool matched to the topic."),
                evidence_metric("Regulatory gate", "Required", "central bank/securities/insurance regulator", "High", "Licensing, KYC/AML, capital, and consumer protection shape the model."),
                evidence_metric("Economic basis", "volume x take rate or spread", "IIDATECH formula gate", "Medium", "Final model needs loss, fraud, funding, and compliance costs."),
                evidence_metric("Evidence gap", "Cohort and risk data needed", "primary diligence", "Medium", "Needs customer acquisition, default/fraud, retention, and unit-risk evidence."),
            ],
        },
        "energy": {
            "name": "Energy Evidence Model",
            "required_scope": "asset/resource + customer/offtaker + region + policy/tariff structure",
            "metrics": [
                evidence_metric("Sizing status", "Source-gated", "EIA/IEA/grid regulator/project filings", "High", "Use capacity, generation, tariff, or offtake data matched to geography."),
                evidence_metric("Policy gate", "Required", "energy ministry/regulator/incentive rules", "High", "Policy and grid rules can dominate economics."),
                evidence_metric("Economic basis", "capacity x utilization x realized price", "IIDATECH formula gate", "Medium", "Final model needs capex, opex, load factor, tariff, and financing costs."),
                evidence_metric("Evidence gap", "Project economics needed", "developer/offtaker diligence", "Medium", "Needs site, interconnection, capex, and offtake validation."),
            ],
        },
        "water_environment": {
            "name": "Water / Environmental Infrastructure Evidence Model",
            "required_scope": "water problem + customer/plant type + geography + treatment technology + regulatory driver",
            "metrics": [
                evidence_metric("Sizing status", "Source-gated", "water regulator / utility / government datasets", "High", "Use plant counts, discharge volume, tariff/capex, and compliance requirements matched to the topic."),
                evidence_metric("Regulatory gate", "Required", "pollution-control board / environmental regulator", "High", "Water treatment demand often depends on discharge permits, standards, and enforcement."),
                evidence_metric("Economic basis", "flow volume x treatment cost or project capex", "IIDATECH formula gate", "Medium", "Final model needs m3/day, technology choice, capex, opex, sludge/disposal, and uptime assumptions."),
                evidence_metric("Evidence gap", "Plant-level validation needed", "operator/vendor/customer interviews", "Medium", "Needs facility counts, effluent characteristics, vendor quotes, and compliance pain."),
            ],
        },
        "sports": {
            "name": "Sports / Fitness Evidence Model",
            "required_scope": "one wedge: youth academy, club/league management, fitness facility, fan engagement, event/ticketing, or sports media",
            "metrics": [
                evidence_metric("Participation denominator", "Source-gated", "SFIA / Active Lives / AusPlay / Eurobarometer / local sports ministry", "High", "Use country-matched participation surveys first; do not convert all active people into software buyers."),
                evidence_metric("Revenue basis", "registration fees, subscriptions, memberships, ticketing, sponsorship, or media ARPU", "pricing pages / filings / audited club reports", "Medium-High", "Sports wedges have different monetization; keep youth software, gyms, clubs, media, and betting separate."),
                evidence_metric("Operational constraint", "seasonality + coach/admin capacity + safety/compliance", "club/operator/practitioner sources", "Medium", "Sports businesses often fail on operations, scheduling, volunteer/admin burden, or facility utilization."),
                evidence_metric("Evidence gap", "buyer/operator validation needed", "published surveys, practitioner threads, interviews", "Medium", "Use Reddit/YouTube/podcast evidence only as qualitative voice; final numbers need filings, pricing, or surveys."),
            ],
        },
        "general_market": {
            "name": "General Evidence Model",
            "required_scope": "product/use case + buyer segment + geography + channel",
            "metrics": [
                evidence_metric("Sizing status", "Source-gated", "official statistics/company filings/analyst sources", "High", "No generic TAM is shown until domain-specific evidence is attached."),
                evidence_metric("Model requirement", "Bottom-up wedge", "IIDATECH formula gate", "High", "Define customers, price, frequency, and channel before modeling."),
                evidence_metric("Competitive basis", "Source-gated", "filings/pricing pages/channel checks", "Medium", "Competitor share requires disclosed data or proxy methodology."),
                evidence_metric("Evidence gap", "Primary validation needed", "customer/interview plan", "Medium", "Needs buyer calls and pricing/channel checks."),
            ],
        },
    }
    profile = profile_map.get(domain, profile_map["general_market"])
    common.update({
        "industry_model_name": profile["name"],
        "assumptions": {
            "model_status": "No generic TAM model applied.",
            "required_scope": profile["required_scope"],
            "sizing_rule": "TAM/SAM/SOM can be shown only after topic-specific source evidence and explicit formulas are populated.",
        },
        "executive_metrics": profile["metrics"],
        "formula_rows": [
            {"model_part": "TAM", "formula": "eligible customers or volume x price/frequency", "required_data": "official or audited market volume and topic-specific price"},
            {"model_part": "SAM", "formula": "TAM x reachable geography/channel/use-case share", "required_data": "distribution constraints and buyer eligibility"},
            {"model_part": "SOM", "formula": "SAM x realistic penetration over period", "required_data": "sales capacity, conversion, churn/retention, competitor response"},
            {"model_part": "Unit economics", "formula": "revenue - COGS - acquisition - service/compliance costs", "required_data": "cost stack and cohort behavior"},
        ],
        "scenario_rows": [
            {"scenario": "Bear", "model_output": "Validation incomplete", "logic": "Weak source coverage or unclear buyer economics blocks a numeric model.", "source_status": "Needs official/filing/primary data."},
            {"scenario": "Base", "model_output": "Narrow wedge validated", "logic": "A defined buyer/use case supports explicit bottom-up sizing.", "source_status": "Needs price, volume, and adoption evidence."},
            {"scenario": "Bull", "model_output": "Repeatable expansion", "logic": "Evidence supports expansion into adjacent customer segments or regions.", "source_status": "Needs cohort and competitive proof."},
        ],
        "driver_rows": [
            {"driver": "Customer/volume base", "why_it_matters": "Defines the addressable universe."},
            {"driver": "Price or take rate", "why_it_matters": "Translates volume into revenue pool."},
            {"driver": "Adoption/penetration", "why_it_matters": "Converts TAM/SAM into realistic obtainable revenue."},
            {"driver": "Churn/retention", "why_it_matters": "Determines lifetime value and forecast durability."},
            {"driver": "Cost to serve", "why_it_matters": "Controls contribution margin and valuation quality."},
        ],
        "source_gate_rows": [
            {"claim_type": "Market size", "minimum_evidence": "two domain-matched sources or one official source plus bottom-up model", "allowed_output": "range with assumptions"},
            {"claim_type": "Forecast", "minimum_evidence": "historical time series or named adoption drivers", "allowed_output": "scenario forecast"},
            {"claim_type": "Valuation", "minimum_evidence": "unit economics and comparable company/transaction evidence", "allowed_output": "sensitivity table"},
        ],
        "methodology_notes": [
            "Generic market assumptions were intentionally disabled.",
            "The dashboard shows validation gates until domain-specific data is sufficient.",
            "This prevents cross-industry metric contamination and unsupported TAM/CAGR claims.",
        ],
    })
    return common


def build_market_model(topic: str, industry: str, target: str, horizon: str) -> dict[str, Any]:
    domain = classify_model_domain(topic, industry)
    if domain != "ai_workflow_automation":
        return build_evidence_first_model(topic, industry, target, horizon, domain)
    country_specific_target = (target or "").strip().lower() not in {
        "",
        "global",
        "worldwide",
        "international",
        "regional database only",
    }

    inputs = MarketModelInputs()
    years = list(range(inputs.start_year, inputs.end_year + 1))
    adoption_rates = {
        2026: 0.03,
        2027: 0.06,
        2028: 0.10,
        2029: 0.15,
        2030: 0.21,
        2031: 0.27,
    }

    reachable = inputs.reachable_smbs_m * 1_000_000
    tam_base = reachable * inputs.base_acv
    tam_conservative = 20_000_000 * inputs.conservative_acv
    tam_upside = reachable * inputs.upside_acv
    sam = tam_base * inputs.sam_share
    som_low = sam * inputs.som_low_share
    som_high = sam * inputs.som_high_share

    forecast_rows = []
    for year in years:
        adoption = adoption_rates[year]
        adopted_accounts = reachable * adoption
        revenue_pool = adopted_accounts * inputs.base_acv
        retained_revenue = revenue_pool * (1 - inputs.annual_churn)
        forecast_rows.append({
            "year": year,
            "adoption_rate": adoption,
            "adopted_accounts": round(adopted_accounts),
            "gross_revenue_pool": round(revenue_pool),
            "retained_after_30pct_churn": round(retained_revenue),
            "gross_revenue_pool_fmt": money(revenue_pool),
            "retained_after_churn_fmt": money(retained_revenue),
        })

    scenario_rows = [
        {
            "scenario": "Bear",
            "reachable_smbs": 20_000_000,
            "acv": inputs.conservative_acv,
            "tam": round(tam_conservative),
            "tam_fmt": money(tam_conservative),
            "logic": "Low willingness to pay; mostly lightweight self-serve automation.",
        },
        {
            "scenario": "Base",
            "reachable_smbs": round(reachable),
            "acv": inputs.base_acv,
            "tam": round(tam_base),
            "tam_fmt": money(tam_base),
            "logic": "Software-mature SMBs buy governed workflow bundles.",
        },
        {
            "scenario": "Bull",
            "reachable_smbs": round(reachable),
            "acv": inputs.upside_acv,
            "tam": round(tam_upside),
            "tam_fmt": money(tam_upside),
            "logic": "Higher-volume workflows, vertical bundles, and managed automation expand ACV.",
        },
    ]

    sensitivity_rows = []
    for smbs_m in (20, 30, 50):
        for acv in (600, 2400, 6000):
            tam = smbs_m * 1_000_000 * acv
            sensitivity_rows.append({
                "reachable_smbs_m": smbs_m,
                "acv": acv,
                "tam": round(tam),
                "tam_fmt": money(tam),
            })

    workload_rows = []
    for runs in (50, 500, 1_000, 10_000):
        model_cost = runs * inputs.model_cost_per_run
        search_cost = runs * inputs.web_search_share * inputs.web_search_cost_per_call
        gross_margin = (inputs.base_monthly_price - model_cost - search_cost) / inputs.base_monthly_price
        workload_rows.append({
            "monthly_runs": runs,
            "model_cost": round(model_cost, 2),
            "web_search_cost": round(search_cost, 2),
            "gross_margin_before_infra_support": round(gross_margin, 3),
            "gross_margin_pct": f"{gross_margin:.1%}",
        })

    regional_rows = [
        {"region": "United States / North America", "tam": 20_000_000_000, "tam_fmt": "$20.00B", "rationale": "High SaaS maturity, large SBA small-business base, mature self-serve software channel."},
        {"region": "Europe", "tam": 15_000_000_000, "tam_fmt": "$15.00B", "rationale": "Large SME universe; stronger privacy and AI governance requirements."},
        {"region": "APAC", "tam": 25_000_000_000, "tam_fmt": "$25.00B", "rationale": "Large MSME universe; uneven digital maturity and localization requirements."},
        {"region": "Rest of world", "tam": 12_000_000_000, "tam_fmt": "$12.00B", "rationale": "Selective opportunity in digitally mature services, ecommerce, and logistics clusters."},
    ]

    vendor_capture_rows = [
        {"vendor_group": "Zapier", "som_low_capture": "25%", "som_high_capture": "40%", "capture_value_range": f"{money(som_low * 0.25)}-{money(som_high * 0.40)}"},
        {"vendor_group": "Make", "som_low_capture": "10%", "som_high_capture": "20%", "capture_value_range": f"{money(som_low * 0.10)}-{money(som_high * 0.20)}"},
        {"vendor_group": "n8n", "som_low_capture": "5%", "som_high_capture": "15%", "capture_value_range": f"{money(som_low * 0.05)}-{money(som_high * 0.15)}"},
        {"vendor_group": "Microsoft / embedded copilots", "som_low_capture": "20%", "som_high_capture": "35%", "capture_value_range": f"{money(som_low * 0.20)}-{money(som_high * 0.35)}"},
        {"vendor_group": "Vertical / services-led vendors", "som_low_capture": "15%", "som_high_capture": "30%", "capture_value_range": f"{money(som_low * 0.15)}-{money(som_high * 0.30)}"},
    ]

    return {
        "topic": topic,
        "industry": industry,
        "target": target,
        "horizon": horizon,
        "domain": domain,
        "dashboard_mode": "bottom_up_tam",
        "industry_model_name": "AI Workflow Automation Bottom-Up Model",
        "assumptions": {
            "reachable_smbs": round(reachable),
            "base_acv": inputs.base_acv,
            "sam_share": inputs.sam_share,
            "som_share_range": f"{inputs.som_low_share:.0%}-{inputs.som_high_share:.0%}",
            "annual_churn_stress": inputs.annual_churn,
            "web_search_share": inputs.web_search_share,
            "model_cost_per_run": inputs.model_cost_per_run,
        },
        "headline": {
            "tam_base": round(tam_base),
            "tam_base_fmt": "Source-gated for country report" if country_specific_target else money(tam_base),
            "tam_range": "Withheld until country-specific SMB filter and ACV are sourced" if country_specific_target else f"{money(tam_conservative)}-{money(tam_upside)}",
            "sam": round(sam),
            "sam_fmt": "Source-gated for country report" if country_specific_target else money(sam),
            "som_range": "Withheld until channel reach and capture assumptions are sourced" if country_specific_target else f"{money(som_low)}-{money(som_high)}",
            "forecast_cagr_2026_2031": cagr(forecast_rows[0]["gross_revenue_pool"], forecast_rows[-1]["gross_revenue_pool"], 5),
            "forecast_cagr_2026_2031_fmt": "Withheld; global adoption curve is not a country CAGR" if country_specific_target else f"{cagr(forecast_rows[0]['gross_revenue_pool'], forecast_rows[-1]['gross_revenue_pool'], 5):.1%}",
        },
        "executive_metrics": [
            evidence_metric(
                "Base TAM",
                "Withheld for country report" if country_specific_target else money(tam_base),
                "Country-specific source gate" if country_specific_target else "IIDATECH bottom-up SMB model",
                "Low" if country_specific_target else "Medium",
                "Requires local SMB denominator, software-maturity filter, ACV, adoption, and churn evidence." if country_specific_target else "Transparent assumption model, not a third-party market-size estimate.",
            ),
            evidence_metric(
                "SAM",
                "Withheld for country report" if country_specific_target else money(sam),
                "Country-specific source gate" if country_specific_target else "30% serviceable-share assumption",
                "Low" if country_specific_target else "Medium",
                "Requires validation by geography, channel, and workflow wedge.",
            ),
            evidence_metric(
                "SOM range",
                "Withheld for country report" if country_specific_target else f"{money(som_low)}-{money(som_high)}",
                "Country-specific source gate" if country_specific_target else "1-3% SAM capture assumption",
                "Low" if country_specific_target else "Medium",
                "Use as scenario range only after channel reach and acquisition capacity are validated.",
            ),
            evidence_metric(
                "Forecast CAGR",
                "Withheld for country report" if country_specific_target else f"{cagr(forecast_rows[0]['gross_revenue_pool'], forecast_rows[-1]['gross_revenue_pool'], 5):.1%}",
                "Country-specific source gate" if country_specific_target else "Adoption-curve model",
                "Low" if country_specific_target else "Medium",
                "The global adoption curve must not be displayed as a country-specific market CAGR.",
            ),
        ],
        "scenario_rows": scenario_rows,
        "forecast_rows": forecast_rows,
        "sensitivity_rows": sensitivity_rows,
        "workload_rows": workload_rows,
        "regional_rows": regional_rows,
        "vendor_capture_rows": vendor_capture_rows,
        "formula_rows": [
            {"model_part": "TAM", "formula": "reachable software-mature SMBs x annual contract value", "required_data": "validated SMB universe and ACV distribution"},
            {"model_part": "SAM", "formula": "TAM x serviceable share", "required_data": "geography, channel, workflow, and integration reach"},
            {"model_part": "SOM", "formula": "SAM x realistic capture", "required_data": "sales capacity, retention, implementation capacity"},
            {"model_part": "Retained revenue", "formula": "gross revenue pool x (1 - churn)", "required_data": "workflow-level churn and expansion data"},
        ],
        "driver_rows": [
            {"driver": "Reachable SMB universe", "why_it_matters": "Largest swing factor in TAM."},
            {"driver": "ACV", "why_it_matters": "Determines monetization and buyer willingness to pay."},
            {"driver": "Adoption curve", "why_it_matters": "Controls forecast timing."},
            {"driver": "Churn", "why_it_matters": "Reduces retained revenue and LTV."},
            {"driver": "Cost per successful run", "why_it_matters": "Controls gross margin under high workflow volume."},
        ],
        "source_gate_rows": [
            {"claim_type": "SMB universe", "minimum_evidence": "official SMB statistics by region", "allowed_output": "region-specific reachable business estimate"},
            {"claim_type": "Vendor capture", "minimum_evidence": "vendor revenue/customer disclosure or audited proxy", "allowed_output": "range/proxy only"},
            {"claim_type": "Unit economics", "minimum_evidence": "workflow usage, token/search cost, retry/support burden", "allowed_output": "sensitivity table"},
        ],
        "methodology_notes": [
            "TAM = reachable software-mature SMBs x annual contract value.",
            "SAM = 30% of base TAM to reflect immediately serviceable channels and markets.",
            "SOM = 1-3% of SAM for a realistic 3-5 year platform capture range.",
            "Forecast revenue pool = reachable SMBs x adoption rate x ACV.",
            "Retained revenue pool applies a 30% annual churn stress case.",
            "Unit economics are before infrastructure, support, retries, and implementation labor.",
        ],
    }
