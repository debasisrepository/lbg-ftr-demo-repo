# LBG Clear Path

LBG Clear Path is a customer-facing orchestration and transparency layer that enhances existing authenticated journeys within the Lloyds mobile app and Bank of Scotland mobile app. The solution provides cross-channel continuity and case transparency.

## Architecture

- **Backend**: FastAPI (Python 3.11+) modular monolith with SQLAlchemy ORM
- **Frontend**: React + TypeScript + Vite with IBM Carbon Design System
- **Database**: SQLite (development) / PostgreSQL (production)
- **Deployment**: Docker containers with nginx reverse proxy

## Prerequisites

- **Python 3.11+** - [Download](https://python.org)
- **Node.js 20.19+/22.12+** - [Download](https://nodejs.org)
- **npm** (included with Node.js)
- **Git Bash** (Windows only) - [Download](https://git-scm.com/download/win)
- **Docker & Docker Compose** (for container deployment) - [Download](https://docker.com)

## Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd lbg-ftr-demo-repo
   ```

2. **Run the application**
   ```bash
   ./start.sh
   ```
   
   On Windows:
   ```batch
   start.bat
   ```

   The script will:
   - Check prerequisites
   - Create Python virtual environment
   - Install all dependencies
   - Run database migrations
   - Seed test data
   - Start backend (http://localhost:9000)
   - Start frontend (http://localhost:5173)
   - Print default credentials

3. **Access the application**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:9000
   - API Documentation: http://localhost:9000/docs

4. **Stop the application**
   ```bash
   ./stop.sh
   ```
   
   On Windows:
   ```batch
   stop.bat
   ```

### Default Credentials

**Admin User:**
- Email: `admin@example.com`
- Password: `admin123`

**Colleague User:**
- Email: `colleague@example.com`
- Password: `colleague123`

**Regular Users:**
- Email: `user1@example.com` through `user4@example.com`
- Password: `user123`

## Testing

### Backend Tests

```bash
cd backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pytest -v
```

Run specific test suites:
```bash
pytest tests/unit/ -v           # Unit tests
pytest tests/integration/ -v    # Integration tests
pytest tests/acceptance/ -v     # Acceptance tests
```

### Frontend Tests

```bash
cd frontend
npm run test              # Run unit tests (vitest)
npx playwright test       # Run E2E tests
```

## Docker Deployment

### SQLite (Development)

```bash
docker compose up --build
```

Access:
- Application: http://localhost:80
- Backend API: http://localhost:8000

### PostgreSQL (Production)

```bash
docker compose -f docker-compose.yml -f docker-compose.postgres.yml up --build
```

The application will:
- Start PostgreSQL database
- Run migrations
- Seed test data
- Start backend and frontend services

### Stop Containers

```bash
docker compose down
```

## Project Structure

```
lbg-ftr-demo-repo/
├── backend/                    # FastAPI backend
│   ├── app/                   # Application code
│   │   ├── adapters/         # External system integrations
│   │   ├── core/             # Core utilities (security, errors, etc)
│   │   ├── jobs/             # Background jobs
│   │   ├── models/           # SQLAlchemy models
│   │   ├── repositories/     # Data access layer
│   │   ├── routers/          # API endpoints
│   │   ├── schemas/          # Pydantic schemas
│   │   ├── services/         # Business logic
│   │   ├── config.py         # Configuration
│   │   ├── database.py       # Database setup
│   │   ├── main.py           # Application entry point
│   │   └── seed.py           # Seed data
│   ├── alembic/              # Database migrations
│   ├── tests/                # Test suite
│   ├── Dockerfile            # Backend container
│   ├── docker-entrypoint.sh  # Container startup script
│   ├── pyproject.toml        # Python dependencies
│   └── dev.env               # Development environment variables
│
├── frontend/                  # React frontend
│   ├── src/                  # Source code
│   │   ├── components/       # React components
│   │   ├── routes/           # Page components
│   │   ├── hooks/            # Custom hooks
│   │   ├── lib/              # Utilities and API client
│   │   └── test/             # Test utilities
│   ├── e2e/                  # Playwright E2E tests
│   ├── public/               # Static assets
│   ├── Dockerfile            # Frontend container
│   ├── default.conf.template # nginx configuration
│   └── package.json          # Node dependencies
│
├── .github/workflows/        # CI/CD workflows
├── docker-compose.yml        # Base Docker Compose config
├── docker-compose.postgres.yml # PostgreSQL override
├── start.sh                  # Local startup script
├── stop.sh                   # Local shutdown script
├── start.bat                 # Windows startup wrapper
└── stop.bat                  # Windows shutdown wrapper
```

## Environment Configuration

### Backend (backend/dev.env)

Key environment variables:

```bash
DATABASE_URL=sqlite:///./app.db          # Database connection string
JWT_SECRET=dev-secret-change-me          # JWT signing secret
CORS_ALLOW_ORIGINS=http://localhost:5173 # Allowed CORS origins
ADAPTER_MODE=sandbox                     # Adapter mode (sandbox/live)
```

### Frontend

The frontend automatically proxies `/api` requests to the backend. No additional configuration required for local development.

## API Documentation

Once the backend is running, interactive API documentation is available at:
- Swagger UI: http://localhost:9000/docs
- ReDoc: http://localhost:9000/redoc

## Development Workflow

1. **Make changes** to backend or frontend code
2. **Backend changes** - The development server will auto-reload
3. **Frontend changes** - Vite will hot-reload in the browser
4. **Run tests** before committing:
   ```bash
   cd backend && pytest
   cd frontend && npm run test
   ```
5. **Commit changes** using conventional commit messages:
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

## Troubleshooting

### Port Already in Use

If ports 9000 or 5173 are in use, `start.sh` will automatically find the next available port.

### Database Issues

Reset the database:
```bash
rm backend/app.db
cd backend
source .venv/bin/activate
alembic upgrade head
python -c "from app.seed import seed_data; seed_data()"
```

### Docker Build Issues

Clean rebuild:
```bash
docker compose down -v
docker compose build --no-cache
docker compose up
```

### Frontend Build Errors

Clear caches:
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

## License

Copyright © 2024 Lloyds Banking Group
