"""Deterministic TAM / SAM / SOM from Opus-extracted base figures (sourced via Perplexity)."""
from __future__ import annotations

import re
from typing import Any

from iidatech.services.market_currency import currency_for_geography

_PCT_RE = re.compile(r"([\d,.]+)\s*%")
_NUM_RE = re.compile(
    r"(?:₹|Rs\.?|\$|USD|INR|GBP|€|EUR)?\s*([\d,]+(?:\.\d+)?)\s*"
    r"(lakh\s*crore|lakh\s*cr|crore|cr|lakh|lac|billion|million|bn|m|thousand|k)?",
    re.I,
)


def _pct_value(raw: Any) -> float | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        v = float(raw)
        return v / 100.0 if v > 1 else v
    text = str(raw).strip()
    if not text:
        return None
    m = _PCT_RE.search(text)
    if m:
        try:
            return float(m.group(1).replace(",", "")) / 100.0
        except ValueError:
            return None
    try:
        v = float(text.replace(",", ""))
        return v / 100.0 if v > 1 else v
    except ValueError:
        return None


def parse_market_value(text: str) -> float | None:
    """Parse currency amounts including Indian lakh / crore notation."""
    s = str(text or "").strip()
    if not s:
        return None
    s = re.sub(r"\[(?:NOT FOUND|FACT|DERIVED|ESTIMATE)\]", "", s, flags=re.I).strip()
    m = _NUM_RE.search(s)
    if not m:
        return None
    try:
        amount = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    unit = (m.group(2) or "").lower().replace(" ", "")
    mult = 1.0
    if "lakhcrore" in unit or "lakhcr" in unit:
        mult = 1e12
    elif "crore" in unit or unit == "cr":
        mult = 1e7
    elif "lakh" in unit or unit == "lac":
        mult = 1e5
    elif "billion" in unit or unit == "bn":
        mult = 1e9
    elif unit == "m" or "million" in unit:
        mult = 1e6
    elif unit == "k" or "thousand" in unit:
        mult = 1e3
    return amount * mult


def _figure_numeric(row: dict[str, Any]) -> float | None:
    if not isinstance(row, dict):
        return None
    for key in ("numeric", "numeric_value", "amount"):
        if row.get(key) is not None:
            try:
                return float(row[key])
            except (TypeError, ValueError):
                pass
    return parse_market_value(str(row.get("value") or ""))


def _figure_pct(row: dict[str, Any]) -> float | None:
    if not isinstance(row, dict):
        return None
    if row.get("value_pct") is not None:
        return _pct_value(row.get("value_pct"))
    return _pct_value(row.get("value") or row.get("pct"))


def _format_currency(amount: float, currency: dict[str, Any]) -> str:
    code = str(currency.get("code") or "USD").upper()
    symbol = str(currency.get("symbol") or "$")
    if amount <= 0:
        return "[NOT FOUND]"
    if code == "INR":
        if amount >= 1e12:
            return f"{symbol}{amount / 1e12:.2f} lakh crore"
        if amount >= 1e7:
            return f"{symbol}{amount / 1e7:.2f} Cr"
        if amount >= 1e5:
            return f"{symbol}{amount / 1e5:.2f} L"
        return f"{symbol}{amount:,.0f}"
    if amount >= 1e9:
        return f"{symbol}{amount / 1e9:.2f}B"
    if amount >= 1e6:
        return f"{symbol}{amount / 1e6:.2f}M"
    if amount >= 1e3:
        return f"{symbol}{amount / 1e3:.2f}K"
    return f"{symbol}{amount:,.0f}"


def _row(
    value: float,
    *,
    label: str,
    source_url: str = "",
    source_name: str = "",
    notes: str = "",
    currency: dict[str, Any],
) -> dict[str, Any]:
    return {
        "value": _format_currency(value, currency),
        "numeric": value,
        "label": label,
        "source_url": source_url,
        "source_name": source_name,
        "notes": notes,
    }


