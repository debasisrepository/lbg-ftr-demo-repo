"""Authentication and session router (FR-001, FR-002)"""
import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..core.middleware import get_correlation_id
from ..database import get_db
from ..models.notification import CustomerNotification
from ..schemas.auth_schemas import (
    ExtendSessionResponse,
    ProofRequest,
    ProofResponse,
    RecoveryRequest,
    RecoveryResponse,
    SignInRequest,
    SignInResponse,
    SignOutResponse,
    StepUpChallengeRequest,
    StepUpChallengeResponse,
    VerifyStepUpRequest,
    VerifyStepUpResponse,
)
from ..services.auth_service import AuthService
from ..services.session_service import SessionService
from ..services.step_up_service import StepUpService

router = APIRouter()


@router.post("/sign-in", response_model=SignInResponse)
def sign_in(
    request_body: SignInRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> SignInResponse:
    """
    Sign in with username and password (FR-001).
    Returns password_only auth level requiring proof submission.
    """
    correlation_id = get_correlation_id(request)
    client_ip = request.client.host if request.client else None

    auth_service = AuthService(db)
    return auth_service.sign_in(request_body, client_ip, correlation_id)


@router.post("/proof", response_model=ProofResponse)
def submit_proof(
    request_body: ProofRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> ProofResponse:
    """
    Submit second-factor proof (FR-002).
    Verifies passcode or biometric and upgrades session to proven auth level.
    """
    correlation_id = get_correlation_id(request)

    auth_service = AuthService(db)
    return auth_service.submit_proof(request_body, correlation_id)


@router.post("/step-up", response_model=StepUpChallengeResponse)
def create_step_up_challenge(
    request_body: StepUpChallengeRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> StepUpChallengeResponse:
    """
    Create a step-up challenge for sensitive actions (payment approval, payee change).
    Requires proven session.
    """
    correlation_id = get_correlation_id(request)

    # TODO: Extract session_id from JWT token (requires auth middleware)
    # For now, expect it in the request context or header
    session_id_str = request.headers.get("X-Session-ID")
    if not session_id_str:
        from ..core.errors import AuthenticationError
        raise AuthenticationError("Session ID required")

    session_id = uuid.UUID(session_id_str)

    step_up_service = StepUpService(db)
    return step_up_service.create_challenge(session_id, request_body, correlation_id)


@router.post("/step-up/{challenge_reference}/verify", response_model=VerifyStepUpResponse)
def verify_step_up(
    challenge_reference: str,
    request_body: VerifyStepUpRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> VerifyStepUpResponse:
    """
    Verify a step-up challenge with passcode or biometric proof.
    """
    correlation_id = get_correlation_id(request)

    step_up_service = StepUpService(db)
    return step_up_service.verify_challenge(challenge_reference, request_body, correlation_id)


@router.post("/session/extend", response_model=ExtendSessionResponse)
def extend_session(
    request: Request,
    db: Session = Depends(get_db)
) -> ExtendSessionResponse:
    """
    Extend session expiry (reset inactivity timeout).
    Requires valid session.
    """
    # TODO: Extract session_id from JWT token (requires auth middleware)
    session_id_str = request.headers.get("X-Session-ID")
    if not session_id_str:
        from ..core.errors import AuthenticationError
        raise AuthenticationError("Session ID required")

    session_id = uuid.UUID(session_id_str)

    session_service = SessionService(db)
    return session_service.extend_session(session_id)


@router.post("/sign-out", response_model=SignOutResponse)
def sign_out(
    request: Request,
    db: Session = Depends(get_db)
) -> SignOutResponse:
    """
    Sign out and end session.
    """
    # TODO: Extract session_id from JWT token (requires auth middleware)
    session_id_str = request.headers.get("X-Session-ID")
    if not session_id_str:
        # If no session, already signed out
        return SignOutResponse(message="Signed out successfully")

    session_id = uuid.UUID(session_id_str)

    session_service = SessionService(db)
    return session_service.sign_out(session_id)


@router.post("/recovery", response_model=RecoveryResponse)
def start_recovery(
    request_body: RecoveryRequest,
    request: Request,
    db: Session = Depends(get_db)
) -> RecoveryResponse:
    """
    Start account recovery flow.
    Creates a recovery challenge and sends notification.
    """
    import uuid
    from datetime import datetime, timedelta

    from ..models.session import StepUpChallenge
    from ..repositories.customer_repository import CustomerRepository
    from ..services.notification_service import NotificationService

    correlation_id = getattr(request.state, "correlation_id", str(uuid.uuid4()))

    # Find customer by username (email)
    customer_repo = CustomerRepository(db)
    customer = customer_repo.get_by_external_identity_ref(request_body.username)

    if not customer:
        # Don't reveal whether username exists - return success anyway
        return RecoveryResponse(
            message="If an account exists with that email, recovery instructions have been sent.",
            recovery_reference=None
        )

    # Create recovery challenge
    now = datetime.now(datetime.now().astimezone().tzinfo)
    recovery_challenge = StepUpChallenge(
        step_up_challenge_id=uuid.uuid4(),
        customer_id=customer.customer_id,
        session_id=None,  # No active session during recovery
        purpose="sign_in_recovery",
        method="email",
        issued_at=now,
        expires_at=now + timedelta(hours=24),
        result="issued",
        attempt_count=0,
        correlation_id=correlation_id
    )

    db.add(recovery_challenge)
    db.flush()

    # Send notification
    NotificationService(db)
    notification = CustomerNotification(
        customer_notification_id=uuid.uuid4(),
        customer_id=customer.customer_id,
        notification_type="credential_recovery",
        channel="email",
        template_code="RECOVERY_LINK",
        title="Account Recovery Request",
        body_summary=f"Recovery link: {recovery_challenge.step_up_challenge_id}",
        delivery_state="queued",
        correlation_id=correlation_id,
        support_case_reference=None,
        dispatched_at=None,
        read_at=None,
        provider_reference=None
    )

    db.add(notification)
    db.commit()

    return RecoveryResponse(
        message="If an account exists with that email, recovery instructions have been sent.",
        recovery_reference=str(recovery_challenge.step_up_challenge_id)
    )
