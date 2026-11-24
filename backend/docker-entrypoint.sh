#!/bin/sh
set -e

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Run seed data
echo "Seeding database..."
python app/cli.py seed

# Execute the CMD (uvicorn server)
exec "$@"
