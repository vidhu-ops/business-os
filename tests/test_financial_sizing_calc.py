from iidatech.services.financial_sizing_calc import build_canonical_financials, metric_value_missing


def test_empty_opus_base_uses_perplexity_harvest():
    opus = {
        "base_figures": {
            "industry_revenue": {"value": ""},
            "buyer_count": {"value": ""},
            "arpu_annual": {"value": ""},
            "published_reference": [],
        }
    }
    sizing = {
        "market_size_facts": [
            {
                "metric": "TAM",
                "value": "$500 million",
                "source_url": "https://ex.com",
                "notes": "niche",
            }
        ],
        "tam_candidates": [
            {"value": "$500 million", "scope": "niche", "source_url": "https://ex.com"}
        ],
    }
    out = build_canonical_financials(
        opus, geography="India", topic="CRM clinics", sizing_fallback=sizing
    )
    assert not metric_value_missing(out.get("tam")), out.get("tam")
    assert float(out["tam"]["numeric"]) == 500_000_000


def test_not_found_is_missing():
    assert metric_value_missing({"value": "[NOT FOUND]"})
    assert metric_value_missing({"value": ""})
    assert not metric_value_missing({"value": "$12M"})


def test_prebuilt_financial_fallback_kept():
    fb = {"tam": {"value": "$500M", "label": "FACT"}, "sam": {"value": "[NOT FOUND]"}}
    out = build_canonical_financials({}, geography="US", topic="SaaS", sizing_fallback=fb)
    assert out.get("tam", {}).get("value") == "$500M"
def test_stock_rent_proxy_tam():
    from iidatech.services.financial_sizing_calc import build_canonical_financials, metric_value_missing

    sizing = {
        "bottom_up_inputs": [
            {
                "metric": "stock_sqft",
                "value": "346 million sq ft",
                "source_url": "https://jll.example/warehousing",
                "notes": "India institutional warehousing",
            },
            {
                "metric": "rent_psf_month",
                "value": "Rs 28 per sq ft per month",
                "source_url": "https://kf.example/rent",
                "notes": "Grade-A Mumbai/Pune",
            },
        ],
        "top_down_inputs": [
            {
                "step": "Maharashtra share of India industrial output",
                "value": "14.2%",
                "source_url": "https://ibef.example/mh",
            }
        ],
        "tam_candidates": [
            {
                "value": "No live-web market revenue source for industrial real estate",
                "scope": "niche",
                "notes": "junk text must be ignored",
            }
        ],
    }
    out = build_canonical_financials(
        {"base_figures": {}},
        geography="India — Maharashtra",
        topic="industrial real estate leasing",
        sizing_fallback=sizing,
    )
    assert not metric_value_missing(out.get("tam")), out.get("tam")
    # 346e6 * 28 * 12 = 116,256,000,000
    assert abs(float(out["tam"]["numeric"]) - 116_256_000_000) < 1.0
