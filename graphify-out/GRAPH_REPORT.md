# Graph Report - lbg-ftr-demo-repo  (2026-11-24)

## Corpus Check
- 179 files · ~102,954 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 20 file(s) not represented in the graph (top: (none) 7, .example 2, .db 2)

## Summary
- 1455 nodes · 3467 edges · 116 communities (56 shown, 60 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 253 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `341e2e54`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Intelligent Receivables and Collections Application
- UUID
- test_pipeline_migration_parity.py
- PromiseRepository
- RoleRepository
- WorkQueuePage.tsx
- logging.py
- TASK-3 Backend Feature B1 Handoff
- test_evaluators.py
- 825dddf12e48_create_all_tables.py
- health.py
- ConditionEvaluator
- lbg-ftr-receivables-backend
- auth-context.tsx
- sqlalchemy_orm
- AuthService
- compilerOptions
- Frontend - Receivables & Collections Application
- compilerOptions
- LandingPage.tsx
- devDependencies
- App.tsx
- configured.py
- InteractionRepository
- common.ts
- customer.ts
- PromiseForm.tsx
- tsconfig.json
- customer360_service.py
- steps
- typing
- PolicyEvaluationRecord
- queue_items.py
- UUID
- RequestContext
- audit.py
- Customer360Service
- datetime
- SapReceivablesReader
- config.py
- Customer
- promise_service.py
- cli.py
- auth.py
- backend
- .login
- eslint.config.js
- package.json
- db_session
- routers/policy.py
- IdempotencyRecord
- switch_active_role
- TASK-4 Backend Feature B2 Handoff
- security.py
- test_policy_acceptance.py
- list_promises
- Endpoints Added
- Request/Response Shapes
- CustomerRepository
- test_policy_engine_service.py
- queue_service.py
- active_rule_set
- TASK-5 Handoff: Backend Feature B3 - Deterministic Policy Enforcement
- PolicyFailureError
- .create_promise
- FixedClock
- @playwright/test
- main.py
- useLanding.ts
- scripts
- PolicyEngineService
- BearerCaptureMiddleware
- evaluator
- CorrelationIdMiddleware
- RequestLogMiddleware
- vite
- @testing-library/jest-dom
- test_field_present_passes_when_field_exists
- test_sum_matches_fails
- test_all_belong_to_passes
- test_one_of_present_passes
- test_flag_is_false_passes_when_false
- test_nested_field_in_dict
- test_nested_field_missing_returns_none
- test_decimal_greater_than_fails
- test_field_in_set_passes
- test_promise_acceptance.py
- get_customer_view
- start.sh
- stop.sh
- .login

## God Nodes (most connected - your core abstractions)
1. `RoleProfile` - 49 edges
2. `RequestContext` - 45 edges
3. `Customer` - 44 edges
4. `CustomerAccount` - 44 edges
5. `User` - 43 edges
6. `Clock` - 43 edges
7. `hash_password()` - 42 edges
8. `RoleAssignment` - 41 edges
9. `Base` - 38 edges
10. `PolicyRuleSetVersion` - 32 edges

## Surprising Connections (you probably didn't know these)
- `Policy Validation` --references--> `PolicyFailureError`  [INFERRED]
  .handoff/TASK-4.md → backend/app/core/errors.py
- `SAP Integration` --references--> `SapCustomerContextReader`  [INFERRED]
  .handoff/TASK-4.md → backend/app/adapters/sap/__init__.py
- `Scheduled Jobs` --references--> `scheduled_queue_refresh()`  [INFERRED]
  .handoff/TASK-3.md → backend/app/jobs/scheduler.py
- `SAP Integration` --references--> `SapCustomerContextReader`  [INFERRED]
  .handoff/TASK-3.md → backend/app/adapters/sap/__init__.py
- `SAP Integration` --references--> `SapReceivablesReader`  [INFERRED]
  .handoff/TASK-3.md → backend/app/adapters/sap/__init__.py

## Import Cycles
- None detected.

## Communities (116 total, 60 thin omitted)

### Community 0 - "Intelligent Receivables and Collections Application"
Cohesion: 0.07
Nodes (29): API Documentation, Backend, Backend Environment Variables, CI/CD, Configuration, Customer 360 View (FR-C360-001), Database Migration Issues, Deployment (+21 more)

### Community 2 - "UUID"
Cohesion: 0.09
Nodes (20): hash_password(), AuditEvent, RoleAssignment, RoleProfile, test_get_audit_events(), test_get_audit_events_filtered_by_actor(), test_get_audit_events_filtered_by_type(), test_login_endpoint() (+12 more)

### Community 3 - "test_pipeline_migration_parity.py"
Cohesion: 0.12
Nodes (18): _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key(), _has_alembic_version(), _last_name(), _mapped_columns() (+10 more)

### Community 4 - "PromiseRepository"
Cohesion: 0.15
Nodes (3): PromiseScopeLink, PromiseToPay, PromiseRepository

### Community 6 - "WorkQueuePage.tsx"
Cohesion: 0.17
Nodes (15): @testing-library/user-event@^14.5.2, QueueFilters(), QueueFiltersProps, QueueFilterValues, QueueTable(), QueueTableProps, QueueFilters, useQueue() (+7 more)

### Community 8 - "TASK-3 Backend Feature B1 Handoff"
Cohesion: 0.18
Nodes (9): scheduled_queue_refresh(), Audit Trail, Authentication Flow, Policy Engine, Queue Refresh Process, Role-Based Access, Scheduled Jobs, Seed Credentials (+1 more)

### Community 9 - "test_evaluators.py"
Cohesion: 0.07
Nodes (19): test_all_belong_to_fails(), test_collection_min_size_fails(), test_collection_min_size_passes(), test_collection_min_size_with_empty(), test_collection_min_size_with_none(), test_decimal_greater_than_passes(), test_decimal_greater_than_with_none(), test_field_equals_context_fails() (+11 more)

### Community 11 - "health.py"
Cohesion: 0.24
Nodes (5): health(), readiness(), HealthCheckSchema, HealthResponse, ReadinessResponse

### Community 19 - "auth-context.tsx"
Cohesion: 0.20
Nodes (12): apiClient, ApiError, request(), RequestOptions, AuthContext, AuthContextValue, LoginRequest, LogoutResponse (+4 more)

### Community 20 - "sqlalchemy_orm"
Cohesion: 0.10
Nodes (9): run_migrations_offline(), run_migrations_online(), downgrade(), upgrade(), downgrade(), upgrade(), Base, InteractionLogEntry (+1 more)

### Community 22 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 23 - "Frontend - Receivables & Collections Application"
Cohesion: 0.11
Nodes (17): API Integration, Build, Demo Credentials, Development, End-to-End Tests, Environment Variables, Frontend - Receivables & Collections Application, Lint (+9 more)

### Community 24 - "compilerOptions"
Cohesion: 0.15
Nodes (12): compilerOptions, allowSyntheticDefaultImports, lib, module, moduleResolution, noEmit, noUnusedLocals, noUnusedParameters (+4 more)

### Community 25 - "LandingPage.tsx"
Cohesion: 0.16
Nodes (12): @testing-library/react@^16.0.1, vitest@^2.1.5, FreshnessNotice(), FreshnessNoticeProps, RoleSwitcher(), RoleSwitcherProps, useLanding(), formatDate() (+4 more)

### Community 26 - "devDependencies"
Cohesion: 0.15
Nodes (13): devDependencies, autoprefixer@^10.4.20, eslint@^9.15.0, postcss@^8.4.49, tailwindcss@^3.4.15, @types/react-dom@^18.3.1, typescript@^5.6.3, autoprefixer (+5 more)

### Community 27 - "App.tsx"
Cohesion: 0.14
Nodes (19): dependencies, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0, App(), RequireAuth(), RequireAuthProps, AppShell() (+11 more)

### Community 28 - "configured.py"
Cohesion: 0.17
Nodes (3): get_sap_customer_context_reader(), StubSapCustomerContextReader, StubSapReceivablesReader

### Community 30 - "common.ts"
Cohesion: 0.40
Nodes (4): ApiError, HealthResponse, ReadinessCheck, ReadinessResponse

### Community 31 - "customer.ts"
Cohesion: 0.15
Nodes (19): AccountSummary(), AccountSummaryProps, InvoiceTable(), InvoiceTableProps, SectionCard(), SectionCardProps, PromiseFormProps, useCustomerView() (+11 more)

### Community 32 - "PromiseForm.tsx"
Cohesion: 0.19
Nodes (16): AccountContextCard(), AccountContextCardProps, FailedConditionList(), FailedConditionListProps, POLICY_RULES, PolicyCheckPanel(), PolicyCheckPanelProps, PolicyRule (+8 more)

### Community 34 - "customer360_service.py"
Cohesion: 0.18
Nodes (7): UnappliedCashReference, AccountData, Customer360Response, CustomerListItem, CustomerListResponse, ProfileData, ReceivableItemData

### Community 35 - "steps"
Cohesion: 0.06
Nodes (35): name, runs-on, services, steps, DATABASE_URL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+27 more)

