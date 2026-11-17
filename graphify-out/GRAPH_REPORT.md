# Graph Report - lbg-ftr-demo-repo  (2026-11-17)

## Corpus Check
- 199 files · ~145,728 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 30 file(s) not represented in the graph (top: .css 13, (none) 7, .db 3)

## Summary
- 1994 nodes · 5058 edges · 135 communities (65 shown, 70 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 432 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `341e2e54`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LBG Clear Path
- ActionService
- database
- deps.py
- CaseTransitionRequest
- test_case_acceptance.py
- .utcnow
- auth-context.tsx
- LBG Clear Path - Backend
- RestrictedDataScreen
- test_smoke.py
- @carbon/react
- lbg-clear-path-backend
- .current_expected_by
- LBG Clear Path - Frontend
- compilerOptions
- AuthRepository
- package.json
- TASK-3 Backend Handoff: Intake and Case Creation
- customer_action_requested
- compilerOptions
- Session
- scripts
- datetime
- notifications.py
- host-config.ts
- ManagementApiAdapter
- communication_service.py
- Clock
- CircuitBreaker
- get_lifeline
- TASK-8 Handoff: Cross-Channel Continuity (FR-013, FR-015)
- main.py
- backend
- BaseModel
- list_colleague_cases
- api.ts
- CommunicationRepository
- communication_service.py
- TASK-4 Handoff: Backend Feature B2 - Case Summary and Notifications
- .create_case
- with
- test_action_service.py
- @carbon/react
- FastAPI
- test_pipeline_migration_parity.py
- .refresh_if_pending
- event_to_update_type
- Settings
- Key Files Modified/Created
- test_return_visit.py
- auth_service.py
- .allowed_successors
- event_bus.py
- Adapter
- incident_ingest_job.py
- utils.ts
- api-client.ts
- StatusService
- ContinuityRefreshJob
- get_status_service
- continuity_allow_list.yaml
- TASK-6 Handoff: Service Status and Lifeline
- withdrawn
- cases.py
- TASK-7 Handoff: Owner and Expected-By Management
- Session
- lifeline.tsx
- TASK-10: Backend Feature B8 - Protected Actions with SCA
- HistoryService
- routers/auth.py
- .transition
- AdapterHealth
- fallback_guidance
- test_continuity_service.py
- AuditService
- test_every_active_case_shows_ownership
- test_ownership_text_is_customer_understandable
- test_expected_by_date_shown_when_valid_commitment_exists
- test_stale_date_replaced_with_explanatory_text
- test_expected_by_revisions_recorded_in_history
- .record
- test_multiple_owner_changes_tracked_correctly
- test_multiple_expected_by_revisions_tracked_correctly
- test_lifecycle.py
- start.sh
- LifecycleGraph
- ConfigRepository
- .report_outcome
- UUID
- @playwright/test
- typing
- TASK-5 Handoff: Lifecycle States (FR-004, FR-021)
- .build
- ActionRepository
- docker-entrypoint.sh
- stop.sh

## God Nodes (most connected - your core abstractions)
1. `Clock` - 81 edges
2. `Case` - 80 edges
3. `CaseRepository` - 69 edges
4. `HistoryRepository` - 66 edges
5. `AuditService` - 63 edges
6. `AuditRepository` - 60 edges
7. `CaseOwnership` - 59 edges
8. `ExpectedByCommitment` - 58 edges
9. `OwnershipRepository` - 58 edges
10. `ContinuityService` - 49 edges

## Surprising Connections (you probably didn't know these)
- `Acceptance Criteria Verified` --references--> `LifecycleGraph`  [INFERRED]
  .handoff/TASK-5.md → backend/app/core/lifecycle_graph.py
- `Backend Flow` --references--> `LifecycleGraph`  [INFERRED]
  .handoff/TASK-5.md → backend/app/core/lifecycle_graph.py
- `Event Bus Integration` --references--> `CorrespondenceAdapter`  [INFERRED]
  .handoff/TASK-4.md → backend/app/adapters/correspondence_adapter.py
- `Case List and Detail` --references--> `CaseSummary`  [INFERRED]
  .handoff/TASK-4.md → backend/app/schemas/case.py
- `Case List and Detail` --references--> `CaseDetail`  [INFERRED]
  .handoff/TASK-4.md → backend/app/schemas/case.py

## Import Cycles
- None detected.

## Communities (135 total, 70 thin omitted)

### Community 0 - "LBG Clear Path"
Cohesion: 0.08
Nodes (25): API Documentation, Architecture, Backend (backend/dev.env), Backend Tests, Database Issues, Default Credentials, Development Workflow, Docker Build Issues (+17 more)

### Community 1 - "ActionService"
Cohesion: 0.18
Nodes (5): ActionService, test_report_outcome_action_not_found(), test_report_outcome_idempotent(), test_start_and_complete_protected_action_failed(), test_start_and_complete_protected_action_success()

### Community 2 - "database"
Cohesion: 0.07
Nodes (29): PIP_TARGET, build, depends_on, environment, args, context, dockerfile, condition (+21 more)

### Community 3 - "deps.py"
Cohesion: 0.09
Nodes (5): UnitOfWork, get_principal(), get_uow(), Principal, require_scope()

### Community 4 - "CaseTransitionRequest"
Cohesion: 0.17
Nodes (8): CaseTransitionRequest, test_transition_case_success(), test_transition_close_without_outcome_422(), test_transition_invalid_transition_422(), test_transition_not_found_404(), test_transition_restricted_data_422(), test_transition_same_state_422(), `app/schemas/case.py`

### Community 5 - "test_case_acceptance.py"
Cohesion: 0.10
Nodes (9): test_get_cases_by_reference_requires_authentication(), test_get_cases_by_reference_returns_404_for_nonexistent(), test_get_cases_by_reference_returns_404_for_other_customer(), test_get_cases_by_reference_returns_case_detail(), test_post_cases_creates_new_case(), test_post_cases_rejects_restricted_data(), test_post_cases_requires_authentication(), test_post_cases_returns_not_eligible_for_ineligible_issue() (+1 more)

### Community 6 - ".utcnow"
Cohesion: 0.05
Nodes (20): hash_password(), create_app(), KillSwitchSetting, OwnerTeamMapping, seed_data(), test_ownership_change_recorded_in_history(), auth_client(), colleague_client() (+12 more)

### Community 7 - "auth-context.tsx"
Cohesion: 0.14
Nodes (19): AppRouter(), RequireAuth(), RequireAuthProps, AppLayout(), AppLayoutProps, AuthContext, AuthContextType, AuthProvider() (+11 more)

### Community 8 - "LBG Clear Path - Backend"
Cohesion: 0.17
Nodes (11): API Endpoints, Authentication (`/api/v1/auth`), Default Credentials, Environment Variables, Health, LBG Clear Path - Backend, Run, Setup (+3 more)

### Community 10 - "test_smoke.py"
Cohesion: 0.29
Nodes (3): test_health_check(), test_health_ready(), test_login_smoke()

### Community 12 - "@carbon/react"
Cohesion: 0.27
Nodes (10): FallbackGuidance(), FallbackGuidanceProps, ProtectedStepPanel(), ProtectedStepPanelProps, ScaPrompt(), ScaPromptProps, ProtectedActionPage(), ProtectedAction (+2 more)

### Community 22 - "LBG Clear Path - Frontend"
Cohesion: 0.07
Nodes (26): API Integration, Auth Flow, Build, Carbon Design System, Configuration, Contributing, Deployment, Development (+18 more)

### Community 23 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 25 - "package.json"
Cohesion: 0.05
Nodes (59): dependencies, @carbon/icons-react@^11.47.0, @carbon/react@^1.64.0, @carbon/styles@^1.64.0, clsx@^2.1.1, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0 (+51 more)

### Community 26 - "TASK-3 Backend Handoff: Intake and Case Creation"
Cohesion: 0.12
Nodes (16): Backend Flow, Case Creation Flow, Colleague Account, Configuration, Customer Accounts, Eligibility Rules, Endpoints Implemented, Environment Variables (+8 more)

### Community 27 - "customer_action_requested"
Cohesion: 0.05
Nodes (36): approved_wording_set, body_text, deep_link_target, notification_type, safe_preview_text, subject_text, approved_wording_set, body_text (+28 more)

### Community 28 - "compilerOptions"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include

### Community 29 - "Session"
Cohesion: 0.22
Nodes (4): test_transition_case_success(), test_transition_close_without_outcome(), test_transition_invalid_transition(), test_transition_same_state()

### Community 30 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, e2e, lint, preview, test

### Community 31 - "datetime"
Cohesion: 0.07
Nodes (10): run_migrations_offline(), run_migrations_online(), upgrade(), Base, UserAccount, CaseLifecycleTransition, AgentExecutionRecord, PolicyDecision (+2 more)

### Community 32 - "notifications.py"
Cohesion: 0.14
Nodes (9): list_notifications(), NotificationItem, open_notification(), OpenNotificationRequest, OpenNotificationResponse, Page, Case List and Detail, Endpoints Implemented (+1 more)

### Community 33 - "host-config.ts"
Cohesion: 0.47
Nodes (5): Brand, getBrandLabel(), getCurrentBrand(), getHostConfig(), HostConfig

### Community 34 - "ManagementApiAdapter"
Cohesion: 0.25
Nodes (3): ManagementApiAdapter, action_service(), action_service()

### Community 36 - "Clock"
Cohesion: 0.08
Nodes (36): Clock, ContinuityContext, AuditRepository, CaseRepository, ContinuityRepository, HistoryRepository, OwnershipRepository, get_action_service() (+28 more)

### Community 43 - "TASK-8 Handoff: Cross-Channel Continuity (FR-013, FR-015)"
Cohesion: 0.10
Nodes (20): Acceptance Tests (tests/acceptance/test_continuity_acceptance.py), Architecture Notes, Background Job, ChannelHandoff, Colleague Scope, ContinuityContext, ContinuityPackageBuilder, ContinuityRefreshJob (+12 more)

### Community 45 - "backend"
Cohesion: 0.08
Nodes (28): BACKEND_HOST, build, env_file, environment, healthcheck, ports, volumes, x-preview-port (+20 more)

### Community 46 - "BaseModel"
Cohesion: 0.20
Nodes (6): HistoryRequest, LoginRequest, LoginResponse, MeResponse, RefreshResponse, UserSummary

### Community 47 - "list_colleague_cases"
Cohesion: 0.12
Nodes (4): CaseReferenceGenerator, new_id(), get_colleague_case(), list_colleague_cases()

### Community 48 - "api.ts"
Cohesion: 0.10
Nodes (36): ExpectedByBlock(), ExpectedByBlockProps, OwnerBlock(), OwnerBlockProps, StatusChip(), StatusChipProps, NotificationList(), NotificationListProps (+28 more)

### Community 49 - "CommunicationRepository"
Cohesion: 0.11
Nodes (9): CommunicationRecord, NotificationRecord, CommunicationRepository, test_get_notifications_for_customer(), test_notifications_scoped_to_customer(), test_open_notification_with_expired_token_fails(), test_open_notification_with_unknown_token(), test_open_notification_with_valid_token() (+1 more)

### Community 50 - "communication_service.py"
Cohesion: 0.14
Nodes (6): CorrespondenceAdapter, handle_case_event(), CommunicationService, NotificationDispatcher, TestCommunicationService, Services

### Community 51 - "TASK-4 Handoff: Backend Feature B2 - Case Summary and Notifications"
Cohesion: 0.13
Nodes (14): Acceptance Criteria Status, Acceptance Tests, CaseSummary (in Page items), Event Bus Integration, Integration Tests, NotificationItem (in Page items), Page wrapper (generic), Response Shapes (+6 more)

### Community 53 - ".create_case"
Cohesion: 0.08
Nodes (9): CaseCreateRequest, PolicyResult, test_create_case_persists_all_components(), test_create_case_returns_not_eligible_for_ineligible_issue_type(), test_create_case_surfaces_existing_open_case(), test_get_case_retrieves_case_with_projections(), test_create_case_creates_new_case_successfully(), test_create_case_returns_not_eligible_when_policy_denies() (+1 more)

### Community 54 - "with"
Cohesion: 0.09
Nodes (25): defaults, runs-on, steps, run, defaults, runs-on, steps, jobs (+17 more)

### Community 55 - "test_action_service.py"
Cohesion: 0.17
Nodes (8): action_service(), mock_action_repo(), mock_audit_service(), mock_case_repo(), mock_clock(), mock_history_repo(), mock_identity_adapter(), mock_management_api_adapter()

### Community 56 - "@carbon/react"
Cohesion: 0.10
Nodes (14): @testing-library/react@^16.1.0, vitest@^2.1.0, ChannelOption, HandoffChooser(), HandoffChooserProps, SharedFieldsPanel(), SharedFieldsPanelProps, ContinueChannelPage() (+6 more)

### Community 59 - "test_pipeline_migration_parity.py"
Cohesion: 0.11
Nodes (18): _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key(), _has_alembic_version(), _last_name(), _mapped_columns() (+10 more)

### Community 61 - "event_to_update_type"
Cohesion: 0.29
Nodes (6): event_to_update_type, CaseStatusChanged, ExpectedByChanged, IncidentDeclared, OwnerChanged, ProtectedActionRequested

### Community 64 - "Key Files Modified/Created"
Cohesion: 0.22
Nodes (7): Adapters, Configuration, Key Files Modified/Created, Main App, Routers, Schemas, Seed

### Community 65 - "test_return_visit.py"
Cohesion: 0.05
Nodes (28): auth_client_colleague(), client(), db_session(), _fresh_schema(), continuity_service(), mock_audit_service(), mock_repos(), test_restore_return_visit_audit_called_with_correlation_id() (+20 more)

### Community 66 - "auth_service.py"
Cohesion: 0.21
Nodes (4): create_jwt(), decode_jwt(), hash_token(), verify_password()

### Community 72 - "incident_ingest_job.py"
Cohesion: 0.15
Nodes (4): IncidentAdapter, get_job_instance(), IncidentIngestJob, Background Job

### Community 73 - "utils.ts"
Cohesion: 0.21
Nodes (12): IncidentCard(), IncidentCardProps, cn(), formatCurrency(), formatDateTime(), formatRelativeTime(), getRiskBadgeColor(), getStatusBadgeColor() (+4 more)

### Community 75 - "api-client.ts"
Cohesion: 0.21
Nodes (8): apiClient, ApiError, request(), CaseHistoryPage(), ReportIssuePage(), mockNavigate, HistoryEvent, Page

### Community 76 - "StatusService"
Cohesion: 0.05
Nodes (29): LifelineGuidance, ServiceIncident, ServiceStatusPublication, record_fallback_exposure(), StatusService, test_app_routes_users_to_status_when_case_retrieval_fails(), test_case_service_outage_does_not_prevent_status_and_lifeline_access(), test_customers_can_access_service_status_during_disruption() (+21 more)

### Community 80 - "continuity_allow_list.yaml"
Cohesion: 0.50
Nodes (3): colleague_payload, llm_safe_payload, structured_context

### Community 83 - "TASK-6 Handoff: Service Status and Lifeline"
Cohesion: 0.13
Nodes (14): Architecture Notes, Configuration, Files Created, GET /api/v1/lifeline, GET /api/v1/status, Implemented Endpoints, Integration with Frontend, Lifeline Guidance (2) (+6 more)

### Community 84 - "withdrawn"
Cohesion: 0.12
Nodes (15): committed, description, revised, description, under_review, default, description, withdrawn (+7 more)

### Community 85 - "cases.py"
Cohesion: 0.06
Nodes (19): IdentityAdapter, ConcurrencyError, DependencyUnavailable, DomainError, NotFoundError, get_case(), get_continuity_package(), list_cases() (+11 more)

### Community 86 - "TASK-7 Handoff: Owner and Expected-By Management"
Cohesion: 0.13
Nodes (14): Acceptance Criteria Coverage, Case Detail Changes, Continuity Refresh, Expected-By Explanatory Text, Files Created, History Events, Implemented Endpoints, Notes for UI Implementation (+6 more)

### Community 87 - "Session"
Cohesion: 0.11
Nodes (13): change_owner(), create_case(), get_history_service(), HandoffRequest, ProtectedActionRequest, record_handoff(), report_sca_outcome(), restore_return_visit() (+5 more)

### Community 88 - "lifeline.tsx"
Cohesion: 0.17
Nodes (12): CacheAgeNote(), CacheAgeNoteProps, LifelineGuidanceList(), LifelineGuidanceListProps, LifelineItem, formatCacheAge(), getCacheAgeSeconds(), getLifelineCache() (+4 more)

### Community 89 - "TASK-10: Backend Feature B8 - Protected Actions with SCA"
Cohesion: 0.14
Nodes (13): API Endpoints, Dependencies, Fallback Guidance Catalogue, GET /api/v1/cases/{case_reference}/actions/{action_id}, GET /api/v1/cases/{case_reference}/history, Implementation Summary, POST /api/v1/cases/{case_reference}/actions, POST /api/v1/cases/{case_reference}/actions/{action_id}/sca-outcome (+5 more)

### Community 93 - "routers/auth.py"
Cohesion: 0.28
Nodes (8): AuthorizationError, get_db(), get_auth_service(), get_me(), login(), logout(), refresh(), AuthService

### Community 98 - "fallback_guidance"
Cohesion: 0.20
Nodes (9): fallback_guidance, card_freeze_card, card_replace_card, card_stop_card, card_update_limit, money_direct_debit, money_payment, money_standing_order (+1 more)

### Community 99 - "test_continuity_service.py"
Cohesion: 0.10
Nodes (13): continuity_service(), mock_audit_repo(), mock_audit_service(), mock_case_repo(), mock_clock(), mock_continuity_repo(), mock_history_repo(), mock_ownership_repo() (+5 more)

### Community 102 - "AuditService"
Cohesion: 0.09
Nodes (18): CustomerCaseAdapter, ValidationError, CaseEvent, Case, CaseAnchorLink, CaseStatusProjection, IssueEligibilityRule, CaseOwnership (+10 more)

### Community 116 - "start.sh"
Cohesion: 0.43
Nodes (7): check_prerequisites(), DATABASE_URL, find_available_port(), native_path(), port_in_use(), portable_sed(), start.sh script

### Community 118 - "LifecycleGraph"
Cohesion: 0.15
Nodes (9): LifecycleGraph, test_lifecycle_graph_loads_transitions(), test_lifecycle_graph_allows_valid_transition(), test_lifecycle_graph_caching(), test_lifecycle_graph_rejects_invalid_transition(), `app/core/lifecycle_graph.py`, `app/routers/cases.py`, `app/services/case_service.py` (+1 more)

### Community 119 - "ConfigRepository"
Cohesion: 0.10
Nodes (8): ConfigRepository, PolicyService, case_service(), case_service(), case_service(), case_service(), mock_repos(), mock_services()

### Community 121 - ".report_outcome"
Cohesion: 0.12
Nodes (7): test_get_action_status_endpoint(), test_get_history_shows_complete_timeline(), test_history_records_protected_action_events(), test_protected_action_sca_abandoned_shows_fallback(), test_protected_action_sca_failure_shows_fallback(), test_start_protected_action_case_not_found(), test_start_protected_action_case_not_found()

### Community 122 - "UUID"
Cohesion: 0.07
Nodes (22): ProtectedActionRequest, ExpectedByRevisionRequest, OwnerChangeRequest, test_report_outcome_different_outcome_after_finalized(), test_report_outcome_failed(), test_report_outcome_idempotent(), test_report_outcome_success(), test_start_protected_action_success() (+14 more)

### Community 131 - "TASK-5 Handoff: Lifecycle States (FR-004, FR-021)"
Cohesion: 0.25
Nodes (7): Acceptance Criteria Verified, Backend Flow, Implemented Endpoints, POST /api/v1/cases/{case_reference}/transitions, Seed Data, TASK-5 Handoff: Lifecycle States (FR-004, FR-021), Testing

### Community 136 - ".build"
Cohesion: 0.10
Nodes (7): ChannelHandoff, ContinuityPackageBuilder, test_get_package_case_not_found(), test_list_colleague_cases(), test_package_builder_build(), test_package_builder_colleague_view(), test_record_handoff()

### Community 142 - "ActionRepository"
Cohesion: 0.13
Nodes (5): ActionRepository, get_protected_action(), test_protected_action_requires_sca_success(), test_system_records_sca_invocation_and_outcome(), Key Implementation Details

## Knowledge Gaps
- **2 isolated node(s):** `DATABASE_URL`, `lbg-clear-path-backend`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 965 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **70 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clock` connect `Clock` to `notifications.py`, `test_return_visit.py`, `auth_service.py`, `communication_service.py`, `ManagementApiAdapter`, `.utcnow`, `AuditService`, `Adapter`, `.build`, `main.py`, `list_colleague_cases`, `CommunicationRepository`, `communication_service.py`, `cases.py`, `ConfigRepository`, `UUID`, `datetime`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `CaseRepository` (e.g. with `CaseService` and `case_service()`) actually correct?**
  _`CaseRepository` has 3 INFERRED edges - model-reasoned connections that need verification._
- **What connects `DATABASE_URL`, `lbg-clear-path-backend` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `LBG Clear Path` be split into smaller, more focused modules?**
  _Cohesion score 0.07692307692307693 - nodes in this community are weakly interconnected._
- **Why does `Case` connect `AuditService` to `ActionService`, `test_continuity_service.py`, `Clock`, `.find_open_by_issue_type`, `.utcnow`, `.build`, `ActionRepository`, `.create_case`, `cases.py`, `test_action_service.py`, `.report_outcome`, `UUID`, `.refresh_if_pending`, `.transition`, `datetime`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **Should `database` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Why does `Base` connect `datetime` to `Clock`, `AuditService`, `.utcnow`, `.build`, `StatusService`, `.record`, `CommunicationRepository`, `AuthRepository`, `UUID`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._