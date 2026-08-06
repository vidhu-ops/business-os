"""Real execution tool handlers wired to iidatech.integrations."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from iidatech.execution.task_engine import create_task
from iidatech.execution.team_memory import get_shared_team_memory, update_shared_team_memory
from iidatech.execution.tool_outcomes import execution_result, tool_result, validation_required_result
from iidatech.integrations.comms import send_email_message, send_slack_message
from iidatech.integrations.files import write_document, write_proposal
from iidatech.integrations.finance import create_payment_link, generate_invoice_pdf
from iidatech.integrations.registry import is_configured
from iidatech.integrations.sales import (
    score_leads_file,
    store_leads,
    upsert_crm_records,
    write_leads_csv,
)
from iidatech.integrations.scheduling import book_calcom_meeting, create_calendar_event
from iidatech.integrations.search import unified_search
from iidatech.storage.execution_repository import list_kpi_history
from iidatech.validation.competitor_evidence import is_verified_competitor_row

_ARTIFACT_ROOT = Path(__file__).resolve().parents[2] / "business_build_outputs" / "employee_runtime"


def _as_dict(v: Any) -> dict:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list:
    return v if isinstance(v, list) else []


def _artifact_dir(report_id: str, employee_id: str) -> Path:
    rid = str(report_id or "default")
    root = _ARTIFACT_ROOT
    if rid.startswith(("os2_", "exec_")):
        root = Path(__file__).resolve().parents[2] / "business_build_outputs" / "employee_os2"
    path = root / rid / str(employee_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _report_v3(context: dict) -> dict:
    rc = context.get("report_context") or {}
    return rc if rc.get("schema_version") else rc.get("report_v3") or {}


def _verified_competitors(v3: dict) -> list[dict]:
    matrix = _as_list(_as_dict(v3.get("competitor_truth")).get("matrix"))
    return [r for r in matrix if isinstance(r, dict) and is_verified_competitor_row(r)]


def _live_search_configured() -> bool:
    try:
        from iidatech.execution.session_api_keys import get_perplexity_override

        if get_perplexity_override():
            return True
    except ImportError:
        pass
    try:
        from iidatech.evidence_bank.perplexity_client import perplexity_enabled

        return perplexity_enabled()
    except Exception:
        return is_configured("serpapi") or is_configured("tavily") or is_configured("exa")


def _competitors_from_report_context(context: dict) -> list[dict]:
    rc = context.get("report_context") if isinstance(context.get("report_context"), dict) else {}
    truth = _as_dict(rc.get("competitor_truth"))
    matrix = _as_list(truth.get("matrix"))
    if matrix:
        out = [r for r in matrix if isinstance(r, dict) and str(r.get("name") or "").strip()]
        if out:
            return out
    v3 = _report_v3(context)
    verified = _verified_competitors(v3)
    if verified:
        return verified
    truth = _as_dict(v3.get("competitor_truth"))
    matrix = _as_list(truth.get("matrix"))
    out = [r for r in matrix if isinstance(r, dict) and str(r.get("name") or "").strip()]
    if out:
        return out
    for row in _as_list(v3.get("competitor_matrix")):
        if isinstance(row, dict) and str(row.get("name") or "").strip():
            out.append(row)
    if out:
        return out
    for sec in _as_list(v3.get("sections")):
        if not isinstance(sec, dict):
            continue
        if int(sec.get("id") or 0) in {7, 8, 60}:
            try:
                from iidatech.services.perplexity_report_engine import _competitors_from_section_metrics

                return _competitors_from_section_metrics(sec)
            except Exception:
                break
    return []


def _live_competitor_fetch(context: dict) -> list[dict]:
    if not _live_search_configured():
        return []
    rc = context.get("report_context") if isinstance(context.get("report_context"), dict) else context
    v3 = _report_v3(context)
    topic = str(rc.get("topic") or v3.get("topic") or "").strip()
    industry = str(rc.get("industry") or v3.get("industry") or "General").strip()
    geography = str(rc.get("geography") or rc.get("country") or v3.get("geography") or "Global").strip()
    if not topic:
        return []
    try:
        from iidatech.evidence_bank.perplexity_client import fetch_market_intelligence

        intel = fetch_market_intelligence(topic, domain=industry or topic, target=geography, industry=industry)
        rows: list[dict] = []
        for ent in _as_list(intel.get("entities")):
            if not isinstance(ent, dict):
                continue
            name = str(ent.get("name") or ent.get("company_name") or "").strip()
            if not name:
                continue
            rows.append(
                {
                    "name": name,
                    "pricing": str(ent.get("pricing") or ent.get("firecrawl_pricing") or "").strip(),
                    "positioning": str(ent.get("positioning") or "").strip(),
                    "source": str(ent.get("source_url") or ent.get("source") or "perplexity_sonar").strip(),
                    "url": str(ent.get("source_url") or "").strip(),
                    "discovered_via": "perplexity_live",
                    "evidence_backed": True,
                }
            )
        return rows
    except Exception:
        return []


def _tool_serp_search(payload: dict, context: dict) -> dict[str, Any]:
    query = str(payload.get("query") or _report_v3(context).get("topic") or "").strip()
    limit = int(payload.get("max_results") or 10)
    logs: list[str] = []
    if query and _live_search_configured():
        rows, metrics = unified_search(query, limit=limit)
        logs.append(f"live_search:{len(rows)} results")
        if rows:
            return execution_result(
                success=True,
                result={"results": rows, "result_count": len(rows), "query": query, "source": "live_api"},
                execution_mode="real",
                verified=False,
                metrics={"search_providers": metrics},
                logs=logs,
            )
    verified = _competitors_from_report_context(context)
    if not verified:
        verified = _live_competitor_fetch(context)
    if not verified:
        return validation_required_result(field="competitor_search")
    results = [
        {"title": r.get("name"), "snippet": r.get("positioning") or "", "source": r.get("source")}
        for r in verified[:limit]
    ]
    logs.append("fallback:verified_report_competitors")
    return execution_result(
        success=True,
        result={"results": results, "result_count": len(results), "query": query, "source": "verified_report"},
        execution_mode="real",
        verified=True,
        logs=logs,
    )


def _tool_sql_memory_query(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "")
    limit = int(payload.get("limit") or 20)
    memory = get_shared_team_memory(report_id) if report_id else {}
    kpis = list_kpi_history(report_id, limit=limit) if report_id else []
    verified_kpis = [k for k in kpis if k.get("notes") != "simulated"]
    rows = [{"type": "team_memory", "keys": list(memory.keys())[:limit]}]
    rows.extend({"type": "kpi", **k} for k in verified_kpis[:limit])
    return execution_result(
        success=True,
        result={"rows": rows, "row_count": len(rows)},
        execution_mode="real",
        verified=bool(rows),
        metrics={"kpi_rows": len(verified_kpis)},
    )


def _tool_competitor_lookup(payload: dict, context: dict) -> dict[str, Any]:
    verified = _competitors_from_report_context(context)
    if not verified:
        verified = _live_competitor_fetch(context)
    if not verified:
        return validation_required_result(
            field="competitors",
            detail="Run Understand your market first, or add a Perplexity API key for live competitor search",
        )
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "research")
    out_dir = _artifact_dir(report_id, employee_id)
    path = out_dir / f"competitors_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(verified, indent=2), encoding="utf-8")
    competitors = [
        {"name": r.get("name"), "pricing": r.get("pricing"), "source": r.get("source") or r.get("url")}
        for r in verified
    ]
    return execution_result(
        success=True,
        result={"competitors": competitors, "competitor_count": len(competitors), "source": "perplexity_live"},
        artifacts=[str(path)],
        execution_mode="real",
        verified=True,
        kpis={"competitors_found": len(competitors)},
        logs=["competitor_lookup:live"],
    )


def _tool_evidence_writer(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "research")
    gaps = _as_list(payload.get("gaps")) or ["evidence gap"]
    out_dir = _artifact_dir(report_id, employee_id)
    path = out_dir / f"evidence_log_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"
    entries = [{"gap": str(g), "status": "logged", "ts": datetime.now(timezone.utc).isoformat()} for g in gaps[:20]]
    path.write_text("\n".join(json.dumps(e) for e in entries) + "\n", encoding="utf-8")
    if report_id:
        update_shared_team_memory(report_id, {"last_evidence_log": str(path)})
    return execution_result(
        success=True,
        result={"evidence_log_path": str(path), "entries_written": len(entries)},
        artifacts=[str(path)],
        execution_mode="real",
        verified=True,
        logs=[f"wrote {path.name}"],
    )


def _tool_lead_scraper(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "")
    employee_id = str(context.get("employee_id") or "growth")
    target = max(5, min(90, int(payload.get("target_count") or 25)))
    rc = _report_v3(context)
    icp = str(payload.get("icp_segment") or rc.get("topic") or "target companies").strip()
    geography = str(payload.get("geography") or rc.get("geography") or rc.get("country") or "Global").strip()
    if not _live_search_configured():
        return validation_required_result(
            field="leads",
            detail="Add a Perplexity API key (Employee OS 2 → API keys) for live lead search",
        )
    from iidatech.evidence_bank.perplexity_client import search_structured_leads
    from iidatech.integrations.sales import format_leads_preview, normalize_lead_records

    # Batch searches when asking for larger daily volumes (cap 90)
    leads = []
    citations_all = []
    search_out = {"backend": None, "error": ""}
    remaining = max(5, min(90, target))
    batch_num = 0
    while remaining > 0 and batch_num < 4 and len(leads) < target:
        batch_num += 1
        take = min(30, remaining)
        variant = icp if batch_num == 1 else f"{icp} (batch {batch_num}, additional companies)"
        search_out = search_structured_leads(icp=variant, geography=geography, limit=take)
        batch = normalize_lead_records(
            search_out.get("parsed"),
            citations=search_out.get("citations"),
            limit=take,
        )
        citations_all.extend(list(search_out.get("citations") or []))
        seen = {(str(l.get("email") or "").lower(), str(l.get("company") or "").lower()) for l in leads}
        for row in batch:
            key = (str(row.get("email") or "").lower(), str(row.get("company") or "").lower())
            if key in seen:
                continue
            seen.add(key)
            leads.append(row)
        remaining = target - len(leads)
        if not batch:
            break
    leads = leads[:target]
    if not leads:
        err = str(search_out.get("error") or "").strip()
        detail = err or "Live search returned no parseable companies — try a narrower ICP or geography"
        return validation_required_result(field="leads", detail=detail)
    out_dir = _artifact_dir(report_id or "default", employee_id)
    csv_path = out_dir / f"leads_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
    write_leads_csv(csv_path, leads)
    crm_out = store_leads(report_id or "default", leads) if report_id else {"stored": 0}
    if report_id:
        update_shared_team_memory(report_id, {"last_leads_csv": str(csv_path), "leads_generated": len(leads)})
    preview = format_leads_preview(leads)
    with_email = sum(1 for l in leads if l.get("email"))
    return execution_result(
        success=True,
        result={
            "leads_generated": len(leads),
            "qualified_leads": len(leads),
            "leads_with_email": with_email,
            "csv_path": str(csv_path),
            "crm_stored": crm_out.get("stored", 0),
            "preview_markdown": preview,
            "leads": leads[: min(15, len(leads))],
        },
        artifacts=[str(csv_path)],
        execution_mode="real",
        verified=True,
        metrics={"search_backend": search_out.get("backend"), "target_count": target, "icp": icp[:120]},
        logs=[f"csv:{csv_path.name}", f"crm_stored:{crm_out.get('stored', 0)}", f"live_leads:{len(leads)}"],
    )


def _business_context_blurb(context: dict) -> str:
    rc = context.get("report_context") if isinstance(context.get("report_context"), dict) else {}
    topic = str(rc.get("topic") or rc.get("idea") or "the business")
    industry = str(rc.get("industry") or "")
    geo = str(rc.get("geography") or rc.get("country") or "Global")
    lines = [f"Topic: {topic}", f"Industry: {industry}", f"Market: {geo}"]
    for sec in (rc.get("sections") or [])[:4]:
        if not isinstance(sec, dict):
            continue
        body = str(sec.get("body_markdown") or sec.get("content") or "").strip()
        if body:
            title = str(sec.get("title") or "section")
            lines.append(f"Report excerpt ({title}): {body[:500]}")
    return "\n".join(lines)


_TEMPLATE_NOTICE = (
    "> ⚠️ **Template draft — no AI provider responded.** Add or fix an API key in "
    "Employee OS settings and re-run this task to get a tailored deliverable.\n\n"
)


def _llm_write_markdown(
    path: Path,
    *,
    prompt: str,
    system: str,
    fallback: str,
) -> tuple[str, str]:
    """Generate via session LLM keys; on failure write a clearly-labeled template."""
    from iidatech.execution.os2_llm import generate_with_session_keys

    text, provider = generate_with_session_keys(prompt, system=system)
    if text and provider:
        body = text.strip() + "\n"
    else:
        body = _TEMPLATE_NOTICE + fallback.strip() + "\n"
    path.write_text(body, encoding="utf-8")
    return body, provider


def _tool_campaign_builder(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "growth")
    out_dir = _artifact_dir(report_id, employee_id)
    channel = str(payload.get("channel") or "email")
    budget = payload.get("budget")
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ctx_blurb = _business_context_blurb(context)
    goal = str(payload.get("goal") or payload.get("brief") or f"Launch a {channel} campaign")
    budget_line = f"Budget: {budget}" if budget is not None else "Budget: not specified — propose a lean SMB test budget"
    prompt = (
        f"Create a complete, client-ready {channel} marketing campaign plan.\n\n"
        f"{ctx_blurb}\n\n"
        f"Goal: {goal}\n{budget_line}\n\n"
        "Include these sections with specific content (no placeholder bullets):\n"
        "1. Objective & success metrics\n2. ICP / audience\n3. Messaging pillars & positioning\n"
        "4. Offer and primary CTA\n5. Channel tactics and creative direction\n"
        "6. 2-week launch timeline (day-by-day)\n7. KPI targets\n8. Three ad headline hooks\n\n"
        "Output markdown only."
    )
    md_path = out_dir / f"campaign_{ts}.md"
    topic_line = ctx_blurb.splitlines()[0].replace("Topic: ", "") if ctx_blurb else "the business"
    fallback = (
        f"# {channel.title()} campaign\n\n"
        f"**Objective:** Drive qualified leads for {topic_line}.\n\n"
        f"**ICP:** SMB decision-makers in the target market.\n\n"
        f"**CTA:** Book a demo.\n"
    )
    body, provider = _llm_write_markdown(
        md_path,
        prompt=prompt,
        system="You are a senior growth marketer producing actionable campaign plans.",
        fallback=fallback,
    )
    json_path = out_dir / f"campaign_{ts}.json"
    doc = {
        "channel": channel,
        "budget": budget,
        "status": "draft",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider or "template",
        "plan_markdown_path": str(md_path),
        "summary": body[:600],
        "goal": goal,
    }
    json_path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    logs = [f"campaign_plan:{md_path.name}", f"campaign_meta:{json_path.name}"]
    if provider:
        logs.append(f"llm:{provider}")
    if is_configured("n8n"):
        try:
            from backend_integrations import post_n8n
            post_n8n({"event": "campaign_draft", "report_id": report_id, "campaign": doc})
            logs.append("n8n:webhook_sent")
        except Exception as exc:
            logs.append(f"n8n:error:{str(exc)[:80]}")
    return execution_result(
        success=True,
        result={
            "campaign_id": json_path.stem,
            "campaign_path": str(json_path),
            "plan_path": str(md_path),
            "channel": channel,
            "provider": provider,
        },
        artifacts=[str(md_path), str(json_path)],
        execution_mode="real",
        verified=bool(provider),
        logs=logs,
    )


def _tool_ad_copy_generator(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "growth")
    channel = str(payload.get("channel") or "linkedin")
    variants = int(payload.get("variants") or 3)
    out_dir = _artifact_dir(report_id, employee_id)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ctx_blurb = _business_context_blurb(context)
    prompt = (
        f"Write {max(variants, 1)} complete {channel} ad variants.\n\n"
        f"{ctx_blurb}\n\n"
        "For each variant include: headline (≤40 chars), primary text (≤150 words), "
        "CTA, and targeting notes.\n"
        "Use markdown with `## Variant N` headings. Be specific to the business — no placeholders."
    )
    path = out_dir / f"ad_copy_{channel}_{ts}.md"
    fallback = "\n\n".join(
        f"## Variant {i + 1}\n\n**Headline:** Grow faster with automation\n\n"
        f"**Body:** Reach your ICP on {channel} with a clear value prop and demo CTA.\n\n**CTA:** Book a demo"
        for i in range(max(variants, 1))
    )
    body, provider = _llm_write_markdown(
        path,
        prompt=prompt,
        system="You write high-converting B2B ad copy.",
        fallback=f"# Ad copy — {channel}\n\n{fallback}\n",
    )
    return execution_result(
        success=True,
        result={"variants": variants, "copy_path": str(path), "channel": channel, "provider": provider},
        artifacts=[str(path)],
        execution_mode="real",
        verified=bool(provider),
        logs=[f"ad_copy:{path.name}"] + ([f"llm:{provider}"] if provider else []),
    )


def _tool_outreach_writer(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "growth")
    steps = int(payload.get("sequence_steps") or 3)
    tone = str(payload.get("tone") or "professional")
    out_dir = _artifact_dir(report_id, employee_id)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    ctx_blurb = _business_context_blurb(context)
    prompt = (
        f"Write a {max(steps, 1)}-step cold outreach email sequence ({tone} tone).\n\n"
        f"{ctx_blurb}\n\n"
        "For each step include: subject line, body (≤180 words), and send timing.\n"
        "Use markdown with `## Step N` headings. Personalize to the ICP — no generic filler."
    )
    path = out_dir / f"outreach_{ts}.md"
    fallback = "\n\n".join(
        f"## Step {i + 1}\n\n**Subject:** Quick idea for your team\n\n"
        f"**Body:** Hi {{first_name}}, noticed teams like yours struggle with manual workflows. "
        f"We help automate outreach and CRM follow-up. Open to a 15-minute call?\n\n**Send:** Day {i * 3}"
        for i in range(max(steps, 1))
    )
    body, provider = _llm_write_markdown(
        path,
        prompt=prompt,
        system="You write concise B2B sales outreach sequences.",
        fallback=f"# Outreach sequence ({tone})\n\n{fallback}\n",
    )
    logs = [f"sequence:{path.name}"] + ([f"llm:{provider}"] if provider else [])
    if is_configured("slack"):
        slack = send_slack_message(f"Outreach sequence drafted for report {report_id}")
        logs.append(f"slack:{'ok' if slack.get('ok') else slack.get('message')}")
    to_email = str(payload.get("send_to") or "")
    if to_email and (is_configured("gmail_smtp") or is_configured("resend") or is_configured("sendgrid")):
        mail = send_email_message(to_email, "Outreach sequence ready", f"Sequence saved at {path}")
        logs.append(f"email:{'ok' if mail.get('ok') else mail.get('message')}")
    return execution_result(
        success=True,
        result={"sequence_path": str(path), "steps_written": steps, "tone": tone, "provider": provider},
        artifacts=[str(path)],
        execution_mode="real",
        verified=bool(provider) or bool(to_email and logs[-1].startswith("email:ok")),
        logs=logs,
    )



def _tool_outreach_personalizer(payload: dict, context: dict) -> dict[str, Any]:
    from iidatech.execution.outreach_pipeline import personalize_leads

    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    rc = context.get("report_context") if isinstance(context.get("report_context"), dict) else {}
    out = personalize_leads(
        report_id,
        idea=str(rc.get("topic") or rc.get("idea") or ""),
        industry=str(rc.get("industry") or ""),
        geography=str(rc.get("geography") or rc.get("country") or "Global"),
        max_leads=int(payload.get("max_leads") or 90),
        use_llm=True,
    )
    return execution_result(
        success=bool(out.get("ok")),
        result=out,
        artifacts=[str(out.get("queue_path"))] if out.get("queue_path") else [],
        execution_mode="real",
        verified=bool(out.get("ok")),
        logs=[str(out.get("message") or ""), f"drafted:{out.get('drafted', 0)}"],
    )

def _tool_crm_update(payload: dict, context: dict) -> dict[str, Any]:
    records = _as_list(payload.get("records"))
    if not records:
        return validation_required_result(field="crm_records")
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    out = upsert_crm_records(report_id, records)
    return execution_result(
        success=True,
        result={"records_updated": out.get("records_updated", 0), "backend": out.get("backend")},
        execution_mode="real",
        verified=True,
        metrics={"backend": out.get("backend")},
        errors=out.get("errors") or [],
        logs=[f"crm:{out.get('backend')}"],
    )


def _tool_lead_scoring(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    leads_path = payload.get("leads_path") or get_shared_team_memory(report_id).get("last_leads_csv")
    if not leads_path or not Path(str(leads_path)).exists():
        return validation_required_result(field="lead_scoring", detail="Run lead_scraper first")
    threshold = float(payload.get("threshold") or 0.5)
    scored = score_leads_file(str(leads_path), threshold=threshold)
    if not scored.get("ok"):
        return validation_required_result(field="lead_scoring", detail=scored.get("error"))
    return execution_result(
        success=True,
        result={
            "scored_count": scored["scored_count"],
            "qualified_count": scored["qualified_count"],
            "scores_path": scored["scores_path"],
        },
        artifacts=[scored["scores_path"]],
        execution_mode="real",
        verified=True,
        metrics={"threshold": threshold},
    )


def _tool_proposal_builder(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "sales")
    account = str(payload.get("account_name") or "Prospect")
    offer = str(payload.get("offer") or "IIDATECH platform")
    out_dir = _artifact_dir(report_id, employee_id)
    doc = write_proposal(out_dir, account_name=account, offer=offer)
    return execution_result(
        success=True,
        result={"proposal_path": doc["path"], "account_name": account},
        artifacts=[doc["path"]],
        execution_mode="real",
        verified=True,
    )


def _tool_meeting_scheduler(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "")
    if not report_id:
        return validation_required_result(field="meeting")
    title = str(payload.get("title") or "Discovery call")[:240]
    employee_id = str(context.get("employee_id") or "sales")
    task = create_task(report_id, title=title, owner_employee_id=employee_id, priority="high")
    if not task.get("task_id"):
        return validation_required_result(field="meeting")
    logs = [f"task:{task.get('task_id')}"]
    artifacts: list[str] = []
    attendee = str(payload.get("attendee_email") or "")
    if is_configured("calcom"):
        booking = book_calcom_meeting(title=title, attendee_email=attendee)
        logs.append(f"calcom:{'ok' if booking.get('ok') else booking.get('message')}")
        if booking.get("ok"):
            return execution_result(
                success=True,
                result={"task_id": task.get("task_id"), "scheduled": True, "booking": booking},
                execution_mode="real",
                verified=True,
                task_id=task.get("task_id"),
                logs=logs,
            )
    cal = create_calendar_event(title=title, out_dir=_artifact_dir(report_id, employee_id))
    if cal.get("ics_path"):
        artifacts.append(cal["ics_path"])
    logs.append(f"calendar:{cal.get('provider')}")
    return execution_result(
        success=True,
        result={"task_id": task.get("task_id"), "scheduled": True, "calendar": cal},
        artifacts=artifacts,
        execution_mode="real",
        verified=cal.get("provider") == "google_calendar",
        task_id=task.get("task_id"),
        logs=logs,
    )


def _tool_workflow_builder(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "ops")
    name = str(payload.get("workflow_name") or "workflow")
    steps = _as_list(payload.get("steps")) or ["intake", "review", "ship"]
    out_dir = _artifact_dir(report_id, employee_id)
    path = out_dir / f"workflow_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    doc = {"name": name, "steps": steps, "created_at": datetime.now(timezone.utc).isoformat()}
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")
    logs = [f"workflow:{path.name}"]
    if is_configured("n8n"):
        try:
            from backend_integrations import post_n8n
            post_n8n({"event": "workflow_created", "workflow": doc})
            logs.append("n8n:ok")
        except Exception as exc:
            logs.append(f"n8n:{str(exc)[:60]}")
    return execution_result(
        success=True,
        result={"workflow_path": str(path), "step_count": len(steps)},
        artifacts=[str(path)],
        execution_mode="real",
        verified=False,
        logs=logs,
    )


def _tool_task_scheduler(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "")
    created = []
    for title in _as_list(payload.get("tasks"))[:10]:
        if not str(title).strip():
            continue
        t = create_task(report_id, title=str(title)[:240], priority="medium")
        if t.get("task_id"):
            created.append(t["task_id"])
    if not created:
        return validation_required_result(field="tasks")
    return execution_result(
        success=True,
        result={"tasks_created": created, "count": len(created)},
        execution_mode="real",
        verified=True,
        metrics={"tasks_created": len(created)},
    )


def _tool_sop_writer(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "ops")
    title = str(payload.get("sop_title") or "Standard operating procedure")
    checklist = _as_list(payload.get("checklist")) or ["Define scope", "Execute", "Review"]
    out_dir = _artifact_dir(report_id, employee_id)
    doc = write_document(
        out_dir,
        filename=f"sop_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md",
        title=title,
        sections=[str(c) for c in checklist],
    )
    return execution_result(
        success=True,
        result={"sop_path": doc["path"]},
        artifacts=[doc["path"]],
        execution_mode="real",
        verified=True,
    )


def _tool_runway_calculator(payload: dict, context: dict) -> dict[str, Any]:
    if not (payload.get("verified_financials") or context.get("verified_financials")):
        return validation_required_result(field="runway", detail="founder-verified cash and burn required")
    cash = payload.get("cash")
    burn = payload.get("monthly_burn")
    if cash is None or burn is None:
        return validation_required_result(field="runway", detail="cash and monthly_burn required")
    try:
        cash_f, burn_f = float(cash), float(burn)
    except (TypeError, ValueError):
        return validation_required_result(field="runway")
    if burn_f <= 0:
        return validation_required_result(field="runway")
    runway = round(cash_f / burn_f, 1)
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "finance")
    out_dir = _artifact_dir(report_id, employee_id)
    path = out_dir / "runway.json"
    path.write_text(json.dumps({"runway_months": runway, "verified": True}, indent=2), encoding="utf-8")
    return execution_result(
        success=True,
        result={"runway_months": runway, "report_path": str(path)},
        artifacts=[str(path)],
        execution_mode="real",
        verified=True,
        kpis={"runway_months": runway},
    )


def _tool_pnl_model(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "finance")
    months = int(payload.get("months") or 12)
    out_dir = _artifact_dir(report_id, employee_id)
    path = out_dir / f"pnl_{months}m.json"
    model = {"months": months, "gross_margin_pct": None, "status": "draft_requires_founder_inputs"}
    path.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return execution_result(
        success=True,
        result={"pnl_path": str(path), "gross_margin_pct": None, "status": "draft"},
        artifacts=[str(path)],
        execution_mode="real",
        verified=False,
        logs=["pnl_draft_created"],
    )


def _tool_invoice_generator(payload: dict, context: dict) -> dict[str, Any]:
    report_id = str(payload.get("report_id") or context.get("report_id") or "default")
    employee_id = str(context.get("employee_id") or "finance")
    client = str(payload.get("client") or "Client")
    amount = float(payload.get("amount") or 0)
    currency = str(payload.get("currency") or "USD")
    if amount <= 0:
        return validation_required_result(field="invoice", detail="positive amount required")
    out_dir = _artifact_dir(report_id, employee_id)
    pdf_path = out_dir / f"invoice_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    inv = generate_invoice_pdf(out_path=pdf_path, client=client, amount=amount, currency=currency)
    logs = [f"invoice:{inv.get('invoice_id')}"]
    payment = {}
    if payload.get("create_payment_link"):
        payment = create_payment_link(
            amount_cents=int(amount * 100),
            currency=currency.lower(),
            description=f"Invoice {inv.get('invoice_id')}",
            success_url=str(payload.get("success_url") or "https://example.com/success"),
            cancel_url=str(payload.get("cancel_url") or "https://example.com/cancel"),
        )
        logs.append(f"payment:{'ok' if payment.get('ok') else payment.get('message', 'skipped')}")
    artifacts = [inv.get("invoice_path")] if inv.get("invoice_path") else []
    return execution_result(
        success=True,
        result={"invoice_path": inv.get("invoice_path"), "invoice_id": inv.get("invoice_id"), "payment": payment},
        artifacts=[a for a in artifacts if a],
        execution_mode="real",
        verified=True,
        logs=logs,
    )


TOOL_HANDLERS = {
    "serp_search": _tool_serp_search,
    "sql_memory_query": _tool_sql_memory_query,
    "competitor_lookup": _tool_competitor_lookup,
    "evidence_writer": _tool_evidence_writer,
    "lead_scraper": _tool_lead_scraper,
    "campaign_builder": _tool_campaign_builder,
    "ad_copy_generator": _tool_ad_copy_generator,
    "outreach_writer": _tool_outreach_writer,
    "outreach_personalizer": _tool_outreach_personalizer,
    "crm_update": _tool_crm_update,
    "lead_scoring": _tool_lead_scoring,
    "proposal_builder": _tool_proposal_builder,
    "meeting_scheduler": _tool_meeting_scheduler,
    "workflow_builder": _tool_workflow_builder,
    "task_scheduler": _tool_task_scheduler,
    "sop_writer": _tool_sop_writer,
    "runway_calculator": _tool_runway_calculator,
    "pnl_model": _tool_pnl_model,
    "invoice_generator": _tool_invoice_generator,
}