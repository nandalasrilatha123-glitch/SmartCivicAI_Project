#!/bin/sh
# Waits for Postgres to accept connections, runs Alembic migrations, then
# hands off to whatever CMD was passed (uvicorn by default). Also seeds
# demo data on first boot if SEED_ON_START=true and the database looks empty.
set -e

DB_HOST="${DB_HOST:-db}"
DB_PORT="${DB_PORT:-5432}"

echo "Waiting for Postgres at ${DB_HOST}:${DB_PORT}..."
attempt=0
until python -c "
import socket, sys
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(2)
try:
    s.connect(('${DB_HOST}', ${DB_PORT}))
    sys.exit(0)
except Exception:
    sys.exit(1)
"; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "Postgres did not become available in time — check the db service logs."
    exit 1
  fi
  sleep 2
done
echo "Postgres is up."

echo "Running Alembic migrations..."
alembic upgrade head

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "SEED_ON_START=true — running seed script. NOTE: accounts/modules/departments"
  echo "are idempotent, but this APPENDS a fresh batch of demo complaints every time"
  echo "it runs — only enable this for a one-off first boot, not on every restart."
  python -m app.seed || echo "Seeding failed — continuing startup anyway."
fi

echo "Starting: $*"
exec "$@"
