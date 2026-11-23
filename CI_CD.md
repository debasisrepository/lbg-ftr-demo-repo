# CI/CD Pipeline Documentation

## Overview

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the Release 1 Mobile Banking Platform. The pipeline automates building, testing, scanning, and deploying the application across multiple environments.

## Pipeline Architecture

### CI Pipeline (`.github/workflows/ci.yml`)

The CI pipeline runs on every push and pull request to `main` and `develop` branches. It consists of the following stages:

```
┌─────────────────────────────────────────────────────────────┐
│                     CI Pipeline                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Backend Lint &  │    │  Frontend Lint & │              │
│  │  Type Check      │    │  Type Check      │              │
│  └────────┬─────────┘    └────────┬─────────┘              │
│           │                       │                         │
│           ▼                       ▼                         │
│  ┌──────────────────┐    ┌──────────────────┐              │
│  │  Backend Tests   │    │  Frontend Tests  │              │
│  │  (PostgreSQL)    │    │  (Unit + Build)  │              │
│  └────────┬─────────┘    └────────┬─────────┘              │
│           │                       │                         │
│           └───────┬───────────────┘                         │
│                   ▼                                         │
│          ┌──────────────────┐                               │
│          │   E2E Tests      │                               │
│          │   (Playwright)   │                               │
│          └────────┬─────────┘                               │
│                   │                                         │
│                   ▼                                         │
│          ┌──────────────────┐                               │
│          │  Docker Build &  │                               │
│          │  Stack Test      │                               │
│          └────────┬─────────┘                               │
│                   │                                         │
│          ┌────────┴─────────┐                               │
│          │                  │                               │
│          ▼                  ▼                               │
│  ┌──────────────┐   ┌──────────────┐                       │
│  │  Security    │   │ Integration  │                       │
│  │  Scan        │   │ Report       │                       │
│  └──────────────┘   └──────────────┘                       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### CD Pipeline (`.github/workflows/cd.yml`)

The CD pipeline runs on:
- Pushes to `main` branch (deploys to staging)
- Version tags (`v*.*.*`) (deploys to production)
- Manual workflow dispatch

```
┌─────────────────────────────────────────────────────────────┐
│                     CD Pipeline                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│          ┌──────────────────────┐                           │
│          │  Build & Publish     │                           │
│          │  Container Images    │                           │
│          └──────────┬───────────┘                           │
│                     │                                       │
│                     ▼                                       │
│          ┌──────────────────────┐                           │
│          │  Deploy to Staging   │                           │
│          └──────────┬───────────┘                           │
│                     │                                       │
│                     ▼                                       │
│          ┌──────────────────────┐                           │
│          │  Smoke Test Staging  │                           │
│          └──────────┬───────────┘                           │
│                     │                                       │
│                     ▼                                       │
│          ┌──────────────────────┐                           │
│          │ Deploy to Production │  (tags only)              │
│          └──────────┬───────────┘                           │
│                     │                                       │
│                     ▼                                       │
│          ┌──────────────────────┐                           │
│          │ Smoke Test Production│                           │
│          └──────────────────────┘                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## CI Pipeline Details

### 1. Backend Lint & Type Check

**Purpose:** Ensures code quality and type safety for Python backend code.

**Steps:**
- Python 3.11 setup
- Install dependencies from `pyproject.toml`
- Run `ruff` linter (checks for E, F, W, C, N violations)
- Run `mypy` for static type checking

**Failure Conditions:**
- Linting errors (except E501 - line too long)
- Type checking errors
- Import errors

### 2. Backend Tests

**Purpose:** Validates backend functionality with comprehensive test coverage.

**Infrastructure:**
- PostgreSQL 15 service container
- Python 3.11 with backend dependencies
- Coverage reporting enabled

**Steps:**
- Run Alembic migrations against PostgreSQL
- Execute full test suite (unit, integration, acceptance)
- Generate coverage reports (XML, HTML, terminal)
- Upload coverage to Codecov

**Test Categories:**
- **Unit tests:** Service layer business logic
- **Integration tests:** Database and repository operations
- **Acceptance tests:** Full API endpoint workflows

**Coverage Requirements:**
- Overall: >80%
- Critical paths (auth, payments): >90%

### 3. Frontend Lint & Type Check

**Purpose:** Ensures code quality and type safety for React/TypeScript frontend.

**Steps:**
- Node.js 22 setup with npm cache
- Install dependencies via `npm ci`
- Run ESLint for code quality
- Run TypeScript compiler for type checking

**Failure Conditions:**
- ESLint errors
- TypeScript compilation errors
- Missing type definitions

### 4. Frontend Tests

