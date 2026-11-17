from app.services.orchestrator.orchestrator import Orchestrator
from app.services.orchestrator.schemas import StartSessionRequest


def test_orchestrator_start_session(db_session, auth_client):
    """Test orchestrator can start a session and return turn"""
    orchestrator = Orchestrator(db_session)
    
    request = StartSessionRequest(
        message_text="I have a problem with my card",
        entry_context_type="none",
        entry_context_ref=None,
        status_context_shown=False
    )
    
    result = orchestrator.start_session(1, request)
    
    assert result.session_id is not None
    assert result.thread_id is not None
    assert result.state == "started"
    assert result.ai_disclosure is True
    assert result.human_path_shown is True
    assert len(result.new_entries) >= 2


def test_orchestrator_handle_message(db_session, auth_client):
    """Test orchestrator can handle follow-up messages"""
    orchestrator = Orchestrator(db_session)
    
    # Start session
    request = StartSessionRequest(
        message_text="I need help with a payment",
        entry_context_type="none",
        entry_context_ref=None,
        status_context_shown=False
    )
    result1 = orchestrator.start_session(1, request)
    
    # Send follow-up
    result2 = orchestrator.handle_message(result1.session_id, 1, "The payment failed yesterday")
    
    assert result2.session_id == result1.session_id
    assert len(result2.new_entries) >= 2


def test_orchestrator_request_human(db_session, auth_client):
    """Test orchestrator can escalate to human"""
    orchestrator = Orchestrator(db_session)
    
    request = StartSessionRequest(
        message_text="I want to speak to a person",
        entry_context_type="none",
        entry_context_ref=None,
        status_context_shown=False
    )
    result = orchestrator.start_session(1, request)
    
    # Request human
    human_result = orchestrator.request_human(result.session_id, 1)
    
    assert human_result["case_ref"] is not None
    assert human_result["case_id"] is not None
    assert "CP-" in human_result["case_ref"]
