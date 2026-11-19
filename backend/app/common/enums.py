from enum import Enum


class UserStatus(str, Enum):
    """User identity status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"


class SessionState(str, Enum):
    """Authentication session state."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class ChallengeType(str, Enum):
    """Step-up challenge type."""
    LOGIN_STEP_UP = "login_step_up"
    PAYEE_ACTION = "payee_action"
    PAYMENT_APPROVAL = "payment_approval"


class ChallengeMethod(str, Enum):
    """Step-up challenge method."""
    PASSCODE = "passcode"
    BIOMETRIC = "biometric"
    DYNAMIC_LINK = "dynamic_link"


class ChallengeStatus(str, Enum):
    """Step-up challenge status."""
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"
    LOCKED = "locked"


class ProfileType(str, Enum):
    """User profile type."""
    PERSONAL = "personal"
    BUSINESS = "business"


class AccountType(str, Enum):
    """Account type."""
    CURRENT_ACCOUNT = "current_account"
    SAVINGS_ACCOUNT = "savings_account"
    CREDIT_CARD = "credit_card"
    LOAN = "loan"
    BUSINESS_ACCOUNT = "business_account"


class FreshnessState(str, Enum):
    """Data freshness state."""
    CURRENT = "current"
    DELAYED = "delayed"
    UNAVAILABLE = "unavailable"


class CoPResultCode(str, Enum):
    """Confirmation of Payee result code."""
    MATCH = "match"
    CLOSE_MATCH = "close_match"
    NO_MATCH = "no_match"
    UNAVAILABLE = "unavailable"


class CoPDecisionState(str, Enum):
    """Confirmation of Payee decision state."""
    PENDING = "pending"
    CONFIRMED = "confirmed"


class InstructionState(str, Enum):
    """Payment instruction state."""
    PREPARED = "prepared"
    HELD = "held"
    APPROVED = "approved"
    SENT = "sent"
    PENDING = "pending"
    FAILED = "failed"


class FraudDecisionCode(str, Enum):
    """Fraud decision code."""
    ALLOW = "allow"
    WARN = "warn"
    STEP_UP = "step_up"
    HOLD = "hold"


class PaymentStatusCode(str, Enum):
    """Payment status code."""
    SENT = "sent"
    PENDING = "pending"
    FAILED = "failed"


class NotificationType(str, Enum):
    """Notification type."""
    PAYMENT_SENT = "payment_sent"
    PAYMENT_FAILED = "payment_failed"
    SECURITY_ALERT = "security_alert"
    SCA_REQUIRED = "sca_required"


class DispatchState(str, Enum):
    """Notification dispatch state."""
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class AuditEventType(str, Enum):
    """Audit event type."""
    AUTH_LOGIN_SUCCEEDED = "AUTH_LOGIN_SUCCEEDED"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    STEP_UP_VERIFIED = "STEP_UP_VERIFIED"
    STEP_UP_LOCKED = "STEP_UP_LOCKED"
    PAYEE_CREATED = "PAYEE_CREATED"
    PAYEE_WARNING_PRESENTED = "PAYEE_WARNING_PRESENTED"
    PAYEE_WARNING_CONFIRMED = "PAYEE_WARNING_CONFIRMED"
    PAYMENT_PREPARED = "PAYMENT_PREPARED"
    PAYMENT_HELD = "PAYMENT_HELD"
    PAYMENT_APPROVED = "PAYMENT_APPROVED"
    PAYMENT_SENT = "PAYMENT_SENT"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_FAILED = "PAYMENT_FAILED"


class AuditSeverity(str, Enum):
    """Audit severity level."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class JourneyStep(str, Enum):
    """Journey step names."""
    SIGN_IN = "sign_in"
    PROVE_IDENTITY = "prove_identity"
    SEE_ACCOUNTS = "see_accounts"
    CHOOSE_PAYEE = "choose_payee"
    ENTER_APPROVE = "enter_approve"
    PAYMENT_SENT = "payment_sent"


class JourneyOutcomeCode(str, Enum):
    """Journey step outcome code."""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    BLOCKED = "blocked"
