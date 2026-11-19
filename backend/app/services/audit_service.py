from sqlalchemy.orm import Session
from app.repositories.audit_repository import AuditRepository
from app.common.enums import AuditEventType, AuditSeverity


class AuditService:
    """Service for audit logging."""

    def __init__(self, db: Session):
        self.audit_repo = AuditRepository(db)

    def log_auth_login_succeeded(
        self,
        correlation_id: str,
        auth_session_id: int,
        user_identity_id: int,
        payload: dict | None = None
    ) -> None:
        """Log successful authentication."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type="auth_session",
            entity_id=str(auth_session_id),
            event_type=AuditEventType.AUTH_LOGIN_SUCCEEDED.value,
            severity=AuditSeverity.INFO.value,
            payload=payload
        )

    def log_auth_login_failed(
        self,
        correlation_id: str,
        username: str,
        payload: dict | None = None
    ) -> None:
        """Log failed authentication attempt."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=None,
            user_identity_id=None,
            entity_type="user_identity",
            entity_id=username,
            event_type=AuditEventType.AUTH_LOGIN_FAILED.value,
            severity=AuditSeverity.WARNING.value,
            payload=payload
        )

    def log_auth_logout(
        self,
        correlation_id: str,
        auth_session_id: int,
        user_identity_id: int
    ) -> None:
        """Log user logout."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type="auth_session",
            entity_id=str(auth_session_id),
            event_type=AuditEventType.AUTH_LOGOUT.value,
            severity=AuditSeverity.INFO.value
        )

    def log_step_up_verified(
        self,
        correlation_id: str,
        auth_session_id: int,
        user_identity_id: int,
        challenge_id: int,
        method: str
    ) -> None:
        """Log successful step-up authentication."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type="step_up_challenge",
            entity_id=str(challenge_id),
            event_type=AuditEventType.STEP_UP_VERIFIED.value,
            severity=AuditSeverity.INFO.value,
            payload={"method": method}
        )

    def log_step_up_locked(
        self,
        correlation_id: str,
        auth_session_id: int,
        user_identity_id: int,
        challenge_id: int,
        attempts_used: int
    ) -> None:
        """Log step-up authentication lockout."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type="step_up_challenge",
            entity_id=str(challenge_id),
            event_type=AuditEventType.STEP_UP_LOCKED.value,
            severity=AuditSeverity.WARNING.value,
            payload={"attempts_used": attempts_used}
        )

    def log_payment_prepared(
        self,
        correlation_id: str,
        auth_session_id: int,
        user_identity_id: int,
        payment_instruction_id: int,
        amount_minor: int,
        payee_id: int
    ) -> None:
        """Log payment preparation."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type="payment_instruction",
            entity_id=str(payment_instruction_id),
            event_type=AuditEventType.PAYMENT_PREPARED.value,
            severity=AuditSeverity.INFO.value,
            payload={"amount_minor": amount_minor, "payee_id": payee_id}
        )

    def log_payment_held(
        self,
        correlation_id: str,
        auth_session_id: int,
        user_identity_id: int,
        payment_instruction_id: int,
        hold_reason: str | None
    ) -> None:
        """Log payment held by fraud."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type="payment_instruction",
            entity_id=str(payment_instruction_id),
            event_type=AuditEventType.PAYMENT_HELD.value,
            severity=AuditSeverity.WARNING.value,
            payload={"hold_reason": hold_reason}
        )

    def log_payment_approved(
        self,
        correlation_id: str,
        auth_session_id: int,
        user_identity_id: int,
        payment_instruction_id: int,
        challenge_id: int
    ) -> None:
        """Log payment approval."""
        self.audit_repo.create_audit_log(
            correlation_id=correlation_id,
            auth_session_id=auth_session_id,
            user_identity_id=user_identity_id,
            entity_type="payment_instruction",
            entity_id=str(payment_instruction_id),
            event_type=AuditEventType.PAYMENT_APPROVED.value,
            severity=AuditSeverity.INFO.value,
            payload={"challenge_id": challenge_id}
        )
