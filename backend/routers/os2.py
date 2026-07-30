from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.services import os2_service
from backend.services.credit_service import charge_office_week
from backend.services.workspaces import load_workspace, save_workspace

router = APIRouter(prefix="/os2", tags=["os2"])


class ScopeBody(BaseModel):
    mode: str = "full_office"
    departments: list[str] = Field(default_factory=list)
    harness_ids: list[str] = Field(default_factory=list)


class ApiKeysBody(BaseModel):
    keys: dict[str, str] = Field(default_factory=dict)


class ChatBody(BaseModel):
    message: str = Field(min_length=1)


class RunNextBody(BaseModel):
    auto_approve_external: bool = False


@router.get("/{workspace_id}")
def get_os2_workspace(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.bootstrap_os2(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{workspace_id}/scope")
def patch_scope(workspace_id: str, body: ScopeBody, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    from iidatech.execution.office_scope import OfficeScope

    scope = OfficeScope(mode=body.mode, departments=body.departments, harness_ids=body.harness_ids)
    saved = os2_service.save_scope(workspace, scope)
    return {"scope": saved, "configured": scope.is_configured()}


@router.patch("/{workspace_id}/keys")
def patch_api_keys(workspace_id: str, body: ApiKeysBody, _: str = Depends(get_current_user)) -> dict:
    merged = os2_service.set_session_keys(workspace_id, body.keys)
    return {"active_key_providers": list(merged.keys())}


@router.get("/{workspace_id}/chat/{harness_id}")
def get_chat(workspace_id: str, harness_id: str, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    from backend.services.workspace_context import workspace_report_id

    chat = os2_service.load_agent_chat(workspace_report_id(workspace), harness_id)
    return {"chat": chat}


@router.post("/{workspace_id}/chat/{harness_id}")
def post_chat(workspace_id: str, harness_id: str, body: ChatBody, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.run_agent_chat(workspace_id, harness_id, body.message)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{workspace_id}/checklist/build")
def build_checklist(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    workspace = load_workspace(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Project not found")
    checklist = os2_service.build_team_checklist(workspace)
    return {"checklist": checklist}


@router.post("/{workspace_id}/checklist/run-next")
def checklist_run_next(workspace_id: str, body: RunNextBody, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.run_checklist_next(workspace_id, auto_approve_external=body.auto_approve_external)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workspace_id}/pulse")
def taylor_pulse(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        state = os2_service.bootstrap_os2(workspace_id)
        return {"pulse": state.get("taylor_pulse")}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workspace_id}/command")
def command_center(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.command_center_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workspace_id}/war-room")
def war_room(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.war_room_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workspace_id}/office")
def office_board(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.office_board_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class OfficeActionBody(BaseModel):
    action: str
    goals: list[str] = Field(default_factory=list)
    auto_approve: bool = False


@router.post("/{workspace_id}/office/action")
def office_action(workspace_id: str, body: OfficeActionBody, email: str = Depends(get_current_user)) -> dict:
    credit: dict | None = None
    if body.action == "full_day":
        workspace = load_workspace(workspace_id)
        if not workspace:
            raise HTTPException(status_code=404, detail="Project not found")
        scope = os2_service._scope_from_workspace(workspace)
        mode = "full_office" if scope.is_full_office() else "department"
        departments = list(scope.departments) if scope.mode == "department" else []
        credit = charge_office_week(email, workspace, mode=mode, departments=departments)
        save_workspace(workspace)
    try:
        result = os2_service.run_office_action(
            workspace_id,
            body.action,
            goals=body.goals,
            auto_approve=body.auto_approve,
        )
        if credit is not None:
            result["credit"] = credit
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class TaylorActionBody(BaseModel):
    action: str


@router.post("/{workspace_id}/taylor/action")
def taylor_action(workspace_id: str, body: TaylorActionBody, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.run_taylor_action(workspace_id, body.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


class TaskActionBody(BaseModel):
    action: str


@router.post("/{workspace_id}/tasks/{task_id}/action")
def task_action(workspace_id: str, task_id: str, body: TaskActionBody, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.run_task_action(workspace_id, task_id, body.action)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{workspace_id}/oauth")
def oauth_status(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return {"providers": os2_service.oauth_links(workspace_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workspace_id}/memory")
def company_memory(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return {"memory": os2_service.company_memory_snapshot(workspace_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class HarnessBody(BaseModel):
    name: str
    base_harness_id: str = "sales_lead"
    tagline: str = "Custom workflows"
    starters: list[str] = Field(default_factory=list)


@router.get("/{workspace_id}/harnesses")
def get_harnesses(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return {"custom": os2_service.list_custom_harnesses(workspace_id)}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{workspace_id}/harnesses")
def post_harness(workspace_id: str, body: HarnessBody, _: str = Depends(get_current_user)) -> dict:
    try:
        items = os2_service.add_custom_harness(workspace_id, body.model_dump())
        return {"custom": items}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{workspace_id}/employees")
def get_employees(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.list_employees_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


class HireBody(BaseModel):
    name: str = ""
    role: str
    catalog: bool = False


class DepartmentHireRow(BaseModel):
    id: str
    name: str = ""
    headcount: int = Field(ge=0, le=20, default=1)


class DepartmentsBody(BaseModel):
    departments: list[DepartmentHireRow] = Field(default_factory=list)


class HumanBody(BaseModel):
    name: str = Field(min_length=1)
    role: str = ""
    departments: list[str] = Field(default_factory=list)


class BroadcastBody(BaseModel):
    message: str = Field(min_length=1)
    from_agent: str = "taylor"


@router.post("/{workspace_id}/employees")
def post_hire(workspace_id: str, body: HireBody, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.hire_employee_action(workspace_id, name=body.name, role=body.role, catalog=body.catalog)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{workspace_id}/departments")
def get_departments(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.departments_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/{workspace_id}/departments")
def patch_departments(workspace_id: str, body: DepartmentsBody, _: str = Depends(get_current_user)) -> dict:
    try:
        rows = [r.model_dump() for r in body.departments]
        return os2_service.set_departments_hiring(workspace_id, rows)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{workspace_id}/org-chart")
def get_org_chart(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.org_chart_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/{workspace_id}/humans")
def get_humans(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.list_humans_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{workspace_id}/humans")
def post_human(workspace_id: str, body: HumanBody, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.add_human_employee(workspace_id, name=body.name, role=body.role, departments=body.departments)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.delete("/{workspace_id}/humans/{human_id}")
def delete_human(workspace_id: str, human_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.remove_human_employee(workspace_id, human_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{workspace_id}/collaboration")
def get_collaboration(workspace_id: str, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.collaboration_snapshot(workspace_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/{workspace_id}/chat/broadcast")
def post_broadcast(workspace_id: str, body: BroadcastBody, _: str = Depends(get_current_user)) -> dict:
    try:
        return os2_service.run_broadcast_chat(workspace_id, body.message, from_agent=body.from_agent)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
