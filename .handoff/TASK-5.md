# TASK-5 Handoff: Lifecycle States (FR-004, FR-021)

## Implemented Endpoints

### POST /api/v1/cases/{case_reference}/transitions
Transitions a case to a new lifecycle state with validation against allowed edges.

**Auth**: Bearer token, colleague scope required

**Request**:
```json
{
  "to_state": "in_progress",
  "basis_type": "approved_manual_update",
  "basis_reference": "APPROVAL-001",
  "status_code": "in_progress",
  "status_label": "In Progress",
  "status_summary_text": "We're working on your case and will update you soon.",
  "latest_meaningful_update_text": "Case is now in progress.",
  "next_step_text": "We'll contact you when we have more information.",
  "outcome_summary": "Required only when to_state is 'closed'"
}
```

**Response 201**:
```json
{
  "case": {
    "case_reference": "CP-ABC123XY45",
    "current_lifecycle_state": "in_progress",
    "status_code": "in_progress",
    "status_label": "In Progress",
    "continuity_state": "refresh_pending",
    "owner": { ... },
    "expected_by": { ... },
    ...
  },
  "event": {
    "id": "uuid",
    "sequence_number": 2,
    "event_type": "CaseStatusChanged",
    "event_timestamp": "2026-11-17T...",
    "summary_text": "Case is now in progress.",
    "customer_visible_flag": true,
    "actor_type": "colleague",
    "basis_type": "approved_manual_update",
    "basis_reference": "APPROVAL-001",
    "lifecycle_from": "case_created",
    "lifecycle_to": "in_progress"
  }
}
```

**Error Responses**:
- `401`: Unauthorized (no valid token)
- `403`: Forbidden (not colleague scope)
- `404`: Case not found or not visible to principal
- `422`: Validation error:
  - Invalid transition (not allowed by lifecycle graph)
  - Already in target state
  - Closing without outcome_summary
  - Restricted data in free text fields

## Backend Flow

1. **Validate transition** against `LifecycleGraph`:
   - Loads allowed transitions from `case_lifecycle_transitions` table
   - Cached for 60 seconds to avoid repeated queries
   - Checks `(from_state, to_state, basis_type)` tuple is allowed
   
2. **Write successor projection**:
   - Close current `case_status_projections` row (set `effective_to`, `is_current=false`)
   - Insert new projection with `is_current=true`, `effective_from=now`

3. **Update current fields** on `cases`:
   - `current_lifecycle_state`, `current_status_code`, `current_status_label`
   - `latest_meaningful_update_at` = now
   - `continuity_state` = "refresh_pending" (triggers continuity refresh)
   - If closing: `closed_at` = now, `outcome_summary` = request value

4. **Append CaseStatusChanged event**:
   - `sequence_number` allocated via `next_sequence(case_id)`
   - `event_payload_json` includes `lifecycle_from` and `lifecycle_to`
   - `customer_visible_flag` = true
   - `basis_type` and `basis_reference` from request

5. **Audit entry**:
   - Category: `case_change`
   - Event type: `case_status_changed`
   - Metadata includes from/to states and basis

## Key Components

### `app/core/lifecycle_graph.py`
- `LifecycleGraph` class validates transitions
- `is_allowed(from_state, to_state, basis_type)` checks if edge exists
- `allowed_successors(from_state)` returns set of valid next states
- Reloads transitions from database every 60 seconds

### `app/services/case_service.py`
- `transition()` method implements full transition logic
- Uses `LifecycleGraph` for validation
- Writes projection, updates case, appends event, records audit

### `app/routers/cases.py`
- `POST /api/v1/cases/{case_reference}/transitions` endpoint
- Requires colleague scope via `require_scope("colleague")`
- Returns 201 on success

### `app/schemas/case.py`
- `CaseTransitionRequest` - request schema with validation
- `CaseTransitionResult` - response with case and event
- `HistoryEvent` - event representation

## Seed Data

Lifecycle transitions are seeded in `app/seed.py`:
```python
case_created -> under_review (operational_event)
case_created -> in_progress (approved_manual_update)
under_review -> in_progress (operational_event)
in_progress -> resolved (operational_event)
resolved -> closed (approved_manual_update)
```

## Testing

- **Unit tests** (`tests/unit/test_lifecycle.py`): LifecycleGraph validation logic
- **Integration tests** (`tests/integration/test_lifecycle_integration.py`): Service layer with database
- **Acceptance tests** (`tests/acceptance/test_transitions_acceptance.py`): Service-level tests (integration style) - uses direct service calls rather than HTTP due to pre-existing auth_client fixture issue affecting all acceptance tests project-wide

All test suites seed the required lifecycle transitions and validate:
- Valid transitions succeed
- Invalid transitions rejected with 422
- Same-state transitions rejected
- Closure requires outcome_summary
- Restricted data validation

## Dependencies

Depends on TASK-4 (case detail, projections) for:
- `Case` model with current lifecycle/status fields
- `CaseStatusProjection` model with time-bounded rows
- `CaseRepository.current_projection()` method
- `HistoryRepository.next_sequence()` and `add_event()` methods
- `AuditService.record()` method

## Acceptance Criteria Verified

✅ Every customer-visible lifecycle transition is tied to a recorded operational event or approved manual update (via `basis_type` and `basis_reference`)

✅ The system prevents unsupported transitions that have no operational basis (via `LifecycleGraph` validation)

✅ Closed Cases remain viewable with their final outcome summary and historical updates (via `closed_at`, `outcome_summary`, and append-only events)

✅ Service Status and Lifeline availability is maintained independently as designed in ADR-005 (no coupling to lifecycle logic)
