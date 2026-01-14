from alembic import op
import sqlalchemy as sa

revision = 'd00945f93f23'
down_revision = '12f90a9790c8'

def upgrade():
    # 1. Lệnh SQL này sẽ xóa bảng/index NẾU NÓ TỒN TẠI, nếu không có sẽ tự bỏ qua không báo lỗi
    op.execute("DROP TABLE IF EXISTS metrics_history CASCADE")
    op.execute("DROP INDEX IF EXISTS idx_metrics_db_name")
    op.execute("DROP INDEX IF EXISTS idx_metrics_db_type")
    op.execute("DROP INDEX IF EXISTS idx_metrics_timestamp")

    # 2. Tạo bảng dormitory_bills
    op.create_table('dormitory_bills',
        sa.Column('bill_id', sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column('employee_id', sa.String(length=20), nullable=False),
        sa.Column('term_code', sa.String(length=10), nullable=False),
        sa.Column('dorm_code', sa.String(length=20), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('bill_id'),
        sa.UniqueConstraint('employee_id', 'term_code', 'dorm_code', name='uq_bill_entry')
    )

def downgrade():
    op.drop_table('dormitory_bills')
