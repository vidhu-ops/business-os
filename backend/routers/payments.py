from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.auth import get_current_user
from backend.config import settings
from backend.services.account_service import activate_plan
from backend.services.credit_service import add_credits
from backend.services.freecharge_service import build_checkout_request, gateway_info, is_configured, parse_webhook_payload
from backend.services.payment_service import (
    create_credit_pack_order,
    create_order,
    get_order,
    get_order_by_merchant_txn,
    list_public_plans,
    mark_order_paid,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/payments", tags=["payments"])


class CheckoutBody(BaseModel):
    plan_id: str = Field(min_length=2)


class CreditPackCheckoutBody(BaseModel):
    pack_id: str = Field(min_length=2)


def _fulfill_paid_order(order: dict) -> None:
    kind = str(order.get("order_kind") or "subscription")
    email = str(order.get("email") or "")
    if kind == "credit_pack":
        credits = int(order.get("credits_granted") or 0)
        if credits > 0:
            add_credits(email, credits, reason="credit_pack_purchase", metadata={"order_id": order.get("order_id")})
        return
    activate_plan(email, str(order.get("plan_id") or "growth"))


def _frontend_base() -> str:
    return (settings.frontend_url or "http://localhost:3000").rstrip("/")


def _api_base(request: Request) -> str:
    return str(request.base_url).rstrip("/")


@router.get("/plans")
def payment_plans() -> dict:
    return {"plans": list_public_plans(), "gateway": gateway_info()}


@router.post("/checkout/credits")
def start_credit_pack_checkout(body: CreditPackCheckoutBody, request: Request, email: str = Depends(get_current_user)) -> dict:
    if not is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway is not configured yet")
    order = create_credit_pack_order(
        email=email,
        pack_id=body.pack_id.strip().lower(),
        return_url=f"{_frontend_base()}/payment/callback",
        notify_url=f"{_api_base(request)}/api/v1/payments/webhook/freecharge",
    )
    checkout = build_checkout_request(
        merchant_txn_id=str(order["merchant_txn_id"]),
        amount_paise=int(order["amount_paise"]),
        currency=str(order["currency"]),
        customer_email=email,
        return_url=f"{order['return_url']}?order_id={order['order_id']}",
        notify_url=str(order["notify_url"]),
        description=str(order.get("plan_name") or "IIDATECH credits"),
    )
    return {"order": order, "checkout": checkout}


@router.post("/checkout")
def start_checkout(body: CheckoutBody, request: Request, email: str = Depends(get_current_user)) -> dict:
    if not is_configured():
        raise HTTPException(status_code=503, detail="Payment gateway is not configured yet")
    plan_id = body.plan_id.strip().lower()
    order = create_order(
        email=email,
        plan_id=plan_id,
        return_url=f"{_frontend_base()}/payment/callback",
        notify_url=f"{_api_base(request)}/api/v1/payments/webhook/freecharge",
    )
    checkout = build_checkout_request(
        merchant_txn_id=str(order["merchant_txn_id"]),
        amount_paise=int(order["amount_paise"]),
        currency=str(order["currency"]),
        customer_email=email,
        return_url=f"{order['return_url']}?order_id={order['order_id']}",
        notify_url=str(order["notify_url"]),
        description=str(order.get("plan_name") or "IIDATECH Growth"),
    )
    return {"order": order, "checkout": checkout}


@router.post("/webhook/freecharge")
async def freecharge_webhook(request: Request) -> dict:
    try:
        content_type = (request.headers.get("content-type") or "").lower()
        if "application/json" in content_type:
            body = await request.json()
        else:
            form = await request.form()
            body = dict(form)
        if not isinstance(body, dict):
            raise ValueError("Invalid webhook body")
        data = parse_webhook_payload(body)
    except Exception as exc:
        logger.warning("Freecharge webhook rejected: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    merchant_txn_id = str(data.get("merchantTxnId") or data.get("merchant_txn_id") or "")
    status = str(data.get("status") or data.get("txnStatus") or data.get("paymentStatus") or "").lower()
    gateway_ref = str(data.get("txnId") or data.get("fcTxnId") or data.get("gatewayTxnId") or "")

    order = get_order_by_merchant_txn(merchant_txn_id) if merchant_txn_id else None
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if status in {"success", "successful", "paid", "captured", "completed"}:
        mark_order_paid(order["order_id"], gateway_ref=gateway_ref, raw_status=status)
        paid = get_order(order["order_id"]) or order
        _fulfill_paid_order(paid)
    else:
        from backend.services.payment_service import update_order

        update_order(order["order_id"], status="failed", gateway_status=status, gateway_ref=gateway_ref)

    return {"ok": True}


@router.get("/orders/{order_id}")
def fetch_order(order_id: str, email: str = Depends(get_current_user)) -> dict:
    order = get_order(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if str(order.get("email", "")).lower() != email.lower():
        raise HTTPException(status_code=403, detail="Not your order")
    return {"order": order}
