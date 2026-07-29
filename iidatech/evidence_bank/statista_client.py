"""Statista Connect API client - licensed harvest for report pipeline (no scraping)."""
from __future__ import annotations

import os
import time
from typing import Any

import requests

_STATISTA_BASE = "https://api.statista.ai"
_RESEARCH_DONE_STATUSES = frozenset(
    {
        "key_facts_generated",
        "answer_rated",
        "title_generated",
        "answer_generated",
        "done",
    }
)


def _api_key() -> str:
    try:
        from on_demand_research import local_secret_value

        return str(local_secret_value("STATISTA_API_KEY", "STATISTA_CONNECT_API_KEY") or "").strip()
    except Exception:
        pass
    return str(os.getenv("STATISTA_API_KEY") or os.getenv("STATISTA_CONNECT_API_KEY") or "").strip()


def statista_enabled() -> bool:
    if not _api_key():
        return False
    return os.getenv("STATISTA_ENABLED", "1").strip().lower() not in ("0", "false", "no", "off")


def statista_mode() -> str:
    return str(os.getenv("STATISTA_MODE", "research_ai") or "research_ai").strip().lower()


def statista_max_credits_per_report() -> int:
    try:
        return max(0, int(os.getenv("STATISTA_MAX_CREDITS_PER_REPORT", "1") or "1"))
    except ValueError:
        return 1


def _headers() -> dict[str, str]:
    return {
        "x-api-key": _api_key(),
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    timeout: int = 60,
) -> tuple[dict[str, Any] | list[Any] | None, dict[str, Any]]:
    trace: dict[str, Any] = {"path": path, "method": method, "errors": [], "status_code": None}
    url = f"{_STATISTA_BASE}{path}"
    try:
        resp = requests.request(
            method,
            url,
            headers=_headers(),
            params=params,
            json=json_body,
            timeout=timeout,
        )
        trace["status_code"] = resp.status_code
        if resp.status_code == 401:
            trace["errors"].append("statista_unauthorized_check_api_key")
            return None, trace
        if resp.status_code == 403:
            trace["errors"].append("statista_forbidden_check_api_package")
            return None, trace
        resp.raise_for_status()
        return resp.json(), trace
    except requests.RequestException as exc:
        trace["errors"].append(str(exc)[:240])
        return None, trace
    except ValueError as exc:
        trace["errors"].append(f"statista_json_parse_failed: {exc}"[:240])
        return None, trace


def search_statistics(query: str, *, size: int = 5) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    data, trace = _request(
        "GET",
        "/v1/search/statistics",
        params={"q": query, "size": max(1, min(int(size), 10))},
    )
    trace["credits"] = 1
    items: list[dict[str, Any]] = []
    if isinstance(data, dict):
        raw = data.get("items") if isinstance(data.get("items"), list) else []
        items = [row for row in raw if isinstance(row, dict)]
        trace["total_count"] = data.get("total_count")
    return items, trace


def research_ai_ask(question: str) -> tuple[str, dict[str, Any]]:
    data, trace = _request("POST", "/v1/research-ai/ask", json_body={"question": question})
    token = ""
    if isinstance(data, dict):
        token = str(data.get("researchToken") or data.get("research_token") or "").strip()
    if not token:
        trace.setdefault("errors", []).append("statista_research_ai_no_token")
    return token, trace


