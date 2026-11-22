# Security Scan Report

**Project:** Sample Bank Mobile Banking Application  
**Scan Date:** 2026-11-22  
**Scanner Version:** 1.0.0  
**Target Stack:** Python (FastAPI) + React (TypeScript)  
**Scope:** Backend + Frontend + Dependencies

---

## Executive Summary

| Severity | Count |
|----------|-------|
| Critical | 0 |
| High     | 5 |
| Medium   | 6 |
| Low      | 4 |
| Info     | 4 |

**Overall Risk Level:** High

### Key Findings

- **Authentication & Authorization:** 5 high-severity findings related to missing authentication middleware, horizontal privilege escalation, and incomplete entitlement checks
- **Session Management:** 2 medium-severity findings related to insecure session token transmission and session fixation
- **Dependencies:** No CVEs found (0 vulnerabilities in 397 npm packages and all Python dependencies)
- **Code Quality:** Good - no SQL injection, XSS, or hardcoded secrets detected
- **Business Logic:** Dual authorization workflow incomplete, race condition in payment approval

### Immediate Action Required

1. **Implement global authentication middleware** to prevent authentication bypass
2. **Add ownership verification** to all payment and resource endpoints
3. **Enforce entitlement checks** on payment operations
4. **Complete dual authorization** for business payments
5. **Enable rate limiting** in production

---

## Dependency Vulnerabilities (CVE)

### Python Dependencies (pip-audit)

✅ **No vulnerabilities found**

Scanned packages:
- fastapi 0.115.0+
- uvicorn 0.54.0
- sqlalchemy 2.0.35+
- pydantic 2.10.0+
- bcrypt 4.2.1+
- pyjwt 2.10.0+
- cryptography 44.0.0+

All dependencies are up to date with no known CVEs.

### Node.js Dependencies (npm audit)

✅ **No vulnerabilities found**

Scanned 397 packages (10 prod, 388 dev):
- react 18.3.1
- react-router-dom 7.18.6
- vite 6.0.1
- typescript 5.6.2

All dependencies are current with no known vulnerabilities.

---

## SAST Findings

### Critical Severity (0 findings)

None.

---

### High Severity (5 findings)

#### H-001: Missing Global Authentication Middleware
**CWE-306: Missing Authentication for Critical Function**  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**Severity:** High (CVSS 8.5)

**Location:** `backend/app/main.py:30`

**Description:**  
The application does not enforce authentication at the middleware level. JWT token extraction is implemented per-route using dependency injection in individual endpoint functions. This pattern is error-prone and creates risk of authentication bypass if a developer forgets to include the authentication dependency.

**Current Implementation:**
```python
# Each route manually extracts token
def get_current_customer_id(request: Request) -> uuid.UUID:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthorizationError("Missing or invalid authorization header")
    token = auth_header.split(" ")[1]
    payload = decode_jwt_token(token)
    return uuid.UUID(payload.get("sub"))
```

**Impact:**  
- Routes without explicit authentication dependency are accessible without credentials
- Inconsistent authentication enforcement across endpoints
- Increased risk of developer error leading to unprotected endpoints

**Remediation:**
1. Implement global authentication middleware that extracts and validates JWT tokens
2. Store authenticated user context in `request.state`
3. Use `Depends()` to access pre-authenticated context
4. Maintain an explicit allowlist of public routes

**Example Fix:**
```python
# app/core/auth_middleware.py
async def auth_middleware(request: Request, call_next):
    if request.url.path in PUBLIC_ROUTES:
        return await call_next(request)
    
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError("Missing authorization header")
    
    token = auth_header.replace("Bearer ", "")
    payload = decode_jwt_token(token)  # raises on invalid
    
    request.state.customer_id = uuid.UUID(payload["sub"])
    request.state.session_id = uuid.UUID(payload["session_id"])
    request.state.profile_id = payload.get("active_profile_id")
    
    return await call_next(request)

# main.py
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
```

**Regulatory Impact:** Violates PCI-DSS 8.2, OWASP ASVS 2.1

---

