"""add incident_report table

Revision ID: 2_add_incident_report
Revises: 1bccdcbe3fda
Create Date: 2026-11-22 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2_add_incident_report'
down_revision: Union[str, None] = '1bccdcbe3fda'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create incident_report table
    op.create_table(
        'incident_report',
        sa.Column('incident_report_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_reference', sa.String(length=64), nullable=False),
        sa.Column('incident_category', sa.String(length=64), nullable=False),
        sa.Column('incident_title', sa.String(length=255), nullable=False),
        sa.Column('incident_description', sa.String(length=2000), nullable=True),
        sa.Column('severity', sa.String(length=16), nullable=False, server_default='medium'),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='reported'),
        sa.Column('external_incident_ref', sa.String(length=128), nullable=True),
        sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('correlation_id', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('incident_report_id', name='pk_incident_report'),
        sa.CheckConstraint(
            "incident_category IN ('technical_issue', 'service_outage', 'data_issue', 'security_concern', 'other')",
            name='ck_incident_category'
        ),
        sa.CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name='ck_incident_severity'
        ),
        sa.CheckConstraint(
            "status IN ('reported', 'acknowledged', 'investigating', 'resolved', 'closed')",
            name='ck_incident_status'
        ),
    )
    
    # Create indexes
    op.create_index('idx_incident_customer', 'incident_report', ['customer_id', 'reported_at'])
    op.create_index('idx_incident_reference', 'incident_report', ['incident_reference'], unique=True)
    op.create_index('idx_incident_status', 'incident_report', ['status', 'reported_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_incident_status', table_name='incident_report')
    op.drop_index('idx_incident_reference', table_name='incident_report')
    op.drop_index('idx_incident_customer', table_name='incident_report')
    
    # Drop table
    op.drop_table('incident_report')