def research_ai_answer(
    research_token: str,
    *,
    timeout_sec: int = 120,
    poll_interval_sec: float = 2.5,
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    trace: dict[str, Any] = {"phase": "research_ai_poll", "errors": [], "polls": 0}
    if not research_token:
        trace["errors"].append("missing_research_token")
        return None, trace
    deadline = time.time() + max(15, int(timeout_sec))
    last_payload: dict[str, Any] | None = None
    while time.time() < deadline:
        data, req_trace = _request(
            "GET",
            "/v1/research-ai/answer",
            params={"research_token": research_token},
        )
        trace["polls"] = int(trace.get("polls") or 0) + 1
        if req_trace.get("errors"):
            trace["errors"].extend(req_trace["errors"])
        if not isinstance(data, dict):
            time.sleep(poll_interval_sec)
            continue
        last_payload = data
        state = data.get("state") if isinstance(data.get("state"), dict) else {}
        status = str(state.get("status") or "").strip().lower()
        trace["last_status"] = status
        if status in _RESEARCH_DONE_STATUSES and isinstance(data.get("response"), dict):
            trace["credits"] = 1
            return data, trace
        if status in {"failed", "error", "moderation_failed"}:
            trace["errors"].append(f"statista_research_ai_failed:{status}")
            return data, trace
        time.sleep(poll_interval_sec)
    trace["errors"].append("statista_research_ai_timeout")
    return last_payload, trace


def _statistics_to_facts(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facts: list[dict[str, Any]] = []
    for row in items:
        title = str(row.get("title") or row.get("subject") or "Statistic").strip()
        link = str(row.get("link") or "").strip()
        if not link.startswith("http"):
            continue
        desc = str(row.get("description") or row.get("subject") or "").strip()
        year = ""
        for key in ("released_at", "updated_at", "date"):
            val = str(row.get(key) or "").strip()
            if len(val) >= 4:
                year = val[:4]
                break
        publisher = ""
        pubs = row.get("publishers") if isinstance(row.get("publishers"), list) else []
        if pubs and isinstance(pubs[0], dict):
            publisher = str(pubs[0].get("title") or "").strip()
        facts.append(
            {
                "metric": title[:120],
                "value": desc[:240] or title[:120],
                "source_url": link,
                "year": year,
                "publisher": publisher or "Statista",
                "label": "FACT",
                "notes": "Statista Discovery search - verify figure on linked Statista page.",
            }
        )
    return facts


def _research_ai_to_facts(payload: dict[str, Any]) -> tuple[list[dict[str, Any]], str]:
    response = payload.get("response") if isinstance(payload.get("response"), dict) else {}
    answer = str(response.get("answer") or "").strip()
    facts: list[dict[str, Any]] = []
    for idx, kf in enumerate(response.get("keyFacts") or []):
        if not isinstance(kf, dict):
            continue
        title = str(kf.get("title") or f"Key fact {idx + 1}").strip()
        value = str(kf.get("value") or "").strip()
        unit = str(kf.get("unit") or "").strip()
        if unit and unit not in value:
            value = f"{value} {unit}".strip()
        if not value:
            continue
        source_url = ""
        sources = response.get("sources") if isinstance(response.get("sources"), list) else []
        if sources and isinstance(sources[0], dict):
            source_url = str(sources[0].get("url") or "").strip()
        facts.append(
            {
                "metric": title[:120],
                "value": value[:240],
                "source_url": source_url or "https://www.statista.com/",
                "year": "",
                "publisher": "Statista Research AI",
                "label": "FACT",
                "notes": "Statista Research AI key fact - tier-2 licensed source.",
            }
        )
    for src in response.get("sources") or []:
        if not isinstance(src, dict):
            continue
        url = str(src.get("url") or "").strip()
        if not url.startswith("http"):
            continue
        title = str(src.get("title") or "Statista source").strip()
        text = str(src.get("text") or src.get("titleShort") or "").strip()
        facts.append(
            {
                "metric": title[:120],
                "value": text[:240] or title[:120],
                "source_url": url,
                "year": str(src.get("releasedAt") or "")[:4],
                "publisher": str(src.get("source") or "Statista"),
                "label": "FACT",
                "notes": "Statista Research AI cited source.",
            }
        )
    return facts[:20], answer


def _build_question(topic: str, industry: str, geography: str) -> str:
    return (
        f"What is the market size, growth rate, key competitors, and pricing benchmarks for "
        f"{topic} in {geography} ({industry})? Include MSME or startup-relevant statistics where available."
    )


def statista_harvest_pack(
    topic: str,
    industry: str = "General",
    geography: str = "Global",
) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "enabled": statista_enabled(),
        "financial_facts": [],
        "competitor_facts": [],
        "pricing_facts": [],
        "source_urls": [],
        "research_ai_answer": "",
        "credits_used": 0,
        "traces": [],
        "errors": [],
        "mode": statista_mode(),
    }
    if not statista_enabled():
        empty["note"] = "statista_disabled_or_missing_api_key"
        return empty

    max_credits = statista_max_credits_per_report()
    if max_credits <= 0:
        empty["note"] = "statista_max_credits_zero"
        return empty

    mode = statista_mode()
    credits = 0
    financial_facts: list[dict[str, Any]] = []
    source_urls: list[str] = []
    traces: list[dict[str, Any]] = []
    errors: list[str] = []
    research_answer = ""
    query = f"{topic} {geography} {industry}".strip()

    if mode in ("statistics", "both") and credits < max_credits:
        items, trace = search_statistics(query, size=5)
        traces.append({"phase": "statista_search_statistics", **trace})
        if trace.get("errors"):
            errors.extend(str(e) for e in trace["errors"])
        else:
            credits += int(trace.get("credits") or 1)
            financial_facts.extend(_statistics_to_facts(items))
            for row in items:
                link = str(row.get("link") or "").strip()
                if link.startswith("http"):
                    source_urls.append(link)

    if mode in ("research_ai", "both") and credits < max_credits:
        question = _build_question(topic, industry, geography)
        token, ask_trace = research_ai_ask(question)
        traces.append({"phase": "statista_research_ai_ask", **ask_trace})
        if ask_trace.get("errors"):
            errors.extend(str(e) for e in ask_trace["errors"])
        elif token:
            payload, poll_trace = research_ai_answer(token)
            traces.append({"phase": "statista_research_ai_answer", **poll_trace})
            if poll_trace.get("errors"):
                errors.extend(str(e) for e in poll_trace["errors"])
            if isinstance(payload, dict):
                credits += int(poll_trace.get("credits") or 1)
                ai_facts, research_answer = _research_ai_to_facts(payload)
                financial_facts.extend(ai_facts)
                response = payload.get("response") if isinstance(payload.get("response"), dict) else {}
                for src in response.get("sources") or []:
                    if isinstance(src, dict):
                        url = str(src.get("url") or "").strip()
                        if url.startswith("http"):
                            source_urls.append(url)

    seen: set[str] = set()
    deduped: list[dict[str, Any]] = []
    for fact in financial_facts:
        if not isinstance(fact, dict):
            continue
        key = f"{fact.get('metric')}|{fact.get('source_url')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(fact)

    return {
        "enabled": True,
        "financial_facts": deduped[:25],
        "competitor_facts": [],
        "pricing_facts": [],
        "source_urls": list(dict.fromkeys(source_urls))[:20],
        "research_ai_answer": research_answer,
        "credits_used": credits,
        "traces": traces,
        "errors": errors,
        "mode": mode,
        "note": "statista_licensed_harvest",
    }


def merge_statista_into_harvest(
    harvest: dict[str, Any],
    statista_pack: dict[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    out = dict(harvest or {})
    citations = [
        str(u).strip()
        for u in (statista_pack.get("source_urls") or [])
        if str(u).strip().startswith("http")
    ]
    for key in ("financial_facts", "competitor_facts", "pricing_facts"):
        pri = [r for r in (statista_pack.get(key) or []) if isinstance(r, dict)]
        sec = [r for r in (out.get(key) or []) if isinstance(r, dict)]
        out[key] = pri + sec
    notes = str(statista_pack.get("research_ai_answer") or "").strip()
    if notes:
        prior = str(out.get("search_notes") or "").strip()
        block = f"STATISTA RESEARCH AI SUMMARY: {notes[:1200]}"
        out["search_notes"] = f"{block}\n\n{prior}".strip() if prior else block
    out["statista"] = {
        "credits_used": statista_pack.get("credits_used", 0),
        "mode": statista_pack.get("mode"),
        "fact_count": len(statista_pack.get("financial_facts") or []),
    }
    return out, citations


def format_statista_block(statista_pack: dict[str, Any]) -> str:
    if not statista_pack or not statista_pack.get("enabled"):
        return ""
    lines = [
        "STATISTA LICENSED DATA (tier-2 - prefer over blogs; cite source_url on each row):",
        f"- Mode: {statista_pack.get('mode')} - Credits used this report: {statista_pack.get('credits_used', 0)}",
        "",
    ]
    for fact in (statista_pack.get("financial_facts") or [])[:12]:
        if isinstance(fact, dict):
            lines.append(
                f"- [{fact.get('label', 'FACT')}] {fact.get('metric')}: {fact.get('value')} ({fact.get('source_url')})"
            )
    answer = str(statista_pack.get("research_ai_answer") or "").strip()
    if answer:
        lines.extend(["", "Research AI summary:", answer[:1500]])
    return "\n".join(lines).strip()
