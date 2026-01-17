"""change_dormitory_bill_unique_constraint

Revision ID: cff0ef795a50
Revises: 0492c2f08470
Create Date: 2026-01-17 15:18:34.497195

Changes:
- Drop old unique constraint on (employee_id, term_code, dorm_code)
- Create new unique constraint on (employee_id, term_code)
- This allows only 1 bill per employee per term, regardless of dorm

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cff0ef795a50'
down_revision = '0492c2f08470'
branch_labels = None
depends_on = None


def upgrade():
    # Drop old unique constraint
    op.drop_constraint('uq_bill_entry', 'dormitory_bills', type_='unique')

    # Create new unique constraint on (employee_id, term_code) only
    op.create_unique_constraint(
        'uq_bill_entry',
        'dormitory_bills',
        ['employee_id', 'term_code']
    )


def downgrade():
    # Reverse: drop new constraint
    op.drop_constraint('uq_bill_entry', 'dormitory_bills', type_='unique')

    # Recreate old constraint on (employee_id, term_code, dorm_code)
    op.create_unique_constraint(
        'uq_bill_entry',
        'dormitory_bills',
        ['employee_id', 'term_code', 'dorm_code']
    )
