"""
IdempotencyRepository - database operations for idempotency tracking.
Requirement: REQ-PAY-002, REQ-PAY-003, REQ-PAY-004, REQ-PAY-005
"""
import uuid

from sqlalchemy import and_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.idempotency_record import IdempotencyRecord


class IdempotencyRepository:
    """Repository for idempotency record persistence."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_or_get_existing(
        self,
        customer_id: uuid.UUID,
        operation_type: str,
        idempotency_key: str,
        request_fingerprint: str,
        payment_intent_id: uuid.UUID,
        correlation_id: str | None = None
    ) -> tuple[IdempotencyRecord, bool]:
        """
        Create idempotency record or get existing one.
        Returns (record, is_new) where is_new=True means newly created.
        
        Args:
            customer_id: Customer profile reference ID
            operation_type: 'payment_review' or 'payment_submit'
            idempotency_key: Client-provided idempotency key
            request_fingerprint: SHA-256 hash of canonical request body
            payment_intent_id: Associated payment intent ID
            correlation_id: Optional correlation ID
        
        Returns:
            Tuple of (IdempotencyRecord, is_new)
        
        Raises:
            ValueError: If same key with different fingerprint
        """
        # Try to find existing record
        stmt = select(IdempotencyRecord).where(
            and_(
                IdempotencyRecord.customer_profile_ref_id == customer_id,
                IdempotencyRecord.operation_type == operation_type,
                IdempotencyRecord.idempotency_key == idempotency_key
            )
        )
        existing = self.db.execute(stmt).scalar_one_or_none()
        
        if existing:
            # Same key exists - check fingerprint
            if existing.request_fingerprint != request_fingerprint:
                raise ValueError("idempotency_key_reuse")
            
            # Same key + same fingerprint = replay
            existing.replay_count += 1
            self.db.flush()
            self.db.refresh(existing)
            return (existing, False)
        
        # New record - payment_intent_id is required for both operations
        record = IdempotencyRecord(
            id=uuid.uuid4(),
            customer_profile_ref_id=customer_id,
            operation_type=operation_type,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            payment_intent_id=payment_intent_id,
            resolution_state="in_progress",
            replay_count=0,
            correlation_id=correlation_id
        )
        
        try:
            self.db.add(record)
            self.db.flush()
            self.db.refresh(record)
            
            return (record, True)
        except IntegrityError as e:
            # Race condition - another request created it
            self.db.rollback()
            stmt = select(IdempotencyRecord).where(
                and_(
                    IdempotencyRecord.customer_profile_ref_id == customer_id,
                    IdempotencyRecord.operation_type == operation_type,
                    IdempotencyRecord.idempotency_key == idempotency_key
                )
            )
            existing = self.db.execute(stmt).scalar_one_or_none()
            
            if existing is None:
                # IntegrityError was not from unique constraint on idempotency key
                # Re-raise the original error
                raise e
            
            if existing.request_fingerprint != request_fingerprint:
                raise ValueError("idempotency_key_reuse")
            
            existing.replay_count += 1
            self.db.flush()
            self.db.refresh(existing)
            return (existing, False)
    
    def mark_resolved(
        self,
        record: IdempotencyRecord,
        success: bool,
        status_code: int,
        response_reference: str
    ) -> IdempotencyRecord:
        """
        Mark idempotency record as resolved.
        
        Args:
            record: IdempotencyRecord to update
            success: True if resolved successfully
            status_code: HTTP status code returned
            response_reference: Reference to stored response (e.g., payment_id)
        
        Returns:
            Updated IdempotencyRecord
        """
        record.resolution_state = "resolved_success" if success else "resolved_failure"
        record.response_status_code = status_code
        record.returned_response_reference = response_reference
        self.db.flush()
        self.db.refresh(record)
        return record
    
    def get_by_key(
        self,
        customer_id: uuid.UUID,
        idempotency_key: str
    ) -> IdempotencyRecord | None:
        """
        Get idempotency record by customer and key (any operation type).
        
        Args:
            customer_id: Customer profile reference ID
            idempotency_key: Idempotency key
        
        Returns:
            IdempotencyRecord or None
        """
        stmt = select(IdempotencyRecord).where(
            and_(
                IdempotencyRecord.customer_profile_ref_id == customer_id,
                IdempotencyRecord.idempotency_key == idempotency_key
            )
        ).order_by(IdempotencyRecord.created_at.desc())
        return self.db.execute(stmt).scalars().first()
