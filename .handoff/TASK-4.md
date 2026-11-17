# TASK-4 Handoff: Backend Feature B2 - Case Summary and Notifications

## Endpoints Implemented

### Case List and Detail
- GET /api/v1/cases
  - Query parameters: `lifecycle_state` (optional), `include_closed` (default true), `limit` (1-100, default 20), `offset` (>=0, default 0)
  - Returns: `Page` wrapper with `{items, total, limit, offset}` where items are `CaseSummary` objects
  - Ordered by `latest_meaningful_update_at desc`, then `opened_at desc`
  - Results scoped to caller's `customer_party_id`

- GET /api/v1/cases/{case_reference}
  - Returns: `CaseDetail` with current projections (status, owner, expected-by)
  - Read path uses stored projections only; no upstream adapter call
  - 404 when case belongs to another customer (prevents enumeration)
  - When no current expected_by row, returns `commitment_state=under_review` with approved wording

### Notifications
- GET /api/v1/notifications
  - Query parameters: `limit` (1-100, default 20), `offset` (>=0, default 0)
  - Returns: `Page` wrapper with `{items, total, limit, offset}` where items are `NotificationItem` objects
  - Results scoped to caller's `customer_party_id`

- POST /api/v1/notifications/open
  - Request body: `{deep_link_token: string}`
  - Validates token hash (SHA-256), checks expiry, sets `opened_at`, returns `{deep_link_target, case_reference}`
  - 404 for unknown token or token belonging to another customer
  - 410 Gone for expired token
  - Idempotent: repeat calls for already-opened notification succeed

## Response Shapes

### Page wrapper (generic)
```json
{
  "items": [...],
  "total": 10,
  "limit": 20,
  "offset": 0
}
```

### CaseSummary (in Page items)
```json
{
  "case_reference": "CP-MOCK1",
  "issue_type": "card_declined",
  "issue_title": "Card Declined",
  "current_lifecycle_state": "case_created",
  "status_code": "received",
  "status_label": "Received",
  "latest_meaningful_update_text": "Your case has been received...",
  "latest_meaningful_update_at": "2024-01-01T12:00:00Z",
  "owner": {
    "owner_team_code": "INTAKE_DEFAULT",
    "owner_semantic_label": "Intake Team",
    "owner_display_name": "Intake & Triage",
    "effective_from": "2024-01-01T12:00:00Z"
  },
  "expected_by": {
    "commitment_state": "under_review",
    "expected_by_at": null,
    "customer_explanatory_text": "We're reviewing the timing...",
    "confidence_basis": "initial",
    "effective_from": "2024-01-01T12:00:00Z"
  },
  "opened_at": "2024-01-01T12:00:00Z",
  "closed_at": null,
  "outcome_summary": null
}
```

### NotificationItem (in Page items)
```json
{
  "id": "uuid",
  "case_id": "uuid",
  "case_reference": null,
  "notification_type": "case_update",
  "safe_preview_text": "Your case has been updated",
  "deep_link_target": "case_view",
  "opened_at": "2024-01-01T13:00:00Z",
  "created_at": "2024-01-01T12:00:00Z"
}
```

## Seed Data

### Test Users
- `user1@example.com` / `user123` (CUST-002): Has existing case CP-MOCK1 with 2 notifications (1 opened, 1 new)
- `admin@example.com` / `admin123` (CUST-001): Admin user
- Other test users: user2-4 with no cases

### Seed Case for User1
- Case reference: `CP-MOCK1`
- Issue type: `card_declined`
- Status: `received` (Received)
- Owner: `INTAKE_DEFAULT` (Intake & Triage)
- Expected-by: `under_review` with explanatory text
- 2 notifications:
  - Notification 1: `opened_at` set (already opened)
  - Notification 2: `opened_at` null (new notification)

## Event Bus Integration

Event handler subscribed to:
- `CaseStatusChanged`
- `OwnerChanged`
- `ExpectedByChanged`
- `ProtectedActionRequested`
- `IncidentDeclared`

Maps event types to update types via `/app/config/update_type_map.yaml`, generates notification using template from `/app/config/notification_templates.yaml`, dispatches via `CorrespondenceAdapter` (sandbox mode).

## Key Files Modified/Created

### Schemas
- `app/schemas/case.py` - Added `Page[T]` generic wrapper

### Repositories
- `app/repositories/communication_repository.py` - NEW: `CommunicationRepository` with `by_source_event`, `by_token_hash`, `page_for_customer`

### Services
- `app/services/case_service.py` - Added `list_cases` method
- `app/services/communication_service.py` - NEW: `CommunicationService` with `handle_event`, `NotificationDispatcher`
- `app/services/history_service.py` - NEW: `HistoryService` with `build_pages`, `compute_is_superseded`

### Adapters
- `app/adapters/correspondence_adapter.py` - NEW: `CorrespondenceAdapter.send_push_notification` (sandbox)

### Configuration
- `app/config/notification_templates.yaml` - NEW: 5 templates (status_change, owner_change, expected_by_change, customer_action_requested, incident_update)
- `app/config/update_type_map.yaml` - NEW: Event type to update type mapping

### Routers
- `app/routers/cases.py` - Added GET /api/v1/cases endpoint
- `app/routers/notifications.py` - NEW: GET /api/v1/notifications, POST /api/v1/notifications/open

### Main App
- `app/main.py` - Mounted notifications router, subscribed event handlers in lifespan

### Seed
- `app/seed.py` - Added 2 CommunicationRecord and 2 NotificationRecord for user1's case

## Tests

### Unit Tests
- `tests/unit/test_communication_service.py` - Tests for event handling, dispatcher, notification generation

### Integration Tests
- `tests/integration/test_case_list_integration.py` - Tests for GET /api/v1/cases with pagination, filtering, customer scoping

### Acceptance Tests
- `tests/acceptance/test_notifications_acceptance.py` - Tests for GET /api/v1/notifications, POST /api/v1/notifications/open with various token states

## Acceptance Criteria Status

✅ GET /api/v1/cases with pagination returns `{items, total, limit, offset}`
✅ GET /api/v1/cases/{case_reference} returns CaseDetail with current projections
✅ GET /api/v1/notifications returns paginated notifications
✅ POST /api/v1/notifications/open with `{deep_link_token}` validates and opens
✅ Case summary displays latest approved status, owner, and expected-by data
✅ When no expected-by date is credible, summary states timing is under review
✅ Summary language is customer-readable (uses `customer_facing_text`)
✅ System sends notifications only for approved update types (5 types mapped)
✅ Notification content avoids sensitive case details (uses `safe_preview_text` only)
✅ Opening notification leads to authenticated journey (returns deep_link_target; frontend must enforce RequireAuth)
