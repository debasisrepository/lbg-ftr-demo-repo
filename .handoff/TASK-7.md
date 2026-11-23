# TASK-7 Handoff: Backend Payment Review and Approval

## Endpoints Added

This task adds three endpoints: GET /api/v1/payments/{payment_id}, GET /api/v1/payments, and POST /api/v1/payments/{payment_id}/submit.

### GET /api/v1/payments/{payment_id}
**Purpose:** E-08 - Retrieve single payment status and details  
**Authentication:** Required (Bearer token)  
**Request:** Path parameter `payment_id` (UUID)  
**Response:** `PaymentResponse` with full payment details including:
- `payment_id`, `current_state`, `next_action`
- `customer_visible_status` (Sent/Pending/Failed or null)
- `status_message`, `is_submitted`, `do_not_resubmit`
- `payment_reference`, `amount_minor`, `currency`
- `source_account` (account_id, display_name, masked_account_identifier)
- `payee` (payee_id, payee_name, masked_account_identifier)
- `review_version`, `review_fingerprint`
- `created_at`, `updated_at`

**Error codes:** 401 (session_invalid), 403 (entitlement_denied), 404 (not_found)

---

### GET /api/v1/payments
**Purpose:** E-09 - List customer's payments or reconnect by idempotency key  
**Authentication:** Required (Bearer token)  
**Query parameters:**
- `idempotency_key` (optional, 8-64 chars) - reconnect to payment created/submitted with this key
- `page` (optional, default 1, minimum 1)
- `page_size` (optional, default 20, range 1-50)

**Response:** `PaymentListResponse` containing:
- `items`: Array of `PaymentResponse` objects
- `total`: Total number of matching payments
- `page`: Current page number
- `page_size`: Items per page

**Behavior:**
- With `idempotency_key`: Returns 0-1 items (the payment for that key, if any)
- Without `idempotency_key`: Returns customer's payments, newest first
- Empty result when key not found or no payments exist

**Error codes:** 401 (session_invalid), 422 (validation_error)

---

### POST /api/v1/payments/{payment_id}/submit
**Purpose:** E-11 - Approve and submit payment (approval step only; fraud/submission added in later tasks)  
**Authentication:** Required (Bearer token)  
**Headers:** `Idempotency-Key` (required, 8-64 chars matching `[A-Za-z0-9_-]`)  
**Path parameter:** `payment_id` (UUID)  
**Request body:** `PaymentSubmitRequest` containing:
- `review_version` (integer ≥ 1) - review version being approved
- `review_fingerprint` (string, exactly 64 chars) - SHA-256 fingerprint of approved review
- `approval` object:
  - `method`: "passcode" (only method in this tier)
  - `passcode`: string (4-12 chars) - customer's passcode for step-up

**Processing flow:**
1. Idempotency check - same key + body returns stored result with header `Idempotent-Replayed: true`
2. Same key + different body returns 422 `idempotency_key_reuse`
3. Verify payment is in `review_ready` or `awaiting_dynamic_link_approval` state
4. Verify `review_version` and `review_fingerprint` match current payment values
5. Request CIAM step-up approval bound to review fields and fingerprint
6. CIAM verifies passcode (bcrypt check against sandbox_credentials)
7. Create `authentication_events` row linking to payment_intent
8. Failed/abandoned approval:
   - State: `approval_failed_or_abandoned`
   - `is_submitted`: false
   - `customer_visible_status`: null
   - `next_action`: "start_new_payment"
   - Message: "Payment not sent. No money was sent."
9. Successful approval:
   - Create `dynamic_link_approvals` row (approval_outcome='success', all 15 columns populated)
   - Compare approval details with canonical intent (source account, payee, amount, currency, reference, version, fingerprint)
   - Any mismatch rejects execution → `approval_failed_or_abandoned`
   - Match moves to `fraud_check_in_progress` (actual fraud call added in next task)
   - `is_submitted`: false (not yet submitted)
   - `customer_visible_status`: null
   - Message: "Payment not sent. No money was sent." (until fraud/submission steps complete)

**Response:** `PaymentResponse` (same shape as E-08)  
**Response headers:** `Idempotent-Replayed: true` if replay

**Error codes:**
- 400 `payment_state_invalid` - payment not in submittable state
- 401 `session_invalid` or authentication failed
- 404 `not_found` - payment does not exist or not caller's
- 409 `review_changed` - review_version doesn't match current
- 409 `review_fingerprint` mismatch
- 422 `validation_error` or `idempotency_key_reuse`
- 503 `payments_unavailable` - payments capability disabled

