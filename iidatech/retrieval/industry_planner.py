"""Industry-aware retrieval planner for IIDATECH research layer."""

from __future__ import annotations

from typing import Any

_FESTIVE_DOMAINS = frozenset({
    "festive_retail", "event_services", "wedding_services", "decor_retail", "gifting_retail",
})
_SKINCARE_DOMAINS = frozenset({"d2c_skincare", "ecommerce_retail"})


def resolve_retrieval_profile_key(domain: str, topic: str = "", industry: str = "") -> str:
    blob = f"{domain} {topic} {industry}".lower()
    if domain in _FESTIVE_DOMAINS:
        return domain
    if any(
        t in blob
        for t in (
            "car retail",
            "garage",
            "garage repair",
            "auto repair",
            "service center",
            "luxury car",
            "workshop",
            "dealership",
        )
    ):
        return "automotive_retail"
    if domain in {"crm_automation", "b2b_saas", "revops_sales_automation", "ai_workflow_automation"}:
        return "saas_software"
    if domain in {"healthcare_saas", "dental_clinics", "healthcare_wellness"} or any(
        t in blob
        for t in (
            "healthcare",
            "clinical",
            "hospital",
            "dental",
            "psychology",
            "mental health",
            "sports psychology",
            "athlete wellbeing",
            "nhs",
            "patient",
        )
    ):
        return "healthcare_wellness"
    skincare_signal = any(
        t in blob for t in ("skincare", "cosmetic", "beauty", "serum", "moisturizer", "organic skincare", "nykaa", "purplle")
    )
    festive_signal = any(
        t in blob for t in ("ganesh", "diwali", "navratri", "mandap", "puja", "rangoli", "decoration kit", "festive decor")
    )
    if festive_signal and not skincare_signal:
        if domain in {"event_services", "wedding_services", "decor_retail", "festive_retail", "gifting_retail"}:
            return domain
        if any(t in blob for t in ("wedding", "mandap", "sangeet", "bridal")):
            return "wedding_services"
        if any(t in blob for t in ("rental", "event setup", "light show", "drone")):
            return "event_services"
        return "festive_retail"
    if domain in _SKINCARE_DOMAINS or (
        domain in {"consumer", "fashion"} and skincare_signal
    ):
        return "ecommerce_retail"
    if domain == "automotive":
        return "automotive_retail"
    if domain in {"local_services", "home_services"}:
        return domain
    if domain == "creator_business":
        return "creator_business"
    return "general_market"


