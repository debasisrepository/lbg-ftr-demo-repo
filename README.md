# Intelligent Receivables and Collections Application

A role-based receivables workspace with deterministic policy enforcement, customer 360 views, and promise-to-pay capture.

## Prerequisites

- **Python 3.11+** - [Download](https://python.org)
- **Node.js 20.19+ or 22.12+** - [Download](https://nodejs.org)
- **Git** - For cloning and version control
- **Git Bash** (Windows only) - [Download Git for Windows](https://git-scm.com/download/win)

## Quick Start

### Local Development (SQLite)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lbg-ftr-demo-repo
   ```

2. **Start the application**
   ```bash
   # Linux/macOS/Git Bash
   ./start.sh

   # Windows (runs start.sh under Git Bash)
   start.bat
   ```

   The script will:
   - Check prerequisites
   - Set up Python virtual environment
   - Install dependencies
   - Run database migrations
   - Seed sample data
   - Start backend (http://localhost:9000)
   - Start frontend (http://localhost:5173)

3. **Login with default credentials**
   - **Collections Analyst**
     - Username: `analyst1`
     - Password: `analyst123`
   
   - **Collections Reviewer**
     - Username: `reviewer1`
     - Password: `reviewer123`

4. **Stop the application**
   ```bash
   # Linux/macOS/Git Bash
   ./stop.sh

   # Windows
   stop.bat
   ```

### Docker Deployment

1. **Build and start services**
   ```bash
   docker compose build
   docker compose up -d
   ```

2. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:9000
   - API Documentation: http://localhost:9000/api/docs

3. **Stop services**
   ```bash
   docker compose down
   ```

## Project Structure

```
lbg-ftr-demo-repo/
├── backend/              # FastAPI backend
│   ├── app/             # Application code
│   │   ├── core/        # Core utilities (auth, config, security)
│   │   ├── models/      # SQLAlchemy ORM models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── services/    # Business logic
│   │   ├── routers/     # API routes
│   │   ├── middleware/  # Request middleware
│   │   ├── repositories/# Data access layer
│   │   ├── adapters/    # External system adapters (SAP)
│   │   ├── policy/      # Policy engine
│   │   └── jobs/        # Scheduled jobs
│   ├── alembic/         # Database migrations
│   ├── tests/           # Backend tests
│   ├── Dockerfile       # Backend container
│   └── pyproject.toml   # Python dependencies
├── frontend/            # React + TypeScript + Vite
│   ├── src/
│   │   ├── pages/       # Page components
│   │   ├── components/  # Reusable UI components
│   │   ├── lib/         # API client, auth context
│   │   ├── hooks/       # Custom React hooks
│   │   └── types/       # TypeScript definitions
│   ├── e2e/             # Playwright E2E tests
│   ├── Dockerfile       # Frontend container with nginx
│   └── package.json     # Node dependencies
├── .github/workflows/   # CI/CD pipelines
├── docker-compose.yml   # Container orchestration
├── start.sh            # Cross-platform startup script
└── stop.sh             # Cross-platform shutdown script
```

## Configuration

### Backend Environment Variables

Configuration is loaded from `backend/.env` (auto-created from `backend/dev.env` on first run).

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///./app.db` |
| `SECRET_KEY` | JWT signing secret (32+ chars) | `dev-secret-key-...` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRY_MINUTES` | Token expiry time | `1440` (24 hours) |
| `INACTIVITY_TIMEOUT_SECONDS` | Session inactivity timeout | `1800` (30 minutes) |
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173,...` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | `true` |
| `RATE_LIMIT_MAX_ATTEMPTS` | Max login attempts | `10` |
| `RATE_LIMIT_WINDOW_MINUTES` | Rate limit window | `15` |
| `CUSTOMER_CONTEXT_STALE_SECONDS` | Customer data staleness threshold | `3600` (1 hour) |
| `DEBUG` | Enable debug logging | `true` |
| `LOAD_SEED_DATA` | Auto-seed on startup | `false` |

### Frontend Environment Variables

The frontend uses relative API calls (`/api`) which are proxied in development (Vite) and production (nginx).

**No `VITE_API_URL` configuration needed** - the proxy handles routing automatically.

## Development

### Backend

```bash
cd backend

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate     # Windows

# Run migrations
alembic upgrade head

# Seed database
python app/cli.py seed

# Run tests
python -m pytest tests/ -v

# Lint
ruff check app

# Type check
mypy app
```

### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Run tests
npm test -- --run

# Type check
npm run type-check

# Lint
npm run lint

# Build
npm run build
```

### Running E2E Tests

```bash
cd frontend
npx playwright test
```

## API Documentation

When the backend is running, interactive API documentation is available at:

- **Swagger UI**: http://localhost:9000/api/docs
- **ReDoc**: http://localhost:9000/api/redoc

## Key Features

### Role-Based Workspace (FR-CAPA-001)
- Personalized landing page based on assigned role
- Role switcher for users with multiple roles
- Role-specific widgets and queue access

### Work Queue Management (FR-QUE-001)
- Actionable queue generation with prioritization
- Queue segmentation (active, promise_on_file, non_standard)
- Deterministic ranking based on multiple factors
- Refresh functionality with SAP sync

### Customer 360 View (FR-C360-001)
- Unified customer account context
- Multiple sections: profile, accounts, invoices, receivables, promises, interactions
- Section status indicators (available/unavailable/masked)
- Field-level masking for sensitive data

### Promise-to-Pay Capture (FR-PTP-001)
- Structured promise recording
- Invoice and account balance linking
- Policy validation on capture
- Idempotency support with replay protection

### Deterministic Policy Engine (FR-DTC-001)
- Server-side policy rule evaluation
- Multiple condition types (field_present, decimal_greater_than, field_in_set, etc.)
- Rule set versioning and activation
- Historical evaluation records

## Deployment

### Production Environment

For production deployment:

1. **Set environment variables**
   - Generate secure `SECRET_KEY` (32+ characters)
   - Configure production `DATABASE_URL` (PostgreSQL recommended)
   - Update `CORS_ORIGINS` to match production domains
   - Set `DEBUG=false`

2. **Use PostgreSQL**
   ```bash
   # Install PostgreSQL support
   cd backend
   pip install '.[postgres]'
   
   # Set DATABASE_URL
   export DATABASE_URL=postgresql+psycopg://user:pass@host:5432/dbname
   ```

3. **Run migrations**
   ```bash
   cd backend
   alembic upgrade head
   python app/cli.py seed
   ```

4. **Deploy with Docker**
   ```bash
   docker compose -f docker-compose.yml up -d
   ```

### CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

- **Backend**: lint → type check → migrate (PostgreSQL) → test
- **Frontend**: lint → type check → test → build

## Troubleshooting

### Port Already in Use
The startup script automatically finds available ports starting from 9000 (backend) and 5173 (frontend).

### Database Migration Issues
```bash
cd backend
# Check current migration status
alembic current

# View migration history
alembic history

# Downgrade one revision
alembic downgrade -1

# Upgrade to latest
alembic upgrade head
```

### Frontend Build Errors
```bash
cd frontend
# Clean install
rm -rf node_modules package-lock.json
npm install

# Clear Vite cache
rm -rf .vite dist
npm run build
```

## Support

For issues and questions:
- Check API documentation at http://localhost:9000/docs
- Review logs in terminal output
- Consult project design documents in `/artifacts`

## License

Internal use only - LBG FTR Demo Application
