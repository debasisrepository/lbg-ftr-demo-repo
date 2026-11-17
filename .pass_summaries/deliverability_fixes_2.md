# Deliverability Fixes - Round 2
**Date:** 2026-11-17  
**Pass:** deliverability_fixes (round 2 of 3)  
**Commit:** dc84d3c

## Summary
All 4 deliverability blockers fixed successfully.

---

## Fix 1: Dockerfile - frontend node_modules exclusion
**Finding:** `COPY frontend/ ...` (line 18) runs after dependency install (line 15) and copies `frontend/node_modules/` from build context over the image's installed modules

**File Changed:** `Dockerfile.dockerignore`  
**Action:** Created new ignore file to exclude `frontend/node_modules/` and `frontend/dist/`

**Verification:**
```bash
$ grep "frontend/node_modules/" Dockerfile.dockerignore
frontend/node_modules/

$ grep "frontend/dist/" Dockerfile.dockerignore
frontend/dist/
```

---

## Fix 2: Packaging - seed command missing from container
**Finding:** `start.sh` line 152 runs `python -m app.seed 2>/dev/null` before starting backend, but nothing in the image/entrypoint does this

**File Changed:** `backend/docker-entrypoint.sh`  
**Action:** Updated entrypoint to run `python -m app.seed 2>/dev/null || true` after migrations, matching start.sh exactly. The seed module is already idempotent (checks for existing data before inserting).

**Verification:**
```bash
$ grep "python -m app.seed" backend/docker-entrypoint.sh
python -m app.seed 2>/dev/null || true
```

---

## Fix 3: Packaging - backend service port not published
**Finding:** Service `backend` sets `x-preview-port: 9000` but publishes no port (no `ports:`), so preview creates no Service for it

**File Changed:** `docker-compose.yml`  
**Action:** Changed `expose: ["9000"]` to `ports: ["9000:9000"]` while keeping `x-preview-port: 9000`

**Verification:**
```bash
$ grep -B2 "9000:9000" docker-compose.yml
      - backend-data:/data
    ports:
      - "9000:9000"

$ grep -A1 "x-preview-port: 9000" docker-compose.yml
    x-preview-port: 9000
    healthcheck:
```

---

## Fix 4: env-bootstrap - .env.tmp usage
**Finding:** Copies `.env.tmp` to `.env`, but `.env.tmp` does not exist in the repository

**File Changed:** `start.sh` (lines 153-159)  
**Action:** The finding misread the code - `.env.tmp` was only used as a temporary file during CORS_ORIGINS update (created from `.env`, modified, then moved back). Replaced this pattern with sed-based inline editing to eliminate any `.env.tmp` references and avoid confusion.

**Verification:**
```bash
$ grep "\.env\.tmp" start.sh
(no output - exit code 1 confirms no matches)

$ grep -A3 "Update CORS origins" start.sh
# Update CORS origins in .env before starting
if [ -f .env ]; then
    # Remove existing CORS_ORIGINS line and add new one using sed in-place
    if command -v sed >/dev/null 2>&1; then
```

**Note:** The actual env bootstrap happens at line 120 (`cp dev.env .env`) and was already correct. The committed `backend/dev.env` contains working local development values.

---

## Git Status
All changes committed:
```
commit dc84d3c Fix deliverability blockers - round 2
- Created Dockerfile.dockerignore to exclude frontend/node_modules/ and frontend/dist/
- Updated backend/docker-entrypoint.sh to run seed command matching start.sh
- Added ports mapping (9000:9000) to backend service in docker-compose.yml
- Removed .env.tmp usage from start.sh in favor of sed-based inline editing
```

---

## Files Modified
1. `Dockerfile.dockerignore` - created (new file)
2. `backend/docker-entrypoint.sh` - updated seed command to match start.sh
3. `docker-compose.yml` - added `ports: ["9000:9000"]` to backend service
4. `start.sh` - replaced .env.tmp pattern with sed inline editing

---

## Result
✅ All 4 deliverability blockers addressed
✅ Changes committed to main branch (dc84d3c)
✅ No test files or verification scaffolding created
