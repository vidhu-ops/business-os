"""Structured truth resolution for V3 reports — deterministic sources over LLM prose."""
from __future__ import annotations

from typing import Any

_VALIDATION = "VALIDATION REQUIRED"

# Higher rank wins on conflict. V2 section prose is last resort only.
SOURCE_RANK: dict[str, int] = {
    "quantitative_model": 100,
    "unit_economics_grounding": 95,
    "research_intelligence": 90,
    "structured_research_report": 85,
    "business_blueprint": 80,
    "final_report_audit": 75,
    "investment_decision": 70,
    "diligence_pack": 65,
    "boardroom_strategist": 20,
    "v2_section_prose": 5,
}

STRUCTURED_SOURCES = frozenset(
    k for k, r in SOURCE_RANK.items() if r >= 65 and k != "v2_section_prose"
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
        return float(str(v).replace(",", "").replace("$", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def metric(
    value: Any,
    *,
    source: str,
    confidence: str = "medium",
    validation_state: str = "validation_required",
    display: str | None = None,
) -> dict[str, Any]:
    if value in (None, "", "WITHHELD"):
        return {
            "value": _VALIDATION,
            "display": _VALIDATION,
            "source": source,
            "confidence": confidence,
            "validation_state": "validation_required",
        }
    if str(value).upper().startswith("WITHHELD"):
        return {
            "value": _VALIDATION,
            "display": str(value),
            "source": source,
            "confidence": "low",
            "validation_state": "withheld",
        }
    disp = display if display is not None else str(value)
    state = validation_state
    if state == "validation_required" and _num(value) is not None:
        state = "estimated" if confidence in {"medium", "benchmark-derived"} else "validated"
    return {
        "value": value,
        "display": disp,
        "source": source,
        "confidence": confidence,
        "validation_state": state,
    }


def metric_display(m: Any) -> str:
    if isinstance(m, dict):
        return str(m.get("display") or m.get("value") or _VALIDATION)
    if m in (None, ""):
        return _VALIDATION
    return str(m)


class ProvenanceTracker:
    def __init__(self) -> None:
        self.structured = 0
        self.prose = 0
        self.total = 0

    def record(self, source: str) -> None:
        self.total += 1
        rank = SOURCE_RANK.get(source, 0)
        if source == "v2_section_prose" or rank <= 20:
            self.prose += 1
        elif rank >= 65:
            self.structured += 1
        else:
            self.prose += 1

    def summary(self) -> dict[str, Any]:
        structured_pct = round(100 * self.structured / self.total, 1) if self.total else 100.0
        prose_pct = round(100 * self.prose / self.total, 1) if self.total else 0.0
        return {
            "field_count": self.total,
            "structured_fields": self.structured,
            "prose_fields": self.prose,
            "structured_source_pct": structured_pct,
            "v2_prose_dependency_pct": prose_pct,
        }


class TruthContext:
    """Primary structured objects for V3 — never V2 section markdown."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload
        self.provenance = ProvenanceTracker()
        self.diligence = _as_dict(payload.get("diligence_pack"))
        self.brain = self._brain()
        self.structured = self._structured()
        self.qmodel = _as_dict(payload.get("quantitative_model"))
        self.grounding = _as_dict(payload.get("unit_economics_grounding"))
        self.blueprint = _as_dict(payload.get("business_blueprint"))
        self.audit = _as_dict(payload.get("final_report_audit"))
        self.investment = _as_dict(payload.get("investment_decision"))
        self.sections = _as_dict(payload.get("sections"))  # appendix only — not read by builders

    def _brain(self) -> dict[str, Any]:
        ri = self.payload.get("research_intelligence")
        if isinstance(ri, dict) and ri:
            return ri
        return _as_dict(self.diligence.get("research_intelligence"))

    def _structured(self) -> dict[str, Any]:
        sr = self.payload.get("structured_research_report")
        if isinstance(sr, dict) and sr:
            return sr
        if isinstance(self.diligence.get("structured_research_report"), dict):
            return _as_dict(self.diligence.get("structured_research_report"))
        nested = _as_dict(self.brain.get("structured_report"))
        return _as_dict(nested.get("payload"))

    def resolve(self, candidates: list[tuple[Any, str, str, str]]) -> dict[str, Any]:
        """Pick highest-ranked non-empty candidate. candidates: (value, source, confidence, validation_state)."""
        best: tuple[Any, str, str, str] | None = None
        best_rank = -1
        conflict = False
        for value, source, confidence, vstate in candidates:
            if value in (None, "", _VALIDATION) or (isinstance(value, str) and value.strip().upper() == "WITHHELD"):
                continue
            rank = SOURCE_RANK.get(source, 0)
            if rank > best_rank:
                if best is not None and _num(best[0]) is not None and _num(value) is not None and _num(best[0]) != _num(value):
                    conflict = True
                best = (value, source, confidence, vstate)
                best_rank = rank
        if best is None:
            self.provenance.record("structured_research_report")
            return metric(None, source="none", confidence="low", validation_state="validation_required")
        value, source, confidence, vstate = best
        if conflict:
            vstate = "conflict_resolved"
            confidence = "medium"
        self.provenance.record(source)
        return metric(value, source=source, confidence=confidence, validation_state=vstate)


def compute_report_truth_confidence(
    ctx: TruthContext,
    *,
    brain_confidence: int,
    audit_score: float | None,
    validated_metrics: int,
    total_metrics: int,
) -> dict[str, Any]:
    prov = ctx.provenance.summary()
    metric_pct = round(100 * validated_metrics / total_metrics, 1) if total_metrics else 0.0
    audit_part = min(100, float(audit_score or 0) * 10) if audit_score is not None else 0
    score = round(
        0.35 * brain_confidence
        + 0.25 * prov["structured_source_pct"]
        + 0.25 * metric_pct
        + 0.15 * audit_part,
        1,
    )
    grade = "high" if score >= 75 else "medium" if score >= 50 else "low"
    return {
        "score": score,
        "grade": grade,
        "brain_confidence": brain_confidence,
        "audit_score": audit_score,
        "validated_metric_pct": metric_pct,
        "structured_source_pct": prov["structured_source_pct"],
        "v2_prose_dependency_pct": prov["v2_prose_dependency_pct"],
        "primary_sources": sorted(STRUCTURED_SOURCES, key=lambda s: -SOURCE_RANK[s])[:6],
    }


def grounding_known(ctx: TruthContext, key: str) -> Any:
    known = _as_dict(ctx.grounding.get("known_values"))
    entry = known.get(key) or known.get(key.lower())
    if isinstance(entry, dict):
        return entry.get("value")
    return entry
