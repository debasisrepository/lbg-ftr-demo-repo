"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables."""
    # User accounts
    op.create_table(
        'user_accounts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('username', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('display_name', sa.String(length=255), nullable=True),
        sa.Column('scope', sa.String(length=50), nullable=False),
        sa.Column('customer_party_id', sa.String(length=255), nullable=True),
        sa.Column('colleague_reference', sa.String(length=255), nullable=True),
        sa.Column('brand', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('failed_login_count', sa.Integer(), nullable=False),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("scope IN ('customer', 'colleague')", name='ck_user_scope'),
        sa.CheckConstraint("(scope = 'customer' AND customer_party_id IS NOT NULL) OR (scope = 'colleague' AND colleague_reference IS NOT NULL)", name='ck_user_scope_reference'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username')
    )
    op.create_index(op.f('ix_user_accounts_username'), 'user_accounts', ['username'], unique=True)

    # Auth sessions
    op.create_table(
        'auth_sessions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('token_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_activity_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoke_reason', sa.String(length=50), nullable=True),
        sa.Column('origin_channel', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash')
    )
    op.create_index(op.f('ix_auth_sessions_token_hash'), 'auth_sessions', ['token_hash'], unique=True)
    op.create_index(op.f('ix_auth_sessions_user_id'), 'auth_sessions', ['user_id'], unique=False)
    op.create_index('ix_auth_sessions_user_active', 'auth_sessions', ['user_id', 'revoked_at'], unique=False)

    # Issue eligibility rules
    op.create_table(
        'issue_eligibility_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('issue_type', sa.String(length=100), nullable=False),
        sa.Column('is_eligible', sa.Boolean(), nullable=False),
        sa.Column('redirect_journey_code', sa.String(length=100), nullable=True),
        sa.Column('priority_weight', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('issue_type')
    )
    op.create_index(op.f('ix_issue_eligibility_rules_issue_type'), 'issue_eligibility_rules', ['issue_type'], unique=True)

    # Case lifecycle transitions
    op.create_table(
        'case_lifecycle_transitions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('from_state', sa.String(length=50), nullable=False),
        sa.Column('to_state', sa.String(length=50), nullable=False),
        sa.Column('basis_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint('from_state <> to_state', name='ck_transition_different_states'),
        sa.PrimaryKeyConstraint('id')
    )

    # Owner team mappings
    op.create_table(
        'owner_team_mappings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('owner_team_code', sa.String(length=100), nullable=False),
        sa.Column('owner_semantic_label', sa.String(length=100), nullable=False),
        sa.Column('owner_display_name', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('superseded_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_team_code')
    )
    op.create_index(op.f('ix_owner_team_mappings_owner_team_code'), 'owner_team_mappings', ['owner_team_code'], unique=True)

    # Kill switch settings
    op.create_table(
        'kill_switch_settings',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('component_type', sa.String(length=20), nullable=False),
        sa.Column('component_name', sa.String(length=100), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False),
        sa.Column('execution_mode', sa.String(length=20), nullable=False),
        sa.Column('disabled_reason', sa.Text(), nullable=True),
        sa.Column('disabled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("component_type IN ('agent', 'tool')", name='ck_component_type'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_kill_switch_settings_component_name'), 'kill_switch_settings', ['component_name'], unique=False)

    # Cases
    op.create_table(
        'cases',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_reference', sa.String(length=32), nullable=False),
        sa.Column('customer_party_id', sa.String(length=255), nullable=False),
        sa.Column('brand', sa.String(length=50), nullable=False),
        sa.Column('issue_type', sa.String(length=100), nullable=False),
        sa.Column('classification_source', sa.String(length=50), nullable=False),
        sa.Column('issue_title', sa.String(length=500), nullable=True),
        sa.Column('issue_summary', sa.Text(), nullable=True),
        sa.Column('origin_channel', sa.String(length=50), nullable=False),
        sa.Column('current_lifecycle_state', sa.String(length=50), nullable=False),
        sa.Column('current_status_code', sa.String(length=100), nullable=False),
        sa.Column('current_status_label', sa.String(length=255), nullable=False),
        sa.Column('latest_meaningful_update_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome_summary', sa.Text(), nullable=True),
        sa.Column('retention_category', sa.String(length=50), nullable=False),
        sa.Column('continuity_state', sa.String(length=50), nullable=False),
        sa.Column('complaint_sensitive_flag', sa.Boolean(), nullable=False),
        sa.Column('fraud_sensitive_flag', sa.Boolean(), nullable=False),
        sa.Column('vulnerable_customer_flag', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("brand IN ('lloyds', 'bank_of_scotland')", name='ck_case_brand'),
        sa.CheckConstraint("retention_category IN ('standard', 'regulatory', 'litigation')", name='ck_retention_category'),
        sa.CheckConstraint("continuity_state IN ('current', 'refresh_pending', 'refreshing')", name='ck_continuity_state'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_reference')
    )
    op.create_index(op.f('ix_cases_case_reference'), 'cases', ['case_reference'], unique=True)
    op.create_index(op.f('ix_cases_customer_party_id'), 'cases', ['customer_party_id'], unique=False)
    op.create_index('ix_cases_customer_opened', 'cases', ['customer_party_id', 'opened_at'], unique=False)

    # Case anchor links
    op.create_table(
        'case_anchor_links',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('anchor_domain', sa.String(length=100), nullable=False),
        sa.Column('anchor_system', sa.String(length=100), nullable=False),
        sa.Column('anchor_record_type', sa.String(length=100), nullable=False),
        sa.Column('anchor_record_id', sa.String(length=255), nullable=False),
        sa.Column('anchor_reference', sa.String(length=255), nullable=False),
        sa.Column('link_status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_anchor_links_anchor_reference'), 'case_anchor_links', ['anchor_reference'], unique=False)
    op.create_index(op.f('ix_case_anchor_links_case_id'), 'case_anchor_links', ['case_id'], unique=False)

    # Case status projections
    op.create_table(
        'case_status_projections',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('status_code', sa.String(length=100), nullable=False),
        sa.Column('status_label', sa.String(length=255), nullable=False),
        sa.Column('lifecycle_state', sa.String(length=50), nullable=False),
        sa.Column('status_icon', sa.String(length=50), nullable=True),
        sa.Column('status_color', sa.String(length=50), nullable=True),
        sa.Column('customer_facing_text', sa.Text(), nullable=True),
        sa.Column('next_step_text', sa.Text(), nullable=True),
        sa.Column('source_event_id', sa.Uuid(), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_status_projections_case_id'), 'case_status_projections', ['case_id'], unique=False)
    with op.batch_alter_table('case_status_projections') as batch_op:
        batch_op.create_index(
            'ix_case_status_proj_case_current',
            ['case_id'],
            unique=True,
            postgresql_where=sa.text('is_current = true'),
            sqlite_where=sa.text('is_current = true')
        )
    op.create_index('ix_case_status_proj_case_effective', 'case_status_projections', ['case_id', 'effective_from'], unique=False)

    # Case ownerships
    op.create_table(
        'case_ownerships',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('owner_team_code', sa.String(length=100), nullable=False),
        sa.Column('owner_semantic_label', sa.String(length=100), nullable=False),
        sa.Column('owner_display_name', sa.String(length=255), nullable=False),
        sa.Column('source_event_id', sa.Uuid(), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_case_ownerships_case_id'), 'case_ownerships', ['case_id'], unique=False)
    with op.batch_alter_table('case_ownerships') as batch_op:
        batch_op.create_index(
            'ix_case_ownership_case_current',
            ['case_id'],
            unique=True,
            postgresql_where=sa.text('is_current = true'),
            sqlite_where=sa.text('is_current = true')
        )

    # Expected by commitments
    op.create_table(
        'expected_by_commitments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('commitment_state', sa.String(length=50), nullable=False),
        sa.Column('expected_by_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('customer_explanatory_text', sa.Text(), nullable=True),
        sa.Column('confidence_basis', sa.String(length=100), nullable=True),
        sa.Column('withdrawn_reason_code', sa.String(length=100), nullable=True),
        sa.Column('source_event_id', sa.Uuid(), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("commitment_state IN ('committed', 'revised', 'withdrawn', 'under_review')", name='ck_commitment_state'),
        sa.CheckConstraint("(commitment_state IN ('committed', 'revised') AND expected_by_at IS NOT NULL) OR (commitment_state NOT IN ('committed', 'revised'))", name='ck_expected_by_date_required'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expected_by_commitments_case_id'), 'expected_by_commitments', ['case_id'], unique=False)
    with op.batch_alter_table('expected_by_commitments') as batch_op:
        batch_op.create_index(
            'ix_expected_by_case_current',
            ['case_id'],
            unique=True,
            postgresql_where=sa.text('is_current = true'),
            sqlite_where=sa.text('is_current = true')
        )

    # Continuity contexts
    op.create_table(
        'continuity_contexts',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('package_version', sa.Integer(), nullable=False),
        sa.Column('structured_context_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('llm_safe_payload_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('colleague_payload_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('restricted_fields_excluded_flag', sa.Boolean(), nullable=False),
        sa.Column('last_channel', sa.String(length=50), nullable=True),
        sa.Column('last_presented_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_continuity_contexts_case_id'), 'continuity_contexts', ['case_id'], unique=False)
    with op.batch_alter_table('continuity_contexts') as batch_op:
        batch_op.create_index(
            'ix_continuity_case_current',
            ['case_id'],
            unique=True,
            postgresql_where=sa.text('is_current = true'),
            sqlite_where=sa.text('is_current = true')
        )

    # Channel handoffs
    op.create_table(
        'channel_handoffs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('from_channel', sa.String(length=50), nullable=False),
        sa.Column('to_channel', sa.String(length=50), nullable=False),
        sa.Column('context_presented_flag', sa.Boolean(), nullable=False),
        sa.Column('handoff_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("from_channel IN ('mobile_app', 'chat', 'phone', 'branch', 'colleague_desktop', 'ai_assistant')", name='ck_from_channel'),
        sa.CheckConstraint("to_channel IN ('mobile_app', 'chat', 'phone', 'branch', 'colleague_desktop', 'ai_assistant')", name='ck_to_channel'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_channel_handoffs_case_id'), 'channel_handoffs', ['case_id'], unique=False)
    op.create_index(op.f('ix_channel_handoffs_correlation_id'), 'channel_handoffs', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_channel_handoffs_handoff_timestamp'), 'channel_handoffs', ['handoff_timestamp'], unique=False)

    # Communication records
    op.create_table(
        'communication_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('communication_type', sa.String(length=50), nullable=False),
        sa.Column('subject_text', sa.String(length=500), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('approved_wording_set', sa.String(length=100), nullable=False),
        sa.Column('source_event_id', sa.Uuid(), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_communication_records_case_id'), 'communication_records', ['case_id'], unique=False)
    op.create_index(op.f('ix_communication_records_correlation_id'), 'communication_records', ['correlation_id'], unique=False)

    # Notification records
    op.create_table(
        'notification_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('communication_id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('customer_party_id', sa.String(length=255), nullable=False),
        sa.Column('notification_type', sa.String(length=50), nullable=False),
        sa.Column('safe_preview_text', sa.String(length=500), nullable=False),
        sa.Column('deep_link_token_hash', sa.String(length=255), nullable=False),
        sa.Column('deep_link_target', sa.String(length=50), nullable=False),
        sa.Column('deep_link_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notification_template_code', sa.String(length=100), nullable=False),
        sa.Column('delivery_state', sa.String(length=50), nullable=False),
        sa.Column('delivery_attempts', sa.Integer(), nullable=False),
        sa.Column('delivered_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('opened_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("deep_link_target IN ('case_list', 'case_view')", name='ck_deep_link_target'),
        sa.CheckConstraint("delivery_state IN ('pending', 'sent', 'delivered', 'failed')", name='ck_delivery_state'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('deep_link_token_hash')
    )
    op.create_index(op.f('ix_notification_records_case_id'), 'notification_records', ['case_id'], unique=False)
    op.create_index(op.f('ix_notification_records_communication_id'), 'notification_records', ['communication_id'], unique=False)
    op.create_index(op.f('ix_notification_records_correlation_id'), 'notification_records', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_notification_records_customer_party_id'), 'notification_records', ['customer_party_id'], unique=False)
    op.create_index(op.f('ix_notification_records_deep_link_token_hash'), 'notification_records', ['deep_link_token_hash'], unique=True)
    op.create_index('ix_notification_delivery_state', 'notification_records', ['delivery_state', 'delivered_at'], unique=False)

    # Protected action requests
    op.create_table(
        'protected_action_requests',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('customer_party_id', sa.String(length=255), nullable=False),
        sa.Column('action_type', sa.String(length=100), nullable=False),
        sa.Column('action_domain', sa.String(length=50), nullable=False),
        sa.Column('action_payload_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('request_status', sa.String(length=50), nullable=False),
        sa.Column('requires_sca_flag', sa.Boolean(), nullable=False),
        sa.Column('sca_outcome', sa.String(length=50), nullable=False),
        sa.Column('sca_invoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sca_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('management_api_reference', sa.String(length=255), nullable=True),
        sa.Column('fallback_guidance_text', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("action_domain IN ('card', 'money')", name='ck_action_domain'),
        sa.CheckConstraint("request_status IN ('pending_sca', 'released', 'not_executed')", name='ck_request_status'),
        sa.CheckConstraint("sca_outcome IN ('not_invoked', 'success', 'failed', 'abandoned')", name='ck_sca_outcome'),
        sa.CheckConstraint("(request_status = 'pending_sca') OR (sca_outcome <> 'not_invoked')", name='ck_sca_outcome_when_not_pending'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_protected_action_requests_case_id'), 'protected_action_requests', ['case_id'], unique=False)
    op.create_index(op.f('ix_protected_action_requests_correlation_id'), 'protected_action_requests', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_protected_action_requests_customer_party_id'), 'protected_action_requests', ['customer_party_id'], unique=False)

    # Service incidents
    op.create_table(
        'service_incidents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('incident_reference', sa.String(length=255), nullable=False),
        sa.Column('incident_state', sa.String(length=50), nullable=False),
        sa.Column('affected_service_code', sa.String(length=100), nullable=False),
        sa.Column('customer_impact_summary', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("incident_state IN ('declared', 'monitoring', 'resolved')", name='ck_incident_state'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('incident_reference')
    )
    op.create_index(op.f('ix_service_incidents_incident_reference'), 'service_incidents', ['incident_reference'], unique=True)
    op.create_index(op.f('ix_service_incidents_incident_state'), 'service_incidents', ['incident_state'], unique=False)
    op.create_index('ix_incident_state_resolved', 'service_incidents', ['incident_state', 'resolved_at'], unique=False)

    # Service status publications
    op.create_table(
        'service_status_publications',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('incident_id', sa.Uuid(), nullable=False),
        sa.Column('publication_state', sa.String(length=50), nullable=False),
        sa.Column('headline_text', sa.String(length=500), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('affected_journeys_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=False),
        sa.Column('content_version', sa.Integer(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("publication_state IN ('active', 'withdrawn')", name='ck_publication_state'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_status_publications_incident_id'), 'service_status_publications', ['incident_id'], unique=False)
    op.create_index('ix_status_pub_incident_active', 'service_status_publications', ['incident_id', 'publication_state'], unique=False)

    # Lifeline guidance
    op.create_table(
        'lifeline_guidance',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('incident_id', sa.Uuid(), nullable=False),
        sa.Column('guidance_title', sa.String(length=500), nullable=False),
        sa.Column('guidance_content', sa.Text(), nullable=False),
        sa.Column('guidance_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("guidance_type IN ('fallback', 'safe_action', 'phone')", name='ck_guidance_type'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lifeline_guidance_incident_id'), 'lifeline_guidance', ['incident_id'], unique=False)

    # Policy decisions
    op.create_table(
        'policy_decisions',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('decision_scope', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=True),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('outcome', sa.String(length=50), nullable=False),
        sa.Column('denial_reason_code', sa.String(length=100), nullable=True),
        sa.Column('decision_metadata_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("decision_scope IN ('eligibility', 'continuity', 'colleague_retrieval', 'protected_action')", name='ck_decision_scope'),
        sa.CheckConstraint("outcome IN ('permitted', 'denied')", name='ck_outcome'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_policy_decisions_case_id'), 'policy_decisions', ['case_id'], unique=False)
    op.create_index(op.f('ix_policy_decisions_correlation_id'), 'policy_decisions', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_policy_decisions_decision_scope'), 'policy_decisions', ['decision_scope'], unique=False)
    op.create_index('ix_policy_decision_scope_created', 'policy_decisions', ['decision_scope', 'created_at'], unique=False)

    # Agent execution records
    op.create_table(
        'agent_execution_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('agent_name', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=True),
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('execution_mode', sa.String(length=50), nullable=False),
        sa.Column('output_summary', sa.Text(), nullable=True),
        sa.Column('execution_duration_ms', sa.Integer(), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_execution_records_agent_name'), 'agent_execution_records', ['agent_name'], unique=False)
    op.create_index(op.f('ix_agent_execution_records_case_id'), 'agent_execution_records', ['case_id'], unique=False)
    op.create_index(op.f('ix_agent_execution_records_correlation_id'), 'agent_execution_records', ['correlation_id'], unique=False)

    # Tool invocation records
    op.create_table(
        'tool_invocation_records',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('tool_name', sa.String(length=100), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=True),
        sa.Column('request_summary', sa.Text(), nullable=True),
        sa.Column('external_response_reference', sa.String(length=255), nullable=True),
        sa.Column('tool_credential_scope', sa.String(length=50), nullable=False),
        sa.Column('execution_duration_ms', sa.Integer(), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tool_invocation_records_case_id'), 'tool_invocation_records', ['case_id'], unique=False)
    op.create_index(op.f('ix_tool_invocation_records_correlation_id'), 'tool_invocation_records', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_tool_invocation_records_tool_name'), 'tool_invocation_records', ['tool_name'], unique=False)

    # Audit entries
    op.create_table(
        'audit_entries',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('correlation_id', sa.String(length=255), nullable=False),
        sa.Column('audit_category', sa.String(length=50), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=True),
        sa.Column('actor_reference', sa.String(length=255), nullable=True),
        sa.Column('entity_type', sa.String(length=100), nullable=True),
        sa.Column('entity_id', sa.String(length=255), nullable=True),
        sa.Column('state_before_hash', sa.String(length=255), nullable=True),
        sa.Column('state_after_hash', sa.String(length=255), nullable=True),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('metadata_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("audit_category IN ('case_change', 'access', 'policy', 'action', 'communication', 'fallback_exposure', 'system')", name='ck_audit_category'),
        sa.CheckConstraint("severity IN ('debug', 'info', 'warning', 'error', 'critical')", name='ck_severity'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_entries_actor_reference'), 'audit_entries', ['actor_reference'], unique=False)
    op.create_index(op.f('ix_audit_entries_audit_category'), 'audit_entries', ['audit_category'], unique=False)
    op.create_index(op.f('ix_audit_entries_correlation_id'), 'audit_entries', ['correlation_id'], unique=False)
    op.create_index(op.f('ix_audit_entries_created_at'), 'audit_entries', ['created_at'], unique=False)
    op.create_index(op.f('ix_audit_entries_entity_id'), 'audit_entries', ['entity_id'], unique=False)
    op.create_index('ix_audit_category_created', 'audit_entries', ['audit_category', 'created_at'], unique=False)

    # Case events
    op.create_table(
        'case_events',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('case_id', sa.Uuid(), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('summary_text', sa.Text(), nullable=True),
        sa.Column('event_payload_json', sa.JSON().with_variant(sa.dialects.postgresql.JSONB(), 'postgresql'), nullable=True),
        sa.Column('customer_visible_flag', sa.Boolean(), nullable=False),
        sa.Column('actor_type', sa.String(length=50), nullable=True),
        sa.Column('actor_reference', sa.String(length=255), nullable=True),
        sa.Column('basis_type', sa.String(length=50), nullable=True),
        sa.Column('basis_reference', sa.String(length=255), nullable=True),
        sa.Column('correlation_id', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('case_id', 'sequence_number', name='uq_case_event_sequence')
    )
    op.create_index(op.f('ix_case_events_case_id'), 'case_events', ['case_id'], unique=False)
    op.create_index(op.f('ix_case_events_correlation_id'), 'case_events', ['correlation_id'], unique=False)
    op.create_index('ix_case_event_case_sequence', 'case_events', ['case_id', 'sequence_number'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_table('case_events')
    op.drop_table('audit_entries')
    op.drop_table('tool_invocation_records')
    op.drop_table('agent_execution_records')
    op.drop_table('policy_decisions')
    op.drop_table('lifeline_guidance')
    op.drop_table('service_status_publications')
    op.drop_table('service_incidents')
    op.drop_table('protected_action_requests')
    op.drop_table('notification_records')
    op.drop_table('communication_records')
    op.drop_table('channel_handoffs')
    op.drop_table('continuity_contexts')
    op.drop_table('expected_by_commitments')
    op.drop_table('case_ownerships')
    op.drop_table('case_status_projections')
    op.drop_table('case_anchor_links')
    op.drop_table('cases')
    op.drop_table('kill_switch_settings')
    op.drop_table('owner_team_mappings')
    op.drop_table('case_lifecycle_transitions')
    op.drop_table('issue_eligibility_rules')
    op.drop_table('auth_sessions')
    op.drop_table('user_accounts')