def get_industry_retrieval_profile(domain: str, topic: str = "", industry: str = "") -> dict[str, Any]:
    key = resolve_retrieval_profile_key(domain, topic, industry)
    profiles = {
        "automotive_retail": {
            "profile_id": "automotive_retail",
            "priority_sources": [
                "cardekho.com",
                "carwale.com",
                "team-bhp.com",
                "bmw.in",
                "mercedes-benz.co.in",
                "justdial.com",
                "google.com/maps",
            ],
            "competitor_sources": ["cardekho.com", "carwale.com", "team-bhp.com", "dealer websites", "service menus"],
            "pricing_sources": ["dealer service pages", "cardekho.com", "oem service packages"],
            "buyer_sources": ["team-bhp.com", "google reviews", "youtube.com", "reddit.com"],
            "required_evidence_types": ["named competitors", "service pricing", "customer complaints", "dealer density"],
        },
        "saas_software": {
            "profile_id": "saas_software",
            "priority_sources": [
                "g2.com",
                "capterra.com",
                "producthunt.com",
                "reddit.com",
                "hubspot.com",
                "salesforce.com",
                "zoho.com",
                "pipedrive.com",
            ],
            "competitor_sources": ["g2.com", "capterra.com", "producthunt.com", "official vendor sites"],
            "pricing_sources": ["pricing pages", "g2.com", "capterra.com", "vendor pricing"],
            "buyer_sources": ["reddit.com", "g2 reviews", "capterra reviews", "trustpilot.com"],
            "required_evidence_types": ["competitors", "pricing tiers", "reviews", "integration/churn pain"],
        },
        "ecommerce_retail": {
            "profile_id": "ecommerce_retail",
            "priority_sources": ["flipkart.com", "amazon.in", "nykaa.com", "purplle.com", "trustpilot.com", "reddit.com"],
            "competitor_sources": ["nykaa.com", "purplle.com", "flipkart.com", "amazon.in", "brand sites"],
            "pricing_sources": ["marketplace listings", "brand pricing pages", "nykaa.com"],
            "buyer_sources": ["reddit.com", "trustpilot.com", "amazon reviews", "youtube.com"],
            "required_evidence_types": ["competitors", "pricing", "reviews", "CAC/margin proxies"],
        },
        "festive_retail": {
            "profile_id": "festive_retail",
            "priority_sources": ["amazon.in", "flipkart.com", "indiamart.com", "etsy.com", "meesho.com", "reddit.com"],
            "competitor_sources": ["amazon.in", "flipkart.com", "indiamart.com", "etsy.com", "festive decor brands"],
            "pricing_sources": ["amazon.in", "flipkart.com", "indiamart.com", "brand storefronts"],
            "buyer_sources": ["reddit.com", "apartment society forums", "facebook groups", "youtube.com"],
            "required_evidence_types": ["festive decor competitors", "kit pricing", "society buyer reviews"],
        },
        "event_services": {
            "profile_id": "event_services",
            "priority_sources": ["wedmegood.com", "weddingz.in", "justdial.com", "indiamart.com", "google.com/maps"],
            "competitor_sources": ["wedmegood.com", "weddingz.in", "event planners", "rental vendors"],
            "pricing_sources": ["vendor quote pages", "wedmegood.com", "indiamart.com"],
            "buyer_sources": ["reddit.com", "google reviews", "wedding forums", "youtube.com"],
            "required_evidence_types": ["named event vendors", "rental pricing", "buyer reviews"],
        },
        "wedding_services": {
            "profile_id": "wedding_services",
            "priority_sources": ["wedmegood.com", "weddingz.in", "shaadi.com", "justdial.com", "indiamart.com"],
            "competitor_sources": ["wedmegood.com", "weddingz.in", "mandap vendors", "wedding decorators"],
            "pricing_sources": ["wedding package pages", "vendor menus", "indiamart.com"],
            "buyer_sources": ["reddit.com", "wedding forums", "google reviews"],
            "required_evidence_types": ["wedding vendors", "package pricing", "couple reviews"],
        },
        "decor_retail": {
            "profile_id": "decor_retail",
            "priority_sources": ["amazon.in", "flipkart.com", "indiamart.com", "etsy.com", "pepperfry.com", "urbanladder.com"],
            "competitor_sources": ["amazon.in", "flipkart.com", "decor brands", "indiamart.com"],
            "pricing_sources": ["marketplace listings", "brand sites", "indiamart.com"],
            "buyer_sources": ["reddit.com", "apartment society forums", "youtube.com"],
            "required_evidence_types": ["decor competitors", "product pricing", "buyer reviews"],
        },
        "gifting_retail": {
            "profile_id": "gifting_retail",
            "priority_sources": ["amazon.in", "flipkart.com", "fnp.com", "igp.com", "etsy.com"],
            "competitor_sources": ["fnp.com", "igp.com", "amazon.in", "flipkart.com"],
            "pricing_sources": ["hamper pricing pages", "marketplace listings"],
            "buyer_sources": ["reddit.com", "trustpilot.com", "google reviews"],
            "required_evidence_types": ["gift competitors", "hamper pricing", "buyer reviews"],
        },
        "local_services": {
            "profile_id": "local_services",
            "priority_sources": ["justdial.com", "urbancompany.com", "google.com/maps", "sulekha.com"],
            "competitor_sources": ["justdial.com", "urbancompany.com", "local vendor listings"],
            "pricing_sources": ["service menus", "justdial.com", "urbancompany.com"],
            "buyer_sources": ["google reviews", "reddit.com", "local forums"],
            "required_evidence_types": ["local competitors", "service pricing", "reviews"],
        },
        "home_services": {
            "profile_id": "home_services",
            "priority_sources": ["urbancompany.com", "justdial.com", "google.com/maps", "housejoy.in"],
            "competitor_sources": ["urbancompany.com", "housejoy.in", "local contractors"],
            "pricing_sources": ["service rate cards", "urbancompany.com"],
            "buyer_sources": ["google reviews", "reddit.com", "apartment forums"],
            "required_evidence_types": ["service providers", "visit pricing", "reviews"],
        },
        "creator_business": {
            "profile_id": "creator_business",
            "priority_sources": ["youtube.com", "instagram.com", "linkedin.com", "reddit.com"],
            "competitor_sources": ["creator platforms", "agency sites", "influencer marketplaces"],
            "pricing_sources": ["sponsorship rate cards", "creator tool pricing"],
            "buyer_sources": ["reddit.com", "creator forums", "youtube comments"],
            "required_evidence_types": ["creator competitors", "monetization pricing", "audience signal"],
        },
        "healthcare_wellness": {
            "profile_id": "healthcare_wellness",
            "priority_sources": [
                "pubmed.ncbi.nlm.nih.gov",
                "nhs.uk",
                "nice.org.uk",
                "who.int",
                "cdc.gov",
                "hospital websites",
                "g2.com",
            ],
            "competitor_sources": ["practo.com", "zocdoc.com", "clinic software vendors", "hospital systems"],
            "pricing_sources": ["clinic SaaS pricing pages", "g2.com healthcare", "vendor pricing"],
            "buyer_sources": ["reddit.com", "practitioner forums", "patient review sites", "pubmed"],
            "required_evidence_types": ["named competitors", "clinical pricing", "patient/practitioner pain", "regulatory context"],
        },
        "general_market": {
            "profile_id": "general_market",
            "priority_sources": ["official statistics", "company sites"],
            "competitor_sources": ["company websites", "industry directories"],
            "pricing_sources": ["pricing pages", "marketplace listings"],
            "buyer_sources": ["surveys", "forums", "reviews"],
            "required_evidence_types": ["competitors", "pricing", "buyer signal"],
        },
    }
    return profiles.get(key, profiles["general_market"])


