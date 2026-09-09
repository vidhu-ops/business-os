from backend.services.mini_gauge_service import (
    collect_public_urls,
    mini_signal_fallback,
    profile_from_mini_draft,
    validate_mini_draft,
)


def test_mini_draft_requires_basics():
    assert "company name" in " ".join(validate_mini_draft({})).lower()


def test_mini_draft_accepts_social_urls():
    draft = {
        "company_name": "Acme",
        "geography": "India",
        "gauge_type": "saas",
        "linkedin_url": "linkedin.com/company/acme",
        "instagram_url": "instagram.com/acme",
    }
    assert validate_mini_draft(draft) == []
    urls = collect_public_urls(draft)
    assert any(l == "LinkedIn" for l, _ in urls)
    assert any(l == "Instagram" for l, _ in urls)
    profile = profile_from_mini_draft(draft)
    assert profile["mini_gauge"] is True
    assert "LinkedIn" in profile["public_links"]
    assert profile["intake_source"] == "mini_gauge"


def test_mini_signal_fallback_not_all_zeros():
    draft = {
        "company_name": "IIDATECH",
        "geography": "India",
        "gauge_type": "saas",
        "website": "https://iidatech.com",
        "linkedin_url": "https://linkedin.com/company/iidatech",
        "description": "Market research and business planning platform for founders.",
        "monthly_revenue": "30000",
        "active_customers": "40",
        "team_size": "5",
    }
    profile = profile_from_mini_draft(draft)
    url_context = {
        "urls": [{"label": "Website", "url": "https://iidatech.com"}, {"label": "LinkedIn", "url": "https://linkedin.com/company/iidatech"}],
        "snippets": [
            {"label": "Website", "url": "https://iidatech.com", "snippet": "Research Plan Execute platform for founders", "fetched": "yes"},
            {"label": "LinkedIn", "url": "https://linkedin.com/company/iidatech", "snippet": "", "fetched": "no"},
        ],
        "fetched_count": 1,
        "context_text": "Research Plan Execute",
    }
    audit = mini_signal_fallback(profile, url_context)
    assert int(audit["overall_score"]) > 0
    assert max(int(c["score"]) for c in audit["categories"]) > 0
    assert "checklist" not in str(audit["categories"][0]["summary"]).lower()


def test_mini_profile_maps_positioning_fields():
    draft = {
        "company_name": "Acme",
        "geography": "India",
        "gauge_type": "saas",
        "target_customer": "SMB founders",
        "business_stage": "growing",
        "years_operating": "2",
        "revenue_model": "subscription",
        "competitors": "RivalCo",
        "differentiation": "Faster onboarding",
        "biggest_challenge": "CAC",
        "growth_goal_12m": "Double MRR",
        "website": "https://acme.com",
    }
    profile = profile_from_mini_draft(draft)
    assert profile["target_customer"] == "SMB founders"
    assert profile["operating_stage"] == "growing"
    assert profile["main_competitors"] == "RivalCo"
    assert profile["growth_goal_12_24m"] == "Double MRR"
    assert profile["plan_forward"]["biggest_bottleneck"] == "CAC"