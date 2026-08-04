from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import settings
from backend.services.pricing_catalog import CREDIT_PACKS, list_billable_plans, list_checkout_plans, resolve_checkout_plan_id

BILLABLE_PLANS: dict[str, dict[str, Any]] = {
    row["id"]: {
        "id": row["id"],
        "name": row["display_name"],
        "amount_paise": row["amount_paise"],
        "currency": "INR",
        "price_label": row["price_label"],
        "tagline": (row.get("perks") or [""])[0],
        "description": f"Monthly {row['display_name']} subscription",
    }
    for row in list_billable_plans()
}

BILLABLE_CREDIT_PACKS: dict[str, dict[str, Any]] = {
    pack["id"]: {
        **pack,
        "currency": "INR",
        "kind": "credit_pack",
        "description": f"{pack['credits']} IIDATECH credits",
    }
    for pack in CREDIT_PACKS
}


def _orders_path() -> Path:
    path = settings.outputs_root / "payment_orders.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _load_orders() -> dict[str, Any]:
    path = _orders_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _save_orders(orders: dict[str, Any]) -> None:
    _orders_path().write_text(json.dumps(orders, indent=2, ensure_ascii=False), encoding="utf-8")


def list_public_plans() -> list[dict[str, Any]]:
    return list_checkout_plans()


def get_billable_plan(plan_id: str) -> dict[str, Any] | None:
    resolved = resolve_checkout_plan_id(plan_id)
    return BILLABLE_PLANS.get(resolved)


def get_billable_credit_pack(pack_id: str) -> dict[str, Any] | None:
    return BILLABLE_CREDIT_PACKS.get(pack_id.strip().lower())


def create_order(*, email: str, plan_id: str, return_url: str, notify_url: str) -> dict[str, Any]:
    plan = get_billable_plan(plan_id)
    if not plan:
        raise ValueError("Unknown or non-billable plan")
    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    merchant_txn_id = f"IIDA{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    order = {
        "order_id": order_id,
        "merchant_txn_id": merchant_txn_id,
        "email": email.strip().lower(),
        "plan_id": plan["id"],
        "plan_name": plan["name"],
        "order_kind": "subscription",
        "amount_paise": plan["amount_paise"],
        "currency": plan["currency"],
        "status": "created",
        "return_url": return_url,
        "notify_url": notify_url,
        "created_at": now,
        "updated_at": now,
        "gateway_ref": "",
        "paid_at": "",
    }
    orders = _load_orders()
    orders[order_id] = order
    _save_orders(orders)
    return order


def create_credit_pack_order(*, email: str, pack_id: str, return_url: str, notify_url: str) -> dict[str, Any]:
    pack = get_billable_credit_pack(pack_id)
    if not pack:
        raise ValueError("Unknown credit pack")
    order_id = f"ord_{uuid.uuid4().hex[:16]}"
    merchant_txn_id = f"IIDA{uuid.uuid4().hex[:12].upper()}"
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    order = {
        "order_id": order_id,
        "merchant_txn_id": merchant_txn_id,
        "email": email.strip().lower(),
        "plan_id": pack["id"],
        "plan_name": f"{pack['credits']} credits",
        "order_kind": "credit_pack",
        "credit_pack_id": pack["id"],
        "credits_granted": pack["credits"],
        "amount_paise": pack["amount_paise"],
        "currency": pack["currency"],
        "status": "created",
        "return_url": return_url,
        "notify_url": notify_url,
        "created_at": now,
        "updated_at": now,
        "gateway_ref": "",
        "paid_at": "",
    }
    orders = _load_orders()
    orders[order_id] = order
    _save_orders(orders)
    return order


def get_order(order_id: str) -> dict[str, Any] | None:
    return _load_orders().get(order_id)


def get_order_by_merchant_txn(merchant_txn_id: str) -> dict[str, Any] | None:
    for order in _load_orders().values():
        if order.get("merchant_txn_id") == merchant_txn_id:
            return order
    return None


def update_order(order_id: str, **fields: Any) -> dict[str, Any] | None:
    orders = _load_orders()
    order = orders.get(order_id)
    if not order:
        return None
    order.update(fields)
    order["updated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    orders[order_id] = order
    _save_orders(orders)
    return order


def mark_order_paid(
    order_id: str,
    *,
    gateway_ref: str = "",
    raw_status: str = "",
) -> dict[str, Any] | None:
    order = get_order(order_id)
    if not order:
        return None
    if order.get("status") == "paid":
        return order
    return update_order(
        order_id,
        status="paid",
        gateway_ref=gateway_ref,
        gateway_status=raw_status,
        paid_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )
