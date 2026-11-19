# Sample Bank Mobile Payments MVP

A FastAPI + React application for mobile payment orchestration with Strong Customer Authentication (SCA), Confirmation of Payee (CoP), fraud/scam controls, and payment status normalization.

## Project Purpose

This application serves as the orchestration and normalization layer between customer-facing channels and enterprise systems of record for payment initiation, approval, and tracking. It enforces SCA with dynamic linking, CoP verification, fraud controls, and maintains authoritative application-owned state for payment attempts and normalized outcomes.

## Repository Structure

```
├── backend/              # Python FastAPI backend (modular monolith)
│   ├── app/             # Application code
│   │   ├── models/      # SQLAlchemy ORM models (26 tables)
│   │   ├── schemas/     # Pydantic request/response schemas
│   │   ├── services/    # Business logic and orchestration
│   │   ├── routers/     # API endpoints (auth, profiles, accounts, payees, payments)
│   │   ├── repositories/# Data access layer
│   │   ├── adapters/    # External system integrations (13 adapters)
│   │   ├── core/        # Security, middleware, errors
│   │   ├── config.py    # Settings management
│   │   ├── database.py  # Database session management
│   │   └── seed.py      # Idempotent seed data with demo credentials
│   ├── alembic/         # Database migrations (Alembic)
│   ├── tests/           # Backend tests (pytest)
│   ├── Dockerfile       # Backend container image
│   ├── docker-entrypoint.sh  # Migration/seed runner
│   ├── pyproject.toml   # Python dependencies
│   └── dev.env          # Local development environment variables
├── frontend/            # React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── pages/       # Page components (SignIn, Proof, Accounts, etc.)
│   │   ├── components/  # Reusable UI components
│   │   ├── features/    # Feature-specific logic (payments, auth)
│   │   ├── lib/         # Utilities (API client, validators, money)
│   │   └── types/       # TypeScript type definitions
│   ├── e2e/             # End-to-end tests (Playwright)
│   ├── Dockerfile       # Frontend container image (nginx)
│   ├── default.conf.template  # Nginx reverse proxy config
│   └── package.json     # Node.js dependencies
├── .github/workflows/   # CI/CD pipeline configuration
├── docker-compose.yml   # Local container orchestration (SQLite)
├── docker-compose.postgres.yml  # PostgreSQL override
├── start.sh             # Cross-platform startup script
├── stop.sh              # Cross-platform shutdown script
├── start.bat            # Windows wrapper (runs start.sh via Git Bash)
├── stop.bat             # Windows wrapper (runs stop.sh via Git Bash)
└── shared_config.json   # Shared API version and token settings
```

## Prerequisites

- **Python**: 3.11 or higher
- **Node.js**: 22.12 or higher
- **npm**: Latest version
- **Git**: For Windows users, Git Bash is required to run start.sh

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd lbg-ftr-demo-repo
```

### 2. Start the Application

The start script automatically:
- Checks prerequisites (Python 3.11+, Node.js 22.12+)
- Creates virtual environment and installs backend dependencies
- Installs frontend dependencies
- Runs database migrations
- Seeds demo data
- Starts backend and frontend on available ports
- Prints access URLs and demo credentials

**Linux/macOS/Git Bash:**
```bash
./start.sh
```

**Windows (cmd):**
```bash
start.bat
```

The application will start and display:
```
Frontend: http://localhost:5173
Backend:  http://localhost:9000
API Docs: http://localhost:9000/api/v1/docs

=== Default Credentials ===
  Email:    sasha.patel@gmail.com
  Password: Demo1234!
  Passcode: 123456
```

### 3. Access the Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:9000
- **API Documentation**: http://localhost:9000/api/v1/docs
- **Health Check**: http://localhost:9000/api/v1/health

### 4. Stop the Application

**Linux/macOS/Git Bash:**
```bash
./stop.sh
```

**Windows (cmd):**
```bash
stop.bat
```

## Testing

### Backend Tests

Run all backend tests:
```bash
cd backend
python -m pytest tests/ -v
```

Run specific test files:
```bash
python -m pytest tests/test_auth_acceptance.py -v
```

Run with coverage:
```bash
python -m pytest tests/ --cov=app --cov-report=html
```

### Frontend Tests

Run unit tests:
```bash
cd frontend
npm test
```

Run end-to-end tests:
```bash
cd frontend
npx playwright test
```

Run specific E2E test:
```bash
npx playwright test src/e2e/journey_new_request_to_approval.spec.ts
```

### Code Quality

Backend linting and type checking:
```bash
cd backend
ruff check .
mypy app --ignore-missing-imports
```

Frontend linting and type checking:
```bash
cd frontend
npm run lint
npx tsc --noEmit
```

## Docker Deployment

### Local Docker Compose (SQLite)

Build and start all services:
```bash
docker compose build
docker compose up -d
```

Check service health:
```bash
docker compose ps
curl -f http://localhost:80/health
```

Stop services:
```bash
docker compose down
```

### PostgreSQL Deployment

Use the PostgreSQL override for production-like setup:
```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml build
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up -d
```

This adds:
- PostgreSQL 16 database service
- Backend configured with `psycopg[binary]` driver
- Database connection via service name: `postgresql+psycopg://app_user:app_password@database:5432/app_db`

