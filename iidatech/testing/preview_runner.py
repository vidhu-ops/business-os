"""Run full product preview (research -> V3 -> business -> employees) without LLM cost."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from iidatech.execution import hire_default_team, infer_business_type, run_agent_company_cycle
from iidatech.validation.v3_render_guard import apply_v3_guard_to_payload
from iidatech.routing.domain_router import route_domain
from iidatech.services.business_blueprint import build_deterministic_business_blueprint
from iidatech.services.business_context import build_business_context_object
from iidatech.services.execution_blueprint import build_execution_blueprint
from iidatech.storage.db import ensure_execution_schema
from iidatech.testing.manual_preview import build_preview_report_payload, enable_manual_preview, is_manual_preview


def run_product_preview(
    topic: str,
    industry: str = "General",
    geography: str = "Global",
    *,
    provision_employees: bool = True,
) -> dict[str, Any]:
    """End-to-end customer simulation for UI display."""
    enable_manual_preview()
    started = time.time()
    case = {
        "case_id": "ui_preview",
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "expected_competitors": 3,
        "expected_pricing_rows": 2,
    }
    route = route_domain(topic, industry, geography)
    domain = str(route.get("selected_domain") or "")
    payload = build_preview_report_payload(case, domain=domain, routed_confidence=float(route.get("confidence") or 0))

    apply_v3_guard_to_payload(payload)
    v3 = payload.get("report_v3")
    v3_md = str(payload.get("report_v3_markdown") or "")
    ctx = build_business_context_object(topic, industry, geography, payload, [])
    blueprint = build_deterministic_business_blueprint(
        ctx,
        domain=domain or infer_business_type(industry=industry, topic=topic, report_v3=v3),
        icp_block={"named_buyer_profiles": [{"named_buyer_profile": f"Primary buyer — {topic[:80]}", "buyer_trigger": "operational pain"}]},
        idea=topic,
        industry=industry,
        geography=geography,
    )
    execution = build_execution_blueprint(blueprint, idea=topic, geography=geography)

    employee_cycle = None
    team_size = 0
    if provision_employees:
        ensure_execution_schema()
        report_id = f"preview_{abs(hash(topic + geography)) % 10_000_000}"
        bt = infer_business_type(industry=industry, topic=topic, report_v3=v3)
        team = hire_default_team(report_id, business_type=bt, founder_name="Founder")
        team_size = len(team)
        employee_cycle = run_agent_company_cycle(report_id, report_v3=v3)

    audit = payload.get("final_report_audit") or {}
    return {
        "success": True,
        "preview_mode": True,
        "topic": topic,
        "industry": industry,
        "geography": geography,
        "routed_domain": domain,
        "routing_confidence": route.get("confidence"),
        "runtime_sec": round(time.time() - started, 2),
        "report_score": audit.get("market_style_score"),
        "payload": payload,
        "report_v3": v3,
        "report_v3_markdown": v3_md,
        "business_blueprint": blueprint,
        "execution_blueprint": execution,
        "boardroom": payload.get("boardroom_strategist") or {},
        "employee_team_size": team_size,
        "employee_cycle": employee_cycle,
        "manual_preview_active": is_manual_preview(),
    }


def save_preview_artifact(result: dict[str, Any], out_dir: Path | None = None) -> Path:
    """Write visible markdown artifact for CLI / file browser."""
    root = out_dir or Path(__file__).resolve().parents[2] / "qa_outputs"
    root.mkdir(parents=True, exist_ok=True)
    path = root / "preview_latest.md"
    lines = [
        f"# IIDATECH Product Preview: {result.get('topic', '')}",
        f"Geography: {result.get('geography')} | Domain: {result.get('routed_domain')} | Score: {result.get('report_score')}",
        "",
        result.get("report_v3_markdown") or "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def main() -> int:
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Run visible IIDATECH product preview")
    parser.add_argument("topic", nargs="?", default="CRM automation for SMBs")
    parser.add_argument("--industry", default="SaaS / B2B Software")
    parser.add_argument("--geography", default="Global")
    args = parser.parse_args()
    result = run_product_preview(args.topic, args.industry, args.geography)
    out = save_preview_artifact(result)
    print(f"Preview saved: {out}")
    print(f"Score={result.get('report_score')} domain={result.get('routed_domain')} runtime={result.get('runtime_sec')}s")
    return 0 if result.get("success") else 1


if __name__ == "__main__":
    raise SystemExit(main())