#### H-002: Horizontal Privilege Escalation - Payment Access
**CWE-639: Authorization Bypass Through User-Controlled Key**  
**OWASP:** A01:2021 – Broken Access Control  
**Severity:** High (CVSS 9.0)

**Locations:**
- `backend/app/routers/payments.py:94` (approve_payment)
- `backend/app/routers/payments.py:159` (submit_payment)
- `backend/app/routers/payments.py:207` (get_payment)
- `backend/app/routers/payments.py:246` (get_payment_receipt)

**Description:**  
Payment endpoints accept payment_order_id as a parameter but do not verify that the authenticated customer owns the payment order before performing operations. An attacker can access, approve, or submit other customers' payments by changing the UUID in the request.

**Vulnerable Code:**
```python
@router.get("/{payment_order_id}", response_model=PaymentDetailResponse)
def get_payment(payment_order_id: uuid.UUID, db: Session = Depends(get_db)):
    payment_service = PaymentService(db)
    result = payment_service.get_payment_with_details(payment_order_id)
    # Missing: verify result["payment_order"].customer_id == authenticated_customer_id
    return PaymentDetailResponse(...)
```

**Attack Scenario:**
1. Attacker creates a legitimate payment (payment_order_id = A)
2. Attacker enumerates or guesses another customer's payment ID (payment_order_id = B)
3. Attacker calls GET /api/v1/payments/B with valid JWT
4. System returns victim's payment details without ownership check
5. Attacker can then approve or submit victim's payment

**Impact:**
- **Critical**: Complete payment fraud - attacker can view, approve, and submit any payment
- **Data Breach**: Exposure of sensitive payment details (amounts, payees, account numbers)
- **Regulatory Violation**: GDPR, PCI-DSS, PSD2 Strong Customer Authentication bypass

**Remediation:**
Add ownership verification to all payment endpoints:

```python
def get_payment(
    payment_order_id: uuid.UUID,
    customer_id: uuid.UUID = Depends(get_current_customer_id),
    db: Session = Depends(get_db)
):
    result = payment_service.get_payment_with_details(payment_order_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # CRITICAL: Verify ownership
    if result["payment_order"].customer_id != customer_id:
        raise HTTPException(status_code=404, detail="Payment not found")  # Don't reveal existence
    
    return PaymentDetailResponse(...)
```

**Regulatory Impact:** Violates PSD2 SCA requirements, PCI-DSS 6.5.8, OWASP ASVS 4.1

---

#### H-003: Insecure Direct Object Reference - Incident Reports
**CWE-639: Authorization Bypass Through User-Controlled Key**  
**OWASP:** A01:2021 – Broken Access Control  
**Severity:** High (CVSS 8.5)

**Location:** `backend/app/routers/incidents.py:67`

**Description:**  
The incident report retrieval endpoint fetches the report first, then checks ownership. This creates a timing attack vector and unnecessarily loads sensitive data before authorization.

**Vulnerable Code:**
```python
def get_incident_report(incident_reference: str, customer_id: uuid.UUID = Depends(...)):
    incident_report = incident_service.get_incident_report(incident_reference)  # Load first
    
    if incident_report.customer_id != customer_id:  # Check later
        raise HTTPException(status_code=404)
```

**Impact:**
- Information disclosure via timing attacks
- Unnecessary database load of unauthorized records
- Potential cache poisoning

**Remediation:**
```python
# Pass customer_id to service layer
def get_incident_report(incident_reference: str, customer_id: uuid.UUID):
    incident_report = incident_service.get_incident_report_for_customer(
        incident_reference, customer_id  # Check at DB query level
    )
```

---

#### H-004: Incomplete Entitlement Enforcement - Payment Operations
**CWE-862: Missing Authorization**  
**OWASP:** A01:2021 – Broken Access Control  
**Severity:** High (CVSS 8.0)

**Location:** `backend/app/routers/payments.py:44` (prepare_payment)

**Description:**  
The accounts overview endpoint correctly checks that the active profile has 'view_accounts' entitlement. However, payment preparation does not verify that the profile has 'initiate_payments' permission. This allows privilege escalation across profiles.

