# Deliverability Fixes - Round 3
**Date:** 2026-11-17  
**Status:** FIXED

## Blocker Fixed

### Fix 1: Dockerfile - .dockerignore file naming ✅
**Finding:** `frontend/Dockerfile` line 18 copies `frontend/node_modules/` from build context over installed dependencies because `Dockerfile.dockerignore` does not exclude it

**Root Cause:** Docker looks for `.dockerignore` at the build context root, not `Dockerfile.dockerignore`. The prior round created `Dockerfile.dockerignore` with correct exclusions, but Docker never read it.

**File:** `Dockerfile.dockerignore` → `.dockerignore` (renamed)

**Change:** Renamed `Dockerfile.dockerignore` to `.dockerignore` so Docker can find and apply the exclusion rules

**Verification:**
```bash
$ grep "frontend/node_modules/" .dockerignore
frontend/node_modules/

$ grep "frontend/dist/" .dockerignore
frontend/dist/

$ ls -la Dockerfile.dockerignore 2>&1
ls: cannot access 'Dockerfile.dockerignore': No such file or directory
```

The `.dockerignore` file now exists at the context root with the exclusions for `frontend/node_modules/` and `frontend/dist/`, preventing the host's node_modules from overwriting the container's installed dependencies during `COPY frontend/` at line 18.

## Commit
- `7f266d7` - Fix deliverability blocker - round 3: rename Dockerfile.dockerignore to .dockerignore

## Analysis
The second round created the correct content but used the wrong filename. Docker's `.dockerignore` lookup order is:
1. `<dockerfile-path>.dockerignore` (e.g., `frontend/Dockerfile.dockerignore`)
2. `.dockerignore` at the build context root

Since the build context is `.` (repo root) per `docker-compose.yml`, and there was no `frontend/Dockerfile.dockerignore`, Docker needed `.dockerignore` at the repo root. The rename resolves the blocker.