def build_industry_queries(topic: str, domain: str, country: str = "", industry: str = "") -> dict[str, list[str]]:
    key = resolve_retrieval_profile_key(domain, topic, industry)
    geo = country.strip() if country and country.strip().lower() not in {"global", "world", "worldwide"} else ""
    city = "Mumbai" if "india" in (country or "").lower() else ""
    base = " ".join(x for x in (topic, industry, geo) if x).strip()
    if key == "automotive_retail":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:cardekho.com {base} luxury car service center dealers",
                f"site:carwale.com {base} premium car workshop network",
                f"site:team-bhp.com {base} service experience review",
                f"{base} BMW Mercedes Audi Porsche dealer service center {city}",
            ],
            "pricing_queries": [
                f"{base} BMW service package cost {geo}",
                f"{base} Mercedes maintenance cost service menu {geo}",
                f"site:cardekho.com {base} service cost package pricing",
            ],
            "buyer_queries": [
                f"site:team-bhp.com {base} service complaint maintenance cost",
                f"{base} luxury car garage review google {city}",
            ],
            "regulation_queries": [f"{base} automotive service regulation compliance {geo}"],
        }
    if key == "saas_software":
        return {
            "profile_id": key,
            "competitor_queries": [
                "site:g2.com HubSpot CRM SMB pricing reviews",
                "site:capterra.com Zoho CRM Pipedrive Salesforce SMB comparison",
                f"site:producthunt.com {base} CRM automation",
                f"{base} HubSpot Zoho Pipedrive Salesforce Freshsales comparison",
            ],
            "pricing_queries": [
                "HubSpot CRM pricing per user month",
                "Zoho CRM pricing plans USD",
                "Pipedrive pricing starting at per user",
                "Salesforce Essentials SMB pricing",
            ],
            "buyer_queries": [
                "site:reddit.com CRM automation SMB too expensive integration issues",
                "site:g2.com HubSpot CRM cons difficult onboarding",
                "site:capterra.com Zoho CRM poor support buggy",
            ],
            "regulation_queries": [f"{base} CRM data privacy GDPR compliance"],
        }
    if key == "ecommerce_retail":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:nykaa.com {base} organic skincare brands",
                f"site:purplle.com {base} D2C skincare competitors",
                f"{base} organic skincare brand competitors India",
            ],
            "pricing_queries": [
                f"{base} organic skincare price INR flipkart amazon",
                f"site:nykaa.com {base} serum moisturizer price",
            ],
            "buyer_queries": [
                f"site:reddit.com {base} skincare too expensive delivery issues",
                f"{base} organic skincare reviews trustpilot",
            ],
            "regulation_queries": [f"{base} cosmetics regulation India CDSCO"],
        }
    if key == "festive_retail":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:amazon.in {base} festive decoration kit",
                f"site:flipkart.com {base} diwali ganesh decoration kit",
                f"site:indiamart.com {base} eco-friendly festive decor suppliers",
                f"site:etsy.com {base} handmade festive decor kit",
            ],
            "pricing_queries": [
                f"{base} decoration kit price INR amazon flipkart",
                f"site:indiamart.com {base} bulk festive decor pricing",
            ],
            "buyer_queries": [
                f"{base} apartment society festive decor reviews",
                f"site:reddit.com {base} diwali decoration kit society",
            ],
            "regulation_queries": [f"{base} eco-friendly festive product compliance India"],
        }
    if key == "event_services":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:wedmegood.com {base} vendors",
                f"site:indiamart.com {base} event decor rental",
                f"{base} drone light show companies India",
                f"site:justdial.com {base} event setup rental {city}",
            ],
            "pricing_queries": [
                f"{base} mandap rental pricing {geo}",
                f"{base} event decor package cost {geo}",
            ],
            "buyer_queries": [
                f"site:reddit.com {base} event vendor review",
                f"{base} wedding event rental reviews google {city}",
            ],
            "regulation_queries": [f"{base} event drone show permissions India DGCA"],
        }
    if key == "wedding_services":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:wedmegood.com {base} mandap decor vendors",
                f"site:weddingz.in {base} wedding decor rental",
                f"{base} wedding mandap rental {geo}",
            ],
            "pricing_queries": [
                f"{base} mandap rental cost {geo}",
                f"site:indiamart.com {base} wedding decor package price",
            ],
            "buyer_queries": [
                f"site:reddit.com {base} wedding mandap rental review",
                f"{base} destination wedding decor reviews {geo}",
            ],
            "regulation_queries": [f"{base} wedding venue regulations {geo}"],
        }
    if key == "decor_retail":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:amazon.in {base} home decor products",
                f"site:flipkart.com {base} decoration kit",
                f"site:indiamart.com {base} apartment society decor",
            ],
            "pricing_queries": [
                f"{base} decor kit price amazon flipkart",
                f"site:pepperfry.com {base} decor pricing",
            ],
            "buyer_queries": [
                f"{base} apartment society decor reviews",
                f"site:reddit.com {base} home decor quality delivery",
            ],
            "regulation_queries": [f"{base} home decor product standards India"],
        }
    if key in {"local_services", "home_services"}:
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:justdial.com {base} {city}",
                f"site:urbancompany.com {base} {geo}",
                f"{base} local service providers near {city}",
            ],
            "pricing_queries": [
                f"{base} service pricing {geo}",
                f"site:urbancompany.com {base} rates",
            ],
            "buyer_queries": [
                f"site:reddit.com {base} local service review",
                f"{base} google reviews {city}",
            ],
            "regulation_queries": [f"{base} local service licensing {geo}"],
        }
    if key == "creator_business":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"{base} creator business competitors India",
                f"site:youtube.com {base} creator monetization",
            ],
            "pricing_queries": [
                f"{base} influencer sponsorship rates India",
                f"{base} creator tool pricing",
            ],
            "buyer_queries": [
                f"site:reddit.com {base} creator business revenue",
            ],
            "regulation_queries": [f"{base} creator tax compliance India"],
        }
    if key == "healthcare_wellness":
        return {
            "profile_id": key,
            "competitor_queries": [
                f"site:g2.com {base} healthcare clinic software competitors",
                f"{base} sports psychology platform competitors {geo}",
                f"site:practo.com {base} clinic competitors {geo}",
                f"{base} mental health athlete coaching platforms UK",
            ],
            "pricing_queries": [
                f"{base} clinic SaaS subscription pricing per provider",
                f"site:g2.com {base} healthcare software pricing",
                f"{base} sports psychology coaching session pricing {geo}",
            ],
            "buyer_queries": [
                f"site:reddit.com {base} patient scheduling billing pain",
                f"site:pubmed.ncbi.nlm.nih.gov {base} sports psychology outcomes",
                f"{base} athlete mental health platform reviews",
            ],
            "regulation_queries": [
                f"site:nhs.uk {base} mental health guidance",
                f"site:nice.org.uk {base} clinical standards",
                f"{base} healthcare data privacy HIPAA GDPR compliance",
            ],
        }
    return {
        "profile_id": key,
        "competitor_queries": [f"{base} named competitors pricing"],
        "pricing_queries": [f"{base} pricing fees benchmark"],
        "buyer_queries": [f"{base} customer reviews buyer pain"],
        "regulation_queries": [f"{base} regulation compliance"],
    }


