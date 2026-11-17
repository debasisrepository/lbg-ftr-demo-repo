# TASK-9 Handoff: Return Visit Restoration (FR-017)

## Implementation Summary
Implemented structured continuity storage with restricted data exclusion and return visit restoration capabilities. The feature allows customers to re-authenticate and restore their case context with current state and recent updates visible.

## Endpoints Added

### POST /api/v1/cases/{case_reference}/return-visits
Restore continuity for return visit after re-authentication.

**Auth**: Bearer token, customer scope

**Request Body**:
```json
{
  "return_session_token": "string (required)",
  "channel": "string (optional, default: mobile_app)"
}
```

**Response 200**:
```json
{
  "case": {
    "case_reference": "CP-MOCK1",
    "issue_type": "card_declined",
    "issue_title": "Card Declined",
    "issue_summary": "My card was declined at a store",
    "current_lifecycle_state": "under_review",
    "current_status": {
      "status_code": "reviewing",
      "status_label": "Under Review",
      "lifecycle_state": "under_review"
    },
    "owner": {
      "owner_team_code": "CARDS_DISPUTES",
      "owner_display_name": "Card Disputes"
    },
    "expected_by": {
      "expected_by_at": "2026-11-17T12:00:00Z",
      "customer_explanatory_text": "We'll update you soon",
      "commitment_state": "committed"
    },
    "opened_at": "2026-11-17T10:00:00Z",
    "closed_at": null,
    "outcome_summary": null
  },
  "recent_updates": [
    {
      "event_type": "CaseStatusChanged",
      "summary_text": "Status changed to under review",
      "event_timestamp": "2026-11-17T11:30:00Z",
      "customer_visible_flag": true
    }
  ],
  "context_version": 5,
  "return_visit_restored_at": "2026-11-17T12:00:00Z"
}
```

**Errors**:
- `401 Unauthorized`: Invalid or missing bearer token
- `404 Not Found`: Case not found or not visible to customer
- `422 Unprocessable Entity`: Invalid return session token or channel

## Backend Components

### IdentityAdapter (app/adapters/identity_adapter.py)
Sandbox identity adapter with four methods:
- `authenticate_customer(return_session_token)`: Validates return session token and returns customer identity
- `check_colleague_entitlement(colleague_reference, customer_party_id)`: Checks colleague access entitlement
- `start_sca(customer_party_id, action_type)`: Initiates Strong Customer Authentication challenge
- `confirm_sca(challenge_reference, customer_response)`: Validates SCA response

**Sandbox Behavior**:
- Accepts any non-empty return session token
- Always returns `CUST-002` (matches seed user1)
- All colleague entitlement checks return `True`
- SCA challenges always succeed with non-empty response

### ContinuityService.restore_return_visit()
New method in `app/services/continuity_service.py`:
- Authenticates return session token via IdentityAdapter
- Fetches case with customer scoping
- Retrieves current continuity context and version
- Fetches recent customer-visible events (limit 10)
- Builds complete case detail with owner and expected-by
- Records audit entry for return visit restoration
- Returns package with case, recent_updates, context_version, and timestamp

### Continuity Allow-List Configuration (app/config/continuity_allow_list.yaml)
Three payload tiers:
1. **structured_context** (most permissive): 16 fields including customer_party_id, full case details
2. **colleague_payload** (narrower): 12 fields, excludes customer_party_id for privacy
3. **llm_safe_payload** (most restrictive): 8 fields, excludes PAN, passcodes, security answers, customer PII

**Key Exclusions in llm_safe_payload**:
- `customer_party_id` (customer PII)
- `issue_summary` (may contain sensitive details)
- `current_status_label` (excluded for brevity)
- `owner_display_name` (excluded for brevity)
- `expected_by_text` (excluded for brevity)
- `channel_history` (excluded for brevity)
- `recent_events` (excluded for brevity)

