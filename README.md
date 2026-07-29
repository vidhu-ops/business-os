# IIDATECH Business OS

One GitHub repo: **Next.js UI + FastAPI + iidatech research engine**.

## Quick deploy (one URL)

**Render:** connect `vidhu-ops/business-os` → Blueprint or Web Service. Uses root **`Dockerfile`** (Next.js UI + API in one container).

Full steps: **[docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md)**

> If you see JSON `{"service":"iidatech-api"...}` at your URL, the service is using the **old API-only** deploy. Redeploy from latest `main` (root `Dockerfile` is now the full app).

| Platform | Config | Result |
|----------|--------|--------|
| **Render** | `render.yaml` + `Dockerfile` | One URL, UI + API |
| **Railway** | `railway.toml` + `Dockerfile` | One URL, UI + API |
| **Replit** | `.replit` + `scripts/start-replit.sh` | One Repl, UI + API |

---

## Architecture

| Layer | Tech |
|-------|------|
| Marketing + app UI | Next.js 16 (`web/`) |
| API | FastAPI (`backend/`) |
| Research engine | `iidatech/` Python package |

In the combined Docker image, Next.js proxies `/api/v1/*` to FastAPI on `127.0.0.1:8000`.

---

## Local development

```powershell
cd c:\path\to\business-os
.\scripts\dev_start.ps1
```

- Web: http://localhost:3000  
- API: http://127.0.0.1:8000  

Or manually:

```powershell
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

```powershell
cd web
npm install
npm run dev
```

Copy `.env.example` → `.env` and set `PERPLEXITY_API_KEY`, `JWT_SECRET`.

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `JWT_SECRET` | Yes (prod) | Auth token signing |
| `PERPLEXITY_API_KEY` | For research | Perplexity API |
| `API_URL` | Combined deploy | `http://127.0.0.1:8000` (default in Docker) |
| `CORS_ORIGINS` | Prod | Your public app URL |
| `FRONTEND_URL` | Prod | Same as `CORS_ORIGINS` on single-URL deploy |
| `ANTHROPIC_API_KEY` | Optional | Anthropic models |
| `OPENAI_API_KEY` | Optional | OpenAI models |

---

## Split deploy (optional)

If you prefer Vercel for frontend + Render for API only:

1. **Vercel:** root directory `web`, set `API_URL` to your Render API URL
2. **Render:** use `Dockerfile` or `Dockerfile.api` (API only)

See [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) for the combined (one-URL) path.

---

## Replit

1. Import `vidhu-ops/business-os`
2. Secrets: `JWT_SECRET`, `PERPLEXITY_API_KEY`
3. Leave `API_URL` unset (defaults to `http://127.0.0.1:8000`)
4. Run — opens Next.js on port 3000

---

## Repo layout

```
business-os/
├── web/                 # Next.js frontend
├── backend/             # FastAPI routes
├── iidatech/            # Research & execution engine
├── Dockerfile.combined  # One-image deploy (Render/Railway)
├── render.yaml          # Render Blueprint
├── railway.toml         # Railway config
└── scripts/
    ├── dev_start.ps1
    ├── start-replit.sh
    └── render-combined-start.sh
```
