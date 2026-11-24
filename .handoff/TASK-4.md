# TASK-4 Backend Feature B2 Handoff

## Endpoints Added

All routes mounted under `/api/v1`:

### Customers
- `GET /api/v1/customers` - Search/list customers with query filters (q, portfolio_ref, limit, offset); requires Bearer token and `view_customer` action
- `GET /api/v1/customers/{customer_id}/view` - Get Customer 360 view with sections (profile, accounts, invoices, receivable_items, unapplied_cash, promises, source_interactions); optional filters (account_id, invoice_limit); requires Bearer token and `view_customer` action

### Promises
- `POST /api/v1/promises` - Create promise-to-pay with policy validation and idempotency; requires Bearer token, `capture_promise` action, and `Idempotency-Key` header; returns 201 for new promise or 200 for idempotent replay
- `GET /api/v1/promises` - List promises with filters (customer_id, customer_account_id, promise_status, captured_by_me, promised_from, promised_to, limit, offset); requires Bearer token and `view_promise` action
- `GET /api/v1/promises/{promise_id}` - Get promise by ID; requires Bearer token and `view_promise` action

### Policy
- `GET /api/v1/policy/evaluations` - List policy evaluation history with filters (evaluation_result, evaluation_context_type, action_type, subject_entity_type, subject_entity_id, actor_user_id, rule_set_version_number, from, to, limit, offset); requires Bearer token and `view_policy_history` action
- `GET /api/v1/policy/rule-sets` - List policy rule sets with filters (rule_set_status, region_code, include_rules, limit, offset); requires Bearer token and `view_policy_config` action

### Audit Events
- `GET /api/v1/audit-events` - List audit events with filters (event_type, affected_entity_type, affected_entity_id, actor_user_id, customer_account_id, correlation_id, from, to, limit, offset); requires Bearer token and `view_audit_trail` action

## Request/Response Shapes

