from __future__ import annotations

import hashlib
import json
import os
from base64 import b64decode, b64encode
from datetime import datetime, timezone
from typing import Any

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.padding import PKCS7

SANDBOX_BASE = "https://sandbox-axispg.freecharge.in"
PRODUCTION_BASE = "https://secure-axispg.freecharge.in"
CHECKOUT_PATH = "/payment/v1/checkout"


def _mode() -> str:
    return (os.getenv("FREECHARGE_MODE") or "sandbox").strip().lower()


def is_configured() -> bool:
    return bool(
        (os.getenv("FREECHARGE_MERCHANT_ID") or "").strip()
        and (os.getenv("FREECHARGE_SECRET_KEY") or "").strip()
        and (os.getenv("FREECHARGE_AES_KEY") or "").strip()
    )


def gateway_info() -> dict[str, Any]:
    mode = _mode()
    return {
        "provider": "freecharge",
        "configured": is_configured(),
        "mode": mode,
        "checkout_path": CHECKOUT_PATH,
    }


def _base_url() -> str:
    return PRODUCTION_BASE if _mode() == "production" else SANDBOX_BASE


def _merchant_id() -> str:
    return (os.getenv("FREECHARGE_MERCHANT_ID") or "").strip()


def _secret_key() -> str:
    return (os.getenv("FREECHARGE_SECRET_KEY") or "").strip()


def _aes_key_bytes() -> bytes:
    raw = (os.getenv("FREECHARGE_AES_KEY") or "").strip()
    if not raw:
        raise ValueError("FREECHARGE_AES_KEY is not set")
    try:
        decoded = b64decode(raw)
        if len(decoded) in (16, 24, 32):
            return decoded
    except Exception:
        pass
    key = raw.encode("utf-8")
    if len(key) in (16, 24, 32):
        return key
    return hashlib.sha256(key).digest()


def _aes_iv_bytes() -> bytes:
    raw = (os.getenv("FREECHARGE_AES_IV") or "").strip()
    if raw:
        try:
            decoded = b64decode(raw)
            if len(decoded) == 16:
                return decoded
        except Exception:
            pass
        iv = raw.encode("utf-8")
        if len(iv) == 16:
            return iv
    return b"\x00" * 16


def _sign_payload(payload: dict[str, Any]) -> str:
    secret = _secret_key()
    parts = [str(payload[key]) for key in sorted(payload.keys()) if payload[key] is not None]
    canonical = "|".join(parts) + "|" + secret
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _encrypt(plain_text: str) -> str:
    key = _aes_key_bytes()
    iv = _aes_iv_bytes()
    padder = PKCS7(128).padder()
    padded = padder.update(plain_text.encode("utf-8")) + padder.finalize()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    encrypted = encryptor.update(padded) + encryptor.finalize()
    return b64encode(encrypted).decode("ascii")


def _decrypt(enc_data: str) -> str:
    key = _aes_key_bytes()
    iv = _aes_iv_bytes()
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(b64decode(enc_data)) + decryptor.finalize()
    unpadder = PKCS7(128).unpadder()
    plain = unpadder.update(decrypted) + unpadder.finalize()
    return plain.decode("utf-8")


def build_checkout_request(
    *,
    merchant_txn_id: str,
    amount_paise: int,
    currency: str,
    customer_email: str,
    return_url: str,
    notify_url: str,
    description: str = "",
) -> dict[str, Any]:
    if not is_configured():
        raise ValueError("Freecharge gateway is not configured")
    amount_rupees = f"{amount_paise / 100:.2f}"
    payload: dict[str, Any] = {
        "merchantId": _merchant_id(),
        "merchantTxnId": merchant_txn_id,
        "amount": amount_rupees,
        "currencyCode": currency,
        "customerEmail": customer_email,
        "returnUrl": return_url,
        "notifyUrl": notify_url,
        "txnDate": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "txnNote": description or "IIDATECH subscription",
    }
    payload["signature"] = _sign_payload(payload)
    enc_data = _encrypt(json.dumps(payload, separators=(",", ":"), ensure_ascii=False))
    checkout_url = f"{_base_url()}{CHECKOUT_PATH}"
    return {
        "checkout_url": checkout_url,
        "merchant_id": _merchant_id(),
        "enc_data": enc_data,
        "fields": {
            "merchantId": _merchant_id(),
            "encData": enc_data,
        },
    }


def parse_webhook_payload(body: dict[str, Any]) -> dict[str, Any]:
    enc_data = str(body.get("encData") or body.get("enc_data") or "").strip()
    if not enc_data:
        raise ValueError("Missing encData in webhook")
    plain = _decrypt(enc_data)
    data = json.loads(plain)
    if not isinstance(data, dict):
        raise ValueError("Invalid decrypted webhook payload")
    signature = str(data.pop("signature", "") or "")
    expected = _sign_payload(data)
    if signature and signature.lower() != expected.lower():
        raise ValueError("Webhook signature mismatch")
    return data
