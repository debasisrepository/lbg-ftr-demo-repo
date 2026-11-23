# Release 1 Mobile Banking Platform

A controlled personal-customer pilot for iOS and Android smartphone users, delivering authenticated mobile banking capabilities with device registration, passcode and biometric sign-in, account viewing, and payment initiation with scam protection.

## Repository Structure

```
lbg-ftr-demo-repo/
├── backend/              # FastAPI backend service
│   ├── app/              # Application code
│   ├── alembic/          # Database migrations
│   ├── tests/            # Backend tests
│   ├── workers/          # Background workers (outbox publisher)
│   ├── pyproject.toml    # Python dependencies
│   └── dev.env           # Local development configuration
├── frontend/             # React + TypeScript frontend
│   ├── src/              # Application source
│   ├── e2e/              # End-to-end tests (Playwright)
│   ├── package.json      # Node dependencies
│   └── vite.config.ts    # Vite configuration
├── start.sh              # Cross-platform startup script
├── stop.sh               # Graceful shutdown script
├── start.bat             # Windows wrapper (runs start.sh via Git Bash)
├── stop.bat              # Windows wrapper (runs stop.sh via Git Bash)
├── docker-compose.yml    # Base compose (SQLite backend + frontend)
├── docker-compose.postgres.yml  # Optional PostgreSQL override
├── .github/workflows/    # CI/CD pipelines
├── CI_CD.md              # CI/CD pipeline documentation
└── DEPLOYMENT.md         # Deployment guide for all environments
```

## Prerequisites

- **Python 3.11+** (backend)
- **Node.js 20.19+ or 22+** (frontend)
- **npm** (comes with Node.js)
- **Git** (required on all platforms; Git for Windows on Windows)

## Quick Start

### macOS / Linux / Windows (Git Bash)

```bash
./start.sh
```

### Windows (Command Prompt)

```cmd
start.bat
```

The startup script will:
1. Check prerequisites (Python 3.11+, Node.js 20.19+/22+)
2. Create Python virtual environment if missing
3. Install backend dependencies
4. Run database migrations
5. Seed test data
6. Start backend on http://localhost:9000 (or next available port)
7. Install frontend dependencies
8. Start frontend on http://localhost:5173 (or next available port)
8. Print seed credentials for testing

**Access the application:**
- Frontend: http://localhost:5173
- Backend API: http://localhost:9000
- API Documentation: http://localhost:9000/docs

## Seed Credentials

The application includes pre-seeded test accounts for immediate use:

### Customer 1: Alex Taylor
- **Customer ID:** CUST-SYNTH-001
- **Passcode:** Pass1234
- **Accounts:** 3 accounts (Current Account, Savings Account, Credit Card)
- **Payees:** 3 saved payees

### Customer 2: Jordan Smith
- **Customer ID:** CUST-SYNTH-002
- **Passcode:** Pass5678
- **Accounts:** 3 accounts (Current Account, Savings Account, Credit Card)
- **Payees:** 3 saved payees

**Use these credentials to sign in through the mobile frontend.**

## Stopping Services

### macOS / Linux / Windows (Git Bash)

```bash
./stop.sh
```

### Windows (Command Prompt)

```cmd
stop.bat
```

The stop script safely terminates only the services started by start.sh (using the `.pids` file).

## Development Workflow

### Backend Development

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Run tests
pytest

# Run specific test file
pytest tests/test_auth_service.py -v

# Type checking
mypy app --ignore-missing-imports

# Create new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server (requires backend running)
npm run dev

# Run unit tests
npm run test

# Run E2E tests (requires backend running with migrations + seed)
npx playwright test

# Type checking
npm run type-check

# Build production bundle
npm run build

# Preview production build
npm run preview
```

### Running Tests

#### Backend Tests

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pytest -v
```

Test coverage:
- Unit tests: Service layer logic
- Integration tests: Database and API integration
- Acceptance tests: Full feature acceptance criteria

#### Frontend Tests

