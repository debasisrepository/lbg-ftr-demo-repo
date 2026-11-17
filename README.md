# Clear Path MVP

Clear Path provides customer-visible case continuity across assistant-led intake, managed case creation, colleague continuation, and notification dispatch.

## Features

- **Resolve Assistant**: AI-powered customer intake with issue classification and evidence gathering
- **Case Management**: Customer-visible case tracking with status updates and expected-by dates
- **Colleague View**: Hand-off pack with one-screen summary, transcript continuation, and evidence management
- **Policy Engine**: Deterministic L0-L3 autonomy enforcement with SCA requirements
- **Event-Driven Architecture**: Replay-safe event handling with audit logging

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, Alembic
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS
- **Database**: SQLite (development), PostgreSQL (production)
- **Testing**: pytest (backend), Vitest (frontend), Playwright (E2E)

## Prerequisites

- Python 3.11 or higher
- Node.js 20.19+ or 22.12+
- npm 9+

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lbg-ftr-demo-repo
   ```

2. **Start the application**
   ```bash
   chmod +x start.sh stop.sh
   ./start.sh
   ```

   The script will:
   - Check prerequisites
   - Install dependencies
   - Run database migrations
   - Seed default data
   - Start backend and frontend

3. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:9000
   - API Documentation: http://localhost:9000/docs

4. **Stop the application**
   ```bash
   ./stop.sh
   ```

### Default Credentials

**Customer:**
- Email: `admin@example.com`
- Password: `admin123`

**Colleague:**
- Email: `colleague@example.com`
- Password: `colleague123`

## Docker Deployment

### SQLite (Development)

```bash
# Build and start
docker-compose up -d

# Access at http://localhost:80

# Stop
docker-compose down
```

### PostgreSQL (Production)

```bash
# Build and start with PostgreSQL
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml up -d

# Stop
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml down
```

## Development

### Backend

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install .

# Run migrations
python -m alembic upgrade head

# Seed database
python -c "from app.seed import seed_all; from app.database import SessionLocal; seed_all(SessionLocal())"

# Run tests
pytest -v

# Type check
mypy app --ignore-missing-imports

# Start development server
uvicorn app.main:app --reload --port 9000
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run tests
npm test

# Type check
npm run type-check

# Lint
npm run lint

# Start development server
npm run dev

# Build for production
npm run build
```

### End-to-End Tests

```bash
cd frontend

# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npx playwright test

# Run specific test
npx playwright test e2e/journey_resolve_assistant_handoff.spec.ts
```

## Project Structure

```
lbg-ftr-demo-repo/
├── backend/
│   ├── app/
│   │   ├── agents/           # AI agents (intake, triage, case owner, copilot)
│   │   ├── adapters/         # External system adapters
│   │   ├── api/              # API routers
│   │   ├── auth/             # Authentication & authorization
│   │   ├── core/             # Core utilities (clock, errors, context)
│   │   ├── events/           # Event publishing & dispatch
│   │   ├── middleware/       # Request middleware
│   │   ├── services/         # Business logic services
│   │   ├── tools/            # Bounded tool layer
│   │   ├── database.py       # Database configuration
│   │   ├── main.py           # FastAPI application
│   │   └── seed.py           # Seed data
│   ├── alembic/              # Database migrations
│   ├── tests/                # Backend tests
│   ├── pyproject.toml        # Python dependencies
│   └── dev.env               # Development environment variables
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── lib/              # Utilities & API client
│   │   ├── pages/            # Page components
│   │   └── types/            # TypeScript types
│   ├── e2e/                  # Playwright E2E tests
│   ├── package.json          # Node dependencies
│   └── vite.config.ts        # Vite configuration
├── .github/workflows/        # CI/CD workflows
├── docker-compose.yml        # Docker Compose (SQLite)
├── docker-compose.postgres.yml  # PostgreSQL override
├── start.sh                  # Start script
└── stop.sh                   # Stop script
```

