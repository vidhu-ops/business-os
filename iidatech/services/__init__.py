"""Service-layer entry points for IIDATECH."""
from iidatech.services.customer_report_service import generate_customer_report
from iidatech.services.report_engine import generate_report
from iidatech.services.report_api import run_report_api
from iidatech.services.business_context import build_business_context_object
from iidatech.services.business_blueprint import build_deterministic_business_blueprint, merge_blueprint_to_legacy_plan
from iidatech.services.business_strategy_audit import run_business_strategist_audit
from iidatech.services.execution_blueprint import build_execution_blueprint
from iidatech.services.gtm_engine import build_gtm_channel_economics, build_gtm_engine
__all__ = ["generate_report", "run_report_api", "generate_customer_report", "build_business_context_object", "build_deterministic_business_blueprint", "merge_blueprint_to_legacy_plan", "run_business_strategist_audit", "build_execution_blueprint", "build_gtm_channel_economics", "build_gtm_engine"]