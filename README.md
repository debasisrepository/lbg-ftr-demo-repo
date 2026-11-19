# LBG FTR Demo - Digital Banking Payment Journey Platform

A complete digital banking payment journey application enabling authenticated customers to move from sign-in to payment confirmation in one coherent flow.

## Overview

This application provides a secure payment journey covering:
- **FR-001**: Username and password sign-in with step-up authentication
- **FR-002**: Second-factor authentication (passcode/biometric)
- **FR-003**: Account overview with entitlement-based visibility
- **FR-004**: Payee selection and Confirmation of Payee checks
- **FR-005**: Payment entry, validation, fraud checks, and SCA approval
- **FR-006**: Payment status tracking (sent, pending, failed)

## Architecture

- **Backend**: FastAPI (Python 3.11+)
- **Frontend**: React + TypeScript + Vite
- **Database**: SQLite (local), PostgreSQL (production)
- **Migrations**: Alembic
- **Authentication**: JWT with bcrypt password hashing (cost factor 12)

## Repository Structure

```
/repos/lbg-ftr-demo-repo/
├── backend/               # FastAPI backend application
│   ├── app/               # Application code
│   ├── alembic/           # Database migrations
│   ├── tests/             # Test suite
│   ├── Dockerfile         # Backend container image
│   └── pyproject.toml     # Python dependencies
├── frontend/              # React frontend application
│   ├── src/               # React components and pages
│   ├── e2e/               # End-to-end tests
│   ├── Dockerfile         # Frontend container image
│   └── package.json       # Node.js dependencies
├── .github/
│   └── workflows/
│       └── ci.yml         # CI/CD pipeline
├── docker-compose.yml     # SQLite (local/preview)
├── docker-compose.postgres.yml  # PostgreSQL override
├── start.sh               # Local startup script (all platforms)
├── stop.sh                # Local stop script
├── start.bat              # Windows wrapper (runs start.sh under Git Bash)
├── stop.bat               # Windows wrapper (runs stop.sh under Git Bash)
└── README.md              # This file
```

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 20.19+ or 22.12+
- **npm**: 9+ (included with Node.js)
- **Git Bash**: (Windows only) for running shell scripts - [Download](https://git-scm.com/download/win)

## Local Development Setup

### Quick Start

```bash
./start.sh
```

On Windows, run `start.bat` or use Git Bash to run `start.sh` directly.

The start script will:
1. Check prerequisites (Python 3.11+, Node.js 20+)
2. Create Python virtual environment
3. Install backend dependencies
4. Run database migrations
5. Load seed data
6. Start backend server (dynamic port starting at 9000)
7. Install frontend dependencies
8. Start frontend dev server (dynamic port starting at 5173)
9. Print access URLs and default credentials

### Default Credentials

The seed data creates three test users:

| Email | Password | Profile |
|-------|----------|---------|
| `admin@example.com` | `admin123` | Admin with personal profile |
| `john.smith@example.com` | `Personal123!` | Personal banking customer |
| `jane.doe@businessexample.com` | `Business123!` | Business banking customer |

### Accessing the Application

After running `./start.sh`, the services will be available at:

- **Frontend**: http://localhost:5173 (or next available port)
- **Backend API**: http://localhost:9000 (or next available port)
- **API Documentation**: http://localhost:9000/api/docs
- **Health Check**: http://localhost:9000/health

### Stopping the Application

```bash
./stop.sh
```

This stops only the processes started by `start.sh` (recorded in `.pids` file).

## Running Tests

### Backend Tests

```bash
cd backend
source .venv/bin/activate  # Windows: .venv\Scripts\activate
python -m pytest tests/ -v
```

Run with coverage:
```bash
python -m pytest tests/ --cov=app --cov-report=term-missing
```

### Frontend Tests

```bash
cd frontend
npm test
```

Run end-to-end tests:
```bash
npx playwright test
```

## Docker Deployment

### SQLite (Local/Preview)

Build and run with SQLite database:

```bash
docker compose build
docker compose up -d
```

Access the application at http://localhost:80

### PostgreSQL (Production)

Build and run with PostgreSQL:

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml build
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d
```

This configuration:
- Runs PostgreSQL 16 in a separate container
- Backend connects via `postgresql+psycopg://` connection string
- Data persists in `postgres-data` volume

### Docker Commands

```bash
# View logs
docker compose logs -f

# Stop services
docker compose down

# Remove volumes (data loss!)
docker compose down -v

# Rebuild after code changes
docker compose build
docker compose up -d
```

## Database Schema

The application uses 18 tables covering:

- **Authentication**: `user_identity`, `auth_session`, `registered_device`, `step_up_challenge`
- **Profiles**: `user_profile`, `profile_entitlement`
- **Accounts**: `account_snapshot`, `account_data_gap`, `loan_context_snapshot`
- **Payees**: `payee`, `cop_result`
- **Payments**: `payment_instruction`, `fraud_decision`, `payment_approval`, `payment_status_history`
- **Cross-cutting**: `notification_dispatch`, `audit_log`, `journey_event`

All monetary amounts are stored as integer minor units (e.g., £250.00 = 25000).

## Database Migrations

Migrations are run automatically by `start.sh` and `docker-entrypoint.sh`.

To create a new migration:

```bash
cd backend
source .venv/bin/activate
alembic revision --autogenerate -m "description of change"
```

Review the generated migration file in `alembic/versions/` before committing.

To run migrations manually:

```bash
alembic upgrade head
```

## Environment Variables

### Backend

Configuration is loaded from `backend/dev.env` (committed) and `backend/.env` (gitignored, created by start.sh).

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./app.db` | Database connection string |
| `JWT_SECRET_KEY` | (dev key) | Secret key for JWT signing - **change in production** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `JWT_EXPIRY_MINUTES` | `480` | Token expiry (8 hours) |
| `CORS_ORIGINS` | `http://localhost:5173` | Allowed CORS origins (comma-separated) |
| `RATE_LIMIT_ENABLED` | `true` | Enable rate limiting |
| `RATE_LIMIT_LOGIN_ATTEMPTS` | `5` | Max login attempts per window |
| `RATE_LIMIT_LOGIN_WINDOW_SECONDS` | `300` | Rate limit window (5 minutes) |
| `DEBUG` | `true` | Debug mode |

### Frontend

Frontend uses Vite environment variables. API calls use relative `/api` paths (proxied by Vite dev server, forwarded by nginx in Docker).

Do not set `VITE_API_URL` - the application uses relative paths for same-origin API access.

## Development Workflow

1. **Make changes** to models, services, components, or routes
2. **Create a migration** if schema changed:
   ```bash
   cd backend
   alembic revision --autogenerate -m "description"
   ```
3. **Review the migration** (autogenerate may miss some changes)
4. **Run tests**:
   ```bash
   cd backend && python -m pytest tests/
   cd frontend && npm test
   ```
5. **Test locally**:
   ```bash
   ./start.sh
   ```
6. **Test Docker build**:
   ```bash
   docker compose build
   docker compose up
   ```

## Code Quality

### Backend

```bash
cd backend
source .venv/bin/activate

# Type checking
mypy app --ignore-missing-imports

# Linting
ruff check app tests

# Format
ruff format app tests
```

### Frontend

```bash
cd frontend

# Type checking
npm run type-check

# Linting (if configured)
npx eslint src/
```

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on push and pull requests:

1. **Backend Lint**: ruff check
2. **Backend Type Check**: mypy
3. **Backend Test**: pytest with coverage
4. **Frontend Lint**: eslint
5. **Frontend Type Check**: tsc
6. **Frontend Test**: vitest
7. **Frontend Build**: vite build

All checks must pass before merge.

## Security Features

- **Password Hashing**: bcrypt with cost factor 12
- **JWT Tokens**: Include `exp` claim, backed by revocable server-side sessions
- **Rate Limiting**: Protects authentication endpoints (5 attempts per 5-minute window)
- **Input Validation**: Pydantic schemas validate all requests
- **SQL Injection Prevention**: Parameterized queries via SQLAlchemy ORM
- **Audit Logging**: Security events logged to `audit_log` table
- **Step-up Authentication**: Fresh SCA required for payment approval
- **Dynamic Linking**: Payment approval bound to specific payee/amount
- **Confirmation of Payee**: Name matching before payment

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:9000/api/docs
- **ReDoc**: http://localhost:9000/api/redoc

Key endpoints:
- `POST /api/v1/auth/login` - Username/password authentication
- `POST /api/v1/auth/logout` - Session termination
- `POST /api/v1/sca/verify-step-up` - Step-up authentication
- `GET /api/v1/profiles` - List user profiles
- `GET /api/v1/accounts/overview` - Account balances
- `GET /api/v1/payees` - List saved payees
- `POST /api/v1/payees` - Create new payee
- `POST /api/v1/payments/prepare` - Prepare payment
- `POST /api/v1/payments/{id}/approve` - Approve payment
- `GET /api/v1/payments/{id}` - Payment status

## Troubleshooting

### Port Conflicts

If ports 9000 or 5173 are in use, the start script will automatically find the next available port.

### Database Issues

If you encounter database errors:

```bash
cd backend
rm -f app.db  # Delete database
source .venv/bin/activate
alembic upgrade head  # Recreate from migrations
python -m app.seed  # Load seed data
```

### Dependency Issues

Backend:
```bash
cd backend
rm -rf .venv
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install .
```

Frontend:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Windows Issues

Ensure you have Git Bash installed. The start.sh script is designed to run under Git Bash on Windows.

If Python venv activation fails, check that you're using Git Bash (not cmd or PowerShell).

## License

Proprietary - LBG FTR Demo Project
