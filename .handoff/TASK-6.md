# TASK-6 Handoff: Backend Feature B4 - Payment Initiation

## Endpoints Implemented

All endpoints mounted under `/api/v1` prefix:

### E-07: POST /api/v1/payments
Create payment review (payment initiation).

**Headers:**
- `Authorization: Bearer {token}` (required)
- `Idempotency-Key: string (8-64 chars)` (required)
- `X-Correlation-ID: string (max 64 chars)` (optional)

**Request:**
```json
{
  "source_account_id": "uuid",
  "payee_id": "uuid",
  "amount_minor": 100000,
  "currency": "GBP",
  "payment_reference": "string (1-18 chars)"
}
```

**Response 201:**
```json
{
  "payment_id": "uuid",
  "current_state": "review_ready",
  "next_action": "review_and_approve",
  "customer_visible_status": null,
  "status_message": "Payment not sent yet. Review and approve it to send.",
  "is_submitted": false,
  "do_not_resubmit": false,
  "payment_reference": "string",
  "amount_minor": 100000,
  "currency": "GBP",
  "source_account": {
    "account_id": "uuid",
    "display_name": "string",
    "masked_account_identifier": "****1234"
  },
  "payee": {
    "payee_id": "uuid",
    "payee_name": "string",
    "masked_account_identifier": "****5678"
  },
  "review_version": 1,
  "review_fingerprint": "64-char SHA-256 hex",
  "created_at": "2026-11-22T12:00:00Z",
  "updated_at": "2026-11-22T12:00:00Z"
}
```

**Errors:**
- 404: Source account or payee not found
- 403: Not entitled to use this account
- 422: Validation error or idempotency_key_reuse
- 503: payments_unavailable

**Behavior:**
- Creates PaymentIntent in state `draft` then `review_ready` with `review_version` 1
- Computes `review_fingerprint` as SHA-256 over: source_account_reference, payee_id, amount_minor, currency, payment_reference_text, review_version
- Checks source account is entitled and payee is `saved_active`
- Checks `payments` capability is not `unavailable`
- Idempotency: Same key + same body returns stored result (replay)
- Same key + different body returns 422 `idempotency_key_reuse`
- Writes `idempotency_records` with operation_type `payment_review`

### E-10: PATCH /api/v1/payments/{payment_id}
Change payment review (edit critical fields before approval).

**Headers:**
- `Authorization: Bearer {token}` (required)
- `X-Correlation-ID: string (max 64 chars)` (optional)

**Request:**
```json
{
  "expected_review_version": 1,
  "source_account_id": "uuid (optional)",
  "payee_id": "uuid (optional)",
  "amount_minor": 150000,
  "payment_reference": "Updated reference"
}
```

**Response 200:**
```json
{
  "payment_id": "uuid",
  "current_state": "review_ready",
  "next_action": "review_and_approve",
  "customer_visible_status": null,
  "status_message": "Payment not sent yet. Review and approve it to send.",
  "is_submitted": false,
  "do_not_resubmit": false,
  "payment_reference": "Updated reference",
  "amount_minor": 150000,
  "currency": "GBP",
  "source_account": { ... },
  "payee": { ... },
  "review_version": 2,
  "review_fingerprint": "new 64-char SHA-256 hex",
  "created_at": "2026-11-22T12:00:00Z",
  "updated_at": "2026-11-22T12:01:00Z"
}
```

**Errors:**
- 404: Payment not found
- 409: `review_changed` (expected_review_version mismatch) or `review_not_editable` (state not `review_ready` or `awaiting_dynamic_link_approval`)
- 422: Validation error

**Behavior:**
- Allowed only in `review_ready` or `awaiting_dynamic_link_approval` states
- Changes to critical fields (source account, payee, amount, reference) increment `review_version`
- Recomputes `review_fingerprint` with new values and new version
- Returns 409 `review_not_editable` if payment is in later state (fraud check, submission, etc.)
- Returns 409 `review_changed` if `expected_review_version` doesn't match current `review_version`

## Database Tables

