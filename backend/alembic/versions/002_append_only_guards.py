"""Append-only guard triggers

Revision ID: 002
Revises: 001
Create Date: 2024-01-01 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create append-only guard triggers."""
    # Determine database dialect
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # PostgreSQL triggers
        op.execute("""
            CREATE OR REPLACE FUNCTION prevent_audit_mutation() RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'audit_entries table is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER audit_entries_guard
            BEFORE UPDATE OR DELETE ON audit_entries
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation();
        """)

        op.execute("""
            CREATE OR REPLACE FUNCTION prevent_case_event_mutation() RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'case_events table is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER case_events_guard
            BEFORE UPDATE OR DELETE ON case_events
            FOR EACH ROW EXECUTE FUNCTION prevent_case_event_mutation();
        """)

        op.execute("""
            CREATE OR REPLACE FUNCTION prevent_channel_handoff_mutation() RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'channel_handoffs table is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER channel_handoffs_guard
            BEFORE UPDATE OR DELETE ON channel_handoffs
            FOR EACH ROW EXECUTE FUNCTION prevent_channel_handoff_mutation();
        """)

        op.execute("""
            CREATE OR REPLACE FUNCTION prevent_policy_decision_mutation() RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'policy_decisions table is append-only';
            END;
            $$ LANGUAGE plpgsql;
        """)
        op.execute("""
            CREATE TRIGGER policy_decisions_guard
            BEFORE UPDATE OR DELETE ON policy_decisions
            FOR EACH ROW EXECUTE FUNCTION prevent_policy_decision_mutation();
        """)

    elif dialect == "sqlite":
        # SQLite triggers
        op.execute("""
            CREATE TRIGGER audit_entries_update_guard
            BEFORE UPDATE ON audit_entries
            BEGIN
                SELECT RAISE(ABORT, 'audit_entries table is append-only');
            END;
        """)
        op.execute("""
            CREATE TRIGGER audit_entries_delete_guard
            BEFORE DELETE ON audit_entries
            BEGIN
                SELECT RAISE(ABORT, 'audit_entries table is append-only');
            END;
        """)

        op.execute("""
            CREATE TRIGGER case_events_update_guard
            BEFORE UPDATE ON case_events
            BEGIN
                SELECT RAISE(ABORT, 'case_events table is append-only');
            END;
        """)
        op.execute("""
            CREATE TRIGGER case_events_delete_guard
            BEFORE DELETE ON case_events
            BEGIN
                SELECT RAISE(ABORT, 'case_events table is append-only');
            END;
        """)

        op.execute("""
            CREATE TRIGGER channel_handoffs_update_guard
            BEFORE UPDATE ON channel_handoffs
            BEGIN
                SELECT RAISE(ABORT, 'channel_handoffs table is append-only');
            END;
        """)
        op.execute("""
            CREATE TRIGGER channel_handoffs_delete_guard
            BEFORE DELETE ON channel_handoffs
            BEGIN
                SELECT RAISE(ABORT, 'channel_handoffs table is append-only');
            END;
        """)

        op.execute("""
            CREATE TRIGGER policy_decisions_update_guard
            BEFORE UPDATE ON policy_decisions
            BEGIN
                SELECT RAISE(ABORT, 'policy_decisions table is append-only');
            END;
        """)
        op.execute("""
            CREATE TRIGGER policy_decisions_delete_guard
            BEFORE DELETE ON policy_decisions
            BEGIN
                SELECT RAISE(ABORT, 'policy_decisions table is append-only');
            END;
        """)


def downgrade() -> None:
    """Drop append-only guard triggers."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute("DROP TRIGGER IF EXISTS audit_entries_guard ON audit_entries;")
        op.execute("DROP FUNCTION IF EXISTS prevent_audit_mutation();")
        op.execute("DROP TRIGGER IF EXISTS case_events_guard ON case_events;")
        op.execute("DROP FUNCTION IF EXISTS prevent_case_event_mutation();")
        op.execute("DROP TRIGGER IF EXISTS channel_handoffs_guard ON channel_handoffs;")
        op.execute("DROP FUNCTION IF EXISTS prevent_channel_handoff_mutation();")
        op.execute("DROP TRIGGER IF EXISTS policy_decisions_guard ON policy_decisions;")
        op.execute("DROP FUNCTION IF EXISTS prevent_policy_decision_mutation();")
    elif dialect == "sqlite":
        op.execute("DROP TRIGGER IF EXISTS audit_entries_update_guard;")
        op.execute("DROP TRIGGER IF EXISTS audit_entries_delete_guard;")
        op.execute("DROP TRIGGER IF EXISTS case_events_update_guard;")
        op.execute("DROP TRIGGER IF EXISTS case_events_delete_guard;")
        op.execute("DROP TRIGGER IF EXISTS channel_handoffs_update_guard;")
        op.execute("DROP TRIGGER IF EXISTS channel_handoffs_delete_guard;")
        op.execute("DROP TRIGGER IF EXISTS policy_decisions_update_guard;")
        op.execute("DROP TRIGGER IF EXISTS policy_decisions_delete_guard;")
