#!/usr/bin/env bash
# ============================================================
# Entrypoint: ensure the SQLite schema exists before PHP serves
# requests (api.php?action=data queries the `tweets` table, which
# only exists after DBManager.init_db runs). Idempotent — safe on
# every start because CREATE TABLE IF NOT EXISTS.
# ============================================================
set -euo pipefail

DB_PATH="${DB_PATH:-data/database.sqlite}"

echo "[entrypoint] Initializing database schema at ${DB_PATH} ..."
python - <<PY
from src.database.db_manager import DBManager
DBManager("${DB_PATH}")
print("[entrypoint] DB ready.")
PY

echo "[entrypoint] Starting: $*"
exec "$@"
