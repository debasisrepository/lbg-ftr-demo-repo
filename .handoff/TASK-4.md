# Task 4 Handoff: Tool Layer, Adapters, Evidence Service, Colleague API

## API Endpoints

All endpoints are mounted under `/api/v1` prefix.

### My Cases API - Evidence

**POST /api/v1/resolve/{session_id}/evidence**
- Request: multipart/form-data with file, evidence_type, display_label
- Response: `{ evidence: EvidenceView, turn: ResolveTurn }`
- Uploads evidence file with checksum-based deduplication

**POST /api/v1/resolve/{session_id}/confirmations**
- Request: `{ sca_reference: string }`
- Response: ResolveTurn with outcome or sca_challenge
- Confirms proposed action after SCA verification

### Colleague View API

**POST /api/v1/colleague/cases**
- Request: `{ origin_source: string, problem_statement: string }`
- Response: `{ case_id, case_ref, status, problem_statement }`
- Creates Case from colleague desktop

**GET /api/v1/colleague/cases**
- Query params: page (default 1), page_size (default 20, max 100)
- Response: `{ items: [ColleagueCaseListItem], total: number }`
- Lists colleague worklist with pagination

**GET /api/v1/colleague/cases/{case_id}**
- Response: HandoffPack with one-screen summary, handling indicators, route reason, arrival source
- Includes optional copilot_note (under 1.5s budget, failure does not block)

**GET /api/v1/colleague/cases/{case_id}/thread**
- Query params: page, page_size (max 200)
- Response: `{ entries: [TranscriptEntryResponse], total: number }`
- Paginated transcript with role labels and visibility scopes

**POST /api/v1/colleague/cases/{case_id}/thread/entries**
- Request: `{ content_text: string, visibility_scope: "customer_and_colleague" | "colleague_only" }`
- Response: TranscriptEntryResponse
- Posts colleague reply with visibility selector

**POST /api/v1/colleague/cases/{case_id}/evidence-requests**
- Request: `{ display_label: string, evidence_type?: string }`
- Response: `{ evidence_id, display_label, state: "requested" }`
- Requests additional evidence from customer

**POST /api/v1/colleague/cases/{case_id}/pickup**
- Request: `{ colleague_user_id: string }`
- Response: `{ case_id, case_ref, owner_colleague_display }`
- Assigns Case to colleague, records colleague_owner in case_assignment

**GET /api/v1/colleague/cases/{case_id}/evidence/{evidence_id}/content**
- Response: Evidence file content (stub in demo)
- Downloads evidence file

## Tool Layer

Eight bounded tools implemented:
- T1: `get_transactions` - Retrieve transactions (needs token)
- T2: `request_document` - Request document (needs token)
- T3: `schedule_callback` - Record callback preference (no adapter call)
- T4: `card_controls` - Freeze/unfreeze card (needs token + SCA)
- T5: `retry_payment` - Retry payment (needs token + SCA)
- T6: `create_case` - Create Case (no token)
- T7: `update_case` - Update Case (no token)
- T8: `route_to_queue` - Route to queue (needs token)

**ScopedTokenIssuer**
- Issues customer-scoped, short-lived (120s default) tokens
- Tokens stored in-process memory only
- `can_issue(customer_user_id)` - check if token can be issued
- `issue(customer_user_id, scope, ttl_s)` - issue token
- Returns TokenHandle with token_ref, scope_ref, expires_at

**ScaVerifier**
- Checks SCA reference against customer and proposal
- `verify(sca_reference, customer_user_id, proposal_id)` returns bool
- For demo: succeeds if reference non-empty
- In production: calls PartyAuthenticationAdapter

## Adapters

Seven main adapters plus PartyAuthenticationAdapter:
- A1: TransactionsAdapter - List transactions
- A2: DocumentAdapter - Request document
- A3: ContactSchedulingAdapter - Schedule callback (reserved, not called)
- A4: CardControlsAdapter - Card controls (freeze/unfreeze)
- A5: RoutingAdapter - Route case to queue
- A6: PaymentsAdapter - Retry payment
- A7: NotificationAdapter - Send notification
- PartyAuthenticationAdapter - SCA verification

**GatewayClient**
- Wraps HTTP calls to LBG API gateway
- Attaches correlation ID and customer-scoped token
- For demo: returns stub responses
- Normalizes gateway responses to AdapterResult (ok, payload, error_code)

## Evidence Service

**EvidenceService.record_evidence**
- request_only=True: creates requested evidence item
- request_only=False: stores file with checksum, checks for duplicates in same thread
- Returns EvidenceItem (new or existing)
- Checksum-based idempotency: same file in same thread returns existing item

## Agents

**CaseOwnerAgent** (case_owner_agent, max L1)
- `compose_summary(problem_statement, classification, route_reason, evidence_count)` - drafts hand-off summary (max 1500 chars)
- `draft_customer_update(case_ref, status, expected_by)` - drafts heartbeat update (max 400 chars)
- For demo: deterministic template (SummaryTemplate fallback)

**ColleagueCopilotAgent** (colleague_copilot_agent, max L0)
- `next_best_context(summary_text, classification, route_reason, vulnerability_flag)` - one-screen summary note (max 1000 chars)
- Runs under 1.5s budget, failure does not block handoff pack
- For demo: deterministic template

## Backend Flows

**Tool execution flow:**
1. Orchestrator requests tool with policy approval reference (decision_id)
2. ToolLayer checks approval, validates args, checks execution mode (shadow vs live)
3. If tool needs token: ScopedTokenIssuer.issue → token stored in memory
4. If tool needs SCA: ScaVerifier.verify (second line of defence)
5. Execute: call adapter (for A1-A7) or in-process (for T6-T7)
6. Write tool_invocation row with execution_mode, result, error_code
7. Return ToolResult

**Evidence upload flow:**
1. Customer uploads file via POST /api/v1/resolve/{session_id}/evidence
2. EvidenceService computes checksum (SHA-256)
3. Check for duplicate by checksum in same thread → return existing if found
4. Store file with storage_key (object store in production, stub in demo)
5. Create evidence_item row: state='received', checksum, file_size_bytes
6. Return EvidenceView + ResolveTurn

**Colleague pickup flow:**
1. Colleague calls POST /api/v1/colleague/cases/{case_id}/pickup
2. Check if already owned by another colleague → 409 Conflict
3. If owned by this colleague → return unchanged (idempotent)
4. Release existing colleague_owner assignment (is_current=False, released_at=now)
5. Create new colleague_owner assignment (is_current=True, assigned_at=now)
6. Update case.owner_colleague_display
7. Return Case with owner_colleague_display

## Seed Credentials

- Admin: admin@example.com / admin123 (customer, not colleague)
- Colleague: colleague@example.com / colleague123 (colleague role)

## Notes

- All colleague endpoints require is_colleague=True (403 otherwise)
- Evidence checksum uses SHA-256
- Tokens stored in-process memory only (not persisted)
- For demo: gateway responses are stubs, always succeed
- In production: GatewayClient uses pooled httpx.Client with TLS, mTLS, retry policy
- Copilot agent failure does not block handoff pack assembly (optional under 1.5s budget)
