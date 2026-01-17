"""add_api_keys_table

Revision ID: 0492c2f08470
Revises: 0846970e5b1f
Create Date: 2026-01-17 08:20:54.696597

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0492c2f08470'
down_revision: Union[str, None] = '0846970e5b1f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('key_prefix', sa.String(length=16), nullable=False),
        sa.Column('scopes', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_by', sa.String(length=10), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_key_prefix'), 'api_keys', ['key_prefix'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_api_keys_key_prefix'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')

    # Drop table
    op.drop_table('api_keys')
