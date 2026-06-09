#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [[ ! -x ".venv/bin/topconf" ]]; then
  echo "Missing .venv/bin/topconf. Run scripts/refresh_and_recollect.sh or install the project first."
  exit 1
fi

echo "==> Enriching missing abstracts via OpenAlex DOI lookup"
.venv/bin/topconf enrich-abstracts --batch-size 50 --delay-seconds 0.2

echo
echo "==> Database summary"
.venv/bin/python scripts/summarize_database.py

