"""Deterministic team-leader: read business plan, assign harness tasks (no LLM routing)."""
from __future__ import annotations

import hashlib
import re
from typing import Any

HARNESS_LABELS: dict[str, str] = {
    "research_analyst": "Sam - Research",
    "sales_lead": "Alex - Sales Lead",
    "growth_marketer": "Morgan - Growth",
    "creative_producer": "Riley - Creative",
    "ops_manager": "Jordan - Ops",
}

_TEAM_LEADER_NAME = "Taylor - Team Leader (COO)"


from iidatech.execution.plan_ingest import normalize_plan


def _plan_snapshot(plan: dict[str, Any] | None, *, topic: str, industry: str, geography: str) -> dict[str, Any]:
    plan = normalize_plan(plan, topic=topic, industry=industry, geography=geography)
    concept = plan.get("business_concept") if isinstance(plan.get("business_concept"), dict) else {}
    icp = plan.get("validated_icp") if isinstance(plan.get("validated_icp"), dict) else {}
    profiles = icp.get("named_buyer_profiles", []) if isinstance(icp.get("named_buyer_profiles"), list) else []
    top_icp = profiles[0] if profiles and isinstance(profiles[0], dict) else {}
    marketing = plan.get("marketing_work_pack") if isinstance(plan.get("marketing_work_pack"), dict) else {}
    targeting = marketing.get("targeting") if isinstance(marketing.get("targeting"), dict) else {}
    message = marketing.get("message_hierarchy") if isinstance(marketing.get("message_hierarchy"), dict) else {}
    landing = marketing.get("landing_page_copy") if isinstance(marketing.get("landing_page_copy"), dict) else {}
    sequence = marketing.get("outreach_sequence") if isinstance(marketing.get("outreach_sequence"), list) else []
    first_email = sequence[0] if sequence and isinstance(sequence[0], dict) else {}
    blueprint = plan.get("execution_blueprint") if isinstance(plan.get("execution_blueprint"), dict) else {}
    materials = plan.get("execution_materials_to_create") if isinstance(plan.get("execution_materials_to_create"), list) else []
    return {
        "idea": str(concept.get("idea") or topic or "").strip(),
        "industry": str(concept.get("industry") or industry or "").strip(),
        "geography": str(concept.get("geography") or geography or "").strip(),
        "buyer": str(top_icp.get("named_buyer_profile") or targeting.get("primary_icp") or "target buyer").strip(),
        "pain": str(top_icp.get("pain") or message.get("pain_message") or "").strip(),
        "trigger": str(top_icp.get("buyer_trigger") or "").strip(),
        "cta": str(message.get("cta") or landing.get("primary_cta") or "book a validation call").strip(),
        "channels": list(marketing.get("channel_order") or []),
        "blueprint_tasks": list(blueprint.get("weekly_tasks") or blueprint.get("tasks") or []),
        "materials": [str(m) for m in materials if str(m).strip()][:12],
    }


def _task_id(harness_id: str, title: str, seq: int) -> str:
    raw = f"{harness_id}|{title}|{seq}".lower()
    return f"tl_{hashlib.sha256(raw.encode()).hexdigest()[:10]}"


def _item(
    *,
    seq: int,
    harness_id: str,
    title: str,
    prompt: str,
    task_kind: str = "harness",
    oauth_provider: str = "",
    depends_on: list[str] | None = None,
    external: bool = False,
) -> dict[str, Any]:
    return {
        "id": _task_id(harness_id, title, seq),
        "seq": seq,
        "harness_id": harness_id,
        "assignee": HARNESS_LABELS.get(harness_id, harness_id),
        "title": title,
        "prompt": prompt,
        "task_kind": task_kind,
        "oauth_provider": oauth_provider,
        "external": external,
        "depends_on": list(depends_on or []),
        "status": "pending",
        "approved": not external,
        "result": "",
        "artifacts": [],
        "error": "",
    }


