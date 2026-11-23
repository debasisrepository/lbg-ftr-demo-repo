# TASK-9 Handoff: Backend Feature B7 - Payment Hold and Outcomes

## Completed Backend Features

### E-11 Final Flow

**POST /api/v1/payments/{payment_id}/submit** now includes complete submission flow:
- After approval succeeds and fraud check returns "allow", payment moves to `submission_in_progress`
- **Outbox event written atomically** with state transition (`payment_outbox_events` row with `event_type="payment.submitted"`)
- Payment converged to `customer_visible_status` using ONE convergence function `_converge_customer_visible_status()`
- Outbox publisher (`workers/outbox_publisher.py`) polls pending events and submits to PaymentsHubAdapter
- **Hub response within 10s**: converges to `completed` (customer_visible_status="Sent")
- **No response within 10s**: converges to `pending_confirmation` (customer_visible_status="Pending", do_not_resubmit=true, message="Don't send this payment again")
- **Rejected**: converges to `rejected` (customer_visible_status="Failed", message="No money was sent")
- **Hold outcome** (from TASK-8): converges to `held_for_review` (customer_visible_status="Pending", hold_latest_decision_at shown, do_not_resubmit=true)

### Database Tables

**payment_outbox_events** (14 columns):
- `id` (UUID, PK)
- `payment_intent_id` (UUID, FK → payment_intents.id)
- `state_transition_id` (UUID, UNIQUE, nullable)
- `event_sequence` (INTEGER, CHECK ≥ 1)
- `event_type` (VARCHAR(48))
- `event_payload` (JSON/JSONB)
- `publish_state` (VARCHAR(12), CHECK IN ('pending','published','failed','retrying'), DEFAULT 'pending')
- `attempt_count` (INTEGER, CHECK ≥ 0, DEFAULT 0)
- `next_attempt_at` (TIMESTAMPTZ, nullable)
- `last_error_code` (VARCHAR(48), nullable)
- `published_at` (TIMESTAMPTZ, nullable)
- `event_stream_reference` (VARCHAR(128), nullable)
- `correlation_id` (VARCHAR(64))
- `created_at`, `updated_at` (TIMESTAMPTZ)
- Indexes: `ix_poe_payment`, `ix_poe_publish_state`, `ix_poe_next_attempt`, `ix_poe_correlation`

**payment_execution_statuses** (all columns):
- Payment hub submission results and scheme outcomes
- `scheme_outcome` IN ('accepted','rejected','pending','timeout','unknown')
- `expected_arrival_time` from hub (when available)
- `final_indicator` distinguishes final from interim status

**payment_status_projections** (19 columns):
- `payment_intent_id` (UUID, FK UNIQUE → payment_intents.id)
- `customer_profile_ref_id` (UUID, FK → customer_profile_refs.id)
- `payment_reference_text` (VARCHAR(18))
- `amount_minor` (BIGINT, CHECK > 0)
- `currency` (CHAR(3), DEFAULT 'GBP')
- `payee_display_name` (VARCHAR(120))
- `customer_visible_status` (VARCHAR(8), CHECK IN ('Sent','Pending','Failed'))
- `held_indicator` (BOOLEAN, DEFAULT FALSE)
- `unresolved_indicator` (BOOLEAN, DEFAULT FALSE)
- `do_not_resubmit` (BOOLEAN, DEFAULT FALSE, CHECK IF 'Pending' THEN TRUE)
- `expected_arrival_time` (TIMESTAMPTZ, nullable)
- `hold_latest_decision_at` (TIMESTAMPTZ, nullable)
- `last_event_sequence` (BIGINT, CHECK ≥ 0)
- `last_source_event_id` (VARCHAR(64))
- `as_of_timestamp` (TIMESTAMPTZ)
- `freshness_status` (VARCHAR(14), CHECK IN ('within_target','breached','unknown'), DEFAULT 'within_target')
- `provenance_reference` (VARCHAR(128))
- `projection_updated_at` (TIMESTAMPTZ)
- Constraint: `ck_psp_pending_no_resubmit` enforces do_not_resubmit=true when status='Pending'

**consumed_events** (5 columns):
- `consumer_name` (VARCHAR(32), CHECK IN ('read_model_accounts','read_model_payments','status_and_flags','notifications'))
- `event_id` (VARCHAR(64))
- `event_type` (VARCHAR(48))
- `correlation_id` (VARCHAR(64))
- `processed_at` (TIMESTAMPTZ)
- Unique index: `ix_ce_consumer_event` on (consumer_name, event_id) for idempotency

**Migration**: `alembic/versions/20261123_0010_add_outbox_execution_status_projection.py`

### Status Convergence (ONE Function)

`PaymentOrchestrationService._converge_customer_visible_status(state)` is the SINGLE function that maps internal states to customer-visible status:
- **Sent**: `completed` only
- **Pending**: `held_for_review`, `submission_in_progress`, `submitted_to_payments_hub`, `pending_confirmation`, `unknown_unresolved` (always with do_not_resubmit=true)
- **Failed**: `failed`, `rejected`
- **None** (not submitted): `draft`, `review_ready`, `awaiting_dynamic_link_approval`, `approval_failed_or_abandoned`, `fraud_check_in_progress`, `warning_presented`, `stopped_after_warning`