**Attack Scenario:**
1. User switches to a "view-only" profile (can_initiate_payments = false)
2. User calls POST /api/v1/payments/prepare with view-only profile active
3. System allows payment preparation despite lack of permission
4. User can initiate payments with insufficient privileges

**Impact:**
- Profile-based authorization bypass
- Business logic violation
- Separation of duties compromise

**Current Code:**
```python
# backend/app/routers/accounts.py - CORRECT
def get_accounts_overview(...):
    entitlement_service.require_capability(db, profile_id, "view_accounts")  # ✓
    
# backend/app/routers/payments.py - MISSING
def prepare_payment(...):
    # Missing: entitlement_service.require_capability(db, profile_id, "initiate_payments")
```

**Remediation:**
```python
@router.post("/prepare", response_model=PaymentPrepareResponse)
def prepare_payment(
    request: Request,
    payment_request: PaymentPrepareRequest,
    profile_id: uuid.UUID = Depends(get_current_profile_id),
    db: Session = Depends(get_db)
):
    # Add entitlement check
    entitlement_service = EntitlementService()
    entitlement_service.require_capability(db, profile_id, "initiate_payments")
    
    # Proceed with payment preparation
    payment_service = PaymentService(db)
    # ...
```

**Regulatory Impact:** Violates SOD (Separation of Duties) requirements, OWASP ASVS 4.1

---

#### H-005: Dual Authorization Bypass - Business Payments
**CWE-863: Incorrect Authorization**  
**OWASP:** A01:2021 – Broken Access Control  
**Severity:** High (CVSS 7.5)

**Location:** `backend/app/services/payment_service.py:217` (approve_payment)

**Description:**  
The payment approval service does not enforce dual authorization for business accounts. While the ScaApproval model supports tracking multiple approvers, the business logic does not verify that high-value business payments have been approved by two distinct users before submission.

**Missing Logic:**
- No check for profile_type = "business"
- No threshold check for payment amount
- No verification of distinct approver count
- Second approver can be the same user on different device

**Impact:**
- Single-user approval of business payments
- Internal fraud risk
- Audit compliance failure
- Regulatory violation (dual authorization required for business banking)

**Remediation:**
```python
def approve_payment(self, payment_order_id, device_id, customer_id, ...):
    payment_order = self.payment_order_repo.get_by_id(payment_order_id)
    
    # Check if dual authorization required
    profile = self.profile_repo.get_by_id(payment_order.profile_id)
    if profile.profile_type == "business" and payment_order.amount_minor > 50000_00:  # £50k
        # Get existing approvals
        existing_approvals = self.sca_approval_repo.get_by_payment_order(payment_order_id)
        
        # Verify distinct approvers
        approver_ids = {a.customer_id for a in existing_approvals}
        if customer_id in approver_ids:
            raise AuthorizationError("Payment already approved by this user")
        
        if len(approver_ids) < 1:  # Need at least 2 total
            # Record first approval but don't allow submission
            self.approval_service.create_sca_approval(...)
            payment_order.current_internal_state = "pending_second_approval"
            return payment_order
    
    # Proceed with final approval
    self.approval_service.create_sca_approval(...)
```

**Regulatory Impact:** Violates banking dual control requirements, SOX compliance, OWASP ASVS 4.1

---

### Medium Severity (6 findings)

#### M-001: Insecure Session Token Transmission
**CWE-614: Sensitive Cookie in HTTPS Session Without 'Secure' Attribute**  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**Severity:** Medium (CVSS 6.5)

**Location:** `backend/app/routers/auth.py:78`

**Description:**  
Session IDs are transmitted via custom X-Session-ID headers instead of HTTP-only secure cookies. This pattern:
- Exposes sessions to XSS attacks (JavaScript can read headers)
- Requires manual management on client side
- Does not benefit from browser security features

**Current Implementation:**
```python
session_id_str = request.headers.get("X-Session-ID")
```

**Impact:**
- XSS vulnerability can steal session tokens
- CSRF protection more complex
- Session tokens visible in browser DevTools

**Remediation:**
Use HTTP-only, secure cookies:
```python
response.set_cookie(
    key="session_token",
    value=session_token,
    httponly=True,
    secure=True,  # HTTPS only
    samesite="Lax",
    max_age=1800
)
```

