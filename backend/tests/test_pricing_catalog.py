from backend.services.pricing_catalog import (
    credit_cost_for_action,
    normalize_plan_id,
    research_credit_cost,
    resolve_checkout_plan_id,
    signup_credits_for_plan,
)


def test_normalize_plan_aliases():
    assert normalize_plan_id("starter") == "starter"
    assert normalize_plan_id("growth") == "growth"
    assert resolve_checkout_plan_id("starter") == "growth"


def test_research_tier_credits():
    assert research_credit_cost(3) == 5
    assert research_credit_cost(8) == 8
    assert research_credit_cost(16) == 15
    assert research_credit_cost(25) == 20


def test_credit_cost_for_research_with_sections():
    assert credit_cost_for_action("research", section_count=16) == 15
    assert credit_cost_for_action("business_plan") == 5


def test_signup_credits():
    assert signup_credits_for_plan("starter") == 30


def test_employee_work_and_mentor_cost_one_credit():
    assert credit_cost_for_action("employee_work") == 1
    assert credit_cost_for_action("mentor") == 1
