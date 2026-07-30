from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.services.audit_service import audit_status

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/status")
def get_audit_status(email: str = Depends(get_current_user)) -> dict:
    return audit_status(email)