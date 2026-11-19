# Graph Report - lbg-ftr-demo-repo  (2026-11-19)

## Corpus Check
- 217 files · ~74,258 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 17 file(s) not represented in the graph (top: (none) 7, .css 2, .tsbuildinfo 2)

## Summary
- 2035 nodes · 4098 edges · 126 communities (73 shown, 53 thin omitted)
- Extraction: 94% EXTRACTED · 6% INFERRED · 0% AMBIGUOUS · INFERRED: 263 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `341e2e54`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Sample Bank Mobile Payments MVP
- package.json
- test_pipeline_migration_parity.py
- conftest.py
- .verify_challenge
- react
- compilerOptions
- index.ts
- compilerOptions
- steps
- @vitejs/plugin-react
- scripts
- tsconfig.json
- start.sh
- ReviewApprovePage.tsx
- PaymentFlowProvider.tsx
- test_auth_integration.py
- .submit_proof
- stop.sh
- auth.py
- lbg-ftr-demo-backend
- payments.py
- ciam_adapter.py
- get_rate_limiter
- fraud_case_adapter.py
- security.py
- ApprovalService
- seed.py
- loan_adapter.py
- DeviceRepository
- errors.py
- profiles.py
- AuthAttemptRepository
- react
- test_payments_acceptance.py
- AccountsPage.tsx
- core_banking_adapter.py
- observability_adapter.py
- .create_payee
- healthcheck
- playwright.config.ts
- backend
- mandate_adapter.py
- cop_adapter.py
- get_accounts_overview
- adapters.py
- payee_schemas.py
- payee_directory_adapter.py
- test_payees_acceptance.py
- uuid
- profiles.py
- BankAccountRepository
- status_recorder.py
- ProofPage.tsx
- test_accounts_acceptance.py
- payments_hub_adapter.py
- test_profiles_acceptance.py
- EntitlementService
- notification.py
- notifications.py
- payment_service.py
- ValidationError
- AdapterBase
- payment_service.py
- get_db
- payments.py
- payment_limit_repository.py
- support_routing_adapter.py
- notification_service.py
- PayeeRepository
- LoginRateLimiter
- TreatmentMapper
- PaymentService
- errors.py
- ServiceStatusNotice
- fraud_decision_adapter.py
- AddPayeePage.tsx
- .get_by_customer_id
- middleware.py
- notification_adapter.py
- DuplicateDetector
- test_health_acceptance.py
- test_notifications_acceptance.py
- devDependencies
- FraudService
- eslint.config.js
- App.tsx
- IdempotencyRecord
- Base
- sqlalchemy
- CapabilityHealthRegistry
- @testing-library/jest-dom
- test_smoke.py
- docker-entrypoint.sh
- account_schemas.py
- profile_schemas.py
- playwright.config.ts
- datetime
- models/__init__.py
- test_entitlement_service.py
- Settings
- support.py

## God Nodes (most connected - your core abstractions)
1. `Base` - 37 edges
2. `get_rate_limiter()` - 32 edges
3. `AdapterBase` - 28 edges
4. `react` - 25 edges
5. `PayeeService` - 24 edges
6. `react-router-dom` - 22 edges
7. `PaymentService` - 20 edges
8. `AuthorizationError` - 20 edges
9. `CopService` - 19 edges
10. `EntitlementService` - 19 edges

## Surprising Connections (you probably didn't know these)
- `PayeeService` --uses--> `PayeeRepository`  [INFERRED]
  backend/app/services/payee_service.py → backend/app/repositories/payee_repository.py
- `PaymentService` --uses--> `PayeeRepository`  [INFERRED]
  backend/app/services/payment_service.py → backend/app/repositories/payee_repository.py
- `get_accounts_overview()` --uses--> `ProfileService`  [INFERRED]
  backend/app/routers/accounts.py → backend/app/services/profile_service.py
- `prepare_payment()` --uses--> `PaymentService`  [INFERRED]
  backend/app/routers/payments.py → backend/app/services/payment_service.py
- `approve_payment()` --uses--> `PaymentService`  [INFERRED]
  backend/app/routers/payments.py → backend/app/services/payment_service.py

## Import Cycles
- None detected.

## Communities (126 total, 53 thin omitted)

### Community 0 - "Sample Bank Mobile Payments MVP"
Cohesion: 0.04
Nodes (47): 1. Clone and Setup, 2. Start the Application, 3. Access the Application, 4. Stop the Application, API Documentation, Architecture, Backend Configuration, Backend Job (+39 more)

