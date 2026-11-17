# Graph Report - lbg-ftr-demo-repo  (2026-11-17)

## Corpus Check
- 199 files · ~58,533 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 18 file(s) not represented in the graph (top: (none) 8, .env 2, .tsbuildinfo 2)

## Summary
- 1354 nodes · 2881 edges · 88 communities (49 shown, 39 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 226 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `341e2e54`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Clear Path MVP
- evidence_router.py
- Clock
- test_pipeline_migration_parity.py
- ResolveSessionPage.tsx
- layer.py
- PolicyEngine
- UnitOfWork
- api-client.ts
- ScaVerifier
- session_auth.py
- clear-path-backend
- compilerOptions
- audit/repository.py
- devDependencies
- ColleagueCasePage.tsx
- ResolvePage.tsx
- compilerOptions
- ScopedTokenIssuer
- Clear Path Frontend
- package.json
- IntakeTriageAgent
- App.tsx
- resolve_router.py
- orchestrator.py
- test_my_cases_api.py
- Backend Flows
- AdapterRequest
- colleague/cases_router.py
- AppUser
- definitions.py
- .execute
- dataclasses
- eslint.config.js
- send_message
- utils.ts
- main.py
- deps.py
- CaseConfirmationPage.tsx
- Task 4 Handoff: Tool Layer, Adapters, Evidence Service, Colleague API
- AuthService
- typing
- scripts
- test_colleague_api.py
- environment
- @playwright/test
- @vitejs/plugin-react
- RedactionBoundary
- steps
- Clear Path Backend
- OrchestrationRepository
- GuardrailSupervisorAgent
- database
- auth-context.tsx
- auth_router.py
- correlation.py
- middleware/errors.py
- LoginRateLimiter
- start.sh
- .utc_now
- dataclasses
- docker-entrypoint.sh
- stop.sh

## God Nodes (most connected - your core abstractions)
1. `Clock` - 62 edges
2. `AppUser` - 46 edges
3. `AdapterRequest` - 38 edges
4. `GatewayClient` - 35 edges
5. `Base` - 32 edges
6. `Orchestrator` - 28 edges
7. `AdapterResult` - 27 edges
8. `AuthService` - 22 edges
9. `EventRepository` - 22 edges
10. `CaseService` - 21 edges

## Surprising Connections (you probably didn't know these)
- `Resolve Endpoints` --references--> `ResolveTurn`  [INFERRED]
  .handoff/TASK-3.md → backend/app/services/orchestrator/schemas.py
- `ToolLayer` --uses--> `ScopedTokenIssuer`  [INFERRED]
  backend/app/tools/layer.py → backend/app/tools/token_issuer.py
- `Orchestrator` --uses--> `IntakeTriageAgent`  [INFERRED]
  backend/app/services/orchestrator/orchestrator.py → backend/app/agents/intake_triage.py
- `create_case()` --uses--> `CreateCaseRequest`  [INFERRED]
  backend/app/api/my_cases/cases_router.py → backend/app/services/case/schemas.py
- `Orchestrator` --uses--> `CreateCaseRequest`  [INFERRED]
  backend/app/services/orchestrator/orchestrator.py → backend/app/services/case/schemas.py

## Import Cycles
- None detected.

## Communities (88 total, 39 thin omitted)

### Community 0 - "Clear Path MVP"
Cohesion: 0.06
Nodes (30): API Endpoints, Architecture, Authentication, Backend, Backend (.env), Backend Modules, Backend Tests, Clear Path MVP (+22 more)

### Community 1 - "evidence_router.py"
Cohesion: 0.23
Nodes (4): confirm_action(), ConfirmationRequest, EvidenceView, upload_evidence()

### Community 2 - "Clock"
Cohesion: 0.06
Nodes (32): run_migrations_online(), upgrade(), downgrade(), upgrade(), PasswordHasher, Settings, Clock, IdGenerator (+24 more)

### Community 3 - "test_pipeline_migration_parity.py"
Cohesion: 0.10
Nodes (19): test_import_boundaries(), _alembic(), _annotation_kind(), _column_kind(), _env_py_text(), _foreign_key(), _has_alembic_version(), _last_name() (+11 more)

### Community 4 - "ResolveSessionPage.tsx"
Cohesion: 0.09
Nodes (21): AssistantFindingsCard(), AssistantFindingsCardProps, Finding, EvidenceFile, EvidenceUpload(), EvidenceUploadProps, ProposalCard(), ProposalCardProps (+13 more)

### Community 5 - "layer.py"
Cohesion: 0.18
Nodes (5): RequestContext, ToolLayer, ToolRequest, ToolResult, test_tool_layer_invoke()

### Community 6 - "PolicyEngine"
Cohesion: 0.18
Nodes (10): PolicyEngine, ActionControl, PolicyDecision, PolicyDecisionResponse, PolicyEvaluationRequest, ToolInvocationRequest, test_policy_engine_approve_l0_action(), test_policy_engine_deny_sca_required_not_authenticated() (+2 more)

### Community 8 - "api-client.ts"
Cohesion: 0.18
Nodes (11): LoginPage(), apiClient, ApiError, request(), RequestOptions, mockApiClient, mockApiClient, mockNavigate (+3 more)

### Community 22 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleResolution, noEmit (+11 more)

### Community 23 - "audit/repository.py"
Cohesion: 0.19
Nodes (7): AuditHasher, AuditRepository, AuditService, test_audit_hash_chain_integrity(), test_audit_repository_has_no_update_or_delete_methods(), test_audit_service_creates_entry_with_hash_chain(), test_audit_service_supports_different_actor_types()

### Community 24 - "devDependencies"
Cohesion: 0.11
Nodes (19): devDependencies, autoprefixer@^10.4.20, eslint@^9.15.0, jsdom@^25.0.1, postcss@^8.4.49, tailwindcss@^3.4.15, @testing-library/react@^16.0.1, @types/node@^22.10.1 (+11 more)

### Community 25 - "ColleagueCasePage.tsx"
Cohesion: 0.09
Nodes (28): ColleagueWorklist(), ColleagueWorklistProps, WorklistItem, EvidenceItem, EvidencePanel(), EvidencePanelProps, HandlingIndicators(), HandlingIndicatorsProps (+20 more)

### Community 26 - "ResolvePage.tsx"
Cohesion: 0.19
Nodes (11): AiDisclosure(), AiDisclosureProps, HumanPathButton(), HumanPathButtonProps, StatusContextCard(), StatusContextCardProps, Transaction, TransactionPicker() (+3 more)

### Community 27 - "compilerOptions"
Cohesion: 0.22
Nodes (8): compilerOptions, allowSyntheticDefaultImports, composite, module, moduleResolution, skipLibCheck, strict, include

### Community 28 - "ScopedTokenIssuer"
Cohesion: 0.16
Nodes (3): ScopedTokenIssuer, TokenHandle, test_token_issuer()

### Community 29 - "Clear Path Frontend"
Cohesion: 0.05
Nodes (37): API Client, API Connection Issues, API Integration, API Proxy, Authentication Flow, Browser DevTools, Build & Deploy, Build Errors (+29 more)

### Community 30 - "package.json"
Cohesion: 0.13
Nodes (14): @testing-library/jest-dom@^6.6.3, @testing-library/user-event@^14.5.2, @types/react@^18.3.12, @vitest/ui@^2.1.8, engines, node, name, private (+6 more)

### Community 35 - "IntakeTriageAgent"
Cohesion: 0.21
Nodes (3): AgentResult, BaseAgent, IntakeTriageAgent

### Community 36 - "App.tsx"
Cohesion: 0.19
Nodes (14): App(), ColleagueCasesPage(), DashboardPage(), RequireAuth(), RequireAuthProps, Header(), Layout(), LayoutProps (+6 more)

### Community 37 - "resolve_router.py"
Cohesion: 0.17
Nodes (15): create_case(), get_case(), list_cases(), CaseDetailResponse, CaseListItem, CaseListResponse, CaseResponse, CreateCaseRequest (+7 more)

### Community 38 - "orchestrator.py"
Cohesion: 0.19
Nodes (10): Orchestrator, HumanRequestResponse, ResolveSessionView, ResolveTurn, ResolveTurnEntry, SendMessageRequest, StartSessionRequest, test_orchestrator_handle_message() (+2 more)

### Community 39 - "test_my_cases_api.py"
Cohesion: 0.13
Nodes (7): test_get_case_detail(), test_get_cases_lists_cases(), test_get_resolve_session(), test_post_cases_creates_case(), test_post_human_request(), test_post_resolve_messages(), test_post_resolve_starts_session()

### Community 40 - "Backend Flows"
Cohesion: 0.20
Nodes (9): API Endpoints, Backend Flows, Case Creation (Out-of-Scope or Human Requested), Case Timeline, Cases Endpoints, Resolve Endpoints, Seed Data, Session Start → Intake Agent (+1 more)

### Community 45 - "AdapterRequest"
Cohesion: 0.05
Nodes (20): AdapterBase, AdapterRequest, AdapterResult, CardControlsAdapter, ContactSchedulingAdapter, DocumentAdapter, GatewayClient, GatewayResponse (+12 more)

### Community 46 - "colleague/cases_router.py"
Cohesion: 0.06
Nodes (22): create_colleague_case(), get_colleague_case(), get_evidence_content(), get_thread(), list_colleague_cases(), pickup_case(), post_colleague_reply(), request_evidence() (+14 more)

### Community 47 - "AppUser"
Cohesion: 0.22
Nodes (4): AppUser, AuthSession, LoginAttempt, AuthRepository

### Community 48 - "definitions.py"
Cohesion: 0.10
Nodes (23): DomainEventCreate, DomainEventView, EventOutboxView, AuditLogEntryCreate, AuditLogEntryView, NotificationRecordCreate, NotificationRecordView, CallbackScheduleResult (+15 more)

### Community 49 - ".execute"
Cohesion: 0.17
Nodes (3): AdapterExecutor, ExecutorResult, ToolExecutor

### Community 50 - "dataclasses"
Cohesion: 0.20
Nodes (3): CaseOwnerAgent, CustomerUpdateDraft, SummaryDraft

### Community 51 - "eslint.config.js"
Cohesion: 0.18
Nodes (10): @eslint/js@^9.15.0, eslint-plugin-react-hooks@^5.0.0, eslint-plugin-react-refresh@^0.4.14, globals@^15.12.0, typescript-eslint@^8.15.0, @eslint/js, eslint-plugin-react-hooks, eslint-plugin-react-refresh (+2 more)

### Community 52 - "send_message"
Cohesion: 0.19
Nodes (4): get_resolve_session(), request_human(), send_message(), start_resolve()

### Community 53 - "utils.ts"
Cohesion: 0.13
Nodes (9): dependencies, clsx@^2.1.1, react@^18.3.1, react-dom@^18.3.1, react-router-dom@^6.28.0, tailwind-merge@^2.5.4, clsx, react-dom (+1 more)

### Community 54 - "main.py"
Cohesion: 0.07
Nodes (17): get_dispatcher(), OutboxDispatcher, DomainEvent, EventOutbox, EventPublisher, EventRegistry, get_event_registry(), EventRepository (+9 more)

### Community 55 - "deps.py"
Cohesion: 0.24
Nodes (7): get_current_user(), AppError, AuthenticationError, AuthorizationError, NotFoundError, RateLimitError, ValidationError

### Community 56 - "CaseConfirmationPage.tsx"
Cohesion: 0.16
Nodes (16): CaseHero(), CaseHeroProps, CaseRow(), CaseRowProps, ChecklistCard(), ChecklistCardProps, MyCasesList(), MyCasesListProps (+8 more)

### Community 57 - "Task 4 Handoff: Tool Layer, Adapters, Evidence Service, Colleague API"
Cohesion: 0.17
Nodes (11): Adapters, Agents, API Endpoints, Backend Flows, Colleague View API, Evidence Service, My Cases API - Evidence, Notes (+3 more)

### Community 58 - "AuthService"
Cohesion: 0.19
Nodes (4): login(), logout(), AuthService, TokenService

### Community 60 - "scripts"
Cohesion: 0.29
Nodes (7): scripts, build, dev, lint, preview, test, type-check

### Community 61 - "test_colleague_api.py"
Cohesion: 0.20
Nodes (5): auth_client(), test_colleague_create_case(), test_colleague_list_cases(), test_colleague_login(), test_list_colleague_cases_requires_colleague_role()

### Community 62 - "environment"
Cohesion: 0.07
Nodes (33): BACKEND_HOST, build, driver, environment, expose, healthcheck, volumes, args (+25 more)

### Community 67 - "@vitejs/plugin-react"
Cohesion: 0.29
Nodes (4): vite@^6.0.1, @vitejs/plugin-react@^4.3.4, vite, @vitejs/plugin-react

### Community 68 - "RedactionBoundary"
Cohesion: 0.17
Nodes (6): RedactedContext, RedactionBoundary, test_redaction_clean_text(), test_redaction_detects_injection_pattern(), test_redaction_detects_pan(), test_redaction_detects_passcode_reference()

### Community 69 - "steps"
Cohesion: 0.07
Nodes (32): runs-on, services, steps, DATABASE_URL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER, RATE_LIMIT_ENABLED (+24 more)

### Community 70 - "Clear Path Backend"
Cohesion: 0.06
Nodes (30): API Documentation, API Endpoints, Architecture, Auth Type Safety, Authentication, Clear Path Backend, Code Style, Colleague View (+22 more)

### Community 73 - "database"
Cohesion: 0.07
Nodes (29): PIP_TARGET, build, depends_on, environment, args, context, dockerfile, condition (+21 more)

### Community 74 - "auth-context.tsx"
Cohesion: 0.36
Nodes (5): AuthContext, AuthContextType, LoginRequest, LoginResponse, User

### Community 75 - "auth_router.py"
Cohesion: 0.33
Nodes (5): get_me(), ResolveTurnMinimal, LoginRequest, LoginResponse, UserResponse

### Community 79 - "start.sh"
Cohesion: 0.48
Nodes (6): check_prerequisites(), DATABASE_URL, find_available_port(), native_path(), port_in_use(), start.sh script

### Community 82 - ".utc_now"
Cohesion: 0.09
Nodes (19): CaseRecord, CaseTimelineEvent, CaseDetailResponse, CaseListItem, CaseListResponse, CaseResponse, CreateCaseRequest, CaseService (+11 more)

## Knowledge Gaps
- **2 isolated node(s):** `clear-path-backend`, `DATABASE_URL`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 524 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Clock` connect `Clock` to `evidence_router.py`, `layer.py`, `orchestrator.py`, `PolicyEngine`, `AdapterRequest`, `LoginRateLimiter`, `colleague/cases_router.py`, `AppUser`, `.utc_now`, `main.py`, `audit/repository.py`, `AuthService`, `ScopedTokenIssuer`?**
  _High betweenness centrality (0.073) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `Clock` (e.g. with `AppUser` and `AuthSession`) actually correct?**
  _`Clock` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `clear-path-backend`, `DATABASE_URL` to the rest of the system?**
  _2 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Clear Path MVP` be split into smaller, more focused modules?**
  _Cohesion score 0.06451612903225806 - nodes in this community are weakly interconnected._
- **Why does `AppUser` connect `AppUser` to `evidence_router.py`, `Clock`, `resolve_router.py`, `auth_router.py`, `colleague/cases_router.py`, `send_message`, `deps.py`, `AuthService`, `test_colleague_api.py`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `AppUser` (e.g. with `get_me()` and `get_current_user()`) actually correct?**
  _`AppUser` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Clock` be split into smaller, more focused modules?**
  _Cohesion score 0.060404040404040404 - nodes in this community are weakly interconnected._