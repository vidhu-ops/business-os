# Deploy IIDATECH on Render (one URL)

This repo ships a **combined Docker image**: FastAPI on `127.0.0.1:8000` + Next.js on Render `PORT`.

## Auto-deploy from GitHub

1. Connect repo **`vidhu-ops/iida-final-vercel`** (branch **`main`**) to Render service **business-os-2**.
2. Use root **`Dockerfile`** and **`render.yaml`**.
3. Push to **`main`** — Render rebuilds if auto-deploy is enabled; otherwise **Manual Deploy** in the dashboard.

## Custom domain `iidatech.com` (required)

**DNS:** See **[docs/DNS_IIDATECH_COM.md](DNS_IIDATECH_COM.md)** (Render custom domain + GoDaddy CNAME). Do not attach **iidatech.biz** to this service.

**Render env (Dashboard → Environment):**

| Variable | Value |
|----------|--------|
| `PUBLIC_APP_URL` | `https://iidatech.com` |
| `NEXT_PUBLIC_SITE_URL` | `https://iidatech.com` |
| `OAUTH_REDIRECT_URI` | `https://iidatech.com/api/v1/oauth/callback` |

Or click **Sync** from Blueprint after updating `render.yaml`.

## Environment variables

**Set automatically on startup** (no manual work):

- `FRONTEND_URL` ← `RENDER_EXTERNAL_URL`
- `CORS_ORIGINS` ← same public URL
- `OAUTH_REDIRECT_URI` ← `{FRONTEND_URL}/api/v1/oauth/callback`

**You must set once in Render → Environment** (Dashboard → your service → Environment):

| Variable | Required for |
|----------|----------------|
| `DATABASE_URL` | **Durable signup/login** (Neon Postgres). Without this or a disk, accounts vanish on redeploy. |
| `DATA_DIR` | Optional alternative: `/var/data` when a Render disk is attached (Starter+) |
| `PERPLEXITY_API_KEY` | Market research, leads |
| `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` | Business plan, Employee OS agents |
| `ZO_API_KEY` | Plan It Out / Business Plan hub (optional if using other keys) |
| `ADMIN_EMAIL` | Admin CRM/analytics sign-in and partner notifications (`admin@iidatech.com`) |
| `PARTNER_ADMIN_KEY` | Approve service providers (`X-Admin-Key` header) |
| `GMAIL_SMTP_USER` / `GMAIL_SMTP_PASSWORD` | Optional — email notifications for new partner signups |
| `SLACK_WEBHOOK_URL` | Optional — Slack alerts for new partner signups |

### Durable auth (required for production)

Render’s free container disk is wiped on every deploy. To keep accounts and projects:

1. **Preferred (free):** create a Neon Postgres DB and set `DATABASE_URL` on Render, **or**
2. **Disk:** upgrade to Starter, attach a disk at `/var/data`, set `DATA_DIR=/var/data`.

After `DATABASE_URL` is set, signup/login stores users + project index in Postgres so sign-in survives redeploys.

**Payments (Freecharge):**

| Variable | Required for |
|----------|----------------|
| `FREECHARGE_MERCHANT_ID` | Merchant ID from Freecharge onboarding |
| `FREECHARGE_SECRET_KEY` | Signing secret from welcome email |
| `FREECHARGE_AES_KEY` | AES-256 encryption key (from FCPG key exchange) |
| `FREECHARGE_MODE` | `sandbox` (test) or `production` (live) |
| `FREECHARGE_AES_IV` | Optional IV if provided by FCPG |

Webhook URL to register in Freecharge merchant portal:
`https://YOUR-SERVICE.onrender.com/api/v1/payments/webhook/freecharge`

Return URL (auto-built): `https://YOUR-SERVICE.onrender.com/payment/callback?order_id=...`

`JWT_SECRET` is auto-generated from `render.yaml`.

## Health check

`https://YOUR-SERVICE.onrender.com/api/v1/health` → `{"status":"ok"}`

## OAuth (optional)

Register this redirect URL in Google / LinkedIn / HubSpot developer consoles:

`https://YOUR-SERVICE.onrender.com/api/v1/oauth/callback`

## Canva Connect (platform service account)

For production at `https://iidatech.com`, register this redirect URL in the [Canva Developer Portal](https://www.canva.com/developers/):

`https://iidatech.com/api/v1/oauth/callback`

| Variable | Required for |
|----------|----------------|
| `CANVA_CLIENT_ID` | Canva Connect OAuth |
| `CANVA_CLIENT_SECRET` | Canva Connect OAuth |
| `CANVA_USE_SERVICE_ACCOUNT` | Set to `true` so all users share the IIDATECH platform Canva (no per-user OAuth) |
| `CANVA_REFRESH_TOKEN` | Optional but recommended — persists tokens across Render redeploys |
| `PARTNER_ADMIN_KEY` | One-time admin connect and status checks |

| **One-time admin connect** (use setup wizard if Canva says "update browser"):

`https://iidatech.com/api/v1/canva/admin/setup?key=PARTNER_ADMIN_KEY`

On the setup page: copy the Canva link and open it in **Chrome on your phone** (not Cursor or embedded browsers).

After OAuth completes, copy the refresh token into Render as `CANVA_REFRESH_TOKEN`. Without it, tokens are stored on the container filesystem and are lost on redeploy.

**Admin status check:**

`https://iidatech.com/api/v1/canva/admin/status?key=PARTNER_ADMIN_KEY`

## Free tier cold starts

Render **Free** services spin down after ~15 minutes without traffic; the next visit can take **30–90s**. Upgrade to **Starter** in Render for always-on, or accept occasional cold starts. There is **no** keep-warm GitHub Action in this repo.

## Custom domain (`iidatech.com`) not loading

Follow **[docs/DNS_IIDATECH_COM.md](DNS_IIDATECH_COM.md)** (Render custom domain first, then GoDaddy DNS). Remove **iidatech.biz** from Render custom domains on this service. Until DNS propagates, `https://business-os-2.onrender.com` still serves the app.

## Troubleshooting

- **Cold start / ~1 min load**: Free tier slept; upgrade to Starter or wait for the container to wake.
- **Research timeout**: Ensure `PERPLEXITY_API_KEY` is set on the server.
- **Employee OS**: Add LLM key under **Integrations** in the app, or set `OPENAI_API_KEY` in Render env.
