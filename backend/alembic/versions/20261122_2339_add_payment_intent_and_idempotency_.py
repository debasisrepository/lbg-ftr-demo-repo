"""add_payment_intent_and_idempotency_tables

Revision ID: 20261122_2339
Revises: 20261122_2323
Create Date: 2026-11-22 23:39:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'e4f6c9a1b2d3'
down_revision: str | None = 'bc93b66cb03c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop stub tables from initial migration first
    op.drop_table('idempotency_records')
    op.drop_table('payment_intents')
    
    # Create payment_intents table with all 23 columns
    op.create_table(
        'payment_intents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('customer_profile_ref_id', sa.Uuid(), nullable=False),
        sa.Column('source_account_reference', sa.String(length=64), nullable=False),
        sa.Column('payee_id', sa.Uuid(), nullable=False),
        sa.Column('amount_minor', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('payment_reference_text', sa.String(length=18), nullable=False),
        sa.Column('payment_channel', sa.String(length=8), nullable=False),
        sa.Column('initiation_type', sa.String(length=24), nullable=False),
        sa.Column('review_version', sa.Integer(), nullable=False),
        sa.Column('review_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('current_state', sa.String(length=32), nullable=False),
        sa.Column('customer_visible_status', sa.String(length=8), nullable=True),
        sa.Column('do_not_resubmit', sa.Boolean(), nullable=False),
        sa.Column('expected_arrival_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payments_hub_reference', sa.String(length=64), nullable=True),
        sa.Column('hold_latest_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customer_reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_state_changed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('row_version', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('amount_minor > 0', name='ck_pi_amount_positive'),
        sa.CheckConstraint('review_version >= 1', name='ck_pi_review_version'),
        sa.CheckConstraint('row_version >= 1', name='ck_pi_row_version'),
        sa.CheckConstraint("length(payment_reference_text) >= 1", name='ck_pi_payment_reference_length'),
        sa.CheckConstraint("payment_channel IN ('mobile')", name='ck_pi_payment_channel'),
        sa.CheckConstraint("initiation_type IN ('saved_payee_payment')", name='ck_pi_initiation_type'),
        sa.CheckConstraint(
            "current_state IN ('draft', 'review_ready', 'awaiting_dynamic_link_approval', 'approval_failed_or_abandoned', 'fraud_check_in_progress', 'warning_presented', 'stopped_after_warning', 'held_for_review', 'submission_in_progress', 'submitted_to_payments_hub', 'pending_confirmation', 'completed', 'failed', 'rejected', 'unknown_unresolved')",
            name='ck_pi_current_state'
        ),
        sa.CheckConstraint("customer_visible_status IS NULL OR customer_visible_status IN ('Sent', 'Pending', 'Failed')", name='ck_pi_status_mapping'),
        sa.ForeignKeyConstraint(['customer_profile_ref_id'], ['customer_profile_refs.id'], ),
        sa.ForeignKeyConstraint(['payee_id'], ['payees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_payment_intents_customer_profile_ref_id'), 'payment_intents', ['customer_profile_ref_id'], unique=False)
    op.create_index(op.f('ix_payment_intents_current_state'), 'payment_intents', ['current_state'], unique=False)
    op.create_index(op.f('ix_payment_intents_payee_id'), 'payment_intents', ['payee_id'], unique=False)

    # Create idempotency_records table with all columns
    op.create_table(
        'idempotency_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('customer_profile_ref_id', sa.Uuid(), nullable=False),
        sa.Column('payment_intent_id', sa.Uuid(), nullable=False),
        sa.Column('operation_type', sa.String(length=16), nullable=False),
        sa.Column('idempotency_key', sa.String(length=64), nullable=False),
        sa.Column('request_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('resolution_state', sa.String(length=24), nullable=False),
        sa.Column('response_status_code', sa.Integer(), nullable=True),
        sa.Column('returned_response_reference', sa.String(length=128), nullable=True),
        sa.Column('replay_count', sa.Integer(), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("operation_type IN ('payment_review', 'payment_submit')", name='ck_ir_operation_type'),
        sa.CheckConstraint("resolution_state IN ('in_progress', 'resolved_success', 'resolved_failure', 'linked_existing_result')", name='ck_ir_resolution_state'),
        sa.CheckConstraint('response_status_code IS NULL OR (response_status_code >= 100 AND response_status_code <= 599)', name='ck_ir_response_status_code'),
        sa.CheckConstraint('replay_count >= 0', name='ck_ir_replay_count'),
        sa.ForeignKeyConstraint(['customer_profile_ref_id'], ['customer_profile_refs.id'], ),
        sa.ForeignKeyConstraint(['payment_intent_id'], ['payment_intents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('customer_profile_ref_id', 'operation_type', 'idempotency_key', name='uq_idempotency_key_per_customer_operation')
    )
    op.create_index(op.f('ix_idempotency_records_customer_profile_ref_id'), 'idempotency_records', ['customer_profile_ref_id'], unique=False)
    op.create_index(op.f('ix_idempotency_records_idempotency_key'), 'idempotency_records', ['idempotency_key'], unique=False)
    op.create_index(op.f('ix_idempotency_records_payment_intent_id'), 'idempotency_records', ['payment_intent_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_idempotency_records_payment_intent_id'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_idempotency_key'), table_name='idempotency_records')
    op.drop_index(op.f('ix_idempotency_records_customer_profile_ref_id'), table_name='idempotency_records')
    op.drop_table('idempotency_records')
    op.drop_index(op.f('ix_payment_intents_payee_id'), table_name='payment_intents')
    op.drop_index(op.f('ix_payment_intents_current_state'), table_name='payment_intents')
    op.drop_index(op.f('ix_payment_intents_customer_profile_ref_id'), table_name='payment_intents')
    op.drop_table('payment_intents')