```bash
cd frontend

# Unit tests
npm run test

# E2E tests (requires backend running)
npx playwright test

# E2E tests with UI
npx playwright test --ui

# Specific E2E test
npx playwright test e2e/journey_new_request_to_sent.spec.ts
```

## Docker Deployment

### SQLite (Default)

```bash
# Build images
docker compose build

# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v
```

**Access:**
- Frontend: http://localhost:80
- Backend API: http://localhost:9000
- API Docs: http://localhost:9000/docs

### PostgreSQL (Optional)

For production-like deployment with PostgreSQL:

```bash
# Build with PostgreSQL support
docker compose -f docker-compose.yml -f docker-compose.postgres.yml build

# Start with PostgreSQL
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d

# View logs
docker compose -f docker-compose.yml -f docker-compose.postgres.yml logs -f

# Stop services
docker compose -f docker-compose.yml -f docker-compose.postgres.yml down
```

**PostgreSQL Configuration:**
- Host: `database` (internal service name)
- Port: `5432`
- Database: `lbg_ftr_demo`
- User: `lbgapp`
- Password: `dev-postgres-password` (change in production!)

## CI/CD Pipeline

The repository includes comprehensive CI/CD pipelines for automated building, testing, and deployment.

### Continuous Integration (`.github/workflows/ci.yml`)

Runs on every push and pull request to `main` and `develop` branches.

**Pipeline Stages:**

1. **Backend Lint & Type Check**
   - Ruff linter for code quality
   - Mypy for static type checking

2. **Backend Tests**
   - PostgreSQL service container
   - Full test suite (unit, integration, acceptance)
   - Code coverage reporting (Codecov)

3. **Frontend Lint & Type Check**
   - ESLint for code quality
   - TypeScript compiler for type checking

4. **Frontend Tests**
   - Vitest unit tests with coverage
   - Production build verification

5. **E2E Tests**
   - Playwright tests covering full user journeys
   - Backend + Frontend integration testing

6. **Docker Build & Scan**
   - Build backend and frontend images
   - Test SQLite and PostgreSQL compose stacks
   - Health endpoint verification

7. **Security Scanning**
   - Trivy vulnerability scanner
   - Bandit Python security linter
   - SARIF reports to GitHub Security

8. **Integration Report**
   - Consolidated build status
   - Artifact inventory

### Continuous Deployment (`.github/workflows/cd.yml`)

Deploys to staging and production environments.

**Triggers:**
- Push to `main` → Staging deployment
- Version tags (`v*.*.*`) → Production deployment
- Manual workflow dispatch

**Deployment Flow:**

```
Build & Publish Images
         ↓
Deploy to Staging
         ↓
Smoke Test Staging
         ↓
Deploy to Production (manual approval required)
         ↓
Smoke Test Production
         ↓
Rollback if Failed
```

**Container Registry:**
- GitHub Container Registry (ghcr.io)
- Versioned images with semantic versioning
- SHA-based tags for traceability

### Documentation

For detailed CI/CD information, see:
- **[CI_CD.md](CI_CD.md)** - Complete CI/CD pipeline documentation
- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Deployment guide for all environments

## Environment Variables

### Backend Configuration

Create `backend/.env` or use `backend/dev.env` as a template:

```env
# Database
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_INACTIVITY_TIMEOUT_MINUTES=15
BCRYPT_COST_FACTOR=12

# CORS
CORS_ORIGINS=http://localhost:5173

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_PER_ADDRESS_WINDOW_SECONDS=300
RATE_LIMIT_LOGIN_PER_ADDRESS_MAX_ATTEMPTS=5
RATE_LIMIT_LOGIN_PER_CUSTOMER_WINDOW_SECONDS=300
RATE_LIMIT_LOGIN_PER_CUSTOMER_MAX_ATTEMPTS=10

# Payment Configuration
PAYMENT_LIMIT_MINOR=100000000

# Freshness & Fraud
FRESHNESS_TARGET_SECONDS=60
SCAM_CHECK_BUDGET_MS=300
HOLD_DECISION_BUSINESS_DAYS=4
```

