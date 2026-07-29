"""Section-aware evidence retrieval query templates."""

from __future__ import annotations

RETRIEVAL_QUERY_TEMPLATES: dict[str, str] = {
    "market_sizing": (
        "{topic} {industry} {target} market size TAM SAM SOM revenue denominator "
        "population business count GDP official statistics {section_title}"
    ),
    "competition": (
        "{topic} {industry} {target} competitors market share pricing revenue "
        "company filings public comps vendor landscape {section_title}"
    ),
    "regulation": (
        "{topic} {industry} {target} regulation compliance certification licensing "
        "standards regulator policy approval timeline {section_title}"
    ),
    "consumer_demand": (
        "{topic} {industry} {target} buyer behavior adoption survey interview "
        "willingness to pay purchase journey switching costs practitioner voice {section_title}"
    ),
    "financial_feasibility": (
        "{topic} {industry} {target} unit economics margin pricing CAC payback churn "
        "revenue forecast valuation multiples funding benchmark {section_title}"
    ),
    "operations": (
        "{topic} {industry} {target} operating model hiring salary benchmark "
        "implementation cost procurement vendor stack delivery capacity {section_title}"
    ),
    "general": "{topic} {industry} {target} {section_title} market evidence official source",
}

SECTION_RETRIEVAL_FAMILY: dict[str, str] = {
    "Market Size & Valuation": "market_sizing",
    "Historical Market Data": "market_sizing",
    "Market Forecast (2026-2031)": "market_sizing",
    "Market Overview & Definition": "market_sizing",
    "Regional Analysis": "market_sizing",
    "Competitive Landscape": "competition",
    "Key Player Profiles": "competition",
    "Market Share Analysis": "competition",
    "Competitive Benchmarking": "competition",
    "M&A Activity": "competition",
    "Regulatory Environment": "regulation",
    "Certification, Compliance & Launch Timeline": "regulation",
    "Restraints & Challenges": "regulation",
    "Consumer Behavior": "consumer_demand",
    "Go-To-Market Playbook": "consumer_demand",
    "Market Segmentation": "consumer_demand",
    "Growth Drivers": "consumer_demand",
    "Opportunities & White Spaces": "consumer_demand",
    "Financial Forecasting Basis": "financial_feasibility",
    "Valuation Support": "financial_feasibility",
    "Investment Diligence Gate": "financial_feasibility",
    "Investment & Funding Activity": "financial_feasibility",
    "Startup Budget & Revenue Model": "financial_feasibility",
    "Operating Model & Hiring Plan": "operations",
    "Founder Build Plan": "operations",
    "Ground-Up Execution Roadmap": "operations",
    "Supply Chain Analysis": "operations",
    "Pricing Analysis": "operations",
}


def section_retrieval_family(section_title: str) -> str:
    return SECTION_RETRIEVAL_FAMILY.get(str(section_title or "").strip(), "general")


def build_evidence_retrieval_query(
    topic: str,
    industry: str,
    target: str,
    section_title: str,
) -> str:
    family = section_retrieval_family(section_title)
    template = RETRIEVAL_QUERY_TEMPLATES.get(family, RETRIEVAL_QUERY_TEMPLATES["general"])
    return template.format(
        topic=str(topic or "").strip(),
        industry=str(industry or "").strip(),
        target=str(target or "").strip(),
        section_title=str(section_title or "").strip(),
    ).strip()
