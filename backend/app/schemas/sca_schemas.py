from pydantic import BaseModel, Field


class StepUpVerifyRequest(BaseModel):
    """Step-up authentication verification request."""
    session_id: int
    method: str = Field(..., pattern="^(passcode|biometric)$")
    passcode: str | None = Field(None, min_length=6, max_length=6)
    biometric_assertion: str | None = None
    device_id: str | None = None


class StepUpVerifyResponse(BaseModel):
    """Step-up authentication verification response."""
    status: str
    session_id: int
    step_up_verified: bool
    remaining_attempts: int | None = None
    next_route: str
    available_methods: list[str]
