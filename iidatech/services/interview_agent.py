"""Primary research infrastructure - interview schemas and signal scoring (no live scraping)."""
from __future__ import annotations
from typing import Any

FOUNDER_INTERVIEW_SCHEMA = {
    "persona": "", "pain_points": [], "current_tools": [], "budget": "", "urgency": "",
    "objections": [], "willingness_to_switch": "",
}
BUYER_INTERVIEW_SCHEMA = {
    "buying_triggers": [], "budget_range": "", "alternatives_considered": [], "purchase_frequency": "",
    "decision_maker": "", "success_metric": "",
}
PRACTITIONER_INTERVIEW_SCHEMA = {
    "role": "", "workflow_pain": [], "unit_economics_notes": [], "revenue_drivers": [], "tools_used": [],
}

_DOMAIN_QUESTIONS = {
    "saas": {
        "founder": ["What workflow breaks today?", "What tools are you paying for?", "What is your monthly software budget?", "What would make you switch in 30 days?"],
        "buyer": ["What triggered this search?", "Who signs the contract?", "What is your per-seat budget?", "What alternatives did you reject and why?"],
        "practitioner": ["How many hours/week on manual work?", "What is your cost per closed deal?", "Which integration is non-negotiable?"],
    },
    "d2c": {
        "founder": ["What margin do you need per unit?", "Which channel drove your last 10 orders?", "What is your return rate assumption?"],
        "buyer": ["Why did you buy vs alternatives?", "What price point felt fair?", "Will you repurchase in 90 days?"],
        "practitioner": ["What is your CAC by channel?", "What is contribution margin after shipping?", "What SKU has highest repeat rate?"],
    },
    "healthcare": {
        "founder": ["What compliance path are you assuming?", "Who is the economic buyer?", "What is reimbursement sensitivity?"],
        "buyer": ["What clinical or ops KPI must improve?", "What is the procurement cycle?", "What incumbent contract blocks switching?"],
        "practitioner": ["Patients/visits per day?", "Revenue per visit?", "Biggest admin bottleneck?"],
    },
    "general": {
        "founder": ["Describe the buyer in one sentence.", "What proof would convince you to charge more?", "What is blocking launch this week?"],
        "buyer": ["What problem is urgent?", "What budget band is realistic?", "What would a successful pilot measure?"],
        "practitioner": ["Walk through the workflow step-by-step.", "Where is time or money lost?", "What metric would prove ROI?"],
    },
}


def _resolve_domain(domain: str) -> str:
    d = (domain or "general").lower()
    if any(x in d for x in ("saas", "crm", "b2b", "software")):
        return "saas"
    if any(x in d for x in ("d2c", "ecommerce", "retail", "consumer")):
        return "d2c"
    if "health" in d:
        return "healthcare"
    return "general"


def build_interview_questionnaire(domain: str) -> dict[str, Any]:
    key = _resolve_domain(domain)
    qs = _DOMAIN_QUESTIONS.get(key, _DOMAIN_QUESTIONS["general"])
    return {
        "domain": key,
        "founder_interview": {"schema": FOUNDER_INTERVIEW_SCHEMA, "questions": qs["founder"]},
        "buyer_interview": {"schema": BUYER_INTERVIEW_SCHEMA, "questions": qs["buyer"]},
        "practitioner_interview": {"schema": PRACTITIONER_INTERVIEW_SCHEMA, "questions": qs["practitioner"]},
        "minimum_sample": {"founder": 5, "buyer": 10, "practitioner": 8},
    }


def score_interview_signal(interview_data: dict[str, Any]) -> dict[str, Any]:
    data = interview_data if isinstance(interview_data, dict) else {}
    pains = data.get("pain_points") or data.get("workflow_pain") or data.get("buying_triggers") or []
    objections = data.get("objections") or []
    budget = str(data.get("budget") or data.get("budget_range") or "")
    urgency = str(data.get("urgency") or "")
    score = 3.0
    score += min(2.0, len(pains) * 0.4)
    score += 1.0 if budget else 0.0
    score += 1.0 if urgency else 0.0
    score -= min(1.5, len(objections) * 0.3)
    return {"signal_score_10": round(max(1.0, min(10.0, score)), 1), "pain_count": len(pains), "has_budget_signal": bool(budget)}


def aggregate_interview_insights(interviews: list[dict[str, Any]] | None) -> dict[str, Any]:
    interviews = [i for i in (interviews or []) if isinstance(i, dict)]
    if not interviews:
        return {"confidence_score": 0.0, "recurring_pains": [], "willingness_to_pay_range": "", "objections": [], "urgency_score": 0.0, "interview_count": 0}
    pains, objections, budgets, urgencies = [], [], [], []
    for row in interviews:
        pains.extend(row.get("pain_points") or row.get("workflow_pain") or row.get("buying_triggers") or [])
        objections.extend(row.get("objections") or [])
        if row.get("budget") or row.get("budget_range"):
            budgets.append(str(row.get("budget") or row.get("budget_range")))
        if row.get("urgency"):
            urgencies.append(str(row.get("urgency")))
    pain_freq: dict[str, int] = {}
    for p in pains:
        k = str(p).strip().lower()[:80]
        if k:
            pain_freq[k] = pain_freq.get(k, 0) + 1
    recurring = [p for p, c in sorted(pain_freq.items(), key=lambda x: -x[1]) if c >= 2][:8]
    signals = [score_interview_signal(i).get("signal_score_10", 0) for i in interviews]
    return {
        "confidence_score": round(sum(signals) / max(len(signals), 1) / 10.0, 2),
        "recurring_pains": recurring or list(pain_freq.keys())[:5],
        "willingness_to_pay_range": budgets[0] if len(budgets) == 1 else (f"{min(budgets)} - {max(budgets)}" if budgets else ""),
        "objections": list(dict.fromkeys(str(o) for o in objections))[:10],
        "urgency_score": round(len(urgencies) / max(len(interviews), 1), 2),
        "interview_count": len(interviews),
    }