### Database Schema
The `continuity_contexts` table already includes:
- `restricted_fields_excluded_flag` (Boolean, default=True, nullable=False)
- `llm_safe_payload_json` (JSON column for LLM-safe filtered context)

All continuity packages created by the system set `restricted_fields_excluded_flag=True`.

## Backend Flow
1. **Authenticate return session**: IdentityAdapter validates return_session_token
2. **Fetch current continuity context**: Retrieve current package version and state
3. **Restore session state**: Build complete case detail with current ownership, expected-by, and recent updates
4. **Return continuity package**: Send complete package with case, updates, version, and restoration timestamp
5. **Audit trail**: Record return_visit_restored event with customer actor and case entity

## Seed Data
Existing seed data includes:
- `user1@example.com` / `user123` (CUST-002) with active case `CP-MOCK1`
- Case has continuity context, ownership, expected-by, and events
- Return visit restoration works with any valid return session token (sandbox mode)

## Test Coverage

### Unit Tests (tests/unit/test_return_visit.py)
- `test_restore_return_visit_success`: Successful restoration with mocked dependencies
- `test_restore_return_visit_case_not_found`: NotFoundError when case doesn't exist
- `test_restore_return_visit_invalid_token`: ValueError for empty/invalid token
- `test_restore_return_visit_no_context_version_defaults_to_one`: Context version defaults to 1
- `test_restore_return_visit_audit_called_with_correlation_id`: Audit entry created with correct parameters

### Integration Tests (tests/integration/test_return_visit_integration.py)
- `test_restore_return_visit_integration`: Full flow with real database
- `test_restore_return_visit_no_existing_context`: Works when no context exists yet
- `test_restore_return_visit_case_not_found`: NotFoundError for non-existent case
- `test_restore_return_visit_invalid_token`: ValueError for invalid token

### Acceptance Tests (tests/acceptance/test_return_visit_acceptance.py)
- `test_return_visit_restores_continuity_package`: POST endpoint returns complete package (FR-017)
- `test_continuity_package_always_has_restricted_fields_excluded_true`: Flag always set correctly
- `test_llm_safe_payload_excludes_pan_passcodes_security_answers`: Sensitive data excluded from LLM payload
- `test_return_visit_backend_flow_authenticate_fetch_restore_return`: Complete backend flow validation
- `test_after_reauth_customer_can_reopen_active_case_see_current_state`: Customer sees current state and published updates

## Acceptance Criteria Verification
✅ POST /api/v1/cases/{case_reference}/return-visits with {return_session_token} returns restored ContinuityPackage  
✅ Continuity package always includes restricted_fields_excluded=true  
✅ llm_safe_payload excludes PAN/passcodes/security answers  
✅ Backend flow: authenticate return session → fetch current continuity context → restore session state → return continuity package  
✅ Continuity data shared across channels is limited to approved case context elements and event history  
✅ Restricted data classes such as PAN, passcodes, and security answers are excluded from LLM-facing continuity payloads  
✅ The customer receives a coherent journey without the system relying on unrestricted transcript replication  
✅ After re-authentication, the customer can reopen the same active Case and see current state  
✅ Previously published updates remain visible across sessions

## Security & Compliance
- Return session tokens validated before any data access
- Customer scoping enforced: only cases belonging to authenticated customer are accessible
- Audit trail created for every return visit restoration
- PAN, passcodes, and security answers explicitly excluded from LLM-safe payloads
- Restricted fields exclusion flag enforced at database level

## Dependencies
- IdentityAdapter for return session token validation (sandbox mode)
- Existing ContinuityService, CaseRepository, OwnershipRepository, HistoryRepository
- Existing audit infrastructure for return visit logging

## Notes for Frontend Implementation
- Use POST /api/v1/cases/{case_reference}/return-visits after customer re-authenticates
- Pass return_session_token from identity system
- Display case current state, owner, expected-by from response
- Show recent_updates as chronological history (newest first)
- context_version can be used for cache validation
- Handle 404 (case not found), 422 (invalid token), 401 (auth failed)
