from __future__ import annotations

from typing import Any


def country_choices() -> list[str]:
    try:
        from country_industry_packs import country_options

        rows = country_options()
        choices = ["Global"] + [c for c in rows if str(c).strip().lower() != "global"]
        return choices or ["Global"]
    except Exception:
        return [
            "Global",
            "India",
            "United States",
            "United Kingdom",
            "Canada",
            "Australia",
            "Germany",
            "France",
            "Netherlands",
            "Singapore",
            "United Arab Emirates",
        ]


def assess_topic_scope(topic: str, industry: str, target: str) -> dict[str, Any]:
    try:
        from iidatech.services.report_engine import _load_app_module

        app = _load_app_module(quiet=True)
        result = app.assess_topic_scope(topic, industry, target)
        if isinstance(result, dict):
            return result
    except Exception:
        pass

    from backend.services.workspaces import assess_topic_scope as basic_scope

    scope = basic_scope(topic, industry, target)
    geo = target if target and target.lower() not in {"global", "worldwide", "international"} else "India"
    scope.setdefault(
        "suggestions",
        [
            f"One product category for one buyer segment in {geo}",
            f"One workflow inside {industry or 'the industry'} for a named customer type in {geo}",
        ],
    )
    return scope