### Container Access

Frontend is exposed on port 80:
- **Application**: http://localhost (or http://127.0.0.1)
- **API Proxy**: http://localhost/api/v1/... (forwarded to backend:9000)

Note: Use `127.0.0.1` instead of `localhost` on macOS if localhost resolves to IPv6.

## Database

### Local Development (SQLite)
- **Engine**: SQLite (file-based, no server required)
- **Location**: `backend/app.db`
- **Migrations**: Managed by Alembic
- **Auto-migrate**: start.sh runs `alembic upgrade head` automatically

### Deployed/CI (PostgreSQL)
- **Engine**: PostgreSQL 16
- **Connection**: Via DATABASE_URL environment variable
- **Migrations**: Same Alembic migrations work on both SQLite and PostgreSQL

### Migration Commands

Run migrations:
```bash
cd backend
alembic upgrade head
```

Create a new migration:
```bash
cd backend
alembic revision --autogenerate -m "description of change"
```

Check migration status:
```bash
alembic current
alembic history
```

## Environment Configuration

### Backend Configuration

Configuration is in `backend/dev.env` (automatically copied to `backend/.env` on first run).

Key settings:
```env
# Database
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION_SECONDS=1800

# CORS (updated by start.sh with dynamic frontend port)
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Session
SESSION_MAX_SECONDS=1800
SESSION_INACTIVITY_SECONDS=300
SESSION_WARN_AFTER_SECONDS=240

# Rate Limiting
RATE_LIMIT_ENABLED=false

# Adapter Modes (stub|live)
ADAPTER_MODE_CIAM=stub
ADAPTER_MODE_MANDATE=stub
ADAPTER_MODE_CORE_BANKING=stub
ADAPTER_MODE_LOAN=stub
ADAPTER_MODE_PAYEE_DIRECTORY=stub
ADAPTER_MODE_COP=stub
ADAPTER_MODE_PAYMENT_ORCHESTRATION=stub
ADAPTER_MODE_PAYMENTS_HUB=stub
ADAPTER_MODE_FRAUD_DECISION=stub
ADAPTER_MODE_FRAUD_CASE=stub
ADAPTER_MODE_NOTIFICATION=stub
ADAPTER_MODE_OBSERVABILITY=stub
ADAPTER_MODE_SUPPORT_ROUTING=stub
```

### Frontend Configuration

Frontend uses environment variables at build time:
- `BACKEND_PORT`: Set by start.sh for local dev (read by Vite proxy)
- No hardcoded backend URLs (uses relative `/api` paths)

## Architecture

### Backend (Modular Monolith)

The backend implements 9 domain service modules:

1. **Identity and Session Services** (`app/routers/auth.py`)
   - Sign-in, proof (passcode/biometric), step-up authentication
   - Session lifecycle management
   - Rate limiting and generic error messages

2. **Entitlement and Profile Services** (`app/routers/profiles.py`)
   - Profile switching and entitlement resolution
   - Server-side authorization enforcement

3. **Accounts and Loans Aggregation** (`app/routers/accounts.py`)
   - Account overview with parallel adapter calls
   - Core banking and loan servicing integration

4. **Payee Services** (`app/routers/payees.py`)
   - Payee CRUD with encrypted account numbers
   - Mandatory CoP evaluation for new/amended payees

5. **Confirmation of Payee** (`app/services/cop_service.py`)
   - Pay.UK CoP provider integration
   - Match/mismatch/partial/unavailable outcome handling

6. **Payment Orchestration** (`app/routers/payments.py`)
   - Payment preparation with limit checks
   - SCA approval with dynamic linking
   - Fraud risk assessment
   - Idempotent submission to Payments Hub

