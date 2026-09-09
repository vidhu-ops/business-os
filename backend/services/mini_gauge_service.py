"""Mini GAUGE — short intake + public URL context + scored health snapshot."""

from __future__ import annotations

import html
import json
import re
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import urlparse

from iidatech.services.gauge_intake import GAUGE_BUSINESS_TYPES, gauge_type_label

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")
_SCRIPT_RE = re.compile(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>")


def _clean(value: Any, *, limit: int = 4000) -> str:
    return _WS_RE.sub(" ", str(value or "")).strip()[:limit]


def _num(value: Any) -> str:
    text = _clean(value, limit=80)
    if not text:
        return ""
    digits = re.sub(r"[^\d.\-]", "", text.replace(",", ""))
    return digits or text


def _normalize_url(raw: str) -> str:
    text = _clean(raw, limit=500)
    if not text:
        return ""
    if not re.match(r"^https?://", text, re.I):
        text = "https://" + text
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    return text


def collect_public_urls(draft: dict[str, Any]) -> list[tuple[str, str]]:
    """Return labeled URLs from mini draft (website + social + other)."""
    items: list[tuple[str, str]] = []
    website = _normalize_url(str(draft.get("website") or ""))
    if website:
        items.append(("Website", website))
    linkedin = _normalize_url(str(draft.get("linkedin_url") or ""))
    if linkedin:
        items.append(("LinkedIn", linkedin))
    instagram = _normalize_url(str(draft.get("instagram_url") or ""))
    if instagram:
        items.append(("Instagram", instagram))
    other_raw = str(draft.get("other_urls") or "")
    for line in other_raw.replace(",", "\n").splitlines():
        url = _normalize_url(line)
        if url and url not in {u for _, u in items}:
            items.append(("Other", url))
    return items[:8]


def fetch_url_snippet(url: str, *, limit: int = 2200) -> str:
    """Best-effort public page text for LLM context (no JS rendering)."""
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (compatible; IIDATECH-MiniGauge/1.0; "
                    "+https://iidatech.com)"
                ),
                "Accept": "text/html,application/xhtml+xml,text/plain;q=0.9,*/*;q=0.8",
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            raw = resp.read(180_000)
            charset = "utf-8"
            ctype = str(resp.headers.get("Content-Type") or "")
            if "charset=" in ctype.lower():
                charset = ctype.lower().split("charset=", 1)[1].split(";")[0].strip() or "utf-8"
            text = raw.decode(charset, errors="ignore")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, OSError):
        return ""
    except Exception:
        return ""

    text = _SCRIPT_RE.sub(" ", text)
    text = _TAG_RE.sub(" ", text)
    text = html.unescape(text)
    text = _WS_RE.sub(" ", text).strip()
    return text[:limit]


def gather_url_context(draft: dict[str, Any]) -> dict[str, Any]:
    urls = collect_public_urls(draft)
    snippets: list[dict[str, str]] = []
    for label, url in urls:
        snippet = fetch_url_snippet(url)
        snippets.append(
            {
                "label": label,
                "url": url,
                "snippet": snippet,
                "fetched": "yes" if snippet else "no",
            }
        )
    lines = []
    for row in snippets:
        if row["snippet"]:
            lines.append(f"[{row['label']}] {row['url']}\n{row['snippet']}")
        else:
            lines.append(
                f"[{row['label']}] {row['url']}\n"
                "(Could not fetch page text — use URL + public knowledge.)"
            )
    return {
        "urls": [{"label": l, "url": u} for l, u in urls],
        "snippets": snippets,
        "context_text": "\n\n".join(lines)[:12000],
    }


