# TASK-4: Backend Feature B2 - Profiles, Accounts and Payees

## Overview
Implementation of profiles, accounts, and payees domains with entitlement-based access control, partial-failure handling for account aggregation, and Confirmation of Payee (CoP) checks for new payees.

## API Endpoints

### GET /api/v1/profiles
Returns list of profiles with entitlements for the authenticated user.

**Response:**
```json
{
  "active_profile_id": 1,
  "profiles": [
    {
      "profile_id": 1,
      "profile_type": "personal",
      "display_name": "John Smith",
      "business_name": null,
      "can_view_accounts": true,
      "can_create_payee": true,
      "can_approve_payment": true
    }
  ]
}
```

### POST /api/v1/profiles/activate
Activates a profile for the current session.

**Request:**
```json
{
  "profile_id": 1
}
```

**Response:**
```json
{
  "profile_id": 1,
  "profile_type": "personal",
  "display_name": "John Smith"
}
```

### GET /api/v1/accounts/overview?profile_id=<uuid>
Returns account overview for a profile with partial-failure handling.

**Response:**
```json
{
  "profile": {
    "profile_id": 1,
    "profile_type": "personal",
    "display_name": "John Smith",
    "business_name": null
  },
  "accounts": [
    {
      "account_id": 1,
      "account_type": "current_account",
      "account_name": "Personal Current Account",
      "masked_account_number": "****5678",
      "sort_code": "20-00-00",
      "currency": "GBP",
      "current_balance_minor": 124836,
      "available_balance_minor": 124836,
      "overdraft_available_minor": 100000,
      "available_credit_minor": null,
      "next_repayment_amount_minor": null,
      "next_repayment_due_date": null,
      "freshness_state": "current",
      "last_updated_at": "2026-11-19T10:00:00Z"
    },
    {
      "account_id": 2,
      "account_type": "credit_card",
      "account_name": "Personal Credit Card",
      "masked_account_number": "****9012",
      "sort_code": null,
      "currency": "GBP",
      "current_balance_minor": -18240,
      "available_balance_minor": null,
      "overdraft_available_minor": null,
      "available_credit_minor": 231760,
      "next_repayment_amount_minor": null,
      "next_repayment_due_date": null,
      "freshness_state": "current",
      "last_updated_at": "2026-11-19T10:00:00Z"
    },
    {
      "account_id": 3,
      "account_type": "loan",
      "account_name": "Personal Loan",
      "masked_account_number": "****3456",
      "sort_code": null,
      "currency": "GBP",
      "current_balance_minor": -486000,
      "available_balance_minor": null,
      "overdraft_available_minor": null,
      "available_credit_minor": null,
      "next_repayment_amount_minor": 21250,
      "next_repayment_due_date": "2026-11-28",
      "freshness_state": "current",
      "last_updated_at": "2026-11-19T10:00:00Z"
    }
  ],
  "data_gaps": [
    {
      "source_system": "account_system",
      "message": "Account data temporarily unavailable",
      "freshness_state": "unavailable"
    }
  ]
}
```

### GET /api/v1/payees?profile_id=<uuid>
Returns payee list for a profile.

**Response:**
```json
{
  "payees": [
    {
      "payee_id": 1,
      "display_name": "Jamie Clarke",
      "sort_code": "04-00-04",
      "masked_account_number": "****3746",
      "nickname": null,
      "can_proceed": true,
      "latest_cop_result": "match",
      "latest_cop_checked_at": "2026-10-20T10:00:00Z"
    },
    {
      "payee_id": 2,
      "display_name": "Priya Patel",
      "sort_code": "08-92-99",
      "masked_account_number": "****2178",
      "nickname": null,
      "can_proceed": true,
      "latest_cop_result": "match",
      "latest_cop_checked_at": "2026-09-20T10:00:00Z"
    }
  ]
}
```

### POST /api/v1/payees
Creates a new payee with fresh payee-action SCA and CoP check.