---

## Database Schema Changes

### dynamic_link_approvals table
All 15 columns implemented:
- `id` (UUID, PK)
- `payment_intent_id` (UUID, FK to payment_intents, indexed)
- `review_version` (INTEGER, CHECK ≥ 1)
- `review_fingerprint` (VARCHAR(64))
- `source_account_reference` (VARCHAR(64))
- `payee_id` (UUID, FK to payees, indexed)
- `approved_amount_minor` (BIGINT, CHECK > 0)
- `approved_currency` (CHAR(3))
- `approved_reference_text` (VARCHAR(18))
- `approval_challenge_reference` (VARCHAR(128))
- `signed_approval_reference` (VARCHAR(256), nullable)
- `approval_outcome` (VARCHAR(12), CHECK IN ('pending','success','failed','abandoned','expired'), default 'pending')
- `approved_at` (TIMESTAMPTZ, nullable)
- `correlation_id` (VARCHAR(64), indexed)
- `created_at`, `updated_at` (TIMESTAMPTZ)

**Constraints:**
- CHECK `ck_dla_success_complete`: approval_outcome ≠ 'success' OR (approved_at IS NOT NULL AND signed_approval_reference IS NOT NULL)
- Partial UNIQUE index on (payment_intent_id, review_version) WHERE approval_outcome = 'success'

**Indexes:**
- `ix_dla_payment` on payment_intent_id
- `ix_dla_payee` on payee_id
- `ix_dla_correlation` on correlation_id
- Partial unique index for one successful approval per payment+version

---

## Seed Data

**Uses existing seed data from TASK-1 through TASK-6:**
- Customer: Alex Taylor (CUST-SYNTH-001), passcode "Pass1234" (bcrypt hashed in sandbox_credentials)
- Account: Current Account ending 1234, eligible for payments
- Payees: 3 saved_active payees (Jamie Clarke, Priya Patel, K Evans Lettings)

**No additional seed data required for this task.**

---

## State Machine Flows

### Approval Flow (E-11)
```
review_ready
  → awaiting_dynamic_link_approval (CIAM approval requested)
    → approval_failed_or_abandoned (wrong passcode OR fingerprint mismatch)
       [terminal for this attempt; customer can start new payment]
    → fraud_check_in_progress (successful approval, approval matches intent)
       [next task will add actual fraud call and continue flow]
```

### Never-Submitted States (customer_visible_status = null)
- `draft`
- `review_ready`
- `awaiting_dynamic_link_approval`
- `approval_failed_or_abandoned`
- `fraud_check_in_progress` (until fraud call completes)
- `warning_presented`, `stopped_after_warning` (added in next task)

### Status Messages by State
- `review_ready`: "Payment not sent yet. Review and approve it to send."
- `approval_failed_or_abandoned`: "Payment not sent. No money was sent."
- `fraud_check_in_progress`: "Payment not sent. No money was sent." (changes in next task)

---

## Acceptance Criteria Coverage

### FR-PAY-007 (Review with dynamic linking data)
✅ Customer sees critical payment details before approval (source account, payee, amount, reference)  
✅ Approved details match payment later submitted (fingerprint verification)  
✅ Changing critical field increments review_version and invalidates earlier approvals  
✅ Review step identifies payment (reference, account name, payee name, amount)

### FR-PAY-008 (Dynamic-linking approval)
✅ Payment cannot enter execution without successful approval  
✅ Approval bound to specific reviewed payment details (SHA-256 fingerprint over 4 fields + version)  
✅ Failed/abandoned approval leaves payment unexecuted (approval_failed_or_abandoned state)  
✅ Customer receives clear outcome (status_message, next_action populated)

---

## Testing

**All 23 tests passing:**
- 11 unit tests in `test_payments_approval_service.py`
- 7 integration tests in `test_payments_approval_integration.py`
- 9 acceptance tests in `test_payments_approval_acceptance.py`

**Key test coverage:**
- Successful approval flow → fraud_check_in_progress
- Failed approval (wrong passcode) → approval_failed_or_abandoned
- Review version/fingerprint mismatch → 409 errors
- Idempotency replay returns same result with header
- GET /payments/{id} returns payment details
- GET /payments lists customer payments
- GET /payments?idempotency_key reconnects to specific payment