### Community 36 - "typing"
Cohesion: 0.10
Nodes (7): get_landing(), ActiveRoleRequest, ActiveRoleResponse, LandingResponse, RoleOptionSchema, WidgetSchema, WorkspaceService

### Community 37 - "PolicyEvaluationRecord"
Cohesion: 0.12
Nodes (3): PolicyEvaluationRecord, PolicyRepository, test_ac3_new_rules_take_effect_historical_decisions_unchanged()

### Community 41 - "queue_items.py"
Cohesion: 0.17
Nodes (8): get_refresh_run(), list_queue_items(), trigger_queue_refresh(), QueueGroupSchema, QueueItemSchema, QueueListResponse, QueueRefreshRequest, RefreshRunResponse

### Community 42 - "UUID"
Cohesion: 0.17
Nodes (7): PolicyRule, PolicyRuleSetVersion, seed_policy_rules(), test_get_policy_evaluations(), test_get_policy_evaluations_filtered(), test_get_rule_sets(), test_get_rule_sets_with_rules()

### Community 43 - "RequestContext"
Cohesion: 0.14
Nodes (9): Clock, RequestContext, get_clock(), get_correlation_id(), get_db(), get_request_context(), require_action(), create_promise() (+1 more)

### Community 46 - "Customer360Service"
Cohesion: 0.16
Nodes (5): InvoiceData, PromiseData, Section, UnappliedCashData, Customer360Service