### Frontend Configuration

The frontend uses environment variables prefixed with `VITE_`. For local development, the frontend proxies API calls to the backend via Vite's dev server (configured in `vite.config.ts`).

No `VITE_API_URL` is needed for local development - the proxy handles routing `/api` to the backend automatically.

## Architecture Overview

### Backend (FastAPI + SQLAlchemy + SQLite/PostgreSQL)

**Key Components:**
- **Authentication:** Passcode-based auth with JWT sessions, rate limiting
- **Payment Orchestration:** State machine for payment flows with outbox pattern
- **Dynamic Link Approval:** Step-up authentication via CIAM sandbox
- **Scam Checks:** Fraud engine integration with warning/hold flows
- **Event-Driven:** Outbox publisher for payment events
- **Read Models:** Event-fed projections for accounts and payment status

**Database Migrations:** Alembic manages schema versioning

**Background Workers:**
- Outbox publisher (`workers/outbox_publisher.py`)
- Event consumers for status convergence

### Frontend (React + TypeScript + Vite + Tailwind CSS)

**Key Features:**
- Sign-in with passcode
- Account overview with balances and freshness indicators
- Saved payee selection
- Payment entry and review
- Dynamic link approval with passcode verification
- Scam warning presentation with stop/continue options
- Payment outcome display (Sent/Pending/Failed)
- Session reconnect capability

**Testing:**
- Unit tests (vitest)
- E2E tests (Playwright) covering full payment journeys

## API Documentation

Once the backend is running, visit:
- **OpenAPI Docs (Swagger UI):** http://localhost:9000/docs
- **ReDoc:** http://localhost:9000/redoc
- **OpenAPI JSON:** http://localhost:9000/openapi.json

## Troubleshooting

### Port Already in Use

The startup script automatically finds the next available port if the default port (9000 for backend, 5173 for frontend) is in use. The printed URLs will show the actual ports.

### Database Migration Issues

```bash
cd backend
source .venv/bin/activate

# Check current migration version
alembic current

# View migration history
alembic history

# Reset database (WARNING: destroys all data)
rm app.db
alembic upgrade head
python -c "from app.seed import seed_database; from app.database import get_db; seed_database(next(get_db()))"
```

### Frontend Build Failures

```bash
cd frontend

# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite dist

# Rebuild
npm run build
```

### Docker Issues

```bash
# Remove all containers and volumes
docker compose down -v

# Rebuild from scratch
docker compose build --no-cache

# View detailed logs
docker compose logs -f backend
docker compose logs -f frontend
```

### Python Version Issues on Windows (Git Bash)

If you see "`python3: command not found`" or "`python3` exits with code 9009", the startup script will automatically try `python` instead. Ensure you have Python 3.11+ installed from https://python.org.

### Node Version Issues

The frontend requires Node.js 20.19+ or 22+. Check your version:

```bash
node --version
```

If you have an older version, download the latest LTS from https://nodejs.org.

## Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `pytest` (backend), `npm run test` (frontend)
4. Run linters: `ruff check app` (backend), `npm run lint` (frontend)
5. Run type checking: `mypy app` (backend), `npm run type-check` (frontend)
6. Create a pull request

All pull requests trigger the CI pipeline, which must pass before merging.

## Release Process

1. Ensure all tests pass on `main` branch
2. Create a version tag: `git tag -a v1.2.3 -m "Release v1.2.3"`
3. Push the tag: `git push origin v1.2.3`
4. CI/CD pipeline automatically builds and deploys to staging
5. After staging validation, approve production deployment
6. Monitor deployment progress in GitHub Actions

For detailed release procedures, see [DEPLOYMENT.md](DEPLOYMENT.md).

## License

Proprietary - Lloyds Banking Group

## Support

For issues or questions:
- Create an issue in the repository
- Contact the development team
- Refer to [CI_CD.md](CI_CD.md) for pipeline issues
- Refer to [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
