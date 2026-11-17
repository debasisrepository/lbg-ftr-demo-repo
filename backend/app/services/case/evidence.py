"""Evidence service for handling evidence items with checksum idempotency."""
import uuid
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.clock import Clock
from app.services.case.models import EvidenceItem


class EvidenceService:
    """
    Manages evidence items attached to Cases.
    Handles file uploads with checksum-based idempotency.
    """
    def __init__(self, clock: Clock):
        self.clock = clock
    
    def record_evidence(
        self,
        db: Session,
        thread_id: uuid.UUID,
        display_label: str,
        evidence_type: str,
        file_bytes: bytes | None = None,
        mime_type: str | None = None,
        request_only: bool = False,
        requested_by_type: str = "assistant"
    ) -> EvidenceItem:
        """
        Record evidence item.
        
        For request_only=True: creates requested item without file.
        For file upload: stores with checksum, checks for duplicates.
        
        Args:
            db: Database session
            thread_id: Conversation thread UUID
            display_label: Display label for evidence
            evidence_type: Evidence type code
            file_bytes: File content bytes (None for request)
            mime_type: MIME type of file
            request_only: True to just record request
            requested_by_type: 'assistant' or 'colleague'
        
        Returns:
            EvidenceItem (new or existing)
        """
        if request_only:
            # Create evidence request
            evidence = EvidenceItem(
                id=uuid.uuid4(),
                thread_id=thread_id,
                state="requested",
                display_label=display_label,
                requested_at=self.clock.utc_now(),
                mime_type=None,
                file_size_bytes=None,
                storage_key=None,
                checksum=None,
                llm_eligible=False,
                received_at=None
            )
            db.add(evidence)
            db.flush()
            return evidence
        
        # Handle file upload
        if not file_bytes:
            raise ValueError("file_bytes required when request_only=False")
        
        # Compute checksum
        checksum = hashlib.sha256(file_bytes).hexdigest()
        
        # Check for duplicate by checksum in same thread
        existing = db.query(EvidenceItem).filter(
            EvidenceItem.thread_id == thread_id,
            EvidenceItem.checksum == checksum
        ).first()
        
        if existing:
            # Return existing (idempotent)
            return existing
        
        # Create new evidence item
        # For demo: storage_key is just the evidence ID
        # In production: write to object store first
        evidence_id = uuid.uuid4()
        storage_key = f"evidence/{evidence_id}"
        
        evidence = EvidenceItem(
            id=evidence_id,
            thread_id=thread_id,
            state="received",
            display_label=display_label,
            requested_at=self.clock.utc_now(),
            mime_type=mime_type,
            file_size_bytes=len(file_bytes),
            storage_key=storage_key,
            checksum=checksum,
            llm_eligible=False,  # Set after redaction review
            received_at=self.clock.utc_now()
        )
        db.add(evidence)
        db.flush()
        return evidence
