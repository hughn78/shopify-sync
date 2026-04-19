#!/usr/bin/env bash
set -euo pipefail

ROOT="/Volumes/1TB-SSD/OpenClaw-Workspace/Shopify_Barcodes"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

cleanup() {
  echo
  echo "Shutting down..."
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting backend on http://127.0.0.1:8000"
(
  cd "$BACKEND"
  source .venv/bin/activate
  alembic upgrade head
  exec uvicorn app.main:app --host 127.0.0.1 --port 8000
) &

BACKEND_PID=$!

echo "Starting frontend on http://127.0.0.1:5173"
(
  cd "$FRONTEND"
  if [ ! -d node_modules ]; then
    npm install
  fi
  exec npm run dev -- --host 127.0.0.1 --port 5173
) &

FRONTEND_PID=$!

echo
printf 'Frontend: http://127.0.0.1:5173\nBackend:  http://127.0.0.1:8000\nDocs:     http://127.0.0.1:8000/docs\n\n'

echo "Press Ctrl+C to stop both services."
wait "$BACKEND_PID" "$FRONTEND_PID"
