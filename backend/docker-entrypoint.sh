#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python -c "from app.seed import seed_database; seed_database()" 2>/dev/null || true

echo "Starting application..."
exec "$@"
