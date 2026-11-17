#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Seeding database..."
python -c "from app.seed import seed_data; seed_data()" || true

exec "$@"
