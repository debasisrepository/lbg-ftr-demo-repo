# Deliverability Fixes - Round 2
**Date**: 2026-11-19
**Commit**: 03196a0

## Findings Fixed

### 1. ✅ Docker Compose - Backend Port Publishing
**Blocker**: `docker-compose.yml`: service `backend` sets `x-preview-port: 9000` but publishes no port (no `ports:`), so the preview creates no Service for it and nothing can reach it

**File**: `docker-compose.yml`

**Fix**: Added `ports: ["9000:9000"]` to backend service configuration between `volumes:` and `healthcheck:` sections.

**Verification**:
```bash
$ cat docker-compose.yml | grep -A2 "ports:"
    ports:
      - "9000:9000"
    healthcheck:
```

The backend service now publishes port 9000 on both the host and container, matching the x-preview-port setting.

---

### 2. ✅ Python Type Error - CustomerRepository Method
**Blocker**: `backend/app/routers/auth.py:166`: "CustomerRepository" has no attribute "get_by_username" [attr-defined]

**File**: `backend/app/routers/auth.py`

**Fix**: Changed method call from `customer_repo.get_by_username(request_body.username)` to `customer_repo.get_by_external_identity_ref(request_body.username)` on line 166.

The CustomerRepository class defines `get_by_external_identity_ref()` method, not `get_by_username()`.

**Verification**:
```bash
$ grep "get_by_external_identity_ref" backend/app/routers/auth.py
    customer = customer_repo.get_by_external_identity_ref(request_body.username)

$ python -m mypy backend/app/routers/auth.py --no-error-summary 2>&1 | grep -i "error" | head -5
(no output - no errors found)
```

The type error is resolved and mypy reports no attr-defined errors.

---

### 3. ✅ Frontend Build - DeviceBridge Method Name
**Blocker**: `frontend/package.json`: `npm run build` fails - `src/pages/StepUpPage.tsx(97,48): error TS2551: Property 'requestBiometric' does not exist on type 'DeviceBridge'. Did you mean 'requestBiometricProof'?`

**File**: `frontend/src/pages/StepUpPage.tsx`

**Fix**: Changed `handleBiometric` function to:
- Call `deviceBridge.requestBiometricProof('step-up')` instead of `deviceBridge.requestBiometric('step-up')`
- Handle the `BiometricProofResult` return type properly by checking `result.success` and `result.proof_data`
- Use `result.error_message` when biometric fails

The DeviceBridge interface defines `requestBiometricProof()` which returns `BiometricProofResult`, not a simple string.

**Verification**:
```bash
$ npm run build 2>&1 | grep -E "(error|✓ built)"
✓ built in 3.02s
```

The frontend builds successfully with no TypeScript errors.

---

## Summary

All three blockers from round 2 have been fixed:

1. **Docker packaging** - Backend service now publishes port 9000, enabling preview routing
2. **Python types** - Fixed method name to match actual CustomerRepository API
3. **Frontend build** - Fixed DeviceBridge method call to use correct interface method

All changes committed in git commit `03196a0`.

## No Cleanup Required

No temporary verification files, test scripts, or scaffolding were created in this pass. The changes were surgical fixes to existing source files only.