**Purpose:** Validates frontend components and builds production bundle.

**Steps:**
- Install dependencies
- Run Vitest unit tests with coverage
- Build production bundle with Vite
- Upload coverage reports
- Archive build artifacts

**Test Coverage:**
- Component rendering
- User interactions
- API client behavior
- Auth context state management

### 5. E2E Tests

**Purpose:** Validates complete user journeys across frontend and backend.

**Infrastructure:**
- PostgreSQL service container
- Backend with SQLite database
- Playwright with Chromium

**Test Scenarios:**
- User authentication (sign-in/sign-out)
- Account overview display
- Payment initiation and approval
- Warning and outcome flows
- Session reconnect and idempotency

**Steps:**
- Set up backend with migrations and seed data
- Install Playwright browsers
- Run E2E test suite
- Upload test results and reports

### 6. Docker Build & Stack Test

**Purpose:** Validates containerized deployment configuration.

**Steps:**
- Build backend and frontend Docker images
- Test SQLite compose stack
- Test PostgreSQL compose stack
- Verify health endpoints
- Archive Docker images

**Validation Checks:**
- Images build successfully
- Containers start and run
- Health endpoints return 200 OK
- Frontend serves correctly
- Database migrations apply

### 7. Security Scan

**Purpose:** Identifies security vulnerabilities in dependencies and code.

**Tools:**
- **Trivy:** Filesystem vulnerability scanning
- **Bandit:** Python security linter

**Checks:**
- Known CVEs in dependencies
- Insecure coding patterns
- Hardcoded secrets
- SQL injection risks
- Authentication bypasses

**Output:**
- SARIF report uploaded to GitHub Security
- JSON reports archived as artifacts

### 8. Integration Report

**Purpose:** Summarizes all CI pipeline results.

**Outputs:**
- Build status for all jobs
- Artifact inventory
- Coverage summaries
- Security findings summary

## CD Pipeline Details

### 1. Build & Publish Container Images

**Purpose:** Creates and publishes versioned container images.

**Registries:**
- GitHub Container Registry (ghcr.io)

**Image Tagging Strategy:**
- Branch name (e.g., `main`)
- Semantic version (e.g., `v1.2.3`, `1.2`, `1`)
- Git SHA (e.g., `sha-abc1234`)

**Images:**
- `ghcr.io/<org>/lbg-ftr-demo-repo/backend`
- `ghcr.io/<org>/lbg-ftr-demo-repo/frontend`

**Build Features:**
- Multi-stage builds for optimization
- Layer caching via GitHub Actions cache
- PostgreSQL support baked in (`.[postgres]`)

### 2. Deploy to Staging

**Trigger:** Push to `main` branch or manual dispatch

**Environment:**
- URL: `https://staging.lbg-ftr-demo.example.com`
- Database: Managed PostgreSQL
- Approval: None (automatic)

**Steps:**
1. Pull versioned container images
2. Apply database migrations (Alembic)
3. Update container orchestration (Kubernetes/ECS/etc.)
4. Run health checks
5. Notify deployment completion

**Rollback:** Automatic on health check failure

### 3. Smoke Test Staging

**Purpose:** Validates critical functionality in staging environment.

**Tests:**
- Login flow with seed credentials
- Account overview rendering
- Payment initiation (without real submission)
- API health endpoints

**Failure Handling:**
- Blocks production deployment
- Triggers notification
- Maintains previous staging version

### 4. Deploy to Production

**Trigger:** Version tag (`v*.*.*`) or manual dispatch

**Environment:**
- URL: `https://lbg-ftr-demo.example.com`
- Database: Managed PostgreSQL with PITR
- Approval: Required (GitHub environment protection)

**Prerequisites:**
- Successful staging deployment
- Passing staging smoke tests
- Manual approval

**Deployment Strategy:**
- Blue/green deployment recommended
- Database migrations with rollback plan
- Gradual traffic shifting (10% → 50% → 100%)
- Monitoring dashboards active

**Safety Checks:**
- Pre-deployment health check
- Database backup verification
- Read-only mode toggle available

### 5. Smoke Test Production

**Purpose:** Validates production deployment success.

**Tests:**
- Critical user journeys
- API health and readiness
- Authentication flow
- Database connectivity

**Monitoring:**
- Error rate < 0.1%
- Response time < 2s (p95)
- No increase in 5xx errors

### 6. Rollback Procedure

**Trigger:** Production smoke test failure

**Steps:**
1. Stop traffic to new version
2. Revert to previous container images
3. Rollback database migrations if necessary
4. Restore previous routing configuration
5. Verify health checks pass
6. Notify team of rollback

