#!/usr/bin/env bash
set -euo pipefail

cd /app
export API_URL="${API_URL:-http://127.0.0.1:8000}"
export PYTHONPATH=/app
WEB_PORT="${PORT:-3000}"

if [ -n "${RENDER_EXTERNAL_URL:-}" ]; then
  export FRONTEND_URL="${FRONTEND_URL:-$RENDER_EXTERNAL_URL}"
  export CORS_ORIGINS="${CORS_ORIGINS:-$RENDER_EXTERNAL_URL}"
  export OAUTH_REDIRECT_URI="${OAUTH_REDIRECT_URI:-${FRONTEND_URL}/api/v1/oauth/callback}"
fi

if [ ! -f opportunity_workspaces/demo_readonly/workspace.json ]; then
  echo "Seeding demo_readonly workspace ..."
  python tools/assemble_demo.py || true
fi

echo "Starting IIDATECH API at ${API_URL} ..."
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 1 &
API_PID=$!

# Start Next.js in parallel once API process is up (don't wait for full cold import).
echo "Starting Next.js on port ${WEB_PORT} (API still warming) ..."
cd /app/web
env API_URL="$API_URL" npm run start -- --hostname 0.0.0.0 --port "${WEB_PORT}" &
WEB_PID=$!

cleanup() {
  kill "$API_PID" "$WEB_PID" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Waiting for API health check ..."
ready=0
for _ in $(seq 1 120); do
  if curl -fsS "${API_URL}/api/v1/health" >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! kill -0 "$API_PID" 2>/dev/null; then
    echo "API process exited before becoming ready." >&2
    wait "$API_PID" || true
    exit 1
  fi
  sleep 1
done

if [ "$ready" -ne 1 ]; then
  echo "API did not become ready at ${API_URL} within 120s." >&2
  exit 1
fi

echo "API ready. Combined stack is live."
wait "$WEB_PID"
