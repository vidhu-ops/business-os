from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services.workspace_context import workspace_report_context, workspace_report_id
from backend.services.workspaces import load_workspace, save_workspace
from iidatech.execution.employee_os2_harness import OS2_HARNESSES, execute_harness_job
from iidatech.execution.os2_api_keys import merge_api_keys

router = APIRouter(prefix="/team", tags=["team"])


class TeamRunBody(BaseModel):
    workspace_id: str
    harness_id: str
    message: str = Field(default="Run your default starter task for this project.")


@router.get("/roster")
def team_roster(_: str = Depends(get_current_user)) -> dict:
    return {
        "agents": [
            {
                "id": h["id"],
                "name": h.get("name"),
                "role": h.get("role"),
                "tagline": h.get("tagline"),
                "starters": h.get("starters") or [],
            }
            for h in OS2_HARNESSES
        ]
    }


@router.get("/{workspace_id}")
def team_status(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    team = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    return {
        "team": team,
        "report_id": workspace_report_id(workspace),
        "has_research": bool((workspace.get("research_report") or {}).get("available")),
    }


@router.post("/run")
def run_team_task(body: TeamRunBody, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(body.workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")

    report_id = workspace_report_id(workspace)
    api_keys = merge_api_keys()
    report_context = workspace_report_context(workspace)

    result = execute_harness_job(
        body.harness_id,
        body.message,
        report_id=report_id,
        api_keys=api_keys,
        report_context=report_context,
    )

    team = workspace.get("employee_os") if isinstance(workspace.get("employee_os"), dict) else {}
    runs = list(team.get("runs") or [])
    runs.insert(
        0,
        {
            "harness_id": body.harness_id,
            "message": body.message,
            "success": bool(result.get("success")),
            "reply": result.get("reply"),
            "artifacts": result.get("artifacts") or [],
        },
    )
    team["available"] = True
    team["runs"] = runs[:20]
    workspace["employee_os"] = team
    save_workspace(workspace)
    return {"success": bool(result.get("success")), "result": result}
