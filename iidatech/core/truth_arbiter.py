"""Truth Arbitration Layer -- sole writer of customer-facing IIDATECH truth.

Collects candidates from intelligence engines, scores them, picks winners,
and emits one canonical truth object with full provenance per field.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from iidatech.report_modes import infer_report_mode
from iidatech.validation.competitor_evidence import (
    DEFAULT_COMPETITOR_EVIDENCE_GAPS,
    filter_verified_competitor_matrix,
    filter_verified_pricing_rows,
    is_live_serp_evidence_row,
    is_synthetic_competitor_name,
    is_verified_competitor_row,
    is_verified_pricing_row,
)
from iidatech.validation.payload_guard import validate_payload_integrity

SECTION_BLOCKED = "BLOCKED"
SECTION_PARTIAL = "PARTIAL"
SECTION_VALID = "VALID"
_MIN_TRUTH_SCORE = 60.0
_VALIDATION = "VALIDATION REQUIRED"

_SOURCE_QUALITY: dict[str, float] = {
    "serp": 95.0,
    "serp_intelligence": 95.0,
    "sql_proprietary": 90.0,
    "evidence_bank": 90.0,
    "quantitative_model": 88.0,
    "research_brain": 80.0,
    "research_intelligence": 80.0,
    "unit_economics_grounding": 78.0,
    "gtm_engine": 75.0,
    "execution_blueprint": 72.0,
    "boardroom": 70.0,
    "investment_decision": 70.0,
    "final_report_audit": 68.0,
    "v2_prose": 40.0,
    "v2_section": 40.0,
    "manual_preview": 5.0,
    "business_blueprint": 35.0,
    "preview": 5.0,
}

_SYNTHETIC_SOURCES = frozenset(
    {
        "",
        "preview",
        "synthetic",
        "manual_preview",
        "preview-mock",
        "preview band",
        "estimated",
        "unverified",
        "business_blueprint",
    }
)

_GENERIC_ICP = re.compile(
    r"^(primary buyer|workflow buyer|named buyer|generic buyer|icp\s*[#:]?\s*\d+)",
    re.I,
)
_FAKE_COMPETITOR = re.compile(r"^competitor\s*[#:]?\s*\d+\b", re.I)
_GENERIC_CHANNELS = frozenset(
    {"social media", "digital marketing", "word of mouth", "generic channel", "online ads"}
)


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _num(v: Any) -> float | None:
    if v in (None, "", "WITHHELD", _VALIDATION):
        return None
    if isinstance(v, dict):
        v = v.get("value") or v.get("display")
    try:
        s = str(v).replace(",", "").replace("$", "").replace("%", "").replace("₹", "").strip()
        return float(s)
    except (TypeError, ValueError):
        return None


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _brain(payload: dict) -> dict:
    ri = payload.get("research_intelligence")
    if isinstance(ri, dict) and ri:
        return ri
    return _as_dict(_as_dict(payload.get("diligence_pack")).get("research_intelligence"))


def _source_quality(source: str) -> float:
    key = _norm(source).replace(" ", "_")
    for tier, score in _SOURCE_QUALITY.items():
        if tier in key or key in tier:
            return score
    if "serp" in key:
        return 95.0
    if "research" in key:
        return 80.0
    if "gtm" in key:
        return 75.0
    if "boardroom" in key or "investment" in key:
        return 70.0
    if "preview" in key or "manual" in key:
        return 5.0
    if "blueprint" in key:
        return 35.0
    return 50.0


def _provenance_field(
    value: Any,
    *,
    source: str,
    truth_score: float,
    verified: bool,
    evidence_count: int = 0,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    block: dict[str, Any] = {
        "value": value,
        "source": source,
        "confidence": round(min(0.99, max(0.0, truth_score / 100.0)), 2),
        "verified": verified,
        "evidence_count": evidence_count,
        "truth_score": round(truth_score, 1),
    }
    if extra:
        block.update(extra)
    return block


def _candidate(
    field: str,
    value: Any,
    source: str,
    *,
    evidence_count: int = 1,
    recency: float = 0.7,
    plausibility: float = 1.0,
    agreement: float = 0.5,
    verified: bool = False,
    reject_reason: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    sq = _source_quality(source)
    score = (
        0.30 * sq
        + 0.25 * min(100.0, evidence_count * 20.0)
        + 0.20 * (recency * 100.0)
        + 0.15 * (plausibility * 100.0)
        + 0.10 * (agreement * 100.0)
    )
    if reject_reason:
        score = 0.0
    return {
        "field": field,
        "value": value,
        "source": source,
        "source_quality": sq,
        "evidence_count": evidence_count,
        "recency": recency,
        "plausibility": plausibility,
        "agreement": agreement,
        "verified": verified,
        "truth_score": round(score, 1),
        "reject_reason": reject_reason,
        "extra": extra or {},
    }


def score_truth_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score and sort candidates (scores already computed; re-rank)."""
    scored = []
    for c in candidates:
        if c.get("reject_reason"):
            c = {**c, "truth_score": 0.0}
        scored.append(c)
    scored.sort(key=lambda x: float(x.get("truth_score") or 0), reverse=True)
    return scored


def pick_best_truth(candidates: list[dict[str, Any]], *, min_score: float = _MIN_TRUTH_SCORE) -> dict[str, Any] | None:
    """Pick highest-scoring candidate above threshold."""
    ranked = score_truth_candidates(candidates)
    for c in ranked:
        score = float(c.get("truth_score") or 0)
        if score >= min_score and not c.get("reject_reason"):
            return c
    return None


