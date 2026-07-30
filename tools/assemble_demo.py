import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "opportunity_workspaces" / "demo_readonly"
research = (DEMO / "research.md").read_text(encoding="utf-8")
new_plan = (DEMO / "new_business_plan.md").read_text(encoding="utf-8")
gauge_plan = (DEMO / "gauge_forward_plan.md").read_text(encoding="utf-8")
now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

gauge_intake = {
    "step": 5, "gauge_type": "saas", "company_name": "Acme CRM Pvt Ltd",
    "website": "https://acmecrm.example.in", "geography": "India",
    "industry": "SaaS / B2B Software", "currency": "INR",
    "monthly_revenue": "1800000", "monthly_costs": "1100000",
    "active_customers": "142", "churn_pct": "4.2", "team_size": "11",
    "competitors": "Zoho CRM, Freshsales, Kylas",
    "description": "B2B CRM automation for Indian SMBs with WhatsApp-first workflows.",
    "priority_12_months": "Cut churn below 3.5% and prove clinic vertical GTM",
    "success_12_months": "28L MRR with documented unit economics",
    "biggest_bottleneck": "Churn and CAC visibility",
    "checklists": {"saas": {"Financials": [{"checked": True, "value": "P&L monthly"}]}},
}

gauge_audit = {
    "overall_score": 68,
    "overall_label": "Solid foundation — close gaps before scaling spend",
    "overall_summary": "Revenue growing but unit economics and retention need tracking before ad scale.",
    "plain_english_read": "You are at 68/100. Fix churn cohort tracking and CAC by channel before scaling spend.",
    "focus_areas": ["Cohort churn dashboard", "CAC by channel", "Clinic vertical SKU", "Runway model"],
    "categories": [
        {"name": "Financials", "score": 72, "status": "watch", "summary": "Margins tracked; runway informal."},
        {"name": "Customers", "score": 65, "status": "watch", "summary": "Churn not segmented by cohort."},
        {"name": "Sales & Marketing", "score": 61, "status": "watch", "summary": "CAC not unified by channel."},
        {"name": "Operations", "score": 70, "status": "strong", "summary": "Fulfillment reliable."},
        {"name": "Product & Team", "score": 66, "status": "watch", "summary": "Roadmap ad hoc."},
        {"name": "Competitive Position", "score": 64, "status": "watch", "summary": "Local differentiation known."},
    ],
    "key_metrics": [
        {"label": "Gross margin", "value": "38%", "benchmark": "40-55%", "assessment": "below"},
        {"label": "Monthly churn", "value": "4.2%", "benchmark": "<3%", "assessment": "below"},
    ],
    "top_actions": [
        {"title": "Instrument churn by cohort", "why": "Need cohort data.", "impact": "high", "effort": "medium"},
        {"title": "Unify CAC by channel", "why": "Spend is guesswork.", "impact": "high", "effort": "low"},
    ],
    "industry_landscape": "India SMB CRM growing; WhatsApp-native wins.",
    "risks": ["Churn above benchmark", "CAC fragmented", "Informal cash planning"],
    "sources": ["IIDATECH demo sample"],
}

ws = {
    "workspace_id": "demo_readonly",
    "workspace_dir": str(DEMO.resolve()),
    "owner_email": "demo@local",
    "demo_readonly": True,
    "idea": "CRM automation for SMBs",
    "industry": "SaaS / B2B Software",
    "country": "India",
    "areas": "Mumbai, Bangalore",
    "current_path": "Understand your market",
    "updated_at": now,
    "scope_assessment": {"ok": True, "issues": []},
    "research_report": {
        "available": True, "pipeline": "demo", "topic": "CRM automation for SMBs",
        "geography": "India", "section_count": 8,
        "report_markdown": research, "markdown": research, "warnings": [],
        "full_result": {"success": True, "topic": "CRM automation for SMBs", "section_count": 8, "report_markdown": research},
    },
    "business_plan_mode": "new",
    "business_builder_is_existing": False,
    "plan_intake": {"idea": "CRM automation for SMBs", "industry": "SaaS / B2B Software", "country": "India", "use_research": True},
    "business_plan": {"available": True, "markdown": new_plan, "report_markdown": new_plan, "company_mode": "new"},
    "gauge_intake": gauge_intake,
    "gauge_audit": gauge_audit,
    "gauge_forward_plan": {"available": True, "markdown": gauge_plan, "report_markdown": gauge_plan},
    "automation": {
        "available": True, "demo_sample": True,
        "demo_queue": {"items": [
            {"label": "Market sizing summary", "status": "completed", "result": "TAM/SAM/SOM from IIDATECH research."},
            {"label": "Competitive snapshot", "status": "completed", "result": "Top 5 India CRM competitors with pricing."},
            {"label": "ICP outreach draft", "status": "completed", "result": "WhatsApp sequence for clinic owners."},
        ]},
        "log": [{"success": True, "item": {"label": "Competitive snapshot", "status": "completed", "result": "Competitor matrix ready."}}],
    },
}
(DEMO / "workspace.json").write_text(json.dumps(ws, indent=2, ensure_ascii=False), encoding="utf-8")
print("OK", (DEMO / "workspace.json").stat().st_size)