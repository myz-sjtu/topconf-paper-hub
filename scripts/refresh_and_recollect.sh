#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DB_PATH="${TOPCONF_DB_PATH:-topconf_papers.db}"
BACKUP_DIR="${TOPCONF_BACKUP_DIR:-backups}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
TOPCONF_BIN=".venv/bin/topconf"

ACM_CONFERENCES=(
  SIGCOMM
  CoNEXT
  MobiCom
  IMC
  SIGMETRICS
  ISCA
  MICRO
  ASPLOS
  EuroSys
  KDD
)

OPENREVIEW_CONFERENCES=(
  ICLR
  NeurIPS
  ICML
)

CVF_CONFERENCES=(
  CVPR
  ICCV
)

USENIX_CONFERENCES=(
  NSDI
  FAST
)

conference_args() {
  local args=()
  for conference in "$@"; do
    args+=(--conference "$conference")
  done
  printf '%q ' "${args[@]}"
}

run_topconf() {
  echo
  echo "==> $TOPCONF_BIN $*"
  "$TOPCONF_BIN" "$@"
}

if [[ ! -x "$TOPCONF_BIN" ]]; then
  echo "==> Creating local virtual environment and installing project"
  "$PYTHON_BIN" -m venv .venv
  .venv/bin/pip install -e ".[dev]"
fi

if command -v lsof >/dev/null 2>&1 && [[ -f "$DB_PATH" ]]; then
  if lsof "$DB_PATH" >/dev/null 2>&1; then
    echo "ERROR: $DB_PATH is currently open by another process."
    echo "Stop the FastAPI server before refreshing the database, for example:"
    echo "  pkill -f 'uvicorn app.main:app'"
    echo
    echo "To bypass this guard intentionally, run:"
    echo "  TOPCONF_FORCE_REFRESH=1 $0"
    if [[ "${TOPCONF_FORCE_REFRESH:-0}" != "1" ]]; then
      exit 1
    fi
  fi
fi

mkdir -p "$BACKUP_DIR"
if [[ -f "$DB_PATH" ]]; then
  stamp="$(date +%Y%m%d-%H%M%S)"
  backup_path="$BACKUP_DIR/topconf_papers.$stamp.db"
  echo "==> Backing up existing database to $backup_path"
  cp "$DB_PATH" "$backup_path"
  for suffix in "-wal" "-shm"; do
    if [[ -f "$DB_PATH$suffix" ]]; then
      cp "$DB_PATH$suffix" "$backup_path$suffix"
    fi
  done
  echo "==> Removing existing database $DB_PATH"
  rm -f "$DB_PATH" "$DB_PATH-wal" "$DB_PATH-shm"
fi

echo "==> Initializing clean database"
run_topconf init-db

echo "==> Collecting strict DBLP baseline for all configured conferences, recent 5 years"
run_topconf crawl --source dblp

echo "==> Collecting ACM Digital Library metadata for ACM-backed conferences"
# shellcheck disable=SC2046
run_topconf crawl $(conference_args "${ACM_CONFERENCES[@]}") --source acm_dl

echo "==> Collecting OpenReview metadata for ICLR / NeurIPS / ICML"
# shellcheck disable=SC2046
run_topconf crawl $(conference_args "${OPENREVIEW_CONFERENCES[@]}") --source openreview

echo "==> Collecting CVF metadata for CVPR / ICCV"
# shellcheck disable=SC2046
run_topconf crawl $(conference_args "${CVF_CONFERENCES[@]}") --source cvf

echo "==> Collecting USENIX metadata for NSDI / FAST"
# shellcheck disable=SC2046
run_topconf crawl $(conference_args "${USENIX_CONFERENCES[@]}") --source usenix

echo "==> Enriching missing abstracts via OpenAlex DOI lookup"
run_topconf enrich-abstracts --batch-size 50 --delay-seconds 0.2

echo
echo "==> Final database summary"
.venv/bin/python scripts/summarize_database.py

echo
echo "Done. Start the dashboard with:"
echo "  cd $ROOT_DIR"
echo "  .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000"
