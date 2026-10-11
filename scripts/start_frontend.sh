#!/usr/bin/env bash
# Boot the frontend dev server.
set -euo pipefail
cd "$(dirname "$0")/../frontend"
npm install
exec npm run dev