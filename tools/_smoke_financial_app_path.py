"""End-to-end financial path smoke (no live LLM calls)."""
from __future__ import annotations

from iidatech.services.financial_sizing_calc import (
    build_canonical_financials,
    metric_value_missing,
)
from iidatech.services.simple_perplexity_report import (
    build_financial_snapshot_section,
    _fallback_financial_from_sizing,
    _format_financial_block,
)


def _assert_has_tam(label, financial):
    tam = (financial or {}).get("tam") or {}
    assert not metric_value_missing(tam), f"{label}: missing TAM -> {tam}"
    assert float(tam.get("numeric") or 0) > 0 or "$" in str(tam.get("value")) or "Cr" in str(tam.get("value")) or "M" in str(tam.get("value")), tam
    print(f"OK {label}: TAM={tam.get('value')} SAM={(financial.get('sam') or {}).get('value')} SOM={(financial.get('som') or {}).get('value')}")


def test_app_path_empty_opus_plus_revenue_harvest():
    """Mirrors research.py: Opus empty base_figures + Perplexity sizing harvest."""
    opus = {"base_figures": {"industry_revenue": {"value": ""}, "published_reference": []}}
    sizing = {
        "market_size_facts": [
            {"metric": "TAM", "value": "$1.2 billion", "source_url": "https://ex.com/tam", "geography_scope": "niche", "notes": "category"}
        ],
        "tam_candidates": [{"value": "$1.2 billion", "scope": "niche", "source_url": "https://ex.com/tam"}],
    }
    financial = build_canonical_financials(opus, geography="United States", topic="CRM SaaS", sizing_fallback=sizing)
    if metric_value_missing((financial or {}).get("tam")):
        harvested = _fallback_financial_from_sizing(sizing)
        if harvested and not metric_value_missing(harvested.get("tam")):
            financial = harvested
        else:
            financial = build_canonical_financials({}, geography="United States", topic="CRM SaaS", sizing_fallback=sizing)
    _assert_has_tam("revenue-harvest", financial)
    block = _format_financial_block(financial)
    assert "1.2" in block or "1200" in block or "B" in block or "NOT FOUND" not in block.split("TAM")[1][:80]
    section, _ = build_financial_snapshot_section(financial, "United States")
    assert "[NOT FOUND]" not in section.split("Primary market sizing")[1].split("Top-down")[0]
    assert "TAM" in section


def test_app_path_industrial_stock_rent_proxy():
    """Industrial real-estate case: no INR revenue TAM, but stock + rent + state share."""
    opus = {
        "base_figures": {
            "industry_revenue": {"value": ""},
            "buyer_count": {"value": ""},
            "arpu_annual": {"value": ""},
            "stock_sqft": {"value": ""},
            "rent_psf": {"value": ""},
            "published_reference": [{"value": "No live-web market revenue source", "scope": "niche"}],
        }
    }
    sizing = {
        "market_size_facts": [],
        "tam_candidates": [
            {"value": "No live-web market revenue source for industrial real estate leasing and construction in Maharashtra was provided in the available search results.", "scope": "niche"}
        ],
        "bottom_up_inputs": [
            {"metric": "stock_sqft", "value": "346 million sq ft", "source_url": "https://www.jll.co.in/warehousing", "notes": "India institutional warehousing stock"},
            {"metric": "rent_psf_month", "value": "Rs 28 per sq ft per month", "source_url": "https://www.knightfrank.com/india-warehousing", "notes": "Grade-A Mumbai/Pune"},
        ],
        "top_down_inputs": [
            {"step": "Maharashtra share of India industrial output", "value": "14.2%", "source_url": "https://www.ibef.org/states/maharashtra"},
        ],
        "denominator_facts": [],
    }
    financial = build_canonical_financials(
        opus,
        geography="India — Maharashtra",
        topic="real estate leasing and construction for industrial sector",
        sizing_fallback=sizing,
    )
    if metric_value_missing((financial or {}).get("tam")):
        harvested = _fallback_financial_from_sizing(sizing)
        if harvested and not metric_value_missing(harvested.get("tam")):
            financial = harvested
        else:
            financial = build_canonical_financials(
                {},
                geography="India — Maharashtra",
                topic="real estate leasing and construction for industrial sector",
                sizing_fallback=sizing,
            )
    _assert_has_tam("industrial-proxy", financial)
    assert not metric_value_missing(financial.get("sam"))
    assert not metric_value_missing(financial.get("som"))
    section, _ = build_financial_snapshot_section(financial, "India — Maharashtra")
    primary = section.split("Primary market sizing")[1].split("Top-down")[0]
    assert "[NOT FOUND]" not in primary, primary
    assert "Cr" in primary or "₹" in primary
    print("SNAPSHOT OK:\n", "\n".join(primary.strip().splitlines()[:12]))


def test_junk_only_sizing_still_missing():
    """If literally no numeric inputs exist, NOT FOUND is correct."""
    sizing = {
        "tam_candidates": [{"value": "No live-web market revenue source", "scope": "niche"}],
        "market_size_facts": [],
    }
    financial = build_canonical_financials(
        {"base_figures": {}},
        geography="India — Maharashtra",
        topic="industrial real estate",
        sizing_fallback=sizing,
    )
    assert metric_value_missing((financial or {}).get("tam"))
    print("OK junk-only correctly missing")


if __name__ == "__main__":
    test_app_path_empty_opus_plus_revenue_harvest()
    test_app_path_industrial_stock_rent_proxy()
    test_junk_only_sizing_still_missing()
    print("APP FINANCIAL PATH PASS")