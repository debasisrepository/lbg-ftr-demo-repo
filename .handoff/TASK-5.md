# TASK-5 Handoff: Backend Feature B3 - Deterministic Policy Enforcement

## Overview
Completed deterministic policy enforcement with rule set activation CLI, full evaluator implementations, evaluation history, audit security guard, and retention purge. All acceptance tests pass for FR-DTC-001.

## CLI Commands Added

### activate-rule-set
Activate a policy rule set version and supersede any active rule sets for the same region.

```bash
python app/cli.py activate-rule-set --version 1 --approver analyst1
```

**Parameters:**
- `--version N`: Rule set version number to activate
- `--approver USERNAME`: Username of approving user

**Behavior:**
- Finds rule set by version number
- Validates approver user exists
- Deactivates any currently active rule sets for the same region (marks as "superseded")
- Activates target rule set with approval metadata
- Sets effective_from timestamp
- Commits transaction

**Output:**
```
Successfully activated rule set version 1
  Region: ALL
  Label: Initial Rule Set v1.0
  Approved by: analyst1
  Effective from: 2026-11-24 17:51:08+00:00
  Superseded 1 previous rule set(s)
```

### purge
Purge old audit events beyond retention period (default 90 days).

```bash
python app/cli.py purge --retention-days 90
```

**Parameters:**
- `--retention-days N`: Number of days to retain (default 90)

**Behavior:**
- Counts audit events older than retention cutoff
- Deletes old events in bulk
- Commits transaction

## Policy Evaluators

All 9 condition types are fully implemented in `app/policy/evaluators.py`:

1. **field_present**: Checks if field exists and is not None
2. **decimal_greater_than**: Compares decimal field to threshold
3. **field_in_set**: Validates field value against allowed set
4. **field_equals_context**: Compares two fields within context
5. **collection_min_size**: Validates collection has minimum size
6. **sum_matches**: Validates sum of collection field matches target within tolerance
7. **all_belong_to**: Validates all collection items belong to parent
8. **one_of_present**: Validates at least one of listed fields is present
9. **flag_is_false**: Validates boolean flag is false (treats None as false)

Each evaluator supports nested field paths using dot notation (e.g., `account.balance`).

## Policy Engine Service

**Evaluation Flow:**
1. Retrieve active rule set for region (or allow by default if none)
2. Load enabled rules for action type
3. Evaluate rules in order (evaluation_order, then rule_code)
4. Collect failed conditions
5. Determine overall result (allow/deny)
6. Create evaluation record with:
   - Rule set version ID (or NULL if no active rule set)
   - All rules applied and their results
   - Failed conditions with messages and parameters
   - Input snapshot for auditability
   - Actor, timestamp, correlation ID

**Deterministic Behavior:**
- Same input + same rule set = same result
- Rules evaluated in fixed order
- No random, no unordered iteration
- Failed conditions identified with rule codes

## Audit Service Security Guard

The audit service (`app/services/audit_service.py`) includes a security guard that removes forbidden fields from audit payloads:

**Forbidden Fields:**
- `password`
- `token`
- `password_hash`
- `access_token`
- `credit_status_indicator`

The `_sanitize_payload` method recursively removes these fields from dicts and lists before storing audit events.

## Evaluation History

Policy evaluation records are append-only and immutable. Each record captures:
- **rule_set_version_id**: Which rule set was used (nullable for no active rule set)
- **evaluation_result**: allow/deny
- **failed_conditions_json**: All failed conditions with details
- **rules_applied_json**: All rules evaluated with pass/fail/error status
- **input_snapshot_json**: Complete input data
- **actor_user_id**, **actor_role_code**: Who performed the action
- **evaluated_at**: Timestamp
- **correlation_id**: Request correlation

Historical evaluations remain unchanged when rule sets are updated. New evaluations use the currently active rule set, but old evaluations retain their original rule set reference and results.

## Database Changes

**Migration:** `ee8b590fbd9a_make_policy_evaluation_rule_set_version_nullable.py`

Made `policy_evaluation_records.rule_set_version_id` nullable to support recording evaluations when no active rule set exists (allow by default scenario).

**Models Updated:**
- `app/models/policy.py`: PolicyEvaluationRecord.rule_set_version_id now nullable

**Services Updated:**
- `app/services/policy_engine_service.py`: Handle null rule_set_version_id, convert subject_entity_id string to UUID

## Tests Added

### Unit Tests (28 tests)
**tests/test_evaluators.py**
- Tests for all 9 condition evaluators
- Happy path and failure cases
- Edge cases (None, empty collections, nested fields)
- Error handling (unknown condition type)

