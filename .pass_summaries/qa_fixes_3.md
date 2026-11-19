# QA Fixes Round 3 Summary

## Result: PARTIAL IMPROVEMENT - 5 failures remain (down from 8)

Playwright tests improved from 53 passed / 8 not passing to **56 passed / 5 failures / 61 total**.

## BEFORE and AFTER Counts

### Playwright (E2E tests)
- **BEFORE**: 53 passed, 8 not passing (2 failures, 6 errors), 61 collected
- **AFTER**: 56 passed, 5 failures, 0 errors, 61 collected

### Backend (pytest - not re-run, unchanged)
- 190 passed, 0 not passing, 190 collected

### Frontend unit (vitest - not re-run, unchanged)  
- 116 passed, 0 not passing, 116 collected

### Combined
- **BEFORE**: 359 passed, 8 not passing (2 failures + 6 errors), 367 collected
- **AFTER**: 362 passed, 5 failures, 0 errors, 367 collected

## Root Causes Fixed

### 1. Incorrect button text in E2E tests (LARGEST CLUSTER - 6 errors eliminated)
**Root cause**: Tests expected button text that didn't match the actual UI.

**Tests affected**:
- `journey_add_payee_and_pay.spec.ts` - all 5 tests (clicking "Continue" instead of "Add payee")
- `wireframe_05_payment_entry.spec.ts` - 5 occurrences (clicking "Pay" instead of "Pay £X.XX")
- `wireframe_06_payment_outcome.spec.ts` - 7 occurrences (clicking "Pay" instead of "Pay £40.00")
- `journey_new_request_to_approval.spec.ts` - 2 occurrences (clicking "Pay" instead of "Pay £X.XX")

**Fix applied**:
- `journey_add_payee_and_pay.spec.ts` lines 101, 209, 261, 310, 360: Changed `button:has-text("Continue")` to `button:has-text("Add payee")` for initial form submission
- `journey_add_payee_and_pay.spec.ts` line 112: Changed `button:has-text("Save payee")` to `button:has-text("Continue")` (after CoP check)
- `wireframe_05_payment_entry.spec.ts` lines 79, 120, 139, 156, 175: Changed `button:has-text("Pay")` to include amount
- `wireframe_06_payment_outcome.spec.ts`: Changed all 7 occurrences from `button:has-text("Pay")` to `button:has-text("Pay £40.00")`
- `journey_new_request_to_approval.spec.ts` lines 186, 238: Changed to include amount

### 2. Missing £ symbol in payment button text (PRODUCT BUG)
**Root cause**: EnterPaymentPage button displayed "Pay 75.50" instead of "Pay £75.50".

**File**: `frontend/src/pages/EnterPaymentPage.tsx` line 247

**Fix applied**: Changed button text from:
```typescript
{preparing ? 'Preparing...' : `Pay ${amountGbp ? amountGbp : '£0.00'}`}
```
To:
```typescript
{preparing ? 'Preparing...' : `Pay ${amountGbp ? (amountGbp.startsWith('£') ? amountGbp : `£${amountGbp}`) : '£0.00'}`}
```

This ensures the button always shows "Pay £X.XX" format regardless of whether user types "75.50" or "£75.50".

### 3. Strict mode violations on duplicate text matches
**Root cause**: Tests used overly broad selectors that matched multiple elements.

**Fix applied**:
- `journey_add_payee_and_pay.spec.ts` lines 145-147: Added `.first()` to locators for payee name, amount, and reference
- `wireframe_06_payment_outcome.spec.ts` line 65: Added `.first()` to `text=/PAY/i` locator

### 4. Wrong sort code in test
**Root cause**: Test expected "04-00-04" but Jamie Clarke's seed data has "12-34-56".

**File**: `journey_new_request_to_approval.spec.ts` line 83

**Fix applied**: Changed `text=04-00-04` to `text=12-34-56`

### 5. Wrong URL pattern in validation tests  
**Root cause**: Tests expected `/payees/add` but actual route is `/add-payee`.

**Files**: `journey_add_payee_and_pay.spec.ts` lines 267, 316

**Fix applied**: Changed `toHaveURL(/\/payees\/add/)` to `toHaveURL(/\/add-payee/)`

## Failures That Remain (5 total)

### 1. journey_add_payee_and_pay › completes full journey
**Symptom**: `expect(locator).toBeVisible() failed` for "Payment to new payee" reference text  
**Line**: 147  
**Reason**: Reference field may not be displaying on review page, or text doesn't match exactly

### 2. journey_add_payee_and_pay › handles CoP mismatch
**Symptom**: Not detailed in latest run
**Likely**: Similar assertion issue with CoP outcome handling

### 3. journey_add_payee_and_pay › allows editing payee details after CoP check
**Symptom**: Not detailed in latest run  
**Likely**: Test expects edit functionality that doesn't exist or uses wrong selector

### 4. journey_new_request_to_approval › completes full payment journey
**Symptom**: `expect(locator).toBeVisible() failed` for `select#account`  
**Line**: 88  
**Reason**: Payment entry page doesn't have a `select#account` element - likely uses different selector or element type

### 5. wireframe_06_payment_outcome › displays sent payment outcome with reference
**Symptom**: `expect(locator).toBeVisible() failed` for "Jamie Clarke"  
**Line**: 69  
**Reason**: Payment outcome page may not display payee name, or uses different format

## Cleanup Completed

Deleted test scaffolding files:
- `backend/_start_server.py`
- `backend/_stop_server.py`  
- `backend/_server.log`
- `frontend/_start_frontend.py`
- `frontend/_stop_frontend.py`
- `frontend/_frontend.log`

Kept for pipeline:
- `.verification/playwright.xml` - 22,502 bytes, 61 tests, 5 failures
- `.verification/pytest.xml` - unchanged from prior pass
- `.verification/vitest.xml` - unchanged from prior pass
- `.venv/`, `node_modules/`, `app.db`, `e2e.db` - all in `.gitignore`

## Changes Summary

**Product code changes**:
1. `frontend/src/pages/EnterPaymentPage.tsx` - fixed button text to always include £ symbol

**Test code changes**:
2. `frontend/src/e2e/journey_add_payee_and_pay.spec.ts` - 12 button selector fixes, 2 URL pattern fixes, 3 strict mode fixes
3. `frontend/src/e2e/wireframe_05_payment_entry.spec.ts` - 5 button selector fixes
4. `frontend/src/e2e/wireframe_06_payment_outcome.spec.ts` - 7 button selector fixes, 1 strict mode fix
5. `frontend/src/e2e/journey_new_request_to_approval.spec.ts` - 2 button selector fixes, 1 sort code fix

## Next Steps for Round 4

The remaining 5 failures require inspection of the actual page elements:
1. Check ReviewApprovePage to see if reference field is conditionally hidden
2. Verify EnterPaymentPage account selector element - may be `select` without id, or different element type
3. Check PaymentOutcomePage to see what payee information is actually displayed
4. Consider if some assertions test features not yet implemented or incorrectly expect elements that don't exist

All 6 timeout errors eliminated - tests now fail with clear assertions rather than hanging.
