# TASK-6 Handoff: Service Status and Lifeline

## Implemented Endpoints

### GET /api/v1/status
Returns current service status and active incidents.

**Query Parameters:**
- `affected_service_code` (optional, string, max 60 chars): Filter to one affected service

**Response 200:**
```json
{
  "status_state": "operational|disruption",
  "incidents": [
    {
      "incident_reference": "string",
      "incident_state": "declared|monitoring|resolved",
      "affected_service_code": "string",
      "customer_impact_summary": "string",
      "started_at": "ISO datetime",
      "resolved_at": "ISO datetime or null",
      "publications": [
        {
          "headline_text": "string",
          "summary_text": "string",
          "affected_journeys": ["string"],
          "published_at": "ISO datetime"
        }
      ]
    }
  ],
  "lifeline_available": true|false,
  "generated_at": "ISO datetime",
  "cache_version": "string or null",
  "max_age_seconds": 60
}
```

**Errors:**
- `422`: Invalid query parameter
- `503`: Service temporarily unavailable

### GET /api/v1/lifeline
Returns lifeline guidance for current disruptions.

**Query Parameters:**
- `incident_reference` (optional, string, max 80 chars): Restrict to one incident
- `cached_version` (optional, string): Client's cached version for conditional GET

**Response 200:**
```json
{
  "guidance_items": [
    {
      "id": "uuid",
      "incident_id": "uuid",
      "guidance_category": "fallback|safe_action|phone",
      "guidance_title": "string",
      "guidance_body": "string",
      "published_at": "ISO datetime"
    }
  ],
  "protective_actions": ["string"],
  "fallback_channels": [
    {
      "channel_type": "phone|callback|branch|online",
      "label": "string",
      "contact_detail": "string or null",
      "availability_text": "string or null"
    }
  ],
  "cache_version": "string",
  "cache_age_seconds": 0,
  "generated_at": "ISO datetime",
  "withdrawn_cache_versions": []
}
```

**Response 304:** Not Modified (when cached_version matches current)

**Errors:**
- `422`: Invalid query parameter
- `503`: Service temporarily unavailable

### POST /api/v1/status/fallback-exposures
Records that status/lifeline content was shown due to fallback condition (best-effort).

**Request Body:**
```json
{
  "incident_reference": "string (optional, max 80 chars)",
  "content_source": "live|cached",
  "cache_version": "string (optional, max 40 chars)",
  "trigger": "case_service_unavailable|customer_opened",
  "case_reference": "string (optional, max 32 chars)"
}
```

**Response 202:**
```json
{
  "recorded": true|false,
  "correlation_id": "uuid or null"
}
```

**Errors:**
- `422`: Validation error (always returns 202 for internal errors)

## Seed Data

The seed script creates:

### Service Incidents (2)
1. `INC-2024-CARD-001` - Card payments issue (declared)
   - affected_service_code: `card_payments`
   - Started 2 hours ago
   
2. `INC-2024-MOBILE-002` - Mobile banking slower (monitoring)
   - affected_service_code: `mobile_banking`
   - Started 1 hour ago

### Service Status Publications (2)
1. Publication for INC-2024-CARD-001
   - headline: "Card payment issues"
   - affected_journeys: ["card_payment", "atm_withdrawal"]
   
2. Publication for INC-2024-MOBILE-002
   - headline: "Mobile app slower than usual"
   - affected_journeys: ["mobile_login", "mobile_banking"]

### Lifeline Guidance (2)
1. Guidance for INC-2024-CARD-001
   - Title: "Alternative payment methods"
   - Type: fallback
   
2. Guidance for INC-2024-MOBILE-002
   - Title: "Mobile app access tips"
   - Type: fallback

## Background Job

`IncidentIngestJob` runs every `INCIDENT_POLL_SECONDS` (default 20s) and:
1. Calls `IncidentAdapter.get_incidents()`
2. In sandbox mode, returns 2 synthetic incidents
3. Upserts incidents into `service_incidents` table
4. Started automatically in app lifespan

## Architecture Notes

- Status and lifeline services operate independently of case service
- StatusService uses only IncidentRepository (no case dependencies)
- Public endpoints (no authentication required)
- Designed for high availability during disruptions
- Supports caching via cache_version and conditional GET (304)
- IncidentAdapter in sandbox mode returns synthetic data

## Test Coverage

**Unit tests (9):** Service layer logic
- Operational vs disruption state
- Incident filtering
- Publication inclusion
- Lifeline guidance
- Cache version handling
- Fallback exposure recording

**Integration tests (7):** HTTP endpoint behavior
- Status endpoint with/without incidents
- Lifeline endpoint with/without guidance
- 304 Not Modified response
- Fallback exposure recording
- Validation errors

**Acceptance tests (10):** FR-019, FR-020, FR-021 compliance
- Customers can access status during disruption
- Status identifies affected service
- Status remains reachable when case service degraded
- Lifeline guidance available during disruption
- Approved fallback options included
- Cached content support
- Independence from case service
- Routing to status on case retrieval failure

## Configuration

Environment variables (already in config.py):
- `INCIDENT_POLL_SECONDS`: Polling interval for incident ingest (default: 20)
- `STATUS_MAX_AGE_SECONDS`: Cache max-age for status responses (default: 60)
- `ADAPTER_MODE`: "sandbox" for synthetic data, "live" for real integration

## Files Created

- `app/repositories/incident_repository.py` - IncidentRepository
- `app/services/status_service.py` - StatusService
- `app/adapters/incident_adapter.py` - IncidentAdapter
- `app/jobs/incident_ingest_job.py` - IncidentIngestJob
- `app/routers/status.py` - Status endpoints
- Updated `app/main.py` - Mount status router, start incident job
- Updated `app/seed.py` - Add incident seed data
- `tests/unit/test_status_service.py` - 9 unit tests
- `tests/integration/test_status_integration.py` - 7 integration tests
- `tests/acceptance/test_status_acceptance.py` - 10 acceptance tests

## Integration with Frontend

Frontend should:
1. Call `GET /api/v1/status` to check for disruptions
2. Display incident information when status_state is "disruption"
3. Show lifeline link when `lifeline_available` is true
4. Call `GET /api/v1/lifeline` to get guidance items
5. Store `cache_version` and use for conditional GET
6. Fall back to cached content on 503 errors
7. Call `POST /api/v1/status/fallback-exposures` when showing cached content or when case retrieval fails