7. **Fraud/Scam Interaction** (`app/services/fraud_service.py`)
   - Pre-submission risk assessment
   - Decision translation (allow/warn/challenge/hold/block)

8. **Notification Services** (`app/services/notification_service.py`)
   - Security and payment notifications
   - Delivery tracking (in-app status is authoritative)

9. **Audit and Observability** (`app/services/audit_service.py`)
   - Structured audit logging
   - Correlation ID tracking
   - Security-significant event capture

### Frontend (React SPA)

- **Same-origin `/api` integration**: Browser calls relative `/api` paths, proxied by Vite dev server or nginx
- **Authentication**: JWT tokens stored in localStorage, attached to API requests via Bearer header
- **Session management**: Inactivity guard with 5-minute timeout, 4-minute warning
- **Payment flow**: Multi-step state machine (entering → prepared → approving → friction → submitting → outcome)
- **Responsive design**: Tailwind CSS with mobile-first approach

### Security

- **Authentication**: Username/password + second-factor proof (passcode or biometric)
- **Authorization**: Server-side entitlement enforcement on every protected endpoint
- **SCA Dynamic Linking**: Fresh step-up bound to exact account, payee, amount, reference
- **Input Validation**: Client-side validation + mandatory server-side validation
- **Output Encoding**: Pydantic schemas prevent sensitive field leakage
- **Parameterized Queries**: SQLAlchemy ORM prevents SQL injection
- **Password Hashing**: bcrypt with cost factor 12
- **JWT Tokens**: Signed with HS256, 30-minute expiry
- **Session Tokens**: SHA-256 hashed before storage
- **CORS**: Configured per environment, never wildcard in production

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:9000/api/v1/docs
- **ReDoc**: http://localhost:9000/api/v1/redoc

Key API endpoint groups:
- `/api/v1/auth/*` - Authentication and session management
- `/api/v1/profiles/*` - Profile switching and entitlements
- `/api/v1/accounts/*` - Account and loan overview
- `/api/v1/payees/*` - Payee management and CoP
- `/api/v1/payments/*` - Payment preparation, approval, submission
- `/api/v1/notifications/*` - Customer notifications
- `/api/v1/support/*` - Scam claims and async webhooks
- `/api/v1/health` - Service health check

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request:

### Backend Job
- PostgreSQL service container
- Python 3.11 setup
- Install dependencies (including postgres extras)
- Run migrations
- Ruff linting
- Mypy type checking
- Pytest with coverage

### Frontend Job
- Node.js 22 setup
- Install dependencies
- ESLint linting
- TypeScript type checking
- Vitest unit tests
- Production build

Both jobs run in parallel for fast feedback.

## Environment Separation

### Local Development
- SQLite database (no server required)
- Stub adapters for external systems
- Dynamic port detection
- Auto-reload for development

### Docker Compose (Local)
- SQLite database with named volume
- All services containerized
- Same-origin API via nginx proxy
- Health checks for all services

### Docker Compose + PostgreSQL (Staging)
- PostgreSQL 16 database
- Production-like database engine
- All migrations and seeds still work
- Service dependency management

### Production (Implied)
- PostgreSQL database
- Live adapters for external systems
- Kubernetes/cloud deployment
- Secrets from external key management
- Centralized logging and monitoring

## Troubleshooting

### Port Already in Use
start.sh automatically detects and uses the next available port. Check logs:
```bash
cat backend.log
cat frontend.log
```

### Database Locked
Stop all services and remove the database:
```bash
./stop.sh
rm backend/app.db
./start.sh
```

### Migration Conflicts
Reset migrations to head:
```bash
cd backend
alembic downgrade base
alembic upgrade head
```

### Node/Python Version Issues
Verify versions:
```bash
python --version  # Should be 3.11+
node --version    # Should be v22.12+
```

### Docker Build Fails
Clean and rebuild:
```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Windows: Git Bash Not Found
Install Git for Windows from https://git-scm.com/download/win

The start.bat and stop.bat wrappers require Git Bash to run start.sh and stop.sh.

## Development Workflow

1. **Make changes** to backend (app/) or frontend (src/)
2. **Run tests** to verify changes
3. **Run linting** to check code style
4. **Create migration** if database models changed
5. **Test locally** with start.sh
6. **Test in Docker** with docker compose
7. **Commit** with conventional commit message (feat:, fix:, etc.)
8. **Push** and let CI validate

## License

Proprietary - Sample Bank Internal Use Only

## Support

For issues, questions, or contributions, please contact the development team.