def _is_generic_icp(name: str, topic: str = "") -> bool:
    n = str(name or "").strip()
    if not n:
        return True
    if _GENERIC_ICP.match(n):
        return True
    if re.match(r"^icp\s+\d+\s*:", n, re.I):
        return True
    if topic and _norm(n) == _norm(topic):
        return True
    return False


def _reject_competitor_row(row: dict) -> str | None:
    name = str(row.get("name") or row.get("competitor") or "").strip()
    if not name:
        return "empty_name"
    if is_synthetic_competitor_name(name) or _FAKE_COMPETITOR.match(name):
        return "synthetic_name"
    if is_live_serp_evidence_row(row):
        return None
    source = str(row.get("source") or row.get("source_url") or row.get("url") or row.get("official_url") or "")
    if source.lower() in _SYNTHETIC_SOURCES or source.lower().startswith("preview"):
        return "synthetic_source"
    if not is_verified_competitor_row(row):
        price = row.get("price") or row.get("pricing") or row.get("price_band")
        if price in (None, "", "unknown", "WITHHELD") and not source:
            return "no_source_or_pricing"
    return None


def _serp_structured_records(payload: dict) -> list[dict]:
    out: list[dict] = []
    diligence = _as_dict(payload.get("diligence_pack"))
    for key in ("serp_intelligence", "evidence_bank", "evidence_harvest"):
        block = _as_dict(payload.get(key) if key != "serp_intelligence" else (payload.get(key) or diligence.get(key)))
        out.extend(_as_list(block.get("structured_records")))
        out.extend(_as_list(block.get("entities")))
    trace = _as_dict(payload.get("evidence_bank_trace"))
    if trace.get("structured_records"):
        out.extend(_as_list(trace.get("structured_records")))
    for row in _as_list(payload.get("evidence_rows")):
        if isinstance(row, dict) and str(row.get("record_type") or "").lower() in {"competitor", "pricing", "buyer_voice", "buyer_pain"}:
            out.append(row)
    return out


