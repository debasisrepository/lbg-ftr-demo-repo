# Task 3: Backend Feature B1 - Sign-in and Step-up Authentication

## Implementation Summary

This task implements the authentication and step-up authentication (SCA) domains for the payment journey platform, covering FR-001 (Sign in) and FR-002 (Prove it's her) requirements.

## API Endpoints

### Authentication Endpoints

#### POST /api/v1/auth/login
Sign in with username and password.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200 OK):**
```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in_seconds": 28800,
  "session_id": 123,
  "step_up_required": true,
  "available_step_up_methods": ["passcode", "biometric"],
  "active_profile_id": 456
}
```

**Error Responses:**
- 401 Unauthorized: "We couldn't sign you in with those details." (generic error for invalid credentials, non-existent user, or inactive account)
- 429 Too Many Requests: "Too many sign-in attempts. Try again shortly." (rate limit exceeded)
- 422 Validation Error: Missing or invalid fields

**Behavioral Notes:**
- Generic error message protects against account enumeration
- Rate limiting: 5 attempts per IP per 300 seconds (configurable)
- Returns JWT access token with `exp` claim
- Session backed by revocable server-side record
- Returns available step-up methods from registered devices

#### POST /api/v1/auth/logout
Logout and revoke session.

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

**Error Responses:**
- 401 Unauthorized: Token missing, invalid, or session revoked

### Step-up Authentication Endpoints

#### POST /api/v1/sca/verify-step-up
Verify step-up authentication with passcode or biometric.

**Request Body:**
```json
{
  "session_id": 123,
  "method": "passcode",
  "passcode": "123456",
  "biometric_assertion": null,
  "device_id": "device-001"
}
```

**Method Values:**
- `"passcode"`: 6-digit passcode verification (requires `passcode` field)
- `"biometric"`: Biometric verification (requires `biometric_assertion` field)

**Response (200 OK) - Success:**
```json
{
  "status": "verified",
  "session_id": 123,
  "step_up_verified": true,
  "remaining_attempts": null,
  "next_route": "/accounts",
  "available_methods": []
}
```

**Response (200 OK) - Failed Attempt:**
```json
{
  "status": "failed",
  "session_id": 123,
  "step_up_verified": false,
  "remaining_attempts": 2,
  "next_route": "/step-up",
  "available_methods": ["passcode"]
}
```

**Response (200 OK) - Locked After 3 Attempts:**
```json
{
  "status": "locked",
  "session_id": 123,
  "step_up_verified": false,
  "remaining_attempts": 0,
  "next_route": "/login",
  "available_methods": ["password"]
}
```

**Error Responses:**
- 400 Bad Request: "Passcode required" or "Biometric assertion required"
- 400 Bad Request: "Challenge expired"
- 400 Bad Request: "Invalid session"
- 422 Validation Error: Invalid method or missing required fields

**Behavioral Notes:**
- Passcode lockout after 3 failed attempts
- Lockout persisted in `step_up_challenge` table
- Locked passcode directs user back to password authentication
- Biometric data never transmitted to bank (only assertion/outcome)
- Audit events logged for all attempts and lockouts

## Seed Credentials

The following credentials are available in seed data:

**Admin User:**
- Username: `admin@example.com`
- Password: `admin123`
- Profile: Personal profile (ID varies)
- Device: Registered with passcode and biometric enabled

**Personal User:**
- Username: `john.smith@example.com`
- Password: `Personal123!`
- Profile: Personal profile
- Device: Registered with passcode and biometric enabled

**Business User:**
- Username: `jane.doe@businessexample.com`
- Password: `Business123!`
- Profile: Business profile
- Device: Not registered (for testing missing device scenarios)

**Step-up Verification:**
- Passcode for all devices: `123456` (stub implementation)
- Biometric: Any non-empty assertion accepted (stub implementation)

## Architecture Components

### Schemas
- `app/schemas/auth_schemas.py`: LoginRequest, TokenResponse, LogoutResponse
- `app/schemas/sca_schemas.py`: StepUpVerifyRequest, StepUpVerifyResponse
- `app/schemas/common_schemas.py`: ErrorResponse

### Repositories
- `app/repositories/auth_repository.py`: User identity, session, and device persistence
- `app/repositories/sca_repository.py`: Step-up challenge persistence
- `app/repositories/audit_repository.py`: Audit log persistence
- `app/repositories/telemetry_repository.py`: Journey event persistence

### Services
- `app/services/auth_service.py`: Authentication logic, rate limiting, generic error handling
- `app/services/sca_service.py`: Step-up verification, passcode lockout, biometric handling
- `app/services/audit_service.py`: Security event audit logging
- `app/services/telemetry_service.py`: Journey step telemetry

