"""
ORM models for all database tables.
Import all models here so Alembic can discover them.
"""
from app.models.account_read_model import AccountReadModel
from app.models.audit_event import AuditEvent
from app.models.authentication_event import AuthenticationEvent
from app.models.capability_status_record import CapabilityStatusRecord
from app.models.consumed_event import ConsumedEvent
from app.models.customer_profile_ref import CustomerProfileRef
from app.models.device_registration import DeviceRegistration
from app.models.dynamic_link_approval import DynamicLinkApproval
from app.models.entitlement_decision import EntitlementDecision
from app.models.idempotency_record import IdempotencyRecord
from app.models.notification_delivery_attempt import NotificationDeliveryAttempt
from app.models.notification_trigger_record import NotificationTriggerRecord
from app.models.payee import Payee
from app.models.payment_execution_status import PaymentExecutionStatus
from app.models.payment_intent import PaymentIntent
from app.models.payment_outbox_event import PaymentOutboxEvent
from app.models.payment_state_transition import PaymentStateTransition
from app.models.payment_status_projection import PaymentStatusProjection
from app.models.read_model_freshness_record import ReadModelFreshnessRecord
from app.models.sandbox_credential import SandboxCredential
from app.models.sandbox_entitlement import SandboxEntitlement
from app.models.scam_check_outcome import ScamCheckOutcome
from app.models.user_session import UserSession

__all__ = [
    "AccountReadModel",
    "AuditEvent",
    "AuthenticationEvent",
    "CapabilityStatusRecord",
    "ConsumedEvent",
    "CustomerProfileRef",
    "DeviceRegistration",
    "DynamicLinkApproval",
    "EntitlementDecision",
    "IdempotencyRecord",
    "NotificationDeliveryAttempt",
    "NotificationTriggerRecord",
    "Payee",
    "PaymentExecutionStatus",
    "PaymentIntent",
    "PaymentOutboxEvent",
    "PaymentStateTransition",
    "PaymentStatusProjection",
    "ReadModelFreshnessRecord",
    "SandboxCredential",
    "SandboxEntitlement",
    "ScamCheckOutcome",
    "UserSession",
]
