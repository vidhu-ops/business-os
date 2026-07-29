"""GAUGE business health instrument types and checklists."""

from __future__ import annotations

from typing import Any

GAUGE_STEP_LABELS = ["Business", "Checklist", "Data"]

GAUGE_BUSINESS_TYPES: list[dict[str, str]] = [
    {"id": 'saas', "label": 'Software / SaaS'},
    {"id": 'ecommerce', "label": 'E-commerce'},
    {"id": 'retail', "label": 'Retail / Brick & Mortar'},
    {"id": 'restaurant', "label": 'Restaurant / Food Service'},
    {"id": 'agency', "label": 'Agency / Service / Consulting'},
    {"id": 'other', "label": 'Other'},
]

GAUGE_CHECKLISTS: dict[str, dict[str, list[str]]] = {
    'saas': {
        'Financials': ['We track MRR/ARR monthly', 'We know our gross margin', 'We track cash runway'],
        'Customers': ['We track monthly churn rate', 'We know average LTV per customer', 'We segment customers by plan/tier'],
        'Sales & Marketing': ['We track CAC by channel', 'We know our free-to-paid conversion rate', 'We have a defined pricing/packaging strategy'],
        'Operations': ['We track uptime/reliability', 'We have a documented onboarding flow', 'We use a support ticketing system'],
        'Product & Team': ['We track feature usage/adoption', 'We have a public product roadmap', 'Team responsibilities are clearly divided'],
        'Competitive Position': ['We track at least 3 direct competitors', 'We know our differentiation vs competitors', 'We monitor competitor pricing changes'],
    },
    'ecommerce': {
        'Financials': ['We track revenue by product/SKU', 'We know gross margin after shipping/returns', 'We track cash flow monthly'],
        'Customers': ['We track repeat purchase rate', 'We know average order value (AOV)', 'We track reviews/ratings'],
        'Sales & Marketing': ['We track CAC by ad channel', 'We know our conversion rate (visits to sales)', 'We run email/SMS retention campaigns'],
        'Operations': ['We track fulfillment time and accuracy', 'We track return/refund rate', 'We forecast inventory'],
        'Product & Team': ['We track best/worst selling products', 'We have a process for new product launches', 'Team roles for ops/marketing/support are clear'],
        'Competitive Position': ['We track competitor pricing', 'We know our market share estimate', 'We monitor competitor reviews/positioning'],
    },
    'retail': {
        'Financials': ['We track sales per square foot', 'We track gross margin by category', 'We track monthly cash flow'],
        'Customers': ['We track repeat customer visits', 'We collect customer feedback', 'We know average basket size'],
        'Sales & Marketing': ['We track foot traffic', 'We run local promotions/events', 'We have a loyalty program'],
        'Operations': ['We track inventory turnover', 'We track shrinkage/loss', 'Staff scheduling matches peak hours'],
        'Product & Team': ['We track best/worst selling products', 'We have a restocking/reorder process', 'Staff roles are clearly defined'],
        'Competitive Position': ['We track nearby competitor pricing', 'We know what differentiates our store', 'We monitor foot traffic trends in the area'],
    },
    'restaurant': {
        'Financials': ['We track food cost percentage', 'We track labor cost percentage', 'We track daily/weekly sales trends'],
        'Customers': ['We track repeat customer rate', 'We collect customer feedback/reviews', 'We know our average check size'],
        'Sales & Marketing': ['We run local marketing/promotions', 'We track delivery platform performance', 'We have an active social presence'],
        'Operations': ['We track table turnover/wait times', 'We track supplier/vendor costs', 'We track waste/spoilage'],
        'Product & Team': ['We track best/worst selling menu items', 'Staff scheduling matches demand patterns', 'We have a training process for new staff'],
        'Competitive Position': ['We know nearby competitor pricing', 'We track our online rating vs competitors', 'We know what makes us different locally'],
    },
    'agency': {
        'Financials': ['We track revenue per client/project', 'We know profit margin per project type', 'We track monthly cash flow'],
        'Customers': ['We track client retention/renewal rate', 'We know client lifetime value', 'We collect client satisfaction feedback'],
        'Sales & Marketing': ['We track lead source and conversion rate', 'We have a defined sales pipeline', 'We track proposal win rate'],
        'Operations': ['We track team utilization/billable hours', 'We have documented project workflows', 'We track project profitability'],
        'Product & Team': ['Service offerings are clearly packaged', 'We track employee workload/capacity', 'We have an onboarding process for new hires'],
        'Competitive Position': ['We track competitor pricing/positioning', 'We know our niche differentiation', 'We track referral sources'],
    },
    'other': {
        'Financials': ['We track monthly revenue and costs', 'We know our profit margin', 'We track cash flow'],
        'Customers': ['We track customer retention', 'We know customer lifetime value', 'We collect customer feedback'],
        'Sales & Marketing': ['We track where customers/leads come from', 'We track conversion rate', 'We have a defined pricing strategy'],
        'Operations': ['We have documented core processes', 'We track key operational bottlenecks', 'We use tools/software to run operations'],
        'Product & Team': ['We track product/service performance', 'Team roles are clearly defined', 'We have a hiring/onboarding process'],
        'Competitive Position': ['We track direct competitors', 'We know our differentiation', 'We monitor broader industry trends'],
    },
}

