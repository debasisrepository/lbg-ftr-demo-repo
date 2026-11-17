"""Test evidence service."""
import uuid
from app.services.case.evidence import EvidenceService
from app.core.clock import Clock


def test_evidence_request_only(db_session):
    """Test evidence request without file."""
    service = EvidenceService(Clock())
    
    thread_id = uuid.uuid4()
    
    evidence = service.record_evidence(
        db=db_session,
        thread_id=thread_id,
        display_label="Bank statement",
        evidence_type="document",
        request_only=True,
        requested_by_type="assistant"
    )
    
    assert evidence.id is not None
    assert evidence.state == "requested"
    assert evidence.display_label == "Bank statement"
    assert evidence.checksum is None


def test_evidence_file_upload(db_session):
    """Test evidence file upload with checksum."""
    service = EvidenceService(Clock())
    
    thread_id = uuid.uuid4()
    file_bytes = b"Test file content"
    
    evidence = service.record_evidence(
        db=db_session,
        thread_id=thread_id,
        display_label="Receipt",
        evidence_type="document",
        file_bytes=file_bytes,
        mime_type="application/pdf",
        request_only=False
    )
    
    assert evidence.id is not None
    assert evidence.state == "received"
    assert evidence.checksum is not None
    assert evidence.file_size_bytes == len(file_bytes)


def test_evidence_deduplication(db_session):
    """Test checksum-based deduplication."""
    service = EvidenceService(Clock())
    
    thread_id = uuid.uuid4()
    file_bytes = b"Same file content"
    
    # Upload once
    evidence1 = service.record_evidence(
        db=db_session,
        thread_id=thread_id,
        display_label="Doc1",
        evidence_type="document",
        file_bytes=file_bytes,
        mime_type="application/pdf",
        request_only=False
    )
    
    # Upload same file again
    evidence2 = service.record_evidence(
        db=db_session,
        thread_id=thread_id,
        display_label="Doc2",
        evidence_type="document",
        file_bytes=file_bytes,
        mime_type="application/pdf",
        request_only=False
    )
    
    # Should return the same evidence item (idempotent)
    assert evidence1.id == evidence2.id
    assert evidence1.checksum == evidence2.checksum
