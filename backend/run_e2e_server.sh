#!/bin/bash
set -e

echo "=== E2E Server Setup ==="
echo "DATABASE_URL: $DATABASE_URL"
echo "E2E_BACKEND_PORT: $E2E_BACKEND_PORT"

# Delete old database if it exists
if [ -f "e2e.db" ]; then
    echo "Removing old e2e.db"
    rm -f e2e.db e2e.db-shm e2e.db-wal
fi

# Run migrations
echo "Running migrations..."
.venv/bin/python -m alembic upgrade head

# Run seed
echo "Running seed..."
.venv/bin/python -m app.seed

# Verify seed data
echo "Verifying seed data..."
.venv/bin/python -c "
from app.database import SessionLocal
from app.models import DeviceRegistration
db = SessionLocal()
count = db.query(DeviceRegistration).count()
print(f'Device count: {count}')
db.close()
"

# Start server
echo "Starting server on port ${E2E_BACKEND_PORT:-9000}..."
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port "${E2E_BACKEND_PORT:-9000}"
