"""add_scam_check_outcomes

Revision ID: b8f1d2e3c4a5
Revises: 7cdd87e1f842
Create Date: 2026-11-23 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b8f1d2e3c4a5'
down_revision: str | None = '7cdd87e1f842'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop stub table from initial migration first
    op.drop_table('scam_check_outcomes')
    
    # Create scam_check_outcomes table
    op.create_table('scam_check_outcomes',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_intent_id', sa.Uuid(), nullable=False),
        sa.Column('review_version', sa.Integer(), nullable=False),
        sa.Column('fraud_engine_reference', sa.String(length=128), nullable=True),
        sa.Column('risk_outcome', sa.String(length=12), nullable=False),
        sa.Column('decision_inputs', sa.JSON().with_variant(JSONB, 'postgresql'), nullable=False),
        sa.Column('decision_latency_ms', sa.Integer(), nullable=True),
        sa.Column('customer_warning_required', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('policy_allows_continue', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('customer_warning_presented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customer_decision', sa.String(length=14), nullable=False, server_default='not_applicable'),
        sa.Column('customer_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('hold_latest_decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('correlation_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('review_version >= 1', name='ck_sco_review_version'),
        sa.CheckConstraint("risk_outcome IN ('allow','warn','hold','unavailable')", name='ck_sco_risk_outcome'),
        sa.CheckConstraint('decision_latency_ms IS NULL OR decision_latency_ms >= 0', name='ck_sco_latency'),
        sa.CheckConstraint("customer_decision IN ('not_applicable','pending','stopped','continued')", name='ck_sco_customer_decision'),
        sa.CheckConstraint("customer_decision <> 'continued' OR (policy_allows_continue = TRUE AND customer_warning_presented_at IS NOT NULL)", name='ck_sco_continue_needs_policy'),
        sa.CheckConstraint("customer_warning_required = (risk_outcome = 'warn')", name='ck_sco_warn_flag'),
        sa.ForeignKeyConstraint(['payment_intent_id'], ['payment_intents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_intent_id', 'review_version', name='uq_sco_payment_version')
    )
    
    # Create indexes
    op.create_index('ix_sco_payment', 'scam_check_outcomes', ['payment_intent_id'])
    op.create_index('ix_sco_correlation', 'scam_check_outcomes', ['correlation_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_sco_correlation', table_name='scam_check_outcomes')
    op.drop_index('ix_sco_payment', table_name='scam_check_outcomes')
    
    # Drop table
    op.drop_table('scam_check_outcomes')