### Community 47 - "datetime"
Cohesion: 0.12
Nodes (6): LoginAttempt, User, UserRepository, test_get_customer_view(), test_get_customers_list(), test_get_promise_by_id()

### Community 48 - "SapReceivablesReader"
Cohesion: 0.15
Nodes (4): SapCustomerContextReader, SapReceivablesReader, SAP Integration, SAP Integration

### Community 51 - "Customer"
Cohesion: 0.14
Nodes (8): SapReferenceSynchronizer, Customer, CustomerAccount, Invoice, ReceivableItem, ReferenceRepository, test_fr_c360_001_criterion_1_unified_view(), test_non_standard_items_flagged()

### Community 52 - "promise_service.py"
Cohesion: 0.18
Nodes (10): _check_action(), AppError, AuthenticationError, AuthorizationError, ConflictError, NotFoundError, RateLimitError, SapUnavailableError (+2 more)

### Community 53 - "cli.py"
Cohesion: 0.18
Nodes (5): activate_rule_set(), purge_audit_events(), seed(), SystemClock, docker-entrypoint.sh script

### Community 54 - "auth.py"
Cohesion: 0.23
Nodes (9): get_session(), login(), logout(), LoginRequest, LogoutResponse, RoleContextSchema, SessionResponse, TokenResponse (+1 more)

### Community 55 - "backend"
Cohesion: 0.12
Nodes (18): build, environment, ports, volumes, x-preview-port, args, context, dockerfile (+10 more)

### Community 63 - "eslint.config.js"
Cohesion: 0.18
Nodes (10): @eslint/js@^9.15.0, eslint-plugin-react-hooks@^5.0.0, eslint-plugin-react-refresh@^0.4.14, globals@^15.12.0, typescript-eslint@^8.15.0, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh (+2 more)

### Community 64 - "package.json"
Cohesion: 0.15
Nodes (12): jsdom@^25.0.1, @types/node@^22.10.2, @types/react@^18.3.12, engines, node, name, private, type (+4 more)

### Community 65 - "db_session"
Cohesion: 0.25
Nodes (3): auth_client(), client(), db_session()

### Community 66 - "routers/policy.py"
Cohesion: 0.17
Nodes (8): list_policy_evaluations(), list_rule_sets(), PolicyEvaluationItem, PolicyEvaluationListResponse, PolicyEvaluationResultSchema, RuleItem, RuleSetItem, RuleSetListResponse

### Community 69 - "TASK-4 Backend Feature B2 Handoff"
Cohesion: 0.09
Nodes (21): Acceptance Criteria Covered, Audit Events, AuditEventListResponse, Customer360Response, Customer 360 Section States, CustomerListResponse, Customers, Endpoints Added (+13 more)

### Community 70 - "security.py"
Cohesion: 0.11
Nodes (6): create_access_token(), decode_access_token(), verify_password(), test_api_health_endpoint(), test_health_endpoint(), test_models_import()

### Community 71 - "test_policy_acceptance.py"
Cohesion: 0.13
Nodes (7): policy_service(), rule_set_v1(), rule_set_v2(), test_ac1_all_configured_policy_validations_applied(), test_ac2_multiple_failures_all_identified(), test_ac2_policy_validation_fails_action_rejected_with_condition(), test_deterministic_evaluation_same_input_same_result()

