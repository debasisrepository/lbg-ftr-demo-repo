# LBG Clear Path - Backend

FastAPI backend for the LBG Clear Path case tracking and transparency system.

## Stack

- **Python**: 3.11+
- **Framework**: FastAPI
- **ORM**: SQLAlchemy (sync engine)
- **Migrations**: Alembic
- **Database**: SQLite (local development), PostgreSQL (deployed)
- **Auth**: JWT with bcrypt password hashing

## Structure

```
backend/
├── app/
│   ├── core/           # Cross-cutting concerns (event bus, UoW, security, errors)
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic request/response DTOs
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   ├── routers/        # API endpoints
│   ├── config.py       # Settings (pydantic-settings)
│   ├── database.py     # Database engine and session
│   ├── deps.py         # FastAPI dependencies
│   ├── main.py         # Application factory
│   └── seed.py         # Seed data
├── alembic/            # Database migrations
├── tests/              # Test suite
├── pyproject.toml      # Dependencies
└── alembic.ini         # Alembic configuration
```

## Setup

1. **Create virtual environment:**
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install .
   ```

3. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

4. **Seed database:**
   ```bash
   python -m app.seed
   ```

## Run

Start the development server:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 9000
```

Access:
- API: http://localhost:9000
- Docs: http://localhost:9000/docs
- ReDoc: http://localhost:9000/redoc

## Test

Run tests:

```bash
pytest tests/ -v
```

With coverage:

```bash
pytest tests/ --cov=app --cov-report=term-missing
```

## Default Credentials

- **Customer**: `admin@example.com` / `admin123`
- **Colleague**: `colleague@example.com` / `colleague123`

## Environment Variables

Key configuration variables (see `dev.env`):

- `DATABASE_URL`: Database connection string
- `JWT_SECRET`: Secret for signing JWT tokens
- `SESSION_LIFETIME_MINUTES`: Session token lifetime (default 30)
- `SESSION_INACTIVITY_MINUTES`: Inactivity timeout (default 15)
- `LOGIN_FAILURE_THRESHOLD`: Failed login attempts before lockout (default 5)
- `CORS_ALLOW_ORIGINS`: Comma-separated list of allowed origins

## API Endpoints

### Authentication (`/api/v1/auth`)

- `POST /login` - Login with username/password
- `POST /refresh` - Refresh session token
- `POST /logout` - Logout and revoke session
- `GET /me` - Get current user info

### Health

- `GET /health` - Liveness check
- `GET /health/ready` - Readiness check (validates DB connectivity)
