#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

DB_PATH="${TOPCONF_DB_PATH:-topconf_papers.db}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
REFRESH="${TOPCONF_REFRESH:-auto}"
SKIP_EMPTY_CHECK="${TOPCONF_SKIP_EMPTY_CHECK:-0}"
TOPCONF_BIN=".venv/bin/topconf"

truthy() {
  case "${1:-}" in
    1|true|TRUE|yes|YES|on|ON) return 0 ;;
    *) return 1 ;;
  esac
}

if [[ ! -x ".venv/bin/python" ]]; then
  echo "==> Creating local Python environment"
  "$PYTHON_BIN" -m venv .venv
fi

if [[ ! -x "$TOPCONF_BIN" ]]; then
  echo "==> Installing Python project"
  .venv/bin/pip install -e ".[dev]"
fi

should_refresh=0
if truthy "$REFRESH"; then
  should_refresh=1
elif [[ "$REFRESH" == "auto" && ! -f "$DB_PATH" ]]; then
  should_refresh=1
fi

if [[ "$should_refresh" == "1" ]]; then
  echo "==> Refreshing database before static export"
  TOPCONF_FORCE_REFRESH="${TOPCONF_FORCE_REFRESH:-1}" ./scripts/refresh_and_recollect.sh
else
  echo "==> Reusing existing database at $DB_PATH"
fi

echo "==> Auditing venue assignments before static export"
.venv/bin/python scripts/audit_and_clean_database.py

export_args=()
if truthy "$SKIP_EMPTY_CHECK"; then
  export_args+=(--skip-empty-check)
fi

echo "==> Exporting JSON and Markdown for VitePress"
if [[ "${#export_args[@]}" -gt 0 ]]; then
  .venv/bin/python scripts/export_static_site.py "${export_args[@]}"
else
  .venv/bin/python scripts/export_static_site.py
fi

echo
echo "Static data is ready. Build the site with:"
echo "  npm install"
echo "  npm run docs:build"