def select_section_industry_queries(query_plan: dict, section_title: str, max_queries: int = 3) -> list[str]:
    title = str(section_title or "")
    competitive = {"Competitive Landscape", "Key Player Profiles", "Market Share Analysis"}
    pricing_sections = {"Pricing Analysis", "Market Size and Valuation", "Market Size & Valuation"}
    buyer = {"Consumer Behavior", "Market Trends", "Restraints & Challenges"}
    if title in competitive:
        buckets = query_plan.get("competitor_queries", [])[:2] + query_plan.get("pricing_queries", [])[:1]
    elif title in pricing_sections:
        buckets = query_plan.get("pricing_queries", [])[:2] + query_plan.get("competitor_queries", [])[:1]
    elif title in buyer:
        buckets = query_plan.get("buyer_queries", [])[:2] + query_plan.get("competitor_queries", [])[:1]
    else:
        buckets = (
            query_plan.get("competitor_queries", [])[:1]
            + query_plan.get("pricing_queries", [])[:1]
            + query_plan.get("buyer_queries", [])[:1]
        )
    out: list[str] = []
    seen: set[str] = set()
    for q in buckets:
        key = str(q).lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(q)
        if len(out) >= max_queries:
            break
    return out


def industry_query_actions(topic: str, domain: str, country: str, industry: str = "") -> list[dict]:
    plan = build_industry_queries(topic, domain, country, industry=industry)
    actions: list[dict] = []
    for bucket, intent in (
        ("competitor_queries", "industry competitor intelligence"),
        ("pricing_queries", "industry pricing intelligence"),
        ("buyer_queries", "industry buyer/review intelligence"),
        ("regulation_queries", "industry regulation context"),
    ):
        for query in plan.get(bucket, [])[:3]:
            actions.append({"gap": bucket, "intent": intent, "query": query})
    return actions


def competitor_intelligence_gate(record_counts: dict | None) -> dict[str, Any]:
    counts = record_counts or {}
    named = int(counts.get("named_competitor_operator_records", 0) or 0)
    pricing = int(counts.get("direct_pricing_unit_cost_records", 0) or 0)
    buyer = int(counts.get("survey_practitioner_buyer_records", 0) or 0)
    passed = named >= 3 and pricing >= 2 and buyer >= 3
    return {
        "gate": "competitor_intelligence",
        "passed": passed,
        "named_competitors": named,
        "pricing_records": pricing,
        "buyer_review_records": buyer,
        "requirement": {"named_competitors": 3, "pricing_records": 2, "buyer_review_records": 3},
        "failed_reasons": [] if passed else [
            *([f"named competitors {named}/3"] if named < 3 else []),
            *([f"pricing records {pricing}/2"] if pricing < 2 else []),
            *([f"buyer/review records {buyer}/3"] if buyer < 3 else []),
        ],
        "score_cap_10": 10.0 if passed else 6.5,
        "verdict_cap_rule": "STRONG_YES" if passed else "CONDITIONAL_YES",
    }
