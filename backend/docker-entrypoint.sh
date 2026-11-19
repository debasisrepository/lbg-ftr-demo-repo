#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Loading seed data..."
python -m app.seed

echo "Starting application..."
exec "$@"
