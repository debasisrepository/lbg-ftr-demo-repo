#!/bin/sh
# Backend docker entrypoint — runs migrations and seed before starting server
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python app/seed.py 2>/dev/null || true

echo "Starting backend server..."
exec "$@"
