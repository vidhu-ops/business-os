"""Single customer-facing report entrypoint."""
from __future__ import annotations

from typing import Any


def generate_customer_report(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Firewall -> truth_arbiter -> compiler -> guard -> render."""
    from iidatech.validation.v3_render_guard import guard_v3_render

    data = payload if isinstance(payload, dict) else {}
    result = guard_v3_render(data)
    if isinstance(result.get("payload"), dict):
        data.update(result["payload"])
    data["report_v3"] = result.get("v3")
    data["report_v3_markdown"] = result.get("markdown") or ""
    from iidatech.ui.plain_render import prepend_degradation_banner

    data["report_v3_markdown"] = prepend_degradation_banner(data["report_v3_markdown"], data)
    data["v3_guard"] = {
        "blocked": result.get("blocked"),
        "confidence": result.get("confidence"),
        "firewall": result.get("firewall"),
        "integrity": result.get("integrity"),
    }
    return result