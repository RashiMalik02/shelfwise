#!/bin/sh
set -eu

# Migrations run on every start. env.py holds a Postgres advisory lock, so
# several replicas starting together will queue up instead of colliding.
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  echo "entrypoint: applying database migrations"
  alembic upgrade head
fi

if [ "${SEED_DEMO_DATA:-false}" = "true" ]; then
  python -m app.seed
fi

exec "$@"
