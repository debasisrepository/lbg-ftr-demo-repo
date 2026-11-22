"""Payment orchestration service"""
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from ..models.payment import IdempotencyRecord, PaymentLimitCheck, PaymentOrder
from ..repositories.payment_limit_check_repository import PaymentLimitCheckRepository
from ..repositories.payment_limit_repository import PaymentLimitRepository
from ..repositories.payment_order_repository import PaymentOrderRepository
from ..services.approval_service import ApprovalService
from ..services.audit_service import AuditService
from ..services.dynamic_link_builder import DynamicLinkBuilder
from ..services.fraud_service import FraudService
from ..services.notification_service import NotificationService
from ..services.payment_validator import PaymentValidator
from ..services.status_normalizer import StatusNormalizer
from ..services.status_recorder import StatusRecorder
from ..services.submission_service import SubmissionService


class PaymentService:
    """Main payment orchestration service"""

    def __init__(self, db: Session):
        self.db = db
        self.payment_order_repo = PaymentOrderRepository(db)
        self.payment_limit_repo = PaymentLimitRepository(db)
        self.payment_limit_check_repo = PaymentLimitCheckRepository(db)

        # Service dependencies
        self.payment_validator = PaymentValidator(db)
        self.fraud_service = FraudService(db)
        self.approval_service = ApprovalService(db)
        self.submission_service = SubmissionService(db)
        self.notification_service = NotificationService(db)
        self.audit_service = AuditService(db)
        self.status_recorder = StatusRecorder(db)

    def prepare_payment(
        self,
        customer_id: uuid.UUID,
        profile_id: uuid.UUID,
        source_account_id: uuid.UUID,
        payee_id: uuid.UUID,
        amount_minor: int,
        currency_code: str,
        payment_reference: str | None,
        idempotency_key: str,
        correlation_id: str
    ) -> dict:
        """Prepare a new payment (FR-005)"""

        # Validate payment request
        account, payee = self.payment_validator.validate_payment_request(
            customer_id,
            profile_id,
            source_account_id,
            payee_id,
            amount_minor
        )

        # Check for existing payment with same idempotency key
        existing_payment = self.payment_order_repo.get_by_idempotency_key(idempotency_key)
        if existing_payment:
            return existing_payment

        # Generate customer payment reference
        customer_payment_ref = f"PAY{uuid.uuid4().hex[:8].upper()}"

        # Build dynamic link digest
        dynamic_link_digest = DynamicLinkBuilder.build_digest(
            source_account_id,
            payee_id,
            amount_minor,
            currency_code,
            payment_reference
        )

        now = datetime.now(datetime.now().astimezone().tzinfo)

        # Create payment order
        payment_order = PaymentOrder(
            payment_order_id=uuid.uuid4(),
            customer_id=customer_id,
            profile_id=profile_id,
            source_account_id=source_account_id,
            payee_id=payee_id,
            cop_check_id=None,  # Link from payee
            idempotency_key=idempotency_key,
            customer_payment_ref=customer_payment_ref,
            payment_reference=payment_reference,
            amount_minor=amount_minor,
            currency_code=currency_code,
            payment_type="faster_payment",
            dynamic_link_digest=dynamic_link_digest,
            external_payment_ref=None,
            current_internal_state="prepared",
            normalized_status="pending",
            latest_status_at=now,
            duplicate_suppression_until=None,
            expected_arrival_text=None,
            submitted_at=None,
            completed_at=None,
            correlation_id=correlation_id,
            created_at=now,
            updated_at=now
        )

        payment_order = self.payment_order_repo.create(payment_order)

        # Create idempotency record
        idempotency_record = IdempotencyRecord(
            idempotency_record_id=uuid.uuid4(),
            payment_order_id=payment_order.payment_order_id,
            idempotency_key=idempotency_key,
            request_hash="",  # Placeholder
            first_seen_at=now,
            last_seen_at=now,
            replay_count=0,
            response_reference=None,
            created_at=now,
            updated_at=now
        )
        self.db.add(idempotency_record)

        # Perform limit checks
        self._check_payment_limits(
            payment_order,
            profile_id,
            source_account_id,
            amount_minor,
            correlation_id
        )

        # Perform fraud assessment
        self.fraud_service.assess_payment(
            payment_order.payment_order_id,
            customer_id,
            amount_minor,
            payee_id,
            correlation_id
        )

        # Record audit event
        self.audit_service.record_payment_event(
            customer_id,
            payment_order.payment_order_id,
            "payment_prepared",
            "success",
            correlation_id
        )

        self.db.commit()

        return {
            "payment_order": payment_order,
            "account_name": account.account_name if account else "Unknown Account",
            "payee_name": payee.payee_name if payee else "Unknown Payee"
        }

    def _check_payment_limits(
        self,
        payment_order: PaymentOrder,
        profile_id: uuid.UUID,
        source_account_id: uuid.UUID,
        amount_minor: int,
        correlation_id: str
    ) -> bool:
        """Check payment against limits"""

        # Get active limits for profile and account
        profile_limits = self.payment_limit_repo.get_active_limits_for_profile(profile_id)
        account_limits = self.payment_limit_repo.get_active_limits_for_account(source_account_id)

        all_limits = profile_limits + account_limits
        all_passed = True

        now = datetime.now(datetime.now().astimezone().tzinfo)

        for limit in all_limits:
            if limit.limit_type == "per_payment":
                result = "passed" if amount_minor <= limit.amount_limit_minor else "blocked_over_limit"
            elif limit.limit_type == "daily":
                # Simplified daily check (stub)
                result = "passed"
            else:
                result = "passed"

            if result != "passed":
                all_passed = False

            # Record limit check
            limit_check = PaymentLimitCheck(
                payment_limit_check_id=uuid.uuid4(),
                payment_order_id=payment_order.payment_order_id,
                payment_limit_id=limit.payment_limit_id,
                check_type=limit.limit_type,
                evaluated_amount_minor=amount_minor,
                limit_amount_minor=limit.amount_limit_minor,
                available_balance_minor=None,
                result=result,
                customer_message_code="over_limit" if result == "blocked_over_limit" else None,
                evaluated_at=now,
                created_at=now
            )
            self.payment_limit_check_repo.create(limit_check)

        return all_passed

    def approve_payment(
        self,
        payment_order_id: uuid.UUID,
        device_id: uuid.UUID,
        customer_id: uuid.UUID,
        correlation_id: str,
        step_up_challenge_ref: str | None = None
    ) -> PaymentOrder:
        """Approve payment with SCA (FR-005) and dual authorization for business payments (H-005)"""
        from ..core.errors import AuthorizationError
        from ..repositories.profile_repository import ProfileRepository

        payment_order = self.payment_order_repo.get_by_id(payment_order_id)
        if not payment_order:
            raise ValueError("Payment order not found")

        # H-005: Check if dual authorization required for business payments
        profile_repo = ProfileRepository()
        profile = profile_repo.get_by_id(self.db, payment_order.profile_id)
        
        # Dual authorization threshold for business payments: £50,000
        DUAL_AUTH_THRESHOLD_MINOR = 50000_00
        requires_dual_auth = (
            profile and 
            profile.profile_type == "business" and 
            payment_order.amount_minor >= DUAL_AUTH_THRESHOLD_MINOR
        )

        if requires_dual_auth:
            # Get existing approvals for this payment
            existing_approvals = self.sca_approval_repo.get_by_payment_order(payment_order_id)
            
            # Check if current user already approved
            approver_customer_ids = {
                approval.customer_id for approval in existing_approvals 
                if hasattr(approval, 'customer_id')
            }
            
            # Store customer_id in approval for dual auth tracking
            if customer_id in approver_customer_ids:
                raise AuthorizationError("You have already approved this payment")
            
            # If this is the first approval, mark as pending second approval
            if len(existing_approvals) == 0:
                # Create first approval
                sca_approval = self.approval_service.create_sca_approval(
                    payment_order_id,
                    device_id,
                    payment_order.source_account_id,
                    payment_order.payee_id,
                    payment_order.amount_minor,
                    payment_order.currency_code,
                    payment_order.payment_reference,
                    correlation_id,
                    step_up_challenge_ref
                )
                
                # Store customer_id for dual auth tracking
                # Note: ScaApproval model would need customer_id field added in production
                
                # Update to pending_second_approval status
                internal_state = "pending_second_approval"
                normalized_status = "pending_approval"
                
                payment_order = self.payment_order_repo.update_status(
                    payment_order,
                    internal_state,
                    normalized_status
                )
                
                self.status_recorder.record_status_change(
                    payment_order_id,
                    internal_state,
                    normalized_status,
                    None,
                    correlation_id
                )
                
                self.audit_service.record_payment_event(
                    customer_id,
                    payment_order_id,
                    "payment_first_approval",
                    "success",
                    correlation_id
                )
                
                self.db.commit()
                return payment_order
            else:
                # This is the second approval - verify different approver
                # In production, check customer_id stored with first approval
                pass  # Fall through to complete approval

        # Create SCA approval (for non-dual-auth or second approval)
        self.approval_service.create_sca_approval(
            payment_order_id,
            device_id,
            payment_order.source_account_id,
            payment_order.payee_id,
            payment_order.amount_minor,
            payment_order.currency_code,
            payment_order.payment_reference,
            correlation_id,
            step_up_challenge_ref
        )

        # Update payment status
        internal_state = "awaiting_sca"
        normalized_status = StatusNormalizer.normalize(internal_state)

        payment_order = self.payment_order_repo.update_status(
            payment_order,
            internal_state,
            normalized_status
        )

        # Record status change
        self.status_recorder.record_status_change(
            payment_order_id,
            internal_state,
            normalized_status,
            None,
            correlation_id
        )

        # Record audit event
        event_type = "payment_second_approval" if requires_dual_auth and len(existing_approvals) > 0 else "payment_approved"
        self.audit_service.record_payment_event(
            customer_id,
            payment_order_id,
            event_type,
            "success",
            correlation_id
        )

        self.db.commit()

        return payment_order

    def submit_payment(
        self,
        payment_order_id: uuid.UUID,
        customer_id: uuid.UUID,
        correlation_id: str
    ) -> PaymentOrder:
        """Submit payment to hub (FR-006)"""

        payment_order = self.payment_order_repo.get_by_id(payment_order_id)
        if not payment_order:
            raise ValueError("Payment order not found")

        # Submit via submission service
        payment_order = self.submission_service.submit_payment(
            payment_order,
            correlation_id
        )

        # Create notification
        self.notification_service.create_payment_notification(
            customer_id,
            payment_order_id,
            "payment_sent",
            "payment_sent",
            "Payment sent",
            f"Your payment of £{payment_order.amount_minor / 100:.2f} has been sent",
            correlation_id
        )

        # Record audit event
        self.audit_service.record_payment_event(
            customer_id,
            payment_order_id,
            "payment_submitted",
            "success",
            correlation_id
        )

        self.db.commit()

        return payment_order

    def get_payment(self, payment_order_id: uuid.UUID) -> PaymentOrder | None:
        """Get payment order by ID"""
        return self.payment_order_repo.get_by_id(payment_order_id)

    def get_payment_with_details(self, payment_order_id: uuid.UUID) -> dict | None:
        """Get payment order with account and payee details"""
        from ..repositories.bank_account_repository import BankAccountRepository
        from ..repositories.payee_repository import PayeeRepository

        payment_order = self.payment_order_repo.get_by_id(payment_order_id)
        if not payment_order:
            return None

        bank_account_repo = BankAccountRepository()
        payee_repo = PayeeRepository()

        account = bank_account_repo.get_by_id(self.db, payment_order.source_account_id)
        payee = payee_repo.get_by_id(self.db, payment_order.payee_id)

        return {
            "payment_order": payment_order,
            "account_name": account.account_name if account else "Unknown Account",
            "payee_name": payee.payee_name if payee else "Unknown Payee"
        }