### payment_intents (all 23 columns)
- `id` (UUID, PK)
- `customer_profile_ref_id` (UUID, FK)
- `source_account_reference` (VARCHAR(64))
- `payee_id` (UUID, FK)
- `amount_minor` (BIGINT, >0)
- `currency` (CHAR(3), default 'GBP')
- `payment_reference_text` (VARCHAR(18), length ≥ 1)
- `payment_channel` (VARCHAR(8), default 'mobile', IN ('mobile'))
- `initiation_type` (VARCHAR(24), default 'saved_payee_payment', IN ('saved_payee_payment'))
- `review_version` (INTEGER, ≥ 1, default 1)
- `review_fingerprint` (VARCHAR(64))
- `current_state` (VARCHAR(32), default 'draft', IN 15 states)
- `customer_visible_status` (VARCHAR(8), NULL or IN ('Sent','Pending','Failed'))
- `do_not_resubmit` (BOOLEAN, default FALSE)
- `expected_arrival_time` (TIMESTAMPTZ, NULL)
- `payments_hub_reference` (VARCHAR(64), NULL)
- `hold_latest_decision_at` (TIMESTAMPTZ, NULL)
- `customer_reviewed_at` (TIMESTAMPTZ, NULL)
- `submitted_at` (TIMESTAMPTZ, NULL)
- `last_state_changed_at` (TIMESTAMPTZ, default CURRENT_TIMESTAMP)
- `row_version` (INTEGER, ≥ 1, default 1)
- `correlation_id` (VARCHAR(64), NULL)
- `created_at` (TIMESTAMPTZ, default CURRENT_TIMESTAMP)
- `updated_at` (TIMESTAMPTZ, default CURRENT_TIMESTAMP, onupdate CURRENT_TIMESTAMP)

### idempotency_records (all columns)
- `id` (UUID, PK)
- `customer_profile_ref_id` (UUID, FK)
- `operation_type` (VARCHAR(16), IN ('payment_review', 'payment_submit'))
- `idempotency_key` (VARCHAR(64))
- `request_fingerprint` (VARCHAR(64))
- `payment_intent_id` (UUID, FK)
- `resolution_state` (VARCHAR(24), default 'in_progress', IN ('in_progress','resolved_success','resolved_failure','linked_existing_result'))
- `response_status_code` (INTEGER, 100-599, NULL)
- `returned_response_reference` (VARCHAR(128), NULL)
- `replay_count` (INTEGER, ≥ 0, default 0)
- `correlation_id` (VARCHAR(64), NULL)
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)
- Unique constraint: `(customer_profile_ref_id, operation_type, idempotency_key)`

## Seed Data

Use existing seed customers from TASK-3 handoff:

| Customer | Account IDs | Payee IDs |
|----------|-------------|-----------|
| Alex Taylor (CUST-SYNTH-001) | Query from account_read_models where customer_profile_ref_id = '00000000-0000-0000-0000-000000000001' | Query from payees where customer_profile_ref_id = same |
| Jordan Smith (CUST-SYNTH-002) | Query from account_read_models where customer_profile_ref_id = '00000000-0000-0000-0000-000000000002' | Query from payees where customer_profile_ref_id = same |

Each customer has:
- 3 accounts (from TASK-4 seed)
- 3 payees (from TASK-5 seed): Jamie Clarke, Priya Patel, K Evans Lettings

## Backend Flows

### E-07: Create Payment Review
1. Check `payments` capability is not `unavailable` (503 if unavailable)
2. Get source account by ID, scoped to customer (404 if not found)
3. Check source account entitlement via EntitlementSandboxAdapter (403 if denied)
4. Get payee by ID, scoped to customer, check `payee_status` is `saved_active` (404 if not found/not active)
5. Compute request fingerprint (SHA-256 of canonical request body)
6. Compute review fingerprint (SHA-256 over source_account_reference, payee_id, amount_minor, currency, payment_reference_text, review_version=1)
7. Create or get existing via IdempotencyRepository:
   - If existing with same fingerprint: increment replay_count, return stored payment (replay)
   - If existing with different fingerprint: 422 `idempotency_key_reuse`
   - If new: create PaymentIntent and IdempotencyRecord
8. Create PaymentIntent:
   - `current_state`: `review_ready`
   - `review_version`: 1
   - `review_fingerprint`: computed SHA-256
   - `customer_visible_status`: NULL
   - `is_submitted`: FALSE
   - `do_not_resubmit`: FALSE
9. Mark IdempotencyRecord as `resolved_success` with status_code 201
10. Commit transaction
11. Return PaymentResponse with `next_action` = `review_and_approve`