---

#### M-002: Session Fixation Vulnerability
**CWE-384: Session Fixation**  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**Severity:** Medium (CVSS 6.5)

**Location:** `backend/app/services/auth_service.py:159` (submit_proof)

**Description:**  
When a user submits second-factor proof and upgrades from 'password_only' to 'proven' auth level, the session ID is not regenerated. This allows session fixation attacks where an attacker pre-establishes a session and tricks the victim into authenticating with it.

**Attack Scenario:**
1. Attacker creates session S1 with password_only auth level
2. Attacker tricks victim into using session S1
3. Victim submits second factor, upgrading S1 to proven level
4. Attacker now has proven session without knowing victim's credentials

**Remediation:**
```python
def submit_proof(self, request: ProofRequest, correlation_id: str):
    # ... verify proof ...
    
    # Regenerate session token after privilege elevation
    old_session = self.session_repo.get_by_id(session_id_uuid)
    self.session_repo.end_session(old_session, 'upgraded')
    
    # Create new session with proven auth level
    new_token = generate_session_token()
    new_session = self.session_repo.create(
        customer_id=old_session.customer_id,
        session_token_hash=hash_token(new_token),
        auth_level='proven',  # Upgraded
        ...
    )
    
    return ProofResponse(session_id=str(new_session.session_id), ...)
```

---

#### M-003: Race Condition in Payment Approval
**CWE-362: Concurrent Execution using Shared Resource with Improper Synchronization**  
**OWASP:** A04:2021 – Insecure Design  
**Severity:** Medium (CVSS 6.0)

**Location:** `backend/app/services/payment_service.py:217`

**Description:**  
The payment approval process does not use database-level locking. Concurrent approval requests could result in:
- Double submission
- Inconsistent state (two approvals created but payment submitted once)
- Race between approval and status check

**Remediation:**
```python
def approve_payment(self, payment_order_id, ...):
    # Use SELECT FOR UPDATE to lock row
    payment_order = self.payment_order_repo.get_by_id_for_update(payment_order_id)
    
    if payment_order.current_internal_state != "prepared":
        raise ValidationError("Payment cannot be approved in current state")
    
    # Critical section - locked
    self.approval_service.create_sca_approval(...)
    payment_order.current_internal_state = "awaiting_sca"
    
    self.db.commit()  # Release lock
```

---

#### M-004: Missing CSRF Protection
**CWE-352: Cross-Site Request Forgery (CSRF)**  
**OWASP:** A01:2021 – Broken Access Control  
**Severity:** Medium (CVSS 6.5)

**Location:** `backend/app/main.py`

**Description:**  
While the application uses JWT tokens in Authorization headers (which provides some CSRF protection), state-changing operations like payments and profile switching should have additional CSRF defenses. If session cookies were used, CSRF would be a critical issue.

**Impact:**
- If migrating to cookie-based sessions, CSRF attacks become possible
- Defense-in-depth missing

**Remediation:**
Implement double-submit cookie pattern:
```python
# Generate CSRF token on login
csrf_token = secrets.token_urlsafe(32)
response.set_cookie("csrf_token", csrf_token, httponly=False)
response.headers["X-CSRF-Token"] = csrf_token

# Verify on state-changing requests
@router.post("/payments/prepare")
def prepare_payment(request: Request, ...):
    csrf_cookie = request.cookies.get("csrf_token")
    csrf_header = request.headers.get("X-CSRF-Token")
    
    if not csrf_cookie or csrf_cookie != csrf_header:
        raise HTTPException(403, "CSRF token mismatch")
```

---

#### M-005: Weak Default Secret Key
**CWE-798: Use of Hard-coded Credentials**  
**OWASP:** A02:2021 – Cryptographic Failures  
**Severity:** Medium (CVSS 7.0)

**Location:** `backend/app/config.py:12`

**Description:**  
The default JWT secret key is "change-me-in-production-min-32-chars". While intended for development, this poses a risk if:
- Accidentally deployed to production
- Developers don't rotate secrets
- Key is predictable for test environments

