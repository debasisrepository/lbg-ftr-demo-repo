# Task 4 Handoff: Accounts Overview and Freshness

## Endpoints Implemented

### GET /api/v1/accounts
**E-04: Accounts overview with honest freshness**

Returns paginated account list with balance availability state and freshness indicators.

**Response Structure:**
```json
{
  "items": [
    {
      "account_id": "uuid",
      "account_type": "current | savings | card | loan",
      "display_name": "string",
      "masked_account_identifier": "****1234",
      "balance": {
        "availability_state": "current | stale | unavailable | unknown",
        "amount_minor": 124836,
        "currency": "GBP",
        "display_text": "£1,248.36"
      },
      "as_of_timestamp": "2026-11-22T10:30:00Z",
      "freshness_status": "within_target | breached | unknown",
      "freshness_text": "Updated 2 minutes ago",
      "item_state": "available | partial",
      "payment_source_eligible": true
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20,
  "overview_state": "complete | partial | unavailable",
  "capability": {
    "capability_name": "accounts_overview",
    "status_value": "healthy | stale | partial | unavailable | restricted",
    "customer_message_code": "string or null",
    "customer_message": "Account overview is available",
    "recovery_guidance": "string or null",
    "effective_from": "2026-11-22T10:00:00Z"
  }
}
```

**Query Parameters:**
- `page` (integer, optional, default 1, minimum 1): 1-based page number
- `page_size` (integer, optional, default 20, 1-50): Items per page

**Authentication:** Required (Bearer token)

**Status Codes:**
- 200: Success
- 401: Invalid or expired session
- 403: Not entitled to view accounts
- 422: Invalid pagination parameters

---

### GET /api/v1/capability-statuses
**E-06: Capability status for all capabilities**

Returns current status for all 4 capabilities: accounts_overview, saved_payees, payments, payment_status.

**Response Structure:**
```json
{
  "items": [
    {
      "capability_name": "accounts_overview",
      "status_value": "healthy",
      "customer_message_code": null,
      "customer_message": "Account overview is available",
      "recovery_guidance": "",
      "effective_from": "2026-11-22T10:00:00Z"
    }
  ],
  "total": 4,
  "page": 1,
  "page_size": 4
}
```

**Authentication:** Required (Bearer token)

**Status Codes:**
- 200: Success
- 401: Invalid or expired session

---

## Seed Data

Each customer has 3 accounts:

### Customer 1: Alex Taylor (CUST-SYNTH-001)

1. **Main Current Account**
   - Type: current
   - Masked ID: ****1234
   - Balance: £1,248.36
   - State: current (within freshness target)
   - Payment source eligible: Yes

2. **Instant Saver**
   - Type: savings
   - Masked ID: ****5678
   - Balance: £3,500.00
   - State: current (within freshness target)
   - Payment source eligible: Yes

3. **Joint Account**
   - Type: current
   - Masked ID: ****9012
   - Balance: £1,248.36
   - State: stale (breached freshness, ~2.5 hours old)
   - Payment source eligible: No (stale)

### Customer 2: Jordan Smith (CUST-SYNTH-002)
Same 3 accounts with different system references.

---

## Key Behaviors

### Balance Availability States

1. **current**: Balance is fresh and trustworthy
   - `amount_minor` and `currency` are present
   - `as_of_timestamp` is within freshness target (60 seconds)
   - Eligible as payment source

2. **stale**: Balance is outdated
   - `amount_minor` and `currency` are present
   - `as_of_timestamp` is older than freshness target
   - Display text includes "(may be out of date)"
   - NOT eligible as payment source

3. **unavailable**: Balance cannot be shown
   - `amount_minor` is NULL
   - `currency` is NULL
   - Display text: "Balance unavailable"
   - NOT eligible as payment source

4. **unknown**: Freshness cannot be established
   - `amount_minor` is NULL
   - `currency` is NULL
   - Display text: "Balance cannot be shown"
   - NOT eligible as payment source

### Freshness Indicators

- **freshness_status**: within_target | breached | unknown
- **freshness_text**: Plain-language time-based text
  - "Updated moments ago" (< 1 minute)
  - "Updated 5 minutes ago" (< 1 hour)
  - "Updated 2 hours ago" (< 1 day)
  - "Updated 3 days ago" (≥ 1 day)
  - "Data may be out of date" (breached)
  - "Freshness cannot be established" (unknown)

### Overview State

- **complete**: All accounts available with fresh data
- **partial**: At least one account unavailable or some data missing
- **unavailable**: No accounts can be shown

### Payment Source Eligibility

An account is eligible as a payment source when:
- `balance_availability_state` is "current"
- `balance_amount_minor` is NOT NULL

Stale, unavailable, or unknown accounts are NOT eligible.

---

## Honest Balance Handling

**Rule: Never show missing balance as zero.**

- Missing balance → `amount_minor: null`, `currency: null`
- Unavailable state → Display text: "Balance unavailable"
- Unknown state → Display text: "Balance cannot be shown"
- Zero is ONLY shown when the actual balance is £0.00 and state is current

---

## Entitlement Checks

- Entitlement checked via `EntitlementSandboxAdapter`
- Customer must have `resource_type: "account"` with `decision: "allow"`
- 403 response if not entitled to view any accounts

---

## Capability Status

All 4 capabilities are seeded as "healthy" by default:
- accounts_overview
- saved_payees
- payments
- payment_status

Each has plain-language customer messages and recovery guidance based on status_value.

---

## Test Coverage

- **Unit tests**: 8 tests covering service logic, freshness computation, currency formatting
- **Integration tests**: 7 tests covering API endpoints, pagination, unavailable balances
- **Acceptance tests**: 6 tests covering all FR-ACCT-001, FR-ACCT-002, FR-ACCT-003 acceptance criteria

All tests passing.

---

## Notes for Frontend (TASK-5+)

1. Use GET /api/v1/accounts to display account overview
2. Check `payment_source_eligible` flag before allowing account selection for payments
3. Display `freshness_text` to show data currency
4. Handle `item_state: "partial"` with appropriate UI indication
5. Check `overview_state` and `capability.status_value` for degraded mode handling
6. Never display missing balance as £0.00 - use `display_text` from balance object
7. Use `as_of_timestamp` to show when balance was last updated
8. Respect `payment_source_eligible` flag - only current, fresh balances can be used for payments
