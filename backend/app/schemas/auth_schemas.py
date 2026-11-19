"""Authentication and session API schemas"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# Sign-in request/response (FR-001)
class SignInRequest(BaseModel):
    """Username and password sign-in request"""
    username: str = Field(..., min_length=1, description="Customer username or email")
    password: str = Field(..., min_length=1, description="Customer password")
    device_id: str | None = Field(None, description="Device ID if registered device")


class SignInResponse(BaseModel):
    """Sign-in response - password_only auth level"""
    session_id: str
    customer_id: str
    auth_level: str  # 'password_only'
    requires_proof: bool
    proof_methods: list[str]  # ['passcode', 'biometric']
    proof_deadline: datetime | None


# Proof submission request/response (FR-002)
class ProofRequest(BaseModel):
    """Second-factor proof submission"""
    session_id: str
    proof_type: str  # 'passcode' or 'biometric'
    proof_value: str | None = Field(None, description="Passcode digits or biometric attestation")
    device_id: str | None = Field(None, description="Device ID for biometric proof")


class ProofResponse(BaseModel):
    """Proof submission response"""
    session_id: str
    auth_level: str  # 'proven' on success
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    active_profile_id: str | None


# Step-up challenge request/response
class StepUpChallengeRequest(BaseModel):
    """Create a step-up challenge for sensitive actions"""
    purpose: str  # 'payment_approval', 'payee_change'
    context: dict[str, object] = Field(default_factory=dict, description="Context to bind challenge to")


class StepUpChallengeResponse(BaseModel):
    """Step-up challenge created"""
    challenge_reference: str
    method: str
    expires_at: datetime


class VerifyStepUpRequest(BaseModel):
    """Verify a step-up challenge"""
    proof_type: str  # 'passcode' or 'biometric'
    proof_value: str | None
    device_id: str | None


class VerifyStepUpResponse(BaseModel):
    """Step-up verification result"""
    result: str  # 'passed' or 'failed'
    auth_level: str


# Session extension
class ExtendSessionResponse(BaseModel):
    """Session extension response"""
    session_id: str
    expires_at: datetime
    inactivity_timeout_seconds: int


# Sign-out response
class SignOutResponse(BaseModel):
    """Sign-out confirmation"""
    message: str


# Recovery request/response
class RecoveryRequest(BaseModel):
    """Account recovery initiation"""
    username: str


class RecoveryResponse(BaseModel):
    """Recovery initiated"""
    message: str
    recovery_reference: str | None


# Session info (for token payload)
class SessionInfo(BaseModel):
    """Current session information"""
    session_id: str
    customer_id: str
    auth_level: str
    active_profile_id: str | None
    device_id: str | None

    model_config = ConfigDict(from_attributes=True)
