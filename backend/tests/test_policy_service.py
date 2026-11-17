from app.services.policy.engine import PolicyEngine
from app.services.policy.schemas import PolicyEvaluationRequest


def test_policy_engine_approve_l0_action(db_session):
    """Test policy engine approves L0 information-only action"""
    engine = PolicyEngine(db_session)
    
    request = PolicyEvaluationRequest(
        action_code="provide_information",
        customer_user_id=1,
        issue_classification="payment_query",
        authenticated=True,
        vulnerability_indicators=[],
        confidence_pct=85,
        repeated_failure=False,
        explicit_human_request=False
    )
    
    decision = engine.evaluate(request)
    
    assert decision.outcome == "approved"
    assert decision.decision_id is not None


def test_policy_engine_escalate_on_vulnerability(db_session):
    """Test policy engine escalates when vulnerability detected"""
    engine = PolicyEngine(db_session)
    
    request = PolicyEvaluationRequest(
        action_code="provide_information",
        customer_user_id=1,
        issue_classification="payment_query",
        authenticated=True,
        vulnerability_indicators=["vulnerability"],
        confidence_pct=85,
        repeated_failure=False,
        explicit_human_request=False
    )
    
    decision = engine.evaluate(request)
    
    assert decision.outcome == "escalate_human"
    assert decision.reason_code == "vulnerability_detected"


def test_policy_engine_escalate_on_low_confidence(db_session):
    """Test policy engine escalates on low confidence"""
    engine = PolicyEngine(db_session)
    
    request = PolicyEvaluationRequest(
        action_code="provide_information",
        customer_user_id=1,
        issue_classification="payment_query",
        authenticated=True,
        vulnerability_indicators=[],
        confidence_pct=50,
        repeated_failure=False,
        explicit_human_request=False
    )
    
    decision = engine.evaluate(request)
    
    assert decision.outcome == "escalate_human"
    assert decision.reason_code == "low_confidence"


def test_policy_engine_deny_sca_required_not_authenticated(db_session):
    """Test policy engine denies SCA-required action when not authenticated"""
    engine = PolicyEngine(db_session)
    
    request = PolicyEvaluationRequest(
        action_code="card_controls",
        customer_user_id=1,
        issue_classification="card_issue",
        authenticated=False,
        vulnerability_indicators=[],
        confidence_pct=85,
        repeated_failure=False,
        explicit_human_request=False
    )
    
    decision = engine.evaluate(request)
    
    assert decision.outcome == "denied"
    assert decision.reason_code == "sca_required"
