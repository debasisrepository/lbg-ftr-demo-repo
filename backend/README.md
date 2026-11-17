# Clear Path Backend

FastAPI-based backend service for the Clear Path MVP.

## Architecture

### Core Components

- **FastAPI Application**: RESTful API with OpenAPI documentation
- **SQLAlchemy ORM**: Sync database operations with Alembic migrations
- **Event System**: Domain events with outbox pattern for reliable dispatch
- **Policy Engine**: Deterministic autonomy enforcement (L0-L3)
- **Agent Layer**: Intake & Triage, Case Owner, Colleague Copilot, Guardrail Supervisor
- **Tool Layer**: Eight bounded tools with policy approval and SCA verification
- **Adapter Layer**: Seven system adapters for external integrations

### Module Structure

```
app/
├── agents/           # AI agent implementations
├── adapters/         # External system adapters (A1-A7)
├── api/              # API routers (auth, my_cases, colleague)
├── auth/             # Authentication & authorization
├── core/             # Core utilities (clock, IDs, errors, context)
├── events/           # Event publishing & dispatch
├── middleware/       # Request middleware (correlation, auth, errors)
├── services/         # Business logic services
│   ├── audit/        # Audit logging with hash chaining
│   ├── case/         # Case management service
│   ├── heartbeat/    # Heartbeat monitoring
│   ├── notification/ # Notification dispatch
│   ├── orchestrator/ # Orchestration engine
│   ├── policy/       # Policy evaluation
│   └── redaction/    # Redaction boundary
├── tools/            # Bounded tool implementations
├── database.py       # Database configuration
├── main.py           # FastAPI application
└── seed.py           # Seed data
```

## Setup

### Prerequisites

- Python 3.11+
- pip

### Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install .

# For PostgreSQL support
pip install ".[postgres]"
```

### Database Setup

```bash
# Copy dev.env to .env (if not exists)
cp dev.env .env

# Run migrations
python -m alembic upgrade head

# Seed database
python -c "from app.seed import seed_all; from app.database import SessionLocal; seed_all(SessionLocal())"
```

### Running

```bash
# Development with auto-reload
uvicorn app.main:app --reload --port 9000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 9000
```

### API Documentation

Once running, access:
- Swagger UI: http://localhost:9000/docs
- ReDoc: http://localhost:9000/redoc
- OpenAPI JSON: http://localhost:9000/openapi.json

## Testing

```bash
# Run all tests
pytest -v

# Run specific test file
pytest tests/test_my_cases_api.py -v

# Run with coverage
pytest --cov=app --cov-report=html

# Type checking
mypy app --ignore-missing-imports
```

## Database Migrations

```bash
# Create new migration
python -m alembic revision --autogenerate -m "description"

# Apply migrations
python -m alembic upgrade head

# Rollback one migration
python -m alembic downgrade -1

# View migration history
python -m alembic history
```

## Environment Variables

See `dev.env` for all available configuration options:

- `DATABASE_URL`: Database connection string (default: SQLite)
- `JWT_SECRET`: Secret key for JWT signing (min 32 chars)
- `JWT_ALGORITHM`: JWT signing algorithm (default: HS256)
- `JWT_EXPIRY_SECONDS`: Token expiry time (default: 3600)
- `SESSION_INACTIVITY_SECONDS`: Session timeout (default: 900)
- `RATE_LIMIT_ENABLED`: Enable login rate limiting (default: true)
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)
- `DEBUG`: Enable debug mode (default: true)

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login with email/password
- `POST /api/v1/auth/logout` - Logout current session
- `GET /api/v1/auth/me` - Get current user profile

### My Cases (Customer)
- `POST /api/v1/resolve` - Start resolve session
- `GET /api/v1/resolve/{session_id}` - Get session state
- `POST /api/v1/resolve/{session_id}/messages` - Send message to assistant
- `POST /api/v1/resolve/{session_id}/human-request` - Request human assistance
- `POST /api/v1/resolve/{session_id}/evidence` - Upload evidence file
- `POST /api/v1/resolve/{session_id}/confirmations` - Confirm action with SCA
- `POST /api/v1/cases` - Create case manually
- `GET /api/v1/cases` - List customer's cases
- `GET /api/v1/cases/{case_id}` - Get case detail

### Colleague View
- `POST /api/v1/colleague/cases` - Create case from desktop
- `GET /api/v1/colleague/cases` - List team worklist
- `GET /api/v1/colleague/cases/{case_id}` - Get hand-off pack
- `GET /api/v1/colleague/cases/{case_id}/thread` - Get conversation thread
- `POST /api/v1/colleague/cases/{case_id}/thread/entries` - Post colleague reply
- `POST /api/v1/colleague/cases/{case_id}/evidence-requests` - Request evidence
- `POST /api/v1/colleague/cases/{case_id}/pickup` - Pickup case assignment
- `GET /api/v1/colleague/cases/{case_id}/evidence/{evidence_id}/content` - Download evidence

### Health Check
- `GET /api/v1/health` - Service health status

## Seed Data

Default credentials:
- **Customer**: `admin@example.com` / `admin123`
- **Colleague**: `colleague@example.com` / `colleague123`

Seed data includes:
- 2 users (customer and colleague)
- 4 agents in agent_registry
- 9 action controls in action_control table

## Docker

```bash
# Build image
docker build -t clear-path-backend .

# Run with SQLite
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:////data/app.db \
  -v backend-data:/data \
  clear-path-backend

# Run with PostgreSQL
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql+psycopg://user:pass@db:5432/clearpath \
  clear-path-backend
```

## Development Notes

### Code Style
- Follow PEP 8 naming conventions
- Use type hints for all functions
- Document complex business logic
- Write tests for new features

### Auth Type Safety
- User.id is Integer with auto-increment
- All FKs to User.id are Integer
- JWT payload embeds `str(user.id)` and parses back to int

### Database Patterns
- Use sync SQLAlchemy (not async)
- All UUID columns use `Uuid` type with `uuid.UUID` defaults
- Migrations created with Alembic autogenerate
- Seed data is idempotent

### Event Handling
- All events go through EventPublisher
- OutboxDispatcher handles async dispatch
- Events are replay-safe and idempotent

### Policy Engine
- Seven deterministic rules
- No agent override permitted
- Returns machine-readable outcomes

## Troubleshooting

### Migration Issues
```bash
# Reset database (dev only)
rm app.db
python -m alembic upgrade head
python -c "from app.seed import seed_all; from app.database import SessionLocal; seed_all(SessionLocal())"
```

### Import Errors
```bash
# Reinstall dependencies
pip install --force-reinstall .
```

### Port Already in Use
```bash
# Find process using port 9000
lsof -i :9000  # macOS/Linux
netstat -ano | findstr :9000  # Windows

# Kill process or use different port
uvicorn app.main:app --port 9001
```