**Remediation:**
```python
class Settings(BaseSettings):
    secret_key: str = "change-me-in-production-min-32-chars"
    environment: str = "development"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Fail in production with default key
        if self.environment == "production" and "change-me" in self.secret_key:
            raise RuntimeError(
                "Production deployment detected with default SECRET_KEY. "
                "Set a strong secret key via environment variable."
            )
```

---

#### M-006: Rate Limiting Disabled by Default
**CWE-770: Allocation of Resources Without Limits or Throttling**  
**OWASP:** A04:2021 – Insecure Design  
**Severity:** Medium (CVSS 6.0)

**Location:** `backend/dev.env:17`

**Description:**  
Rate limiting is disabled by default (`RATE_LIMIT_ENABLED=false`). This exposes the application to:
- Brute-force attacks on authentication
- Credential stuffing
- Denial of service
- API abuse

**Remediation:**
```bash
# Production configuration
RATE_LIMIT_ENABLED=true

# Add rate limits per endpoint
# Login: 5 attempts per minute per IP
# Payment: 10 per minute per customer
# API: 100 requests per minute per customer
```

---

### Low Severity (4 findings)

#### L-001: Overly Permissive CORS Configuration
**CWE-942: Permissive Cross-domain Policy with Untrusted Domains**  
**OWASP:** A05:2021 – Security Misconfiguration  
**Severity:** Low (CVSS 4.0)

**Location:** `backend/app/main.py:45`

**Description:**  
CORS is configured with `allow_methods=['*']` and `allow_headers=['*']`. While `allow_origins` is restricted, the wildcards increase attack surface.

**Remediation:**
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # Explicit list
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],  # Explicit list
)
```

---

#### L-002: Missing Security Headers
**CWE-693: Protection Mechanism Failure**  
**OWASP:** A05:2021 – Security Misconfiguration  
**Severity:** Low (CVSS 5.5)

**Location:** `backend/app/main.py`

**Description:**  
The application does not set critical security headers:
- Content-Security-Policy
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security

**Remediation:**
```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

#### L-003: Stub Authentication Adapters in Use
**CWE-306: Missing Authentication for Critical Function**  
**OWASP:** A07:2021 – Identification and Authentication Failures  
**Severity:** Low (CVSS 9.5 if deployed to production)

**Location:** `backend/dev.env:20`

**Description:**  
All external adapters (CIAM, fraud, payment hub) are configured in 'stub' mode. This is acceptable for development but catastrophic if deployed to production.

**Remediation:**
```python
# Add startup validation
@app.on_event("startup")
def validate_production_config():
    if settings.environment == "production":
        stub_adapters = [
            k for k, v in vars(settings).items() 
            if k.startswith("adapter_mode_") and v == "stub"
        ]
        if stub_adapters:
            raise RuntimeError(
                f"Production deployment with stub adapters: {stub_adapters}"
            )
```

---

#### L-004: Potential Information Disclosure via Error Messages
**CWE-209: Generation of Error Message Containing Sensitive Information**  
**OWASP:** A04:2021 – Insecure Design  
**Severity:** Low (CVSS 4.5)

**Location:** `backend/app/core/errors.py`

**Description:**  
Generic exception handler may expose stack traces or internal details in error responses. Verify debug mode is disabled in production.

**Remediation:**
```python
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if settings.environment == "development":
        # Full error details in dev
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc), "traceback": traceback.format_exc()}
        )
    else:
        # Generic message in production
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred. Please contact support."}
        )
```

---

## Secrets Detection

✅ **No hardcoded secrets found**

Scanned for:
- API keys
- AWS credentials
- Private keys (RSA, SSH, PGP)
- Connection strings with embedded passwords
- JWT secrets in source code

All sensitive values are loaded from environment variables. Development secrets in `dev.env` are appropriately weak placeholders.

---

## Remediation Plan

### Priority 1: Critical & High Severity (Fix Immediately)