def collect_candidate_truths(payload: dict[str, Any] | None) -> dict[str, list[dict[str, Any]]]:
    """Collect truth candidates from all intelligence sources (read-only)."""
    payload = payload if isinstance(payload, dict) else {}
    brain = _brain(payload)
    snapshot = _as_dict(payload.get("_identity_snapshot"))
    diligence = _as_dict(payload.get("diligence_pack"))
    qmodel = _as_dict(payload.get("quantitative_model"))
    blueprint = payload.get("business_blueprint") if isinstance(payload.get("business_blueprint"), dict) else {}
    topic = str(payload.get("topic") or snapshot.get("topic") or "")

    candidates: dict[str, list[dict[str, Any]]] = {
        "identity": [],
        "competitors": [],
        "pricing": [],
        "customer": [],
        "market_sizes": [],
        "economics": [],
        "gtm": [],
        "execution": [],
        "investment": [],
    }

    # IDENTITY -- user input primary
    identity_val = {
        "topic": str(payload.get("topic") or snapshot.get("topic") or ""),
        "industry": str(payload.get("industry") or snapshot.get("industry") or ""),
        "geography": str(payload.get("target") or payload.get("geography") or snapshot.get("geography") or ""),
        "report_mode": infer_report_mode(
            topic,
            payload.get("report_mode"),
            workflow_choice=str(payload.get("workflow_choice") or ""),
        ),
    }
    candidates["identity"].append(
        _candidate("identity", identity_val, "user_input", evidence_count=3, recency=1.0, plausibility=1.0, agreement=1.0, verified=True)
    )
    if snapshot:
        snap_val = {**identity_val, "topic": str(snapshot.get("topic") or identity_val["topic"])}
        candidates["identity"].append(
            _candidate("identity", snap_val, "identity_stamp", evidence_count=2, recency=0.95, verified=True)
        )

    # COMPETITORS -- serp primary, research brain fallback
    seen_comp: set[str] = set()
    for row in _serp_structured_records(payload):
        if str(row.get("record_type") or "").lower() != "competitor":
            continue
        name = str(row.get("name") or row.get("company_name") or "").strip()
        if not name:
            continue
        key = _norm(name)
        if key in seen_comp:
            continue
        seen_comp.add(key)
        reject = _reject_competitor_row(
            {
                "name": name,
                "source": row.get("source_url") or row.get("url"),
                "price": row.get("price") or row.get("pricing"),
                "trust_score": row.get("trust_score"),
                "evidence_backed": row.get("verification_status") != "unverified",
                "verification_status": row.get("verification_status"),
            }
        )
        candidates["competitors"].append(
            _candidate(
                "competitor_row",
                {
                    "name": name,
                    "positioning": row.get("positioning") or "",
                    "pricing": row.get("price") or row.get("pricing"),
                    "source": row.get("source_url") or row.get("url"),
                    "trust_score": row.get("trust_score"),
                },
                "serp_intelligence",
                evidence_count=int(row.get("mention_frequency") or 1),
                recency=0.85,
                verified=reject is None,
                reject_reason=reject,
            )
        )

    comp = _as_dict(brain.get("competitor_map"))
    for row in filter_verified_competitor_matrix(_as_list(comp.get("competitor_matrix"))):
        name = str(row.get("name") or row.get("competitor") or "").strip()
        key = _norm(name)
        if key in seen_comp:
            continue
        seen_comp.add(key)
        reject = _reject_competitor_row(row)
        candidates["competitors"].append(
            _candidate(
                "competitor_row",
                {
                    "name": name,
                    "positioning": row.get("positioning") or row.get("plan") or "",
                    "pricing": row.get("price") or row.get("pricing") or row.get("price_band"),
                    "source": row.get("source") or row.get("url"),
                    "trust_score": row.get("trust_score"),
                },
                "research_brain",
                evidence_count=2,
                recency=0.75,
                verified=reject is None,
                reject_reason=reject,
            )
        )

    for row in _as_list(_as_dict(diligence.get("competitor_intelligence_pack")).get("competitors")):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or "").strip()
        key = _norm(name)
        if not name or key in seen_comp:
            continue
        seen_comp.add(key)
        reject = _reject_competitor_row(row)
        candidates["competitors"].append(
            _candidate(
                "competitor_row",
                {
                    "name": name,
                    "positioning": row.get("positioning") or "",
                    "pricing": row.get("pricing") or row.get("pricing_model") or "",
                    "source": row.get("official_url") or row.get("url") or "",
                    "trust_score": row.get("trust_score"),
                },
                "serp_live_discovery",
                evidence_count=2,
                recency=0.9,
                verified=reject is None,
                reject_reason=reject,
            )
        )

    # PRICING -- serp shopping primary
    for row in _serp_structured_records(payload):
        rtype = str(row.get("record_type") or "").lower()
        if rtype not in {"pricing", "competitor"}:
            continue
        price = row.get("price") or row.get("pricing")
        if price in (None, "", "unknown"):
            continue
        source = str(row.get("source_url") or row.get("url") or "")
        reject = None
        if source.lower() in _SYNTHETIC_SOURCES:
            reject = "synthetic_source"
        candidates["pricing"].append(
            _candidate(
                "pricing_row",
                {
                    "competitor": row.get("name") or row.get("company_name"),
                    "price": price,
                    "source": source,
                    "verification_status": row.get("verification_status") or "live_serp",
                },
                "serp_intelligence",
                evidence_count=2,
                recency=0.9,
                verified=reject is None or is_live_serp_evidence_row(row),
                reject_reason=reject,
            )
        )

    for row in _serp_structured_records(payload):
        if str(row.get("record_type") or "").lower() != "market_signal":
            continue
        metric = str(row.get("metric") or row.get("snippet") or "").strip()
        if not metric:
            continue
        candidates["market_sizes"].append(
            _candidate(
                "tam_hint",
                {
                    "value": metric,
                    "formula": "serp_proxy_hint",
                    "source": row.get("source_url") or "",
                },
                "serp_intelligence",
                evidence_count=1,
                recency=0.85,
                verified=False,
                reject_reason="proxy_not_verified",
            )
        )

    for row in filter_verified_pricing_rows(_as_list(comp.get("competitor_matrix"))):
        reject = None if is_verified_pricing_row(row) else "unverified_pricing"
        candidates["pricing"].append(
            _candidate(
                "pricing_row",
                {
                    "competitor": row.get("name") or row.get("competitor"),
                    "price": row.get("price") or row.get("pricing") or row.get("price_band"),
                    "source": row.get("source"),
                },
                "research_brain",
                evidence_count=2,
                recency=0.7,
                verified=reject is None,
                reject_reason=reject,
            )
        )

    bands = comp.get("pricing_bands")
    if isinstance(bands, dict) and any(_num(v) is not None for v in bands.values()):
        src = str(comp.get("pricing_source") or "research_brain")
        reject = "synthetic_bands" if src.lower() in _SYNTHETIC_SOURCES else None
        candidates["pricing"].append(
            _candidate("pricing_bands", bands, src, evidence_count=1, recency=0.6, reject_reason=reject)
        )

    # CUSTOMER -- buyer voice primary
    for row in _serp_structured_records(payload):
        if str(row.get("record_type") or "").lower() not in {"buyer_voice", "buyer_pain"}:
            continue
        name = str(row.get("name") or row.get("segment") or row.get("category") or "buyer signal").strip()
        reject = "generic_icp" if _is_generic_icp(name, topic) else None
        candidates["customer"].append(
            _candidate(
                "icp_profile",
                {
                    "name": name,
                    "pain": row.get("complaints") or row.get("pain") or row.get("review_text"),
                    "wtp": row.get("wtp_signals"),
                    "source": row.get("source_url"),
                },
                "serp_intelligence",
                evidence_count=2,
                recency=0.85,
                verified=reject is None,
                reject_reason=reject,
            )
        )

    cust = _as_dict(brain.get("customer_truth"))
    survey = _as_dict(diligence.get("survey_interview_findings"))
    for row in (
        _as_list(survey.get("icp_profiles"))
        + _as_list(survey.get("buyer_profiles"))
        + _as_list(cust.get("icp_profiles"))
        + _as_list(cust.get("buyer_personas"))
    ):
        if not isinstance(row, dict):
            continue
        name = str(row.get("name") or row.get("named_buyer_profile") or row.get("segment") or "").strip()
        reject = "generic_icp" if _is_generic_icp(name, topic) else None
        candidates["customer"].append(
            _candidate(
                "icp_profile",
                {
                    "name": name,
                    "pain": row.get("pain") or row.get("primary_pain"),
                    "trigger": row.get("buyer_trigger") or row.get("trigger"),
                    "wtp": row.get("willingness_to_pay") or row.get("wtp"),
                },
                "research_brain",
                evidence_count=2,
                recency=0.7,
                verified=reject is None,
                reject_reason=reject,
            )
        )

    for pain in _as_list(cust.get("top_pains")):
        if not isinstance(pain, dict):
            continue
        cat = str(pain.get("category") or pain.get("theme") or "").strip()
        if not cat:
            continue
        candidates["customer"].append(
            _candidate(
                "ranked_pain",
                {"category": cat, "evidence": pain.get("sample") or pain.get("evidence") or pain.get("pain")},
                "research_brain",
                evidence_count=int(pain.get("frequency") or 1),
                recency=0.65,
                verified=True,
            )
        )

    # MARKET SIZES -- quantitative model primary
    headline = _as_dict(qmodel.get("headline"))
    fin = _as_dict(brain.get("financial_truth"))
    for key in ("tam", "sam", "som"):
        qval = headline.get(f"{key}_base") or qmodel.get(key)
        formula = headline.get("methodology") or _as_dict(fin.get(key)).get("formula") or _as_dict(fin.get(key)).get("method")
        reject = None
        if qval in (None, "", "WITHHELD"):
            reject = "missing_value"
        elif not formula and not qmodel.get("evidence_backed"):
            reject = "no_formula"
        candidates["market_sizes"].append(
            _candidate(
                key,
                {"value": qval, "formula": formula},
                "quantitative_model",
                evidence_count=3 if formula else 1,
                recency=0.8,
                verified=reject is None,
                reject_reason=reject,
            )
        )
        # research brain fallback
        block = _as_dict(fin.get(key))
        rval = block.get("value") or block.get(key)
        if rval not in (None, "", "WITHHELD"):
            rreject = None if block.get("evidence_backed") or block.get("computed") else "unverified"
            candidates["market_sizes"].append(
                _candidate(
                    key,
                    {"value": rval, "formula": block.get("formula") or block.get("method")},
                    "research_brain",
                    evidence_count=2,
                    recency=0.7,
                    verified=rreject is None,
                    reject_reason=rreject,
                )
            )

    # ECONOMICS -- GTM engine primary (via grounded research), blueprint rejected
    ue = _as_dict(fin.get("unit_economics"))
    grounding = _as_dict(payload.get("unit_economics_grounding"))
    blueprint_ue = _as_dict(_as_dict(blueprint.get("unit_economics")))
    for key, src_key in (
        ("cac", "cac"),
        ("ltv", "ltv"),
        ("arpu", "arpu"),
        ("gross_margin", "margin"),
        ("payback_months", "payback_months"),
        ("burn_multiple", "burn_multiple"),
    ):
        val = ue.get(src_key) if ue else None
        if val in (None, "", "WITHHELD") and grounding:
            val = grounding.get(key) or grounding.get(src_key)
        reject = None
        n = _num(val)
        if n is None:
            reject = "missing"
        elif key == "cac" and n <= 0:
            reject = "cac_non_positive"
        elif key == "arpu" and n <= 0:
            reject = "arpu_non_positive"
        elif key == "ltv" and n <= 0:
            reject = "ltv_non_positive"
        elif key == "payback_months" and n < 1:
            reject = "payback_too_low"
        if ue.get("evidence_backed") or grounding.get("evidence_backed"):
            src = "gtm_engine" if key in {"cac", "ltv", "arpu"} else "research_brain"
            candidates["economics"].append(
                _candidate(key, n, src, evidence_count=3, recency=0.75, verified=reject is None, reject_reason=reject)
            )
        elif n is not None:
            candidates["economics"].append(
                _candidate(key, n, "research_brain", evidence_count=1, recency=0.5, verified=False, reject_reason=reject or "unverified")
            )
        # blueprint candidate always rejected for customer path
        bval = blueprint_ue.get(key) or blueprint_ue.get(src_key)
        if bval not in (None, "", "WITHHELD"):
            candidates["economics"].append(
                _candidate(key, _num(bval), "business_blueprint", evidence_count=0, recency=0.3, reject_reason="blueprint_not_customer_source")
            )

    # GTM
    strat = _as_dict(brain.get("strategic_recommendations"))
    for ch in _as_list(strat.get("launch_strategy")) or _as_list(strat.get("gtm")):
        if isinstance(ch, str) and ch.strip():
            reject = "generic_channel" if _norm(ch) in _GENERIC_CHANNELS else None
            candidates["gtm"].append(
                _candidate("channel", ch.strip(), "research_brain", evidence_count=1, recency=0.7, reject_reason=reject)
            )
    exec_bp = payload.get("execution_blueprint") if isinstance(payload.get("execution_blueprint"), dict) else {}
    if exec_bp:
        candidates["gtm"].append(
            _candidate("execution_blueprint", exec_bp, "execution_blueprint", evidence_count=2, recency=0.65, verified=True)
        )

    # EXECUTION
    first_rev = _as_list(strat.get("first_revenue_path")) or _as_list(strat.get("fast_revenue_path"))
    if first_rev:
        candidates["execution"].append(
            _candidate("first_revenue_path", first_rev, "research_brain", evidence_count=2, recency=0.7, verified=True)
        )

    # INVESTMENT -- boardroom primary
    inv = _as_dict(payload.get("investment_decision"))
    audit = _as_dict(payload.get("final_report_audit"))
    verdict = inv.get("verdict") or inv.get("investment_verdict")
    if verdict:
        ev_count = len(_as_list(inv.get("rationale"))) + len(_as_list(diligence.get("citation_ledger")))
        reject = "unsupported_confidence" if ev_count < 1 and not brain.get("confidence_score") else None
        candidates["investment"].append(
            _candidate(
                "verdict",
                {
                    "verdict": str(verdict).upper(),
                    "investment_score": inv.get("investment_score"),
                    "rationale": _as_list(inv.get("rationale")),
                    "risks": _as_list(inv.get("risks")),
                },
                "boardroom",
                evidence_count=max(1, ev_count),
                recency=0.8,
                verified=reject is None,
                reject_reason=reject,
            )
        )
    if audit.get("market_style_score") is not None:
        candidates["investment"].append(
            _candidate(
                "audit_score",
                audit.get("market_style_score") or audit.get("report_score"),
                "final_report_audit",
                evidence_count=1,
                recency=0.6,
                verified=True,
            )
        )

    return candidates