### Community 72 - "list_promises"
Cohesion: 0.22
Nodes (3): list_promises(), PromiseListItem, PromiseListResponse

### Community 73 - "Endpoints Added"
Cohesion: 0.40
Nodes (5): Authentication, Endpoints Added, Health, Queue Items, Workspace

### Community 74 - "Request/Response Shapes"
Cohesion: 0.40
Nodes (5): LandingResponse, QueueListResponse, RefreshRunResponse, Request/Response Shapes, TokenResponse

### Community 76 - "test_policy_engine_service.py"
Cohesion: 0.14
Nodes (8): test_evaluate_all_rules_pass(), test_evaluate_disabled_rule_not_evaluated(), test_evaluate_multiple_rules_fail(), test_evaluate_no_active_rule_set_allows(), test_evaluate_one_rule_fails(), test_evaluate_only_evaluates_matching_action_type(), test_evaluate_persists_evaluation_record(), test_evaluate_stores_input_snapshot()

### Community 78 - "queue_service.py"
Cohesion: 0.08
Nodes (10): get_sap_receivables_reader(), PrioritizationAssessment, QueueItem, SapSyncRun, SapTransactionReference, QueueRepository, SyncRunRepository, QueueService (+2 more)

### Community 79 - "active_rule_set"
Cohesion: 0.22
Nodes (4): active_rule_set(), policy_service(), promise_amount_rule(), promise_scope_rule()

### Community 80 - "TASK-5 Handoff: Backend Feature B3 - Deterministic Policy Enforcement"
Cohesion: 0.10
Nodes (19): Acceptance Tests (5 tests), activate-rule-set, Audit Service Security Guard, CLI Commands Added, Database Changes, Evaluation History, FR-DTC-001 Coverage, Notes (+11 more)

### Community 83 - "FixedClock"
Cohesion: 0.10
Nodes (13): FixedClock, RoleContext, test_fr_c360_001_criterion_2_unavailable_sections(), test_fr_c360_001_criterion_3_field_masking(), test_get_customer_view_with_masking(), test_get_customer_view_with_sensitive_access(), test_search_customers(), test_fr_ptp_001_criterion_1_mandatory_fields() (+5 more)

### Community 85 - "main.py"
Cohesion: 0.14
Nodes (4): lifespan(), list_audit_events(), AuditEventItem, AuditEventListResponse

### Community 86 - "useLanding.ts"
Cohesion: 0.53
Nodes (4): ActiveRoleRequest, ActiveRoleResponse, LandingResponse, LandingWidget

### Community 87 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, type-check

### Community 94 - "vite"
Cohesion: 0.40
Nodes (4): vite@^6.0.1, @vitejs/plugin-react@^4.3.4, vite, @vitejs/plugin-react

### Community 108 - "test_promise_acceptance.py"
Cohesion: 0.20
Nodes (5): PromiseCreateRequest, PromiseResponse, ScopeLinkInput, ScopeLinkOutput, SourceInteractionInput

### Community 110 - "start.sh"
Cohesion: 0.53
Nodes (4): check_prerequisites(), find_available_port(), port_in_use(), start.sh script

## Knowledge Gaps
- **1 isolated node(s):** `lbg-ftr-receivables-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 667 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **60 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clock` connect `RequestContext` to `PromiseRepository`, `AuthService`, `InteractionRepository`, `customer360_service.py`, `typing`, `queue_items.py`, `UUID`, `audit.py`, `datetime`, `SapReceivablesReader`, `auth.py`, `.login`, `routers/policy.py`, `IdempotencyRecord`, `switch_active_role`, `list_promises`, `queue_service.py`, `main.py`, `PolicyEngineService`, `get_customer_view`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Customer` (e.g. with `SapReferenceSynchronizer` and `ReferenceRepository`) actually correct?**
  _`Customer` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `lbg-ftr-receivables-backend` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Intelligent Receivables and Collections Application` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Why does `RequestContext` connect `RequestContext` to `routers/policy.py`, `customer360_service.py`, `typing`, `switch_active_role`, `PromiseRepository`, `list_promises`, `queue_items.py`, `test_promise_acceptance.py`, `get_customer_view`, `Customer360Service`, `.create_promise`, `Customer`, `FixedClock`, `main.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Should `UUID` be split into smaller, more focused modules?**
  _Cohesion score 0.09371980676328502 - nodes in this community are weakly interconnected._
- **Why does `PolicyFailureError` connect `PolicyFailureError` to `PromiseRepository`, `TASK-4 Backend Feature B2 Handoff`, `test_promise_acceptance.py`, `.create_promise`, `promise_service.py`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._