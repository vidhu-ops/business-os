"""Report renderers for IIDATECH research outputs."""
from iidatech.renderers.research_report_renderer import render_structured_research_report
from iidatech.services.customer_report_service import generate_customer_report

__all__ = [
    "render_structured_research_report",
    "generate_customer_report",
]


def apply_v3_guard_to_payload(payload):  # noqa: ANN001
    from iidatech.validation.v3_render_guard import apply_v3_guard_to_payload as _fn

    return _fn(payload)


def guard_v3_render(payload):  # noqa: ANN001
    from iidatech.validation.v3_render_guard import guard_v3_render as _fn

    return _fn(payload)


__all__ += ["apply_v3_guard_to_payload", "guard_v3_render"]
