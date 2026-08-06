# Deploy IIDATECH on Render (one URL)

This repo ships a **combined Docker image**: FastAPI on `127.0.0.1:8000` + Next.js on Render `PORT`.

## Auto-deploy from GitHub

1. Connect repo `vidhu-ops/business-os` to Render (Blueprint or Web Service).
2. Use root `Dockerfile` and `render.yaml`.
3. Push to `main` — Render rebuilds automatically.

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
| `ADMIN_EMAIL` | Partner application notifications |
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

For production at `https://iidatech.biz`, register this redirect URL in the [Canva Developer Portal](https://www.canva.com/developers/):

`https://iidatech.biz/api/v1/oauth/callback`

| Variable | Required for |
|----------|----------------|
| `CANVA_CLIENT_ID` | Canva Connect OAuth |
| `CANVA_CLIENT_SECRET` | Canva Connect OAuth |
| `CANVA_USE_SERVICE_ACCOUNT` | Set to `true` so all users share the IIDATECH platform Canva (no per-user OAuth) |
| `CANVA_REFRESH_TOKEN` | Optional but recommended — persists tokens across Render redeploys |
| `PARTNER_ADMIN_KEY` | One-time admin connect and status checks |

| **One-time admin connect** (use setup wizard if Canva says "update browser"):

`https://iidatech.biz/api/v1/canva/admin/setup?key=PARTNER_ADMIN_KEY`

On the setup page: copy the Canva link and open it in **Chrome on your phone** (not Cursor or embedded browsers).

After OAuth completes, copy the refresh token into Render as `CANVA_REFRESH_TOKEN`. Without it, tokens are stored on the container filesystem and are lost on redeploy.

**Admin status check:**

`https://iidatech.biz/api/v1/canva/admin/status?key=PARTNER_ADMIN_KEY`

## Keep warm (avoid cold starts)

Render **Free** web services spin down after ~15 minutes with no traffic. The next
visit then takes ~30–90s while the container cold-starts. That is platform behavior,
not an app bug.

### Why the GitHub ping alone fails

The repo Action (`.github/workflows/keep-warm.yml`) pings every **5 minutes**, but
GitHub’s scheduled cron often runs late or skips. If any gap exceeds ~15 minutes,
Render sleeps again.

### What actually works (pick one)

| Option | Cost | Reliability |
|--------|------|-------------|
| **1. Upgrade Render instance → Starter** | ~$7/mo | Best. Paid instances **do not** spin down. |
| **2. External 5‑min monitor (UptimeRobot / cron-job.org)** | Free | Good. More reliable than GitHub Actions. |
| **3. GitHub Keep warm Action only** | Free | Weak. Use as backup only. |

**Also:** Free workspaces get ~**750 instance hours/month**. Keeping the box warm
24/7 uses most of that (~720h). If hours run out, Render suspends Free services
until next month — another reason Starter is better for a real product.

### Setup (recommended free path)

1. Create a monitor at [UptimeRobot](https://uptimerobot.com/) (or [cron-job.org](https://cron-job.org/)):
   - URL: `https://iidatech.biz/api/health?warm=1`
   - Interval: **every 5 minutes**
   - Type: HTTP(s)
2. Confirm **Actions → Keep warm** is enabled on the deploy repo (backup ping).
3. Optional repo variable `KEEP_WARM_URL` overrides the default `https://iidatech.biz`.

### Setup (always-on)

In the Render dashboard → your web service → **Instance type** → change **Free → Starter**.
No redeploy required. Cold starts stop.

Local loop while developing:

```powershell
powershell -File scripts/keep-warm.ps1
```

## Troubleshooting

- **Cold start / ~1 min load**: Free tier slept. Add UptimeRobot (5 min) or upgrade to Starter.
- **Research timeout**: Ensure `PERPLEXITY_API_KEY` is set on the server.
- **Employee OS**: Add LLM key under **Integrations** in the app, or set `OPENAI_API_KEY` in Render env.
