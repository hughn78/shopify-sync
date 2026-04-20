#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
FRONTEND="$ROOT/frontend"
BACKEND="$ROOT/backend"
STATIC="$BACKEND/app/static"

# Build frontend if: no build exists, or --build flag passed, or source is newer than build
needs_build=false
if [ ! -f "$STATIC/index.html" ]; then
  needs_build=true
elif [ "${1:-}" = "--build" ]; then
  needs_build=true
elif [ -n "$(find "$FRONTEND/src" -newer "$STATIC/index.html" -name '*.ts' -o -name '*.tsx' -o -name '*.css' 2>/dev/null | head -1)" ]; then
  needs_build=true
fi

if $needs_build; then
  echo "Building frontend..."
  cd "$FRONTEND"
  if [ ! -d node_modules ]; then
    npm install --silent
  fi
  npm run build
  echo "Frontend built."
fi

echo ""
echo "  App: http://127.0.0.1:8000"
echo "  API: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop."
echo ""

cd "$BACKEND"
source .venv/bin/activate
alembic upgrade head
exec uvicorn app.main:app --host 127.0.0.1 --port 8000
