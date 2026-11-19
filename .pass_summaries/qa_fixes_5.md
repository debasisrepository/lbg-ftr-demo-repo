# QA Fixes Round 5 Summary

## Final Result: ALL TESTS PASSING ✅

### Before and After Counts

**BEFORE (from pipeline measurement):**
- pytest: 190 passed, 0 failed, 190 collected
- vitest: 114 passed, 2 failed, 116 collected  
- playwright: 59 passed, 2 failed, 61 collected
- **TOTAL: 363 passed, 4 failed, 367 collected**

**AFTER (this round):**
- pytest: 190 passed, 0 failed, 190 collected (unchanged - no pytest failures)
- vitest: 116 passed, 0 failed, 116 collected (2 tests fixed)
- playwright: 61 passed, 0 failed, 61 collected (2 tests fixed)
- **TOTAL: 367 passed, 0 failed, 367 collected** ✅

## Root Cause Analysis and Fixes

All four failures shared a common root cause: **test selectors not matching actual component text**.

### Root Cause 1: Text Matcher Pattern Issue (2 vitest failures)

**Files Changed:**
- `frontend/src/__tests__/CopOutcomePanel.test.tsx` (line 21)
- `frontend/src/__tests__/AddPayeePage.test.tsx` (line 138)

**Problem:** Tests were searching for exact text `'Name matches'` using `getByText('Name matches')`, but the component renders `"Confirmation of Payee: Name matches"` where the prefix and title are concatenated into a single text node. The exact string matcher couldn't find a standalone "Name matches" substring.

**Fix:** Changed from exact string match to regex pattern:
```diff
- expect(screen.getByText('Name matches')).toBeInTheDocument()
+ expect(screen.getByText(/Name matches/)).toBeInTheDocument()
```

**Why this is correct:** The component intentionally prefixes the outcome with "Confirmation of Payee:" for clarity. The test should verify the outcome is present, not enforce an exact text node structure.

### Root Cause 2: Invalid Playwright Selector Syntax (1 playwright failure)

**File Changed:**
- `frontend/src/e2e/journey_add_payee_and_pay.spec.ts` (line 366)

**Problem:** Test used `button:has-text(/Edit|Change|Back/i)` which is invalid - Playwright's `has-text()` pseudo-class does not accept regex patterns. This caused a CSS parse error.

**Fix:** Changed to proper Playwright role selector:
```diff
- const editButton = page.locator('button:has-text(/Edit|Change|Back/i)')
+ const editButton = page.getByRole('button', { name: /Edit details/i })
```

**Why this is correct:** The AddPayeePage component has an "Edit details" button (line 273 of AddPayeePage.tsx) that appears after a successful CoP check. Using `getByRole` with regex is the correct Playwright pattern.

### Root Cause 3: Wrong Button Text (1 playwright failure)

**File Changed:**
- `frontend/src/e2e/journey_new_request_to_approval.spec.ts` (line 139)

**Problem:** Test expected a "Done" button on the payment outcome page, but the actual button text is "Back to accounts" (PaymentOutcomePage.tsx line 197).

**Fix:** Changed selector to match actual button text:
```diff
- const doneButton = page.locator('button:has-text("Done")')
+ const doneButton = page.getByRole('button', { name: /Back to accounts/i })
```

**Why this is correct:** The wireframe and product design specify "Back to accounts" as the primary action after a successful payment. The test was based on outdated expectations.

### Configuration Fix

**File Changed:**
- `frontend/playwright.config.ts` (lines 66, 74)

**Problem:** Playwright's `webServer` configuration had `reuseExistingServer: false`, preventing manual server startup for targeted test runs.

**Fix:** Changed to allow reuse in non-CI environments:
```diff
- reuseExistingServer: false,
+ reuseExistingServer: !process.env.CI,
```

**Why this is correct:** This matches the standard pattern for local development while preserving CI isolation.

## About the Unused Function

**`get_payment` in `backend/app/services/payment_service.py` (line 312):**

This function is defined but has no callers in the product code. It was superseded by `get_payment_with_details` (line 316), which is used in:
- `app/routers/payments.py` (lines 202, 241)

**Verdict:** This is legitimate dead code from the previous round's refactoring. The product correctly uses `get_payment_with_details` for all payment retrieval needs, and the simpler `get_payment` method is unreachable. No test failures are caused by its absence.

## Verification

All tests were re-run with services on ports 9421 (backend) and 5221 (frontend):

1. **vitest** (frontend unit tests): 116 passed in 3.49s
2. **playwright** (E2E tests): 61 passed in 1.7m
3. **pytest**: No changes needed (no failures in scope)

JUnit XML written to `.verification/playwright.xml` for pipeline validation.

## Cleanup

Removed all verification scaffolding:
- `backend/_start_server.py`, `backend/_stop_server.py`, `backend/_server.log`
- `frontend/_start_frontend.py`, `frontend/_stop_frontend.py`, `frontend/_frontend.log`

Kept for pipeline:
- `.verification/playwright.xml` (12KB, 61 test results)
- `.verification/pytest.xml` (38KB, from earlier run)
- `.verification/vitest.xml` (24KB, from earlier run)

## Summary

**ALL 4 FAILURES FIXED.** Every failing test identified by the pipeline now passes:
- 2 vitest failures: fixed by using regex matchers for partial text matching
- 2 playwright failures: fixed by using correct Playwright selectors and actual button text

No product code changes were required - all fixes were test-side corrections to match the existing, working UI implementation.