### Community 1 - "package.json"
Cohesion: 0.13
Nodes (14): jsdom@^25.0.1, tailwindcss@^3.4.15, @types/node@^26.6.6, @types/react-dom@^18.3.1, engines, node, name, private (+6 more)

### Community 2 - "test_pipeline_migration_parity.py"
Cohesion: 0.12
Nodes (18): _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key(), _has_alembic_version(), _last_name(), _mapped_columns() (+10 more)

### Community 3 - "conftest.py"
Cohesion: 0.11
Nodes (7): Customer, auth_client(), client(), db_session(), demo_customer(), _fresh_schema(), seeded_data()

### Community 5 - "react"
Cohesion: 0.19
Nodes (5): InactivityGuardProps, RequireAuthProps, Header(), Layout(), LayoutProps

### Community 6 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 7 - "index.ts"
Cohesion: 0.12
Nodes (15): ApiError, BankAccount, CopCheck, Customer, Entitlement, LoanSnapshot, LoginRequest, LoginResponse (+7 more)

### Community 8 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, isolatedModules, lib, module, moduleDetection, moduleResolution, noEmit (+8 more)

### Community 9 - "steps"
Cohesion: 0.06
Nodes (35): name, runs-on, services, steps, DATABASE_URL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER (+27 more)

### Community 11 - "@vitejs/plugin-react"
Cohesion: 0.33
Nodes (4): vite@^6.0.1, @vitejs/plugin-react@^4.3.4, vite, @vitejs/plugin-react

### Community 12 - "scripts"
Cohesion: 0.33
Nodes (6): scripts, build, dev, lint, preview, test

### Community 13 - "tsconfig.json"
Cohesion: 0.33
Nodes (5): compilerOptions, baseUrl, paths, files, references

### Community 14 - "start.sh"
Cohesion: 0.48
Nodes (6): check_prerequisites(), DATABASE_URL, find_available_port(), native_path(), port_in_use(), start.sh script

### Community 15 - "ReviewApprovePage.tsx"
Cohesion: 0.15
Nodes (14): PURPOSE_OPTIONS, RiskFrictionPanel(), RiskFrictionPanelProps, ApprovalResponse, ApprovePaymentRequest, useApprovePayment(), RiskResponseRequest, RiskResponseResult (+6 more)

### Community 22 - "PaymentFlowProvider.tsx"
Cohesion: 0.15
Nodes (16): useAccountsOverview(), PaymentFlowContext, PaymentFlowContextValue, PaymentFlowState, RiskFriction, usePaymentFlow(), PaymentLimit, PreparedPayment (+8 more)

### Community 23 - "test_auth_integration.py"
Cohesion: 0.10
Nodes (9): test_biometric_proof_flow(), test_proof_with_invalid_session(), test_proof_with_wrong_passcode(), test_recovery_endpoint(), test_session_extend(), test_sign_in_and_proof_flow(), test_sign_in_endpoint(), test_sign_in_invalid_credentials() (+1 more)

### Community 24 - ".submit_proof"
Cohesion: 0.08
Nodes (6): AuthenticationError, SessionRepository, extend_session(), ExtendSessionResponse, SignOutResponse, SessionService

### Community 27 - "auth.py"
Cohesion: 0.09
Nodes (16): create_step_up_challenge(), sign_in(), sign_out(), start_recovery(), submit_proof(), verify_step_up(), ProofResponse, RecoveryRequest (+8 more)

### Community 32 - "payments.py"
Cohesion: 0.13
Nodes (9): PaymentApprovalRequest, PaymentApprovalResponse, PaymentDetailResponse, PaymentPrepareRequest, PaymentPrepareResponse, PaymentRiskResponseRequest, PaymentRiskResponseResponse, PaymentSubmitRequest (+1 more)

### Community 33 - "ciam_adapter.py"
Cohesion: 0.07
Nodes (4): CiamAdapter, get_ciam_adapter(), LiveCiamAdapter, StubCiamAdapter

### Community 34 - "get_rate_limiter"
Cohesion: 0.08
Nodes (21): hash_identifier(), ProofRequest, SignInRequest, AuthService, get_rate_limiter(), test_fr001_ac1_first_device_sign_in(), test_fr001_ac2_empty_fields_validation(), test_fr001_ac3_invalid_credentials_generic_error() (+13 more)