### E-10: Change Payment Review
1. Get payment by ID, scoped to customer (404 if not found)
2. Check state is `review_ready` or `awaiting_dynamic_link_approval` (409 `review_not_editable` otherwise)
3. Check `expected_review_version` matches current `review_version` (409 `review_changed` if mismatch)
4. Apply changes to critical fields:
   - If `source_account_id` changed: get new account (404 if not found), update `source_account_reference`
   - If `payee_id` changed: get new payee (404 if not found/not active), update `payee_id`
   - If `amount_minor` changed: update `amount_minor`
   - If `payment_reference` changed: update `payment_reference_text`
5. If any critical field changed:
   - Increment `review_version`
   - Recompute `review_fingerprint` with new values and new version
   - Update `updated_at` timestamp
6. Commit transaction
7. Return updated PaymentResponse

## Adapters Scaffolded (not called in this task)

### FraudEngineSandboxAdapter
- `check_payment_fraud_risk(...)` → raises NotImplementedError
- Scaffolded for E-11 (submit payment)

### PaymentsHubAdapter
- `submit_payment(...)` → raises NotImplementedError
- `get_payment_status(...)` → raises NotImplementedError
- Scaffolded for E-11 and E-08

## Testing

Run tests:
```bash
cd /repos/lbg-ftr-demo-repo/backend
source .venv/bin/activate
pytest tests/test_payments_service.py tests/test_payments_integration.py tests/test_payments_acceptance.py -v
```

## Frontend Integration Notes

1. **Create payment:** POST to `/api/v1/payments` with `Idempotency-Key` header and body containing source_account_id, payee_id, amount_minor, currency, payment_reference
2. **Review screen:** Show the returned `source_account`, `payee`, `amount_minor`, `currency`, `payment_reference` - exactly the four dynamic-linked fields
3. **Change payment:** PATCH to `/api/v1/payments/{payment_id}` with `expected_review_version` and new values for fields to change
4. **Handle review version:** Store `review_version` from response; send it as `expected_review_version` when changing
5. **Handle 409 review_changed:** Reload payment and show customer that payment was changed by another action
6. **Handle 409 review_not_editable:** Show customer that payment is past the review stage
7. **Handle 422 idempotency_key_reuse:** Generate a new idempotency key for the new payment attempt
8. **Idempotency:** Generate one idempotency key per payment journey; reuse same key if retrying after transient failure
9. **State interpretation:** 
   - `is_submitted` = FALSE and `current_state` = "review_ready" → show "Review and approve" action
   - `next_action` = "review_and_approve" → enable approval button
10. **Correlation:** Always read `X-Correlation-ID` from response header for support tracing

## State Machine

This task implements the first two states:
- `draft` → `review_ready` (on create)
- `review_ready` ← (on change, stays in review_ready with incremented version)

Future states (not implemented in this task):
- `awaiting_dynamic_link_approval` (E-11)
- `fraud_check_in_progress` (E-11)
- `warning_presented` (E-12)
- `held_for_review` (E-11)
- `submission_in_progress` (E-11)
- `completed`, `failed`, `rejected` (E-08, E-11)

## Review Fingerprint Computation

```
canonical = "{source_account_reference}|{payee_id}|{amount_minor}|{currency}|{payment_reference_text}|{review_version}"
review_fingerprint = SHA256(canonical).hexdigest()
```

Example:
```
ACC-CUST-SYNTH-001-001|550e8400-e29b-41d4-a716-446655440000|100000|GBP|Rent payment|1
→ SHA-256 → 64-character hex string
```

## Configuration

No new environment variables for this task. Uses existing:
- `SECRET_KEY`: Required
- `DATABASE_URL`: Database connection

## Acceptance Criteria Verified

**FR-PAY-002: Initiate a payment to a saved payee**
- ✅ Customer can choose valid source account and saved payee before payment submission
- ✅ Customer can provide payment amount and payment reference within defined journey
- ✅ App prevents payment submission until required payment-entry information is present (422 validation)
- ✅ Started payment remains pending approval until required approval step completes (`review_ready` state, `is_submitted` = false)

**FR-PAY-003: Capture payment reference**
- ✅ Customer can enter payment reference before submitting payment
- ✅ Entered payment reference is shown during payment review (in PaymentResponse)
- ✅ Customer can see which attempted payment status refers to (reference always present)
- ✅ Reference shown matches reference approved by customer (after change, new reference with new version)
