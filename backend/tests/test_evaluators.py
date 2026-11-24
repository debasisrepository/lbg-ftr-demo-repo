"""Unit tests for policy condition evaluators."""
from decimal import Decimal

import pytest

from app.policy.evaluators import ConditionEvaluator


@pytest.fixture
def evaluator():
    """Create evaluator instance."""
    return ConditionEvaluator()


def test_field_present_passes_when_field_exists(evaluator):
    """Test field_present passes when field has value."""
    params = {"field": "promised_amount"}
    context = {"promised_amount": 100.00}
    
    result = evaluator.evaluate("field_present", params, context)
    
    assert result is True


def test_field_present_fails_when_field_missing(evaluator):
    """Test field_present fails when field is None."""
    params = {"field": "promised_amount"}
    context = {"promised_amount": None}
    
    result = evaluator.evaluate("field_present", params, context)
    
    assert result is False


def test_field_present_nested_field(evaluator):
    """Test field_present with nested field path."""
    params = {"field": "account.balance"}
    context = {"account": {"balance": 500.00}}
    
    result = evaluator.evaluate("field_present", params, context)
    
    assert result is True


def test_decimal_greater_than_passes(evaluator):
    """Test decimal_greater_than passes when value exceeds threshold."""
    params = {"field": "promised_amount", "threshold": "0"}
    context = {"promised_amount": 100.00}
    
    result = evaluator.evaluate("decimal_greater_than", params, context)
    
    assert result is True


def test_decimal_greater_than_fails(evaluator):
    """Test decimal_greater_than fails when value is below threshold."""
    params = {"field": "promised_amount", "threshold": "1000"}
    context = {"promised_amount": 100.00}
    
    result = evaluator.evaluate("decimal_greater_than", params, context)
    
    assert result is False


def test_decimal_greater_than_with_none(evaluator):
    """Test decimal_greater_than returns False for None value."""
    params = {"field": "promised_amount", "threshold": "0"}
    context = {"promised_amount": None}
    
    result = evaluator.evaluate("decimal_greater_than", params, context)
    
    assert result is False


def test_field_in_set_passes(evaluator):
    """Test field_in_set passes when value is in allowed set."""
    params = {"field": "promise_scope_type", "allowed_values": ["invoice", "account_balance"]}
    context = {"promise_scope_type": "invoice"}
    
    result = evaluator.evaluate("field_in_set", params, context)
    
    assert result is True


def test_field_in_set_fails(evaluator):
    """Test field_in_set fails when value is not in allowed set."""
    params = {"field": "promise_scope_type", "allowed_values": ["invoice", "account_balance"]}
    context = {"promise_scope_type": "partial"}
    
    result = evaluator.evaluate("field_in_set", params, context)
    
    assert result is False


def test_field_in_set_with_none(evaluator):
    """Test field_in_set returns False for None value."""
    params = {"field": "promise_scope_type", "allowed_values": ["invoice"]}
    context = {"promise_scope_type": None}
    
    result = evaluator.evaluate("field_in_set", params, context)
    
    assert result is False


def test_field_equals_context_passes(evaluator):
    """Test field_equals_context passes when fields match."""
    params = {"field": "customer_id", "context_field": "account.customer_id"}
    context = {
        "customer_id": "123",
        "account": {"customer_id": "123"}
    }
    
    result = evaluator.evaluate("field_equals_context", params, context)
    
    assert result is True


def test_field_equals_context_fails(evaluator):
    """Test field_equals_context fails when fields don't match."""
    params = {"field": "customer_id", "context_field": "account.customer_id"}
    context = {
        "customer_id": "123",
        "account": {"customer_id": "456"}
    }
    
    result = evaluator.evaluate("field_equals_context", params, context)
    
    assert result is False


def test_collection_min_size_passes(evaluator):
    """Test collection_min_size passes when collection is large enough."""
    params = {"field": "scope_links", "min_size": 1}
    context = {"scope_links": [{"invoice_id": "1"}]}
    
    result = evaluator.evaluate("collection_min_size", params, context)
    
    assert result is True


def test_collection_min_size_fails(evaluator):
    """Test collection_min_size fails when collection is too small."""
    params = {"field": "scope_links", "min_size": 2}
    context = {"scope_links": [{"invoice_id": "1"}]}
    
    result = evaluator.evaluate("collection_min_size", params, context)
    
    assert result is False


def test_collection_min_size_with_empty(evaluator):
    """Test collection_min_size with empty collection."""
    params = {"field": "scope_links", "min_size": 1}
    context = {"scope_links": []}
    
    result = evaluator.evaluate("collection_min_size", params, context)
    
    assert result is False


def test_collection_min_size_with_none(evaluator):
    """Test collection_min_size returns False for None."""
    params = {"field": "scope_links", "min_size": 1}
    context = {"scope_links": None}
    
    result = evaluator.evaluate("collection_min_size", params, context)
    
    assert result is False