---

## Known Limitations (By Design)

1. **Fraud checking stubbed:** E-11 moves to `fraud_check_in_progress` but does not call fraud engine. Actual fraud call, warning presentation, hold handling added in TASK-8.

2. **No actual submission:** Payment stays in `fraud_check_in_progress` with `is_submitted=false`. Submission to payments hub added in later task.

3. **Passcode-only approval:** Biometric approval deferred (FR-AUTH-004 out of scope).

4. **No warning/hold states:** `warning_presented`, `stopped_after_warning`, `held_for_review` added in TASK-8.

5. **customer_visible_status remains null:** Sent/Pending/Failed states assigned only after fraud/submission complete (later tasks).

---

## Next Task Integration Points

**TASK-8 should:**
1. After successful approval in E-11, call fraud decisioning engine
2. Handle allow/warn/hold outcomes
3. Add E-12 endpoint (POST /payments/{id}/warning-decision)
4. Add `scam_check_outcomes` table rows
5. Continue to submission for 'allow' outcome
6. Present warning for 'warn' outcome (with E-12 to handle customer decision)
7. Move to `held_for_review` for 'hold' outcome
8. Update state machine flow to reach `completed`/`failed`/`rejected` terminal states
9. Set `customer_visible_status` to Sent/Pending/Failed as appropriate

**E-12 endpoint (POST /payments/{id}/warning-decision) is NOT in this task - it will be added in TASK-8.**

**Files to extend in TASK-8:**
- `app/services/payment_orchestration_service.py` - add fraud call after approval succeeds
- `app/routers/payments.py` - add E-12 endpoint  
- `app/adapters/fraud_engine_sandbox_adapter.py` - implement fraud check method
- `app/models/scam_check_outcome.py` - complete model
- `app/repositories/scam_check_outcome_repository.py` - create repository

---

## Configuration

**Environment variables used:**
- `DATABASE_URL` - database connection
- `RATE_LIMIT_ENABLED` - rate limiting toggle
- Seed credentials loaded from `backend/dev.env` or `backend/.env.example`

**No new environment variables introduced.**

---

## API Contract Verification

All endpoints follow architecture contract:
- Prefix: `/api/v1` ✅
- Field naming: snake_case ✅
- Error responses: `ErrorResponse` with detail, status_code, error_code, correlation_id ✅
- Idempotency: E-07 and E-11 require `Idempotency-Key` header ✅
- Same key + same body returns stored result with `Idempotent-Replayed: true` ✅
- Same key + different body returns 422 `idempotency_key_reuse` ✅
- Pagination: E-09 uses standard `{items, total, page, page_size}` shape ✅

---

## Example Usage

### Create payment review (E-07, from TASK-6)
```
POST /api/v1/payments
Headers: Authorization: Bearer <token>, Idempotency-Key: payment-001
Body: {
  "source_account_id": "...",
  "payee_id": "...",
  "amount_minor": 10000,
  "currency": "GBP",
  "payment_reference": "Rent payment"
}
Response 201: { payment_id, current_state: "review_ready", review_version: 1, review_fingerprint: "abc...", ... }
```

### Approve and submit payment (E-11, new in TASK-7)
```
POST /api/v1/payments/{payment_id}/submit
Headers: Authorization: Bearer <token>, Idempotency-Key: submit-001
Body: {
  "review_version": 1,
  "review_fingerprint": "abc...",
  "approval": {
    "method": "passcode",
    "passcode": "Pass1234"
  }
}
Response 200: { payment_id, current_state: "fraud_check_in_progress", is_submitted: false, ... }
```

### Get payment status (E-08, new in TASK-7)
```
GET /api/v1/payments/{payment_id}
Headers: Authorization: Bearer <token>
Response 200: { payment_id, current_state, payment_reference, amount_minor, ... }
```

### List payments (E-09, new in TASK-7)
```
GET /api/v1/payments?page=1&page_size=20
Headers: Authorization: Bearer <token>
Response 200: { items: [...], total: 5, page: 1, page_size: 20 }
```

### Reconnect by idempotency key (E-09, new in TASK-7)
```
GET /api/v1/payments?idempotency_key=submit-001
Headers: Authorization: Bearer <token>
Response 200: { items: [{ payment_id, current_state, ... }], total: 1, page: 1, page_size: 1 }
```
