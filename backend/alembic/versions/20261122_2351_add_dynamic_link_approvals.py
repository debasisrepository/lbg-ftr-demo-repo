"""add_dynamic_link_approvals

Revision ID: 7cdd87e1f842
Revises: 20261122_2339_add_payment_intent_and_idempotency_
Create Date: 2026-11-22 23:51:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '7cdd87e1f842'
down_revision: str | None = 'e4f6c9a1b2d3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Drop stub table from initial migration first
    op.drop_table('dynamic_link_approvals')
    
    # Create dynamic_link_approvals table
    op.create_table('dynamic_link_approvals',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('payment_intent_id', sa.Uuid(), nullable=False),
        sa.Column('review_version', sa.Integer(), nullable=False),
        sa.Column('review_fingerprint', sa.String(length=64), nullable=False),
        sa.Column('source_account_reference', sa.String(length=64), nullable=False),
        sa.Column('payee_id', sa.Uuid(), nullable=False),
        sa.Column('approved_amount_minor', sa.BigInteger(), nullable=False),
        sa.Column('approved_currency', sa.String(length=3), nullable=False),
        sa.Column('approved_reference_text', sa.String(length=18), nullable=False),
        sa.Column('approval_challenge_reference', sa.String(length=128), nullable=False),
        sa.Column('signed_approval_reference', sa.String(length=256), nullable=True),
        sa.Column('approval_outcome', sa.String(length=12), nullable=False, server_default='pending'),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('correlation_id', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.CheckConstraint('review_version >= 1', name='ck_dla_review_version'),
        sa.CheckConstraint('approved_amount_minor > 0', name='ck_dla_amount'),
        sa.CheckConstraint("approval_outcome IN ('pending','success','failed','abandoned','expired')", name='ck_dla_outcome'),
        sa.CheckConstraint("approval_outcome <> 'success' OR (approved_at IS NOT NULL AND signed_approval_reference IS NOT NULL)", name='ck_dla_success_complete'),
        sa.ForeignKeyConstraint(['payment_intent_id'], ['payment_intents.id'], ),
        sa.ForeignKeyConstraint(['payee_id'], ['payees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_dla_correlation', 'dynamic_link_approvals', ['correlation_id'], unique=False)
    op.create_index('ix_dla_payment', 'dynamic_link_approvals', ['payment_intent_id'], unique=False)
    op.create_index('ix_dla_payee', 'dynamic_link_approvals', ['payee_id'], unique=False)
    
    # Create partial unique index for successful approvals
    with op.batch_alter_table('dynamic_link_approvals') as batch_op:
        batch_op.create_index(
            'ix_dla_payment_version_success',
            ['payment_intent_id', 'review_version'],
            unique=True,
            sqlite_where=sa.text("approval_outcome = 'success'"),
            postgresql_where=sa.text("approval_outcome = 'success'")
        )


def downgrade() -> None:
    op.drop_index('ix_dla_payment_version_success', table_name='dynamic_link_approvals')
    op.drop_index('ix_dla_payee', table_name='dynamic_link_approvals')
    op.drop_index('ix_dla_payment', table_name='dynamic_link_approvals')
    op.drop_index('ix_dla_correlation', table_name='dynamic_link_approvals')
    op.drop_table('dynamic_link_approvals')