def _plausibility_market_sizes(size_picks: dict[str, dict]) -> list[str]:
    violations: list[str] = []
    tam = _num(size_picks.get("tam", {}).get("value"))
    sam = _num(size_picks.get("sam", {}).get("value"))
    som = _num(size_picks.get("som", {}).get("value"))
    if tam and sam and sam > tam:
        violations.append("sam_exceeds_tam")
    if sam and som and som > sam:
        violations.append("som_exceeds_sam")
    if tam and som and som > tam:
        violations.append("som_exceeds_tam")
    return violations


def _plausibility_economics(metrics: dict[str, dict]) -> list[str]:
    violations: list[str] = []
    cac = _num(metrics.get("cac", {}).get("value"))
    ltv = _num(metrics.get("ltv", {}).get("value"))
    if cac is not None and cac <= 0:
        violations.append("invalid_cac")
    if ltv is not None and ltv <= 0:
        violations.append("invalid_ltv")
    if cac and ltv and cac > 0 and (ltv / cac) > 20:
        if not metrics.get("ltv", {}).get("verified"):
            violations.append("ltv_cac_ratio_unsupported")
    return violations


def build_canonical_truth_object(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Arbitrate all candidates into one canonical customer-facing truth object."""
    payload = payload if isinstance(payload, dict) else {}
    raw = collect_candidate_truths(payload)
    snapshot = _as_dict(payload.get("_identity_snapshot"))
    integrity = validate_payload_integrity(payload, snapshot)

    # IDENTITY -- reject drift; stamped snapshot wins when integrity fails
    if not integrity.get("ok", True) and snapshot:
        topic_snap = str(snapshot.get("topic") or "")
        identity = {
            "topic": topic_snap,
            "industry": str(snapshot.get("industry") or ""),
            "geography": str(snapshot.get("geography") or snapshot.get("target") or ""),
            "report_mode": infer_report_mode(
                topic_snap,
                payload.get("report_mode"),
                workflow_choice=str(payload.get("workflow_choice") or ""),
            ),
        }
        identity_valid = False
    else:
        id_pick = pick_best_truth(raw["identity"]) or (raw["identity"][0] if raw["identity"] else None)
        identity = id_pick["value"] if id_pick else {"topic": "", "industry": "", "geography": "", "report_mode": "research"}
        identity_valid = integrity.get("ok", True) and bool(str(identity.get("topic") or "").strip())

    # COMPETITORS
    comp_rows: list[dict] = []
    seen: set[str] = set()
    for c in score_truth_candidates(raw["competitors"]):
        if float(c.get("truth_score") or 0) < _MIN_TRUTH_SCORE or c.get("reject_reason"):
            continue
        row = c["value"]
        key = _norm(row.get("name"))
        if key in seen:
            continue
        seen.add(key)
        comp_rows.append(
            _provenance_field(
                row,
                source=c["source"],
                truth_score=float(c["truth_score"]),
                verified=bool(c.get("verified")),
                evidence_count=int(c.get("evidence_count") or 0),
            )
        )
    comp_status = SECTION_VALID if comp_rows else SECTION_BLOCKED

    # PRICING
    price_rows: list[dict] = []
    price_bands: dict = {}
    for c in score_truth_candidates(raw["pricing"]):
        if float(c.get("truth_score") or 0) < _MIN_TRUTH_SCORE or c.get("reject_reason"):
            continue
        if c["field"] == "pricing_bands":
            price_bands = c["value"]
        elif c["field"] == "pricing_row":
            price_rows.append(
                _provenance_field(
                    c["value"],
                    source=c["source"],
                    truth_score=float(c["truth_score"]),
                    verified=bool(c.get("verified")),
                    evidence_count=int(c.get("evidence_count") or 0),
                )
            )
    price_status = SECTION_VALID if price_rows else (SECTION_PARTIAL if price_bands else SECTION_BLOCKED)

    # CUSTOMER
    icps: list[dict] = []
    pains: list[dict] = []
    for c in score_truth_candidates(raw["customer"]):
        if float(c.get("truth_score") or 0) < _MIN_TRUTH_SCORE or c.get("reject_reason"):
            continue
        if c["field"] == "icp_profile" and len(icps) < 3:
            icps.append(
                _provenance_field(
                    c["value"],
                    source=c["source"],
                    truth_score=float(c["truth_score"]),
                    verified=bool(c.get("verified")),
                    evidence_count=int(c.get("evidence_count") or 0),
                )
            )
        elif c["field"] == "ranked_pain" and len(pains) < 8:
            pains.append(
                _provenance_field(
                    c["value"],
                    source=c["source"],
                    truth_score=float(c["truth_score"]),
                    verified=True,
                    evidence_count=int(c.get("evidence_count") or 0),
                )
            )
    cust_status = SECTION_VALID if icps or pains else SECTION_BLOCKED

    # MARKET SIZES
    size_picks: dict[str, dict] = {}
    try:
        from iidatech.validation.consumer_trust import strict_metric_withheld
    except ImportError:
        def strict_metric_withheld(_payload: dict, _key: str) -> bool:
            return False

    for key in ("tam", "sam", "som"):
        if strict_metric_withheld(payload, key):
            size_picks[key] = _provenance_field(
                None,
                source="strict_verification_pack",
                truth_score=0.0,
                verified=False,
                evidence_count=0,
                extra={"withheld": True, "formula": None},
            )
            continue
        field_candidates = [c for c in raw["market_sizes"] if c["field"] == key]
        best = pick_best_truth(field_candidates)
        if best:
            val_block = best["value"]
            n = _num(val_block.get("value") if isinstance(val_block, dict) else val_block)
            size_picks[key] = _provenance_field(
                n,
                source=best["source"],
                truth_score=float(best["truth_score"]),
                verified=bool(best.get("verified")),
                evidence_count=int(best.get("evidence_count") or 0),
                extra={"formula": val_block.get("formula") if isinstance(val_block, dict) else None},
            )
    market_violations = _plausibility_market_sizes(size_picks)
    for v in market_violations:
        for k in ("sam", "som"):
            if k in size_picks and v.startswith(k[:3]):
                size_picks.pop(k, None)
    tam_hints = [
        c
        for c in score_truth_candidates(raw["market_sizes"])
        if c.get("field") == "tam_hint" and float(c.get("truth_score") or 0) >= _MIN_TRUTH_SCORE
    ]
    market_status = SECTION_VALID if (
        size_picks.get("tam") and _num(_as_dict(size_picks.get("tam")).get("value")) is not None
    ) else (
        SECTION_PARTIAL if tam_hints else SECTION_BLOCKED
    )

    # ECONOMICS
    econ_metrics: dict[str, dict] = {}
    for key in ("cac", "ltv", "arpu", "gross_margin", "payback_months", "burn_multiple"):
        field_candidates = [c for c in raw["economics"] if c["field"] == key]
        best = pick_best_truth(field_candidates)
        if best:
            econ_metrics[key] = _provenance_field(
                best["value"],
                source=best["source"],
                truth_score=float(best["truth_score"]),
                verified=bool(best.get("verified")),
                evidence_count=int(best.get("evidence_count") or 0),
            )
    econ_violations = _plausibility_economics(econ_metrics)
    for v in econ_violations:
        if v == "invalid_cac":
            econ_metrics.pop("cac", None)
        if v == "invalid_ltv":
            econ_metrics.pop("ltv", None)
    econ_status = SECTION_VALID if econ_metrics.get("cac") and econ_metrics.get("ltv") else (
        SECTION_PARTIAL if econ_metrics else SECTION_BLOCKED
    )

    # GTM (via engine on interim stub)
    gtm_block: dict[str, Any] = {"status": SECTION_BLOCKED, "owner": "gtm_engine"}
    try:
        from iidatech.services.gtm_engine import build_gtm_channel_economics, build_gtm_engine

        stub = {
            "topic": identity.get("topic"),
            "unit_economics": {
                "table": [
                    {"metric": k.upper(), "value": v.get("value")}
                    for k, v in econ_metrics.items()
                ]
            },
        }
        plan = payload.get("business_plan") if isinstance(payload.get("business_plan"), dict) else {}
        eng = build_gtm_engine(stub, plan)
        channels = _as_list(eng.get("acquisition_channels"))
        gtm_block = {
            "status": SECTION_VALID if channels else SECTION_BLOCKED,
            "owner": "gtm_engine",
            "vertical": eng.get("vertical"),
            "acquisition_channels": channels,
            "recommended_launch_sequence": _as_list(eng.get("recommended_launch_sequence")),
            "first_channel": eng.get("first_channel"),
            "scale_channel": eng.get("scale_channel"),
            "channel_economics": build_gtm_channel_economics({**stub, "go_to_market": {"gtm_engine": eng}}),
            "truth_score": 75.0,
        }
    except Exception:
        gtm_block["missing_evidence"] = ["GTM channel validation"]

    # EXECUTION
    exec_pick = pick_best_truth([c for c in raw["execution"] if c["field"] == "first_revenue_path"])
    exec_status = SECTION_VALID if exec_pick else SECTION_BLOCKED
    execution_truth = {
        "status": exec_status,
        "owner": "gtm_engine",
        "first_revenue_path": (exec_pick or {}).get("value") or [],
    }

    # INVESTMENT
    inv_pick = pick_best_truth([c for c in raw["investment"] if c["field"] == "verdict"])
    inv_status = SECTION_VALID if inv_pick else SECTION_BLOCKED
    inv_val = inv_pick["value"] if inv_pick else {}
    investment_truth = {
        "status": inv_status,
        "owner": "boardroom",
        "verdict": _provenance_field(
            inv_val.get("verdict"),
            source="boardroom",
            truth_score=float((inv_pick or {}).get("truth_score") or 0),
            verified=bool((inv_pick or {}).get("verified")),
            evidence_count=int((inv_pick or {}).get("evidence_count") or 0),
        )
        if inv_pick
        else None,
        "rationale": inv_val.get("rationale") or [],
        "risks": inv_val.get("risks") or [],
        "investment_score": inv_val.get("investment_score"),
    }

    blocked_sections: list[str] = []
    missing: list[str] = []
    if not identity_valid:
        blocked_sections.append("identity")
    if comp_status == SECTION_BLOCKED:
        blocked_sections.append("competitors")
        missing.extend(DEFAULT_COMPETITOR_EVIDENCE_GAPS)
    if price_status == SECTION_BLOCKED:
        blocked_sections.append("pricing")
        missing.append("pricing pages")
    if cust_status == SECTION_BLOCKED:
        blocked_sections.append("customer")
        missing.append("buyer interviews / ICP validation")
    if market_status == SECTION_BLOCKED:
        blocked_sections.append("market")
        missing.append("TAM denominator inputs")
    if econ_status == SECTION_BLOCKED:
        blocked_sections.append("economics")
        missing.append("unit economics with cited sources")
    if gtm_block.get("status") == SECTION_BLOCKED:
        blocked_sections.append("gtm")

    confidence = min(
        100,
        30
        + len([s for s in (comp_status, price_status, cust_status, market_status, econ_status) if s == SECTION_VALID]) * 12,
    )

    return {
        "identity": {
            **identity,
            "valid": identity_valid,
            "violations": integrity.get("violations") or [],
        },
        "market_truth": {
            "status": market_status,
            "owner": "quantitative_model",
            "tam": size_picks.get("tam"),
            "sam": size_picks.get("sam"),
            "som": size_picks.get("som"),
            "tam_proxy_hints": [
                _provenance_field(
                    c["value"],
                    source=c["source"],
                    truth_score=float(c["truth_score"]),
                    verified=False,
                    evidence_count=int(c.get("evidence_count") or 0),
                )
                for c in tam_hints[:3]
            ],
            "violations": market_violations,
        },
        "customer_truth": {
            "status": cust_status,
            "owner": "buyer_voice_bank",
            "icps": icps,
            "ranked_pains": pains,
        },
        "competitor_truth": {
            "status": comp_status,
            "owner": "serp_intelligence",
            "matrix": comp_rows,
            "competitor_count": len(comp_rows),
        },
        "pricing_truth": {
            "status": price_status,
            "owner": "serp_intelligence",
            "competitor_pricing_table": price_rows,
            "bands": price_bands,
        },
        "economics_truth": {
            "status": econ_status,
            "owner": "gtm_engine",
            "metrics": econ_metrics,
            "violations": econ_violations,
        },
        "gtm_truth": gtm_block,
        "execution_truth": execution_truth,
        "investment_truth": investment_truth,
        "truth_metadata": {
            "arbiter_version": "1.0",
            "confidence": confidence,
            "missing_evidence": sorted(set(missing)),
            "blocked_sections": blocked_sections,
            "identity_valid": identity_valid,
            "hallucination_flags": [],
            "min_truth_score": _MIN_TRUTH_SCORE,
        },
    }


def should_block_customer_report(
    truth: dict[str, Any],
    *,
    firewall: dict[str, Any] | None = None,
    integrity: dict[str, Any] | None = None,
) -> tuple[bool, list[str]]:
    """Return (blocked, reasons) for Phase 6 blocking conditions."""
    truth = truth if isinstance(truth, dict) else {}
    meta = _as_dict(truth.get("truth_metadata"))
    reasons: list[str] = []

    if not meta.get("identity_valid", True):
        reasons.append("identity_corrupted")
    identity = _as_dict(truth.get("identity"))
    if integrity and not integrity.get("ok", True):
        reasons.append("payload_integrity_failed")
    if identity.get("violations"):
        reasons.extend(identity["violations"])

    fw = firewall or {}
    comp = _as_dict(truth.get("competitor_truth"))
    identity = _as_dict(truth.get("identity"))
    mode = str(identity.get("report_mode") or "research")
    if (
        comp.get("status") == SECTION_BLOCKED
        and int(comp.get("competitor_count") or 0) == 0
        and mode in {"investor_memo", "business_builder"}
    ):
        reasons.append("zero_verified_competitors")
    if int(fw.get("hard_critical_count") or 0) > 0 and comp.get("status") == SECTION_BLOCKED:
        reasons.append("zero_verified_competitors")
    hard_codes = {
        "fake_competitor",
        "generic_competitor_label",
        "circular_icp",
        "circular_icp_topic",
        "impossible_cac",
        "impossible_arpu",
        "suspicious_payback",
        "suspicious_ltv_cac",
        "manual_preview_synthetic",
    }
    issues = [i for i in (_as_list(fw.get("issues")) + _as_list(fw.get("critical"))) if isinstance(i, dict)]
    hard_issues = [i for i in issues if i.get("code") in hard_codes and i.get("severity") == "critical"]
    if len(hard_issues) > 2:
        reasons.append("hallucination_flags_exceeded")

    econ = _as_dict(truth.get("economics_truth"))
    if econ.get("violations"):
        reasons.append("economics_invalid")

    meta["hallucination_flags"] = [str(i.get("code") or i) for i in issues[:12]]
    truth["truth_metadata"] = meta
    return bool(reasons), reasons


def _unwrap_provenance(block: dict[str, Any] | None) -> Any:
    if not isinstance(block, dict):
        return block
    if "value" in block and "source" in block and "truth_score" in block:
        return block.get("value")
    return block


def _unwrap_matrix(rows: list) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        val = row.get("value") if "value" in row and "source" in row else row
        if isinstance(val, dict):
            out.append(val)
        else:
            out.append(row)
    return out


def adapt_arbiter_truth_for_compiler(truth: dict[str, Any] | None) -> dict[str, Any]:
    """Map arbiter canonical truth into report_compiler schema for V3 compile."""
    truth = truth if isinstance(truth, dict) else {}
    identity = _as_dict(truth.get("identity"))
    market = _as_dict(truth.get("market_truth"))
    comp = _as_dict(truth.get("competitor_truth"))
    price = _as_dict(truth.get("pricing_truth"))
    cust = _as_dict(truth.get("customer_truth"))
    econ = _as_dict(truth.get("economics_truth"))
    gtm = _as_dict(truth.get("gtm_truth"))
    execution = _as_dict(truth.get("execution_truth"))
    inv = _as_dict(truth.get("investment_truth"))
    meta = _as_dict(truth.get("truth_metadata"))

    metrics: dict[str, Any] = {}
    for key, block in _as_dict(econ.get("metrics")).items():
        if isinstance(block, dict):
            metrics[key] = {
                "key": key,
                "value": block.get("value"),
                "source": block.get("source"),
                "evidence_backed": block.get("verified"),
                "computed": False,
                "confidence": "high" if block.get("verified") else "medium",
            }

    matrix = _unwrap_matrix(_as_list(comp.get("matrix")))
    icps_raw = _unwrap_matrix(_as_list(cust.get("icps")))
    pains_raw = _unwrap_matrix(_as_list(cust.get("ranked_pains")))
    price_rows = _unwrap_matrix(_as_list(price.get("competitor_pricing_table")))

    sizes = {}
    for k in ("tam", "sam", "som"):
        block = market.get(k)
        if isinstance(block, dict) and block.get("value") is not None:
            sizes[k] = {
                "value": block.get("value"),
                "source": block.get("source"),
                "evidence_backed": block.get("verified"),
                "computed": bool(block.get("formula")),
                "confidence": "high" if block.get("verified") else "medium",
            }

    verdict_block = inv.get("verdict")
    raw_verdict = _unwrap_provenance(verdict_block) if verdict_block else ""
    vkey = str(raw_verdict or "MAYBE").upper().replace(" ", "_")
    customer_decision = {
        "STRONG_YES": "BUILD",
        "CONDITIONAL_YES": "BUILD WITH CONDITIONS",
        "MAYBE": "BUILD WITH CONDITIONS",
        "NO": "DO NOT BUILD",
        "BUILD": "BUILD",
        "AVOID": "DO NOT BUILD",
    }.get(vkey, "BUILD WITH CONDITIONS")

    return {
        "identity": {
            "topic": identity.get("topic"),
            "industry": identity.get("industry"),
            "geography": identity.get("geography"),
            "report_mode": identity.get("report_mode"),
        },
        "market_truth": {
            "status": market.get("status"),
            "owner": market.get("owner"),
            "vertical": identity.get("industry"),
            "market_sizes": sizes,
            "missing_evidence": meta.get("missing_evidence") or [],
        },
        "competitor_truth": {
            "status": comp.get("status"),
            "owner": comp.get("owner"),
            "competitor_count": comp.get("competitor_count", len(matrix)),
            "matrix": matrix,
            "market_leaders": [r.get("name") for r in matrix[:5] if r.get("name")],
            "missing_evidence": list(DEFAULT_COMPETITOR_EVIDENCE_GAPS) if not matrix else [],
        },
        "pricing_truth": {
            "status": price.get("status"),
            "owner": price.get("owner"),
            "bands": price.get("bands") or {},
            "competitor_pricing_table": price_rows,
            "missing_evidence": [] if price_rows else ["pricing pages"],
        },
        "customer_truth": {
            "status": cust.get("status"),
            "owner": cust.get("owner"),
            "icps": icps_raw,
            "ranked_pains": pains_raw,
            "missing_evidence": [] if icps_raw else ["buyer interviews / ICP validation"],
        },
        "numeric_truth": {
            "status": econ.get("status"),
            "owner": econ.get("owner"),
            "metrics": metrics,
            "missing_evidence": meta.get("missing_evidence") or [],
            "impossible_economics": econ.get("violations") or [],
        },
        "gtm_truth": gtm,
        "execution_truth": execution,
        "investment_truth": {
            "status": inv.get("status"),
            "owner": inv.get("owner"),
            "verdict": raw_verdict,
            "customer_decision": customer_decision if raw_verdict else _VALIDATION,
            "rationale": inv.get("rationale") or [],
            "risks": inv.get("risks") or [],
            "investment_score": inv.get("investment_score"),
        },
        "risk_truth": {"status": SECTION_VALID if inv.get("risks") else SECTION_BLOCKED, "risk_map": []},
        "metadata": {
            **meta,
            "arbiter": True,
            "confidence": meta.get("confidence", 0),
        },
        "truth_metadata": meta,
    }
