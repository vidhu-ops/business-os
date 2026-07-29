"""Task and employee lifecycle for Employee OS."""
from __future__ import annotations
from iidatech.execution.long_memory import on_task_blocked, on_task_completed
from iidatech.storage.execution_repository import deactivate_employee, get_task, insert_employee, insert_task, list_employees, update_task

def hire_employee(report_id, *, name, role, department="", authority_level=5, skills=None):
    return insert_employee(report_id, name=name, role=role, department=department, authority_level=authority_level, skills=skills)

def remove_employee(employee_id):
    return deactivate_employee(employee_id)

def create_task(report_id, *, title, owner_employee_id=None, priority="medium", due_date=None, dependencies=None):
    return insert_task(report_id, title=title, owner_employee_id=owner_employee_id, priority=priority, due_date=due_date, dependencies=dependencies)

def assign_task(task_id, owner_employee_id):
    return update_task(task_id, owner_employee_id=owner_employee_id, status="assigned")

def complete_task(task_id):
    task = get_task(task_id)
    updated = update_task(task_id, status="completed", blockers=[])
    if task and updated:
        on_task_completed(str(task.get("report_id") or ""), task.get("owner_employee_id"), updated)
    return updated

def block_task(task_id, blocker):
    task = get_task(task_id)
    if not task:
        return None
    blockers = list(task.get("blockers") or [])
    if blocker and blocker not in blockers:
        blockers.append(blocker)
    updated = update_task(task_id, status="blocked", blockers=blockers)
    if updated:
        on_task_blocked(str(task.get("report_id") or ""), task.get("owner_employee_id"), updated, str(blocker))
    return updated

def unblock_task(task_id, resolved_blocker=None):
    task = get_task(task_id)
    if not task:
        return None
    blockers = list(task.get("blockers") or [])
    if resolved_blocker and resolved_blocker in blockers:
        blockers.remove(resolved_blocker)
    status = "open" if not blockers else "blocked"
    return update_task(task_id, status=status, blockers=blockers)

def founder_employee_id(report_id):
    for emp in list_employees(report_id):
        if str(emp.get("role", "")).lower() == "founder":
            return str(emp["employee_id"])
    return None
