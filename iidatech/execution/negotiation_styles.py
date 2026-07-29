"""Role negotiation styles for Employee OS debates."""
from __future__ import annotations

from typing import Any

NEGOTIATION_STYLES: dict[str, dict[str, Any]] = {
    "Research Analyst": {
        "style": "skeptical",
        "traits": ["evidence_obsessed", "blocks_weak_claims"],
        "risk_tolerance": 0.15,
        "priority": 1,
    },
    "Growth Marketer": {
        "style": "aggressive",
        "traits": ["wants_experimentation", "tolerates_uncertainty"],
        "risk_tolerance": 0.85,
        "priority": 2,
    },
    "Finance Manager": {
        "style": "conservative",
        "traits": ["blocks_risky_spend", "runway_focused"],
        "risk_tolerance": 0.2,
        "priority": 1,
    },
    "Sales Lead": {
        "style": "opportunity_driven",
        "traits": ["pushes_for_speed", "pipeline_first"],
        "risk_tolerance": 0.7,
        "priority": 3,
    },
    "COO": {
        "style": "mediator",
        "traits": ["resolves_execution_conflicts", "compromise_builder"],
        "risk_tolerance": 0.5,
        "priority": 9,
    },
}


def get_negotiation_style(role: str) -> dict[str, Any]:
    return dict(NEGOTIATION_STYLES.get(role, {"style": "collaborative", "traits": [], "risk_tolerance": 0.5, "priority": 5}))