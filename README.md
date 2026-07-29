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

### 2. Backend — Render

1. [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**
2. Connect `vidhu-ops/business-os` (uses `render.yaml` in repo)
3. Set secret env vars: `PERPLEXITY_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
4. Copy the service URL (e.g. `https://business-os-api.onrender.com`)
5. Set `CORS_ORIGINS` and `FRONTEND_URL` to your Vercel URL

### 3. Wire them together

| Where | Variable | Value |
|-------|----------|-------|
| Vercel | `API_URL` | `https://business-os-api.onrender.com` |
| Render | `CORS_ORIGINS` | `https://your-app.vercel.app` |
| Render | `FRONTEND_URL` | `https://your-app.vercel.app` |

Vercel `*.vercel.app` preview URLs are allowed automatically by the API CORS config.