def _pick_tam_from_candidates(
    candidates: list[dict[str, Any]],
    topic: str,
) -> tuple[float | None, dict[str, Any] | None]:
    """Prefer niche-scoped published TAM when multiple candidates exist."""
    topic_tokens = {t for t in re.findall(r"[a-z]{4,}", str(topic).lower())}
    best: tuple[float, dict[str, Any], int] | None = None
    for cand in candidates:
        if not isinstance(cand, dict):
            continue
        val = _figure_numeric(cand)
        if val is None or val <= 0:
            continue
        scope = str(cand.get("scope") or "").lower()
        notes = str(cand.get("notes") or "").lower()
        blob = f"{scope} {notes} {cand.get('value', '')}".lower()
        score = 0
        if scope in {"niche", "segment", "category"}:
            score += 3
        if scope in {"domestic", "national"}:
            score += 1
        if any(tok in blob for tok in topic_tokens):
            score += 2
        if scope == "global" or "adjacent" in scope:
            score -= 1
        if best is None or score > best[2] or (score == best[2] and val < best[0]):
            best = (val, cand, score)
    if best:
        return best[0], best[1]
    return None, None


def compute_from_base_figures(
    base: dict[str, Any],
    *,
    geography: str,
    topic: str,
) -> dict[str, Any]:
    currency = currency_for_geography(geography)

    industry = base.get("industry_revenue") if isinstance(base.get("industry_revenue"), dict) else {}
    niche_slice = base.get("niche_slice_pct") if isinstance(base.get("niche_slice_pct"), dict) else {}
    buyers = base.get("buyer_count") if isinstance(base.get("buyer_count"), dict) else {}
    addressable = base.get("addressable_pct") if isinstance(base.get("addressable_pct"), dict) else {}
    arpu = base.get("arpu_annual") if isinstance(base.get("arpu_annual"), dict) else {}
    geo_f = base.get("geo_filter_pct") if isinstance(base.get("geo_filter_pct"), dict) else {}
    seg_f = base.get("segment_filter_pct") if isinstance(base.get("segment_filter_pct"), dict) else {}
    fit_f = base.get("product_fit_pct") if isinstance(base.get("product_fit_pct"), dict) else {}
    som_cap = base.get("som_capture_pct") if isinstance(base.get("som_capture_pct"), dict) else {}

    industry_val = _figure_numeric(industry)
    niche_pct = _figure_pct(niche_slice) or 1.0
    buyer_n = _figure_numeric(buyers)
    addr_pct = _figure_pct(addressable) or 1.0
    arpu_n = _figure_numeric(arpu)
    geo_pct = _figure_pct(geo_f) if geo_f else 1.0
    seg_pct = _figure_pct(seg_f) if seg_f else 1.0
    fit_pct = _figure_pct(fit_f) if fit_f else 1.0
    som_pct = _figure_pct(som_cap) or 0.04

    refs = base.get("published_reference") if isinstance(base.get("published_reference"), list) else []
    pub_tam, pub_row = _pick_tam_from_candidates(refs, topic)

    top_down_tam: float | None = None
    if industry_val and industry_val > 0:
        top_down_tam = industry_val * niche_pct

    bottom_up_tam: float | None = None
    if buyer_n and arpu_n and buyer_n > 0 and arpu_n > 0:
        bottom_up_tam = buyer_n * addr_pct * arpu_n

    tam_val: float | None = None
    tam_notes = ""
    tam_label = "DERIVED"
    tam_source = industry.get("source_url") or (pub_row or {}).get("source_url") or ""
    tam_source_name = industry.get("source_name") or (pub_row or {}).get("source_name") or ""

    if top_down_tam and bottom_up_tam:
        ratio = max(top_down_tam, bottom_up_tam) / min(top_down_tam, bottom_up_tam)
        if ratio <= 2.0:
            tam_val = (top_down_tam + bottom_up_tam) / 2.0
            tam_notes = (
                f"Reconciled top-down ({_format_currency(top_down_tam, currency)}) and "
                f"bottom-up ({_format_currency(bottom_up_tam, currency)}); within 2× — averaged."
            )
        else:
            tam_val = bottom_up_tam
            tam_notes = (
                f"Top-down {_format_currency(top_down_tam, currency)} vs bottom-up "
                f"{_format_currency(bottom_up_tam, currency)} (>2×) — niche bottom-up used."
            )
    elif bottom_up_tam:
        tam_val = bottom_up_tam
        tam_notes = (
            f"Bottom-up: {buyer_n:,.0f} buyers × {addr_pct*100:.1f}% addressable × "
            f"{_format_currency(arpu_n, currency)} ARPU"
        )
        tam_label = "DERIVED"
    elif top_down_tam:
        tam_val = top_down_tam
        tam_notes = (
            f"Top-down: {_format_currency(industry_val, currency)} industry × {niche_pct*100:.1f}% niche slice"
        )
        tam_label = "DERIVED"
    elif pub_tam:
        tam_val = pub_tam
        tam_notes = str((pub_row or {}).get("notes") or "Published reference TAM for niche/category")
        tam_label = "FACT"
        tam_source = str((pub_row or {}).get("source_url") or "")
        tam_source_name = str((pub_row or {}).get("source_name") or "")

    sam_val = tam_val * geo_pct * seg_pct * fit_pct if tam_val else None
    som_val = sam_val * som_pct if sam_val else None

    sam_notes = (
        f"TAM × geo {geo_pct*100:.0f}% × segment {seg_pct*100:.0f}% × product-fit {fit_pct*100:.0f}%"
        if sam_val
        else ""
    )
    som_notes = f"{som_pct*100:.1f}% of SAM — 3–5 year obtainable capture" if som_val else ""

    top_down_block = {
        "method": "Industry revenue × niche slice",
        "formula": (
            f"{_format_currency(industry_val or 0, currency)} × {niche_pct*100:.1f}%"
            if industry_val
            else ""
        ),
        "result": _format_currency(top_down_tam or 0, currency) if top_down_tam else "",
        "label": "DERIVED",
        "source_url": str(industry.get("source_url") or ""),
        "notes": str(niche_slice.get("notes") or ""),
    }
    bottom_up_block = {
        "method": "Buyers × addressable % × annual ARPU",
        "formula": (
            f"{buyer_n:,.0f} × {addr_pct*100:.1f}% × {_format_currency(arpu_n or 0, currency)}"
            if buyer_n and arpu_n
            else ""
        ),
        "result": _format_currency(bottom_up_tam or 0, currency) if bottom_up_tam else "",
        "label": "DERIVED",
        "source_url": str(arpu.get("source_url") or buyers.get("source_url") or ""),
        "notes": "",
    }

    return {
        "currency": currency,
        "tam": _row(
            tam_val or 0,
            label=tam_label,
            source_url=str(tam_source or ""),
            source_name=str(tam_source_name or ""),
            notes=tam_notes,
            currency=currency,
        )
        if tam_val
        else {
            "value": "[NOT FOUND]",
            "label": "NOT FOUND",
            "notes": "Insufficient sourced inputs for TAM",
            "source_url": "",
            "source_name": "",
        },
        "sam": _row(sam_val or 0, label="DERIVED", notes=sam_notes, currency=currency)
        if sam_val
        else {
            "value": "[NOT FOUND]",
            "label": "NOT FOUND",
            "notes": "SAM requires TAM",
            "source_url": "",
            "source_name": "",
        },
        "som": _row(som_val or 0, label="DERIVED", notes=som_notes, currency=currency)
        if som_val
        else {
            "value": "[NOT FOUND]",
            "label": "NOT FOUND",
            "notes": "SOM requires SAM",
            "source_url": "",
            "source_name": "",
        },
        "top_down": top_down_block,
        "bottom_up": bottom_up_block,
        "validation": {
            "top_down_result": _format_currency(top_down_tam or 0, currency) if top_down_tam else "",
            "bottom_up_result": _format_currency(bottom_up_tam or 0, currency) if bottom_up_tam else "",
            "reconciled": bool(
                top_down_tam
                and bottom_up_tam
                and max(top_down_tam, bottom_up_tam) / min(top_down_tam, bottom_up_tam) <= 2.0
            ),
            "notes": tam_notes,
        },
        "tam_reconciliation": tam_notes,
        "published_reference": refs,
        "financial_rows": [],
        "commentary": [],
        "computed": True,
    }


