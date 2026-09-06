#!/bin/sh
set -e

echo "Running Alembic migrations..."
alembic upgrade head || echo "Migration failed, continuing..."

if [ "${SEED_ON_START:-false}" = "true" ]; then
  echo "Running seed script..."
  python -m app.seed || echo "Seeding failed, continuing..."
fi

echo "Starting application..."
exec "$@"