#!/usr/bin/env bash
# Boot the backend service. For local development only.
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "Creating default .env from .env.example"
  cp .env.example .env
fi

python -m pip install -r backend/requirements.txt
python scripts/generate_demo_data.py --clear --scans 8

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload