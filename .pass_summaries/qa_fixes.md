# QA Fixes Summary

## ❌ VERIFICATION DID NOT PASS

**Final E2E Test Results (frontend/src/e2e):**
- BEFORE: 0 failures reported by pipeline (but conditional assertions masked issues)
- AFTER: 61 tests total, **37 passed, 24 not passing** (1 failure + 23 errors)
- Pass rate: 60.7% (37/61)

**Unit Test Results (not re-run per task instructions):**
- pytest: 190 passed (pipeline will verify)
- vitest: 115 passed (pipeline will verify)

## What Was Fixed

### 1. Conditional Assertion Fix (Primary Task Requirement) ✅
**File:** `frontend/src/e2e/journey_add_payee_and_pay.spec.ts:382`

**Problem:** Test used `if (await editButton.isVisible())` which made the test pass even when the button didn't exist.

**Fix:** Changed to unconditional assertion:
```typescript
// Before:
if (await editButton.isVisible()) {
  await editButton.click()
  await expect(page.locator('input#payee-name')).toBeVisible()
}

// After:
await expect(editButton).toBeVisible({ timeout: 5000 })
await editButton.click()
await expect(page.locator('input#payee-name')).toBeVisible()
```

### 2. Hardcoded Backend URL in E2E Tests ✅
**File:** `tests/e2e/02-authenticated-routes.spec.ts`

**Problem:** Test had hardcoded `http://127.0.0.1:9100` URLs from earlier E2E pass.

**Fix:** Added configurable `BACKEND_URL` environment variable:
```typescript
const BACKEND_URL = process.env.BACKEND_URL || 'http://127.0.0.1:9100';
```

### 3. Unauthenticated Page API Guard ✅
**File:** `tests/e2e/03-payment-flow.spec.ts`

**Problem:** Payment outcome page redirects to authenticated pages, causing 403 errors in unauthenticated test.

**Fix:** Added explicit API error allowances:
```typescript
apiGuard.allow(403, '/api/v1/accounts/overview');
apiGuard.allow(403, '/api/v1/profiles');
```

**Result:** Root config E2E tests (tests/e2e/) now pass: **9/9 passed** when run with `BACKEND_URL=http://127.0.0.1:9420`

### 4. Test Navigation Pattern Issues (Partial Fix)
**Files:** `frontend/src/e2e/journey_*.spec.ts`, `frontend/src/e2e/wireframe_05_*.spec.ts`, `frontend/src/e2e/wireframe_06_*.spec.ts`

**Problem:** Tests used `goto('/', { waitUntil: 'networkidle' })` expecting redirect, which timed out.

**Fix:** Changed to direct login navigation matching working test pattern:
```typescript
// Before:
await page.goto('/', { waitUntil: 'networkidle' })
await page.waitForURL('**/login', { timeout: 5000 }).catch(...)

// After:
await page.context().clearCookies()
await page.goto('/login')
await page.waitForLoadState('networkidle')
```

### 5. Wrong Form Selectors in Tests
**Files:** Multiple E2E spec files

**Problem:** Tests used `input[name="username"]` but SignInPage has `<input id="username">` with NO name attribute.

**Fix:** Changed selectors from `input[name="username"]` to `#username` and `input[name="password"]` to `#password` to match actual HTML.

## Remaining Failures (24 tests)

All remaining failures are in `frontend/src/e2e/` tests and fall into these categories:

### Journey Tests (8 failures)
- `journey_add_payee_and_pay.spec.ts` - 5 tests fail finding "Add payee" button or navigating payee flow
- `journey_new_request_to_approval.spec.ts` - 3 tests fail at various points in payment journey

**Root Cause:** These comprehensive journey tests attempt full user flows but encounter missing UI elements, navigation issues, or timing problems that indicate either:
1. Product functionality gaps (missing buttons/routes)
2. Test expectations misaligned with actual product behavior
3. Insufficient wait strategies for async operations

### Wireframe Tests (16 failures)
- `wireframe_02_proof.spec.ts` - 1 test
- `wireframe_05_payment_entry.spec.ts` - 7 tests
- `wireframe_06_payment_outcome.spec.ts` - 8 tests

**Common Patterns:**
- Cannot find expected buttons ("Add payee", navigation controls)
- Cannot complete payment flows
- Timeouts waiting for elements that may not render

### Test vs Product Issue Analysis

**Test Infrastructure Issues Fixed:**
- Wrong selectors ✓
- Wrong navigation pattern ✓
- Hardcoded URLs ✓
- Conditional assertions ✓

**Remaining Issues Appear To Be Product Gaps:**
The tests expect UI elements and flows that may not be fully implemented. Examples:
- "Add payee" button not found on pay-and-transfer page
- Payment outcome flows incomplete
- Navigation paths between pages missing or broken

## Files Changed

**Test Files Modified:**
1. `frontend/src/e2e/journey_add_payee_and_pay.spec.ts` - Fixed conditional assertion, navigation pattern, selectors
2. `frontend/src/e2e/journey_new_request_to_approval.spec.ts` - Fixed navigation pattern, selectors
3. `frontend/src/e2e/wireframe_05_payment_entry.spec.ts` - Fixed navigation pattern, selectors
4. `frontend/src/e2e/wireframe_06_payment_outcome.spec.ts` - Fixed navigation pattern, selectors
5. `tests/e2e/02-authenticated-routes.spec.ts` - Made backend URL configurable
6. `tests/e2e/03-payment-flow.spec.ts` - Added API guard allowances

**No Product Code Changed** - All changes were to test files to fix test infrastructure issues.

## Cleanup Performed

Deleted test scaffolding:
- `backend/_start_server.py`
- `backend/_stop_server.py`
- `backend/_server.log`
- `backend/_server.pid` (if present)
- `frontend/_start_frontend.py`
- `frontend/_stop_frontend.py`
- `frontend/_frontend.log`
- `frontend/_frontend.pid` (if present)
- `_fix_e2e_auth.py`

Kept:
- `.verification/` directory with test results (pytest.xml, vitest.xml, playwright.xml)
- `backend/.venv/`, `frontend/node_modules/` (gitignored)
- `backend/app.db`, `backend/e2e.db` (test databases)
- `backend/.env` (from dev.env as per earlier passes)

## Assessment

**The conditional assertion was fixed as required**, but fixing it exposed that the E2E test suite in `frontend/src/e2e/` has significant issues - 24 of 61 tests do not pass. The root config E2E tests (9 tests in `tests/e2e/`) all pass after fixes.

**The failing tests appear to expose product functionality gaps rather than pure test defects.** The tests expect:
- UI elements that don't exist ("Add payee" button)
- Navigation flows that aren't complete
- Payment entry/outcome screens with specific content

**Next Steps Recommendation:**
1. Product review: Determine which failing test expectations are correct vs. which tests have wrong expectations
2. Implement missing product functionality if tests are correct
3. OR update tests to match actual product scope if tests expect unimplemented features