### CustomerListResponse
```json
{
  "items": [
    {
      "customer_id": "uuid",
      "customer_name": "ABC Corp",
      "sap_customer_ref": "CUST001",
      "regional_business_unit": "UK",
      "credit_status_indicator": "normal",
      "account_count": 2
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### Customer360Response
```json
{
  "customer_id": "uuid",
  "generated_at": "2026-11-24T...",
  "data_freshness": "2026-11-24T...",
  "profile": {
    "status": "available|unavailable|masked",
    "reason": null,
    "as_of": "2026-11-24T...",
    "data": {
      "customer_id": "uuid",
      "customer_name": "ABC Corp",
      "sap_customer_ref": "CUST001",
      "regional_business_unit": "UK",
      "credit_status_indicator": "normal",  // null if masked
      "master_data_source": "SAP"
    }
  },
  "accounts": {
    "status": "available",
    "as_of": "2026-11-24T...",
    "data": [
      {
        "customer_account_id": "uuid",
        "sap_account_ref": "ACCT001",
        "company_code": "1000",
        "currency_code": "GBP",
        "account_status": "active",
        "risk_segment": "medium",
        "portfolio_ref": "PORT_001",
        "collector_owner_user_id": "uuid",
        "open_balance": "15000.00"
      }
    ]
  },
  "invoices": {"status": "available", "data": [...]},
  "receivable_items": {"status": "available", "data": [...]},
  "unapplied_cash": {"status": "unavailable", "reason": "No unapplied cash found"},
  "promises": {"status": "available", "data": [...]},
  "source_interactions": {"status": "available", "data": [...]}
}
```

### PromiseCreateRequest
```json
{
  "customer_account_id": "uuid",
  "promised_amount": "5000.00",
  "currency_code": "GBP",
  "promised_date": "2026-12-01T00:00:00Z",
  "promise_scope_type": "invoice|account_balance|partial",
  "scope_links": [
    {
      "link_type": "invoice",
      "invoice_id": "uuid",
      "linked_amount": "5000.00"
    }
  ],
  "source_interaction_id": "uuid",  // OR source_interaction
  "source_interaction": {
    "interaction_type": "call",
    "interaction_direction": "outbound",
    "interaction_channel": "phone",
    "occurred_at": "2026-11-24T...",
    "summary_text": "Customer promised payment"
  },
  "note": "Optional note"
}
```

### PromiseResponse
```json
{
  "promise_id": "uuid",
  "customer_account_id": "uuid",
  "promised_amount": "5000.00",
  "currency_code": "GBP",
  "promised_date": "2026-12-01T00:00:00Z",
  "promise_scope_type": "invoice",
  "promise_status": "active",
  "captured_by_user_id": "uuid",
  "captured_at": "2026-11-24T...",
  "policy_evaluation_id": "uuid",
  "scope_links": [
    {
      "link_id": "uuid",
      "link_type": "invoice",
      "invoice_id": "uuid",
      "receivable_item_id": null,
      "linked_amount": "5000.00"
    }
  ]
}
```

### PromiseListResponse
```json
{
  "items": [
    {
      "promise_id": "uuid",
      "customer_account_id": "uuid",
      "customer_name": "ABC Corp",
      "promised_amount": "5000.00",
      "currency_code": "GBP",
      "promised_date": "2026-12-01T00:00:00Z",
      "promise_scope_type": "invoice",
      "promise_status": "active",
      "captured_by_user_id": "uuid",
      "captured_at": "2026-11-24T...",
      "breach_detected_at": null
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### PolicyEvaluationListResponse
```json
{
  "items": [
    {
      "evaluation_id": "uuid",
      "rule_set_version_id": "uuid",
      "evaluation_context_type": "promise_capture",
      "action_type": "promise_create",
      "subject_entity_type": "promise_to_pay",
      "subject_entity_id": "uuid",
      "actor_user_id": "uuid",
      "actor_role_code": "collections_analyst",
      "evaluation_result": "allow|deny",
      "failed_condition_code": "PROMISE_SOURCE_REQUIRED",
      "evaluated_at": "2026-11-24T...",
      "evaluated_by_component": "policy_engine_service"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### RuleSetListResponse
```json
{
  "items": [
    {
      "rule_set_version_id": "uuid",
      "version_number": 1,
      "version_label": "v1.0",
      "region_code": null,
      "rule_set_status": "active",
      "effective_from": "2026-11-24T...",
      "effective_to": null,
      "rules": [
        {
          "rule_id": "uuid",
          "rule_code": "PROMISE_AMOUNT_REQUIRED",
          "rule_category": "validation",
          "action_type": "promise_create",
          "rule_description": "Promise amount must be present",
          "failure_message": "Promise amount is required",
          "evaluation_order": 1,
          "is_enabled": true
        }
      ]
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

### AuditEventListResponse
```json
{
  "items": [
    {
      "event_id": "uuid",
      "event_type": "promise_captured",
      "severity": "info",
      "actor_user_id": "uuid",
      "actor_role_code": "collections_analyst",
      "customer_account_id": "uuid",
      "affected_entity_type": "promise_to_pay",
      "affected_entity_id": "uuid",
      "correlation_id": "correlation-123",
      "event_timestamp": "2026-11-24T...",
      "rationale_text": "Promise recorded for invoice payment"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

## Customer 360 Section States

Each section in Customer360Response has a `status` field:

- **available**: Data is present and visible
- **unavailable**: Data not found (e.g., no invoices)
- **masked**: Data exists but sensitive fields are hidden

Sensitive fields (like `credit_status_indicator`) are `null` when user lacks `can_view_sensitive_fields` permission.

## Promise Creation Flow

1. User POSTs `/api/v1/promises` with `Idempotency-Key` header
2. Service checks idempotency key for replay
3. Validates customer account exists
4. Creates or references source interaction
5. Policy engine evaluates `promise_create` action
6. If policy allows, creates promise + scope links
7. Creates idempotency record (expires in 24 hours)
8. Returns 201 for new promise, 200 for replay

## Policy Validation

- Policy engine loads active rule set
- Evaluates rules in order (by `evaluation_order`, then `rule_code`)
- If any rule fails, raises `PolicyFailureError` with `failed_conditions` detail
- Creates `policy_evaluation_records` with result

## Idempotency

- Uses SHA-256 fingerprint of request body
- Same key with different body raises `409 Conflict`
- Same key with same body returns existing promise (200)
- Idempotency records expire after 24 hours

## SAP Integration

- `SapCustomerContextReader` protocol implemented in stub
- Stub returns sample customer context
- Production would call real SAP APIs
- Errors gracefully degrade (unavailable sections)

## Seed Data

Role actions updated for new endpoints:
- `collections_analyst`: `view_customer`, `capture_promise`, `view_promise`, `view_policy_history`, `view_audit_trail`
- `collections_reviewer`: All analyst actions + `view_policy_config`, `view_sensitive`

## Acceptance Criteria Covered

**FR-C360-001:**
1. ✅ Customer data available from authorized sources → unified view
2. ✅ Unavailable sections clearly marked without blocking available data
3. ✅ Sensitive fields masked when user lacks permission

**FR-PTP-001:**
1. ✅ Amount, date, scope, source interaction are mandatory (enforced by policy)
2. ✅ Invoice/account balance links stored in `promise_scope_links`
3. ✅ Omitted required fields → system rejects via policy failure
