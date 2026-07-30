"""Headless report orchestration for IIDATECH.

Provides a stable service API over existing ``app.py`` report logic so QA scripts
and backend workers do not need to import Streamlit UI code directly.

Business logic remains in ``app.py``; this module only coordinates calls and
normalizes responses.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import sys
import time
import traceback
import types
from pathlib import Path
from typing import Any

from iidatech.models.report_config import ReportRunConfig
from iidatech.models.report_modes import (
    funding_ready_mode_for_report_mode,
    normalize_report_mode,
    section_ids_for_mode,
)
from iidatech.models.report_payload import (
    ReportCheckpointInfo,
    ReportCorePayload,
    ReportPayload,
    build_report_metadata,
    classify_payload_gaps,
    extract_sources_from_raw,
    load_checkpoint_info,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SUPPORTED_REPORT_TYPES = frozenset(
    {"research", "institutional", "business_intelligence", "bi", "business"}
)

_REPORT_TYPE_ALIASES = {
    "bi": "business_intelligence",
    "business": "business_intelligence",
}


from iidatech.ui.streamlit_adapter import HeadlessSessionState, HeadlessStreamlitAdapter, ReportEngineAbort


class ReportEngineError(Exception):
    """Raised when the report engine cannot load or run the legacy app module."""


# Legacy aliases for internal callers
_SessionState = HeadlessSessionState
_StreamlitPlaceholder = HeadlessStreamlitAdapter
_STREAMLIT_PATCHED = False
_APP_MODULE: Any | None = None
_HEADLESS_STREAMLIT_MODULE: Any | None = None


def _noop_streamlit_control(*_args: Any, **_kwargs: Any) -> None:
    return None


def _streamlit_cache_decorator(*_args: Any, **_kwargs: Any) -> Any:
    def _wrap(fn: Any) -> Any:
        return fn

    if _args and callable(_args[0]):
        return _args[0]
    return _wrap


class _HeadlessStreamlitSecrets:
    def get(self, key: str, default: Any = "") -> Any:
        return os.environ.get(str(key), default)


class _HeadlessStreamlitQueryParams:
    def get(self, key: str, default: Any = None) -> Any:
        return default


class _HeadlessStreamlitComponentsV1:
    @staticmethod
    def html(*_args: Any, **_kwargs: Any) -> None:
        return None

    @staticmethod
    def iframe(*_args: Any, **_kwargs: Any) -> None:
        return None


class _HeadlessStreamlitComponentsModule(types.ModuleType):
    def __init__(self) -> None:
        super().__init__("streamlit.components")
        self.v1 = _HeadlessStreamlitComponentsV1()


class _HeadlessStreamlitModule(types.ModuleType):
    """Minimal ``streamlit`` package shim for headless legacy imports."""

    def __init__(self, adapter: HeadlessStreamlitAdapter) -> None:
        super().__init__("streamlit")
        self._adapter = adapter
        self.session_state = adapter.session_state
        self.secrets = _HeadlessStreamlitSecrets()
        self.query_params = _HeadlessStreamlitQueryParams()
        self.components = _HeadlessStreamlitComponentsModule()
        self.cache_data = _streamlit_cache_decorator
        self.cache_resource = _streamlit_cache_decorator
        self.stop = _noop_streamlit_control
        self.rerun = _noop_streamlit_control

    def rebind(self, adapter: HeadlessStreamlitAdapter) -> None:
        self._adapter = adapter
        self.session_state = adapter.session_state
        self.stop = adapter.stop
        self.rerun = adapter.rerun

    def __getattr__(self, name: str) -> Any:
        return getattr(self._adapter, name)


def _install_headless_streamlit_shim() -> _HeadlessStreamlitModule:
    global _HEADLESS_STREAMLIT_MODULE
    adapter = HeadlessStreamlitAdapter()
    streamlit_mod = _HeadlessStreamlitModule(adapter)
    components_mod = streamlit_mod.components
    components_v1_mod = components_mod.v1

    sys.modules["streamlit"] = streamlit_mod
    sys.modules["streamlit.components"] = components_mod
    sys.modules["streamlit.components.v1"] = components_v1_mod
    _HEADLESS_STREAMLIT_MODULE = streamlit_mod
    return streamlit_mod


def _patch_streamlit_module() -> None:
    global _STREAMLIT_PATCHED
    if _STREAMLIT_PATCHED:
        return
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    try:
        import streamlit as st
    except ImportError:
        _install_headless_streamlit_shim()
        _STREAMLIT_PATCHED = True
        return

    st.stop = _noop_streamlit_control
    st.rerun = _noop_streamlit_control
    _STREAMLIT_PATCHED = True


def _load_app_module(*, quiet: bool = True) -> Any:
    global _APP_MODULE
    if _APP_MODULE is not None:
        return _APP_MODULE
    if "app" in sys.modules:
        _APP_MODULE = sys.modules["app"]
        return _APP_MODULE

    _patch_streamlit_module()
    try:
        if quiet:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                try:
                    import streamlit_app as app_module
                except ImportError:
                    import app as app_module  # type: ignore[no-redef]
        else:
            try:
                import streamlit_app as app_module
            except ImportError:
                import app as app_module  # type: ignore[no-redef]
    except Exception as exc:
        raise ReportEngineError(f"failed to import streamlit_app.py: {exc}") from exc

    if not hasattr(app_module, "generate_business_build_plan"):
        raise ReportEngineError("streamlit_app.py did not expose generate_business_build_plan")

    _APP_MODULE = app_module
    return app_module


def _normalize_report_type(report_type: str) -> str:
    normalized = str(report_type or "research").strip().lower()
    normalized = _REPORT_TYPE_ALIASES.get(normalized, normalized)
    if normalized not in SUPPORTED_REPORT_TYPES:
        raise ValueError(
            f"Unsupported report_type={report_type!r}. "
            f"Use one of: research, institutional, business_intelligence."
        )
    return normalized


def _coerce_section_range(value: Any, default: tuple[int, int], total_sections: int) -> tuple[int, int]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        start, end = int(value[0]), int(value[1])
    elif isinstance(value, dict) and {"start", "end"} <= set(value):
        start, end = int(value["start"]), int(value["end"])
    else:
        start, end = default
    start = max(1, min(start, total_sections))
    end = max(start, min(end, total_sections))
    return start, end


def _profile_for_report_type(report_type: str, options: dict[str, Any], app: Any) -> dict[str, Any]:
    total_sections = int(getattr(app, "TOTAL_SECTIONS", 33) or 33)
    options = options or {}
    report_mode = normalize_report_mode(options.get("report_mode") or options.get("iidatech_report_mode"))
    mode_ids = section_ids_for_mode(report_mode)
    mode_range = (min(mode_ids), max(mode_ids)) if mode_ids else (1, min(3, total_sections))

    if report_type == "business_intelligence":
        return {
            "mode": "business_intelligence",
            "section_range": None,
            "enable_final_audit": False,
            "enable_claude_section_audit": False,
            "use_report_memory": bool(options.get("use_report_memory", False)),
            "use_cloud_synthesis": bool(options.get("use_cloud_synthesis", True)),
            "enable_auto_topic_research": bool(options.get("enable_auto_topic_research", True)),
        }

    if report_type == "institutional":
        default_range = mode_range if options.get("report_mode") or options.get("iidatech_report_mode") else (1, 6)
        return {
            "mode": "institutional",
            "section_range": _coerce_section_range(options.get("section_range"), default_range, total_sections),
            "report_mode": report_mode,
            "enable_final_audit": bool(options.get("enable_final_audit", report_mode == "institutional")),
            "enable_claude_section_audit": bool(options.get("enable_claude_section_audit", report_mode == "institutional")),
            "use_report_memory": bool(options.get("use_report_memory", False)),
            "use_cloud_synthesis": bool(options.get("use_cloud_synthesis", True)),
            "enable_auto_topic_research": bool(options.get("enable_auto_topic_research", True)),
            "funding_ready_mode": bool(options.get("funding_ready_mode", funding_ready_mode_for_report_mode(report_mode))),
            "iidatech_v2_section_engine": bool(options.get("iidatech_v2_section_engine", True)),
            "anthropic_section_limit": int(options.get("anthropic_section_limit", len(mode_ids) if mode_ids else total_sections)),
        }

    # research
    default_range = mode_range if options.get("report_mode") or options.get("iidatech_report_mode") else (1, 6)
    return {
        "mode": "research",
        "section_range": _coerce_section_range(options.get("section_range"), default_range, total_sections),
        "report_mode": report_mode,
        "enable_final_audit": bool(options.get("enable_final_audit", False)),
        "enable_claude_section_audit": bool(options.get("enable_claude_section_audit", False)),
        "use_report_memory": bool(options.get("use_report_memory", False)),
        "use_cloud_synthesis": bool(options.get("use_cloud_synthesis", True)),
        "enable_auto_topic_research": bool(options.get("enable_auto_topic_research", True)),
        "funding_ready_mode": bool(options.get("funding_ready_mode", False)),
    }


def _bind_headless_streamlit(app: Any, session_state: _SessionState) -> _StreamlitPlaceholder:
    placeholder = _StreamlitPlaceholder(session_state)
    app.st = placeholder
    headless_mod = _HEADLESS_STREAMLIT_MODULE
    if isinstance(headless_mod, _HeadlessStreamlitModule):
        headless_mod.rebind(placeholder)
        return placeholder
    try:
        import streamlit

        streamlit.st = placeholder  # type: ignore[attr-defined]
    except Exception:
        pass
    return placeholder


def _apply_config_to_legacy_app(
    app_module: Any,
    config: ReportRunConfig,
    *,
    timer_placeholder: Any | None = None,
) -> None:
    """Map explicit config onto legacy ``app`` module globals (non-breaking shim)."""
    scope_assessment = config.scope_assessment
    if scope_assessment is None and hasattr(app_module, "assess_topic_scope"):
        scope_assessment = app_module.assess_topic_scope(
            config.topic,
            config.industry,
            config.target,
        )

    bindings = config.legacy_global_bindings()
    placeholder = config.timer_placeholder or timer_placeholder or _StreamlitPlaceholder()
    bindings["timer_placeholder"] = placeholder
    bindings["scope_assessment"] = scope_assessment or {
        "ok": True,
        "issues": [],
        "suggestions": [],
    }

    for global_name, value in bindings.items():
        setattr(app_module, global_name, value)
    report_mode = normalize_report_mode(getattr(config, "report_mode", None) or getattr(app_module, "IIDATECH_REPORT_MODE", None))
    setattr(app_module, "IIDATECH_REPORT_MODE", report_mode)
    setattr(app_module, "FUNDING_READY_REPORT_MODE", bool(config.funding_ready_report_mode))


def _apply_session_state_defaults(
    session_state: _SessionState,
    config: ReportRunConfig,
    options: dict[str, Any],
) -> None:
    """Session keys used by run_report_generation but outside ReportRunConfig."""
    session_state.setdefault("workspace_topic", config.topic)
    session_state.setdefault("workspace_industry", config.industry)
    session_state.setdefault("workspace_country", config.target)
    session_state.setdefault(
        "business_application_purpose",
        options.get("application_purpose", "General market research"),
    )
    session_state.setdefault("founder_workflow_choice_value", config.workflow_choice)
    if options.get("report_mode"):
        session_state["iidatech_report_mode"] = options["report_mode"]
    session_state.setdefault("opportunity_workspace_upload_contexts", options.get("upload_contexts", []))


def _apply_supplementary_legacy_globals(app_module: Any, session_state: _SessionState) -> None:
    """Globals adjacent to report runs that are not part of the 39-name contract."""
    setattr(app_module, "scope_type", "Project")
    setattr(app_module, "database_mode_label", "Project workspace")
    setattr(app_module, "run_btn", False)
    setattr(app_module, "show_commercial_workspace", False)
    setattr(app_module, "workspace_uploads", [])
    setattr(app_module, "workspace_upload_contexts", session_state.get("opportunity_workspace_upload_contexts", []))
    setattr(app_module, "checkpoint_is_current", False)


def _configure_app_run_context(
    app: Any,
    *,
    query: str,
    industry: str,
    geography: str,
    profile: dict[str, Any],
    options: dict[str, Any],
    session_state: _SessionState,
) -> ReportRunConfig:
    config = ReportRunConfig.from_service_options(
        app,
        query=query,
        industry=industry,
        geography=geography,
        profile=profile,
        options=options,
    )
    _apply_session_state_defaults(session_state, config, options)
    _apply_config_to_legacy_app(app, config, timer_placeholder=_StreamlitPlaceholder())
    _apply_supplementary_legacy_globals(app, session_state)
    return config


def _report_payload_from_raw(
    app_module: Any,
    raw: dict[str, Any],
    *,
    session_state: Any | None = None,
) -> ReportPayload:
    """Build ``ReportPayload`` from a legacy report dict (return value or session)."""
    core = ReportCorePayload.from_raw(raw)
    state = session_state or getattr(getattr(app_module, "st", None), "session_state", None)
    checkpoints = load_checkpoint_info(state, app_module) if state is not None else ReportCheckpointInfo()
    missing, unstable = classify_payload_gaps(core, checkpoints)

    model = core.quantitative_model if isinstance(core.quantitative_model, dict) else {}
    completeness = core.evidence_completeness if isinstance(core.evidence_completeness, dict) else {}
    audit = dict(core.final_report_audit)

    report_markdown = _payload_to_markdown(app_module, raw)
    report_html = ""
    market_by_market_markdown = ""
    if hasattr(app_module, "report_to_html"):
        try:
            report_html = app_module.report_to_html(raw, model, completeness)
        except Exception:
            report_html = ""
    if audit and hasattr(app_module, "build_market_by_market_report"):
        try:
            market_by_market_markdown = app_module.build_market_by_market_report(raw, audit)
        except Exception:
            market_by_market_markdown = ""

    return ReportPayload(
        report_markdown=report_markdown,
        report_html=report_html,
        market_by_market_markdown=market_by_market_markdown,
        metadata=build_report_metadata(core),
        sources=extract_sources_from_raw(raw),
        audit=audit,
        checkpoints=checkpoints,
        quality_scores=dict(checkpoints.quality_scores),
        core=core,
        raw=dict(raw),
        missing_fields=missing,
        unstable_fields=unstable,
    )


def _extract_report_payload_from_session(app_module: Any) -> ReportPayload | None:
    """Build explicit ``ReportPayload`` from legacy session state after a report run."""
    session_state = getattr(getattr(app_module, "st", None), "session_state", None)
    if session_state is None:
        return None

    raw = session_state.get("last_iidatech_report")
    if not isinstance(raw, dict):
        return None

    return _report_payload_from_raw(app_module, raw, session_state=session_state)


def _extract_sources_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return extract_sources_from_raw(payload)


def _payload_to_markdown(app: Any, payload: dict[str, Any]) -> str:
    model = payload.get("quantitative_model") if isinstance(payload.get("quantitative_model"), dict) else {}
    completeness = payload.get("evidence_completeness") if isinstance(payload.get("evidence_completeness"), dict) else {}
    if hasattr(app, "report_to_markdown"):
        try:
            return app.report_to_markdown(payload, model, completeness)
        except Exception:
            pass
    return json.dumps(payload, indent=2, ensure_ascii=False, default=str)


def _minimal_founder_plan_markdown(plan: dict[str, Any], query: str) -> str:
    """Readable fallback when founder markdown conversion fails."""
    lines = [f"# Business Plan: {query or 'Your venture'}", ""]
    sections: list[tuple[str, Any]] = [
        ("Executive Summary", plan.get("executive_summary")),
        ("Market Analysis", plan.get("market_analysis")),
        ("Customer & Positioning", plan.get("customer_and_positioning")),
        ("Go-to-Market", plan.get("go_to_market")),
        ("Financial Outlook", plan.get("financial_outlook")),
        ("Risks & Mitigations", plan.get("risks_and_mitigations")),
    ]
    wrote = False
    for title, block in sections:
        if isinstance(block, str) and block.strip():
            lines += [f"## {title}", block.strip(), ""]
            wrote = True
        elif isinstance(block, dict):
            chunk: list[str] = []
            for key, value in block.items():
                if isinstance(value, str) and value.strip():
                    label = str(key).replace("_", " ").strip().title()
                    chunk.append(f"**{label}:** {value.strip()}")
                elif isinstance(value, list) and value and all(isinstance(v, str) for v in value[:6]):
                    label = str(key).replace("_", " ").strip().title()
                    chunk.append(f"**{label}**")
                    chunk.extend(f"- {item}" for item in value[:8])
            if chunk:
                lines += [f"## {title}", *chunk, ""]
                wrote = True
    if not wrote:
        lines += [
            "## Your plan is being prepared",
            "",
            "We generated your business plan but could not format every section for display.",
            "Try running the plan again, or open Employee OS to continue from your research.",
            "",
        ]
    return "\n".join(lines)


def _generate_business_intelligence_report(
    app: Any,
    *,
    query: str,
    industry: str,
    geography: str,
    options: dict[str, Any],
    placeholder: _StreamlitPlaceholder,
) -> dict[str, Any]:
    evidence_items = list(options.get("evidence_items") or [])
    report_context = options.get("report_context")
    application_purpose = options.get("application_purpose")

    plan = app.generate_business_build_plan(
        query,
        industry,
        geography,
        evidence_items,
        report_context,
        application_purpose=application_purpose,
    )
    founder_plan = None
    markdown = ""
    if bool(options.get("founder_readable", True)) and hasattr(app, "build_founder_readable_business_plan"):
        founder_plan = app.build_founder_readable_business_plan(
            plan,
            query,
            industry,
            geography,
            evidence_items,
            report_context,
        )
        if hasattr(app, "founder_business_plan_to_markdown"):
            markdown = app.founder_business_plan_to_markdown(founder_plan)
    if not markdown:
        markdown = _minimal_founder_plan_markdown(plan if isinstance(plan, dict) else {}, query)

    payload = {
        "topic": query,
        "industry": industry,
        "geography": geography,
        "business_plan": plan,
        "founder_readable_plan": founder_plan,
    }
    sources = _extract_sources_from_payload(plan if isinstance(plan, dict) else {})
    return {
        "success": True,
        "report": markdown,
        "metadata": {
            "report_type": "business_intelligence",
            "generation_route": (plan or {}).get("_generation_route") if isinstance(plan, dict) else None,
            "warnings": list(placeholder.warnings),
            "errors": list(placeholder.errors),
            "payload": payload,
        },
        "sources": sources,
    }


def _production_metadata_contract(payload: dict[str, Any], metadata_extra: dict[str, Any] | None = None) -> dict[str, Any]:
    """Stable top-level production fields for QA and API consumers."""
    payload = payload if isinstance(payload, dict) else {}
    extra = metadata_extra if isinstance(metadata_extra, dict) else {}
    audit = extra.get("final_report_audit")
    if not isinstance(audit, dict):
        audit = payload.get("final_report_audit") if isinstance(payload.get("final_report_audit"), dict) else {}
    confidence = extra.get("report_confidence")
    if not isinstance(confidence, dict):
        confidence = payload.get("report_confidence") if isinstance(payload.get("report_confidence"), dict) else {}
    synthesis = extra.get("synthesis_engine")
    if not isinstance(synthesis, dict):
        synthesis = payload.get("synthesis_engine") if isinstance(payload.get("synthesis_engine"), dict) else {}
    score = audit.get("market_style_score")
    funding_ready = audit.get("funding_ready")
    engine = synthesis.get("primary") or "unknown"
    return {
        "score": float(score) if isinstance(score, (int, float)) else None,
        "funding_ready": bool(funding_ready) if funding_ready is not None else None,
        "engine": str(engine),
        "research_confidence": str(confidence.get("research_confidence") or "n/a"),
        "financial_confidence": str(confidence.get("financial_confidence") or "n/a"),
        "investment_confidence": str(confidence.get("investment_confidence") or "n/a"),
    }


def _generate_institutional_or_research_report(
    app: Any,
    *,
    report_type: str,
    query: str,
    industry: str,
    geography: str,
    profile: dict[str, Any],
    options: dict[str, Any],
    placeholder: _StreamlitPlaceholder,
) -> dict[str, Any]:
    if not hasattr(app, "run_report_generation"):
        raise ReportEngineError(
            "app.run_report_generation is unavailable. "
            "Import app.py with headless Streamlit patching before the UI guard."
        )

    started = time.time()
    session_state = placeholder.session_state
    _configure_app_run_context(
        app,
        query=query,
        industry=industry,
        geography=geography,
        profile=profile,
        options=options,
        session_state=session_state,
    )

    run_result = app.run_report_generation()
    if isinstance(run_result, dict):
        extracted = _report_payload_from_raw(app, run_result, session_state=session_state)
    else:
        extracted = _extract_report_payload_from_session(app)
    if extracted is not None and extracted.success:
        payload = extracted.raw
        markdown = extracted.report_markdown
        sources = extracted.sources
        metadata_extra = {
            "final_report_audit": extracted.audit,
            "report_confidence": payload.get("report_confidence"),
            "synthesis_engine": payload.get("synthesis_engine"),
            "quality_scores": extracted.quality_scores,
            "checkpoints": {
                "last_checkpoint_path": extracted.checkpoints.last_checkpoint_path,
                "completed_sections": extracted.checkpoints.completed_sections,
            },
            "missing_fields": extracted.missing_fields,
            "unstable_fields": extracted.unstable_fields,
        }
    else:
        session_state = placeholder.session_state
        payload = session_state.get("last_iidatech_report")
        metadata_extra = {}
        sources = []
        markdown = ""

    if not isinstance(payload, dict):
        payload = getattr(app, "last_iidatech_report", None)
    if not isinstance(payload, dict):
        message = "Report generation finished without a report payload."
        if placeholder.errors:
            message = placeholder.errors[-1]
        failure_meta: dict[str, Any] = {
            "report_type": report_type,
            "warnings": list(placeholder.warnings),
            "errors": list(placeholder.errors) or [message],
            "recoverable_errors": list(placeholder.recoverable_errors),
            "elapsed_seconds": round(time.time() - started, 2),
        }
        if placeholder.last_stop_stack:
            failure_meta["stop_stack"] = placeholder.last_stop_stack
        if placeholder.last_stop_context:
            failure_meta["stop_context"] = placeholder.last_stop_context
        return {
            "success": False,
            "report": "",
            "metadata": failure_meta,
            "sources": [],
        }

    markdown = markdown or _payload_to_markdown(app, payload)
    try:
        from iidatech.ui.plain_render import prepend_degradation_banner

        markdown = prepend_degradation_banner(markdown, payload)
    except Exception:
        pass
    sources = sources or _extract_sources_from_payload(payload)
    sections = payload.get("sections") if isinstance(payload.get("sections"), dict) else {}
    try:
        from iidatech.validation.payload_guard import stamp_payload_identity, validate_payload_integrity

        stamp_payload_identity(payload, source="user")
        integrity = validate_payload_integrity(payload, payload.get("_identity_snapshot"))
        if not integrity.get("ok"):
            placeholder.warnings.append(integrity.get("payload_corruption_error") or "payload_integrity_failed")
    except Exception:
        pass
    production = _production_metadata_contract(payload, metadata_extra)
    intelligence_keys = (
        "sections",
        "research_intelligence",
        "diligence_pack",
        "structured_research_report",
        "quantitative_model",
        "report_v3",
        "report_v3_markdown",
        "report_confidence",
        "final_report_audit",
        "evidence_completeness",
        "synthesis_engine",
    )
    metadata_out = {
        "report_type": report_type,
        "topic": payload.get("topic", query),
        "industry": payload.get("industry", industry),
        "geography": payload.get("geography", geography),
        "section_count": len(sections),
        "evidence_completeness": payload.get("evidence_completeness"),
        **production,
        **metadata_extra,
        "report_mode": payload.get("report_mode") or profile.get("report_mode"),
        "report_degraded": bool(
            payload.get("report_degraded")
            or (payload.get("diligence_pack") or {}).get("report_degraded")
            if isinstance(payload.get("diligence_pack"), dict)
            else payload.get("report_degraded")
        ),
        "report_degrade_reason": (
            payload.get("report_degrade_reason")
            or (payload.get("diligence_pack") or {}).get("report_degrade_reason")
            if isinstance(payload.get("diligence_pack"), dict)
            else payload.get("report_degrade_reason")
        ),
        "degradation_reason": (
            payload.get("degradation_reason")
            or (payload.get("diligence_pack") or {}).get("degradation_reason")
            if isinstance(payload.get("diligence_pack"), dict)
            else payload.get("degradation_reason")
        ),
        "recoverable_errors": list(getattr(placeholder, "recoverable_errors", []) or []),
        "warnings": list(placeholder.warnings),
        "errors": list(placeholder.errors),
        "elapsed_seconds": round(time.time() - started, 2),
    }
    for key in intelligence_keys:
        if key in payload and payload.get(key) is not None:
            metadata_out[key] = payload.get(key)
    return {
        "success": True,
        "report": markdown,
        "payload": payload,
        "metadata": metadata_out,
        "sources": sources,
    }


def generate_report(
    query: str,
    industry: str | None = None,
    geography: str | None = None,
    report_type: str = "research",
    options: dict | None = None,
) -> dict:
    """Generate a report using legacy IIDATECH orchestration in ``app.py``.

    Parameters
    ----------
    query:
        Topic / idea / research question.
    industry:
        Industry label. Defaults to ``General``.
    geography:
        Geography or market scope. Defaults to ``Global``.
    report_type:
        ``research`` (quick sections), ``institutional`` (full report), or
        ``business_intelligence`` (business builder plan).
    options:
        Optional orchestration overrides. Common keys: ``section_range``,
        ``evidence_items``, ``report_context``, ``use_cloud_synthesis``,
        ``enable_auto_topic_research``, ``application_purpose``, ``report_mode``.

    Returns
    -------
    dict
        ``{"success": bool, "report": str, "metadata": dict, "sources": list}``
    """
    options = dict(options or {})
    normalized_type = _normalize_report_type(report_type)
    industry_value = str(industry or options.get("industry") or "General").strip() or "General"
    geography_value = str(geography or options.get("geography") or "Global").strip() or "Global"
    query_value = str(query or "").strip()

    if not query_value:
        return {
            "success": False,
            "report": "",
            "metadata": {"report_type": normalized_type, "errors": ["query is required"]},
            "sources": [],
        }
    if not industry_value:
        return {
            "success": False,
            "report": "",
            "metadata": {"report_type": normalized_type, "errors": ["industry is required"]},
            "sources": [],
        }
    if not geography_value:
        return {
            "success": False,
            "report": "",
            "metadata": {"report_type": normalized_type, "errors": ["geography is required"]},
            "sources": [],
        }

    try:
        app = _load_app_module(quiet=bool(options.get("quiet_import", True)))
        if options.get("manual_preview") or os.getenv("IIDATECH_MANUAL_PREVIEW", "0").strip().lower() in {"1", "true", "yes", "on"}:
            from iidatech.testing.manual_preview import apply_app_llm_mocks, enable_manual_preview

            enable_manual_preview()
            apply_app_llm_mocks(app)
        profile = _profile_for_report_type(normalized_type, options, app)
        session_state = _SessionState()
        placeholder = _bind_headless_streamlit(app, session_state)

        if profile["mode"] == "business_intelligence":
            return _generate_business_intelligence_report(
                app,
                query=query_value,
                industry=industry_value,
                geography=geography_value,
                options=options,
                placeholder=placeholder,
            )

        return _generate_institutional_or_research_report(
            app,
            report_type=normalized_type,
            query=query_value,
            industry=industry_value,
            geography=geography_value,
            profile=profile,
            options=options,
            placeholder=placeholder,
        )
    except ReportEngineAbort as exc:
        return {
            "success": False,
            "report": "",
            "metadata": {
                "report_type": normalized_type,
                "errors": [str(exc)],
                "error_code": getattr(exc, "error_code", "fatal_abort"),
                "recoverable": False,
                "section": None,
                "traceback": traceback.format_exc(limit=12),
                "stop_stack": getattr(exc, "stop_stack", ""),
                "stop_context": getattr(exc, "stop_context", {}),
            },
            "sources": [],
        }
    except ReportEngineError as exc:
        return {
            "success": False,
            "report": "",
            "metadata": {
                "report_type": normalized_type,
                "errors": [str(exc)],
            },
            "sources": [],
        }
    except Exception as exc:
        return {
            "success": False,
            "report": "",
            "metadata": {
                "report_type": normalized_type,
                "errors": [str(exc)],
                "traceback": traceback.format_exc(limit=8),
            },
            "sources": [],
        }


def unresolved_dependencies() -> list[str]:
    """Document optional or external modules still referenced by wrapped app logic."""
    return [
        "pipeline.fetchers.live_fetcher.LiveMultiFetcher (optional V2 upload path)",
        "pipeline.verifier.cross_verifier.CrossVerifier (optional V2 upload path)",
        "ollama local client (optional synthesis route)",
        "Anthropic / DeepSeek API keys (cloud synthesis and audits)",
        "Tavily / Exa / Firecrawl / Xcrael keys (live research enrichment)",
        "ChromaDB + APScheduler (RAG memory via learning_engine)",
    ]


def streamlit_coupling_points() -> list[str]:
    """Places the wrapped legacy orchestration still touches Streamlit."""
    return [
        "app.run_report_generation() uses st.session_state, st.progress, st.status, st.stop",
        "GlobalIntelligenceEngine.synthesis_router() calls st.warning on fallback paths",
        "generate_business_build_plan() reads st.session_state.business_application_purpose",
        "render_* helpers inside run_report_generation (render_source_readiness_preflight, render_section_output)",
        "Headless mode replaces app.st with a placeholder; legacy function bodies are unchanged",
    ]
