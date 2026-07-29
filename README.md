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

## Deploy

Vercel: import repo, set Root Directory to `web`, add `API_URL` env var.

API: deploy repo root on Railway/Render with `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
