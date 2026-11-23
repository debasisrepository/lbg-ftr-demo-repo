"""add outbox execution status projection consumed_events

Revision ID: 20261123_0010
Revises: 20261122_2400
Create Date: 2026-11-23 00:10:00.000000

"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'b8f1d2e3c4a5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop stub tables from initial migration first
    op.drop_table('consumed_events')
    op.drop_table('payment_status_projections')
    op.drop_table('payment_outbox_events')
    op.drop_table('payment_execution_statuses')
    
    # payment_outbox_events
    op.create_table(
        'payment_outbox_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_intent_id', sa.Uuid(), nullable=False),
        sa.Column('state_transition_id', sa.Uuid(), nullable=True),
        sa.Column('event_sequence', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=48), nullable=False),
        sa.Column('event_payload', sa.JSON().with_variant(postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('publish_state', sa.String(length=12), nullable=False, server_default='pending'),
        sa.Column('attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error_code', sa.String(length=48), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('event_stream_reference', sa.String(length=128), nullable=True),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('event_sequence >= 1', name='ck_poe_sequence'),
        sa.CheckConstraint("publish_state IN ('pending','published','failed','retrying')", name='ck_poe_publish_state'),
        sa.CheckConstraint('attempt_count >= 0', name='ck_poe_attempt_count'),
        sa.ForeignKeyConstraint(['payment_intent_id'], ['payment_intents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('state_transition_id', name='uq_poe_state_transition')
    )
    op.create_index('ix_poe_payment', 'payment_outbox_events', ['payment_intent_id'], unique=False)
    op.create_index('ix_poe_publish_state', 'payment_outbox_events', ['publish_state'], unique=False)
    op.create_index('ix_poe_next_attempt', 'payment_outbox_events', ['next_attempt_at'], unique=False)
    op.create_index('ix_poe_correlation', 'payment_outbox_events', ['correlation_id'], unique=False)
    
    # payment_execution_statuses
    op.create_table(
        'payment_execution_statuses',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_intent_id', sa.Uuid(), nullable=False),
        sa.Column('hub_submission_reference', sa.String(length=64), nullable=True),
        sa.Column('scheme_transaction_reference', sa.String(length=64), nullable=True),
        sa.Column('scheme_outcome', sa.String(length=12), nullable=False),
        sa.Column('scheme_outcome_code', sa.String(length=48), nullable=True),
        sa.Column('expected_arrival_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hub_response_latency_ms', sa.Integer(), nullable=True),
        sa.Column('submission_attempt_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_submission_error', sa.String(length=128), nullable=True),
        sa.Column('final_indicator', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('provenance_reference', sa.String(length=128), nullable=True),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("scheme_outcome IN ('accepted','rejected','pending','timeout','unknown')", name='ck_pes_scheme_outcome'),
        sa.CheckConstraint('hub_response_latency_ms >= 0', name='ck_pes_latency'),
        sa.CheckConstraint('submission_attempt_count >= 0', name='ck_pes_attempts'),
        sa.ForeignKeyConstraint(['payment_intent_id'], ['payment_intents.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_intent_id', name='uq_pes_payment')
    )
    op.create_index('ix_pes_hub_ref', 'payment_execution_statuses', ['hub_submission_reference'], unique=False)
    op.create_index('ix_pes_scheme_ref', 'payment_execution_statuses', ['scheme_transaction_reference'], unique=False)
    op.create_index('ix_pes_correlation', 'payment_execution_statuses', ['correlation_id'], unique=False)
    
    # payment_status_projections
    op.create_table(
        'payment_status_projections',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_intent_id', sa.Uuid(), nullable=False),
        sa.Column('customer_profile_ref_id', sa.Uuid(), nullable=False),
        sa.Column('payment_reference_text', sa.String(length=18), nullable=False),
        sa.Column('amount_minor', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.CHAR(length=3), nullable=False, server_default='GBP'),
        sa.Column('payee_display_name', sa.String(length=120), nullable=False),
        sa.Column('customer_visible_status', sa.String(length=8), nullable=False),
        sa.Column('held_indicator', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unresolved_indicator', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('do_not_resubmit', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expected_arrival_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hold_latest_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_event_sequence', sa.BigInteger(), nullable=False),
        sa.Column('last_source_event_id', sa.String(length=64), nullable=True),
        sa.Column('as_of_timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('freshness_status', sa.String(length=14), nullable=False, server_default='within_target'),
        sa.Column('provenance_reference', sa.String(length=128), nullable=True),
        sa.Column('projection_updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('amount_minor > 0', name='ck_psp_amount'),
        sa.CheckConstraint("customer_visible_status IN ('Sent','Pending','Failed')", name='ck_psp_status'),
        sa.CheckConstraint('last_event_sequence >= 0', name='ck_psp_sequence'),
        sa.CheckConstraint("freshness_status IN ('within_target','breached','unknown')", name='ck_psp_freshness'),
        sa.CheckConstraint("(customer_visible_status = 'Pending') = do_not_resubmit", name='ck_psp_pending_no_resubmit'),
        sa.ForeignKeyConstraint(['payment_intent_id'], ['payment_intents.id'], ),
        sa.ForeignKeyConstraint(['customer_profile_ref_id'], ['customer_profile_refs.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_intent_id', name='uq_psp_payment')
    )
    op.create_index('ix_psp_customer', 'payment_status_projections', ['customer_profile_ref_id'], unique=False)
    op.create_index('ix_psp_status', 'payment_status_projections', ['customer_visible_status'], unique=False)
    op.create_index('ix_psp_reference', 'payment_status_projections', ['payment_reference_text'], unique=False)
    
    # consumed_events
    op.create_table(
        'consumed_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('consumer_name', sa.String(length=32), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('event_type', sa.String(length=48), nullable=False),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint("consumer_name IN ('read_model_accounts','read_model_payments','status_and_flags','notifications')", name='ck_ce_consumer'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_ce_consumer_event', 'consumed_events', ['consumer_name', 'event_id'], unique=True)
    op.create_index('ix_ce_correlation', 'consumed_events', ['correlation_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_ce_correlation', table_name='consumed_events')
    op.drop_index('ix_ce_consumer_event', table_name='consumed_events')
    op.drop_table('consumed_events')
    
    op.drop_index('ix_psp_reference', table_name='payment_status_projections')
    op.drop_index('ix_psp_status', table_name='payment_status_projections')
    op.drop_index('ix_psp_customer', table_name='payment_status_projections')
    op.drop_table('payment_status_projections')
    
    op.drop_index('ix_pes_correlation', table_name='payment_execution_statuses')
    op.drop_index('ix_pes_scheme_ref', table_name='payment_execution_statuses')
    op.drop_index('ix_pes_hub_ref', table_name='payment_execution_statuses')
    op.drop_table('payment_execution_statuses')
    
    op.drop_index('ix_poe_correlation', table_name='payment_outbox_events')
    op.drop_index('ix_poe_next_attempt', table_name='payment_outbox_events')
    op.drop_index('ix_poe_publish_state', table_name='payment_outbox_events')
    op.drop_index('ix_poe_payment', table_name='payment_outbox_events')
    op.drop_table('payment_outbox_events')
