"""Business Plan workspace helpers."""
from __future__ import annotations

from typing import Any

REFERENCE_REPLIT_APP_URL = "https://aggressive-crushing-learning.replit.app"


def render_reference_iframe(st: Any) -> None:
    """Embed the Replit Business Intelligence Hub for comparison."""
    import streamlit.components.v1 as components

    st.caption("Reference app — use the same idea here and in **Plan Output** to compare results.")
    components.iframe(REFERENCE_REPLIT_APP_URL, height=720, scrolling=True)
