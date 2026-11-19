# Deliverability Fixes Summary

## Findings Fixed

### 1. [BLOCKER] dockerfile — PIP_TARGET variable name
**File changed**: `backend/Dockerfile`, `docker-compose.postgres.yml`

**Change**: Renamed `PIP_TARGET` to `INSTALL_SPEC` on line 21 of Dockerfile and in docker-compose.postgres.yml build args to avoid pip reading it as its own `--target` option.

**Verification**:
```bash
$ grep -n "INSTALL_SPEC\|PIP_TARGET" backend/Dockerfile docker-compose.postgres.yml
backend/Dockerfile:21:ARG INSTALL_SPEC=.
backend/Dockerfile:22:RUN pip install --no-cache-dir "$INSTALL_SPEC"
docker-compose.postgres.yml:22:        INSTALL_SPEC: ".[postgres]"
```

### 2. [BLOCKER] packaging — frontend Dockerfile reads shared_config.json
**Files changed**: `docker-compose.yml`, `frontend/Dockerfile`, `frontend/Dockerfile.dockerignore` (created)

**Change**: 
- Changed frontend build context from `./frontend` to `.` in docker-compose.yml
- Rewrote frontend Dockerfile to copy from wider context: `COPY shared_config.json /app/shared_config.json` and `COPY frontend/ /app/frontend/`
- Created `frontend/Dockerfile.dockerignore` to exclude other components' build artifacts

**Verification**:
```bash
$ grep -A3 "frontend:" docker-compose.yml
  frontend:
    build:
      context: .
      dockerfile: frontend/Dockerfile

$ grep "shared_config.json\|COPY frontend/" frontend/Dockerfile
COPY shared_config.json /app/shared_config.json
COPY frontend/package*.json /app/frontend/
COPY frontend/ /app/frontend/
COPY frontend/default.conf.template /etc/nginx/templates/default.conf.template
```

### 3. [BLOCKER] packaging — backend service missing x-preview-port
**File changed**: `docker-compose.yml`

**Change**: Added `x-preview-port: 9000` to backend service definition.

**Verification**:
```bash
$ grep -A15 "backend:" docker-compose.yml | grep "x-preview-port"
    x-preview-port: 9000
```

### 4. [BLOCKER] dead-route-link — /step-up route missing
**Files changed**: `frontend/src/pages/StepUpPage.tsx` (created), `frontend/src/App.tsx`

**Change**: 
- Created `StepUpPage.tsx` implementing step-up authentication UI with passcode entry and biometric support
- Added route `<Route path="/step-up" element={<StepUpPage />} />` to App.tsx
- Page calls backend endpoints `/auth/step-up` and `/auth/step-up/{reference}/verify`

**Verification**:
```bash
$ grep "step-up" frontend/src/App.tsx
import StepUpPage from './pages/StepUpPage'
            <Route path="/step-up" element={<StepUpPage />} />

$ ls -lh frontend/src/pages/StepUpPage.tsx
-rw-r--r--. 1 appuser appuser 10K Nov 19 17:30 frontend/src/pages/StepUpPage.tsx
```

### 5. [BLOCKER] product-stub — GET / handler
**File changed**: `backend/app/main.py`

**Change**: Modified root handler to query the database (RefCode table) to verify database connectivity instead of returning only static data. Now returns actual runtime status.

**Verification**:
```bash
$ grep -A10 "def root" backend/app/main.py
def root(db: Session = Depends(get_db)) -> dict[str, str]:
    """Root endpoint with database connectivity check"""
    from .models.ref_code import RefCode
    
    # Verify database connectivity by querying ref_code table
    try:
        db.query(RefCode).first()
        status = "running"
    except Exception:
        status = "database_unavailable"
```

### 6. [BLOCKER] product-stub — POST /auth/recovery handler
**File changed**: `backend/app/routers/auth.py`

**Change**: Implemented `start_recovery` endpoint to:
- Look up customer by username
- Create StepUpChallenge with purpose='sign_in_recovery'
- Create CustomerNotification of type 'credential_recovery'
- Persist both to database
- Return recovery reference

**Verification**:
```bash
$ grep -A20 "def start_recovery" backend/app/routers/auth.py | head -15
def start_recovery(
    request_body: RecoveryRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> RecoveryResponse:
    """
    Start account recovery flow.
    Creates a recovery challenge and sends notification.
    """
    from ..repositories.customer_repository import CustomerRepository
    from ..services.notification_service import NotificationService
    from ..models.session import StepUpChallenge
    from datetime import datetime, timedelta
    import uuid
```

### 7. [BLOCKER] python-types — payment_service.py lines 158-159
**File changed**: `backend/app/services/payment_validator.py`

**Change**: Fixed return type annotation from `tuple[object, object]` to `tuple[BankAccount, Payee]` and added proper imports for these model classes.

**Verification**:
```bash
$ cd backend && python -m mypy app/services/payment_service.py --ignore-missing-imports
Success: no issues found in 1 source file

$ grep "tuple\[BankAccount, Payee\]" backend/app/services/payment_validator.py
    ) -> tuple[BankAccount, Payee]:
```

### 8. [BLOCKER] untracked-source — frontend/src/lib/ files excluded
**File changed**: `.gitignore`

**Change**: Changed bare `lib/` pattern to anchored `/backend/lib/` on line 13 so it no longer matches `frontend/src/lib/` at any depth. Then staged the 6 previously-excluded files.

**Verification**:
```bash
$ git check-ignore -v frontend/src/lib/api-client.ts
# Returns nothing (not ignored)

$ git ls-files frontend/src/lib/
frontend/src/lib/api-client.ts
frontend/src/lib/auth-context.tsx
frontend/src/lib/device-bridge.ts
frontend/src/lib/money.ts
frontend/src/lib/scam-claim-reasons.ts
frontend/src/lib/validators.ts

$ grep "^lib/" .gitignore || grep "/backend/lib/" .gitignore
/backend/lib/
```

## Summary

All 8 blocker findings have been fixed:

1. ✅ PIP_TARGET renamed to INSTALL_SPEC in backend Dockerfile and compose args
2. ✅ Frontend Dockerfile now builds from wider context and includes shared_config.json
3. ✅ Backend service has x-preview-port: 9000
4. ✅ /step-up route implemented with full StepUpPage component
5. ✅ Root endpoint now queries database for real status
6. ✅ Recovery endpoint creates real challenge and notification records in database
7. ✅ Type errors fixed by correcting return type annotation in payment_validator
8. ✅ frontend/src/lib/ files now tracked in git after fixing .gitignore pattern

All changes preserve existing functionality and tests. No test modifications were made. Docker packaging kept in sync with start.sh behavior.
