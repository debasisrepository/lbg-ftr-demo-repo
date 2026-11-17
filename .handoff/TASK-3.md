# TASK-3 Backend Handoff: Intake and Case Creation

## Endpoints Implemented

### POST /api/v1/cases
Create a new case or surface existing open case.

**Request:**
```json
{
  "issue_type": "card_declined",
  "issue_summary": "My card was declined at the store",
  "issue_title": "Card Declined (optional)",
  "origin_channel": "mobile_app",
  "brand": "lloyds (optional, defaults to user's brand)",
  "customer_party_id": "CUST-001 (colleague only)",
  "existing_case_reference": "CP-EXISTING (optional)"
}
```

**Response (201 for created, 200 for surfaced/not_eligible):**
```json
{
  "outcome": "created",
  "case": {
    "case_reference": "CP-XXXXXXXXXX",
    "customer_party_id": "CUST-001",
    "brand": "lloyds",
    "issue_type": "card_declined",
    "classification_source": "eligibility_rule",
    "issue_title": "Card Declined",
    "issue_summary": "My card was declined at the store",
    "origin_channel": "mobile_app",
    "current_lifecycle_state": "case_created",
    "status_code": "received",
    "status_label": "Received",
    "status_summary_text": "Your case has been received and is being reviewed.",
    "latest_meaningful_update_text": "Your case has been received and is being reviewed.",
    "latest_meaningful_update_at": null,
    "next_step_text": "We're reviewing your case and will update you soon.",
    "outage_impact_banner_text": null,
    "owner": {
      "owner_team_code": "INTAKE_DEFAULT",
      "owner_semantic_label": "Intake Team",
      "owner_display_name": "Intake & Triage",
      "effective_from": "2024-01-01T00:00:00Z"
    },
    "expected_by": {
      "commitment_state": "under_review",
      "expected_by_at": null,
      "customer_explanatory_text": "We're reviewing the timing and will update you soon.",
      "confidence_basis": "initial",
      "effective_from": "2024-01-01T00:00:00Z"
    },
    "opened_at": "2024-01-01T00:00:00Z",
    "closed_at": null,
    "outcome_summary": null,
    "continuity_state": "current"
  },
  "classification_source": "eligibility_rule",
  "anchor_reference": "CC-MOCK-123",
  "redirect_journey_code": null,
  "redirect_message": null,
  "continuity_available": false
}
```

**Outcomes:**
- `created`: New case created successfully (201)
- `surfaced`: Existing open case found for same issue_type (200)
- `not_eligible`: Issue type not eligible, redirect to existing journey (200)

### GET /api/v1/cases/{case_reference}
Get case details by reference.

**Response (200):**
```json
{
  "case_reference": "CP-XXXXXXXXXX",
  "customer_party_id": "CUST-001",
  "brand": "lloyds",
  "issue_type": "card_declined",
  "classification_source": "eligibility_rule",
  "issue_title": "Card Declined",
  "issue_summary": "My card was declined at the store",
  "origin_channel": "mobile_app",
  "current_lifecycle_state": "case_created",
  "status_code": "received",
  "status_label": "Received",
  "status_summary_text": "Your case has been received and is being reviewed.",
  "latest_meaningful_update_text": "Your case has been received and is being reviewed.",
  "latest_meaningful_update_at": null,
  "next_step_text": "We're reviewing your case and will update you soon.",
  "outage_impact_banner_text": null,
  "owner": {
    "owner_team_code": "INTAKE_DEFAULT",
    "owner_semantic_label": "Intake Team",
    "owner_display_name": "Intake & Triage",
    "effective_from": "2024-01-01T00:00:00Z"
  },
  "expected_by": {
    "commitment_state": "under_review",
    "expected_by_at": null,
    "customer_explanatory_text": "We're reviewing the timing and will update you soon.",
    "confidence_basis": "initial",
    "effective_from": "2024-01-01T00:00:00Z"
  },
  "opened_at": "2024-01-01T00:00:00Z",
  "closed_at": null,
  "outcome_summary": null,
  "continuity_state": "current"
}
```

## Seed Data

### Customer Accounts
- `admin@example.com` / `admin123` (CUST-001, brand: lloyds)
- `user1@example.com` / `user123` (CUST-002, brand: lloyds) - **Has existing open case CP-MOCK1 for card_declined**
- `user2@example.com` / `user123` (CUST-003, brand: lloyds) - No cases
- `user3@example.com` / `user123` (CUST-004, brand: lloyds) - No cases
- `user4@example.com` / `user123` (CUST-005, brand: lloyds) - No cases

### Colleague Account
- `colleague@example.com` / `colleague123` (COLL-001)

### Existing Case for user1
- **Case Reference:** CP-MOCK1
- **Customer:** CUST-002 (user1@example.com)
- **Issue Type:** card_declined
- **Status:** received
- **Lifecycle State:** case_created
- **Owner:** INTAKE_DEFAULT (Intake & Triage)
- **Expected By:** under_review

### Eligibility Rules
- `card_declined`: eligible (priority 100)
- `payment_missing`: eligible (priority 90)
- `general_query`: **not eligible** (redirects to existing_support)

## Backend Flow

### Case Creation Flow
1. Check for existing open case with same issue_type (returns surfaced if found)
2. Policy decision via eligibility rules (returns not_eligible if rule says no or rule missing)
3. Call create_case tool via CustomerCaseAdapter (sandbox mode returns mock anchor)
4. Create all components in single transaction:
   - Case record with generated reference CP-XXXXXXXXXX
   - Anchor link to external system
   - Initial status projection (received/case_created)
   - Initial ownership (INTAKE_DEFAULT team)
   - Initial expected-by commitment (under_review)
   - First CaseCaptured event
   - Audit entry
5. Return created outcome with case detail

### Restricted Data Screening
Requests are rejected with 422 if issue_summary or issue_title contain:
- Valid PAN numbers (13-19 digits passing Luhn check)
- Passcode/PIN/password phrases
- Security answer phrases

## Configuration

### Environment Variables
- `ADAPTER_MODE`: "sandbox" (default) or "live"
- `INTAKE_DEFAULT_OWNER_TEAM_CODE`: "INTAKE_DEFAULT" (default)
- `DEFAULT_REDIRECT_JOURNEY_CODE`: "general_support" (default)

### Owner Team Mappings
- INTAKE_DEFAULT - Intake & Triage (default for new cases)
- CARDS_DISPUTES - Card Disputes
- PAYMENTS_SUPPORT - Payments Support
- FRAUD_TEAM - Fraud Investigation
- COMPLAINTS_TEAM - Customer Complaints

## Error Responses

- **401**: Not authenticated
- **403**: Wrong scope or unauthorized
- **404**: Case not found or belongs to different customer
- **422**: Validation error (restricted data, missing required fields, invalid enum values)
- **503**: Dependency unavailable (adapter circuit breaker open, anchor call failed)
