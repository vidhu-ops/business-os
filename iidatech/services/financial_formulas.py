"""Standard financial formulas for deterministic report calculations."""
from __future__ import annotations

from typing import Any, Callable

# Catalog: id -> metadata (user-provided formula reference set)
FORMULA_LIBRARY: dict[str, dict[str, str]] = {
    "revenue": {"name": "Revenue", "purpose": "Total income from sales before costs", "formula": "Revenue = Price × Quantity Sold"},
    "cogs": {"name": "Cost of Goods Sold (COGS)", "purpose": "Direct cost of producing goods sold", "formula": "COGS = Beginning Inventory + Purchases - Ending Inventory"},
    "gross_profit": {"name": "Gross Profit", "purpose": "Profit after COGS", "formula": "Gross Profit = Revenue - COGS"},
    "gross_margin": {"name": "Gross Profit Margin", "purpose": "Profitability % of revenue", "formula": "(Gross Profit ÷ Revenue) × 100"},
    "net_profit": {"name": "Net Profit", "purpose": "Profit after all expenses", "formula": "Net Profit = Revenue - Total Expenses"},
    "net_margin": {"name": "Net Profit Margin", "purpose": "Revenue remaining as profit", "formula": "(Net Profit ÷ Revenue) × 100"},
    "contribution_margin": {"name": "Contribution Margin", "purpose": "Revenue minus variable costs", "formula": "Contribution Margin = Revenue - Variable Costs"},
    "contribution_margin_ratio": {"name": "Contribution Margin Ratio", "purpose": "% of revenue for fixed costs", "formula": "(Contribution Margin ÷ Revenue) × 100"},
    "contribution_per_unit": {"name": "Contribution per Unit", "purpose": "Profit per unit after variable costs", "formula": "Selling Price - Variable Cost per Unit"},
    "break_even_units": {"name": "Break-Even Point (Units)", "purpose": "Units to cover all costs", "formula": "Fixed Costs ÷ Contribution Margin per Unit"},
    "break_even_revenue": {"name": "Break-Even Revenue", "purpose": "Revenue to cover costs", "formula": "Break-Even Units × Price per Unit"},
    "break_even_revenue_cm": {"name": "Break-Even Revenue (CM ratio)", "purpose": "Revenue to cover costs via CM%", "formula": "Fixed Costs ÷ Contribution Margin Ratio"},
    "roi": {"name": "Return on Investment (ROI)", "purpose": "Investment efficiency", "formula": "(Net Profit ÷ Investment Cost) × 100"},
    "payback_period": {"name": "Payback Period", "purpose": "Time to recoup investment", "formula": "Investment ÷ Annual Cash Inflow"},
    "cac": {"name": "Customer Acquisition Cost (CAC)", "purpose": "Cost per new customer", "formula": "Total Sales & Marketing Costs ÷ New Customers"},
    "clv": {"name": "Customer Lifetime Value (CLV)", "purpose": "Expected revenue per customer", "formula": "Avg Purchase × Purchases × Lifespan"},
    "ltv_cac_ratio": {"name": "LTV : CAC", "purpose": "Unit economics health", "formula": "CLV ÷ CAC"},
    "cac_payback_months": {"name": "CAC Payback (months)", "purpose": "Months to recover CAC", "formula": "CAC ÷ Monthly Gross Profit per Customer"},
    "operating_margin": {"name": "Operating Margin", "purpose": "Revenue after operating expenses", "formula": "(Operating Income ÷ Revenue) × 100"},
    "margin_of_safety": {"name": "Margin of Safety", "purpose": "Sales drop before loss", "formula": "(Current Sales - Break-Even Sales) ÷ Current Sales × 100"},
    "percent_change": {"name": "Percent Change / Growth Rate", "purpose": "Growth or decline", "formula": "((New - Old) ÷ Old) × 100"},
    "markup": {"name": "Markup", "purpose": "Markup on cost", "formula": "((Selling Price - Cost) ÷ Cost) × 100"},
}


