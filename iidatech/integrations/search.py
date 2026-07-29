"""Live search via Perplexity Sonar.

Legacy provider function names (serpapi_search, tavily_search, exa_search) are
retained so execution-runtime callers keep working; all route to perplexity_client.
"""

from __future__ import annotations

from typing import Any

from iidatech.evidence_bank.perplexity_client import perplexity_enabled, search_web


def _alias_search(provider: str, query: str, *, limit: int = 8) -> tuple[list[dict], dict[str, Any]]:
    rows, diag = search_web(query, limit=limit)
    out_diag = {**diag, "provider": provider, "backend": "perplexity_sonar"}
    if not perplexity_enabled():
        out_diag["configured"] = False
        out_diag["attempted"] = False
    labeled = [{**row, "provider": provider} for row in rows]
    return labeled, out_diag


def serpapi_search(query: str, *, limit: int = 8) -> tuple[list[dict], dict[str, Any]]:
    return _alias_search("serpapi", query, limit=limit)


def tavily_search(query: str, *, limit: int = 8) -> tuple[list[dict], dict[str, Any]]:
    return _alias_search("tavily", query, limit=limit)


def exa_search(query: str, *, limit: int = 8) -> tuple[list[dict], dict[str, Any]]:
    return _alias_search("exa", query, limit=limit)


def unified_search(query: str, *, limit: int = 8) -> tuple[list[dict], list[dict[str, Any]]]:
    """Single Perplexity search (no multi-provider merge).

    INCOMPATIBILITY NOTE: previously unified_search merged SerpAPI + Tavily + Exa
    into one deduped list with up to three metric dicts. Perplexity returns one
    citation set; metrics is a one-element list.
    """
    rows, diag = search_web(query, limit=limit)
    return rows, [diag]
