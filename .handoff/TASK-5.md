# TASK-5 Handoff: Backend Feature B3 - Balance Availability and Saved Payees

## Implemented Endpoints

### GET /api/v1/payees
- **Purpose**: View and select saved payees for payment entry
- **Authentication**: Required (bearer token)
- **Request**:
  - Query parameters:
    - `page` (optional, integer, default 1, min 1): Page number (1-based)
    - `page_size` (optional, integer, default 20, min 1, max 50): Items per page
- **Response**: 200 OK
  ```json
  {
    "items": [
      {
        "payee_id": "uuid",
        "payee_name": "Jamie Clarke",
        "payee_sort_code": "04-00-04",
        "masked_account_identifier": "****3321"
      }
    ],
    "total": 3,
    "page": 1,
    "page_size": 20,
    "capability": {
      "capability_name": "saved_payees",
      "status_value": "healthy",
      "customer_message_code": null,
      "customer_message": "Saved payees available",
      "recovery_guidance": null,
      "effective_from": "2026-11-22T10:30:00Z"
    }
  }
  ```
- **Behavior**:
  - Returns only payees with `payee_status` = `saved_active`
  - Full account numbers are NEVER returned (only `masked_account_identifier`)
  - When `saved_payees` capability is unavailable, returns empty page with capability message
  - When entitlement is denied, returns empty page
  - Results ordered by `payee_name`
  - Pagination supported
- **Error responses**:
  - 401 `session_invalid`: Missing or invalid bearer token
  - 403 `entitlement_denied`: Customer not entitled to payees (returns empty page instead)
  - 422 `validation_error`: Invalid pagination parameters
  - 500 `internal_error`: Server error

## Seed Data

Three payees are seeded per customer:

**Customer 1: Alex Taylor (CUST-SYNTH-001)**
- **Payee 1**: Jamie Clarke
  - Sort code: 04-00-04
  - Masked account: ****3321
  - Status: saved_active
  - CoP outcome: match
  
- **Payee 2**: Priya Patel
  - Sort code: 60-83-71
  - Masked account: ****7745
  - Status: saved_active
  - CoP outcome: match
  
- **Payee 3**: K Evans Lettings
  - Sort code: 20-45-77
  - Masked account: ****9842
  - Status: saved_active
  - CoP outcome: close_match

**Customer 2: Jordan Smith (CUST-SYNTH-002)** - same 3 payees

## Database Schema

### Payees Table
Full schema implementation with all 12 columns:
- `id` (UUID, primary key)
- `customer_profile_ref_id` (UUID, FK to customer_profile_refs)
- `payee_name` (VARCHAR(120))
- `payee_account_identifier` (VARCHAR(34)) - full account, never shown to customer
- `payee_sort_code` (VARCHAR(8))
- `masked_account_identifier` (VARCHAR(32))
- `payee_status` (VARCHAR(12), CHECK IN ('saved_active', 'blocked'), DEFAULT 'saved_active')
- `activated_at` (TIMESTAMPTZ)
- `cop_outcome_category` (VARCHAR(24), CHECK IN ('match', 'close_match', 'no_match', 'unable_to_confirm', 'provider_unavailable', 'blocked'))
- `cop_provider_reference` (VARCHAR(128))
- `cop_checked_at` (TIMESTAMPTZ)
- `correlation_id` (VARCHAR(64))
- `created_at` (TIMESTAMPTZ)
- `updated_at` (TIMESTAMPTZ)

### Account Read Model Constraint
Database constraint `ck_arm_amount_state` enforces FR-ACCT-003:
- When `balance_availability_state` IN ('unavailable', 'unknown')
- Then `balance_amount_minor` and `balance_currency` MUST be NULL
- Never allows numeric zero as substitute for unavailable balance

## CoP Adapter Seam

Scaffolded `app/adapters/cop_adapter.py` with method signatures only:
- `CoPAdapter.check_payee_details()` - raises NotImplementedError
- Retained CoP outcome on payee records consumed by fraud decisioning
- Not called in this tier (FR-PAY-005, FR-PAY-006 deferred)

## Capability Integration

The `saved_payees` capability status is checked for every request:
- **healthy**: Returns payees normally
- **unavailable**: Returns empty page with message "Saved payees are currently unavailable. Please try again later."
- **partial**: Returns available payees with message "Some saved payees may not be available"

## Frontend Integration Notes

To use this endpoint:
1. Customer must be authenticated (use bearer token from login)
2. Call `GET /api/v1/payees` to get the list
3. Display each payee with `payee_name`, `payee_sort_code`, and `masked_account_identifier`
4. When customer selects a payee, use `payee_id` to initiate payment entry
5. Never display `payee_account_identifier` - it's not in the response
6. Handle capability messages when `status_value` is not "healthy"

## Test Coverage

All tests passing:
- **Unit tests** (`test_payees_service.py`): 7 tests covering service logic
- **Integration tests** (`test_payees_integration.py`): 7 tests covering API endpoint
- **Acceptance tests** (`test_payees_acceptance.py`): 5 tests covering FR-PAY-001 and FR-ACCT-003 criteria

## Files Modified/Created

**Models**:
- `/repos/lbg-ftr-demo-repo/backend/app/models/payee.py` - Full model implementation

**Schemas**:
- `/repos/lbg-ftr-demo-repo/backend/app/schemas/payees_schemas.py` - PayeeItem, PayeeListResponse, CapabilityStatus

**Repository**:
- `/repos/lbg-ftr-demo-repo/backend/app/repositories/payee_repository.py` - PayeeRepository

**Service**:
- `/repos/lbg-ftr-demo-repo/backend/app/services/payee_service.py` - PayeeService

**Adapter**:
- `/repos/lbg-ftr-demo-repo/backend/app/adapters/cop_adapter.py` - CoP adapter scaffold

**Router**:
- `/repos/lbg-ftr-demo-repo/backend/app/routers/payees.py` - E-05 endpoint

**Main**:
- `/repos/lbg-ftr-demo-repo/backend/app/main.py` - Registered payees router

**Seed**:
- `/repos/lbg-ftr-demo-repo/backend/app/seed.py` - Added 3 payees per customer

**Tests**:
- `/repos/lbg-ftr-demo-repo/backend/tests/test_payees_service.py`
- `/repos/lbg-ftr-demo-repo/backend/tests/test_payees_integration.py`
- `/repos/lbg-ftr-demo-repo/backend/tests/test_payees_acceptance.py`
