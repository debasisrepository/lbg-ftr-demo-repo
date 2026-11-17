# TASK-8 Handoff: Cross-Channel Continuity (FR-013, FR-015)

## Implemented Endpoints

### Customer Scope

**GET /api/v1/cases/{case_reference}/continuity**
- Returns ContinuityPackage with context_version, customer_issue_summary, structured_context, shared_field_names, current_state, recent_updates, and channel_history
- Requires customer scope and customer_party_id match
- Returns 404 if case not found
- Response includes persisted continuity context when available, builds on-demand otherwise

**POST /api/v1/cases/{case_reference}/handoffs**
- Records channel handoff with from_channel, to_channel, and context_presented_flag
- Requires customer scope and customer_party_id match
- Sets case.continuity_state to "refresh_pending"
- Creates audit entry for handoff
- Returns 201 with {"message": "Handoff recorded"}
- Returns 404 if case not found

### Colleague Scope

**GET /api/v1/colleague/cases**
- Query parameter: customer_party_id (required)
- Query parameters: limit (default 20, max 100), offset (default 0)
- Returns Page of ColleagueCaseSummary with items, total, limit, offset
- Requires colleague scope
- Entitlement check: denials return 403 with audit entry
- Each summary includes: case_reference, issue_type, issue_title, current_lifecycle_state, current_status_label, opened_at

**GET /api/v1/colleague/cases/{case_reference}**
- Returns continuity package with colleague fields only
- Requires colleague scope
- Entitlement check: denials return 403 with audit entry
- Creates audit entry for colleague access
- Response includes: context_version, case_reference, customer_party_id, issue_type, issue_title, issue_summary, current_state, current_status, owner, expected_by_at, recent_updates (customer-visible only), channel_history

## Data Model

### ContinuityContext
- case_id, package_version, structured_context_json, llm_safe_payload_json, colleague_payload_json
- restricted_fields_excluded_flag, last_channel, last_presented_at
- effective_from, effective_to, is_current
- Unique index on (case_id, is_current=True)

### ChannelHandoff
- case_id, from_channel, to_channel, context_presented_flag
- handoff_timestamp, correlation_id
- CHECK constraints on from_channel and to_channel: mobile_app, chat, phone, branch, colleague_desktop, ai_assistant

## Services

### ContinuityService
- get_package(case_reference, customer_party_id) → dict: Get continuity package for customer-scoped access
- record_handoff(case_reference, customer_party_id, from_channel, to_channel, context_presented_flag, correlation_id) → None: Record handoff and set continuity_state to refresh_pending
- colleague_retrieve(case_reference, colleague_reference, correlation_id) → dict: Retrieve case for colleague with entitlement check and audit
- list_colleague_cases(customer_party_id, limit, offset) → (list, int): List cases for a customer (colleague scope)
- refresh_if_pending(case_id) → None: Refresh continuity package if state is refresh_pending

### ContinuityPackageBuilder
- Pure function builder with allow-list filtering
- build(case, owner, expected_by, recent_events, handoffs, context_version) → dict: Build full continuity package
- colleague_view(case, owner, expected_by, recent_events, handoffs, context_version) → dict: Build colleague-filtered view
- Uses /app/config/continuity_allow_list.yaml with structured_context, colleague_payload, and llm_safe_payload keys

## Background Job

### ContinuityRefreshJob
- Runs every CONTINUITY_SWEEP_INTERVAL_SECONDS (default 60)
- Finds cases where continuity_state = "refresh_pending"
- Calls ContinuityService.refresh_if_pending() for each case
- Closes current context, builds new package, inserts new context, sets continuity_state = "package_current"
- Started in app lifespan alongside IncidentIngestJob

## Seed Data

### CP-MOCK1 (user1/CUST-002)
- 1 continuity_contexts record with package_version=1
- 2 channel_handoffs: mobile_app→chat, chat→phone
- Handoffs timestamped 1 hour ago and 30 minutes ago
- Continuity context includes structured_context_json, llm_safe_payload_json, colleague_payload_json

## Test Coverage

### Unit Tests (tests/unit/test_continuity_service.py)
- ContinuityPackageBuilder.build() and colleague_view()
- ContinuityService.get_package() with persisted context
- ContinuityService.record_handoff()
- ContinuityService.colleague_retrieve()
- ContinuityService.list_colleague_cases()
- ContinuityService.refresh_if_pending()

### Integration Tests (tests/integration/test_continuity_integration.py)
- GET /api/v1/cases/{case_reference}/continuity
- POST /api/v1/cases/{case_reference}/handoffs
- GET /api/v1/colleague/cases with customer_party_id
- GET /api/v1/colleague/cases/{case_reference}

### Acceptance Tests (tests/acceptance/test_continuity_acceptance.py)
- Case initiated in one channel can be retrieved in another
- Channel change does not create duplicate case
- Receiving channel can access approved continuity context
- Authorized colleagues can retrieve active case
- Retrieved context includes latest approved status, owner, expected-by, recent updates

## Architecture Notes

- ContinuityRepository implements repository pattern for continuity_contexts and channel_handoffs
- ContinuityService orchestrates continuity package retrieval, handoff recording, and refresh
- ContinuityPackageBuilder is a pure function with no side effects, uses allow-list filtering
- Background job processes refresh_pending cases asynchronously
- Colleague endpoints enforce entitlement checks and audit all access
- Handoffs set continuity_state to refresh_pending, triggering async refresh
- Continuity contexts use effective_from/effective_to and is_current for temporal validity
- Allow-list configuration in YAML defines field exposure for structured_context, colleague_payload, llm_safe_payload

## Dependencies

Depends on:
- TASK-4 (events, history): CaseEvent, HistoryRepository for recent_events
- TASK-3 (case service): Case, CaseRepository for case retrieval
- Ownership models: CaseOwnership, ExpectedByCommitment for continuity package

Used by:
- Future UI tasks for displaying continuity packages and recording handoffs
- Future agent tasks for AI-assisted context retrieval