### Community 35 - "fraud_case_adapter.py"
Cohesion: 0.21
Nodes (5): FraudCaseAdapter, FraudCaseResponse, get_fraud_case_adapter(), LiveFraudCaseAdapter, StubFraudCaseAdapter

### Community 36 - "security.py"
Cohesion: 0.13
Nodes (7): create_jwt_token(), generate_hmac_digest(), generate_session_token(), hash_password(), hash_token(), verify_hmac_digest(), verify_password()

### Community 38 - "seed.py"
Cohesion: 0.11
Nodes (13): _seed_demo_payment(), _seed_payment_limits(), seed_database(), _seed_demo_accounts(), _seed_demo_customer(), _seed_demo_entitlements(), _seed_demo_loans(), _seed_demo_payees() (+5 more)

### Community 39 - "loan_adapter.py"
Cohesion: 0.14
Nodes (5): get_loan_adapter(), LiveLoanAdapter, LoanAdapter, LoanData, StubLoanAdapter

### Community 40 - "DeviceRepository"
Cohesion: 0.09
Nodes (3): Device, DeviceRepository, DeviceService

### Community 41 - "errors.py"
Cohesion: 0.11
Nodes (7): app_error_handler(), AppError, generic_exception_handler(), http_exception_handler(), RateLimitError, lifespan(), root()

### Community 42 - "profiles.py"
Cohesion: 0.18
Nodes (5): Session, ProfileService, test_get_profiles_for_customer(), test_set_active_profile(), test_set_active_profile_wrong_customer()

### Community 44 - "react"
Cohesion: 0.21
Nodes (10): dependencies, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0, PaymentStatus, usePaymentStatus(), PaymentOutcomePage(), mockNavigate (+2 more)

### Community 45 - "test_payments_acceptance.py"
Cohesion: 0.17
Nodes (5): test_approve_payment(), test_get_payment(), test_get_payment_receipt(), test_prepare_payment(), test_submit_payment()

### Community 46 - "AccountsPage.tsx"
Cohesion: 0.12
Nodes (15): ProfileSwitcher(), ProfileSwitcherProps, StatusBanner(), StatusBannerProps, AccountOverview, AccountsOverviewResponse, LoanOverview, ProfileEntitlement (+7 more)

### Community 47 - "core_banking_adapter.py"
Cohesion: 0.13
Nodes (5): AccountData, CoreBankingAdapter, get_core_banking_adapter(), LiveCoreBankingAdapter, StubCoreBankingAdapter

### Community 48 - "observability_adapter.py"
Cohesion: 0.10
Nodes (5): get_observability_adapter(), LiveObservabilityAdapter, ObservabilityAdapter, StubObservabilityAdapter, TelemetryExporter

### Community 49 - ".create_payee"
Cohesion: 0.11
Nodes (5): Payee, PayeeService, test_create_payee(), test_get_payees_for_customer(), test_update_payee_triggers_cop_check()

### Community 50 - "healthcheck"
Cohesion: 0.08
Nodes (23): PIP_TARGET, build, depends_on, environment, args, context, dockerfile, condition (+15 more)

### Community 52 - "backend"
Cohesion: 0.10
Nodes (21): build, env_file, environment, healthcheck, volumes, context, dockerfile, build (+13 more)

### Community 54 - "mandate_adapter.py"
Cohesion: 0.14
Nodes (5): EntitlementData, get_mandate_adapter(), LiveMandateAdapter, MandateAdapter, StubMandateAdapter

### Community 55 - "cop_adapter.py"
Cohesion: 0.15
Nodes (5): CopAdapter, CopResult, get_cop_adapter(), LiveCopAdapter, StubCopAdapter

### Community 56 - "get_accounts_overview"
Cohesion: 0.07
Nodes (10): run_parallel(), BankAccount, LoanSnapshot, Profile, ProfileAccountVisibility, LoanSnapshotRepository, ProfileAccountVisibilityRepository, AccountsOverviewService (+2 more)

### Community 58 - "payee_schemas.py"
Cohesion: 0.11
Nodes (21): acknowledge_cop(), create_payee(), get_current_customer_and_profile(), get_payee(), get_payees(), payee_to_out(), run_cop_check(), update_payee() (+13 more)

### Community 59 - "payee_directory_adapter.py"
Cohesion: 0.16
Nodes (4): get_payee_directory_adapter(), LivePayeeDirectoryAdapter, PayeeDirectoryAdapter, StubPayeeDirectoryAdapter

