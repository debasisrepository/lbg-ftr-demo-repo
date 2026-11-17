# TASK-10: Backend Feature B8 - Protected Actions with SCA

## Implementation Summary

Implemented protected actions with Strong Customer Authentication (SCA) gate and case history endpoints per FR-029 and FR-032.

## API Endpoints

All endpoints require `customer` scope unless otherwise noted.

### POST /api/v1/cases/{case_reference}/actions

Start a protected action with SCA.

**Request:**
```json
{
  "action_type": "stop_card",
  "action_domain": "card",
  "action_payload": {
    "card_last_four": "1234",
    "reason": "lost"
  }
}
```

**Response (201):**
```json
{
  "action_id": "uuid-string",
  "sca_challenge_reference": "SCA-CHALLENGE-REF"
}
```

**Errors:**
- 404: Case not found
- 503: SCA service unavailable

### POST /api/v1/cases/{case_reference}/actions/{action_id}/sca-outcome

Report SCA outcome and execute or abort action.

**Request:**
```json
{
  "sca_outcome": "success",
  "sca_verification_token": "TOKEN-FROM-SCA"
}
```

**Values for sca_outcome:** `success`, `failed`, `abandoned`

**Response (200):**
```json
{
  "action_id": "uuid-string",
  "request_status": "released",
  "sca_outcome": "success",
  "management_api_reference": "MGMT-REF-123",
  "fallback_guidance_text": null,
  "completed_at": "2024-01-01T12:00:00Z"
}
```

When SCA fails or is abandoned:
```json
{
  "action_id": "uuid-string",
  "request_status": "not_executed",
  "sca_outcome": "failed",
  "management_api_reference": null,
  "fallback_guidance_text": "We were unable to stop your card automatically. Please call us immediately on 0345 300 0000 to secure your account.",
  "completed_at": "2024-01-01T12:00:00Z"
}
```

**Idempotent:** Repeat calls with same outcome return stored state. Different outcome after finalized returns 400.

**Errors:**
- 404: Action not found
- 400: Invalid request (e.g., different outcome after finalized)

### GET /api/v1/cases/{case_reference}/actions/{action_id}

Get protected action status.

**Response (200):**
```json
{
  "action_id": "uuid-string",
  "action_type": "stop_card",
  "action_domain": "card",
  "request_status": "pending_sca",
  "sca_outcome": "not_invoked",
  "sca_invoked_at": "2024-01-01T12:00:00Z",
  "sca_completed_at": null,
  "management_api_reference": null,
  "fallback_guidance_text": null,
  "completed_at": null,
  "created_at": "2024-01-01T12:00:00Z"
}
```

**Values for request_status:** `pending_sca`, `released`, `not_executed`
**Values for sca_outcome:** `not_invoked`, `success`, `failed`, `abandoned`

**Errors:**
- 404: Action not found
- 400: Invalid action_id format

### GET /api/v1/cases/{case_reference}/history

Get case history with pagination.