## Environment Variables

### Backend (.env)

```bash
DATABASE_URL=sqlite:///./app.db
JWT_SECRET=dev-secret-change-in-production-minimum-32-characters-required
JWT_ALGORITHM=HS256
JWT_EXPIRY_SECONDS=3600
SESSION_INACTIVITY_SECONDS=900
RATE_LIMIT_ENABLED=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
DEBUG=true
```

### Frontend

The frontend uses relative API URLs (`/api`) and does not require environment variables for local development. The Vite dev server proxies `/api` requests to the backend.

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get current user

### My Cases (Customer)
- `POST /api/v1/resolve` - Start resolve session
- `GET /api/v1/resolve/{session_id}` - Get session state
- `POST /api/v1/resolve/{session_id}/messages` - Send message
- `POST /api/v1/resolve/{session_id}/human-request` - Request human assistance
- `POST /api/v1/resolve/{session_id}/evidence` - Upload evidence
- `POST /api/v1/resolve/{session_id}/confirmations` - Confirm action with SCA
- `POST /api/v1/cases` - Create case
- `GET /api/v1/cases` - List customer cases
- `GET /api/v1/cases/{case_id}` - Get case detail

### Colleague View
- `POST /api/v1/colleague/cases` - Create case from desktop
- `GET /api/v1/colleague/cases` - List team worklist
- `GET /api/v1/colleague/cases/{case_id}` - Get hand-off pack
- `GET /api/v1/colleague/cases/{case_id}/thread` - Get conversation thread
- `POST /api/v1/colleague/cases/{case_id}/thread/entries` - Post reply
- `POST /api/v1/colleague/cases/{case_id}/evidence-requests` - Request evidence
- `POST /api/v1/colleague/cases/{case_id}/pickup` - Pickup case

Full API documentation: http://localhost:9000/docs

## Testing

### Backend Tests
```bash
cd backend
pytest -v                                    # All tests
pytest tests/test_smoke.py -v               # Smoke tests
pytest tests/test_my_cases_api.py -v        # My Cases API tests
pytest tests/test_colleague_api.py -v       # Colleague API tests
```

### Frontend Tests
```bash
cd frontend
npm test -- --run                           # All unit tests
npm test src/__tests__/ResolvePage.test.tsx -- --run  # Specific test
npx playwright test                         # All E2E tests
npx playwright test e2e/smoke_login.spec.ts # Specific E2E test
```

## Architecture

### Backend Modules

- **Agents**: Intake & Triage, Case Owner, Colleague Copilot, Guardrail Supervisor
- **Policy Engine**: Deterministic L0-L3 autonomy enforcement with kill switches
- **Redaction Boundary**: Pre-LLM sanitization for PAN, passcodes, injection patterns
- **Tool Layer**: Eight bounded tools with SCA verification
- **Adapters**: Seven system adapters (transactions, documents, cards, payments, routing, notifications, contact scheduling)
- **Event System**: Domain events with outbox pattern for reliable dispatch
- **Audit Service**: Hash-chained append-only audit log
- **Case Service**: Customer-visible continuity record with unique case references

### Frontend Architecture

- **Auth Context**: JWT-based authentication with localStorage
- **API Client**: Centralized HTTP client with auth headers
- **Route Guards**: Protected routes requiring authentication
- **Layout Components**: Header, Sidebar, Layout wrapper
- **Feature Pages**: Resolve Assistant, My Cases, Case Confirmation, Colleague View

## Security

- **Authentication**: JWT tokens with bcrypt password hashing
- **Session Management**: Server-side session tracking with inactivity timeout
- **Rate Limiting**: Login attempt rate limiting to prevent brute force
- **CORS**: Configured origins for cross-origin requests
- **SCA**: Strong Customer Authentication required for money/card actions
- **Redaction**: PAN, passcode, and security answer detection before LLM processing
- **Audit Trail**: Immutable audit log with hash chaining

## License

Copyright © 2024. All rights reserved.