### Community 60 - "test_payees_acceptance.py"
Cohesion: 0.12
Nodes (7): test_acknowledge_cop(), test_create_payee(), test_get_payee_by_id(), test_get_payees(), test_get_payees_requires_auth(), test_run_cop_check(), test_update_payee()

### Community 61 - "uuid"
Cohesion: 0.10
Nodes (6): CopCheck, CopCheckRepository, CopService, test_acknowledge_cop_result(), test_run_cop_check_match(), test_run_cop_check_mismatch()

### Community 62 - "profiles.py"
Cohesion: 0.19
Nodes (6): AuthorizationError, ResourceNotFoundError, get_current_customer_id(), get_profiles(), get_session_id(), set_active_profile()

### Community 65 - "ProofPage.tsx"
Cohesion: 0.15
Nodes (11): StepUpChallenge, ProofLocationState, ProofPage(), ProofResponse, LocationState, SignInPage(), SignInResponse, mockNavigate (+3 more)

### Community 66 - "test_accounts_acceptance.py"
Cohesion: 0.20
Nodes (4): test_accounts_have_required_fields(), test_get_accounts_overview(), test_get_accounts_overview_requires_auth(), test_loans_have_required_fields()

### Community 67 - "payments_hub_adapter.py"
Cohesion: 0.18
Nodes (5): get_payments_hub_adapter(), LivePaymentsHubAdapter, PaymentsHubAdapter, PaymentSubmissionResponse, StubPaymentsHubAdapter

### Community 68 - "test_profiles_acceptance.py"
Cohesion: 0.25
Nodes (3): test_get_profiles_requires_auth(), test_get_profiles_returns_list(), test_set_active_profile()

### Community 69 - "EntitlementService"
Cohesion: 0.24
Nodes (3): EntitlementService, test_check_capability_without_entitlement_fail_safe(), test_require_capability_raises_on_missing()

### Community 71 - "notifications.py"
Cohesion: 0.16
Nodes (7): get_current_customer_id(), get_service_status(), list_notifications(), NotificationListResponse, NotificationResponse, ServiceStatusListResponse, ServiceStatusResponse

### Community 72 - "payment_service.py"
Cohesion: 0.19
Nodes (3): AuditEventRepository, AuditService, test_record_payment_event()

### Community 73 - "ValidationError"
Cohesion: 0.14
Nodes (3): ValidationError, EntitlementRepository, PaymentValidator

### Community 74 - "AdapterBase"
Cohesion: 0.11
Nodes (7): get_payment_orchestration_adapter(), LivePaymentOrchestrationAdapter, PaymentOrchestrationAdapter, PaymentOrchestrationResponse, StubPaymentOrchestrationAdapter, AdapterBase, CircuitState

### Community 75 - "payment_service.py"
Cohesion: 0.13
Nodes (5): PaymentOrder, PaymentLimitCheckRepository, StatusNormalizer, StatusRecorder, SubmissionService

### Community 76 - "get_db"
Cohesion: 0.28
Nodes (3): get_db(), health_check(), readiness_check()

### Community 77 - "payments.py"
Cohesion: 0.17
Nodes (11): get_correlation_id(), approve_payment(), get_current_customer_id(), get_current_device_id(), get_current_profile_id(), get_payment(), get_payment_receipt(), prepare_payment() (+3 more)

### Community 79 - "support_routing_adapter.py"
Cohesion: 0.18
Nodes (5): get_support_routing_adapter(), LiveSupportRoutingAdapter, StubSupportRoutingAdapter, SupportRoutingAdapter, SupportRoutingResponse

### Community 80 - "notification_service.py"
Cohesion: 0.16
Nodes (4): NotificationDeliveryAttemptRepository, NotificationService, test_create_payment_notification(), test_get_customer_notifications()

### Community 84 - "PaymentService"
Cohesion: 0.11
Nodes (5): PaymentOrderRepository, PaymentService, test_approve_payment_updates_status(), test_prepare_payment_creates_order(), test_submit_payment_updates_status()

### Community 85 - "errors.py"
Cohesion: 0.15
Nodes (8): decode_jwt_token(), get_accounts_overview(), get_current_customer_and_profile(), AccountsOverviewResponse, BankAccountOut, Config, LoanSnapshotOut, Config