| Finding | Effort | Impact |
|---------|--------|--------|
| H-001: Missing Auth Middleware | 3 days | Prevents authentication bypass |
| H-002: Payment Authorization | 2 days | Prevents payment fraud |
| H-003: IDOR Incidents | 1 day | Prevents data disclosure |
| H-004: Entitlement Checks | 1 day | Enforces least privilege |
| H-005: Dual Authorization | 3 days | Business compliance |

**Total Effort:** 10 days  
**Business Impact:** Blocks production deployment, prevents fraud

### Priority 2: Medium Severity (Fix Before Release)

| Finding | Effort | Impact |
|---------|--------|--------|
| M-001: Secure Cookies | 2 days | XSS protection |
| M-002: Session Fixation | 1 day | Session security |
| M-003: Race Condition | 2 days | Payment integrity |
| M-004: CSRF Protection | 2 days | Defense-in-depth |
| M-005: Default Secrets | 0.5 day | Production readiness |
| M-006: Rate Limiting | 1 day | DoS protection |

**Total Effort:** 8.5 days

### Priority 3: Low Severity (Fix in Next Sprint)

| Finding | Effort | Impact |
|---------|--------|--------|
| L-001: CORS Config | 0.5 day | Reduced attack surface |
| L-002: Security Headers | 0.5 day | Defense-in-depth |
| L-003: Stub Adapters | 0.5 day | Production validation |
| L-004: Error Messages | 0.5 day | Info disclosure prevention |

**Total Effort:** 2 days

---

## Compliance Mapping

### OWASP Top 10 (2021)

| OWASP Category | Findings | Status |
|----------------|----------|--------|
| A01: Broken Access Control | H-002, H-003, H-004, H-005, M-004 | ❌ Non-compliant |
| A02: Cryptographic Failures | M-005 | ⚠️ Partially compliant |
| A04: Insecure Design | M-003, M-006, L-004 | ⚠️ Partially compliant |
| A05: Security Misconfiguration | L-001, L-002, L-003 | ⚠️ Partially compliant |
| A07: Auth Failures | H-001, M-001, M-002 | ❌ Non-compliant |

### CWE Top 25 (2024)

| CWE | Title | Findings | Rank |
|-----|-------|----------|------|
| CWE-862 | Missing Authorization | H-004 | #3 |
| CWE-639 | Authorization Bypass | H-002, H-003 | #6 |
| CWE-306 | Missing Authentication | H-001, L-003 | #9 |
| CWE-352 | CSRF | M-004 | #10 |
| CWE-798 | Hard-coded Credentials | M-005 | #13 |

### PCI-DSS 4.0

| Requirement | Status | Findings |
|-------------|--------|----------|
| 6.5.1 Injection Flaws | ✅ Pass | No SQL injection found |
| 6.5.3 Insecure Cryptography | ⚠️ Partial | M-005 (weak default key) |
| 6.5.8 Improper Access Control | ❌ Fail | H-002, H-003, H-004 |
| 6.5.10 Broken Authentication | ❌ Fail | H-001, M-001, M-002 |
| 8.2 Multi-factor Authentication | ✅ Pass | Step-up auth implemented |

### PSD2 Strong Customer Authentication

| Requirement | Status | Compliance |
|-------------|--------|-----------|
| Two-factor authentication | ✅ Pass | Password + biometric/passcode |
| Dynamic linking | ✅ Pass | HMAC digest of payment details |
| Transaction signing | ⚠️ Partial | H-005 (dual auth incomplete) |
| Session management | ❌ Fail | M-001, M-002 |

### OWASP ASVS Level 2

| Control | Status | Notes |
|---------|--------|-------|
| 2.1 Authentication | ❌ Fail | H-001, M-001, M-002 |
| 4.1 Authorization | ❌ Fail | H-002, H-003, H-004, H-005 |
| 8.3 Session Management | ⚠️ Partial | M-001, M-002 |
| 9.1 Communication Security | ⚠️ Partial | L-002 (missing headers) |

**Overall ASVS Compliance: Non-compliant** (must fix Critical & High findings)

---

## Testing Recommendations

### 1. Penetration Testing Focus Areas