def metric_value_missing(row: Any) -> bool:
    """True when a TAM/SAM/SOM (or similar) cell has no usable figure."""
    if not isinstance(row, dict):
        return True
    raw = str(row.get("value") or "").strip()
    if not raw:
        return True
    upper = raw.upper().replace("—", "-")
    if upper in {"[NOT FOUND]", "NOT FOUND", "N/A", "NA", "-", "—", "NONE", "UNKNOWN"}:
        return True
    if "NOT FOUND" in upper:
        return True
    return False


def _base_figures_usable(base: dict[str, Any]) -> bool:
    """True when Opus base_figures contain at least one parseable sizing input."""
    if not isinstance(base, dict) or not base:
        return False
    industry = base.get("industry_revenue") if isinstance(base.get("industry_revenue"), dict) else {}
    buyers = base.get("buyer_count") if isinstance(base.get("buyer_count"), dict) else {}
    arpu = base.get("arpu_annual") if isinstance(base.get("arpu_annual"), dict) else {}
    refs = base.get("published_reference") if isinstance(base.get("published_reference"), list) else []
    if _figure_numeric(industry):
        return True
    if _figure_numeric(buyers) and _figure_numeric(arpu):
        return True
    for ref in refs:
        if isinstance(ref, dict) and _figure_numeric(ref):
            return True
    return False


