"""Employee roster defaults and business-type role selection."""
from __future__ import annotations
from iidatech.execution.task_engine import hire_employee

CORE_ROLES = [
    {"role": "Founder", "department": "Leadership", "authority_level": 10},
    {"role": "COO", "department": "Operations", "authority_level": 9},
    {"role": "Research Analyst", "department": "Research", "authority_level": 6},
    {"role": "Growth Marketer", "department": "Marketing", "authority_level": 6},
    {"role": "Sales Lead", "department": "Sales", "authority_level": 7},
    {"role": "Operations Manager", "department": "Operations", "authority_level": 6},
    {"role": "Finance Manager", "department": "Finance", "authority_level": 6},
]
OPTIONAL_ROLES = {"product": {"role": "Product Manager", "department": "Product", "authority_level": 7}, "recruiter": {"role": "Recruiter", "department": "People", "authority_level": 5}, "cs": {"role": "Customer Success", "department": "Customer Success", "authority_level": 6}, "legal": {"role": "Legal", "department": "Legal", "authority_level": 7}}
BUSINESS_TYPE_ROLES = {"saas": ["product"], "d2c": [], "retail": [], "agency": ["cs"], "local_business": []}
_DEFAULT_SKILLS = {"Founder": ["strategy", "fundraising", "hiring"], "COO": ["operations", "process", "vendor management"], "Research Analyst": ["market research", "competitive intel", "evidence"], "Growth Marketer": ["paid media", "content", "funnel analytics"], "Sales Lead": ["outbound", "discovery", "pipeline"], "Operations Manager": ["SOPs", "logistics", "tooling"], "Finance Manager": ["modeling", "unit economics", "budgeting"], "Product Manager": ["roadmap", "UX", "prioritization"], "Recruiter": ["sourcing", "interviews", "scorecards"], "Customer Success": ["onboarding", "retention", "NPS"], "Legal": ["contracts", "compliance", "IP"]}

def infer_business_type(*, industry="", topic="", report_v3=None):
    blob = f"{industry} {topic}".lower()
    if report_v3:
        gtm = report_v3.get("go_to_market", {})
        if isinstance(gtm, dict) and gtm.get("vertical"):
            return str(gtm["vertical"]).lower()
    if any(x in blob for x in ("saas", "b2b software", "subscription", "crm", "platform")):
        return "saas"
    if any(x in blob for x in ("d2c", "direct-to-consumer", "ecommerce", "shopify", "beauty")):
        return "d2c"
    if any(x in blob for x in ("retail", "store", "festive", "wholesale")):
        return "retail"
    if any(x in blob for x in ("agency", "consulting", "services firm")):
        return "agency"
    if any(x in blob for x in ("local", "clinic", "restaurant", "apartment")):
        return "local_business"
    return "saas"

def default_roles_for_business_type(business_type):
    bt = (business_type or "saas").lower()
    roles = [dict(r) for r in CORE_ROLES]
    for key in BUSINESS_TYPE_ROLES.get(bt, []):
        opt = OPTIONAL_ROLES.get(key)
        if opt:
            roles.append(dict(opt))
    if bt == "retail":
        for r in roles:
            if r["role"] == "Operations Manager":
                r["authority_level"] = 7
    if bt == "agency":
        for r in roles:
            if r["role"] == "Sales Lead":
                r["authority_level"] = 8
    return roles

def hire_default_team(report_id, *, business_type="saas", founder_name="Founder"):
    roster = []
    for spec in default_roles_for_business_type(business_type):
        name = founder_name if spec["role"] == "Founder" else f"Virtual {spec['role']}"
        roster.append(hire_employee(report_id, name=name, role=spec["role"], department=spec["department"], authority_level=int(spec["authority_level"]), skills=_DEFAULT_SKILLS.get(spec["role"], [])))
    return roster
