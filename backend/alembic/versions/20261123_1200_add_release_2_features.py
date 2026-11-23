"""add_release_2_features

Revision ID: r2_release_2_features
Revises: af7ea19fc223
Create Date: 2026-11-23 12:00:00.000000

Release 2: Loans, Business Profiles and Scam Reporting
- Add loan fields to account_read_models
- Add business_name to customer_profile_refs
- Add business_profile_read_models table
- Add scam_reports table
- Add incident_reports table for PS26/2 readiness
- Add material_third_party_register table
- Add entitlement_type to sandbox_entitlements

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic.
revision = 'r2_release_2_features'
down_revision = 'af7ea19fc223'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get connection to check dialect
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # 1. Add loan fields to account_read_models (check if they exist first)
    columns = [col['name'] for col in inspector.get_columns('account_read_models')]
    
    if 'loan_outstanding_balance_minor' not in columns:
        op.add_column('account_read_models', sa.Column('loan_outstanding_balance_minor', sa.BigInteger(), nullable=True))
    if 'loan_next_repayment_date' not in columns:
        op.add_column('account_read_models', sa.Column('loan_next_repayment_date', sa.Date(), nullable=True))
    if 'loan_next_repayment_amount_minor' not in columns:
        op.add_column('account_read_models', sa.Column('loan_next_repayment_amount_minor', sa.BigInteger(), nullable=True))
    if 'loan_remaining_term_months' not in columns:
        op.add_column('account_read_models', sa.Column('loan_remaining_term_months', sa.Integer(), nullable=True))
    
    # 2. Add business_name field to customer_profile_refs for business profiles
    cpr_columns = [col['name'] for col in inspector.get_columns('customer_profile_refs')]
    if 'business_name' not in cpr_columns:
        op.add_column('customer_profile_refs', sa.Column('business_name', sa.String(length=160), nullable=True))
    
    # Note: For SQLite, the CHECK constraint update for profile_type must be done manually
    # by running fix_constraint.py or by recreating the database.
    # PostgreSQL would support ALTER TABLE ... DROP CONSTRAINT / ADD CONSTRAINT.
    
    # 3. Create business_profile_read_models table
    if 'business_profile_read_models' not in inspector.get_table_names():
        op.create_table(
            'business_profile_read_models',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('customer_profile_ref_id', sa.String(length=36), nullable=False),
            sa.Column('business_name', sa.String(length=160), nullable=False),
            sa.Column('business_account_system_reference', sa.String(length=64), nullable=False),
            sa.Column('account_type', sa.String(length=16), nullable=False, server_default='business_current'),
            sa.Column('display_name', sa.String(length=80), nullable=False),
            sa.Column('masked_account_identifier', sa.String(length=32), nullable=False),
            sa.Column('balance_amount_minor', sa.BigInteger(), nullable=True),
            sa.Column('balance_currency', sa.String(length=3), nullable=True),
            sa.Column('balance_availability_state', sa.String(length=12), nullable=False, server_default='unknown'),
            sa.Column('pending_outgoing_payments_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('pending_outgoing_payments_amount_minor', sa.BigInteger(), nullable=True),
            sa.Column('as_of_timestamp', sa.DateTime(timezone=True), nullable=True),
            sa.Column('freshness_status', sa.String(length=14), nullable=False, server_default='unknown'),
            sa.Column('source_system_type', sa.String(length=16), nullable=False, server_default='business_banking'),
            sa.Column('projection_updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("account_type IN ('business_current', 'business_savings')", name='ck_bprm_account_type'),
            sa.CheckConstraint("balance_availability_state IN ('current','stale','unavailable','unknown')", name='ck_bprm_state'),
            sa.CheckConstraint("freshness_status IN ('within_target','breached','unknown')", name='ck_bprm_freshness'),
            sa.ForeignKeyConstraint(['customer_profile_ref_id'], ['customer_profile_refs.id'], ),
        )
        op.create_index('ix_bprm_customer', 'business_profile_read_models', ['customer_profile_ref_id'])
        op.create_index('uq_bprm_customer_account', 'business_profile_read_models', ['customer_profile_ref_id', 'business_account_system_reference'], unique=True)
    
    # 4. Add entitlement_type field to sandbox_entitlements
    se_columns = [col['name'] for col in inspector.get_columns('sandbox_entitlements')]
    if 'entitlement_type' not in se_columns:
        op.add_column('sandbox_entitlements', sa.Column('entitlement_type', sa.String(length=16), nullable=True, server_default='view'))
    
    # 5. Create scam_reports table
    if 'scam_reports' not in inspector.get_table_names():
        op.create_table(
            'scam_reports',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('report_reference', sa.String(length=32), nullable=False, unique=True),
            sa.Column('customer_profile_ref_id', sa.String(length=36), nullable=False),
            sa.Column('payment_reference', sa.String(length=32), nullable=False),
            sa.Column('report_type', sa.String(length=20), nullable=False),
            sa.Column('report_reason', sa.String(length=500), nullable=True),
            sa.Column('reported_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='submitted'),
            sa.Column('decision', sa.String(length=20), nullable=True),
            sa.Column('decided_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('decided_by', sa.String(length=120), nullable=True),
            sa.Column('customer_notified_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('timeline_message', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("report_type IN ('scam_app', 'unauthorised')", name='ck_sr_report_type'),
            sa.CheckConstraint("status IN ('submitted', 'under_review', 'decided', 'closed')", name='ck_sr_status'),
            sa.CheckConstraint("decision IS NULL OR decision IN ('approved', 'denied', 'partial')", name='ck_sr_decision'),
            sa.ForeignKeyConstraint(['customer_profile_ref_id'], ['customer_profile_refs.id'], ),
        )
        op.create_index('ix_sr_customer', 'scam_reports', ['customer_profile_ref_id'])
        op.create_index('ix_sr_payment_ref', 'scam_reports', ['payment_reference'])
        op.create_index('ix_sr_report_ref', 'scam_reports', ['report_reference'])
    
    # 6. Create incident_reports table for PS26/2 readiness
    if 'incident_reports' not in inspector.get_table_names():
        op.create_table(
            'incident_reports',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('incident_reference', sa.String(length=32), nullable=False, unique=True),
            sa.Column('incident_type', sa.String(length=50), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False),
            sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('description', sa.String(length=1000), nullable=False),
            sa.Column('affected_service', sa.String(length=100), nullable=True),
            sa.Column('fca_ps26_2_applicable', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('pra_ps7_26_applicable', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('material_impact_threshold_met', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('reporting_route', sa.String(length=20), nullable=True),
            sa.Column('reported_to_regulator_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='detected'),
            sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('root_cause', sa.String(length=1000), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("severity IN ('critical', 'major', 'minor')", name='ck_ir_severity'),
            sa.CheckConstraint("reporting_route IS NULL OR reporting_route IN ('standard', 'enhanced')", name='ck_ir_route'),
            sa.CheckConstraint("status IN ('detected', 'investigating', 'reported', 'resolved', 'closed')", name='ck_ir_status'),
        )
        op.create_index('ix_ir_incident_ref', 'incident_reports', ['incident_reference'])
        op.create_index('ix_ir_detected_at', 'incident_reports', ['detected_at'])
        op.create_index('ix_ir_applicable', 'incident_reports', ['fca_ps26_2_applicable', 'pra_ps7_26_applicable'])
    
    # 7. Create material_third_party_register table
    if 'material_third_party_register' not in inspector.get_table_names():
        op.create_table(
            'material_third_party_register',
            sa.Column('id', sa.String(length=36), primary_key=True),
            sa.Column('third_party_name', sa.String(length=160), nullable=False),
            sa.Column('service_category', sa.String(length=50), nullable=False),
            sa.Column('service_description', sa.String(length=500), nullable=False),
            sa.Column('criticality', sa.String(length=20), nullable=False),
            sa.Column('contract_start_date', sa.Date(), nullable=True),
            sa.Column('contract_review_date', sa.Date(), nullable=True),
            sa.Column('exit_plan_status', sa.String(length=20), nullable=False, server_default='required'),
            sa.Column('exit_plan_last_tested', sa.Date(), nullable=True),
            sa.Column('regulatory_reportable', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
            sa.CheckConstraint("criticality IN ('critical', 'important', 'standard')", name='ck_mtpr_criticality'),
            sa.CheckConstraint("exit_plan_status IN ('required', 'draft', 'approved', 'tested')", name='ck_mtpr_exit_plan'),
        )
        op.create_index('ix_mtpr_third_party_name', 'material_third_party_register', ['third_party_name'])
        op.create_index('ix_mtpr_criticality', 'material_third_party_register', ['criticality'])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('material_third_party_register')
    op.drop_table('incident_reports')
    op.drop_table('scam_reports')
    op.drop_table('business_profile_read_models')
    
    # Remove columns
    op.drop_column('sandbox_entitlements', 'entitlement_type')
    op.drop_column('customer_profile_refs', 'business_name')
    op.drop_column('account_read_models', 'loan_remaining_term_months')
    op.drop_column('account_read_models', 'loan_next_repayment_amount_minor')
    op.drop_column('account_read_models', 'loan_next_repayment_date')
    op.drop_column('account_read_models', 'loan_outstanding_balance_minor')
