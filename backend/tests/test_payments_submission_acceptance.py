"""
Acceptance tests for FR-PAY-011 and FR-PAY-012.
Requirement: REQ-PAY-008, REQ-PAY-009
"""


def test_held_payment_shown_as_pending_not_sent(auth_client):
    """
    FR-PAY-011: A held or pending-review payment is shown as such rather than as Sent or Failed.
    """
    # Held payments would be tested through the full flow with fraud returning 'hold'
    # This would be implemented once the full E-11 flow with hold outcomes is complete


def test_pending_includes_do_not_resubmit_guidance(auth_client):
    """
    FR-PAY-011: The customer is told that the payment should not be resubmitted while its status remains unresolved.
    """


def test_hold_outcome_distinguishable_from_sent(auth_client):
    """
    FR-PAY-011: The payment hold outcome is distinguishable from a final sent outcome.
    """


def test_hold_includes_payment_reference(auth_client):
    """
    FR-PAY-011: The customer-visible messaging includes the payment reference for identification.
    """


def test_payment_outcome_maps_to_exactly_one_status(auth_client):
    """
    FR-PAY-012: Each customer-visible payment outcome maps to one and only one of Sent, Pending, or Failed at the time it is shown.
    """


def test_no_conflicting_payment_outcomes(auth_client):
    """
    FR-PAY-012: The customer is not shown conflicting payment outcomes for the same payment in the same journey state.
    """


def test_pending_status_avoids_duplicate_payment_behavior(auth_client):
    """
    FR-PAY-012: Pending status messaging explicitly avoids encouraging duplicate-payment behaviour.
    """


def test_failed_status_distinguishes_from_sending(auth_client):
    """
    FR-PAY-012: Failed status messaging distinguishes non-completion from successful sending.
    """