This function is called from:
- `approve_and_submit` when moving to submission_in_progress or held_for_review
- `record_warning_decision` when continuing after warning
- Outbox publisher when converging after hub response

### Outbox Publisher Worker

**workers/outbox_publisher.py**:
- Polls `payment_outbox_events` with `publish_state IN ('pending','retrying')` every 2 seconds
- For each pending event:
  - Gets payment intent (must be in `submission_in_progress`)
  - Calls `PaymentsHubAdapter.submit_payment()`
  - Hub response distribution (working tier):
    - 70%: accepted within 10s → converge to `completed` (Sent)
    - 20%: timeout (no response) → converge to `pending_confirmation` (Pending with do-not-resubmit)
    - 10%: rejected → converge to `rejected` (Failed)
  - Creates or updates `payment_execution_statuses` row
  - Marks outbox event as `published` or `failed` with retry schedule

### Event Consumers

**workers/consumers/read_model_payment_consumer.py**:
- Processes payment events into `payment_status_projections`
- Idempotent via `consumed_events` table
- Converges `payment.customer_visible_status` to projection row
- Sets `held_indicator`, `unresolved_indicator`, `do_not_resubmit` flags

**workers/consumers/read_model_account_consumer.py**, **status_consumer.py**, **notification_consumer.py**:
- Seam implementations with idempotency pattern
- Mark events as consumed to prevent replay

### Response Shapes

**PaymentResponse** (from E-07, E-08, E-09, E-10, E-11, E-12):
- `customer_visible_status`: "Sent", "Pending", "Failed", or null
- `do_not_resubmit`: always true when Pending
- `hold_latest_decision_at`: shown when held (within 4 business days)
- `expected_arrival_time`: shown only when hub supplies it (never guessed)
- `status_message`: plain-language text, Pending says "Don't send this payment again"

### Seed Data Usage

Tests use seeded customers:
- Alex Taylor (`CUST-SYNTH-001`, passcode `Pass1234`)
- Seeded accounts (Alice Murray `ACCT-SYNTH-001`, Robert Singh `ACCT-SYNTH-002`)
- Seeded payees (Jamie Clarke sort 04-00-04 ending 3321, Priya Patel sort 60-83-71 ending 7745, K Evans Lettings sort 20-45-77 ending 9842)

### Hold Outcomes (from TASK-8 integration)

When fraud engine returns "hold":
- Payment moves to `held_for_review`
- `customer_visible_status` converges to "Pending"
- `do_not_resubmit` set to true
- `hold_latest_decision_at` set to within 4 business days
- Shown as: "We're checking this payment" with payment reference and do-not-resubmit message

### Frontend Integration Notes

1. **E-11 submit** returns `PaymentResponse`:
   - Check `customer_visible_status`: "Sent", "Pending", or "Failed" (or null if not submitted)
   - `do_not_resubmit` always true for Pending states
   - Use `status_message` for display

2. **E-08 status check** (`GET /api/v1/payments/{payment_id}`):
   - Returns one converged status only
   - Shows payment reference for identification
   - `hold_latest_decision_at` shown when held
   - `expected_arrival_time` shown only when available from hub

3. **E-09 reconnect** (`GET /api/v1/payments?idempotency_key=...`):
   - Returns payment created/submitted under that key
   - Shows current status (may have changed since submission)

4. **Status display**:
   - **Sent**: "Payment sent successfully" (green indicator)
   - **Pending**: "Payment is being processed. Don't send this payment again" (amber indicator)
   - **Failed**: "Payment could not be completed" (red indicator)
   - Always show payment reference with status

### Verification

Acceptance criteria covered:
- **FR-PAY-011**: Hold handling - held shown as Pending with do-not-resubmit, hold_latest_decision_at, payment reference
- **FR-PAY-012**: Clear outcomes - one status only (Sent/Pending/Failed), no conflicts, Pending avoids duplicate behavior, Failed distinguishes from sent

### Tests

- `tests/test_payments_submission_service.py`: Unit tests for status convergence function
- `tests/test_payments_submission_integration.py`: Integration tests for outbox event writing
- `tests/test_payments_submission_acceptance.py`: Acceptance tests for FR-PAY-011 and FR-PAY-012
- `tests/test_outbox_publisher.py`: Unit tests for outbox repository and publisher logic

### Endpoints Summary

- **POST /api/v1/payments** (E-07): Create review, returns PaymentResponse with `current_state="review_ready"`
- **PATCH /api/v1/payments/{payment_id}** (E-10): Change review before approval
- **POST /api/v1/payments/{payment_id}/submit** (E-11): Approve, fraud check, write outbox, submit via publisher, return PaymentResponse with Sent/Pending/Failed
- **POST /api/v1/payments/{payment_id}/warning-decision** (E-12): Stop or continue after warning, writes outbox on continue
- **GET /api/v1/payments/{payment_id}** (E-08): Get status with one converged customer_visible_status
- **GET /api/v1/payments** (E-09): List or reconnect by idempotency_key
