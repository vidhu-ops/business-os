"""Financial benchmark bank - assumption ranges, never presented as company-specific facts."""
from __future__ import annotations
from typing import Any

FINANCIAL_BENCHMARKS: dict[str, dict[str, Any]] = {
    "crm_automation": {"median_cac": 400, "median_arpu": 90, "median_churn_monthly": 0.035, "gross_margin": 0.82, "ltv_cac": 3.1, "payback_months": 14},
    "b2b_saas": {"median_cac": 450, "median_arpu": 110, "median_churn_monthly": 0.03, "gross_margin": 0.80, "ltv_cac": 3.4, "payback_months": 13},
    "saas": {"median_cac": 420, "median_arpu": 95, "median_churn_monthly": 0.032, "gross_margin": 0.81, "ltv_cac": 3.2, "payback_months": 14},
    "ai_workflow_automation": {"median_cac": 550, "median_arpu": 450, "median_churn_monthly": 0.045, "gross_margin": 0.68, "ltv_cac": 2.8, "payback_months": 16},
    "d2c": {"median_cac": 28, "median_arpu": 42, "repeat_purchase_rate": 0.22, "cogs_pct": 0.38, "shipping_pct": 0.12, "returns_pct": 0.08, "gross_margin": 0.42},
    "ecommerce_retail": {"median_cac": 32, "median_arpu": 48, "repeat_purchase_rate": 0.20, "cogs_pct": 0.40, "shipping_pct": 0.11, "returns_pct": 0.10, "gross_margin": 0.39},
    "marketplace": {"take_rate": 0.15, "gmv_per_active_seller": 12000, "gross_margin": 0.55, "median_cac": 65, "buyer_repeat_rate": 0.35},
    "services_agency": {"utilization": 0.68, "labor_margin": 0.45, "median_cac": 900, "median_churn_monthly": 0.06, "project_margin": 0.38},
    "healthcare": {"visit_frequency_annual": 4.2, "utilization": 0.72, "gross_margin": 0.35, "occupancy": 0.68, "median_cac": 180},
    "automotive": {"avg_ticket": 8500, "labor_margin": 0.42, "parts_margin": 0.28, "utilization": 0.65, "median_cac": 120},
    "general": {"median_cac": 500, "median_arpu": 100, "median_churn_monthly": 0.04, "gross_margin": 0.55, "ltv_cac": 2.5, "payback_months": 18},
}

_DOMAIN_ALIASES = {
    "crm_automation": "crm_automation", "b2b_saas": "b2b_saas", "revops_sales_automation": "b2b_saas",
    "saas_software": "saas", "ai_workflow_automation": "ai_workflow_automation",
    "ecommerce_retail": "d2c", "consumer": "d2c", "fashion": "d2c",
    "automotive": "automotive", "automotive_retail": "automotive",
    "healthcare": "healthcare", "finance": "general",
}


def _resolve_domain(domain: str) -> str:
    key = (domain or "general").lower().strip()
    return _DOMAIN_ALIASES.get(key, key if key in FINANCIAL_BENCHMARKS else "general")


def get_financial_benchmarks(domain: str) -> dict[str, Any]:
    key = _resolve_domain(domain)
    bench = dict(FINANCIAL_BENCHMARKS.get(key) or FINANCIAL_BENCHMARKS["general"])
    bench["benchmark_domain"] = key
    bench["assumption_grade"] = "benchmark-derived"
    bench["disclaimer"] = "Industry benchmark ranges — NOT verified company-specific data."
    return bench


def build_benchmark_financial_pack(domain: str, *, currency: str = "USD") -> dict[str, Any]:
    bench = get_financial_benchmarks(domain)
    return {
        "currency": currency,
        "assumption_grade": "benchmark-derived",
        "disclaimer": bench["disclaimer"],
        "benchmark_domain": bench["benchmark_domain"],
        "unit_economics_benchmarks": bench,
        "ranges": {
            "cac_range": [round(bench.get("median_cac", 0) * 0.6, 2), round(bench.get("median_cac", 0) * 1.5, 2)] if bench.get("median_cac") else None,
            "arpu_range": [round(bench.get("median_arpu", 0) * 0.7, 2), round(bench.get("median_arpu", 0) * 1.4, 2)] if bench.get("median_arpu") else None,
            "gross_margin_range": [round(max(0.1, bench.get("gross_margin", 0.5) - 0.12), 2), round(min(0.95, bench.get("gross_margin", 0.5) + 0.08), 2)] if bench.get("gross_margin") else None,
        },
        "validation_required": [
            "Replace benchmark CAC with channel-specific measured CAC",
            "Replace benchmark ARPU/churn with pilot or cohort data",
            "Cite primary source before using benchmarks in investor materials",
        ],
    }