def _num(row: Any) -> float | None:
    if row is None:
        return None
    if isinstance(row, (int, float)):
        return float(row)
    if isinstance(row, dict):
        for k in ("numeric", "numeric_value", "amount", "value"):
            v = row.get(k)
            if isinstance(v, (int, float)):
                return float(v)
        from iidatech.services.financial_sizing_calc import parse_market_value
        return parse_market_value(str(row.get("value") or ""))
    try:
        return float(str(row).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _metric(
    formula_id: str,
    value: float | None,
    *,
    label: str = "DERIVED",
    notes: str = "",
    display: str = "",
) -> dict[str, Any] | None:
    if value is None:
        return None
    meta = FORMULA_LIBRARY.get(formula_id, {})
    return {
        "metric": meta.get("name") or formula_id,
        "formula_id": formula_id,
        "value": display if display else f"{value:,.2f}",
        "numeric": value,
        "label": label,
        "notes": notes or meta.get("formula", ""),
    }


def compute_unit_economics(
    unit: dict[str, Any],
    *,
    fallback_arpu: float | None = None,
    fallback_buyers: float | None = None,
) -> list[dict[str, Any]]:
    """Compute unit-economics metrics from sourced inputs using standard formulas."""
    if not isinstance(unit, dict):
        unit = {}

    price = _num(unit.get("price_per_unit") or unit.get("selling_price"))
    qty = _num(unit.get("quantity_sold") or unit.get("quantity"))
    var_cost = _num(unit.get("variable_cost_per_unit"))
    cogs_unit = _num(unit.get("cogs_per_unit"))
    fixed = _num(unit.get("fixed_costs") or unit.get("fixed_costs_annual"))
    total_expenses = _num(unit.get("total_expenses"))
    cac = _num(unit.get("cac"))
    new_customers = _num(unit.get("new_customers"))
    avg_purchase = _num(unit.get("avg_purchase_value"))
    purchases = _num(unit.get("purchases_per_customer"))
    lifespan = _num(unit.get("customer_lifespan_years"))
    investment = _num(unit.get("investment_cost"))
    operating_income = _num(unit.get("operating_income"))
    old_sales = _num(unit.get("prior_revenue"))
    new_sales = _num(unit.get("current_revenue"))

    if not qty and fallback_buyers:
        qty = fallback_buyers
    if not avg_purchase and fallback_arpu:
        avg_purchase = fallback_arpu

    if cac is None and _num(unit.get("sales_marketing_spend")) and new_customers:
        cac = _num(unit.get("sales_marketing_spend")) / new_customers

    rows: list[dict[str, Any]] = []

    revenue: float | None = None
    if price is not None and qty is not None and price > 0 and qty > 0:
        revenue = price * qty
        rows.append(_metric("revenue", revenue, notes=f"{price:,.2f} × {qty:,.0f} units") or {})

    cogs: float | None = None
    if cogs_unit is not None and qty is not None and qty > 0:
        cogs = cogs_unit * qty
        rows.append(_metric("cogs", cogs, notes=f"{cogs_unit:,.2f}/unit × {qty:,.0f}") or {})
    elif revenue is not None and var_cost is not None and qty is not None and qty > 0:
        cogs = var_cost * qty
        rows.append(_metric("cogs", cogs, notes="Variable cost × quantity (proxy for COGS)") or {})

    gross_profit: float | None = None
    if revenue is not None and cogs is not None:
        gross_profit = revenue - cogs
        rows.append(_metric("gross_profit", gross_profit, notes=f"{revenue:,.2f} - {cogs:,.2f}") or {})
        if revenue > 0:
            rows.append(_metric("gross_margin", (gross_profit / revenue) * 100, display=f"{(gross_profit/revenue)*100:.1f}%", notes="(Gross Profit ÷ Revenue) × 100") or {})

    contribution: float | None = None
    contrib_unit: float | None = None
    if price is not None and var_cost is not None:
        contrib_unit = price - var_cost
        rows.append(_metric("contribution_per_unit", contrib_unit, notes=f"{price:,.2f} - {var_cost:,.2f}") or {})
    if revenue is not None and var_cost is not None and qty is not None and qty > 0:
        contribution = revenue - (var_cost * qty)
        rows.append(_metric("contribution_margin", contribution, notes="Revenue - Variable Costs") or {})
        if revenue > 0:
            cm_ratio = contribution / revenue
            rows.append(_metric("contribution_margin_ratio", cm_ratio * 100, display=f"{cm_ratio*100:.1f}%", notes="(CM ÷ Revenue) × 100") or {})

    if fixed is not None and contrib_unit is not None and contrib_unit > 0:
        be_units = fixed / contrib_unit
        rows.append(_metric("break_even_units", be_units, notes=f"{fixed:,.0f} ÷ {contrib_unit:,.2f}/unit") or {})
        if price is not None and price > 0:
            rows.append(_metric("break_even_revenue", be_units * price, notes="Break-even units × price") or {})
    if fixed is not None and contribution is not None and revenue is not None and revenue > 0:
        cm_ratio = contribution / revenue
        if cm_ratio > 0:
            rows.append(_metric("break_even_revenue_cm", fixed / cm_ratio, notes="Fixed Costs ÷ CM ratio") or {})

    if avg_purchase is not None and purchases is not None and lifespan is not None:
        clv = avg_purchase * purchases * lifespan
        rows.append(_metric("clv", clv, notes=f"{avg_purchase:,.2f} × {purchases:.1f} × {lifespan:.1f} yr") or {})
        if cac is not None and cac > 0:
            rows.append(_metric("ltv_cac_ratio", clv / cac, display=f"{clv/cac:.1f}×", notes="CLV ÷ CAC") or {})

    if cac is not None:
        rows.append(_metric("cac", cac, label="FACT" if unit.get("cac") else "DERIVED") or {})
        if contrib_unit is not None and contrib_unit > 0:
            months = cac / (contrib_unit / 12) if contrib_unit else None
            if months is not None:
                rows.append(_metric("cac_payback_months", months, display=f"{months:.1f} mo", notes="CAC ÷ monthly contribution per customer") or {})

    if revenue is not None and total_expenses is not None:
        net = revenue - total_expenses
        rows.append(_metric("net_profit", net, notes="Revenue - Total Expenses") or {})
        if revenue > 0:
            rows.append(_metric("net_margin", (net / revenue) * 100, display=f"{(net/revenue)*100:.1f}%") or {})

    if revenue is not None and operating_income is not None and revenue > 0:
        rows.append(_metric("operating_margin", (operating_income / revenue) * 100, display=f"{(operating_income/revenue)*100:.1f}%") or {})

    if investment is not None and investment > 0 and revenue is not None and total_expenses is not None:
        net = revenue - total_expenses
        rows.append(_metric("roi", (net / investment) * 100, display=f"{(net/investment)*100:.1f}%") or {})
        if net > 0:
            rows.append(_metric("payback_period", investment / net, display=f"{investment/net:.1f} yr") or {})

    if new_sales is not None and old_sales is not None and old_sales > 0:
        rows.append(_metric("percent_change", ((new_sales - old_sales) / old_sales) * 100, display=f"{((new_sales-old_sales)/old_sales)*100:.1f}%") or {})

    if price is not None and cogs_unit is not None and cogs_unit > 0:
        rows.append(_metric("markup", ((price - cogs_unit) / cogs_unit) * 100, display=f"{((price-cogs_unit)/cogs_unit)*100:.1f}%") or {})

    if revenue is not None and fixed is not None and contrib_unit is not None and price is not None and contrib_unit > 0:
        be_rev = (fixed / contrib_unit) * price
        if revenue > be_rev:
            rows.append(_metric("margin_of_safety", ((revenue - be_rev) / revenue) * 100, display=f"{((revenue-be_rev)/revenue)*100:.1f}%") or {})

    return [r for r in rows if r]