### Adapters (Stubs)
- `app/adapters/ciam_adapter.py`: External CIAM integration stub
- `app/adapters/sca_provider_adapter.py`: External SCA provider stub with hardcoded passcode

### Routers
- `app/routers/auth.py`: Authentication endpoints
- `app/routers/sca.py`: Step-up authentication endpoints

### Middleware
- `app/middleware/correlation_id.py`: Correlation ID generation and propagation
- `app/middleware/auth_context.py`: JWT token validation, user extraction, session verification
- `app/middleware/error_handlers.py`: Custom error handlers for domain exceptions

### Common
- `app/common/idempotency.py`: Idempotency key generation
- `app/common/correlation.py`: Correlation ID extraction from request

## Security Features

1. **Generic Error Messages**: Invalid credentials always return "We couldn't sign you in with those details." to prevent account enumeration
2. **Rate Limiting**: 5 failed login attempts per IP per 5-minute window (configurable)
3. **Password Hashing**: bcrypt with cost factor 12
4. **JWT Tokens**: Include `exp` claim, backed by revocable server-side sessions
5. **Session Revocation**: Server-side session state allows logout and token revocation
6. **Passcode Lockout**: 3 failed passcode attempts lock passcode authentication
7. **Lockout Persistence**: Lockout state persisted in database `step_up_challenge` table
8. **Audit Logging**: All authentication events logged with correlation ID
9. **Biometric Privacy**: Biometric data never transmitted; only assertions verified

## Testing

### Unit Tests
- `tests/test_auth_service.py`: Auth service logic tests
  - Successful login
  - Wrong password
  - User not found
  - Inactive user
  - Rate limiting
  - Logout
- `tests/test_sca_service.py`: SCA service logic tests
  - Passcode success
  - Passcode failure
  - Passcode lockout after 3 attempts
  - Biometric success
  - Locked challenge status

### Integration Tests
- `tests/test_auth_integration.py`: Auth endpoint tests
  - Login endpoint success
  - Login endpoint wrong password
  - Login endpoint user not found
  - Login endpoint missing fields
  - Login rate limit
  - Logout endpoint
  - Logout unauthorized
- `tests/test_sca_integration.py`: SCA endpoint tests
  - Verify step-up passcode success
  - Verify step-up passcode failure
  - Verify step-up passcode lockout
  - Verify step-up biometric success
  - Verify step-up missing passcode
  - Verify step-up invalid method

## Configuration

Environment variables used:
- `JWT_SECRET_KEY`: Secret key for JWT signing (required)
- `JWT_ALGORITHM`: JWT algorithm (default: "HS256")
- `JWT_EXPIRY_MINUTES`: Token expiration in minutes (default: 480)
- `RATE_LIMIT_ENABLED`: Enable/disable rate limiting (default: true)
- `RATE_LIMIT_LOGIN_ATTEMPTS`: Max login attempts (default: 5)
- `RATE_LIMIT_LOGIN_WINDOW_SECONDS`: Rate limit window (default: 300)

## Acceptance Criteria Coverage

✓ Given the username field is empty or the password field is empty, when the customer selects Continue, then the system shows inline validation for the missing field and does not submit the sign-in request.
  - Handled by Pydantic schema validation (422 response)

✓ Given the customer submits incorrect credentials, when authentication fails, then the system shows one generic error message and does not reveal which credential was incorrect.
  - Generic error: "We couldn't sign you in with those details."

✓ Given the customer signs in with valid credentials, when the sign-in request succeeds, then the system advances the customer to the step-up authentication stage.
  - Returns `step_up_required: true` with available methods

✓ Given a registered device and successful primary sign-in, when the customer enters the correct passcode or uses a valid biometric factor, then the system authenticates the step and continues to the account overview.
  - Returns `next_route: "/accounts"` on success

✓ Given the customer enters a wrong passcode three times, when the threshold is reached, then the system pauses passcode sign-in and directs the customer back to password authentication.
  - Returns `status: "locked"` and `next_route: "/login"` after 3 failed attempts

✓ Given biometric sign-in is unavailable on the device, when the customer reaches this step, then the system offers passcode authentication without blocking access.
  - Available methods filtered by device capabilities

## Dependencies

- Task 1: Database schema and seed data (completed)

## Next Steps

- Task 4: Frontend UI for sign-in and step-up screens
- Task 5: Account overview endpoints
- Task 6: Payee management endpoints
- Task 7: Payment orchestration endpoints
