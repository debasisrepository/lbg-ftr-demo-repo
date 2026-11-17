# TASK-3 Handoff: Backend Feature B1

## API Endpoints

### Resolve Endpoints
- `POST /api/v1/resolve` - Start resolve session
  - Request: `{ message_text, entry_context_type?, entry_context_ref?, status_context_shown? }`
  - Response: `ResolveTurn { session_id, thread_id, state, ai_disclosure, human_path_shown, new_entries[], case_ref?, case_id?, classification? }`
  
- `GET /api/v1/resolve/{session_id}` - Get session state
  - Response: `ResolveSessionView { session_id, thread_id, state, entries[], case_ref?, classification? }`
  
- `POST /api/v1/resolve/{session_id}/messages` - Send customer message
  - Request: `{ message_text }`
  - Response: `ResolveTurn` (same shape as start)
  
- `POST /api/v1/resolve/{session_id}/human-request` - Request human escalation
  - Response: `HumanRequestResponse { session_id, thread_id, case_ref, case_id, owner_team_display?, expected_by_at? }`

### Cases Endpoints
- `POST /api/v1/cases` - Create case from app entry
  - Request: `{ origin_source, problem_statement }`
  - Response: `Case { id, case_ref, customer_user_id, status, problem_statement, classification?, owner_team_display?, expected_by_at?, created_at }`
  
- `GET /api/v1/cases` - List customer cases
  - Query: `?limit=50&offset=0`
  - Response: `{ items: [CaseListItem], total: number }`
  
- `GET /api/v1/cases/{case_id}` - Get case detail
  - Response: `CaseDetail { id, case_ref, customer_user_id, status, problem_statement, classification?, owner_team_display?, owner_colleague_display?, route_reason?, expected_by_at?, last_update_at, created_at }`

## Seed Data
- **Logins**: `admin@example.com` / `admin123`, `colleague@example.com` / `colleague123`
- **Agents**: intake_triage_agent, guardrail_supervisor_agent, case_owner_agent, colleague_copilot_agent
- **Action Controls**: create_case, update_case, route_to_queue, provide_information, get_transactions, request_document, schedule_callback, card_controls, retry_payment

## Backend Flows

### Session Start → Intake Agent
1. Customer calls POST /api/v1/resolve with message_text
2. Orchestrator creates session and thread
3. Redaction boundary processes customer text
4. Intake agent classifies issue (payment_query, card_declined, fraud_report, complaint, general_query)
5. Guardrail agent screens for triggers (vulnerability, distress, scam, low confidence, explicit human request)
6. Response includes AI disclosure and human path option

### Case Creation (Out-of-Scope or Human Requested)
1. If out-of-scope OR guardrail triggers, assistant prepares for handoff
2. Customer can POST /api/v1/resolve/{session_id}/human-request
3. CaseService.create_case generates unique case_ref (CP-YYYY-NNNNNN)
4. Case linked to thread, assigned to queue
5. route_to_queue tool routes to "general_support_queue"
6. CaseCaptured event published (stub)
7. Response includes case_ref, owner team, expected_by_at (48h default)

### Case Timeline
- Case appears in My Cases with status "new"
- Expected-by always 48 hours in future for open cases
- Owner team display: "Customer Support Team"
