"""Add evaluations table

Revision ID: 12f90a9790c8
Revises: beb7f4fa17b3
Create Date: 2026-01-10 16:29:09.550741

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '12f90a9790c8'
down_revision: Union[str, None] = 'beb7f4fa17b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('term_code', sa.String(length=10), nullable=False),
        sa.Column('employee_id', sa.String(length=20), nullable=False),
        sa.Column('employee_name', sa.String(length=100), nullable=True),
        sa.Column('job_level', sa.String(length=50), nullable=True),
        sa.Column('nation', sa.String(length=10), nullable=True),
        sa.Column('dept_code', sa.String(length=20), nullable=True),
        sa.Column('dept_name', sa.String(length=200), nullable=True),
        sa.Column('grade_code', sa.String(length=20), nullable=True),
        sa.Column('grade_name', sa.String(length=100), nullable=True),
        sa.Column('init_score', sa.String(length=20), nullable=True),
        sa.Column('init_comment', sa.Text(), nullable=True),
        sa.Column('init_reviewer', sa.String(length=20), nullable=True),
        sa.Column('review_score', sa.String(length=20), nullable=True),
        sa.Column('review_comment', sa.Text(), nullable=True),
        sa.Column('review_reviewer', sa.String(length=20), nullable=True),
        sa.Column('final_score', sa.String(length=20), nullable=True),
        sa.Column('final_comment', sa.Text(), nullable=True),
        sa.Column('final_reviewer', sa.String(length=20), nullable=True),
        sa.Column('mgr_init_score', sa.String(length=20), nullable=True),
        sa.Column('mgr_init_comment', sa.Text(), nullable=True),
        sa.Column('mgr_init_reviewer', sa.String(length=20), nullable=True),
        sa.Column('mgr_review_score', sa.String(length=20), nullable=True),
        sa.Column('mgr_review_comment', sa.Text(), nullable=True),
        sa.Column('mgr_review_reviewer', sa.String(length=20), nullable=True),
        sa.Column('mgr_final_score', sa.String(length=20), nullable=True),
        sa.Column('mgr_final_comment', sa.Text(), nullable=True),
        sa.Column('mgr_final_reviewer', sa.String(length=20), nullable=True),
        sa.Column('leave_days', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create unique constraint
    op.create_unique_constraint('uq_evaluations_term_employee', 'evaluations', ['term_code', 'employee_id'])

    # Create indexes
    op.create_index('ix_evaluations_term_code', 'evaluations', ['term_code'], unique=False)
    op.create_index('ix_evaluations_employee_id', 'evaluations', ['employee_id'], unique=False)
    op.create_index('ix_evaluations_dept_code', 'evaluations', ['dept_code'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_evaluations_dept_code', table_name='evaluations')
    op.drop_index('ix_evaluations_employee_id', table_name='evaluations')
    op.drop_index('ix_evaluations_term_code', table_name='evaluations')

    # Drop unique constraint
    op.drop_constraint('uq_evaluations_term_employee', 'evaluations', type_='unique')

    # Drop table
    op.drop_table('evaluations')
