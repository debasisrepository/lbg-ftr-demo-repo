# TASK-3 Handoff: Backend Feature B1 - Sign-in and Session

## Endpoints Implemented

All endpoints mounted under `/api/v1` prefix:

### E-01: POST /api/v1/auth/login
Passcode sign-in on registered device.

**Request:**
```json
{
  "device_identifier": "string (8-128 chars)",
  "mobile_platform": "iOS" | "Android",
  "passcode": "string (4-12 chars)"
}
```

**Response 200:**
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 3600,
  "expires_at": "2026-11-22T12:00:00Z",
  "inactivity_timeout_seconds": 900,
  "session_id": "uuid",
  "user": {
    "id": "uuid",
    "display_name": "string",
    "profile_type": "personal"
  }
}
```

**Errors:**
- 401: Sign-in failed (generic message)
- 422: Validation error
- 429: Rate limit exceeded
- 503: CIAM unavailable

### E-02: GET /api/v1/auth/session
Validate current session and extend activity.

**Headers:** `Authorization: Bearer {token}`

**Response 200:**
```json
{
  "authenticated": true,
  "session_id": "uuid",
  "issued_at": "2026-11-22T11:00:00Z",
  "expires_at": "2026-11-22T12:00:00Z",
  "last_activity_at": "2026-11-22T11:30:00Z",
  "inactivity_expires_at": "2026-11-22T11:45:00Z",
  "user": {
    "id": "uuid",
    "display_name": "string",
    "profile_type": "personal"
  }
}
```

**Errors:**
- 401: Session invalid, expired, or revoked
- 503: CIAM unavailable

### E-03: POST /api/v1/auth/logout
End session and revoke token.

**Headers:** `Authorization: Bearer {token}`

**Response:** 204 No Content

**Errors:**
- 401: Session invalid or already revoked

### E-13: GET /health
Liveness check (no database round trip).

**Response 200:**
```json
{
  "status": "ok"
}
```

### E-14: GET /health/ready
Readiness check (verifies database connectivity).

**Response 200:**
```json
{
  "status": "ok"
}
```

**Response 503:**
Error response shape when database unavailable.

## Seed Credentials

Use these credentials to test the login flow:

| Customer | Device Identifier | Passcode |
|----------|-------------------|----------|
| Alex Taylor (CUST-SYNTH-001) | device-CUST-SYNTH-001-iOS | Pass1234 |
| Alex Taylor (CUST-SYNTH-001) | device-CUST-SYNTH-001-Android | Pass1234 |
| Jordan Smith (CUST-SYNTH-002) | device-CUST-SYNTH-002-iOS | Pass5678 |
| Jordan Smith (CUST-SYNTH-002) | device-CUST-SYNTH-002-Android | Pass5678 |

**Note:** The device_identifier in the request is the plain identifier. The backend hashes it with SHA-256 for database lookup.

## Backend Flows

### Sign-in Flow (E-01)
1. Rate limit check per client address (5 attempts per 300s)
2. Hash device_identifier with SHA-256
3. Lookup active device registration
4. Reject unregistered device BEFORE passcode check
5. Get customer profile
6. Rate limit check per customer (10 attempts per 300s)
7. Get sandbox credential
8. Verify passcode via CIAM sandbox adapter (bcrypt, cost ≥ 12)
9. Create server-side session (hashed token, issued_at, expires_at, last_activity_at)
10. Record authentication_events entry
11. Return bearer token and user summary

**All failures return same generic message:** "We couldn't sign you in. Check your details and try again."

### Session Validation Flow (E-02)
1. Hash bearer token with SHA-256
2. Lookup session by token_hash
3. Check revocation status
4. Check absolute expiry
5. Check inactivity timeout (15 minutes from last_activity_at)
6. Update last_activity_at (extends inactivity window)
7. Return session details and user summary

### Logout Flow (E-03)
1. Hash bearer token with SHA-256
2. Lookup session by token_hash
3. Set revoked_at and revocation_reason = 'logout'
4. Return 204 No Content

### Health Endpoints
- E-13: Returns 200 immediately (no DB)
- E-14: Executes `SELECT 1` on database, returns 200 if successful or 503 if database unavailable

## Configuration

Environment variables (from `app/config.py`):

- `SECRET_KEY`: Required (no default)
- `JWT_ALGORITHM`: HS256
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: 60
- `JWT_INACTIVITY_TIMEOUT_MINUTES`: 15
- `BCRYPT_COST_FACTOR`: 12
- `RATE_LIMIT_ENABLED`: true
- `RATE_LIMIT_LOGIN_PER_ADDRESS_WINDOW_SECONDS`: 300
- `RATE_LIMIT_LOGIN_PER_ADDRESS_MAX_ATTEMPTS`: 5
- `RATE_LIMIT_LOGIN_PER_CUSTOMER_WINDOW_SECONDS`: 300
- `RATE_LIMIT_LOGIN_PER_CUSTOMER_MAX_ATTEMPTS`: 10

## Database Tables Used

- `customer_profile_refs`: Customer profiles
- `device_registrations`: Registered devices
- `sandbox_credentials`: Passcode hashes
- `sandbox_entitlements`: Resource access permissions
- `user_sessions`: Server-side sessions
- `authentication_events`: Auth attempt audit trail

## Middleware

- `CorrelationMiddleware`: Ensures X-Correlation-ID on every request/response
- Global exception handlers for validation, database, and generic errors
- `get_current_user` dependency for protected routes

## Testing

Run tests:
```bash
cd /repos/lbg-ftr-demo-repo/backend
source .venv/bin/activate
pytest tests/test_auth_service.py tests/test_auth_integration.py tests/test_auth_acceptance.py -v
```

## Frontend Integration Notes

1. **Login:** POST to `/api/v1/auth/login` with device_identifier, mobile_platform, and passcode
2. **Store token:** Save `access_token` in sessionStorage
3. **Protected requests:** Include `Authorization: Bearer {token}` header
4. **Session check:** GET `/api/v1/auth/session` before showing protected content
5. **Logout:** POST to `/api/v1/auth/logout` and clear stored token
6. **Handle 401:** Redirect to login page and clear token
7. **Handle 429:** Show rate limit message with Retry-After
8. **Correlation:** Optionally send X-Correlation-ID; always read it from response for support tracing
