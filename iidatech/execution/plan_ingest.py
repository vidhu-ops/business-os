"""Normalize business plans from any common format for team leader + agents."""
from __future__ import annotations

import json
import re
from typing import Any


def _as_dict(val: Any) -> dict[str, Any]:
    return val if isinstance(val, dict) else {}


def _as_list(val: Any) -> list[Any]:
    return val if isinstance(val, list) else []


def _first_str(*vals: Any) -> str:
    for v in vals:
        s = str(v or "").strip()
        if s:
            return s
    return ""


def normalize_plan(
    raw: Any,
    *,
    topic: str = "",
    industry: str = "",
    geography: str = "",
) -> dict[str, Any]:
    """Accept nested builder plan, founder-readable plan, flat JSON, or markdown text."""
    if raw is None:
        return _empty_shell(topic, industry, geography)
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return _empty_shell(topic, industry, geography)
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    return normalize_plan(parsed, topic=topic, industry=industry, geography=geography)
            except json.JSONDecodeError:
                pass
        return _from_markdown(text, topic=topic, industry=industry, geography=geography)
    if not isinstance(raw, dict):
        return _empty_shell(topic, industry, geography)

    if raw.get("business_concept") or raw.get("validated_icp") or raw.get("marketing_work_pack"):
        return _enrich_shell(raw, topic, industry, geography)

    if raw.get("founder_plan") or raw.get("template_used") or raw.get("customer_acquisition_strategy"):
        return _from_founder_readable(raw, topic, industry, geography)

    if raw.get("idea") or raw.get("business_idea") or raw.get("wedge"):
        return _from_flat(raw, topic, industry, geography)

    if raw.get("sections") or raw.get("phases") or raw.get("action_items"):
        return _from_sections_plan(raw, topic, industry, geography)

    return _enrich_shell(raw, topic, industry, geography)


def _empty_shell(topic: str, industry: str, geography: str) -> dict[str, Any]:
    return {
        "business_concept": {"idea": topic, "industry": industry, "geography": geography},
        "validated_icp": {"named_buyer_profiles": []},
        "marketing_work_pack": {},
        "execution_blueprint": {"tasks": []},
        "execution_materials_to_create": [],
        "first_90_day_plan": [],
    }


def _enrich_shell(plan: dict[str, Any], topic: str, industry: str, geography: str) -> dict[str, Any]:
    out = dict(plan)
    concept = _as_dict(out.get("business_concept"))
    concept.setdefault("idea", topic)
    concept.setdefault("industry", industry)
    concept.setdefault("geography", geography)
    out["business_concept"] = concept
    out.setdefault("validated_icp", {"named_buyer_profiles": []})
    out.setdefault("marketing_work_pack", {})
    out.setdefault("execution_blueprint", {"tasks": []})
    out.setdefault("execution_materials_to_create", _as_list(out.get("execution_materials_to_create")))
    out.setdefault("first_90_day_plan", _as_list(out.get("first_90_day_plan")))
    return out


def _from_founder_readable(raw: dict[str, Any], topic: str, industry: str, geography: str) -> dict[str, Any]:
    concept = {
        "idea": _first_str(raw.get("title"), raw.get("idea"), topic),
        "industry": industry,
        "geography": _first_str(raw.get("geography"), raw.get("target_country"), geography),
    }
    buyer = _first_str(raw.get("buyer"), raw.get("primary_buyer"))
    if isinstance(raw.get("customer_acquisition_strategy"), dict):
        buyer = _first_str(buyer, raw["customer_acquisition_strategy"].get("primary_icp"))
    profiles = []
    if buyer:
        profiles.append({"named_buyer_profile": buyer, "pain": _first_str(raw.get("pain"))})
    materials = _as_list(raw.get("required_outputs")) + _as_list(raw.get("proof_asset_pack"))
    tasks = _as_list(raw.get("first_90_day_plan")) + _as_list(raw.get("milestones"))
    return _enrich_shell(
        {
            "business_concept": concept,
            "validated_icp": {"named_buyer_profiles": profiles},
            "marketing_work_pack": _as_dict(raw.get("customer_acquisition_strategy")),
            "execution_materials_to_create": [str(m) for m in materials if str(m).strip()],
            "execution_blueprint": {"tasks": [str(t) for t in tasks if str(t).strip()]},
            "first_90_day_plan": [str(t) for t in tasks if str(t).strip()],
        },
        topic,
        industry,
        geography,
    )


