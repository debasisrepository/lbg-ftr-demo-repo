"""add_audit_event_columns

Revision ID: af7ea19fc223
Revises: d772c23783b1
Create Date: 2026-11-23 03:09:38.365808+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from datetime import UTC, datetime


# revision identifiers, used by Alembic.
revision: str = 'af7ea19fc223'
down_revision: Union[str, None] = 'd772c23783b1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add columns to audit_events table
    with op.batch_alter_table('audit_events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('event_type', sa.String(64), nullable=False, server_default='unknown'))
        batch_op.add_column(sa.Column('actor_type', sa.String(32), nullable=False, server_default='system'))
        batch_op.add_column(sa.Column('actor_reference', sa.String(128), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('resource_type', sa.String(32), nullable=False, server_default='unknown'))
        batch_op.add_column(sa.Column('resource_reference', sa.String(128), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('action_category', sa.String(32), nullable=False, server_default='unknown'))
        batch_op.add_column(sa.Column('action_detail', sa.String(64), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('outcome', sa.String(16), nullable=False, server_default='unknown'))
        batch_op.add_column(sa.Column('correlation_id', sa.String(64), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))


def downgrade() -> None:
    # Drop columns from audit_events table
    with op.batch_alter_table('audit_events', schema=None) as batch_op:
        batch_op.drop_column('occurred_at')
        batch_op.drop_column('correlation_id')
        batch_op.drop_column('outcome')
        batch_op.drop_column('action_detail')
        batch_op.drop_column('action_category')
        batch_op.drop_column('resource_reference')
        batch_op.drop_column('resource_type')
        batch_op.drop_column('actor_reference')
        batch_op.drop_column('actor_type')
        batch_op.drop_column('event_type')