- **Authentication Bypass:** Attempt to access protected endpoints without JWT
- **Horizontal Privilege Escalation:** Access other customers' payments/accounts
- **Vertical Privilege Escalation:** Escalate from view-only to payment-initiating profile
- **Session Security:** Session fixation, session hijacking, concurrent sessions
- **Payment Fraud:** Dual authorization bypass, approval workflow manipulation

### 2. Security Test Cases

```python
# Test H-002: Payment authorization bypass
def test_cannot_access_other_customer_payment():
    # Customer A creates payment
    payment_id = create_payment(customer_a_token)
    
    # Customer B attempts to access
    response = get_payment(payment_id, customer_b_token)
    
    assert response.status_code == 404
    assert "payment_order_id" not in response.json()

# Test H-004: Entitlement enforcement
def test_cannot_initiate_payment_without_entitlement():
    # Switch to view-only profile
    switch_profile(view_only_profile_id)
    
    # Attempt payment
    response = prepare_payment(amount=100_00, customer_token)
    
    assert response.status_code == 403
    assert "lacks initiate_payments capability" in response.json()["detail"]

# Test H-005: Dual authorization
def test_business_payment_requires_two_approvers():
    payment_id = create_business_payment(amount=100000_00)  # £1000
    
    # First approval
    approve_payment(payment_id, user1_token)
    payment = get_payment(payment_id, user1_token)
    assert payment["status"] == "pending_second_approval"
    
    # Cannot submit with single approval
    response = submit_payment(payment_id, user1_token)
    assert response.status_code == 400
    
    # Second approval by different user
    approve_payment(payment_id, user2_token)
    payment = get_payment(payment_id, user2_token)
    assert payment["status"] == "approved"
```

### 3. Automated Security Testing

- **SAST:** Integrate Bandit (Python), ESLint security plugin (TypeScript)
- **DAST:** OWASP ZAP or Burp Suite automated scans
- **Dependency Scanning:** Integrate pip-audit and npm audit into CI/CD
- **Secret Scanning:** git-secrets or truffleHog in pre-commit hooks

---

## Scan Configuration

### Tools Used

**Dependency Scanning:**
- pip-audit 2.7.3 (Python)
- npm audit 10.9.2 (Node.js)

**SAST:**
- Manual code review with pattern matching
- SQLAlchemy query analysis
- React security best practices check

**Secrets Detection:**
- Regex-based scanning for API keys, tokens, credentials
- Entropy analysis for high-randomness strings
- Environment variable validation

### Scope

**Files Scanned:**
- Backend: 368 Python files (app/, tests/, alembic/)
- Frontend: 55,156+ TypeScript/React files
- Configuration: pyproject.toml, package.json, .env files

**Lines of Code:**
- Backend: ~15,000 LOC
- Frontend: ~1.3M LOC (including node_modules)

**Scan Duration:** ~45 minutes

---

## Conclusion

The Sample Bank mobile banking application demonstrates **good security fundamentals** (no SQL injection, XSS, or hardcoded secrets) but has **critical authorization gaps** that must be fixed before production deployment.

### Strengths
✅ No dependency vulnerabilities  
✅ Parameterized queries (no SQL injection)  
✅ React XSS protection  
✅ Bcrypt password hashing  
✅ JWT-based authentication framework  
✅ Entitlement model designed (partially implemented)  

### Critical Gaps
❌ Missing authentication middleware  
❌ Horizontal privilege escalation vulnerabilities  
❌ Incomplete entitlement enforcement  
❌ Dual authorization not implemented  
❌ Insecure session management  

### Recommendations

**Immediate (Block Deployment):**
1. Implement global authentication middleware
2. Add ownership verification to all resource endpoints
3. Enforce entitlement checks on payments
4. Complete dual authorization for business payments

**Before Production Release:**
5. Migrate to HTTP-only secure cookies
6. Regenerate sessions after privilege elevation
7. Add database locking to prevent race conditions
8. Enable rate limiting

**Defense-in-Depth:**
9. Add security headers middleware
10. Implement CSRF protection
11. Validate production configuration on startup
12. Set up automated security testing in CI/CD

---

**Report Generated:** 2026-11-22 10:30:00 UTC  
**Next Review:** After remediation (target: 2026-12-06)
