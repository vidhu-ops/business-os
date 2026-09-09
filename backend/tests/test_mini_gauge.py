from backend.services.mini_gauge_service import (
    collect_public_urls,
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