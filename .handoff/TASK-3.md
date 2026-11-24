# TASK-3 Backend Feature B1 Handoff

## Endpoints Added

All routes mounted under `/api/v1`:

### Authentication
- `POST /api/v1/auth/login` - Login with username/password, returns TokenResponse with Bearer token, user info, active_role_code, available_roles
- `POST /api/v1/auth/logout` - Logout and revoke session, requires Bearer token
- `GET /api/v1/auth/session` - Get current session info, requires Bearer token

### Workspace
- `GET /api/v1/workspace/landing` - Get role-based landing payload with widgets, allowed_actions, available_roles; requires Bearer token
- `PUT /api/v1/workspace/active-role` - Switch active role, body: `{"role_code": "..."}`, requires Bearer token

### Queue Items
- `GET /api/v1/queue-items` - List queue items with filters (queue_state, non_standard, non_standard_reason, customer_id, assigned_to_me, limit, offset); requires Bearer token
- `POST /api/v1/queue-items/refresh` - Trigger queue refresh, body: `{"scope": "full"|"customer", "customer_id": "..."}`, returns 202 with run_id; requires Bearer token
- `GET /api/v1/queue-items/refresh-runs/{run_id}` - Get refresh run status; requires Bearer token

### Health
- `GET /health` - Liveness check, returns `{"status": "ok", "service": "...", "version": "...", "time": "..."}`, public
- `GET /api/health` - Alias of /health, public
- `GET /health/ready` - Readiness check with database, migrations, sap_adapter checks, returns 200 when ready or 503 when not, public

## Request/Response Shapes

### TokenResponse
```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 86400,
  "inactivity_timeout_seconds": 1800,
  "session_id": "uuid",
  "user": {
    "user_id": "uuid",
    "username": "analyst1",
    "display_name": "Analyst One",
    "email": "analyst1@example.com"
  },
  "active_role_code": "collections_analyst",
  "available_roles": [
    {
      "role_code": "collections_analyst",
      "role_label": "Collections Analyst",
      "allowed_actions": ["view_queue", "view_customer"]
    }
  ]
}
```

### LandingResponse
```json
{
  "active_role_code": "collections_analyst",
  "active_role_label": "Collections Analyst",
  "available_roles": [
    {"role_code": "...", "role_label": "..."}
  ],
  "allowed_actions": ["view_queue", "view_customer"],
  "widgets": [
    {
      "widget_code": "queue_summary",
      "widget_label": "Queue Summary",
      "widget_data": {
        "groups": [
          {"queue_state": "active", "count": 10, "total_amount": 15000.00}
        ]
      }
    }
  ],
  "data_freshness": "2026-11-24T...",
  "generated_at": "2026-11-24T..."
}
```

### QueueListResponse
```json
{
  "items": [
    {
      "queue_item_id": "uuid",
      "receivable_item_id": "uuid",
      "customer_account_id": "uuid",
      "customer_name": "ABC Corp",
      "queue_state": "active",
      "is_non_standard": false,
      "non_standard_reason": null,
      "priority_rank": 1,
      "priority_score": "1500.00",
      "open_amount": "15000.00",
      "currency_code": "GBP",
      "days_past_due": 60,
      "aging_bucket": "61-90",
      "promise_indicator": false,
      "dispute_indicator": false,
      "entered_queue_at": "2026-11-24T...",
      "last_refreshed_at": "2026-11-24T..."
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0,
  "groups": [
    {"queue_state": "active", "count": 1, "total_amount": "15000.00"}
  ],
  "data_freshness": "2026-11-24T..."
}
```

### RefreshRunResponse
```json
{
  "run_id": "uuid",
  "run_status": "running"|"completed"|"failed",
  "trigger_type": "manual"|"scheduled",
  "started_at": "2026-11-24T...",
  "status_url": "/api/v1/queue-items/refresh-runs/{run_id}",
  "completed_at": "2026-11-24T...",
  "records_read": 10,
  "records_upserted": 10,
  "items_ranked": 10,
  "items_flagged_non_standard": 2,
  "error_summary": null
}
```

## Seed Credentials

From TASK-1 seed:
- Username: `analyst1`, Password: `analyst123`, Role: `collections_analyst`
- Username: `reviewer1`, Password: `reviewer123`, Role: `collections_reviewer`

## Authentication Flow

1. POST `/api/v1/auth/login` with `{"username": "analyst1", "password": "analyst123"}`
2. Receive `access_token` in response
3. Include `Authorization: Bearer {access_token}` header in all subsequent requests
4. Token expires after `expires_in` seconds (default 1440 minutes = 24 hours)
5. Session has inactivity timeout (default 1800 seconds = 30 minutes)
6. POST `/api/v1/auth/logout` to revoke session

## Role-Based Access

- Each user can have multiple role assignments
- Login returns `active_role_code` (first available role) and `available_roles` list
- Use `PUT /api/v1/workspace/active-role` to switch between assigned roles
- Each role has:
  - `allowed_widgets`: Widget codes the role can see on landing
  - `entitled_queue_states`: Queue states the role can access
  - `allowed_actions`: Actions the role can perform
  - `can_view_sensitive_fields`: Whether role can see masked fields

## SAP Integration

- MVP uses stub SAP adapter (`app/adapters/sap/stub.py`)
- Returns sample open receivables data
- Real SAP integration would implement `SapReceivablesReader` and `SapCustomerContextReader` protocols
- Synchronizer upserts customers, customer_accounts, invoices, receivable_items from SAP data

## Queue Refresh Process

1. POST `/api/v1/queue-items/refresh` starts a sync run
2. Sync run calls SAP adapter to read open items
3. Synchronizer upserts reference tables (customers, accounts, invoices, receivables)
4. Queue service ranks items deterministically (by days_past_due desc, then sap_open_item_ref asc)
5. Policy engine evaluates queue eligibility (flags disputed, unapplied_cash, pending_evidence as non-standard)
6. Queue items and prioritization assessments created/updated
7. Returns 202 with `run_id` and `status_url`
8. Poll `GET /api/v1/queue-items/refresh-runs/{run_id}` for completion

## Policy Engine

- Loads active rule set from `policy_rule_set_versions` table
- Evaluates rules in order (by `evaluation_order`, then `rule_code`)
- Supported condition types:
  - `field_present`, `decimal_greater_than`, `field_in_set`, `field_equals_context`
  - `collection_min_size`, `sum_matches`, `all_belong_to`, `one_of_present`, `flag_is_false`
- Creates `policy_evaluation_records` with result, failed_conditions, rules_applied
- Used for queue eligibility and promise validation (TASK-4)

## Audit Trail

- All sensitive actions logged to `audit_events` table
- Payload sanitization removes forbidden fields (password, token, credit_status_indicator)
- Events include correlation_id, actor, affected entity, timestamp
- Append-only (no updates/deletes)

## Scheduled Jobs

- `app/jobs/scheduler.py` provides `scheduled_queue_refresh()` function
- Would be invoked by external scheduler (cron, APScheduler, etc.)
- Calls `QueueService.execute_refresh(scope="full", trigger_type="scheduled")`