def test_sum_matches_passes(evaluator):
    """Test sum_matches passes when sum equals target within tolerance."""
    params = {
        "collection_field": "scope_links",
        "sum_field": "linked_amount",
        "target_field": "promised_amount",
        "tolerance": "0.01"
    }
    context = {
        "scope_links": [
            {"linked_amount": 50.00},
            {"linked_amount": 50.00}
        ],
        "promised_amount": 100.00
    }
    
    result = evaluator.evaluate("sum_matches", params, context)
    
    assert result is True


def test_sum_matches_fails(evaluator):
    """Test sum_matches fails when sum doesn't match target."""
    params = {
        "collection_field": "scope_links",
        "sum_field": "linked_amount",
        "target_field": "promised_amount",
        "tolerance": "0.01"
    }
    context = {
        "scope_links": [
            {"linked_amount": 50.00},
            {"linked_amount": 40.00}
        ],
        "promised_amount": 100.00
    }
    
    result = evaluator.evaluate("sum_matches", params, context)
    
    assert result is False


def test_sum_matches_with_tolerance(evaluator):
    """Test sum_matches passes within tolerance."""
    params = {
        "collection_field": "scope_links",
        "sum_field": "linked_amount",
        "target_field": "promised_amount",
        "tolerance": "1.00"
    }
    context = {
        "scope_links": [
            {"linked_amount": 50.00},
            {"linked_amount": 49.50}
        ],
        "promised_amount": 100.00
    }
    
    result = evaluator.evaluate("sum_matches", params, context)
    
    assert result is True


def test_all_belong_to_passes(evaluator):
    """Test all_belong_to passes when all items match parent."""
    params = {
        "collection_field": "scope_links",
        "item_parent_field": "customer_account_id",
        "parent_id_field": "customer_account_id"
    }
    context = {
        "scope_links": [
            {"customer_account_id": "acc123"},
            {"customer_account_id": "acc123"}
        ],
        "customer_account_id": "acc123"
    }
    
    result = evaluator.evaluate("all_belong_to", params, context)
    
    assert result is True


def test_all_belong_to_fails(evaluator):
    """Test all_belong_to fails when items don't match parent."""
    params = {
        "collection_field": "scope_links",
        "item_parent_field": "customer_account_id",
        "parent_id_field": "customer_account_id"
    }
    context = {
        "scope_links": [
            {"customer_account_id": "acc123"},
            {"customer_account_id": "acc456"}
        ],
        "customer_account_id": "acc123"
    }
    
    result = evaluator.evaluate("all_belong_to", params, context)
    
    assert result is False


def test_one_of_present_passes(evaluator):
    """Test one_of_present passes when at least one field exists."""
    params = {"fields": ["source_interaction_id", "source_interaction"]}
    context = {
        "source_interaction_id": "int123",
        "source_interaction": None
    }
    
    result = evaluator.evaluate("one_of_present", params, context)
    
    assert result is True


def test_one_of_present_fails(evaluator):
    """Test one_of_present fails when all fields are None."""
    params = {"fields": ["source_interaction_id", "source_interaction"]}
    context = {
        "source_interaction_id": None,
        "source_interaction": None
    }
    
    result = evaluator.evaluate("one_of_present", params, context)
    
    assert result is False


def test_flag_is_false_passes_when_false(evaluator):
    """Test flag_is_false passes when flag is False."""
    params = {"field": "is_disputed"}
    context = {"is_disputed": False}
    
    result = evaluator.evaluate("flag_is_false", params, context)
    
    assert result is True


def test_flag_is_false_fails_when_true(evaluator):
    """Test flag_is_false fails when flag is True."""
    params = {"field": "is_disputed"}
    context = {"is_disputed": True}
    
    result = evaluator.evaluate("flag_is_false", params, context)
    
    assert result is False


def test_flag_is_false_passes_when_none(evaluator):
    """Test flag_is_false treats None as False."""
    params = {"field": "is_disputed"}
    context = {"is_disputed": None}
    
    result = evaluator.evaluate("flag_is_false", params, context)
    
    assert result is True


def test_unknown_condition_type_raises(evaluator):
    """Test unknown condition type raises ValueError."""
    params = {}
    context = {}
    
    with pytest.raises(ValueError, match="Unknown condition type"):
        evaluator.evaluate("unknown_condition", params, context)


def test_nested_field_in_dict(evaluator):
    """Test nested field access in dict."""
    value = evaluator._get_nested_field(
        {"level1": {"level2": {"level3": "value"}}},
        "level1.level2.level3"
    )
    
    assert value == "value"


def test_nested_field_missing_returns_none(evaluator):
    """Test nested field access returns None when path doesn't exist."""
    value = evaluator._get_nested_field(
        {"level1": {"level2": "value"}},
        "level1.missing.level3"
    )
    
    assert value is None