**Query Parameters:**
- `limit` (integer, 1-100, default 20): Number of events to return
- `offset` (integer, >=0, default 0): Offset for pagination
- `event_type` (string, optional): Filter by event type

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "sequence_number": 10,
      "event_type": "ProtectedActionRequested",
      "event_timestamp": "2024-01-01T12:00:00Z",
      "summary_text": "Protected action requested: stop_card",
      "customer_visible_flag": true,
      "actor_type": "customer",
      "actor_reference": null,
      "basis_type": null,
      "basis_reference": null,
      "lifecycle_from": null,
      "lifecycle_to": null
    },
    {
      "id": "uuid-string",
      "sequence_number": 11,
      "event_type": "ProtectedActionOutcome",
      "event_timestamp": "2024-01-01T12:05:00Z",
      "summary_text": "Protected action completed: stop_card",
      "customer_visible_flag": true,
      "actor_type": "customer",
      "actor_reference": null,
      "basis_type": null,
      "basis_reference": null,
      "lifecycle_from": null,
      "lifecycle_to": null
    }
  ],
  "total": 11,
  "limit": 20,
  "offset": 0
}
```

**Customer scope:** Only sees `customer_visible_flag=true` events, `actor_reference`, `basis_type`, `basis_reference`, `correlation_id` are null.

**Colleague scope:** Sees all events with full details including actor references.

**Event Types:** `CaseCaptured`, `CaseStatusChanged`, `OwnerChanged`, `ExpectedByChanged`, `ChannelHandoffRecorded`, `ProtectedActionRequested`, `ProtectedActionOutcome`

**Errors:**
- 404: Case not found

## State Machine

Protected action request follows this state machine:

1. **pending_sca** (initial state after POST /api/v1/cases/{case_reference}/actions)
   - SCA challenge issued
   - `sca_invoked_at` timestamp set
   - `sca_outcome = not_invoked`

2. **released** (after SCA success)
   - Action executed via ManagementApiAdapter
   - `sca_outcome = success`
   - `management_api_reference` set
   - `completed_at` timestamp set

3. **not_executed** (after SCA failure/abandoned or execution failure)
   - Action not executed
   - `sca_outcome = failed` or `abandoned`
   - `fallback_guidance_text` set from catalogue
   - `completed_at` timestamp set

## Fallback Guidance Catalogue

Configured in `/repos/lbg-ftr-demo-repo/backend/app/config/protected_actions.yaml`:

- **card_stop_card**: "Please call us immediately on 0345 300 0000 to secure your account."
- **card_replace_card**: "Please visit your nearest branch or call 0345 300 0000 for assistance."
- **card_update_limit**: "Please try again later or contact us on 0345 300 0000."
- **card_freeze_card**: "For immediate help, please call 0345 300 0000."
- **money_transfer**: "Please try again later or use telephone banking on 0345 300 0000."
- **money_standing_order**: "Please visit your nearest branch or call 0345 300 0000."
- **money_payment**: "Please try again or contact us on 0345 300 0000 for assistance."
- **money_direct_debit**: "Please call us on 0345 300 0000 or visit your nearest branch."

## Seed Data

Seeded for user1 (CUST-002) case CP-MOCK1:

1. **Protected Action Request (pending_sca)**:
   - ID: `00000000-0000-0000-0000-000000014001`
   - Action type: `stop_card`
   - Action domain: `card`
   - Request status: `pending_sca`
   - SCA invoked: 5 minutes ago
   - Allows testing GET /api/v1/cases/{case_reference}/actions/{action_id} and POST /api/v1/cases/{case_reference}/actions/{action_id}/sca-outcome flows

2. **Case Events (11 total)**:
   1. CaseCaptured
   2. OwnerChanged (INTAKE_DEFAULT → CARDS_DISPUTES)
   3. OwnerChanged (CARDS_DISPUTES → FRAUD_TEAM)
   4. OwnerChanged (FRAUD_TEAM → CARDS_DISPUTES)
   5. ExpectedByChanged (under_review → committed)
   6. ExpectedByChanged (committed → revised)
   7. CaseStatusChanged (case_created → under_review)
   8. CaseStatusChanged (under_review → awaiting_customer)
   9. CaseStatusChanged (awaiting_customer → in_progress)
   10. ChannelHandoffRecorded (mobile_app → chat)
   11. ProtectedActionRequested (stop_card)

## Key Implementation Details

- **ActionRepository**: Methods `open_request_for()`, `get_for_case()`, `update()`
- **ActionService**: Methods `start()`, `report_outcome()` with state machine logic
- **ManagementApiAdapter**: Sandbox mode returns mock reference `MGMT-{domain}-{type}-{correlation_id}`
- **IdentityAdapter**: Sandbox mode `start_sca()` returns mock challenge reference
- **State Transitions**: Enforced by CHECK constraints in database schema
- **Idempotency**: `report_outcome()` allows repeating same outcome, rejects different outcome after finalized
- **Events**: Appends `ProtectedActionRequested` and `ProtectedActionOutcome` to case_events
- **Audit**: Records all actions with correlation_id, category=action

## Test Coverage

- **Unit tests (8)**: ActionService state machine, error cases, idempotency
- **Integration tests (5)**: Full flow with database, success/failure paths
- **Acceptance tests (9)**: FR-029, FR-032 acceptance criteria including SCA requirements, fallback guidance, event recording

## Dependencies

- Identity adapter (Task 9) for SCA flow
- History service for event recording
- Case service for case retrieval
- Audit service for action logging

## Verification Commands

```bash
cd /repos/lbg-ftr-demo-repo/backend

# Unit tests
.venv/bin/python -m pytest tests/unit/test_action_service.py -v

# Integration tests
.venv/bin/python -m pytest tests/integration/test_action_integration.py -v

# Acceptance tests
.venv/bin/python -m pytest tests/acceptance/test_action_acceptance.py -v

# Lint
ruff check app/services/action_service.py
```
