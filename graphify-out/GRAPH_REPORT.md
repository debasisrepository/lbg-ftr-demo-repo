# Graph Report - lbg-ftr-demo-repo  (2026-11-23)

## Corpus Check
- 210 files · ~91,772 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 5, .example 2, .ini 2)

## Summary
- 2061 nodes · 3657 edges · 157 communities (86 shown, 71 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 342 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `341e2e54`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Release 1 Mobile Banking Platform
- ScamCheckOutcome
- steps
- test_pipeline_migration_parity.py
- main.py
- test_auth_service.py
- PaymentIntent
- auth-context.tsx
- LBG FTR Demo Backend
- TASK-5 Handoff: Backend Feature B3 - Balance Availability and Saved Payees
- TASK-12 Handoff: UI U2 - Payee Selection and Payment Entry
- set_sqlite_pragma
- Deployment Guide
- lbg-ftr-demo-backend
- index.ts
- compilerOptions
- compilerOptions
- outbox_publisher.py
- scripts
- AuthRepository
- TASK-3 Handoff: Backend Feature B1 - Sign-in and Session
- TASK-11 Handoff: UI U1 - Sign In and Accounts Overview
- AccountsOverviewPage.tsx
- TASK-6 Handoff: Backend Feature B4 - Payment Initiation
- CIAMSandboxAdapter
- TestPaymentsIntegration
- AccountService
- auth_service.py
- test_auth_integration.py
- .change_payment_review
- with
- vitest
- payments.py
- TestFRAuth003PasscodeSignIn
- Completed Backend Features
- test_smoke.py
- pytest
- status.py
- TASK-15: Integration and End-to-End Tests - Completion Report
- Task 4 Handoff: Accounts Overview and Freshness
- CustomerProfileRef
- AccountReadModelRepository
- IdempotencyRecord
- TestFRPAY002InitiatePayment
- backend
- TestFRPAY003CapturePaymentReference
- Completed Backend Features
- conftest.py
- database
- uuid
- react
- test_accounts_service.py
- test_payments_submission_acceptance.py
- health_check
- env.py
- TASK-7 Handoff: Backend Payment Review and Approval
- package.json
- payees.py
- .approve_and_submit
- DeviceRegistration
- PayeesPage.tsx
- Settings
- get_accounts_overview
- PaymentFailedPage.tsx
- AuthService
- Layout.tsx
- CorrelationMiddleware
- ScamCheckRepository
- process_payment_event
- TASK-10 Handoff: Backend Payment Outcome Details and Idempotency
- sqlalchemy
- test_payments_approval_acceptance.py
- jobs
- test_payees_service.py
- test_payments_approval_integration.py
- test_payments_approval_service.py
- react-router-dom
- deploy-production
- @playwright/test
- run_e2e_server.sh
- with
- ._converge_customer_visible_status
- steps
- CapabilityStatusService
- jobs
- CI/CD Pipeline Configuration Summary
- d94ecebe79c4accf0cddae40b9b06c09350cb47f.md
- e2e-test
- 9eb900594db37556340772852fe5de2433c7ebb0.md
- fa70209e24a1c3c24f44f5b56aa1bbe4773d7dc5.md
- auth.py
- start.sh
- CI/CD Pipeline Documentation
- 20261123_0010_add_outbox_execution_status_projection.py
- JSONORJSONB
- docker-entrypoint.sh
- stop.sh
- environment
- approve_and_submit_payment
- build-and-publish
- CI Pipeline Details
- CD Pipeline Details
- Implemented Artifacts
- rollback
- backend-test
- integration-report
- on
- 20261122_2400_add_scam_check_outcomes.py
- Best Practices Implemented
- steps
- frontend-test
- security-scan
- Pipeline Architecture
- Monitoring & Alerts
- Environment Configuration

## God Nodes (most connected - your core abstractions)
1. `PaymentOrchestrationService` - 81 edges
2. `AccountReadModel` - 74 edges
3. `Payee` - 72 edges
4. `CustomerProfileRef` - 51 edges
5. `CapabilityStatusRecord` - 38 edges
6. `PaymentIntent` - 35 edges
7. `ScamCheckOutcome` - 26 edges
8. `AuthService` - 26 edges
9. `AccountService` - 25 edges
10. `AuthRepository` - 23 edges

## Surprising Connections (you probably didn't know these)
- `Entitlement Checks` --references--> `EntitlementSandboxAdapter`  [INFERRED]
  .handoff/TASK-4.md → backend/app/adapters/entitlement_sandbox_adapter.py
- `POST /api/v1/payments/{payment_id}/submit` --references--> `PaymentSubmitRequest`  [INFERRED]
  .handoff/TASK-7.md → backend/app/schemas/payments_schemas.py
- `Middleware` --references--> `CorrelationMiddleware`  [INFERRED]
  .handoff/TASK-3.md → backend/app/middleware/correlation_middleware.py
- `Known Issues` --references--> `test_idempotent_payment_submission()`  [INFERRED]
  .handoff/TASK-10.md → backend/tests/test_payments_idempotency.py
- `Known Issues` --references--> `test_payment_submit_idempotency_key_reuse_different_body()`  [INFERRED]
  .handoff/TASK-10.md → backend/tests/test_payments_idempotency.py

## Import Cycles
- None detected.

## Communities (157 total, 71 thin omitted)

### Community 0 - "Release 1 Mobile Banking Platform"
Cohesion: 0.05
Nodes (43): API Documentation, Architecture Overview, Backend Configuration, Backend Development, Backend (FastAPI + SQLAlchemy + SQLite/PostgreSQL), Backend Tests, CI/CD Pipeline, Continuous Deployment (`.github/workflows/cd.yml`) (+35 more)

### Community 1 - "ScamCheckOutcome"
Cohesion: 0.10
Nodes (9): AuditEvent, ScamCheckOutcome, test_e11_fraud_allow_moves_to_submission(), test_e11_fraud_hold_moves_to_held_state(), test_e11_fraud_warn_presents_warning(), test_e12_warning_decision_continue_moves_to_submission(), test_e12_warning_decision_continue_not_allowed_returns_403(), test_e12_warning_decision_stop_leaves_unexecuted() (+1 more)

### Community 2 - "steps"
Cohesion: 0.29
Nodes (16): steps, steps, steps, CI, DATABASE_URL, steps, steps, steps (+8 more)

### Community 3 - "test_pipeline_migration_parity.py"
Cohesion: 0.18
Nodes (12): _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key(), _has_alembic_version(), _last_name(), _mapped_columns() (+4 more)

### Community 4 - "main.py"
Cohesion: 0.10
Nodes (4): lifespan(), database_exception_handler(), generic_exception_handler(), validation_exception_handler()

### Community 5 - "test_auth_service.py"
Cohesion: 0.10
Nodes (12): auth_service(), mock_auth_repo(), mock_ciam_adapter(), mock_db(), mock_entitlement_adapter(), sample_credential(), sample_customer(), sample_device() (+4 more)

### Community 6 - "PaymentIntent"
Cohesion: 0.08
Nodes (16): PaymentIntent, test_mark_failed_with_retry(), test_mark_published(), test_fraud_decision_allow_moves_to_submission(), test_fraud_decision_hold_creates_hold_outcome(), test_fraud_decision_unavailable_disables_payments_capability(), test_fraud_decision_warn_creates_scam_outcome_with_warning(), test_payment_response_includes_hold_decision_date_when_held() (+8 more)

### Community 7 - "auth-context.tsx"
Cohesion: 0.15
Nodes (17): App(), RequireAuth(), RequireAuthProps, AuthContext, AuthContextType, AuthProvider(), AuthProviderProps, LoginRequest (+9 more)

### Community 8 - "LBG FTR Demo Backend"
Cohesion: 0.18
Nodes (10): API Endpoints, Database Schema, Development Notes, LBG FTR Demo Backend, Project Structure, Running, Seed Credentials, Setup (+2 more)

### Community 9 - "TASK-5 Handoff: Backend Feature B3 - Balance Availability and Saved Payees"
Cohesion: 0.09
Nodes (14): CoPAdapter, CoPCheckResult, Account Read Model Constraint, Capability Integration, CoP Adapter Seam, Database Schema, Files Modified/Created, Frontend Integration Notes (+6 more)

### Community 10 - "TASK-12 Handoff: UI U2 - Payee Selection and Payment Entry"
Cohesion: 0.09
Nodes (22): API Calls Made, `ApprovalSheet.tsx`, Components Implemented, E2E Tests Implemented, `e2e/wireframe_03_payee_and_entry.spec.ts`, `e2e/wireframe_04_review_and_approval.spec.ts`, Navigation Structure, Pages Implemented (+14 more)

### Community 18 - "Deployment Guide"
Cohesion: 0.04
Nodes (49): All Environments, Backup Strategy, Caching Strategy, Common Issues, Configuration, Configuration, Container Deployments, Creating a Release (+41 more)

### Community 22 - "index.ts"
Cohesion: 0.05
Nodes (33): AccountReadModel, AccountsOverviewResponse, AccountSummary, CustomerProfileRef, DeviceRegistration, LoginRequest, LoginResponse, SessionResponse (+25 more)

### Community 23 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 24 - "compilerOptions"
Cohesion: 0.17
Nodes (11): compilerOptions, allowSyntheticDefaultImports, composite, lib, module, moduleResolution, resolveJsonModule, skipLibCheck (+3 more)

### Community 25 - "outbox_publisher.py"
Cohesion: 0.05
Nodes (10): FraudEngineSandboxAdapter, PaymentsHubAdapter, PaymentExecutionStatus, PaymentOutboxEvent, PaymentExecutionStatusRepository, PaymentOutboxRepository, PaymentRepository, test_get_pending_events() (+2 more)

### Community 26 - "scripts"
Cohesion: 0.25
Nodes (8): scripts, build, dev, lint, preview, test, test:watch, type-check

### Community 27 - "AuthRepository"
Cohesion: 0.07
Nodes (4): AuthenticationEvent, UserSession, AuthRepository, hash_device_identifier()

### Community 29 - "TASK-3 Handoff: Backend Feature B1 - Sign-in and Session"
Cohesion: 0.11
Nodes (17): Backend Flows, Configuration, Database Tables Used, E-01: POST /api/v1/auth/login, E-02: GET /api/v1/auth/session, E-03: POST /api/v1/auth/logout, E-13: GET /health, E-14: GET /health/ready (+9 more)

### Community 30 - "TASK-11 Handoff: UI U1 - Sign In and Accounts Overview"
Cohesion: 0.10
Nodes (19): Acceptance Criteria Coverage, API Integration, Auth Context Updates, Components, Components Implemented, Design Fidelity, E2E Tests, FR-ACCT-001 (Accounts overview) (+11 more)

### Community 31 - "AccountsOverviewPage.tsx"
Cohesion: 0.12
Nodes (17): CapabilityBanner(), CapabilityBannerProps, apiClient, ApiError, request(), AccountItem, AccountsResponse, CapabilityStatus (+9 more)

### Community 32 - "TASK-6 Handoff: Backend Feature B4 - Payment Initiation"
Cohesion: 0.10
Nodes (20): Acceptance Criteria Verified, Adapters Scaffolded (not called in this task), Backend Flows, Configuration, Database Tables, E-07: Create Payment Review, E-07: POST /api/v1/payments, E-10: Change Payment Review (+12 more)

### Community 35 - "AccountService"
Cohesion: 0.10
Nodes (8): AccountItem, AccountOverviewResponse, Balance, CapabilityStatus, AccountService, test_compute_freshness_text(), test_format_currency(), test_get_accounts_overview_entitlement_denied()

### Community 36 - "auth_service.py"
Cohesion: 0.10
Nodes (5): LoginRequest, LoginResponse, SessionResponse, test_login_unregistered_device(), test_login_wrong_passcode()

### Community 40 - "test_auth_integration.py"
Cohesion: 0.08
Nodes (11): test_correlation_id_propagation(), test_login_success(), test_login_unregistered_device(), test_login_validation_error(), test_login_wrong_passcode(), test_logout_no_token(), test_logout_success(), test_multiple_logins_create_separate_sessions() (+3 more)

### Community 44 - "with"
Cohesion: 0.11
Nodes (18): with, build-args, cache, cache-dependency-path, cache-from, cache-to, context, file (+10 more)

### Community 45 - "vitest"
Cohesion: 0.14
Nodes (13): @testing-library/react@^16.0.1, vitest@^2.1.5, AccountCard(), AccountCardProps, AccountItem, BadgeIcon(), BadgeIconProps, mockLogout (+5 more)

### Community 46 - "payments.py"
Cohesion: 0.09
Nodes (16): change_payment_review(), get_payment(), list_payments(), record_warning_decision(), UserSummary, ApprovalCredential, PaymentAccountSummary, PaymentChangeRequest (+8 more)

### Community 47 - "TestFRAuth003PasscodeSignIn"
Cohesion: 0.08
Nodes (4): test_health_endpoint_no_database(), test_readiness_endpoint_checks_database(), TestFRAuth003PasscodeSignIn, TestFRAuth006SessionContinuity

### Community 48 - "Completed Backend Features"
Cohesion: 0.17
Nodes (11): Audit Trail, Completed Backend Features, Database, Fraud Decision Rules (Sandbox), Frontend Integration Notes, Governed Next Steps, Response Shapes, Seed Data Usage (+3 more)

### Community 49 - "test_smoke.py"
Cohesion: 0.20
Nodes (4): test_database_connection(), test_health_check(), test_readiness_check(), test_test_customer_fixture()

### Community 50 - "pytest"
Cohesion: 0.17
Nodes (9): test_logout_session_not_found(), test_validate_session_expired(), test_validate_session_revoked(), _env(), _is_async(), _run(), _seed_module(), seeded() (+1 more)

### Community 51 - "status.py"
Cohesion: 0.15
Nodes (5): get_capability_statuses(), _get_customer_message(), _get_recovery_guidance(), CapabilityStatusItem, CapabilityStatusListResponse

### Community 52 - "TASK-15: Integration and End-to-End Tests - Completion Report"
Cohesion: 0.06
Nodes (30): 1. Explicit Login Through Form, 1. journey_new_request_to_sent.spec.ts, 2. Graceful Error Handling, 2. journey_new_request_to_pending.spec.ts, 3. journey_warning_stop.spec.ts, 3. Robust Navigation, 4. journey_session_reconnect.spec.ts, Acceptance Criteria Verification (+22 more)

### Community 53 - "Task 4 Handoff: Accounts Overview and Freshness"
Cohesion: 0.11
Nodes (17): Balance Availability States, Capability Status, Customer 1: Alex Taylor (CUST-SYNTH-001), Customer 2: Jordan Smith (CUST-SYNTH-002), Endpoints Implemented, Entitlement Checks, Freshness Indicators, GET /api/v1/accounts (+9 more)

### Community 54 - "CustomerProfileRef"
Cohesion: 0.05
Nodes (24): CapabilityStatusRecord, CustomerProfileRef, SandboxEntitlement, hash_passcode(), seed_database(), test_fr_acct_001_accounts_overview_authenticated_entitled(), test_fr_acct_001_partial_data_communicated(), test_fr_acct_002_freshness_indicator_visible() (+16 more)

### Community 58 - "backend"
Cohesion: 0.11
Nodes (19): build, container_name, environment, ports, volumes, x-preview-port, context, dockerfile (+11 more)

### Community 60 - "Completed Backend Features"
Cohesion: 0.14
Nodes (13): Completed Backend Features, Database Tables, E-11 Final Flow, Endpoints Summary, Event Consumers, Frontend Integration Notes, Hold Outcomes (from TASK-8 integration), Response Shapes (+5 more)

### Community 61 - "conftest.py"
Cohesion: 0.13
Nodes (6): SandboxCredential, auth_client(), client(), db_session(), _fresh_schema(), test_customer()

### Community 62 - "database"
Cohesion: 0.11
Nodes (18): PIP_TARGET, build, depends_on, environment, args, context, dockerfile, container_name (+10 more)

### Community 63 - "uuid"
Cohesion: 0.05
Nodes (30): AccountReadModel, Payee, test_fr_pay_001_selecting_payee_for_payment(), test_fr_pay_001_unavailable_payee_not_selectable(), test_get_payees_pagination(), test_fr_pay_009_ac1_payment_journey_can_present_risk_warning(), test_fr_pay_009_ac2_warning_content_makes_clear_payment_may_be_unsafe(), test_fr_pay_009_ac3_payment_does_not_bypass_mandatory_warning() (+22 more)

### Community 64 - "react"
Cohesion: 0.18
Nodes (11): ApprovalSheet(), ApprovalSheetProps, PaymentReviewResponse, WarningDialog(), WarningDialogProps, PaymentReviewPage(), PaymentReviewResponse, PaymentReviewResponse (+3 more)

### Community 65 - "test_accounts_service.py"
Cohesion: 0.22
Nodes (3): test_get_accounts_overview_stale_balance(), test_get_accounts_overview_success(), test_get_accounts_overview_unavailable_balance()

### Community 66 - "test_payments_submission_acceptance.py"
Cohesion: 0.11
Nodes (8): test_failed_status_distinguishes_from_sending(), test_held_payment_shown_as_pending_not_sent(), test_hold_includes_payment_reference(), test_hold_outcome_distinguishable_from_sent(), test_no_conflicting_payment_outcomes(), test_payment_outcome_maps_to_exactly_one_status(), test_pending_includes_do_not_resubmit_guidance(), test_pending_status_avoids_duplicate_payment_behavior()

### Community 69 - "TASK-7 Handoff: Backend Payment Review and Approval"
Cohesion: 0.07
Nodes (26): Acceptance Criteria Coverage, API Contract Verification, Approval Flow (E-11), Approve and submit payment (E-11, new in TASK-7), Configuration, Create payment review (E-07, from TASK-6), Database Schema Changes, dynamic_link_approvals table (+18 more)

### Community 70 - "package.json"
Cohesion: 0.06
Nodes (39): dependencies, clsx@^2.1.1, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0, tailwind-merge@^2.5.5, devDependencies, autoprefixer@^10.4.20 (+31 more)

### Community 73 - "payees.py"
Cohesion: 0.09
Nodes (8): EntitlementSandboxAdapter, CapabilityStatusRepository, PayeeRepository, get_saved_payees(), CapabilityStatus, PayeeItem, PayeeListResponse, PayeeService

### Community 74 - ".approve_and_submit"
Cohesion: 0.10
Nodes (3): DynamicLinkApproval, DynamicLinkApprovalRepository, Endpoints

### Community 78 - "PayeesPage.tsx"
Cohesion: 0.25
Nodes (7): PayeeItem, PayeeListItem(), PayeeListItemProps, CapabilityStatus, CapabilityStatusesResponse, PayeeItem, PayeesResponse

### Community 83 - "PaymentFailedPage.tsx"
Cohesion: 0.25
Nodes (9): OutcomeBadge(), OutcomeBadgeProps, ReconnectingStatus(), PaymentDetailsResponse, PaymentFailedPage(), PaymentDetailsResponse, PaymentSentPage(), mockNavigate (+1 more)

### Community 85 - "Layout.tsx"
Cohesion: 0.48
Nodes (4): Header(), Layout(), LayoutProps, HomePage()

### Community 90 - "TASK-10 Handoff: Backend Payment Outcome Details and Idempotency"
Cohesion: 0.11
Nodes (17): Acceptance Criteria Coverage, API Contracts, Bug Fixes, E-08 GET /api/v1/payments/{payment_id}, E-09 GET /api/v1/payments, Files Created, Files Modified, FR-PAY-013 (Outcome details): (+9 more)

### Community 92 - "sqlalchemy"
Cohesion: 0.05
Nodes (7): upgrade(), ConsumedEvent, EntitlementDecision, NotificationDeliveryAttempt, NotificationTriggerRecord, PaymentStateTransition, ReadModelFreshnessRecord

### Community 94 - "jobs"
Cohesion: 0.13
Nodes (14): env, NODE_VERSION, PYTHON_VERSION, REGISTRY, jobs, smoke-test-production, smoke-test-staging, name (+6 more)

### Community 95 - "test_payees_service.py"
Cohesion: 0.09
Nodes (14): healthy_capability(), mock_capability_repo(), mock_entitlement_adapter(), mock_payee_repo(), payee_service(), sample_customer_id(), sample_payees(), test_get_saved_payees_capability_unavailable() (+6 more)

### Community 98 - "react-router-dom"
Cohesion: 0.39
Nodes (5): PendingBadge(), PaymentPendingPage(), PaymentReviewResponse, mockNavigate, react-router-dom

### Community 100 - "deploy-production"
Cohesion: 0.14
Nodes (15): environment, if, name, needs, runs-on, environment, if, name (+7 more)

### Community 107 - "with"
Cohesion: 0.13
Nodes (15): with, cache, cache-dependency-path, files, flags, format, name, node-version (+7 more)

### Community 116 - "._converge_customer_visible_status"
Cohesion: 0.18
Nodes (5): test_converge_customer_visible_status_failed(), test_converge_customer_visible_status_none_for_not_submitted(), test_converge_customer_visible_status_pending(), test_converge_customer_visible_status_sent(), test_status_convergence_one_function()

### Community 117 - "steps"
Cohesion: 0.27
Nodes (14): steps, steps, steps, BASE_URL, steps, steps, steps, env (+6 more)

### Community 119 - "jobs"
Cohesion: 0.14
Nodes (13): name, needs, runs-on, env, NODE_VERSION, POSTGRES_VERSION, PYTHON_VERSION, name (+5 more)

### Community 120 - "CI/CD Pipeline Configuration Summary"
Cohesion: 0.15
Nodes (13): CI/CD Pipeline Configuration Summary, Compliance and Governance, Continuous Deployment, Continuous Integration, Environment Configuration, Environment Variables, Future Enhancements, Integration with Existing Infrastructure (+5 more)

### Community 121 - "d94ecebe79c4accf0cddae40b9b06c09350cb47f.md"
Cohesion: 0.33
Nodes (5): Error details, Instructions, Page snapshot, Test info, Test source

### Community 122 - "e2e-test"
Cohesion: 0.15
Nodes (13): name, needs, runs-on, services, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, e2e-test (+5 more)

### Community 123 - "9eb900594db37556340772852fe5de2433c7ebb0.md"
Cohesion: 0.40
Nodes (4): Error details, Instructions, Test info, Test source

### Community 124 - "fa70209e24a1c3c24f44f5b56aa1bbe4773d7dc5.md"
Cohesion: 0.40
Nodes (4): Error details, Instructions, Test info, Test source

### Community 126 - "auth.py"
Cohesion: 0.19
Nodes (6): get_db(), get_correlation_id(), get_client_address(), get_session(), login(), logout()

### Community 127 - "start.sh"
Cohesion: 0.48
Nodes (6): check_prerequisites(), DATABASE_URL, find_available_port(), native_path(), port_in_use(), start.sh script

### Community 128 - "CI/CD Pipeline Documentation"
Cohesion: 0.18
Nodes (11): Best Practices, CI/CD Pipeline Documentation, Common CD Failures, Common CI Failures, For Developers, For Release Managers, Maintenance, Overview (+3 more)

### Community 135 - "environment"
Cohesion: 0.18
Nodes (11): description, options, required, type, environment, on, push, workflow_dispatch (+3 more)

### Community 137 - "build-and-publish"
Cohesion: 0.20
Nodes (10): name, outputs, permissions, runs-on, build-and-publish, backend-image, frontend-image, version (+2 more)

### Community 138 - "CI Pipeline Details"
Cohesion: 0.22
Nodes (9): 1. Backend Lint & Type Check, 2. Backend Tests, 3. Frontend Lint & Type Check, 4. Frontend Tests, 5. E2E Tests, 6. Docker Build & Stack Test, 7. Security Scan, 8. Integration Report (+1 more)

### Community 140 - "CD Pipeline Details"
Cohesion: 0.29
Nodes (7): 1. Build & Publish Container Images, 2. Deploy to Staging, 3. Smoke Test Staging, 4. Deploy to Production, 5. Smoke Test Production, 6. Rollback Procedure, CD Pipeline Details

### Community 141 - "Implemented Artifacts"
Cohesion: 0.33
Nodes (6): 1. Continuous Integration Pipeline (`.github/workflows/ci.yml`), 2. Continuous Deployment Pipeline (`.github/workflows/cd.yml`), 3. CI/CD Documentation (`CI_CD.md`), 4. Deployment Guide (`DEPLOYMENT.md`), 5. Updated README.md, Implemented Artifacts

### Community 142 - "rollback"
Cohesion: 0.40
Nodes (5): rollback, if, name, needs, runs-on

### Community 143 - "backend-test"
Cohesion: 0.40
Nodes (5): name, needs, runs-on, services, backend-test

### Community 144 - "integration-report"
Cohesion: 0.40
Nodes (5): if, name, needs, runs-on, integration-report

### Community 145 - "on"
Cohesion: 0.40
Nodes (5): on, pull_request, push, branches, branches

### Community 146 - "20261122_2400_add_scam_check_outcomes.py"
Cohesion: 0.12
Nodes (5): upgrade(), upgrade(), upgrade(), upgrade(), upgrade()

### Community 148 - "Best Practices Implemented"
Cohesion: 0.50
Nodes (4): Best Practices Implemented, For Developers, For Operations, For Release Managers

### Community 149 - "steps"
Cohesion: 0.50
Nodes (4): name, runs-on, steps, backend-lint-and-type-check

### Community 150 - "frontend-test"
Cohesion: 0.50
Nodes (4): name, needs, runs-on, frontend-test

### Community 151 - "security-scan"
Cohesion: 0.50
Nodes (4): security-scan, name, needs, runs-on

### Community 152 - "Pipeline Architecture"
Cohesion: 0.67
Nodes (3): CD Pipeline (`.github/workflows/cd.yml`), CI Pipeline (`.github/workflows/ci.yml`), Pipeline Architecture

### Community 153 - "Monitoring & Alerts"
Cohesion: 0.67
Nodes (3): Deployment Metrics, Monitoring & Alerts, Pipeline Notifications

### Community 154 - "Environment Configuration"
Cohesion: 0.67
Nodes (3): Environment Configuration, Environment Variables, Required Secrets

## Knowledge Gaps
- **2 isolated node(s):** `DATABASE_URL`, `lbg-ftr-demo-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1165 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **71 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PaymentOrchestrationService` connect `payments.py` to `CIAMSandboxAdapter`, `ScamCheckOutcome`, `PaymentIntent`, `approve_and_submit_payment`, `payees.py`, `.approve_and_submit`, `.change_payment_review`, `._converge_customer_visible_status`, `ScamCheckRepository`, `IdempotencyRecord`, `outbox_publisher.py`, `AuthRepository`, `.create_payment_review`, `conftest.py`, `uuid`?**
  _High betweenness centrality (0.056) - this node is a cross-community bridge._
- **Are the 38 inferred relationships involving `PaymentOrchestrationService` (e.g. with `approve_and_submit_payment()` and `change_payment_review()`) actually correct?**
  _`PaymentOrchestrationService` has 38 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DATABASE_URL`, `lbg-ftr-demo-backend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Release 1 Mobile Banking Platform` be split into smaller, more focused modules?**
  _Cohesion score 0.046511627906976744 - nodes in this community are weakly interconnected._
- **Why does `AccountReadModel` connect `uuid` to `test_accounts_service.py`, `ScamCheckOutcome`, `TestPaymentsIntegration`, `PaymentIntent`, `.create_payment_review`, `payments.py`, `CustomerProfileRef`, `AccountReadModelRepository`, `CapabilityStatusService`, `outbox_publisher.py`, `TestFRPAY003CapturePaymentReference`, `sqlalchemy`, `TestFRPAY002InitiatePayment`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 35 inferred relationships involving `AccountReadModel` (e.g. with `PaymentRepository` and `AccountReadModelRepository`) actually correct?**
  _`AccountReadModel` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Should `ScamCheckOutcome` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._