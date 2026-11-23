"""
PaymentOrchestrationService - payment state machine and orchestration.
Requirement: REQ-PAY-002, REQ-PAY-003, REQ-PAY-004, REQ-PAY-005, REQ-PAY-006, REQ-PAY-007
"""
import hashlib
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.adapters.ciam_sandbox_adapter import CIAMSandboxAdapter
from app.adapters.entitlement_sandbox_adapter import EntitlementSandboxAdapter
from app.adapters.fraud_engine_sandbox_adapter import FraudEngineSandboxAdapter
from app.adapters.payments_hub_adapter import PaymentsHubAdapter
from app.models.account_read_model import AccountReadModel
from app.models.audit_event import AuditEvent
from app.models.authentication_event import AuthenticationEvent
from app.models.dynamic_link_approval import DynamicLinkApproval
from app.models.idempotency_record import IdempotencyRecord
from app.models.payee import Payee
from app.models.payment_intent import PaymentIntent
from app.models.payment_outbox_event import PaymentOutboxEvent
from app.models.sandbox_credential import SandboxCredential
from app.models.scam_check_outcome import ScamCheckOutcome
from app.repositories.capability_status_repository import CapabilityStatusRepository
from app.repositories.dynamic_link_approval_repository import (
    DynamicLinkApprovalRepository,
)
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.payment_execution_status_repository import (
    PaymentExecutionStatusRepository,
)
from app.repositories.payment_outbox_repository import PaymentOutboxRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.scam_check_repository import ScamCheckRepository
from app.schemas.payments_schemas import (
    PaymentAccountSummary,
    PaymentChangeRequest,
    PaymentCreateRequest,
    PaymentListResponse,
    PaymentPayeeSummary,
    PaymentResponse,
    PaymentSubmitRequest,
    PaymentWarning,
    WarningDecisionRequest,
)