def _from_flat(raw: dict[str, Any], topic: str, industry: str, geography: str) -> dict[str, Any]:
    concept = {
        "idea": _first_str(raw.get("idea"), raw.get("business_idea"), raw.get("wedge"), topic),
        "industry": _first_str(raw.get("industry"), industry),
        "geography": _first_str(raw.get("geography"), raw.get("country"), raw.get("market"), geography),
    }
    buyer = _first_str(raw.get("buyer"), raw.get("icp"), raw.get("target_customer"))
    profiles = [{"named_buyer_profile": buyer, "pain": _first_str(raw.get("pain"))}] if buyer else []
    tasks = _as_list(raw.get("tasks")) + _as_list(raw.get("steps")) + _as_list(raw.get("action_items"))
    return _enrich_shell(
        {
            "business_concept": concept,
            "validated_icp": {"named_buyer_profiles": profiles},
            "execution_blueprint": {"tasks": [str(t) for t in tasks]},
            "execution_materials_to_create": [str(t) for t in _as_list(raw.get("deliverables"))],
        },
        topic,
        industry,
        geography,
    )


def _from_sections_plan(raw: dict[str, Any], topic: str, industry: str, geography: str) -> dict[str, Any]:
    tasks: list[str] = []
    for key in ("action_items", "phases", "sections", "tasks", "milestones"):
        for item in _as_list(raw.get(key)):
            if isinstance(item, dict):
                tasks.append(_first_str(item.get("title"), item.get("name"), item.get("task"), json.dumps(item)[:120]))
            else:
                tasks.append(str(item))
    return _from_flat({**raw, "tasks": tasks}, topic, industry, geography)


def _from_markdown(text: str, *, topic: str, industry: str, geography: str) -> dict[str, Any]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    tasks: list[str] = []
    materials: list[str] = []
    buyer = ""
    for ln in lines:
        if re.match(r"^#{1,3}\s+", ln):
            materials.append(re.sub(r"^#{1,3}\s+", "", ln))
        elif re.match(r"^[-*]\s+", ln):
            tasks.append(re.sub(r"^[-*]\s+", "", ln))
        elif ln.lower().startswith("buyer:"):
            buyer = ln.split(":", 1)[-1].strip()
    concept = {"idea": topic or (materials[0] if materials else "Business plan"), "industry": industry, "geography": geography}
    profiles = [{"named_buyer_profile": buyer}] if buyer else []
    return _enrich_shell(
        {
            "business_concept": concept,
            "validated_icp": {"named_buyer_profiles": profiles},
            "execution_blueprint": {"tasks": tasks},
            "execution_materials_to_create": materials,
        },
        topic,
        industry,
        geography,
    )


SESSION_PLAN_KEYS = (
    "iidatech_business_plan",
    "business_builder_plan",
    "founder_readable_business_plan",
)


def get_session_business_plan(st: Any) -> dict[str, Any] | None:
    """Read business plan from any mode's session key."""
    for key in SESSION_PLAN_KEYS:
        plan = st.session_state.get(key)
        if isinstance(plan, dict) and plan:
            return plan
    return None


def set_session_business_plan(st: Any, plan: dict[str, Any]) -> None:
    """Write business plan to all shared session keys."""
    if not isinstance(plan, dict) or not plan:
        return
    for key in SESSION_PLAN_KEYS:
        st.session_state[key] = plan
