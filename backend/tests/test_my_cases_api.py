def test_post_resolve_starts_session(auth_client):
    """Test POST /api/v1/resolve starts a session"""
    response = auth_client.post("/api/v1/resolve", json={
        "message_text": "I have a problem with my card",
        "entry_context_type": "none",
        "status_context_shown": False
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "thread_id" in data
    assert data["ai_disclosure"] is True
    assert data["human_path_shown"] is True
    assert len(data["new_entries"]) >= 2


def test_get_resolve_session(auth_client):
    """Test GET /api/v1/resolve/{session_id} returns session view"""
    # Start session
    response1 = auth_client.post("/api/v1/resolve", json={
        "message_text": "I need help"
    })
    data1 = response1.json()
    session_id = data1["session_id"]
    
    # Get session
    response2 = auth_client.get(f"/api/v1/resolve/{session_id}")
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["session_id"] == session_id
    assert len(data2["entries"]) >= 2


def test_post_resolve_messages(auth_client):
    """Test POST /api/v1/resolve/{session_id}/messages sends message"""
    # Start session
    response1 = auth_client.post("/api/v1/resolve", json={
        "message_text": "I have a question"
    })
    data1 = response1.json()
    session_id = data1["session_id"]
    
    # Send message
    response2 = auth_client.post(f"/api/v1/resolve/{session_id}/messages", json={
        "message_text": "The payment failed yesterday"
    })
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["session_id"] == session_id
    assert len(data2["new_entries"]) >= 2


def test_post_human_request(auth_client):
    """Test POST /api/v1/resolve/{session_id}/human-request creates case"""
    # Start session
    response1 = auth_client.post("/api/v1/resolve", json={
        "message_text": "I want to speak to a person"
    })
    data1 = response1.json()
    session_id = data1["session_id"]
    
    # Request human
    response2 = auth_client.post(f"/api/v1/resolve/{session_id}/human-request")
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert "case_ref" in data2
    assert "case_id" in data2
    assert "CP-" in data2["case_ref"]


def test_post_cases_creates_case(auth_client):
    """Test POST /api/v1/cases creates case"""
    response = auth_client.post("/api/v1/cases", json={
        "origin_source": "direct_entry",
        "problem_statement": "I have a problem with my account"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "case_ref" in data
    assert "CP-" in data["case_ref"]


def test_get_cases_lists_cases(auth_client):
    """Test GET /api/v1/cases lists customer cases"""
    # Create a case first
    auth_client.post("/api/v1/cases", json={
        "origin_source": "direct_entry",
        "problem_statement": "Test problem"
    })
    
    # List cases
    response = auth_client.get("/api/v1/cases")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_case_detail(auth_client):
    """Test GET /api/v1/cases/{case_id} returns case detail"""
    # Create a case
    response1 = auth_client.post("/api/v1/cases", json={
        "origin_source": "direct_entry",
        "problem_statement": "Detailed problem"
    })
    data1 = response1.json()
    case_id = data1["id"]
    
    # Get detail
    response2 = auth_client.get(f"/api/v1/cases/{case_id}")
    
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["id"] == case_id
    assert data2["case_ref"] is not None
