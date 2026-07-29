"""Explicit configuration for legacy ``app.run_report_generation`` orchestration.

Maps the 39 module-level globals read by ``run_report_generation()`` without
changing that function or removing globals from ``app.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from iidatech.models.report_modes import funding_ready_mode_for_report_mode, normalize_report_mode


# Canonical list of legacy global names consumed by run_report_generation().
LEGACY_RUN_REPORT_GLOBALS: tuple[str, ...] = (
    "topic",
    "industry",
    "target",
    "horizon",
    "depth",
    "section_range",
    "scope_assessment",
    "country_mode",
    "use_report_memory",
    "use_local_ai",
    "use_cloud_synthesis",
    "enable_auto_topic_research",
    "auto_topic_research_limit",
    "FUNDING_READY_REPORT_MODE",
    "ANTHROPIC_KEY",
    "enable_claude_section_audit",
    "enable_final_audit",
    "enable_self_eval",
    "anthropic_section_limit",
    "local_quality_target",
    "local_quality_retries",
    "claude_section_audit_limit",
    "claude_parallel_workers",
    "claude_redo_attempts",
    "checkpoint_candidate",
    "resume_saved_checkpoint",
    "start_fresh_report",
    "show_debug_data",
    "timer_placeholder",
    "workflow_choice",
    "saved_workspace_uploads",
    "TOTAL_SECTIONS",
    "CHECKPOINT_SCHEMA_VERSION",
    "TAVILY_KEY",
    "EXA_KEY",
    "FIRECRAWL_KEY",
    "XCRAWL_KEY",
    "LIVE_RESEARCH_API_BUDGETS",
    "augment_market_model_with_2026_bank",
    "IIDATECH_V2_SECTION_ENGINE",
)


@dataclass
class ReportRunConfig:
    """Explicit replacement for implicit ``app`` globals used during report runs."""

    # --- topic inputs ---
    topic: str = ""
    industry: str = "General"
    target: str = "Global"
    horizon: str = "2026-2031"
    depth: str = "Project"
    section_range: tuple[int, int] = (1, 3)
    report_mode: str = "standard"
    scope_assessment: dict[str, Any] | None = None
    country_mode: bool = True
    workflow_choice: str = "Research a market"

    # --- synthesis settings ---
    use_local_ai: bool = False
    use_cloud_synthesis: bool = True
    anthropic_section_limit: int = 33
    iidatech_v2_section_engine: bool = True
    use_report_memory: bool = False
    funding_ready_report_mode: bool = False

    # --- research settings ---
    enable_auto_topic_research: bool = True
    auto_topic_research_limit: int = 20
    show_debug_data: bool = False

    # --- audit settings ---
    enable_claude_section_audit: bool = False
    enable_final_audit: bool = False
    enable_self_eval: bool = True
    local_quality_target: float = 7.0
    local_quality_retries: int = 1
    claude_section_audit_limit: int = 33
    claude_parallel_workers: int = 3
    claude_redo_attempts: int = 3

    # --- checkpoint settings ---
    checkpoint_candidate: dict[str, Any] | None = None
    resume_saved_checkpoint: bool = False
    start_fresh_report: bool = True
    checkpoint_schema_version: int = 3

    # --- API / module constants ---
    anthropic_key: str = ""
    tavily_key: str = ""
    exa_key: str = ""
    firecrawl_key: str = ""
    xcrawl_key: str = ""
    live_research_api_budgets: dict[str, Any] = field(default_factory=dict)
    total_sections: int = 33
    augment_market_model_with_2026_bank: Any = None

    # --- runtime UI shim (legacy global, not Streamlit state) ---
    timer_placeholder: Any = None
    saved_workspace_uploads: list[Any] = field(default_factory=list)

    def legacy_global_bindings(self) -> dict[str, Any]:
        """Map dataclass fields to exact ``app`` module global names."""
        return {
            "topic": self.topic,
            "industry": self.industry,
            "target": self.target,
            "horizon": self.horizon,
            "depth": self.depth,
            "section_range": self.section_range,
            "report_mode": self.report_mode,
            "scope_assessment": self.scope_assessment,
            "country_mode": self.country_mode,
            "workflow_choice": self.workflow_choice,
            "use_local_ai": self.use_local_ai,
            "use_cloud_synthesis": self.use_cloud_synthesis,
            "anthropic_section_limit": self.anthropic_section_limit,
            "IIDATECH_V2_SECTION_ENGINE": self.iidatech_v2_section_engine,
            "use_report_memory": self.use_report_memory,
            "FUNDING_READY_REPORT_MODE": self.funding_ready_report_mode,
            "enable_auto_topic_research": self.enable_auto_topic_research,
            "auto_topic_research_limit": self.auto_topic_research_limit,
            "show_debug_data": self.show_debug_data,
            "enable_claude_section_audit": self.enable_claude_section_audit,
            "enable_final_audit": self.enable_final_audit,
            "enable_self_eval": self.enable_self_eval,
            "local_quality_target": self.local_quality_target,
            "local_quality_retries": self.local_quality_retries,
            "claude_section_audit_limit": self.claude_section_audit_limit,
            "claude_parallel_workers": self.claude_parallel_workers,
            "claude_redo_attempts": self.claude_redo_attempts,
            "checkpoint_candidate": self.checkpoint_candidate,
            "resume_saved_checkpoint": self.resume_saved_checkpoint,
            "start_fresh_report": self.start_fresh_report,
            "CHECKPOINT_SCHEMA_VERSION": self.checkpoint_schema_version,
            "ANTHROPIC_KEY": self.anthropic_key,
            "TAVILY_KEY": self.tavily_key,
            "EXA_KEY": self.exa_key,
            "FIRECRAWL_KEY": self.firecrawl_key,
            "XCRAWL_KEY": self.xcrawl_key,
            "LIVE_RESEARCH_API_BUDGETS": self.live_research_api_budgets,
            "TOTAL_SECTIONS": self.total_sections,
            "augment_market_model_with_2026_bank": self.augment_market_model_with_2026_bank,
            "timer_placeholder": self.timer_placeholder,
            "saved_workspace_uploads": self.saved_workspace_uploads,
        }

    @classmethod
    def from_service_options(
        cls,
        app_module: Any,
        *,
        query: str,
        industry: str,
        geography: str,
        profile: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> ReportRunConfig:
        """Build config from ``generate_report`` inputs and legacy app defaults."""
        options = dict(options or {})
        total_sections = int(getattr(app_module, "TOTAL_SECTIONS", 33) or 33)
        topic = str(query or "").strip()
        industry_value = str(industry or options.get("industry") or "General").strip() or "General"
        target = str(geography or options.get("geography") or "Global").strip() or "Global"

        section_range = profile.get("section_range")
        if section_range is None:
            section_range = (1, min(3, total_sections)) if profile.get("mode") == "institutional" else (1, min(3, total_sections))

        scope_assessment = options.get("scope_assessment")
        if scope_assessment is None and hasattr(app_module, "assess_topic_scope"):
            scope_assessment = app_module.assess_topic_scope(topic, industry_value, target)

        budgets = getattr(app_module, "LIVE_RESEARCH_API_BUDGETS", None)
        if not isinstance(budgets, dict):
            budgets = {}

        report_mode = normalize_report_mode(profile.get("report_mode") or options.get("report_mode"))

        return cls(
            topic=topic,
            industry=industry_value,
            target=target,
            horizon=str(options.get("horizon") or "2026-2031"),
            depth=str(options.get("depth") or "Project"),
            section_range=tuple(section_range),
            report_mode=report_mode,
            scope_assessment=scope_assessment if isinstance(scope_assessment, dict) else None,
            country_mode=bool(options.get("country_mode", True)),
            workflow_choice=str(options.get("workflow_choice") or "Research a market"),
            use_local_ai=bool(options.get("use_local_ai", False)),
            use_cloud_synthesis=bool(profile.get("use_cloud_synthesis", True)),
            anthropic_section_limit=int(
                options.get("anthropic_section_limit", profile.get("anthropic_section_limit", total_sections))
            ),
            iidatech_v2_section_engine=bool(
                options.get("iidatech_v2_section_engine", profile.get("iidatech_v2_section_engine", True))
            ),
            use_report_memory=bool(profile.get("use_report_memory", False)),
            funding_ready_report_mode=bool(
                profile.get("funding_ready_mode", funding_ready_mode_for_report_mode(report_mode))
            ),
            enable_auto_topic_research=bool(profile.get("enable_auto_topic_research", True)),
            auto_topic_research_limit=int(options.get("auto_topic_research_limit", 20)),
            show_debug_data=bool(options.get("show_debug_data", False)),
            enable_claude_section_audit=bool(profile.get("enable_claude_section_audit", False)),
            enable_final_audit=bool(profile.get("enable_final_audit", False)),
            enable_self_eval=bool(options.get("enable_self_eval", True)),
            local_quality_target=float(options.get("local_quality_target", 7.0)),
            local_quality_retries=int(options.get("local_quality_retries", 1)),
            claude_section_audit_limit=int(
                options.get("claude_section_audit_limit", total_sections)
            ),
            claude_parallel_workers=int(options.get("claude_parallel_workers", 3)),
            claude_redo_attempts=int(options.get("claude_redo_attempts", 3)),
            checkpoint_candidate=options.get("checkpoint_candidate"),
            resume_saved_checkpoint=bool(options.get("resume_saved_checkpoint", False)),
            start_fresh_report=bool(options.get("start_fresh_report", True)),
            checkpoint_schema_version=int(
                getattr(app_module, "CHECKPOINT_SCHEMA_VERSION", 3) or 3
            ),
            anthropic_key=str(getattr(app_module, "ANTHROPIC_KEY", "") or ""),
            tavily_key=str(getattr(app_module, "TAVILY_KEY", "") or ""),
            exa_key=str(getattr(app_module, "EXA_KEY", "") or ""),
            firecrawl_key=str(getattr(app_module, "FIRECRAWL_KEY", "") or ""),
            xcrawl_key=str(getattr(app_module, "XCRAWL_KEY", "") or ""),
            live_research_api_budgets=dict(budgets),
            total_sections=total_sections,
            augment_market_model_with_2026_bank=getattr(
                app_module, "augment_market_model_with_2026_bank", None
            ),
            timer_placeholder=options.get("timer_placeholder"),
            saved_workspace_uploads=list(options.get("saved_workspace_uploads") or []),
        )


# Globals used by run_report_generation adjacency / UI tail but not in the 39-name list.
UNRESOLVED_LEGACY_GLOBALS: tuple[str, ...] = (
    "scope_type",
    "database_mode_label",
    "run_btn",
    "show_commercial_workspace",
    "workspace_uploads",
    "workspace_upload_contexts",
    "checkpoint_is_current",
)

# Streamlit session_state keys read/written during run_report_generation (not module globals).
UNRESOLVED_SESSION_STATE_KEYS: tuple[str, ...] = (
    "business_application_purpose",
    "last_report_checkpoint",
    "last_iidatech_report",
    "opportunity_workspace_upload_contexts",
    "current_opportunity_workspace",
    "current_opportunity_workspace_path",
    "workspace_topic",
    "workspace_industry",
    "workspace_country",
    "founder_workflow_choice_value",
)
