"""Diligence preset panel (Streamlit) — extracted from app.py phase 1."""
from __future__ import annotations

import streamlit as st

from iidatech.ui.plain_render import render_plain_value, sanitize_report_text

def render_preset_info(topic_brief: dict, model: dict, completeness: dict, diligence_pack: dict):
    """Collapse all pre-report model, source, and diligence material into one panel."""
    strict_pack = diligence_pack.get("strict_verification_pack", {}) or {}
    funding = diligence_pack.get("funding_readiness_pack", {}) or {}
    readiness = diligence_pack.get("readiness", {}) or {}
    executive_metrics = model.get("executive_metrics") or []
    strict_headline = strict_pack.get("headline_display", {}) or {}
    strict_rules = strict_pack.get("display_rules", {}) or {}
    show_model_figures_as_final = bool(strict_rules.get("show_tam_sam_som_as_verified"))
    show_model_figures_as_estimated = bool(strict_rules.get("show_tam_sam_som_as_estimated"))
    show_model_figures = show_model_figures_as_final or show_model_figures_as_estimated

    with st.expander("Preset info", expanded=False):
        st.caption(
            "Source gates, model assumptions, funding checks, pricing packs, compliance notes, and trend evidence. "
            "Open only when you want to inspect the research setup before the report sections."
        )
        if diligence_pack.get("report_degraded"):
            reason = (
                diligence_pack.get("degradation_reason")
                or diligence_pack.get("report_degrade_reason")
                or "unknown"
            )
            st.warning(
                f"⚠ This report was generated with a partial data failure and may be incomplete. "
                f"Reason: {reason}"
            )

        st.markdown("### Topic Intelligence Brief")
        for key, value in (topic_brief or {}).items():
            st.markdown(f"#### {key}")
            st.markdown(sanitize_report_text(str(value)))

        st.markdown("### Executive Modeling Dashboard")
        st.caption(
            f"{model.get('industry_model_name', 'Market model')} | "
            f"Mode: {model.get('dashboard_mode', 'unknown')} | Domain: {model.get('domain', 'general')}"
        )
        if strict_headline:
            cols = st.columns(5)
            headline_rows = [
                ("Base TAM", strict_headline.get("base_tam", "WITHHELD")),
                ("TAM Range", strict_headline.get("tam_range", "WITHHELD")),
                ("SAM", strict_headline.get("sam", "WITHHELD")),
                ("SOM Range", strict_headline.get("som_range", "WITHHELD")),
                ("Forecast CAGR", strict_headline.get("forecast_cagr", "WITHHELD")),
            ]
            for idx, (label, value) in enumerate(headline_rows):
                cols[idx].metric(label, value)
            if show_model_figures_as_estimated and not show_model_figures_as_final:
                st.caption("Figures are planning estimates until strict verification promotes them to hard figures.")
            else:
                st.caption("Figures are shown only when the strict source gate allows them.")
        elif executive_metrics:
            cols = st.columns(min(4, len(executive_metrics)))
            for idx, metric in enumerate(executive_metrics[:4]):
                cols[idx % len(cols)].metric(metric.get("label", "Metric"), metric.get("value", "n/a"))
        else:
            h = model.get("headline", {})
            cols = st.columns(4)
            cols[0].metric("Base TAM", h.get("tam_base_fmt", "n/a"))
            cols[1].metric("SAM", h.get("sam_fmt", "n/a"))
            cols[2].metric("SOM Range", h.get("som_range", "n/a"))
            cols[3].metric("Forecast CAGR", h.get("forecast_cagr_2026_2031_fmt", "n/a"))
        st.caption(
            f"Evidence completeness: {completeness.get('score', 'n/a')}/100 "
            f"({completeness.get('interpretation', 'unknown')}) | "
            f"{completeness.get('record_count', 'n/a')} records across "
            f"{completeness.get('source_families', 'n/a')} source families"
        )
        if model.get("forecast_rows") and show_model_figures:
            st.markdown("#### Evidence / Forecast")
            st.table(model.get("forecast_rows", [])[:12])
        elif executive_metrics:
            st.markdown("#### Executive Evidence Metrics")
            st.table([
                {
                    "Metric": m.get("label", ""),
                    "Value": m.get("value", ""),
                    "Source": m.get("source", ""),
                    "Confidence": m.get("confidence", ""),
                    "Use / Limitation": m.get("note", ""),
                }
                for m in executive_metrics
            ])
        if model.get("scenario_rows"):
            st.markdown("#### Scenarios")
            st.table(model.get("scenario_rows", [])[:12])
        if model.get("formula_rows"):
            st.markdown("#### Formulas")
            st.table(model.get("formula_rows", [])[:12])
        if model.get("driver_rows") or model.get("workload_rows") or model.get("sensitivity_rows"):
            st.markdown("#### Drivers / Unit Economics")
            if model.get("driver_rows"):
                st.table(model.get("driver_rows", [])[:12])
            if model.get("workload_rows") and show_model_figures:
                st.table(model.get("workload_rows", [])[:12])
            if model.get("sensitivity_rows") and show_model_figures:
                st.table(model.get("sensitivity_rows", [])[:12])
            if not show_model_figures:
                st.caption("Unit economics and sensitivity outputs stay hidden from final figures until source gates pass.")
        if model.get("source_gate_rows") or model.get("regional_rows") or model.get("vendor_capture_rows"):
            st.markdown("#### Source Gates")
            if model.get("source_gate_rows"):
                st.table(model.get("source_gate_rows", [])[:12])
            if model.get("regional_rows"):
                st.markdown("Regional model")
                st.table(model.get("regional_rows", [])[:12])
            if model.get("vendor_capture_rows"):
                st.markdown("Vendor capture model")
                st.table(model.get("vendor_capture_rows", [])[:12])

        st.markdown("### Investment Diligence Layer")
        cols = st.columns(4)
        cols[0].metric("Diligence Score", f"{readiness.get('score', 'n/a')}/100")
        cols[1].metric("Readiness", readiness.get("classification", "n/a"))
        cols[2].metric("A-grade Sources", sum(1 for item in diligence_pack.get("citation_ledger", []) if item.get("grade") == "A"))
        cols[3].metric("Funding Gate", funding.get("status_label", "not checked"))
        if readiness.get("investment_grade_warning"):
            st.caption(readiness.get("investment_grade_warning"))
        if funding:
            st.caption(f"Funding readiness: {funding.get('score_100', 'n/a')}/100. {funding.get('funding_memo', '')}")

        st.markdown("#### Strict Verification Gate (10 checks)")
        render_plain_value({
            "summary": strict_pack.get("summary", ""),
            "counts": strict_pack.get("counts", {}),
            "claim_gates": strict_pack.get("claim_gates", {}),
            "numeric_audit_table": (strict_pack.get("numeric_audit_table", []) or [])[:12],
        })
        st.markdown("#### Funding Readiness Gate And Figure Audit")
        render_plain_value({
            "decision_support": funding.get("decision_support", {}),
            "gates": funding.get("gates", []),
            "figure_audit_table": (funding.get("figure_audit_table", []) or [])[:20],
            "must_fix_to_be_funding_ready": funding.get("must_fix_to_be_funding_ready", []),
        })
        preset_sections = [
            ("Published Survey And Practitioner Evidence", diligence_pack.get("survey_interview_findings", {})),
            ("Operational Financial Model", diligence_pack.get("operational_financial_model", {})),
            ("Bottom-Up Market Calculation", diligence_pack.get("bottom_up_market_calculation", {})),
            ("Pricing Intelligence And Package Structure", diligence_pack.get("pricing_intelligence_pack", {})),
            ("Stored 2026 Financial Model Bank Record", diligence_pack.get("stored_2026_financial_model", {})),
            ("Figure Validation And Data Quality", diligence_pack.get("figure_validation_pack", {})),
            ("Financial Cross-Checks", diligence_pack.get("financial_validation_pack", {})),
            ("Regional Depth Plan", diligence_pack.get("regional_depth_plan", {})),
            ("Funding, Multiples, Investor Thesis", {
                "recent_funding_rounds": diligence_pack.get("recent_funding_rounds", {}),
                "comparable_company_multiples": diligence_pack.get("comparable_company_multiples", {}),
                "pricing_intelligence_pack": diligence_pack.get("pricing_intelligence_pack", {}),
                "investor_thesis_map": diligence_pack.get("investor_thesis_map", {}),
            }),
            ("Compliance, Certification, Case Studies", {
                "country_law_standards": diligence_pack.get("country_law_standards", {}),
                "certification_timeline_costs": diligence_pack.get("certification_timeline_costs", {}),
                "compliance_case_studies": diligence_pack.get("compliance_case_studies", {}),
            }),
            ("Behavior, Retention, Trends", {
                "survey_interview_findings": diligence_pack.get("survey_interview_findings", {}),
                "trend_and_technology_evidence": diligence_pack.get("trend_and_technology_evidence", {}),
                "scenario_forecast_pack": diligence_pack.get("scenario_forecast_pack", {}),
                "digital_behavior_retention": diligence_pack.get("digital_behavior_retention", {}),
            }),
        ]
        for title, value in preset_sections:
            st.markdown(f"#### {title}")
            render_plain_value(value)

        st.markdown("### Citation, Benchmark, Valuation, Forecast")
        if diligence_pack.get("citation_ledger"):
            st.markdown("#### Citation Ledger")
            st.table(diligence_pack.get("citation_ledger", [])[:15])
        if diligence_pack.get("competitive_benchmark"):
            st.markdown("#### Competitive Benchmark")
            st.table(diligence_pack.get("competitive_benchmark", []))
        st.markdown("#### Valuation Support")
        render_plain_value(diligence_pack.get("valuation_support", {}))
        st.markdown("#### Forecast Basis")
        render_plain_value(diligence_pack.get("financial_forecast_basis", {}))