def _attach_opus_extras(computed: dict[str, Any], opus_parsed: dict[str, Any]) -> dict[str, Any]:
    for key in ("commentary", "illustrative_scenario"):
        if opus_parsed.get(key):
            computed[key] = opus_parsed[key]
    extra_rows = [
        r
        for r in (opus_parsed.get("financial_rows") or [])
        if isinstance(r, dict)
        and not re.search(r"\bTAM\b|\bSAM\b|\bSOM\b", str(r.get("metric") or ""), re.I)
    ]
    if extra_rows:
        computed["financial_rows"] = list(computed.get("financial_rows") or []) + extra_rows
    return computed


def build_canonical_financials(
    opus_parsed: dict[str, Any],
    *,
    geography: str,
    topic: str,
    sizing_fallback: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge Opus base-figure extraction with deterministic TAM/SAM/SOM math.

    Empty Opus ``base_figures`` must not block Perplexity sizing harvest — otherwise
    reports keep showing ``[NOT FOUND]`` even when Sonar returned real TAM/SAM inputs.
    """
    if not isinstance(opus_parsed, dict):
        opus_parsed = {}

    base = opus_parsed.get("base_figures") if isinstance(opus_parsed.get("base_figures"), dict) else {}
    if base and _base_figures_usable(base):
        computed = compute_from_base_figures(base, geography=geography, topic=topic)
        computed = _attach_opus_extras(computed, opus_parsed)
        if not metric_value_missing(computed.get("tam")):
            return computed
        # Usable-looking inputs still yielded NOT FOUND — try Perplexity harvest next.

    if any(not metric_value_missing(opus_parsed.get(k)) for k in ("tam", "sam", "som")):
        # Prefer already-populated tam/sam/som only when they are real figures.
        if not metric_value_missing(opus_parsed.get("tam")):
            opus_parsed.setdefault("computed", False)
            return opus_parsed

    if isinstance(sizing_fallback, dict) and sizing_fallback:
        # Prefer harvest from Perplexity sizing JSON (market_size_facts / tam_candidates).
        # Do not treat a pre-built {tam,sam,som} dict as harvest input — that wipes numbers.
        harvest_keys = ("market_size_facts", "tam_candidates", "denominator_facts", "bottom_up_inputs")
        looks_like_harvest = any(isinstance(sizing_fallback.get(k), list) for k in harvest_keys)
        if looks_like_harvest:
            harvested = _base_from_sizing_harvest(sizing_fallback, topic=topic)
            if harvested:
                computed = compute_from_base_figures(harvested, geography=geography, topic=topic)
                computed["computed"] = True
                computed = _attach_opus_extras(computed, opus_parsed)
                if not metric_value_missing(computed.get("tam")):
                    return computed
        elif not metric_value_missing(sizing_fallback.get("tam")):
            # Already a financial block from _fallback_financial_from_sizing — keep it.
            out = dict(sizing_fallback)
            out.setdefault("computed", True)
            return _attach_opus_extras(out, opus_parsed)

    if base:
        # Last resort: return Opus-derived NOT FOUND block with commentary attached.
        computed = compute_from_base_figures(base, geography=geography, topic=topic)
        return _attach_opus_extras(computed, opus_parsed)

    return opus_parsed


def _base_from_sizing_harvest(parsed_sizing: dict[str, Any], *, topic: str) -> dict[str, Any]:
    refs: list[dict[str, Any]] = []
    industry: dict[str, Any] = {}
    buyers: dict[str, Any] = {}
    arpu: dict[str, Any] = {}

    for fact in parsed_sizing.get("market_size_facts") or []:
        if not isinstance(fact, dict):
            continue
        metric = str(fact.get("metric") or "").lower()
        row = {
            "value": str(fact.get("value") or ""),
            "source_url": str(fact.get("source_url") or ""),
            "source_name": str(fact.get("source_name") or ""),
            "notes": str(fact.get("notes") or ""),
            "scope": str(fact.get("geography_scope") or "domestic"),
        }
        if "tam" in metric or "market" in metric or "revenue" in metric:
            refs.append({**row, "metric": fact.get("metric")})
        elif "industry" in metric or "category" in metric:
            industry = row

    for cand in parsed_sizing.get("tam_candidates") or []:
        if isinstance(cand, dict):
            refs.append(cand)

    for fact in parsed_sizing.get("denominator_facts") or []:
        if not isinstance(fact, dict):
            continue
        metric = str(fact.get("metric") or "").lower()
        row = {
            "value": str(fact.get("value") or ""),
            "source_url": str(fact.get("source_url") or ""),
            "notes": str(fact.get("notes") or ""),
        }
        if any(k in metric for k in ("buyer", "household", "customer", "user", "smb", "company")):
            buyers = row
        elif "arpu" in metric or "acv" in metric or "price" in metric or "spend" in metric:
            arpu = row

    for inp in parsed_sizing.get("bottom_up_inputs") or []:
        if not isinstance(inp, dict):
            continue
        metric = str(inp.get("metric") or "").lower()
        row = {
            "value": str(inp.get("value") or ""),
            "source_url": str(inp.get("source_url") or ""),
            "notes": str(inp.get("notes") or ""),
        }
        if "buyer" in metric or "count" in metric:
            buyers = buyers or row
        elif "arpu" in metric or "acv" in metric or "price" in metric:
            arpu = arpu or row

    if not industry and refs:
        _, best = _pick_tam_from_candidates(refs, topic)
        if best:
            industry = {
                "value": best.get("value", ""),
                "source_url": best.get("source_url", ""),
                "source_name": best.get("source_name", ""),
                "notes": best.get("notes", ""),
            }

    if not refs and not industry and not buyers:
        return {}

    return {
        "industry_revenue": industry,
        "niche_slice_pct": {"value_pct": 100, "label": "ESTIMATE", "notes": "Full category — refine in Opus pass"},
        "buyer_count": buyers,
        "addressable_pct": {"value_pct": 100, "label": "ESTIMATE", "notes": "All sourced buyers"},
        "arpu_annual": arpu,
        "geo_filter_pct": {"value_pct": 100, "label": "DERIVED", "notes": "Geography filter from report market"},
        "segment_filter_pct": {"value_pct": 100, "label": "ESTIMATE", "notes": "Segment filter — Opus should refine"},
        "product_fit_pct": {"value_pct": 100, "label": "ESTIMATE", "notes": "Product-fit filter — Opus should refine"},
        "som_capture_pct": {"value_pct": 4, "label": "ESTIMATE", "notes": "Default 4% SAM capture (3–5 year planning)"},
        "published_reference": refs,
    }
