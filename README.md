# IIDATECH production stack

Next.js founder product on Vercel + FastAPI backend reusing the existing `iidatech/` Python engine.

## Architecture

| Layer | Tech | Host |
|-------|------|------|
| Marketing + app UI | Next.js 15 | Vercel |
| API | FastAPI | Railway / Render / Fly |
| Research engine | iidatech Python package | Same host as API |

Streamlit is not used in this project.

## Local development

API:
```
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-api.txt
copy .env.example .env
uvicorn backend.main:app --reload --port 8000
```

Web:
```
cd web
npm install
npm run dev
```

Open http://localhost:3000

## Deploy (frontend + backend from this repo)

Two services, one GitHub repo: `vidhu-ops/business-os`

### 1. Frontend — Vercel

1. [vercel.com/new](https://vercel.com/new) → Import `vidhu-ops/business-os`
2. **Root Directory:** `web`
3. **Framework Preset:** Next.js (not FastAPI)
4. **Environment variable:** `API_URL` = your Render API URL (step 2 below)
5. Deploy

### 2. Backend — Render or Railway

**Render:** [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint** → connect repo (`render.yaml`).

**Railway:** [railway.app/new](https://railway.app/new) → **Deploy from GitHub** → `vidhu-ops/business-os`. Uses root `Dockerfile` + `railway.toml` automatically.

Set secret env vars on either platform: `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `JWT_SECRET`.

Copy the API URL, then set `CORS_ORIGINS` and `FRONTEND_URL` to your Vercel URL.

### 3. Wire them together

| Where | Variable | Value |
|-------|----------|-------|
| Vercel | `API_URL` | `https://business-os-api.onrender.com` |
| Render | `CORS_ORIGINS` | `https://your-app.vercel.app` |
| Render | `FRONTEND_URL` | `https://your-app.vercel.app` |

Vercel `*.vercel.app` preview URLs are allowed automatically by the API CORS config.

## Deploy on Replit

1. Import `vidhu-ops/business-os` on [replit.com](https://replit.com).
2. In **Secrets**, set optional keys (`JWT_SECRET`, `PERPLEXITY_API_KEY`, etc.). Leave **`API_URL`** as `http://127.0.0.1:8000` (default in `.replit`) so the Next.js proxy talks to the local FastAPI process.
3. Click **Run** (or deploy). Replit runs `scripts/build-replit.sh` then `scripts/start-replit.sh`, which starts:
   - FastAPI on `127.0.0.1:8000`
   - Next.js on `0.0.0.0:3000` (webview port)
4. Open the webview on port **3000**. API calls go to `/api/v1/*` and are proxied server-side to the local API.

**Verify:** In the Replit shell, `curl http://127.0.0.1:8000/api/v1/health` should return `{"status":"ok",...}`. In the browser, `/app/dashboard` should load without a "Not Found" session error.