def build_checklist_from_plan(
    plan: dict[str, Any] | None,
    *,
    topic: str,
    industry: str,
    geography: str,
) -> dict[str, Any]:
    plan = normalize_plan(plan, topic=topic, industry=industry, geography=geography)
    snap = _plan_snapshot(plan, topic=topic, industry=industry, geography=geography)
    idea = snap["idea"] or topic
    geo = snap["geography"] or geography
    buyer = snap["buyer"]
    cta = snap["cta"]
    pain = snap["pain"] or "core buyer pain from the plan"
    trigger = snap["trigger"] or "buying trigger from the plan"
    items: list[dict[str, Any]] = []
    seq = 0

    def add(**kwargs: Any) -> None:
        nonlocal seq
        seq += 1
        items.append(_item(seq=seq, **kwargs))

    add(
        harness_id="research_analyst",
        title="Competitor and pricing evidence pass",
        prompt=(
            f"Research named competitors, pricing tiers, and review signals for {idea} serving {buyer} in {geo}. "
            f"Pull live evidence and log gaps."
        ),
    )
    lead_dep = [items[-1]["id"]] if items else []
    add(
        harness_id="sales_lead",
        title="Qualified lead list (CSV)",
        prompt=(
            f"Find 20 qualified leads for {idea} targeting {buyer} in {geo}. "
            f"Export real companies with contact names, titles, emails or LinkedIn where available."
        ),
        depends_on=lead_dep,
    )
    outreach_dep = [items[-1]["id"]] if items else []
    add(
        harness_id="sales_lead",
        title="3-step cold outreach sequence",
        prompt=(
            f"Write a 3-step cold outreach sequence for {buyer}. Pain: {pain}. Trigger: {trigger}. CTA: {cta}. "
            f"Include opt-out language."
        ),
        depends_on=outreach_dep,
    )
    campaign_id = None
    add(
        harness_id="growth_marketer",
        title="LinkedIn + email campaign draft",
        prompt=(
            f"Draft a LinkedIn post and email campaign for {idea} in {geo}. Buyer: {buyer}. CTA: {cta}. "
            f"Create 3 ad copy variants."
        ),
    )
    campaign_id = items[-1]["id"]
    add(
        harness_id="creative_producer",
        title="Landing hero and proof brief",
        prompt=f"Create a creative brief for the landing page hero for {idea}. Buyer: {buyer}. Geography: {geo}.",
    )
    add(
        harness_id="ops_manager",
        title="Weekly execution SOP and handoff checklist",
        prompt=f"Write an SOP checklist for weekly sales and marketing execution for {idea}.",
    )
    for mat in snap["materials"][:3]:
        add(
            harness_id=_material_to_harness(mat),
            title=f"Plan deliverable: {mat[:72]}",
            prompt=f"Create this deliverable for {idea} in {geo}: {mat}.",
        )
    for bp in snap["blueprint_tasks"][:2]:
        text = str(bp)
        add(
            harness_id=_text_to_harness(text),
            title=f"Blueprint task: {text[:72]}",
            prompt=f"Execute for {idea} ({geo}): {text}",
        )
    add(
        harness_id="growth_marketer",
        title="Post approved LinkedIn update (OAuth)",
        prompt=f"Publish the approved LinkedIn campaign message for {idea} targeting {buyer}.",
        task_kind="oauth_post",
        oauth_provider="linkedin",
        external=True,
        depends_on=[campaign_id] if campaign_id else [],
    )
    add(
        harness_id="sales_lead",
        title="Send pilot outreach email (OAuth)",
        prompt=f"Send the approved outreach email to the first qualified lead for {idea}.",
        task_kind="oauth_send",
        oauth_provider="gmail",
        external=True,
        depends_on=outreach_dep,
    )
    add(
        harness_id="sales_lead",
        title="Sync leads to HubSpot CRM (OAuth)",
        prompt=f"Create HubSpot contacts for the lead CSV for {idea} in {geo}.",
        task_kind="oauth_crm",
        oauth_provider="hubspot",
        external=True,
        depends_on=lead_dep,
    )
    summary = (
        f"{_TEAM_LEADER_NAME} reviewed the business plan for {idea} ({geo}). "
        f"Assigned {len(items)} tasks. Buyer focus: {buyer}. External steps need OAuth + approval."
    )
    return {
        "team_leader": _TEAM_LEADER_NAME,
        "summary": summary,
        "snapshot": snap,
        "items": items,
        "current_index": 0,
    }


def _material_to_harness(text: str) -> str:
    lower = text.lower()
    if any(x in lower for x in ("lead", "crm", "outreach", "sales")):
        return "sales_lead"
    if any(x in lower for x in ("research", "competitor", "market")):
        return "research_analyst"
    if any(x in lower for x in ("sop", "ops", "workflow")):
        return "ops_manager"
    if any(x in lower for x in ("creative", "landing", "brand", "video")):
        return "creative_producer"
    return "growth_marketer"


def _text_to_harness(text: str) -> str:
    lower = text.lower()
    if re.search(r"\b(lead|outbound|pipeline|crm)\b", lower):
        return "sales_lead"
    if re.search(r"\b(competitor|research|evidence|pricing)\b", lower):
        return "research_analyst"
    if re.search(r"\b(sop|ops|checklist|handoff)\b", lower):
        return "ops_manager"
    if re.search(r"\b(creative|landing|design|storyboard)\b", lower):
        return "creative_producer"
    return "growth_marketer"


def next_runnable_item(
    checklist: dict[str, Any],
    *,
    auto_approve: bool = False,
    harness_ids: set[str] | None = None,
) -> dict[str, Any] | None:
    items = checklist.get("items") if isinstance(checklist.get("items"), list) else []
    done_ids = {str(i.get("id")) for i in items if str(i.get("status")) in {"completed", "skipped"}}
    for item in sorted(items, key=lambda x: int(x.get("seq") or 0)):
        if harness_ids is not None and str(item.get("harness_id") or "") not in harness_ids:
            continue
        if str(item.get("status")) in {"completed", "skipped", "running", "failed", "qc_failed"}:
            # qc_failed requires explicit founder retry (retry_task) — never auto-rerun.
            continue
        deps = [str(d) for d in (item.get("depends_on") or [])]
        if deps and not all(d in done_ids for d in deps):
            continue
        if not auto_approve and not item.get("approved") and str(item.get("status")) != "awaiting_approval":
            if str(item.get("status")) == "pending":
                item["status"] = "awaiting_approval"
            return item
        if auto_approve or item.get("approved"):
            return item
    return None
