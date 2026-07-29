"""Employee tool registry -- schemas, departments, approval gates."""



from __future__ import annotations







from typing import Any







ToolSpec = dict[str, Any]







RESEARCH_TOOLS: list[ToolSpec] = [



    {



        "tool_name": "serp_search",



        "department": "research",



        "input_schema": {"query": "str", "max_results": "int"},



        "output_schema": {"results": "list", "result_count": "int"},



        "requires_approval": False,



    },



    {



        "tool_name": "sql_memory_query",



        "department": "research",



        "input_schema": {"report_id": "str", "limit": "int"},



        "output_schema": {"rows": "list", "row_count": "int"},



        "requires_approval": False,



    },



    {



        "tool_name": "competitor_lookup",



        "department": "research",



        "input_schema": {"report_id": "str"},



        "output_schema": {"competitors": "list", "competitor_count": "int"},



        "requires_approval": False,



    },



    {



        "tool_name": "evidence_writer",



        "department": "research",



        "input_schema": {"gaps": "list", "report_id": "str"},



        "output_schema": {"evidence_log_path": "str", "entries_written": "int"},



        "requires_approval": True,



    },



]







GROWTH_TOOLS: list[ToolSpec] = [



    {



        "tool_name": "lead_scraper",



        "department": "growth",



        "input_schema": {"target_count": "int", "icp_segment": "str"},



        "output_schema": {"leads_generated": "int", "qualified_leads": "int", "csv_path": "str"},



        "requires_approval": False,



    },



    {



        "tool_name": "campaign_builder",



        "department": "growth",



        "input_schema": {"channel": "str", "budget": "float"},



        "output_schema": {"campaign_id": "str", "campaign_path": "str"},



        "requires_approval": True,



    },



    {



        "tool_name": "ad_copy_generator",



        "department": "growth",



        "input_schema": {"channel": "str", "variants": "int"},



        "output_schema": {"variants": "list", "copy_path": "str"},



        "requires_approval": False,



    },



    {



        "tool_name": "outreach_writer",



        "department": "growth",



        "input_schema": {"sequence_steps": "int", "tone": "str"},



        "output_schema": {"sequence_path": "str", "steps_written": "int"},



        "requires_approval": False,



    },



]







SALES_TOOLS: list[ToolSpec] = [



    {



        "tool_name": "crm_update",



        "department": "sales",



        "input_schema": {"report_id": "str", "records": "list"},



        "output_schema": {"records_updated": "int"},



        "requires_approval": False,



    },



    {



        "tool_name": "lead_scoring",



        "department": "sales",



        "input_schema": {"leads_path": "str", "threshold": "float"},



        "output_schema": {"scored_count": "int", "qualified_count": "int", "scores_path": "str"},



        "requires_approval": False,



    },



    {



        "tool_name": "proposal_builder",



        "department": "sales",



        "input_schema": {"account_name": "str", "offer": "str"},



        "output_schema": {"proposal_path": "str"},



        "requires_approval": True,



    },



    {



        "tool_name": "meeting_scheduler",



        "department": "sales",



        "input_schema": {"title": "str", "owner_employee_id": "str"},



        "output_schema": {"task_id": "str", "scheduled": "bool"},



        "requires_approval": False,



    },



]







OPS_TOOLS: list[ToolSpec] = [



    {



        "tool_name": "workflow_builder",



        "department": "ops",



        "input_schema": {"workflow_name": "str", "steps": "list"},



        "output_schema": {"workflow_path": "str", "step_count": "int"},



        "requires_approval": False,



    },



    {



        "tool_name": "task_scheduler",



        "department": "ops",



        "input_schema": {"report_id": "str", "tasks": "list"},



        "output_schema": {"tasks_created": "list", "count": "int"},



        "requires_approval": False,



    },



    {



        "tool_name": "sop_writer",



        "department": "ops",



        "input_schema": {"sop_title": "str", "checklist": "list"},



        "output_schema": {"sop_path": "str"},



        "requires_approval": False,



    },



]







FINANCE_TOOLS: list[ToolSpec] = [



    {



        "tool_name": "runway_calculator",



        "department": "finance",



        "input_schema": {"cash": "float", "monthly_burn": "float"},



        "output_schema": {"runway_months": "float", "report_path": "str"},



        "requires_approval": False,



    },



    {



        "tool_name": "pnl_model",



        "department": "finance",



        "input_schema": {"report_id": "str", "months": "int"},



        "output_schema": {"pnl_path": "str", "gross_margin_pct": "float"},



        "requires_approval": True,



    },



    {



        "tool_name": "invoice_generator",



        "department": "finance",



        "input_schema": {"client": "str", "amount": "float", "currency": "str"},



        "output_schema": {"invoice_path": "str", "invoice_id": "str"},



        "requires_approval": True,



    },



]







# Legacy slug aliases from TOOL_MATRIX -> registry tool_name



SLUG_ALIASES: dict[str, str] = {



    "serpapi": "serp_search",



    "exa": "serp_search",



    "tavily": "serp_search",



    "sql_memory": "sql_memory_query",



    "gtm_engine": "campaign_builder",



    "campaign_generator": "ad_copy_generator",



    "leads_database": "lead_scraper",



    "crm": "crm_update",



    "financial_model": "pnl_model",



    "runway_calculator": "runway_calculator",



    "task_board": "task_scheduler",



    "sop_generator": "sop_writer",



    "vendor_stack": "workflow_builder",



}







_EXECUTION_META: dict[str, tuple[str, bool]] = {



    "serp_search": ("real", False),



    "sql_memory_query": ("real", True),



    "competitor_lookup": ("real", False),



    "evidence_writer": ("real", True),



    "lead_scraper": ("real", False),



    "campaign_builder": ("real", False),



    "ad_copy_generator": ("real", False),



    "outreach_writer": ("real", False),



    "crm_update": ("real", True),



    "lead_scoring": ("real", True),



    "proposal_builder": ("real", True),



    "meeting_scheduler": ("real", True),



    "workflow_builder": ("real", False),



    "task_scheduler": ("real", True),



    "sop_writer": ("real", True),



    "runway_calculator": ("real", False),



    "pnl_model": ("real", False),



    "invoice_generator": ("real", True),



}







ALL_TOOLS: dict[str, ToolSpec] = {}



for group in (RESEARCH_TOOLS, GROWTH_TOOLS, SALES_TOOLS, OPS_TOOLS, FINANCE_TOOLS):



    for spec in group:



        mode, verified = _EXECUTION_META.get(spec["tool_name"], ("simulated", False))



        spec["execution_mode"] = mode



        spec["verified"] = verified



        ALL_TOOLS[spec["tool_name"]] = spec











def list_tools(*, department: str | None = None) -> list[ToolSpec]:



    tools = list(ALL_TOOLS.values())



    if department:



        tools = [t for t in tools if t.get("department") == department]



    return tools











def get_tool(tool_name: str) -> ToolSpec | None:



    name = SLUG_ALIASES.get(tool_name, tool_name)



    return ALL_TOOLS.get(name)











def resolve_tool_name(name: str) -> str:



    return SLUG_ALIASES.get(name, name)











def tools_for_role(role: str, allowed_slugs: list[str]) -> list[ToolSpec]:



    """Map role tool_access slugs to registry specs."""



    seen: set[str] = set()



    out: list[ToolSpec] = []



    for slug in allowed_slugs:



        resolved = resolve_tool_name(slug)



        if resolved in seen:



            continue



        spec = ALL_TOOLS.get(resolved)



        if spec:



            seen.add(resolved)



            out.append(spec)



    return out



