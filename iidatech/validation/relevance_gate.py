"""Canonical topic relevance gate for report-visible / verified evidence records."""
from __future__ import annotations

from typing import Any, Callable

_DEFAULT_MIN_CONFIDENCE = 0.38
_GENERAL_MARKET_MIN_CONFIDENCE = 0.0

_CLASSIFY_TOPIC_DOMAIN: Callable[..., str] | None = None
_RECORD_DOMAIN_CONFIDENCE: Callable[..., float] | None = None


def register_domain_helpers(
    classify_topic_domain: Callable[..., str],
    record_domain_confidence: Callable[..., float],
) -> None:
    """Register app domain helpers without importing app.py (avoids Streamlit UI re-exec)."""
    global _CLASSIFY_TOPIC_DOMAIN, _RECORD_DOMAIN_CONFIDENCE
    _CLASSIFY_TOPIC_DOMAIN = classify_topic_domain
    _RECORD_DOMAIN_CONFIDENCE = record_domain_confidence


def _domain_helpers():
    if callable(_CLASSIFY_TOPIC_DOMAIN) and callable(_RECORD_DOMAIN_CONFIDENCE):
        return _CLASSIFY_TOPIC_DOMAIN, _RECORD_DOMAIN_CONFIDENCE

    import sys

    for mod_name in ("__main__", "app"):
        app_mod = sys.modules.get(mod_name)
        if app_mod is None:
            continue
        mod_dict = getattr(app_mod, "__dict__", {})
        classify_fn = mod_dict.get("classify_topic_domain")
        confidence_fn = mod_dict.get("record_domain_confidence")
        if callable(classify_fn) and callable(confidence_fn):
            register_domain_helpers(classify_fn, confidence_fn)
            return classify_fn, confidence_fn

    raise RuntimeError(
        "classify_topic_domain/record_domain_confidence are unavailable. "
        "Import app.py once before calling is_record_relevant_to_report, and never "
        "import app during an active Streamlit UI session."
    )


def _min_confidence_for_domain(domain: str) -> float:
    if domain == "general_market":
        return _GENERAL_MARKET_MIN_CONFIDENCE
    return _DEFAULT_MIN_CONFIDENCE


def is_record_relevant_to_report(
    record: dict[str, Any],
    topic: str,
    industry: str,
    domain: str,
) -> tuple[bool, str]:
    """Return whether a record is topic-relevant for report output / verified labeling.

  Domain resolution always uses classify_topic_domain(topic, industry) — never
  verification_layer.infer_domain(). The caller-supplied domain is checked for
  drift logging only; gating uses the classified report domain.
    """
    if not isinstance(record, dict) or not record:
        return False, "invalid_record"

    classify_topic_domain, record_domain_confidence = _domain_helpers()
    report_domain = classify_topic_domain(topic, industry)
    caller_domain = str(domain or "").strip()
    if caller_domain and caller_domain != report_domain:
        domain_note = f"classified_domain={report_domain};caller_domain={caller_domain}"
    else:
        domain_note = f"domain={report_domain}"

    try:
        from iidatech.validation.competitor_relevance import (
            is_placeholder_competitor_record,
            record_has_out_of_domain_automotive_signal,
        )

        if is_placeholder_competitor_record(record):
            return False, f"placeholder_competitor_pricing;{domain_note}"
        if record_has_out_of_domain_automotive_signal(
            record,
            domain=report_domain,
            topic=topic,
            industry=industry,
        ):
            return False, f"automotive_contamination;{domain_note}"
    except Exception:
        pass

    confidence = record_domain_confidence(record, report_domain, topic, industry)
    threshold = _min_confidence_for_domain(report_domain)
    if confidence < threshold:
        return (
            False,
            f"domain_confidence_below_threshold:{confidence:.3f}<{threshold:.3f};{domain_note}",
        )

    return True, f"ok;domain_confidence={confidence:.3f};{domain_note}"