**Manual Rollback:**
```bash
# Revert to previous version
kubectl rollout undo deployment/backend
kubectl rollout undo deployment/frontend

# Check status
kubectl rollout status deployment/backend
kubectl rollout status deployment/frontend
```

## Environment Configuration

### Required Secrets

Configure these secrets in GitHub repository settings:

**CI Secrets:**
- `CODECOV_TOKEN` - Codecov upload token (optional)

**CD Secrets:**
- `GITHUB_TOKEN` - Provided by GitHub (automatic)
- `DEPLOY_STAGING_KEY` - Staging deployment credentials
- `DEPLOY_PRODUCTION_KEY` - Production deployment credentials
- `DATABASE_STAGING_URL` - Staging database connection
- `DATABASE_PRODUCTION_URL` - Production database connection

### Environment Variables

**Staging:**
```env
DATABASE_URL=<staging-postgres-url>
SECRET_KEY=<staging-secret-key>
CORS_ORIGINS=https://staging.lbg-ftr-demo.example.com
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_INACTIVITY_TIMEOUT_MINUTES=15
RATE_LIMIT_ENABLED=true
```

**Production:**
```env
DATABASE_URL=<production-postgres-url>
SECRET_KEY=<production-secret-key>
CORS_ORIGINS=https://lbg-ftr-demo.example.com
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_INACTIVITY_TIMEOUT_MINUTES=15
RATE_LIMIT_ENABLED=true
RATE_LIMIT_LOGIN_PER_ADDRESS_MAX_ATTEMPTS=5
```

## Monitoring & Alerts

### Pipeline Notifications

**Success:**
- GitHub commit status checks (green checkmark)
- Deployment notifications in pull requests

**Failure:**
- GitHub commit status checks (red X)
- Email to commit author
- Slack/Teams notification (if configured)

### Deployment Metrics

**Key Metrics:**
- Deployment frequency: Daily (staging), Weekly (production)
- Lead time: < 1 hour from merge to staging
- Change failure rate: < 5%
- Mean time to recovery: < 15 minutes

**Dashboards:**
- CI pipeline success rate
- Test coverage trends
- Build duration trends
- Deployment frequency

## Best Practices

### For Developers

1. **Run tests locally before pushing:**
   ```bash
   cd backend && pytest
   cd frontend && npm run test
   ```

2. **Check linting and types:**
   ```bash
   cd backend && ruff check app && mypy app
   cd frontend && npm run lint && npm run type-check
   ```

3. **Build Docker images locally:**
   ```bash
   docker compose build
   docker compose up -d
   ```

4. **Review CI results:**
   - Check all pipeline jobs pass
   - Review coverage reports
   - Address security findings

### For Release Managers

1. **Creating a release:**
   ```bash
   # Ensure main is clean
   git checkout main
   git pull origin main
   
   # Create and push version tag
   git tag -a v1.2.3 -m "Release version 1.2.3"
   git push origin v1.2.3
   ```

2. **Monitoring deployments:**
   - Watch GitHub Actions progress
   - Monitor staging smoke tests
   - Review production deployment approval
   - Verify production smoke tests

3. **Handling failures:**
   - Review failure logs in GitHub Actions
   - Assess impact and severity
   - Execute rollback if necessary
   - Create incident report

## Troubleshooting

### Common CI Failures

**Backend tests fail:**
- Check database migrations are up to date
- Verify test fixtures are correct
- Review recent code changes for breaking changes

**Frontend build fails:**
- Check Node.js version matches requirement
- Verify all dependencies are in package.json
- Review TypeScript errors

**E2E tests timeout:**
- Increase timeout values in playwright.config.ts
- Check backend startup logs
- Verify seed data is loading correctly

**Docker build fails:**
- Review Dockerfile syntax
- Check all COPY paths exist
- Verify base images are accessible

### Common CD Failures

**Deployment fails:**
- Verify secrets are configured
- Check deployment credentials
- Review infrastructure availability

**Health checks fail:**
- Review application logs
- Check database connectivity
- Verify environment variables

**Smoke tests fail:**
- Check environment URLs
- Verify seed data exists
- Review recent code changes

## Maintenance

### Regular Tasks

**Weekly:**
- Review security scan findings
- Update dependency versions
- Monitor test coverage trends

**Monthly:**
- Rotate deployment credentials
- Review and update pipeline configuration
- Archive old artifacts

**Quarterly:**
- Update base Docker images
- Review and optimize pipeline performance
- Audit access controls

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Alembic Migration Guide](https://alembic.sqlalchemy.org/)
- [Playwright E2E Testing](https://playwright.dev/)
