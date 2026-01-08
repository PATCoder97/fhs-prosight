"""add localId and fix role default

Revision ID: 7b4280a50047
Revises: 9a0ea82c4ee9
Create Date: 2026-01-08 09:45:00.000000

This migration:
1. Adds localId column (VARCHAR 50, nullable, indexed) to users table
2. Changes default role from "user" to "guest" for new users
3. Adds unique constraint on (provider, social_id) to prevent duplicate OAuth accounts
4. Implements proper downgrade for rollback

The migration is backward compatible - it doesn't modify existing user data,
only changes the schema for new users.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b4280a50047'
down_revision = '9a0ea82c4ee9'
branch_labels = None
depends_on = None


def upgrade():
    """Apply schema changes."""
    # Add localId column (nullable for existing users)
    op.add_column('users', sa.Column('localId', sa.String(length=50), nullable=True))
    
    # Create index on localId for faster lookups
    op.create_index('idx_users_localid', 'users', ['localId'], unique=False)
    
    # Change default role for NEW users only (existing users keep their current role)
    op.alter_column('users', 'role',
                    existing_type=sa.String(length=50),
                    server_default='guest',
                    existing_nullable=False)
    
    # Ensure unique constraint for OAuth accounts (provider + social_id combination)
    # This prevents duplicate OAuth accounts from the same provider
    op.create_unique_constraint('uq_provider_social_id', 'users', ['provider', 'social_id'])


def downgrade():
    """Reverse schema changes (in opposite order)."""
    # Drop unique constraint
    op.drop_constraint('uq_provider_social_id', 'users', type_='unique')
    
    # Restore original default role
    op.alter_column('users', 'role',
                    existing_type=sa.String(length=50),
                    server_default='user',
                    existing_nullable=False)
    
    # Drop index on localId
    op.drop_index('idx_users_localid', table_name='users')
    
    # Drop localId column
    op.drop_column('users', 'localId')
