"""add employees table

Revision ID: beb7f4fa17b3
Revises: 7b4280a50047
Create Date: 2026-01-09 09:50:31.116781

This migration:
1. Creates employees table with 20+ fields for employee data
2. Adds indexes on: department_code, identity_number
3. Adds unique constraint on identity_number (CMND/CCCD)
4. Supports Chinese (name_tw) and Vietnamese (name_en) names with UTF-8
5. Implements reversible downgrade
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'beb7f4fa17b3'
down_revision: Union[str, None] = '7b4280a50047'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create employees table with indexes and constraints."""
    op.create_table(
        'employees',
        # Primary Key
        sa.Column('id', sa.String(length=10), primary_key=True, nullable=False),

        # Names
        sa.Column('name_tw', sa.String(length=100), nullable=True),  # Chinese
        sa.Column('name_en', sa.String(length=100), nullable=True),  # Vietnamese

        # Dates
        sa.Column('dob', sa.Date(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),

        # Job Info
        sa.Column('dept', sa.String(length=100), nullable=True),
        sa.Column('department_code', sa.String(length=8), nullable=True),
        sa.Column('job_title', sa.String(length=100), nullable=True),
        sa.Column('job_type', sa.String(length=100), nullable=True),

        # Salary & Personal
        sa.Column('salary', sa.Integer(), nullable=True, default=0),
        sa.Column('address1', sa.String(length=200), nullable=True),
        sa.Column('address2', sa.String(length=200), nullable=True),
        sa.Column('phone1', sa.String(length=20), nullable=True),
        sa.Column('phone2', sa.String(length=20), nullable=True),

        # Family & Legal
        sa.Column('spouse_name', sa.String(length=100), nullable=True),
        sa.Column('nationality', sa.String(length=20), nullable=True),
        sa.Column('identity_number', sa.String(length=32), nullable=True),
        sa.Column('sex', sa.String(length=8), nullable=True),

        # Dormitory (placeholder)
        sa.Column('dorm_id', sa.String(length=20), nullable=True),

        # Audit timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )

    # Create indexes
    op.create_index('idx_employees_id', 'employees', ['id'])
    op.create_index('idx_employees_department_code', 'employees', ['department_code'])
    op.create_index('idx_employees_identity_number', 'employees', ['identity_number'])

    # Create unique constraint on identity_number
    op.create_unique_constraint('uq_employees_identity_number', 'employees', ['identity_number'])


def downgrade() -> None:
    """Drop employees table and its constraints."""
    # Drop indexes (will be dropped with table, but explicit for clarity)
    op.drop_index('idx_employees_identity_number', table_name='employees')
    op.drop_index('idx_employees_department_code', table_name='employees')
    op.drop_index('idx_employees_id', table_name='employees')

    # Drop unique constraint
    op.drop_constraint('uq_employees_identity_number', 'employees', type_='unique')

    # Drop table
    op.drop_table('employees')
