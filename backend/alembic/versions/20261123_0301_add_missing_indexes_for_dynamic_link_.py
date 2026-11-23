"""add_missing_indexes_for_dynamic_link_and_scam_check

Revision ID: d772c23783b1
Revises: d1e2f3a4b5c6
Create Date: 2026-11-23 03:01:27.912528+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd772c23783b1'
down_revision: Union[str, None] = 'd1e2f3a4b5c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add missing indexes for dynamic_link_approvals
    with op.batch_alter_table('dynamic_link_approvals', schema=None) as batch_op:
        batch_op.create_index('ix_dynamic_link_approvals_correlation_id', ['correlation_id'], unique=False)
        batch_op.create_index('ix_dynamic_link_approvals_payee_id', ['payee_id'], unique=False)
        batch_op.create_index('ix_dynamic_link_approvals_payment_intent_id', ['payment_intent_id'], unique=False)
    
    # Add missing indexes for scam_check_outcomes
    with op.batch_alter_table('scam_check_outcomes', schema=None) as batch_op:
        batch_op.create_index('ix_scam_check_outcomes_correlation_id', ['correlation_id'], unique=False)
        batch_op.create_index('ix_scam_check_outcomes_payment_intent_id', ['payment_intent_id'], unique=False)


def downgrade() -> None:
    # Drop indexes for scam_check_outcomes
    with op.batch_alter_table('scam_check_outcomes', schema=None) as batch_op:
        batch_op.drop_index('ix_scam_check_outcomes_payment_intent_id')
        batch_op.drop_index('ix_scam_check_outcomes_correlation_id')
    
    # Drop indexes for dynamic_link_approvals
    with op.batch_alter_table('dynamic_link_approvals', schema=None) as batch_op:
        batch_op.drop_index('ix_dynamic_link_approvals_payment_intent_id')
        batch_op.drop_index('ix_dynamic_link_approvals_payee_id')
        batch_op.drop_index('ix_dynamic_link_approvals_correlation_id')