_TYPE_LABEL_BY_ID: dict[str, str] = {t["id"]: t["label"] for t in GAUGE_BUSINESS_TYPES}


def _category_session_slug(category: str) -> str:
    """Stable session-state token for a checklist category name."""
    return category.replace(" & ", "_and_").replace(" ", "_")


def gauge_checklist_session_key(type_id: str, category: str, index: int) -> str:
    """Session key for a single checklist checkbox (Streamlit ``key=``)."""
    return f"existing_biz_chk_{type_id}_{_category_session_slug(category)}_{index}"


def gauge_checklist_value_session_key(type_id: str, category: str, index: int) -> str:
    """Session key for the numeric value tied to a checked checklist item."""
    return f"existing_biz_chk_val_{type_id}_{_category_session_slug(category)}_{index}"


def gauge_type_label(type_id: str) -> str:
    return _TYPE_LABEL_BY_ID.get(type_id, "business")


def checklist_for_type(type_id: str) -> dict[str, list[str]]:
    return GAUGE_CHECKLISTS.get(type_id) or GAUGE_CHECKLISTS["other"]


def _checklist_entry_checked(entry: Any) -> bool:
    if isinstance(entry, dict):
        return bool(entry.get("checked"))
    return bool(entry)


def _checklist_entry_value(entry: Any) -> str:
    if isinstance(entry, dict):
        return str(entry.get("value") or "").strip()
    return ""


def collect_gauge_checklist_state(
    st: Any,
    type_id: str,
    *,
    key_prefix: str = "existing_biz",
) -> dict[str, list[dict[str, Any]]]:
    """Collect checked flags and optional values for each checklist item."""
    data = checklist_for_type(type_id)
    state: dict[str, list[dict[str, Any]]] = {}
    slug = _category_session_slug
    for category, items in data.items():
        entries: list[dict[str, Any]] = []
        for index in range(len(items)):
            chk_key = f"{key_prefix}_chk_{type_id}_{slug(category)}_{index}"
            val_key = f"{key_prefix}_chk_val_{type_id}_{slug(category)}_{index}"
            if chk_key not in st.session_state and key_prefix == "existing_biz":
                chk_key = gauge_checklist_session_key(type_id, category, index)
                val_key = gauge_checklist_value_session_key(type_id, category, index)
            checked = bool(st.session_state.get(chk_key, False))
            value = str(st.session_state.get(val_key) or "").strip() if checked else ""
            entries.append({"checked": checked, "value": value})
        state[category] = entries
    return state


def gauge_checklist_summary(
    type_id: str,
    checklist_state: dict[str, list[Any]],
) -> dict[str, dict[str, list[str]]]:
    """Per category, split checklist items into has / missing lists."""
    items_by_cat = checklist_for_type(type_id)
    summary: dict[str, dict[str, list[str]]] = {}
    for category, items in items_by_cat.items():
        flags = checklist_state.get(category, [])
        has: list[str] = []
        missing: list[str] = []
        for index, item in enumerate(items):
            entry = flags[index] if index < len(flags) else False
            if _checklist_entry_checked(entry):
                value = _checklist_entry_value(entry)
                has.append(f"{item} (value: {value})" if value else item)
            else:
                missing.append(item)
        summary[category] = {"has": has, "missing": missing}
    return summary


def gauge_checklist_prompt_lines(type_id: str, checklist_state: dict[str, list[Any]]) -> str:
    """Format checklist state like GAUGE ``buildPrompt`` checklist section."""
    summary = gauge_checklist_summary(type_id, checklist_state)
    blocks: list[str] = []
    for category in checklist_for_type(type_id):
        part = summary[category]
        has_text = "; ".join(part["has"]) if part["has"] else "none"
        missing_text = "; ".join(part["missing"]) if part["missing"] else "none"
        blocks.append(f"{category}:\n  Has: {has_text}\n  Missing: {missing_text}")
    return "\n".join(blocks)


def gauge_category_scores(type_id: str, checklist_state: dict[str, list[Any]]) -> dict[str, int]:
    """Simple 0-100 score per GAUGE category from checklist completion."""
    items_by_cat = checklist_for_type(type_id)
    scores: dict[str, int] = {}
    for category, items in items_by_cat.items():
        entries = checklist_state.get(category, [])
        if not items:
            scores[category] = 50
            continue
        done = sum(1 for index in range(len(items)) if _checklist_entry_checked(entries[index] if index < len(entries) else False))
        scores[category] = int(round(100 * done / len(items)))
    return scores