### Service Tests (8 tests)
**tests/test_policy_engine_service.py**
- Evaluation with no active rule set (allow by default)
- Evaluation with all rules passing
- Evaluation with one rule failing
- Evaluation with multiple rules failing
- Input snapshot storage
- Disabled rules not evaluated
- Action type filtering
- Evaluation record persistence

### Acceptance Tests (5 tests)
**tests/test_policy_acceptance.py**

**AC1:** All configured policy validations applied
- Evaluates all enabled rules for action type
- Stores input snapshot
- Records rules_applied_json with pass/fail status
- Persists evaluation record

**AC2:** Policy validation fails → action rejected with failed condition identified
- Denies action when validation fails
- Identifies failed condition by rule_code
- Provides failure details (condition type, message, parameters)
- Records evaluation status for all rules

**AC3:** New rules take effect without altering historical decisions
- v1 rules allow action with amount=50, scope=account_balance
- v1 is superseded, v2 activated (more restrictive)
- v2 rules deny same action
- Historical v1 evaluation record unchanged (still "allow", still references v1)

**Deterministic test:**
- Same input produces same result across multiple evaluations
- Rule evaluation order consistent
- Results reproducible

## Seed Data

Rule set version 1 is seeded with 13 rules:
- Promise validation rules (amount, scope, links, sum matching)
- Queue eligibility rules (dispute flag, deduction flag, evidence indicator, unapplied cash, breach status)

Seed status: "draft" (use activate-rule-set to activate)

## FR-DTC-001 Coverage

**FR-DTC-001:** Deterministic policy enforcement

✅ **AC1:** Given a user attempts a governed action, when the action is evaluated, then all configured policy validations are applied.
- Policy engine loads all enabled rules for action type
- Evaluates each in fixed order
- Records all rules applied and their results

✅ **AC2:** Given a policy validation fails, when the action is submitted, then the action is rejected with the failed condition identified.
- Evaluation result = "deny"
- failed_condition_code identifies first failed rule
- failed_conditions_json contains all failed conditions with details
- Failure message, condition type, and parameters available for UI display

✅ **AC3:** Given policy changes are approved, when new rules take effect, then subsequent actions are validated against the updated rule set without altering historical decisions.
- activate-rule-set CLI supersedes old rule sets
- New evaluations use active rule set
- Historical evaluation records unchanged (immutable, append-only)
- Historical records retain original rule_set_version_id reference

## Related Files

**CLI:**
- `app/cli.py`: activate-rule-set, purge commands

**Models:**
- `app/models/policy.py`: PolicyRuleSetVersion, PolicyRule, PolicyEvaluationRecord

**Services:**
- `app/services/policy_engine_service.py`: evaluate()
- `app/services/audit_service.py`: append() with _sanitize_payload()

**Evaluators:**
- `app/policy/evaluators.py`: ConditionEvaluator, evaluator_registry

**Repositories:**
- `app/repositories/policy_repository.py`: get_active_rule_set, get_rules_for_set, create_evaluation_record, list_evaluations, list_rule_sets

**Tests:**
- `tests/test_evaluators.py`: 28 evaluator tests
- `tests/test_policy_engine_service.py`: 8 service tests
- `tests/test_policy_acceptance.py`: 5 acceptance tests

## Verification

All acceptance checks pass:

```bash
# Evaluator unit tests (28/28 pass)
cd /repos/lbg-ftr-demo-repo/backend && python -m pytest tests/test_evaluators.py -v

# Policy engine service unit tests (8/8 pass)
cd /repos/lbg-ftr-demo-repo/backend && python -m pytest tests/test_policy_engine_service.py -v

# Policy acceptance tests covering FR-DTC-001 (5/5 pass)
cd /repos/lbg-ftr-demo-repo/backend && python -m pytest tests/test_policy_acceptance.py -v

# CLI activation
cd /repos/lbg-ftr-demo-repo/backend && python app/cli.py activate-rule-set --version 1 --approver analyst1
# Output: Successfully activated rule set version 1

# Lint
cd /repos/lbg-ftr-demo-repo/backend && ruff check app
# Only E501 line length warnings from prior tasks; no blocking errors in TASK-5 code
```

## Notes

- Policy evaluation records are append-only (no UPDATE/DELETE methods in repository)
- When no active rule set exists, evaluation allows by default and records with NULL rule_set_version_id
- Evaluators use Decimal for monetary comparisons to avoid floating-point precision issues
- Nested field access supports dict and object attributes
- Correlation IDs thread through all evaluations for request tracing
