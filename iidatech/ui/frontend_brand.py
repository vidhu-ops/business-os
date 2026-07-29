"""User-facing brand strings for Streamlit UI (backend may still call Perplexity APIs)."""
from __future__ import annotations


def brand_frontend_text(text: str) -> str:
    if not text:
        return text
    return (
        text.replace("Perplexity Sonar Pro", "IIDATECH Research Engine")
        .replace("Perplexity-powered", "IIDATECH-powered")
        .replace("Perplexity", "IIDATECH")
        .replace("perplexity_", "iidatech_")
    )


def market_research_download_filename(topic: str) -> str:
    slug = (topic or "market")[:40].replace(" ", "_")
    return f"IIDATECH_MarketResearch_{slug}.md"
