"""initial schema

Revision ID: 001
Revises: 
Create Date: 2026-11-19 10:00:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # user_identity
    op.create_table(
        'user_identity',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('external_identity_id', sa.String(length=100), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_identity_id'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_user_identity_external_id', 'user_identity', ['external_identity_id'])
    op.create_index('ix_user_identity_username', 'user_identity', ['username'])

    # auth_session
    op.create_table(
        'auth_session',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_identity_id', sa.Integer(), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('session_state', sa.String(length=20), nullable=False),
        sa.Column('issued_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('active_profile_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_identity_id'], ['user_identity.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index('ix_auth_session_state', 'auth_session', ['session_state'])
    op.create_index('ix_auth_session_token_hash', 'auth_session', ['token_hash'])
    op.create_index('ix_auth_session_user_identity_id', 'auth_session', ['user_identity_id'])

    # registered_device
    op.create_table(
        'registered_device',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_identity_id', sa.Integer(), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=False),
        sa.Column('device_label', sa.String(length=100), nullable=False),
        sa.Column('public_key_ref', sa.String(length=255), nullable=True),
        sa.Column('biometric_enabled', sa.Boolean(), nullable=False),
        sa.Column('passcode_enabled', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_identity_id'], ['user_identity.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('device_id')
    )
    op.create_index('ix_registered_device_device_id', 'registered_device', ['device_id'])
    op.create_index('ix_registered_device_user_identity_id', 'registered_device', ['user_identity_id'])

    # step_up_challenge
    op.create_table(
        'step_up_challenge',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('auth_session_id', sa.Integer(), nullable=False),
        sa.Column('payment_instruction_id', sa.Integer(), nullable=True),
        sa.Column('challenge_type', sa.String(length=30), nullable=False),
        sa.Column('method', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('device_id', sa.String(length=100), nullable=True),
        sa.Column('attempts_used', sa.Integer(), nullable=False),
        sa.Column('max_attempts', sa.Integer(), nullable=False),
        sa.Column('dynamic_link_hash', sa.String(length=64), nullable=True),
        sa.Column('challenge_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['auth_session_id'], ['auth_session.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_step_up_challenge_auth_session_id', 'step_up_challenge', ['auth_session_id'])
    op.create_index('ix_step_up_challenge_payment_instruction_id', 'step_up_challenge', ['payment_instruction_id'])
    op.create_index('ix_step_up_challenge_status', 'step_up_challenge', ['status'])

    # user_profile
    op.create_table(
        'user_profile',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_identity_id', sa.Integer(), nullable=False),
        sa.Column('profile_type', sa.String(length=20), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('business_name', sa.String(length=255), nullable=True),
        sa.Column('external_profile_id', sa.String(length=100), nullable=False),
        sa.Column('is_default', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['user_identity_id'], ['user_identity.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('external_profile_id')
    )
    op.create_index('ix_user_profile_external_id', 'user_profile', ['external_profile_id'])
    op.create_index('ix_user_profile_user_identity_id', 'user_profile', ['user_identity_id'])

    # profile_entitlement
    op.create_table(
        'profile_entitlement',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('account_external_id', sa.String(length=100), nullable=False),
        sa.Column('can_view_accounts', sa.Boolean(), nullable=False),
        sa.Column('can_create_payee', sa.Boolean(), nullable=False),
        sa.Column('can_approve_payment', sa.Boolean(), nullable=False),
        sa.Column('entitlement_source_version', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_profile_entitlement_account_external_id', 'profile_entitlement', ['account_external_id'])
    op.create_index('ix_profile_entitlement_profile_id', 'profile_entitlement', ['profile_id'])

    # account_snapshot
    op.create_table(
        'account_snapshot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('external_account_id', sa.String(length=100), nullable=False),
        sa.Column('account_type', sa.String(length=30), nullable=False),
        sa.Column('account_name', sa.String(length=100), nullable=False),
        sa.Column('masked_account_number', sa.String(length=20), nullable=False),
        sa.Column('sort_code', sa.String(length=10), nullable=True),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('current_balance_minor', sa.BigInteger(), nullable=False),
        sa.Column('available_balance_minor', sa.BigInteger(), nullable=True),
        sa.Column('overdraft_available_minor', sa.BigInteger(), nullable=True),
        sa.Column('available_credit_minor', sa.BigInteger(), nullable=True),
        sa.Column('freshness_state', sa.String(length=20), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_account_snapshot_external_id', 'account_snapshot', ['external_account_id'])
    op.create_index('ix_account_snapshot_profile_id', 'account_snapshot', ['profile_id'])

    # account_data_gap
    op.create_table(
        'account_data_gap',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('source_system', sa.String(length=50), nullable=False),
        sa.Column('freshness_state', sa.String(length=20), nullable=False),
        sa.Column('message', sa.String(length=500), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cleared_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_account_data_gap_profile_id', 'account_data_gap', ['profile_id'])

    # loan_context_snapshot
    op.create_table(
        'loan_context_snapshot',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('account_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('next_repayment_amount_minor', sa.BigInteger(), nullable=True),
        sa.Column('next_repayment_due_date', sa.Date(), nullable=True),
        sa.Column('source_state', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['account_snapshot_id'], ['account_snapshot.id']),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_loan_context_snapshot_account_snapshot_id', 'loan_context_snapshot', ['account_snapshot_id'])
    op.create_index('ix_loan_context_snapshot_profile_id', 'loan_context_snapshot', ['profile_id'])

    # payee
    op.create_table(
        'payee',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=True),
        sa.Column('sort_code', sa.String(length=10), nullable=False),
        sa.Column('account_number_last4', sa.String(length=4), nullable=False),
        sa.Column('account_number_hash', sa.String(length=64), nullable=False),
        sa.Column('can_proceed', sa.Boolean(), nullable=False),
        sa.Column('created_in_journey', sa.Boolean(), nullable=False),
        sa.Column('payee_action_sca_verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payee_account_number_hash', 'payee', ['account_number_hash'])
    op.create_index('ix_payee_profile_id', 'payee', ['profile_id'])

    # cop_result
    op.create_table(
        'cop_result',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payee_id', sa.Integer(), nullable=False),
        sa.Column('result_code', sa.String(length=20), nullable=False),
        sa.Column('decision_state', sa.String(length=20), nullable=False),
        sa.Column('provider_reference', sa.String(length=100), nullable=True),
        sa.Column('returned_name', sa.String(length=255), nullable=True),
        sa.Column('warning_message', sa.String(length=500), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('override_confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['payee_id'], ['payee.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cop_result_payee_id', 'cop_result', ['payee_id'])

    # payment_instruction
    op.create_table(
        'payment_instruction',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('auth_session_id', sa.Integer(), nullable=False),
        sa.Column('source_account_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('payee_id', sa.Integer(), nullable=False),
        sa.Column('amount_minor', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('reference_text', sa.String(length=255), nullable=True),
        sa.Column('client_idempotency_key', sa.String(length=100), nullable=False),
        sa.Column('payment_reference', sa.String(length=100), nullable=True),
        sa.Column('instruction_state', sa.String(length=20), nullable=False),
        sa.Column('duplicate_submission_blocked', sa.Boolean(), nullable=False),
        sa.Column('expected_arrival_message', sa.String(length=500), nullable=True),
        sa.Column('failure_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['auth_session_id'], ['auth_session.id']),
        sa.ForeignKeyConstraint(['payee_id'], ['payee.id']),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.ForeignKeyConstraint(['source_account_snapshot_id'], ['account_snapshot.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('client_idempotency_key')
    )
    op.create_index('ix_payment_instruction_auth_session_id', 'payment_instruction', ['auth_session_id'])
    op.create_index('ix_payment_instruction_client_idempotency_key', 'payment_instruction', ['client_idempotency_key'])
    op.create_index('ix_payment_instruction_payee_id', 'payment_instruction', ['payee_id'])
    op.create_index('ix_payment_instruction_profile_id', 'payment_instruction', ['profile_id'])
    op.create_index('ix_payment_instruction_source_account_snapshot_id', 'payment_instruction', ['source_account_snapshot_id'])
    op.create_index('ix_payment_instruction_state', 'payment_instruction', ['instruction_state'])

    # fraud_decision
    op.create_table(
        'fraud_decision',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_instruction_id', sa.Integer(), nullable=False),
        sa.Column('decision_code', sa.String(length=20), nullable=False),
        sa.Column('warning_message', sa.String(length=500), nullable=True),
        sa.Column('hold_reason', sa.String(length=500), nullable=True),
        sa.Column('provider_reference', sa.String(length=100), nullable=True),
        sa.Column('decided_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['payment_instruction_id'], ['payment_instruction.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fraud_decision_payment_instruction_id', 'fraud_decision', ['payment_instruction_id'])

    # payment_approval
    op.create_table(
        'payment_approval',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_instruction_id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=True),
        sa.Column('sca_method', sa.String(length=20), nullable=False),
        sa.Column('dynamic_link_hash', sa.String(length=64), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['challenge_id'], ['step_up_challenge.id']),
        sa.ForeignKeyConstraint(['payment_instruction_id'], ['payment_instruction.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payment_approval_challenge_id', 'payment_approval', ['challenge_id'])
    op.create_index('ix_payment_approval_payment_instruction_id', 'payment_approval', ['payment_instruction_id'])

    # payment_status_history
    op.create_table(
        'payment_status_history',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_instruction_id', sa.Integer(), nullable=False),
        sa.Column('status_code', sa.String(length=20), nullable=False),
        sa.Column('rail_reference', sa.String(length=100), nullable=True),
        sa.Column('reason_code', sa.String(length=50), nullable=True),
        sa.Column('reason_detail', sa.String(length=500), nullable=True),
        sa.Column('effective_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['payment_instruction_id'], ['payment_instruction.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payment_status_history_payment_instruction_id', 'payment_status_history', ['payment_instruction_id'])
    op.create_index('ix_payment_status_history_status_code', 'payment_status_history', ['status_code'])

    # notification_dispatch
    op.create_table(
        'notification_dispatch',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('payment_instruction_id', sa.Integer(), nullable=True),
        sa.Column('auth_session_id', sa.Integer(), nullable=True),
        sa.Column('notification_type', sa.String(length=30), nullable=False),
        sa.Column('provider_reference', sa.String(length=100), nullable=True),
        sa.Column('dispatch_state', sa.String(length=20), nullable=False),
        sa.Column('dispatched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['auth_session_id'], ['auth_session.id']),
        sa.ForeignKeyConstraint(['payment_instruction_id'], ['payment_instruction.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notification_dispatch_auth_session_id', 'notification_dispatch', ['auth_session_id'])
    op.create_index('ix_notification_dispatch_payment_instruction_id', 'notification_dispatch', ['payment_instruction_id'])

    # audit_log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('auth_session_id', sa.Integer(), nullable=True),
        sa.Column('user_identity_id', sa.Integer(), nullable=True),
        sa.Column('entity_type', sa.String(length=50), nullable=True),
        sa.Column('entity_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['auth_session_id'], ['auth_session.id']),
        sa.ForeignKeyConstraint(['user_identity_id'], ['user_identity.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_audit_log_auth_session_id', 'audit_log', ['auth_session_id'])
    op.create_index('ix_audit_log_correlation_id', 'audit_log', ['correlation_id'])
    op.create_index('ix_audit_log_entity_id', 'audit_log', ['entity_id'])
    op.create_index('ix_audit_log_event_type', 'audit_log', ['event_type'])
    op.create_index('ix_audit_log_occurred_at', 'audit_log', ['occurred_at'])
    op.create_index('ix_audit_log_user_identity_id', 'audit_log', ['user_identity_id'])

    # journey_event
    op.create_table(
        'journey_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('correlation_id', sa.String(length=100), nullable=False),
        sa.Column('auth_session_id', sa.Integer(), nullable=True),
        sa.Column('profile_id', sa.Integer(), nullable=True),
        sa.Column('journey_step', sa.String(length=30), nullable=False),
        sa.Column('outcome_code', sa.String(length=30), nullable=False),
        sa.Column('failure_reason', sa.String(length=500), nullable=True),
        sa.Column('event_payload_json', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['auth_session_id'], ['auth_session.id']),
        sa.ForeignKeyConstraint(['profile_id'], ['user_profile.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_journey_event_auth_session_id', 'journey_event', ['auth_session_id'])
    op.create_index('ix_journey_event_correlation_id', 'journey_event', ['correlation_id'])
    op.create_index('ix_journey_event_journey_step', 'journey_event', ['journey_step'])
    op.create_index('ix_journey_event_occurred_at', 'journey_event', ['occurred_at'])
    op.create_index('ix_journey_event_profile_id', 'journey_event', ['profile_id'])


def downgrade() -> None:
    op.drop_table('journey_event')
    op.drop_table('audit_log')
    op.drop_table('notification_dispatch')
    op.drop_table('payment_status_history')
    op.drop_table('payment_approval')
    op.drop_table('fraud_decision')
    op.drop_table('payment_instruction')
    op.drop_table('cop_result')
    op.drop_table('payee')
    op.drop_table('loan_context_snapshot')
    op.drop_table('account_data_gap')
    op.drop_table('account_snapshot')
    op.drop_table('profile_entitlement')
    op.drop_table('user_profile')
    op.drop_table('step_up_challenge')
    op.drop_table('registered_device')
    op.drop_table('auth_session')
    op.drop_table('user_identity')