**Request:**
```json
{
  "profile_id": 1,
  "display_name": "K Evans Lettings",
  "nickname": null,
  "sort_code": "20-45-77",
  "account_number": "30019842",
  "payee_action_challenge_id": 123,
  "payee_action_assertion": "123456"
}
```

**Response:**
```json
{
  "payee_id": 3,
  "display_name": "K Evans Lettings",
  "sort_code": "20-45-77",
  "masked_account_number": "****9842",
  "cop_result": "match",
  "warning_message": null,
  "can_proceed": true,
  "override_required": false
}
```

### POST /api/v1/payees/{payee_id}/confirm-warning
Confirms CoP warning and allows proceeding with payee.

**Request:**
```json
{
  "override_reason": "Customer confirmed correct details"
}
```

**Response:**
```json
{
  "payee_id": 3,
  "display_name": "",
  "sort_code": "",
  "masked_account_number": "",
  "cop_result": "close_match",
  "warning_message": null,
  "can_proceed": true,
  "override_required": false
}
```

## Seed Data

### Personal Profile
- **User:** john.smith@example.com / Personal123!
- **Profile Type:** Personal
- **Accounts:**
  - Current Account: £1,248.36 available
  - Credit Card: £182.40 balance, £2,317.60 available credit
  - Loan: £4,860 balance, next repayment £212.50 due 28 Nov 2026

### Business Profile
- **User:** jane.doe@businessexample.com / Business123!
- **Profile Type:** Business
- **Business Name:** Acme Corporation Ltd
- **Accounts:**
  - Business Current Account: £6,420.18 available

### Saved Payees (Personal Profile)
1. **Jamie Clarke**
   - Sort Code: 04-00-04
   - Account: ****3746
   - CoP: Match

2. **Priya Patel**
   - Sort Code: 08-92-99
   - Account: ****2178
   - CoP: Match

3. **K Evans Lettings** (created in journey)
   - Sort Code: 20-45-77
   - Account: ****9842
   - CoP: Match

## Implementation Notes

### Entitlement Service
- Aggregates entitlements from multiple sources (local DB + external adapter)
- Any True entitlement grants permission
- Stub adapter always returns entitled for demo purposes

### Account Overview Service
- Calls account system and loan context adapters independently
- Records data gaps when external systems unavailable
- Returns available data even with partial failures
- Preserves freshness_state on each account
- Loan context enrichment for loan accounts

### Payee Service
- Requires fresh payee-action SCA verification before creating payee
- Performs CoP check via stub adapter (70% match, 15% close_match, 10% no_match, 5% unavailable)
- Hashes full account number for storage
- Stores only last 4 digits of account number
- Sets can_proceed=true only for match result
- Requires explicit override confirmation for close_match/no_match/unavailable

### CoP Adapter (Stub)
- Deterministic hash-based logic for demo
- Returns realistic distribution of results
- Includes appropriate warning messages for non-match cases

## Tests Coverage

### Unit Tests
- `test_entitlement_service.py`: Entitlement resolution and access checks
- `test_account_overview_service.py`: Account aggregation with partial failure handling
- `test_payee_service.py`: Payee creation with SCA and CoP checks

### Integration Tests
- `test_accounts_integration.py`: Account overview endpoint
- `test_payees_integration.py`: Payee list, creation, and warning confirmation endpoints

## Behavioral Notes

1. **Entitlement Check**: All profile and account operations verify profile ownership and entitlements
2. **Partial Failure Handling**: Account overview continues even when external adapters fail, recording data gaps
3. **Fresh SCA**: Payee creation requires verified payee-action SCA challenge
4. **CoP Flow**: Match allows immediate proceed; close_match/no_match/unavailable require explicit override
5. **Data Freshness**: Each account includes freshness_state indicator
6. **Loan Context**: Loan accounts enriched with next repayment amount and due date
