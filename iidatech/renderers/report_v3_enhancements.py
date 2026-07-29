"""V3 report enhancements: execution calendar and risk heatmap."""
from __future__ import annotations
from typing import Any

_VALIDATION = "VALIDATION REQUIRED"

def _as_dict(v):
    return v if isinstance(v, dict) else {}

def _as_list(v):
    return v if isinstance(v, list) else []

def _text(v):
    if v in (None, "", _VALIDATION):
        return _VALIDATION
    return str(v).strip()

def _prob_to_float(probability):
    if isinstance(probability, (int, float)):
        p = float(probability)
        return max(0.0, min(1.0, p if p <= 1 else p / 100))
    text = str(probability or "").lower()
    if "very" in text and "high" in text:
        return 0.9
    if "high" in text or "likely" in text:
        return 0.75
    if "medium" in text or "moderate" in text:
        return 0.45
    if "low" in text or "unlikely" in text:
        return 0.2
    return 0.35

def _severity_from_score(score):
    if score >= 0.72:
        return "critical"
    if score >= 0.52:
        return "high"
    if score >= 0.32:
        return "medium"
    return "low"

def _impact_score(impact):
    text = str(impact or "").lower()
    if not text or text == _VALIDATION.lower():
        return 0.4
    heavy = ("bankrupt", "shutdown", "fatal", "regulatory", "legal", "churn", "runway", "cash")
    medium = ("delay", "margin", "cac", "competition", "supply", "hiring")
    if any(w in text for w in heavy):
        return 0.85
    if any(w in text for w in medium):
        return 0.6
    return 0.45 if len(text) > 40 else 0.35

def build_risk_heatmap(risk_map, *, brain=None, investment=None):
    rows = []
    seen = set()
    for item in _as_list(risk_map):
        if not isinstance(item, dict):
            continue
        risk = _text(item.get("category") or item.get("risk") or item.get("type"))
        if risk.lower() in seen:
            continue
        seen.add(risk.lower())
        prob = _prob_to_float(item.get("probability"))
        impact = _impact_score(item.get("impact"))
        score = prob * 0.55 + impact * 0.45
        rows.append({
            "risk": risk.replace("_", " ").title() if risk != _VALIDATION else risk,
            "severity": _severity_from_score(score),
            "probability": round(prob, 2),
            "mitigation": _text(item.get("mitigation")),
        })
    brain = _as_dict(brain)
    fin = _as_dict(brain.get("financial_truth"))
    if fin.get("invalid_business_model") and "financial" not in seen:
        rows.append({"risk": "Unit economics / COGS", "severity": "critical", "probability": 0.78, "mitigation": "Re-model COGS vs price before scaling spend"})
        seen.add("financial")
    inv = _as_dict(investment)
    for r in _as_list(inv.get("risks"))[:3]:
        if isinstance(r, str) and r.strip():
            key = r.strip()[:40].lower()
            if key in seen:
                continue
            seen.add(key)
            prob = 0.5
            rows.append({"risk": r.strip()[:120], "severity": _severity_from_score(prob * 0.5 + 0.35), "probability": prob, "mitigation": _VALIDATION})
    rows.sort(key=lambda x: ({"critical": 0, "high": 1, "medium": 2, "low": 3}[x["severity"]], -x["probability"]))
    return rows[:12] or [{"risk": "Market adoption", "severity": "medium", "probability": 0.45, "mitigation": "Run 15+ ICP interviews before paid scale"}]

def build_execution_calendar(report_v3):
    plan = _as_dict(report_v3.get("execution_plan"))
    gtm = _as_dict(report_v3.get("go_to_market"))
    ev = _as_dict(report_v3.get("executive_verdict"))
    eng = gtm.get("gtm_engine") if isinstance(gtm.get("gtm_engine"), dict) else {}
    first_channel = _text(gtm.get("first_channel") or eng.get("first_channel"))

    def block(key, title, default_kpi):
        src = _as_dict(plan.get(key))
        actions = [str(a) for a in _as_list(src.get("actions")) if str(a).strip() and str(a) != _VALIDATION]
        milestones = [str(m) for m in _as_list(src.get("milestones")) if str(m).strip()]
        if not actions:
            actions = [_VALIDATION]
        if not milestones:
            milestones = [title]
        return {"focus": title, "actions": actions[:8], "milestones": milestones[:5], "kpi": _text(src.get("kpi") or default_kpi), "budget": _text(src.get("budget"))}

    week1 = block("day_1_7", "Validate ICP and offer", "10 buyer conversations logged")
    week2 = block("week_2_4", "Pilot first channel", f"Launch {first_channel[:60]}")
    week3_src = _as_dict(plan.get("month_2_3"))
    week3 = {"focus": "Repeatable acquisition test", "actions": [str(a) for a in _as_list(week3_src.get("actions"))[:6]] or ["Instrument funnel metrics", "Review CAC vs LTV weekly"], "milestones": [str(m) for m in _as_list(week3_src.get("milestones"))[:4]] or ["First paid customers"], "kpi": _text(week3_src.get("kpi") or "CAC within 1.3x benchmark"), "budget": _text(week3_src.get("budget"))}
    month2 = block("month_2_3", "Prove unit economics", "LTV:CAC > 3 on pilot cohort")
    month3 = {"focus": "Operationalize delivery", "actions": ["Document fulfillment / onboarding SOP", "Hire or contract first ops support", "Weekly KPI review with founder"], "milestones": ["SOP v1 shipped", "Support SLA defined"], "kpi": "Gross margin stable across first 50 customers", "budget": _text(_as_dict(plan.get("month_3_6")).get("budget"))}
    month6 = block("month_3_6", "Scale winning channel", "MRR or revenue run-rate target hit")
    if ev.get("funding_ready"):
        month6["milestones"] = list(month6.get("milestones", [])) + ["Funding data room draft"]
    year1 = []
    for m in _as_list(plan.get("first_revenue_path")) + _as_list(gtm.get("recommended_launch_sequence")):
        s = str(m).strip()
        if s and s not in year1:
            year1.append(s)
    year1 += ["Repeatable GTM with measured CAC", "Core team hired for delivery + growth", "Investor-ready metrics package"]
    return {"week_1": week1, "week_2": week2, "week_3": week3, "month_2": month2, "month_3": month3, "month_6": month6, "year_1_milestones": year1[:10]}
