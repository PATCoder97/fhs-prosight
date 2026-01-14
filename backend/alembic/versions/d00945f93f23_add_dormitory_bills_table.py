"""Add dormitory_bills table

Revision ID: d00945f93f23
Revises: 12f90a9790c8
Create Date: 2026-01-12 10:39:51.954658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd00945f93f23'
down_revision: Union[str, None] = '12f90a9790c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tạo bảng dormitory_bills
    op.create_table('dormitory_bills',
        sa.Column('bill_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.String(length=20), nullable=False),
        sa.Column('term_code', sa.String(length=10), nullable=False),
        sa.Column('dorm_code', sa.String(length=20), nullable=False),
        sa.Column('factory_location', sa.String(length=100), nullable=True),
        sa.Column('elec_last_index', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('elec_curr_index', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('elec_usage', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('elec_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('water_last_index', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('water_curr_index', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('water_usage', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('water_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('shared_fee', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('management_fee', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('elec_curr_index >= elec_last_index', name='chk_elec_index'),
        sa.CheckConstraint('total_amount >= 0 AND elec_amount >= 0 AND water_amount >= 0 AND shared_fee >= 0 AND management_fee >= 0', name='chk_amounts'),
        sa.CheckConstraint('water_curr_index >= water_last_index', name='chk_water_index'),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('bill_id'),
        sa.UniqueConstraint('employee_id', 'term_code', 'dorm_code', name='uq_bill_entry')
    )

    # 2. Tạo các index cho bảng mới
    op.create_index('idx_dormitory_bills_sort', 'dormitory_bills', ['term_code', 'created_at'], unique=False, postgresql_using='btree', postgresql_ops={'term_code': 'DESC', 'created_at': 'DESC'})
    op.create_index(op.f('ix_dormitory_bills_dorm_code'), 'dormitory_bills', ['dorm_code'], unique=False)
    op.create_index(op.f('ix_dormitory_bills_employee_id'), 'dormitory_bills', ['employee_id'], unique=False)
    op.create_index(op.f('ix_dormitory_bills_term_code'), 'dormitory_bills', ['term_code'], unique=False)
    op.create_index(op.f('ix_dormitory_bills_total_amount'), 'dormitory_bills', ['total_amount'], unique=False)

    # 3. Sử dụng khối try-except để tránh lỗi khi bảng hoặc index đã tồn tại/không tồn tại
    try:
        # Thử tạo index cho các bảng đã có, nếu lỗi (do đã có rồi) thì bỏ qua
        op.create_index(op.f('ix_employees_department_code'), 'employees', ['department_code'], unique=False)
        op.create_index(op.f('ix_employees_id'), 'employees', ['id'], unique=False)
        op.create_index(op.f('ix_employees_identity_number'), 'employees', ['identity_number'], unique=True)
        op.create_index(op.f('ix_users_localId'), 'users', ['localId'], unique=False)
    except Exception:
        pass

def downgrade() -> None:
    # Lệnh xóa ngược lại khi cần rollback
    op.drop_index(op.f('ix_users_localId'), table_name='users')
    op.drop_index(op.f('ix_employees_identity_number'), table_name='employees')
    op.drop_index(op.f('ix_employees_id'), table_name='employees')
    op.drop_index(op.f('ix_employees_department_code'), table_name='employees')
    
    op.drop_index(op.f('ix_dormitory_bills_total_amount'), table_name='dormitory_bills')
    op.drop_index(op.f('ix_dormitory_bills_term_code'), table_name='dormitory_bills')
    op.drop_index(op.f('ix_dormitory_bills_employee_id'), table_name='dormitory_bills')
    op.drop_index(op.f('ix_dormitory_bills_dorm_code'), table_name='dormitory_bills')
    op.drop_index('idx_dormitory_bills_sort', table_name='dormitory_bills')
    op.drop_table('dormitory_bills')
