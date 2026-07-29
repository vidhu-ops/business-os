"""Standard tool outcome envelopes for customer trust."""

from __future__ import annotations

from typing import Any

VALIDATION_REQUIRED: dict[str, Any] = {
    "status": "validation_required",
    "verified": False,
    "reason": "insufficient real evidence",
}


def tool_result(
    *,
    success: bool,
    result: dict | None = None,
    kpis: dict | None = None,
    artifacts: list | None = None,
    error: str | None = None,
    execution_mode: str = "simulated",
    verified: bool = False,
    task_id: str | None = None,
    metrics: dict | None = None,
    logs: list | None = None,
    errors: list | None = None,
) -> dict[str, Any]:
    err_list = list(errors or [])
    if error:
        err_list.append(str(error))
    return {
        "success": success,
        "result": result or {},
        "kpis": kpis or {},
        "artifacts": artifacts or [],
        "error": error,
        "execution_mode": execution_mode,
        "verified": verified,
        "task_id": task_id or "",
        "metrics": metrics or {},
        "logs": logs or [],
        "errors": err_list,
    }


def execution_result(
    *,
    task_id: str = "",
    execution_mode: str = "simulated",
    verified: bool = False,
    artifacts: list | None = None,
    metrics: dict | None = None,
    logs: list | None = None,
    errors: list | None = None,
    success: bool = True,
    result: dict | None = None,
    kpis: dict | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    """Phase 3 schema: every tool output includes task_id, metrics, logs, errors."""
    return tool_result(
        success=success,
        result=result,
        kpis=kpis,
        artifacts=artifacts,
        error=error,
        execution_mode=execution_mode,
        verified=verified,
        task_id=task_id,
        metrics=metrics,
        logs=logs,
        errors=errors,
    )


def validation_required_result(**extra: Any) -> dict[str, Any]:
    return tool_result(
        success=False,
        result={**VALIDATION_REQUIRED, **extra},
        execution_mode="simulated",
        verified=False,
    )


def badge_for(outcome: dict[str, Any]) -> str:
    err = str(outcome.get("error") or "")
    if err.startswith("approval_required"):
        return "Blocked"
    if outcome.get("verified"):
        return "Verified"
    if (outcome.get("result") or {}).get("status") == "validation_required":
        return "Blocked"
    if str(outcome.get("execution_mode")) == "real" and outcome.get("success"):
        return "Verified"
    return "Simulated"