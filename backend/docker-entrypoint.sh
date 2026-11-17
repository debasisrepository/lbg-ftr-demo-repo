#!/bin/sh
set -e

# Run migrations
echo "Running database migrations..."
python -m alembic upgrade head

# Run seed data (idempotent - skips existing rows)
echo "Seeding database..."
python -m app.seed 2>/dev/null || true

# Execute CMD
exec "$@"