class PaymentOrchestrationService:
    """Service for payment state machine and orchestration."""
    
    def __init__(self, db: Session):
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.idempotency_repo = IdempotencyRepository(db)
        self.approval_repo = DynamicLinkApprovalRepository(db)
        self.scam_check_repo = ScamCheckRepository(db)
        self.outbox_repo = PaymentOutboxRepository(db)
        self.execution_status_repo = PaymentExecutionStatusRepository(db)
        self.entitlement_adapter = EntitlementSandboxAdapter(db)
        self.ciam_adapter = CIAMSandboxAdapter()
        self.fraud_adapter = FraudEngineSandboxAdapter(availability=1.0)
        self.payments_hub_adapter = PaymentsHubAdapter(response_delay_ms=500)
        self.capability_repo = CapabilityStatusRepository(db)
    
    def _compute_review_fingerprint(
        self,
        source_account_reference: str,
        payee_id: uuid.UUID,
        amount_minor: int,
        currency: str,
        payment_reference: str,
        review_version: int
    ) -> str:
        """
        Compute SHA-256 fingerprint over dynamic-linked fields plus review version.
        
        Args:
            source_account_reference: Source account system reference
            payee_id: Payee ID
            amount_minor: Amount in minor units
            currency: Currency code
            payment_reference: Payment reference
            review_version: Review version
        
        Returns:
            64-character hex SHA-256 fingerprint
        """
        canonical = f"{source_account_reference}|{payee_id!s}|{amount_minor}|{currency}|{payment_reference}|{review_version}"
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    def _compute_request_fingerprint(self, request_dict: dict) -> str:
        """
        Compute SHA-256 fingerprint of canonical request body.
        
        Args:
            request_dict: Request body as dict
        
        Returns:
            64-character hex SHA-256 fingerprint
        """
        # Sort keys for canonical representation
        canonical = "|".join(f"{k}:{v}" for k, v in sorted(request_dict.items()))
        return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    
    def _converge_customer_visible_status(self, state: str) -> str | None:
        """
        ONE status convergence function - maps internal state to customer-visible status.
        This is the single place where customer_visible_status is computed.
        
        Args:
            state: Current payment internal state
        
        Returns:
            One of "Sent", "Pending", "Failed", or None (not submitted yet)
        """
        # Sent: completed only
        if state == "completed":
            return "Sent"
        
        # Pending: held or in-flight states with do-not-resubmit
        if state in ["held_for_review", "submission_in_progress", "submitted_to_payments_hub",
                     "pending_confirmation", "unknown_unresolved"]:
            return "Pending"
        
        # Failed: rejected or failed
        if state in ["failed", "rejected"]:
            return "Failed"
        
        # Not submitted yet - no customer-visible status
        # States: draft, review_ready, awaiting_dynamic_link_approval, approval_failed_or_abandoned,
        #         fraud_check_in_progress, warning_presented, stopped_after_warning
        return None
    
    def _get_status_message(self, state: str, is_submitted: bool) -> str:
        """
        Get plain-language status message for current state.
        
        Args:
            state: Current payment state
            is_submitted: Whether payment has been submitted
        
        Returns:
            Status message string
        """
        if state == "review_ready":
            return "Payment not sent yet. Review and approve it to send."
        elif state in ["draft", "awaiting_dynamic_link_approval", "approval_failed_or_abandoned",
                       "fraud_check_in_progress", "warning_presented", "stopped_after_warning"]:
            return "Payment not sent. No money was sent."
        elif state == "held_for_review":
            return "We're checking this payment. Don't send this payment again."
        elif state in ["submission_in_progress", "submitted_to_payments_hub", "pending_confirmation", "unknown_unresolved"]:
            return "Payment is being processed. Don't send this payment again."
        elif state == "completed":
            return "Payment sent successfully."
        elif state in ["failed", "rejected"]:
            return "Payment could not be completed."
        else:
            return "Payment status unknown."
    
    def _get_next_action(self, state: str) -> str:
        """
        Get next action hint for app.
        
        Args:
            state: Current payment state
        
        Returns:
            Next action string
        """
        if state == "review_ready":
            return "review_and_approve"
        elif state == "warning_presented":
            return "acknowledge_warning"
        elif state in ["held_for_review", "submission_in_progress", "submitted_to_payments_hub",
                       "pending_confirmation", "unknown_unresolved"]:
            return "check_status"
        elif state in ["approval_failed_or_abandoned", "stopped_after_warning", "failed", "rejected"]:
            return "start_new_payment"
        elif state == "completed":
            return "none"
        else:
            return "none"
    
    def _is_submitted_state(self, state: str) -> bool:
        """Check if state counts as submitted."""
        return state in [
            "held_for_review", "submission_in_progress", "submitted_to_payments_hub",
            "pending_confirmation", "completed", "failed", "rejected", "unknown_unresolved"
        ]
    
    def _build_payment_response(
        self,
        payment: PaymentIntent,
        account: AccountReadModel,
        payee: Payee
    ) -> PaymentResponse:
        """
        Build PaymentResponse from payment intent, account, and payee.
        
        Args:
            payment: PaymentIntent
            account: Source AccountReadModel
            payee: Payee
        
        Returns:
            PaymentResponse
        """
        is_submitted = self._is_submitted_state(payment.current_state)
        
        # Get warning if in warning_presented state
        warning = None
        hold_latest_decision_at = None
        
        if payment.current_state == "warning_presented":
            # Get scam check outcome for warning details
            scam_outcome = self.scam_check_repo.get_by_payment_and_version(
                payment.id, payment.review_version
            )
            if scam_outcome and scam_outcome.customer_warning_required:
                allowed_actions = ["stop"]
                if scam_outcome.policy_allows_continue:
                    allowed_actions.append("continue")
                
                warning = PaymentWarning(
                    heading="Warning: This payment may be unsafe",
                    body="We've detected activity that suggests this payment could be a scam. Please review the payment details carefully. If you're unsure, stop and don't send this payment.",
                    allowed_actions=allowed_actions,
                    policy_allows_continue=scam_outcome.policy_allows_continue
                )
        
        elif payment.current_state == "held_for_review":
            # Get hold decision date
            scam_outcome = self.scam_check_repo.get_by_payment_and_version(
                payment.id, payment.review_version
            )
            if scam_outcome:
                hold_latest_decision_at = scam_outcome.hold_latest_decision_at
        
        # Safely extract expected_arrival_time (handle Mock objects in tests)
        expected_arrival = getattr(payment, 'expected_arrival_time', None)
        if expected_arrival is not None and not isinstance(expected_arrival, datetime):
            expected_arrival = None
        
        return PaymentResponse(
            payment_id=payment.id,
            current_state=payment.current_state,
            next_action=self._get_next_action(payment.current_state),
            customer_visible_status=payment.customer_visible_status,
            status_message=self._get_status_message(payment.current_state, is_submitted),
            is_submitted=is_submitted,
            do_not_resubmit=payment.do_not_resubmit,
            payment_reference=payment.payment_reference_text,
            amount_minor=payment.amount_minor,
            currency=payment.currency,
            source_account=PaymentAccountSummary(
                account_id=account.id,
                display_name=account.display_name,
                masked_account_identifier=account.masked_account_identifier
            ),
            payee=PaymentPayeeSummary(
                payee_id=payee.id,
                payee_name=payee.payee_name,
                masked_account_identifier=payee.masked_account_identifier
            ),
            review_version=payment.review_version,
            review_fingerprint=payment.review_fingerprint,
            warning=warning,
            hold_latest_decision_at=hold_latest_decision_at,
            expected_arrival_time=expected_arrival,
            payee_display_name=payee.payee_name,
            created_at=payment.created_at,
            updated_at=payment.updated_at
        )
    
    def create_payment_review(
        self,
        request: PaymentCreateRequest,
        customer_id: str,
        idempotency_key: str,
        correlation_id: str | None = None
    ) -> tuple[PaymentResponse, bool]:
        """
        Create payment review (E-07).
        
        Returns (PaymentResponse, is_replay) where is_replay=True means idempotent replay.
        
        Args:
            request: PaymentCreateRequest
            customer_id: Customer profile reference ID
            idempotency_key: Client-provided idempotency key
            correlation_id: Optional correlation ID
        
        Returns:
            Tuple of (PaymentResponse, is_replay)
        
        Raises:
            HTTPException: 404, 403, 422, 503
        """
        try:
            # Convert customer_id to UUID
            customer_uuid = uuid.UUID(customer_id) if isinstance(customer_id, str) else customer_id
            
            # Check payments capability
            cap = self.capability_repo.get_current_status("payments")
            if cap and cap.status_value == "unavailable":
                raise HTTPException(
                    status_code=503,
                    detail="Payment service is currently unavailable"
                )
            
            # Get source account
            account = self.payment_repo.get_account_by_id(request.source_account_id, customer_id)
            if not account:
                raise HTTPException(
                    status_code=404,
                    detail="Source account not found"
                )
            
            # Check source account entitlement
            entitlement_decision = self.entitlement_adapter.check_resource_access(
                customer_uuid, "account", str(request.source_account_id)
            )
            if entitlement_decision != "allow":
                raise HTTPException(
                    status_code=403,
                    detail="Not entitled to use this account"
                )
            
            # Get payee
            payee = self.payment_repo.get_payee_by_id(request.payee_id, customer_id)
            if not payee or payee.payee_status != "saved_active":
                raise HTTPException(
                    status_code=404,
                    detail="Payee not found or not active"
                )
            
            # Compute request fingerprint for idempotency
            request_dict = request.model_dump()
            request_fingerprint = self._compute_request_fingerprint(request_dict)
            
            # Compute review fingerprint
            review_fingerprint = self._compute_review_fingerprint(
                account.account_system_reference,
                request.payee_id,
                request.amount_minor,
                request.currency,
                request.payment_reference,
                1  # Initial version
            )
            
            # Check for existing idempotency record first (without payment_intent_id)
            # to handle replay before creating anything
            stmt = select(IdempotencyRecord).where(
                and_(
                    IdempotencyRecord.customer_profile_ref_id == customer_uuid,
                    IdempotencyRecord.operation_type == "payment_review",
                    IdempotencyRecord.idempotency_key == idempotency_key
                )
            )
            existing_idempotency = self.db.execute(stmt).scalar_one_or_none()
            
            if existing_idempotency:
                # Replay - check fingerprint and return existing payment
                if existing_idempotency.request_fingerprint != request_fingerprint:
                    raise ValueError("idempotency_key_reuse")
                
                # Get existing payment
                existing_payment = self.payment_repo.get_by_id(
                    existing_idempotency.payment_intent_id, customer_uuid
                )
                if existing_payment:
                    existing_idempotency.replay_count += 1
                    self.db.commit()
                    response = self._build_payment_response(existing_payment, account, payee)
                    return (response, True)
            
            # New request - create payment first, then idempotency record
            payment = PaymentIntent(
                id=uuid.uuid4(),
                customer_profile_ref_id=customer_uuid,
                source_account_reference=account.account_system_reference,
                payee_id=request.payee_id,
                amount_minor=request.amount_minor,
                currency=request.currency,
                payment_reference_text=request.payment_reference,
                payment_channel="mobile",
                initiation_type="saved_payee_payment",
                review_version=1,
                review_fingerprint=review_fingerprint,
                current_state="review_ready",
                customer_visible_status=None,
                do_not_resubmit=False,
                correlation_id=correlation_id
            )
            
            # Create payment first (so FK constraint satisfied)
            created_payment = self.payment_repo.create(payment)
            
            # Then create idempotency record
            idempotency_record = IdempotencyRecord(
                id=uuid.uuid4(),
                customer_profile_ref_id=customer_uuid,
                operation_type="payment_review",
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                payment_intent_id=created_payment.id,
                resolution_state="resolved_success",
                response_status_code=201,
                returned_response_reference=str(created_payment.id),
                replay_count=0,
                correlation_id=correlation_id
            )
            self.db.add(idempotency_record)
            
            self.db.commit()
            
            response = self._build_payment_response(created_payment, account, payee)
            return (response, False)
        
        except ValueError as e:
            self.db.rollback()
            if str(e) == "idempotency_key_reuse":
                raise HTTPException(
                    status_code=422,
                    detail="Idempotency key reused with different request"
                )
            raise
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in create_payment_review: {e!s}"
            )
    
    def change_payment_review(
        self,
        payment_id: uuid.UUID,
        request: PaymentChangeRequest,
        customer_id: str,
        correlation_id: str | None = None
    ) -> PaymentResponse:
        """
        Change payment review (E-10).
        
        Args:
            payment_id: Payment intent ID
            request: PaymentChangeRequest
            customer_id: Customer profile reference ID
            correlation_id: Optional correlation ID
        
        Returns:
            Updated PaymentResponse
        
        Raises:
            HTTPException: 404, 409, 422
        """
        try:
            # Convert customer_id to UUID
            customer_uuid = uuid.UUID(customer_id) if isinstance(customer_id, str) else customer_id
            
            # Get payment
            payment = self.payment_repo.get_by_id(payment_id, customer_uuid)
            if not payment:
                raise HTTPException(
                    status_code=404,
                    detail="Payment not found"
                )
            
            # Check state allows editing
            if payment.current_state not in ["review_ready", "awaiting_dynamic_link_approval"]:
                raise HTTPException(
                    status_code=409,
                    detail="Payment cannot be edited in current state"
                )
            
            # Check expected review version
            if payment.review_version != request.expected_review_version:
                raise HTTPException(
                    status_code=409,
                    detail="Payment has been changed by another request"
                )
            
            # Get current account and payee
            stmt = select(AccountReadModel).where(
                AccountReadModel.account_system_reference == payment.source_account_reference
            )
            account = self.db.execute(stmt).scalar_one_or_none()
            
            payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
            
            if not account or not payee:
                raise HTTPException(
                    status_code=500,
                    detail="Account or payee lookup failed in change_payment_review"
                )
            
            # Track if any critical field changed
            changed = False
            
            # Apply changes
            if request.source_account_id and request.source_account_id != account.id:
                new_account = self.payment_repo.get_account_by_id(request.source_account_id, customer_uuid)
                if not new_account:
                    raise HTTPException(
                        status_code=404,
                        detail="Source account not found"
                    )
                payment.source_account_reference = new_account.account_system_reference
                changed = True
                account = new_account
            
            if request.payee_id and request.payee_id != payment.payee_id:
                new_payee = self.payment_repo.get_payee_by_id(request.payee_id, customer_uuid)
                if not new_payee or new_payee.payee_status != "saved_active":
                    raise HTTPException(
                        status_code=404,
                        detail="Payee not found or not active"
                    )
                payment.payee_id = request.payee_id
                changed = True
                payee = new_payee
            
            if request.amount_minor and request.amount_minor != payment.amount_minor:
                payment.amount_minor = request.amount_minor
                changed = True
            
            if request.payment_reference and request.payment_reference != payment.payment_reference_text:
                payment.payment_reference_text = request.payment_reference
                changed = True
            
            # If anything changed, increment version and recompute fingerprint
            if changed:
                payment.review_version += 1
                payment.review_fingerprint = self._compute_review_fingerprint(
                    payment.source_account_reference,
                    payment.payee_id,
                    payment.amount_minor,
                    payment.currency,
                    payment.payment_reference_text,
                    payment.review_version
                )
                payment.updated_at = datetime.now(UTC)
            
            updated_payment = self.payment_repo.update(payment)
            self.db.commit()
            
            response = self._build_payment_response(updated_payment, account, payee)
            return response
        
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in change_payment_review: {e!s}"
            )
    
    def approve_and_submit(
        self,
        payment_id: uuid.UUID,
        request: PaymentSubmitRequest,
        customer_id: str,
        idempotency_key: str,
        correlation_id: str | None = None
    ) -> tuple[PaymentResponse, bool]:
        """
        Approve and submit payment (E-11).
        
        This is the approval step only. Fraud checking and submission are added in later tasks.
        For now, successful approval moves to fraud_check_in_progress state.
        Failed/abandoned approval returns approval_failed_or_abandoned.
        
        Returns (PaymentResponse, is_replay) where is_replay=True means idempotent replay.
        
        Args:
            payment_id: Payment intent ID
            request: PaymentSubmitRequest
            customer_id: Customer profile reference ID
            idempotency_key: Client-provided idempotency key
            correlation_id: Optional correlation ID
        
        Returns:
            Tuple of (PaymentResponse, is_replay)
        
        Raises:
            HTTPException: 400, 401, 404, 409, 422, 503
        """
        try:
            customer_uuid = uuid.UUID(customer_id) if isinstance(customer_id, str) else customer_id
            
            # Check payments capability
            cap = self.capability_repo.get_current_status("payments")
            if cap and cap.status_value == "unavailable":
                raise HTTPException(
                    status_code=503,
                    detail="Payment service is currently unavailable"
                )
            
            # Get payment
            payment = self.payment_repo.get_by_id(payment_id, customer_uuid)
            if not payment:
                raise HTTPException(
                    status_code=404,
                    detail="Payment not found"
                )
            
            # Check state allows submission
            if payment.current_state not in ["review_ready", "awaiting_dynamic_link_approval"]:
                raise HTTPException(
                    status_code=400,
                    detail="Payment cannot be submitted in current state"
                )
            
            # Check review version matches
            if payment.review_version != request.review_version:
                raise HTTPException(
                    status_code=409,
                    detail="Review version has changed"
                )
            
            # Check review fingerprint matches
            if payment.review_fingerprint != request.review_fingerprint:
                raise HTTPException(
                    status_code=409,
                    detail="Review fingerprint mismatch"
                )
            
            # Compute request fingerprint for idempotency
            request_dict = request.model_dump()
            request_fingerprint = self._compute_request_fingerprint(request_dict)
            
            # Try to create or get existing idempotency record
            idempotency_record, is_new = self.idempotency_repo.create_or_get_existing(
                customer_id=customer_uuid,
                operation_type="payment_submit",
                idempotency_key=idempotency_key,
                request_fingerprint=request_fingerprint,
                payment_intent_id=payment.id,
                correlation_id=correlation_id
            )
            
            if not is_new:
                # Replay - get current payment state and return
                current_payment = self.payment_repo.get_by_id(payment_id, customer_uuid)
                if current_payment:
                    stmt = select(AccountReadModel).where(
                        AccountReadModel.account_system_reference == current_payment.source_account_reference
                    )
                    account = self.db.execute(stmt).scalar_one_or_none()
                    payee = self.payment_repo.get_payee_by_id(current_payment.payee_id, customer_uuid)
                    
                    if account and payee:
                        response = self._build_payment_response(current_payment, account, payee)
                        return (response, True)
            
            # Get customer's sandbox credentials for passcode verification
            stmt = select(SandboxCredential).where(
                SandboxCredential.customer_profile_ref_id == customer_uuid
            )
            credential = self.db.execute(stmt).scalar_one_or_none()
            
            if not credential:
                raise HTTPException(
                    status_code=401,
                    detail="Authentication failed"
                )
            
            # Move to awaiting approval state
            payment.current_state = "awaiting_dynamic_link_approval"
            payment.updated_at = datetime.now(UTC)
            self.payment_repo.update(payment)
            
            # Request dynamic link approval from CIAM
            approval_result = self.ciam_adapter.create_dynamic_link_approval(
                customer_id=str(customer_uuid),
                passcode=request.approval.passcode,
                passcode_hash=credential.passcode_hash,
                review_fingerprint=payment.review_fingerprint
            )
            
            # Create authentication event
            auth_event = AuthenticationEvent(
                id=uuid.uuid4(),
                customer_profile_ref_id=customer_uuid,
                device_registration_id=None,
                client_address_hash=None,
                authentication_type="dynamic_link_approval",
                outcome="success" if approval_result else "failed",
                failure_category="passcode_mismatch" if not approval_result else None,
                ciam_transaction_reference=None,
                linked_business_action_type="payment_intent",
                linked_business_action_id=payment.id,
                correlation_id=correlation_id if correlation_id else "",
                occurred_at=datetime.now(UTC)
            )
            self.db.add(auth_event)
            
            if not approval_result:
                # Approval failed or abandoned
                payment.current_state = "approval_failed_or_abandoned"
                payment.customer_visible_status = None
                payment.is_submitted = False
                payment.do_not_resubmit = False
                payment.updated_at = datetime.now(UTC)
                self.payment_repo.update(payment)
                
                # Mark idempotency as resolved
                self.idempotency_repo.mark_resolved(
                    idempotency_record,
                    success=True,
                    status_code=200,
                    response_reference=str(payment.id)
                )
                
                self.db.commit()
                
                # Get account and payee for response
                stmt = select(AccountReadModel).where(
                    AccountReadModel.account_system_reference == payment.source_account_reference
                )
                account = self.db.execute(stmt).scalar_one_or_none()
                payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
                
                if not account or not payee:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to load payment details"
                    )
                
                response = self._build_payment_response(payment, account, payee)
                return (response, False)
            
            # Approval succeeded - create approval record
            approval_record = DynamicLinkApproval(
                id=uuid.uuid4(),
                payment_intent_id=payment.id,
                review_version=payment.review_version,
                review_fingerprint=payment.review_fingerprint,
                source_account_reference=payment.source_account_reference,
                payee_id=payment.payee_id,
                approved_amount_minor=payment.amount_minor,
                approved_currency=payment.currency,
                approved_reference_text=payment.payment_reference_text,
                approval_challenge_reference="ciam-challenge-ref",
                signed_approval_reference=f"signed-approval-{payment.id}",
                approval_outcome="success",
                approved_at=datetime.now(UTC),
                correlation_id=correlation_id
            )
            self.approval_repo.create(approval_record)
            
            # Compare approval with canonical intent
            if (approval_record.source_account_reference != payment.source_account_reference or
                approval_record.payee_id != payment.payee_id or
                approval_record.approved_amount_minor != payment.amount_minor or
                approval_record.approved_currency != payment.currency or
                approval_record.approved_reference_text != payment.payment_reference_text or
                approval_record.review_version != payment.review_version or
                approval_record.review_fingerprint != payment.review_fingerprint):
                # Mismatch - reject execution
                payment.current_state = "approval_failed_or_abandoned"
                payment.customer_visible_status = None
                payment.is_submitted = False
                payment.do_not_resubmit = False
                payment.updated_at = datetime.now(UTC)
                self.payment_repo.update(payment)
                
                self.idempotency_repo.mark_resolved(
                    idempotency_record,
                    success=True,
                    status_code=200,
                    response_reference=str(payment.id)
                )
                
                self.db.commit()
                
                stmt = select(AccountReadModel).where(
                    AccountReadModel.account_system_reference == payment.source_account_reference
                )
                account = self.db.execute(stmt).scalar_one_or_none()
                payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
                
                if not account or not payee:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to load payment details"
                    )
                
                response = self._build_payment_response(payment, account, payee)
                return (response, False)
            
            # Approval matches - move to fraud_check_in_progress and call fraud engine
            payment.current_state = "fraud_check_in_progress"
            payment.updated_at = datetime.now(UTC)
            self.payment_repo.update(payment)
            
            # Get payee for fraud decision inputs
            payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
            if not payee:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load payee details"
                )
            
            # Compute payee age in days
            if payee.activated_at:
                # Ensure timezone-aware comparison (SQLite may strip timezone)
                activated = payee.activated_at.replace(tzinfo=UTC) if payee.activated_at.tzinfo is None else payee.activated_at
                payee_age_days = (datetime.now(UTC) - activated).days
            else:
                payee_age_days = 0
            
            # Call fraud decisioning engine
            try:
                fraud_decision, latency_ms, engine_ref, policy_allows_continue = self.fraud_adapter.check_payment_fraud_risk(
                    customer_id=customer_uuid,
                    device_hash="device-hash-placeholder",  # Will come from session in production
                    payee_id=payment.payee_id,
                    payee_age_days=payee_age_days,
                    cop_outcome=payee.cop_outcome_category or "not_checked",
                    amount_minor=payment.amount_minor,
                    currency=payment.currency,
                    correlation_id=correlation_id or ""
                )
            except Exception:
                # Fraud engine unavailable - disable payments capability
                self.capability_repo.update_status(
                    "payments",
                    "unavailable",
                    "fraud_service_unavailable",
                    "Payment service is temporarily unavailable",
                    "Please try again later",
                    correlation_id or ""
                )
                self.db.commit()
                raise HTTPException(
                    status_code=503,
                    detail="Fraud decisioning service unavailable"
                )
            
            if fraud_decision == "unavailable":
                # Fraud engine returned unavailable - disable payments capability
                self.capability_repo.update_status(
                    "payments",
                    "unavailable",
                    "fraud_service_unavailable",
                    "Payment service is temporarily unavailable",
                    "Please try again later",
                    correlation_id or ""
                )
                self.db.commit()
                raise HTTPException(
                    status_code=503,
                    detail="Fraud decisioning service unavailable"
                )
            
            # Create scam check outcome record
            decision_inputs = {
                "device_hash": "device-hash-placeholder",
                "payee_age_days": payee_age_days,
                "cop_outcome": payee.cop_outcome_category or "not_checked",
                "amount_minor": payment.amount_minor,
                "currency": payment.currency
            }
            
            scam_outcome = ScamCheckOutcome(
                id=uuid.uuid4(),
                payment_intent_id=payment.id,
                review_version=payment.review_version,
                fraud_engine_reference=engine_ref,
                risk_outcome=fraud_decision,
                decision_inputs=decision_inputs,
                decision_latency_ms=latency_ms,
                customer_warning_required=(fraud_decision == "warn"),
                policy_allows_continue=policy_allows_continue if fraud_decision == "warn" else False,
                customer_warning_presented_at=None,
                customer_decision="not_applicable" if fraud_decision != "warn" else "pending",
                customer_decision_at=None,
                hold_latest_decision_at=None,
                correlation_id=correlation_id or "",
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC)
            )
            
            if fraud_decision == "warn":
                # Warning required - present to customer
                scam_outcome.customer_warning_presented_at = datetime.now(UTC)
                scam_outcome.customer_decision = "pending"
                self.scam_check_repo.create(scam_outcome)
                
                payment.current_state = "warning_presented"
                payment.customer_visible_status = self._converge_customer_visible_status("warning_presented")
                payment.do_not_resubmit = False
                payment.last_state_changed_at = datetime.now(UTC)
                payment.updated_at = datetime.now(UTC)
                self.payment_repo.update(payment)
                
            elif fraud_decision == "hold":
                # Hold for review - converge to Pending with hold indicator
                scam_outcome.hold_latest_decision_at = datetime.now(UTC) + timedelta(days=4)
                self.scam_check_repo.create(scam_outcome)
                
                payment.current_state = "held_for_review"
                payment.customer_visible_status = self._converge_customer_visible_status("held_for_review")
                payment.do_not_resubmit = True
                payment.hold_latest_decision_at = scam_outcome.hold_latest_decision_at
                payment.submitted_at = datetime.now(UTC)
                payment.last_state_changed_at = datetime.now(UTC)
                payment.updated_at = datetime.now(UTC)
                self.payment_repo.update(payment)
                
            else:  # allow
                # Allow - create scam outcome, write outbox event, submit to payments hub
                self.scam_check_repo.create(scam_outcome)
                
                # Move to submission_in_progress and converge status
                payment.current_state = "submission_in_progress"
                payment.customer_visible_status = self._converge_customer_visible_status("submission_in_progress")
                payment.do_not_resubmit = True
                payment.submitted_at = datetime.now(UTC)
                payment.last_state_changed_at = datetime.now(UTC)
                payment.updated_at = datetime.now(UTC)
                self.payment_repo.update(payment)
                
                # Write outbox event (atomically with state transition)
                outbox_event = PaymentOutboxEvent(
                    id=uuid.uuid4(),
                    payment_intent_id=payment.id,
                    state_transition_id=None,  # Would FK to payment_state_transitions in full implementation
                    event_sequence=1,
                    event_type="payment.submitted",
                    event_payload={
                        "payment_id": str(payment.id),
                        "customer_id": str(customer_uuid),
                        "amount_minor": payment.amount_minor,
                        "currency": payment.currency,
                        "payee_id": str(payment.payee_id),
                        "reference": payment.payment_reference_text,
                        "submitted_at": payment.submitted_at.isoformat() if payment.submitted_at else None
                    },
                    publish_state="pending",
                    correlation_id=correlation_id or ""
                )
                self.outbox_repo.create(outbox_event)
            
            # Mark idempotency as resolved
            self.idempotency_repo.mark_resolved(
                idempotency_record,
                success=True,
                status_code=200,
                response_reference=str(payment.id)
            )
            
            self.db.commit()
            
            # Get account and payee for response
            stmt = select(AccountReadModel).where(
                AccountReadModel.account_system_reference == payment.source_account_reference
            )
            account = self.db.execute(stmt).scalar_one_or_none()
            payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
            
            if not account or not payee:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load payment details"
                )
            
            response = self._build_payment_response(payment, account, payee)
            return (response, False)
        
        except ValueError as e:
            self.db.rollback()
            if str(e) == "idempotency_key_reuse":
                raise HTTPException(
                    status_code=422,
                    detail="Idempotency key reused with different request"
                )
            raise
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in approve_and_submit: {e!s}"
            )
    
    def get_payment(
        self,
        payment_id: uuid.UUID,
        customer_id: str
    ) -> PaymentResponse:
        """
        Get payment by ID (E-08).
        
        Args:
            payment_id: Payment intent ID
            customer_id: Customer profile reference ID
        
        Returns:
            PaymentResponse
        
        Raises:
            HTTPException: 404
        """
        try:
            customer_uuid = uuid.UUID(customer_id) if isinstance(customer_id, str) else customer_id
            
            payment = self.payment_repo.get_by_id(payment_id, customer_uuid)
            if not payment:
                raise HTTPException(
                    status_code=404,
                    detail="Payment not found"
                )
            
            # Get account and payee
            stmt = select(AccountReadModel).where(
                AccountReadModel.account_system_reference == payment.source_account_reference
            )
            account = self.db.execute(stmt).scalar_one_or_none()
            payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
            
            if not account or not payee:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load payment details"
                )
            
            response = self._build_payment_response(payment, account, payee)
            return response
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in get_payment: {e!s}"
            )
    
    def list_payments(
        self,
        customer_id: str,
        idempotency_key: str | None = None,
        page: int = 1,
        page_size: int = 20
    ) -> PaymentListResponse:
        """
        List payments for customer (E-09).
        
        With idempotency_key, returns the payment created/submitted under that key (reconnect).
        
        Args:
            customer_id: Customer profile reference ID
            idempotency_key: Optional idempotency key for reconnect
            page: Page number (1-based)
            page_size: Items per page
        
        Returns:
            PaymentListResponse
        
        Raises:
            HTTPException: 500
        """
        try:
            customer_uuid = uuid.UUID(customer_id) if isinstance(customer_id, str) else customer_id
            
            if idempotency_key:
                # Reconnect by idempotency key
                idempotency_record = self.idempotency_repo.get_by_key(
                    customer_uuid,
                    idempotency_key
                )
                
                if idempotency_record and idempotency_record.payment_intent_id:
                    payment = self.payment_repo.get_by_id(
                        idempotency_record.payment_intent_id,
                        customer_uuid
                    )
                    
                    if payment:
                        stmt = select(AccountReadModel).where(
                            AccountReadModel.account_system_reference == payment.source_account_reference
                        )
                        account = self.db.execute(stmt).scalar_one_or_none()
                        payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
                        
                        if account and payee:
                            response_item = self._build_payment_response(payment, account, payee)
                            return PaymentListResponse(
                                items=[response_item],
                                total=1,
                                page=1,
                                page_size=1
                            )
                
                # Key not found or no payment - return empty
                return PaymentListResponse(
                    items=[],
                    total=0,
                    page=1,
                    page_size=page_size
                )
            
            # List all payments for customer (newest first)
            payments = self.payment_repo.list_by_customer(
                customer_uuid,
                page=page,
                page_size=page_size
            )
            
            total = self.payment_repo.count_by_customer(customer_uuid)
            
            items = []
            for payment in payments:
                stmt = select(AccountReadModel).where(
                    AccountReadModel.account_system_reference == payment.source_account_reference
                )
                account = self.db.execute(stmt).scalar_one_or_none()
                payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
                
                if account and payee:
                    response_item = self._build_payment_response(payment, account, payee)
                    items.append(response_item)
            
            return PaymentListResponse(
                items=items,
                total=total,
                page=page,
                page_size=page_size
            )
        
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in list_payments: {e!s}"
            )
    
    def record_warning_decision(
        self,
        payment_id: uuid.UUID,
        request: WarningDecisionRequest,
        customer_id: str,
        correlation_id: str | None = None
    ) -> PaymentResponse:
        """
        Record customer warning decision (E-12).
        
        Valid only while current_state is warning_presented.
        'stop' moves to stopped_after_warning (not submitted).
        'continue' only allowed if policy_allows_continue; moves to submission_in_progress.
        
        Args:
            payment_id: Payment intent ID
            request: WarningDecisionRequest
            customer_id: Customer profile reference ID
            correlation_id: Optional correlation ID
        
        Returns:
            PaymentResponse
        
        Raises:
            HTTPException: 400, 403, 404, 409
        """
        try:
            customer_uuid = uuid.UUID(customer_id) if isinstance(customer_id, str) else customer_id
            
            # Get payment
            payment = self.payment_repo.get_by_id(payment_id, customer_uuid)
            if not payment:
                raise HTTPException(
                    status_code=404,
                    detail="Payment not found"
                )
            
            # Check state allows warning decision
            if payment.current_state != "warning_presented":
                raise HTTPException(
                    status_code=400,
                    detail="Warning decision not valid for current payment state"
                )
            
            # Check review version matches
            if payment.review_version != request.review_version:
                raise HTTPException(
                    status_code=409,
                    detail="Review version has changed"
                )
            
            # Get scam check outcome
            scam_outcome = self.scam_check_repo.get_by_payment_and_version(
                payment.id, payment.review_version
            )
            if not scam_outcome:
                raise HTTPException(
                    status_code=500,
                    detail="Scam check outcome not found"
                )
            
            # Validate decision based on policy
            if request.decision == "continue":
                if not scam_outcome.policy_allows_continue:
                    raise HTTPException(
                        status_code=403,
                        detail="Policy does not allow continuing after this warning"
                    )
                
                # Continue - record decision and move to submission
                scam_outcome.customer_decision = "continued"
                scam_outcome.customer_decision_at = datetime.now(UTC)
                scam_outcome.updated_at = datetime.now(UTC)
                self.db.flush()
                
                # Write audit event for warning traversal
                audit_event = AuditEvent(
                    id=uuid.uuid4(),
                    event_type="payment.warning_traversed",
                    actor_type="customer",
                    actor_reference=str(customer_uuid),
                    resource_type="payment_intent",
                    resource_reference=str(payment.id),
                    action_category="payment_decision",
                    action_detail="warning_continued",
                    outcome="success",
                    correlation_id=correlation_id or "",
                    occurred_at=datetime.now(UTC)
                )
                self.db.add(audit_event)
                
                payment.current_state = "submission_in_progress"
                payment.customer_visible_status = self._converge_customer_visible_status("submission_in_progress")
                payment.do_not_resubmit = True
                payment.submitted_at = datetime.now(UTC)
                payment.last_state_changed_at = datetime.now(UTC)
                payment.updated_at = datetime.now(UTC)
                self.payment_repo.update(payment)
                
                # Write outbox event (atomically with state transition)
                outbox_event = PaymentOutboxEvent(
                    id=uuid.uuid4(),
                    payment_intent_id=payment.id,
                    state_transition_id=None,
                    event_sequence=1,
                    event_type="payment.submitted",
                    event_payload={
                        "payment_id": str(payment.id),
                        "customer_id": str(customer_uuid),
                        "amount_minor": payment.amount_minor,
                        "currency": payment.currency,
                        "payee_id": str(payment.payee_id),
                        "reference": payment.payment_reference_text,
                        "warning_continued": True,
                        "submitted_at": payment.submitted_at.isoformat() if payment.submitted_at else None
                    },
                    publish_state="pending",
                    correlation_id=correlation_id or ""
                )
                self.outbox_repo.create(outbox_event)
                
            else:  # stop
                # Stop - record decision and move to stopped state
                scam_outcome.customer_decision = "stopped"
                scam_outcome.customer_decision_at = datetime.now(UTC)
                scam_outcome.updated_at = datetime.now(UTC)
                self.db.flush()
                
                payment.current_state = "stopped_after_warning"
                payment.customer_visible_status = self._converge_customer_visible_status("stopped_after_warning")
                payment.do_not_resubmit = False
                payment.last_state_changed_at = datetime.now(UTC)
                payment.updated_at = datetime.now(UTC)
                self.payment_repo.update(payment)
            
            self.db.commit()
            
            # Get account and payee for response
            stmt = select(AccountReadModel).where(
                AccountReadModel.account_system_reference == payment.source_account_reference
            )
            account = self.db.execute(stmt).scalar_one_or_none()
            payee = self.payment_repo.get_payee_by_id(payment.payee_id, customer_uuid)
            
            if not account or not payee:
                raise HTTPException(
                    status_code=500,
                    detail="Failed to load payment details"
                )
            
            response = self._build_payment_response(payment, account, payee)
            return response
        
        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error in record_warning_decision: {e!s}"
            )