### Community 86 - "ServiceStatusNotice"
Cohesion: 0.12
Nodes (5): NotificationDeliveryAttempt, ScamClaim, ServiceStatusNotice, ServiceStatusNoticeRepository, ServiceStatusService

### Community 87 - "fraud_decision_adapter.py"
Cohesion: 0.18
Nodes (5): FraudDecisionAdapter, FraudDecisionResponse, get_fraud_decision_adapter(), LiveFraudDecisionAdapter, StubFraudDecisionAdapter

### Community 88 - "AddPayeePage.tsx"
Cohesion: 0.23
Nodes (10): CopOutcomePanel(), CopOutcomePanelProps, CreatePayeeRequest, CreatePayeeResponse, useCreatePayee(), CopCheckOut, PayeeListResponse, PayeeOut (+2 more)

### Community 91 - "notification_adapter.py"
Cohesion: 0.18
Nodes (5): get_notification_adapter(), LiveNotificationAdapter, NotificationAdapter, NotificationDispatchResponse, StubNotificationAdapter

### Community 95 - "devDependencies"
Cohesion: 0.14
Nodes (14): devDependencies, autoprefixer@^10.4.20, eslint@^9.15.0, @testing-library/react@^16.1.0, @testing-library/user-event@^14.6.13, @types/react@^18.3.12, typescript@~5.6.2, vitest@^2.1.5 (+6 more)

### Community 96 - "FraudService"
Cohesion: 0.13
Nodes (5): RiskAssessment, RiskAssessmentRepository, FraudService, test_assess_payment_creates_risk_assessment(), test_high_amount_triggers_warning()

### Community 97 - "eslint.config.js"
Cohesion: 0.18
Nodes (10): @eslint/js@^9.15.0, eslint-plugin-react-hooks@^5.0.0, eslint-plugin-react-refresh@^0.4.14, globals@^15.12.0, typescript-eslint@^8.15.0, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh (+2 more)

### Community 98 - "App.tsx"
Cohesion: 0.15
Nodes (12): App(), usePayees(), PaymentFlowProvider(), CreateScamClaimRequest, ScamClaim, useCreateScamClaim(), PayAndTransferPage(), LocationState (+4 more)

### Community 100 - "Base"
Cohesion: 0.10
Nodes (7): Base, DuplicatePaymentLink, PaymentLimit, PaymentLimitCheck, ScaApproval, DuplicatePaymentLinkRepository, ScaApprovalRepository

### Community 101 - "sqlalchemy"
Cohesion: 0.10
Nodes (4): run_migrations_offline(), run_migrations_online(), upgrade(), AuthAttempt

### Community 104 - "test_smoke.py"
Cohesion: 0.22
Nodes (3): test_database_models_load(), test_health_check(), test_readiness_check()

### Community 107 - "profile_schemas.py"
Cohesion: 0.21
Nodes (7): EntitlementOut, Config, ProfileListResponse, ProfileOut, Config, SetActiveProfileRequest, SetActiveProfileResponse

### Community 120 - "support.py"
Cohesion: 0.09
Nodes (7): ScamClaimRepository, create_scam_claim(), get_current_customer_id(), get_scam_claim(), ScamClaimCreateRequest, ScamClaimResponse, ScamClaimService

## Knowledge Gaps
- **2 isolated node(s):** `DATABASE_URL`, `lbg-ftr-demo-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 907 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **53 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `AdapterBase` connect `AdapterBase` to `fraud_case_adapter.py`, `payments_hub_adapter.py`, `loan_adapter.py`, `payee_directory_adapter.py`, `core_banking_adapter.py`, `observability_adapter.py`, `support_routing_adapter.py`, `cop_adapter.py`, `mandate_adapter.py`, `fraud_decision_adapter.py`, `adapters.py`, `notification_adapter.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `DATABASE_URL`, `lbg-ftr-demo-backend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Sample Bank Mobile Payments MVP` be split into smaller, more focused modules?**
  _Cohesion score 0.041666666666666664 - nodes in this community are weakly interconnected._
- **Why does `get_rate_limiter()` connect `get_rate_limiter` to `ciam_adapter.py`, `LoginRateLimiter`, `AuthAttemptRepository`, `test_auth_integration.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Should `package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.13333333333333333 - nodes in this community are weakly interconnected._
- **Why does `CircuitBreaker` connect `adapters.py` to `AdapterBase`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **Should `test_pipeline_migration_parity.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11827956989247312 - nodes in this community are weakly interconnected._