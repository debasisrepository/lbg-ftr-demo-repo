"""Seed policy rules for the application."""
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.core.clock import Clock

from app.models.policy import PolicyRule, PolicyRuleSetVersion


def seed_policy_rules(db: "Session", clock: "Clock") -> None:
    """Seed policy rule set version 1 with 13 rules."""
    now = clock.now()

    # Create rule set version 1
    rule_set = PolicyRuleSetVersion(
        id=uuid.uuid4(),
        created_at=now,
        updated_at=now,
        version_number=1,
        version_label="Initial Rule Set v1.0",
        region_code="ALL",
        rule_set_status="active",
        effective_from=now,
        change_note="Initial policy rules for MVP"
    )
    db.add(rule_set)
    db.flush()

    # Define 13 policy rules for promise creation
    rules = [
        {
            "rule_code": "promise_amount_required",
            "rule_category": "mandatory_field",
            "action_type": "promise_create",
            "rule_description": "Promise amount must be provided",
            "condition_json": {"type": "field_present", "field": "promised_amount"},
            "parameters_json": {},
            "failure_message": "Promise amount is required",
            "evaluation_order": 1,
        },
        {
            "rule_code": "promise_amount_positive",
            "rule_category": "value_validation",
            "action_type": "promise_create",
            "rule_description": "Promise amount must be positive",
            "condition_json": {"type": "decimal_greater_than", "field": "promised_amount", "threshold": 0},
            "parameters_json": {},
            "failure_message": "Promise amount must be greater than zero",
            "evaluation_order": 2,
        },
        {
            "rule_code": "promise_date_required",
            "rule_category": "mandatory_field",
            "action_type": "promise_create",
            "rule_description": "Promise date must be provided",
            "condition_json": {"type": "field_present", "field": "promised_date"},
            "parameters_json": {},
            "failure_message": "Promise date is required",
            "evaluation_order": 3,
        },
        {
            "rule_code": "promise_scope_required",
            "rule_category": "mandatory_field",
            "action_type": "promise_create",
            "rule_description": "Promise scope type must be provided",
            "condition_json": {"type": "field_present", "field": "promise_scope_type"},
            "parameters_json": {},
            "failure_message": "Promise scope type is required",
            "evaluation_order": 4,
        },
        {
            "rule_code": "promise_links_required",
            "rule_category": "mandatory_field",
            "action_type": "promise_create",
            "rule_description": "Promise scope links must be provided",
            "condition_json": {"type": "collection_min_size", "field": "scope_links", "min_size": 1},
            "parameters_json": {},
            "failure_message": "At least one scope link is required",
            "evaluation_order": 5,
        },
        {
            "rule_code": "promise_source_interaction_required",
            "rule_category": "mandatory_field",
            "action_type": "promise_create",
            "rule_description": "Source interaction must be provided",
            "condition_json": {"type": "one_of_present", "fields": ["source_interaction_id", "source_interaction"]},
            "parameters_json": {},
            "failure_message": "Source interaction is required",
            "evaluation_order": 6,
        },
        {
            "rule_code": "promise_currency_matches_account",
            "rule_category": "referential_integrity",
            "action_type": "promise_create",
            "rule_description": "Promise currency must match account currency",
            "condition_json": {"type": "field_equals_context", "field": "currency_code", "context_field": "account.currency_code"},
            "parameters_json": {},
            "failure_message": "Promise currency must match account currency",
            "evaluation_order": 7,
        },
        {
            "rule_code": "promise_links_belong_to_account",
            "rule_category": "referential_integrity",
            "action_type": "promise_create",
            "rule_description": "All linked items must belong to the promise account",
            "condition_json": {"type": "all_belong_to", "collection": "scope_links", "parent_field": "customer_account_id"},
            "parameters_json": {},
            "failure_message": "All linked items must belong to this account",
            "evaluation_order": 8,
        },
        {
            "rule_code": "promise_link_amounts_match",
            "rule_category": "value_validation",
            "action_type": "promise_create",
            "rule_description": "Sum of link amounts must equal promise amount",
            "condition_json": {"type": "sum_matches", "collection": "scope_links", "field": "linked_amount", "target_field": "promised_amount"},
            "parameters_json": {},
            "failure_message": "Sum of link amounts must equal promise amount",
            "evaluation_order": 9,
        },
        {
            "rule_code": "queue_entry_not_disputed",
            "rule_category": "queue_eligibility",
            "action_type": "queue_entry",
            "rule_description": "Disputed items are non-standard",
            "condition_json": {"type": "flag_is_false", "field": "dispute_indicator"},
            "parameters_json": {},
            "failure_message": "Item marked as disputed",
            "evaluation_order": 10,
        },
        {
            "rule_code": "queue_entry_not_unapplied_cash",
            "rule_category": "queue_eligibility",
            "action_type": "queue_entry",
            "rule_description": "Unapplied cash items are non-standard",
            "condition_json": {"type": "flag_is_false", "field": "unapplied_cash_indicator"},
            "parameters_json": {},
            "failure_message": "Item marked as unapplied cash",
            "evaluation_order": 11,
        },
        {
            "rule_code": "queue_entry_not_pending_evidence",
            "rule_category": "queue_eligibility",
            "action_type": "queue_entry",
            "rule_description": "Evidence-pending items are non-standard",
            "condition_json": {"type": "flag_is_false", "field": "pending_evidence_indicator"},
            "parameters_json": {},
            "failure_message": "Item pending evidence",
            "evaluation_order": 12,
        },
        {
            "rule_code": "queue_entry_valid_scope",
            "rule_category": "queue_eligibility",
            "action_type": "queue_entry",
            "rule_description": "Queue item must have valid scope",
            "condition_json": {"type": "field_in_set", "field": "queue_type", "allowed_values": ["standard_collections"]},
            "parameters_json": {},
            "failure_message": "Invalid queue type",
            "evaluation_order": 13,
        },
    ]

    for rule_data in rules:
        rule = PolicyRule(
            id=uuid.uuid4(),
            created_at=now,
            updated_at=now,
            rule_set_version_id=rule_set.id,
            is_enabled=True,
            **rule_data
        )
        db.add(rule)

    print(f"Seeded policy rule set version {rule_set.version_number} with {len(rules)} rules")
