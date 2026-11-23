# LBG FTR Demo Backend

Release 1 Mobile Banking Platform Backend API

## Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install .

# Copy environment file
cp dev.env .env

# Run database migrations
alembic upgrade head

# Seed database with synthetic data
python -c "from app.seed import seed_database; from app.database import SessionLocal; db = SessionLocal(); seed_database(db); db.close()"
```

## Running

```bash
# Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_smoke.py -v
```

## Type Checking

```bash
mypy app --ignore-missing-imports
```

## Seed Credentials

After running the seed script, use these credentials:

- **Customer 1**: Alex Taylor
  - Passcode: `Pass1234`
  
- **Customer 2**: Jordan Smith
  - Passcode: `Pass5678`

## Project Structure

```
backend/
├── app/
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic request/response schemas
│   ├── repositories/    # Data access layer
│   ├── services/        # Business logic
│   ├── routers/         # FastAPI route handlers
│   ├── middleware/      # Middleware components
│   ├── adapters/        # External service adapters
│   ├── config.py        # Configuration
│   ├── database.py      # Database setup
│   ├── main.py          # FastAPI application
│   └── seed.py          # Seed data script
├── alembic/             # Database migrations
├── tests/               # Test suite
├── workers/             # Background workers
└── pyproject.toml       # Project dependencies
```

## Database Schema

The application uses SQLAlchemy 2.0 with support for both SQLite (local development) and PostgreSQL (production).

All 23 database tables are defined in `app/models/`:
- Authentication: customer_profile_refs, sandbox_credentials, sandbox_entitlements, device_registrations, user_sessions, authentication_events
- Entitlement: entitlement_decisions
- Accounts: account_read_models, read_model_freshness_records
- Payments: payment_intents, payment_state_transitions, dynamic_link_approvals, scam_check_outcomes, payment_execution_statuses, idempotency_records, payment_outbox_events, payment_status_projections
- Payees: payees
- Status: capability_status_records
- Notifications: notification_trigger_records, notification_delivery_attempts
- Events: consumed_events
- Audit: audit_events

## API Endpoints

Currently implemented:
- `GET /health` - Health check
- `GET /health/ready` - Readiness check

Feature endpoints will be added by subsequent tasks.

## Development Notes

- Use sync SQLAlchemy (not async)
- bcrypt cost factor: 12
- All timestamps in UTC
- Idempotent seed data
- Rate limiting can be disabled via `RATE_LIMIT_ENABLED=false`
