# Deploy IIDATECH on Render (one URL)

This repo ships **one Docker image** that runs:

- **FastAPI** on `127.0.0.1:8000` (internal)
- **Next.js** on Render PORT (public URL)

The browser uses a single origin. `/api/v1/*` is proxied server-side to the local API.

## Option A - Blueprint (recommended)

1. Open https://dashboard.render.com
2. New + -> Blueprint
3. Connect GitHub repo `vidhu-ops/business-os`
4. Render reads `render.yaml` and creates one Web Service using `Dockerfile.combined`
5. Set env vars when prompted:
   - PERPLEXITY_API_KEY
   - CORS_ORIGINS = your Render URL (e.g. https://business-os.onrender.com)
   - FRONTEND_URL = same Render URL
6. Deploy (first build may take 10-20 minutes)

## Option B - Manual Web Service

1. New + -> Web Service -> connect repo
2. Environment: Docker
3. Dockerfile Path: Dockerfile.combined
4. Health Check Path: /api/v1/health
5. Env vars:
   - API_URL = http://127.0.0.1:8000
   - JWT_SECRET = random string
   - PERPLEXITY_API_KEY = your key
   - CORS_ORIGINS and FRONTEND_URL = your Render URL

## After deploy

- Open your Render URL - you should see the marketing home page (not JSON)
- Click Start now -> dashboard
- Health: https://YOUR-SERVICE.onrender.com/api/v1/health

## Railway

Deploy from GitHub; uses railway.toml + Dockerfile.combined. Add same env vars.

## Troubleshooting

- JSON at root URL: wrong Dockerfile - use Dockerfile.combined not Dockerfile
- Not Found on /app: check Logs for API startup errors
- Research fails: add PERPLEXITY_API_KEY