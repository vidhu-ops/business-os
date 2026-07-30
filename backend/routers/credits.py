from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.auth import get_current_user
from backend.services.credit_service import get_balance

router = APIRouter(prefix="/credits", tags=["credits"])


@router.get("")
def credits_info(email: str = Depends(get_current_user)) -> dict:
    return get_balance(email)