def validate_mini_draft(draft: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not _clean(draft.get("company_name"), limit=200):
        errors.append("Enter your company name.")
    if not _clean(draft.get("geography"), limit=200):
        errors.append("Enter your primary market / geography.")
    urls = collect_public_urls(draft)
    has_signal = bool(
        urls
        or _clean(draft.get("description"), limit=100)
        or _num(draft.get("monthly_revenue"))
        or _num(draft.get("active_customers"))
    )
    if not has_signal:
        errors.append(
            "Add a website, LinkedIn, Instagram, other URL, short description, or a quick metric."
        )
    gauge_type = _clean(draft.get("gauge_type") or "other", limit=40).lower()
    allowed = {t.get("id") for t in GAUGE_BUSINESS_TYPES if isinstance(t, dict)}
    if allowed and gauge_type not in allowed:
        errors.append("Select a valid business type.")
    return errors


def profile_from_mini_draft(
    draft: dict[str, Any], *, url_context: dict[str, Any] | None = None
) -> dict[str, Any]:
    gauge_type = _clean(draft.get("gauge_type") or "other", limit=40).lower() or "other"
    company_name = _clean(draft.get("company_name"), limit=200)
    website = ""
    for label, url in collect_public_urls(draft):
        if label == "Website":
            website = url
            break
    if not website:
        website = _normalize_url(str(draft.get("website") or ""))

    public_links = "; ".join(f"{label}: {url}" for label, url in collect_public_urls(draft))
    description = _clean(draft.get("description"), limit=4000)
    if not description and company_name:
        description = f"{gauge_type_label(gauge_type)} business operating as {company_name}."

    notes_parts = [
        "MINI GAUGE intake (short form).",
        _clean(draft.get("gauge_notes"), limit=4000),
    ]
    ctx = url_context or {}
    if ctx.get("context_text"):
        notes_parts.append("Public URL / social reads:\n" + str(ctx["context_text"]))

    monthly_rev = _num(draft.get("monthly_revenue"))
    monthly_cost = _num(draft.get("monthly_costs"))
    annual = ""
    if monthly_rev:
        try:
            annual = str(round(float(monthly_rev) * 12, 2))
        except (TypeError, ValueError):
            annual = ""

    return {
        "business_stage": "existing",
        "gauge_business_type": gauge_type,
        "gauge_business_type_label": gauge_type_label(gauge_type),
        "company_name": company_name,
        "website": website,
        "public_links": public_links[:2000],
        "business_description": description,
        "industry": _clean(draft.get("industry")) or gauge_type_label(gauge_type),
        "geography": _clean(draft.get("geography"), limit=200),
        "months_in_operation": _num(draft.get("months_in_operation")),
        "years_operating": "",
        "currency": _clean(draft.get("currency") or "USD", limit=12) or "USD",
        "monthly_revenue": monthly_rev,
        "monthly_costs": monthly_cost,
        "annual_revenue": annual,
        "monthly_opex": monthly_cost,
        "active_customers": _num(draft.get("active_customers")),
        "customer_churn_pct": "",
        "employees_ft": _num(draft.get("team_size")),
        "main_competitors": _clean(draft.get("competitors"), limit=1000),
        "gauge_notes": "\n\n".join(p for p in notes_parts if p).strip()[:12000],
        "plan_purpose": "Internal strategy",
        "target_revenue_year_3": "",
        "funding_amount_needed": "",
        "growth_goal_12_24m": "",
        "gauge_checklist_state": {},
        "gauge_checklist_summary": "Mini Gauge — checklist skipped (upgrade for full GAUGE).",
        "gauge_checklist_prompt": (
            "Mini Gauge mode: no full checklist. Infer category scores from company identity, "
            "optional metrics, and any public URL/social context provided. Mark uncertainty clearly."
        ),
        "plan_forward": {},
        "intake_source": "mini_gauge",
        "mini_gauge": True,
    }


def enrich_market_context_with_urls(profile: dict[str, Any]) -> str:
    """Extend Perplexity snapshot with social / public links when available."""
    from iidatech.services.gauge_audit import fetch_market_context_for_audit

    base = fetch_market_context_for_audit(profile)
    links = _clean(profile.get("public_links"), limit=1500)
    if not links:
        return base
    try:
        from iidatech.evidence_bank.perplexity_client import call_perplexity_json, perplexity_enabled

        if not perplexity_enabled():
            return base
        prompt = (
            "Quick public presence read for a mini business health audit.\n"
            f"Company: {profile.get('company_name')}\n"
            f"Website: {profile.get('website')}\n"
            f"Public links: {links}\n"
            f"Industry: {profile.get('industry')}\n"
            f"Geography: {profile.get('geography')}\n"
            'Return JSON: {"presence_summary":"...","positioning_clues":["..."],'
            '"risks_or_gaps":["..."],"what_to_verify":["..."]}'
        )
        api = call_perplexity_json(prompt, timeout=40)
        if api.get("error"):
            return base
        parsed = api.get("parsed") or api.get("json")
        extra = (
            json.dumps(parsed, ensure_ascii=False)[:4000]
            if isinstance(parsed, dict)
            else str(api.get("text") or "")[:4000]
        )
        if not extra:
            return base
        if base:
            return (base + "\n\nPUBLIC_PRESENCE:\n" + extra)[:9000]
        return extra[:6000]
    except Exception:
        return base


def run_mini_audit(draft: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from backend.services.gauge_service import _text_request
    from iidatech.services.gauge_audit import (
        GAUGE_AUDIT_SYSTEM,
        build_gauge_audit_user_prompt,
        extract_json_object,
        fallback_gauge_audit,
        normalize_gauge_audit,
        salvage_json_object,
    )

    url_context = gather_url_context(draft)
    profile = profile_from_mini_draft(draft, url_context=url_context)
    market_context = enrich_market_context_with_urls(profile)
    prompt = build_gauge_audit_user_prompt(profile, market_context=market_context)
    prompt = (
        "MODE: Mini GAUGE — founder gave a short form + public URLs. "
        "Produce a real scored audit (overall + 6 categories + key metrics + top actions). "
        "If data is thin, score conservatively and say what a full GAUGE would unlock.\n\n"
        + prompt
    )
    try:
        text, route = _text_request(prompt, GAUGE_AUDIT_SYSTEM, 2048, 0.1)
        clean = extract_json_object(text)
        try:
            parsed = json.loads(clean)
        except Exception:
            parsed = salvage_json_object(clean)
        if not isinstance(parsed, dict):
            raise ValueError("Mini GAUGE response was not a JSON object")
        audit = normalize_gauge_audit(parsed)
        audit["_route"] = route
        audit["_mini"] = True
        if market_context:
            audit["_market_context_used"] = True
        if url_context.get("urls"):
            audit["_urls_considered"] = url_context["urls"]
            audit["_urls_fetched"] = [
                {"label": s["label"], "url": s["url"], "fetched": s["fetched"]}
                for s in url_context.get("snippets") or []
            ]
        return audit, profile, url_context
    except Exception as exc:
        audit = fallback_gauge_audit(profile)
        audit["_route"] = f"mini_deterministic_fallback: {str(exc)[:120]}"
        audit["_mini"] = True
        if url_context.get("urls"):
            audit["_urls_considered"] = url_context["urls"]
        return audit, profile, url_context


def mini_metadata() -> dict[str, Any]:
    return {
        "business_types": GAUGE_BUSINESS_TYPES,
        "fields": [
            "company_name",
            "geography",
            "gauge_type",
            "website",
            "linkedin_url",
            "instagram_url",
            "other_urls",
            "description",
            "monthly_revenue",
            "active_customers",
            "team_size",
        ],
        "upgrade_href": "/app/audit",
        "upgrade_label": "Unlock full GAUGE audit",
    }