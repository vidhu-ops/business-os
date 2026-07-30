# Freecharge Payment Gateway

IIDATECH uses [Freecharge Payment Gateway](https://www.freechargepg.in/developer) for Growth plan checkout (INR 4,999/month).

## Flow

1. User opens `/pricing` -> **Start Growth** -> `/checkout?plan=growth` (login required).
2. Backend creates an order in `business_build_outputs/payment_orders.json`.
3. Browser POSTs `merchantId` + `encData` to Freecharge checkout.
4. Freecharge redirects to `/payment/callback?order_id=...`.
5. Freecharge server webhook hits `/api/v1/payments/webhook/freecharge` -> plan upgraded to **growth**.

## Environment variables

| Variable | Description |
|----------|-------------|
| `FREECHARGE_MODE` | `sandbox` or `production` |
| `FREECHARGE_MERCHANT_ID` | Merchant ID from onboarding |
| `FREECHARGE_SECRET_KEY` | Signing secret from welcome email |
| `FREECHARGE_AES_KEY` | AES-256 key (hex, base64, or raw 16/24/32 bytes) |
| `FREECHARGE_AES_IV` | Optional 16-byte IV if FCPG provides one |

## URLs to register with Freecharge

- **Return URL:** `https://YOUR-DOMAIN/payment/callback`
- **Webhook / notify URL:** `https://YOUR-DOMAIN/api/v1/payments/webhook/freecharge`

On Render, use your public service URL (same host serves API + Next.js).

## Sandbox

- Base: `https://sandbox-axispg.freecharge.in`
- Checkout: `POST /payment/v1/checkout`

## When you receive API kit details

Share the official payload field names, signature algorithm, and webhook sample. We can align `freecharge_service.py` and the webhook status mapping.

Support: spg.support@freecharge.com