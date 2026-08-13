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