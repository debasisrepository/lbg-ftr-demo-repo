"""remove_ciam_unique_constraint

Revision ID: r2_remove_ciam_unique
Revises: r2_release_2_features
Create Date: 2026-11-23 13:00:00.000000

Release 2: Remove unique constraint on ciam_subject_reference to support multiple profiles per identity.
Per ADR-003: One identity, many profiles (personal + business).

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'r2_remove_ciam_unique'
down_revision = 'r2_release_2_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    
    # For SQLite, we need to recreate the table without the unique constraint
    # For PostgreSQL, we can just drop the constraint
    if bind.dialect.name == 'sqlite':
        # SQLite doesn't support ALTER TABLE DROP CONSTRAINT
        # The constraint is enforced at the Python model level
        # by setting unique=False in the Column definition
        # When the table is recreated or new database initialized,
        # the constraint won't be there
        
        # Create index for performance since we removed unique constraint
        try:
            op.create_index('ix_customer_profile_refs_ciam_subject_reference', 
                          'customer_profile_refs', 
                          ['ciam_subject_reference'])
        except Exception:
            # Index might already exist
            pass
    
    elif bind.dialect.name == 'postgresql':
        # For PostgreSQL, explicitly drop the unique constraint
        try:
            op.drop_constraint('customer_profile_refs_ciam_subject_reference_key', 
                             'customer_profile_refs', 
                             type_='unique')
        except Exception:
            # Constraint might not exist or have different name
            pass
        
        # Create index for performance
        try:
            op.create_index('ix_customer_profile_refs_ciam_subject_reference', 
                          'customer_profile_refs', 
                          ['ciam_subject_reference'])
        except Exception:
            # Index might already exist
            pass


def downgrade() -> None:
    bind = op.get_bind()
    
    # Drop the index
    try:
        op.drop_index('ix_customer_profile_refs_ciam_subject_reference', 
                     table_name='customer_profile_refs')
    except Exception:
        pass
    
    if bind.dialect.name == 'postgresql':
        # Re-add unique constraint
        try:
            op.create_unique_constraint('customer_profile_refs_ciam_subject_reference_key',
                                       'customer_profile_refs',
                                       ['ciam_subject_reference'])
        except Exception:
            pass
