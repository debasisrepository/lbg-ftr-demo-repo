# TASK-8 Handoff: Backend Feature B6 - Scam Checks and Warning

## Completed Backend Features

### Endpoints

**POST /api/v1/payments/{payment_id}/warning-decision**
- Request: `{"review_version": integer, "decision": "stop"|"continue"}`
- Returns: `PaymentResponse`
- Behavior:
  - Valid only when `current_state` is `warning_presented`
  - `stop`: moves to `stopped_after_warning`, `is_submitted=false`, clear "not sent" message
  - `continue`: only allowed when `policy_allows_continue=true`; writes `audit_events` row with `event_type="payment.warning_traversed"`, moves to `submission_in_progress`
  - Returns 403 `warning_continue_not_permitted` if continue requested when not allowed
  - Returns 400 `payment_state_invalid` if not in `warning_presented` state
  - Returns 409 `review_changed` if `review_version` doesn't match

**Extended POST /api/v1/payments/{payment_id}/submit (E-11)**
- Now includes fraud check flow after approval:
  - Calls `FraudEngineSandboxAdapter.check_payment_fraud_risk()` with inputs: device hash, payee age in days, CoP outcome category, amount band
  - Budget ~300ms for fraud call
  - Returns 503 `fraud_decisioning_unavailable` if unavailable; leaves payment unexecuted, disables `payments` capability
  - **allow**: creates `scam_check_outcomes` row with `risk_outcome='allow'`, moves to `submission_in_progress`, returns `PaymentResponse` with `customer_visible_status="Pending"`
  - **warn**: creates `scam_check_outcomes` row with `customer_decision='pending'`, `policy_allows_continue` from policy config, `customer_warning_presented_at` set, moves to `warning_presented`, returns `PaymentResponse` with `warning` populated
  - **hold**: creates `scam_check_outcomes` row with `hold_latest_decision_at` (within 4 business days), moves to `held_for_review`, returns `PaymentResponse` with `customer_visible_status="Pending"`, `do_not_resubmit=true`

### Database

**scam_check_outcomes table** (all 15 columns):
- `id` (UUID, PK)
- `payment_intent_id` (UUID, FK → payment_intents.id)
- `review_version` (INTEGER, CHECK ≥ 1)
- `fraud_engine_reference` (VARCHAR(128), nullable)
- `risk_outcome` (VARCHAR(12), CHECK IN ('allow','warn','hold','unavailable'))
- `decision_inputs` (JSON/JSONB)
- `decision_latency_ms` (INTEGER, CHECK ≥ 0 or NULL)
- `customer_warning_required` (BOOLEAN, default FALSE)
- `policy_allows_continue` (BOOLEAN, default FALSE)
- `customer_warning_presented_at` (TIMESTAMPTZ, nullable)
- `customer_decision` (VARCHAR(14), CHECK IN ('not_applicable','pending','stopped','continued'), default 'not_applicable')
- `customer_decision_at` (TIMESTAMPTZ, nullable)
- `hold_latest_decision_at` (TIMESTAMPTZ, nullable)
- `correlation_id` (VARCHAR(64))
- `created_at`, `updated_at` (TIMESTAMPTZ)
- Constraints: CHECK `ck_sco_continue_needs_policy`, CHECK `ck_sco_warn_flag`, UNIQUE (`payment_intent_id`, `review_version`)
- Indexes: `ix_sco_payment`, `ix_sco_correlation`

**Migration**: `alembic/versions/20261122_2400_add_scam_check_outcomes.py`

### Response Shapes

**PaymentResponse extended**:
- Added `warning` (object, optional): present only when `current_state` is `warning_presented`
  - `heading` (string): "Warning: This payment may be unsafe"
  - `body` (string): plain-language warning text
  - `allowed_actions` (array of strings): `["stop"]` or `["stop", "continue"]`
  - `policy_allows_continue` (boolean)
- Added `hold_latest_decision_at` (datetime, optional): present when `current_state` is `held_for_review`

### Fraud Decision Rules (Sandbox)

FraudEngineSandboxAdapter implements working-tier rules:
- **unavailable**: if simulated availability check fails
- **warn** (policy_allows_continue=false): if payee age < 1 day OR cop_outcome is "no_match"
- **hold**: if amount > £10,000 (1000000 minor)
- **warn** (policy_allows_continue=true): if amount > £5,000 (500000 minor)
- **allow**: otherwise

### Seed Data Usage

Tests use seeded customers (Alex Taylor CUST-SYNTH-001 with passcode Pass1234), seeded accounts, and seeded payees (Jamie Clarke, Priya Patel, K Evans Lettings).

### Governed Next Steps

- Warning `stop` always allowed; moves to `stopped_after_warning`, nothing submitted
- Warning `continue` only when `policy_allows_continue=true`; writes audit event, moves to `submission_in_progress`
- Hold shows Pending with do-not-resubmit text, reference, and `hold_latest_decision_at` within 4 business days

### Audit Trail

- `audit_events` row written with `event_type="payment.warning_traversed"` when warning continued
- `action_detail="warning_continued"`, `resource_type="payment_intent"`, `resource_reference=<payment_id>`

### Frontend Integration Notes

1. After E-11 submit, check `current_state`:
   - `warning_presented`: display warning UI with heading, body, and buttons for allowed_actions
   - `held_for_review`: show Pending with "We're checking this payment", reference, hold date, do-not-resubmit message
   - `submission_in_progress`: show Pending with "Don't send this payment again"

2. E-12 `/api/v1/payments/{payment_id}/warning-decision`:
   - Call with `{"review_version": 1, "decision": "stop"}` or `"continue"`
   - Handle 403 if continue not allowed
   - After stop: show "Payment not sent"
   - After continue: show Pending status

3. Payment reference always returned for identification

4. Use `next_action` field:
   - `acknowledge_warning`: show warning UI
   - `check_status`: show status screen
   - `start_new_payment`: return to payment entry

### Tests

All acceptance criteria for FR-PAY-009 and FR-PAY-010 covered:
- Warning presentation before execution
- Clear unsafe messaging
- No silent bypass of warnings
- Accessible warning content
- Available next steps shown
- Stop leaves unexecuted
- Continue records traversal
- Stopped payment not shown as sent

### Verification

- Unit tests: `tests/test_payments_fraud_service.py` (13 tests)
- Integration tests: `tests/test_payments_fraud_integration.py` (8 tests)
- Acceptance tests: `tests/test_payments_fraud_acceptance.py` (10 tests)
- All tests use seeded data, no mocking of database layer
