"""Legacy full pipeline — closed to public use."""
from __future__ import annotations
from typing import Any

def render_closed_legacy_research_tab(st: Any) -> None:
    st.markdown("#### Closed for public use")
    st.info(
        "The previous multi-pass research engine is retired from public use. "
        "Use the **Market research report** tab (Perplexity + Claude, 3/8/16/25 sections)."
    )
