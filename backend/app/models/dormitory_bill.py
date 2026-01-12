"""
Dormitory Bill Model

Stores employee dormitory billing information including electricity, water,
and management fees with composite unique key on (employee_id, term_code, dorm_code).
"""

from sqlalchemy import Column, BigInteger, String, Numeric, DateTime, ForeignKey, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.sql import func
from app.models.user import Base


class DormitoryBill(Base):
    """Employee dormitory billing record."""

    __tablename__ = "dormitory_bills"

    # Primary Key
    bill_id = Column(BigInteger, primary_key=True, autoincrement=True)

    # Foreign Keys & Required Fields
    employee_id = Column(String(20), ForeignKey("employees.id"), nullable=False, index=True)
    term_code = Column(String(10), nullable=False, index=True)
    dorm_code = Column(String(20), nullable=False, index=True)

    # Optional Fields
    factory_location = Column(String(100))

    # Electricity Billing
    elec_last_index = Column(Numeric(10, 2), default=0)
    elec_curr_index = Column(Numeric(10, 2), default=0)
    elec_usage = Column(Numeric(10, 2), default=0)
    elec_amount = Column(Numeric(15, 2), default=0)

    # Water Billing
    water_last_index = Column(Numeric(10, 2), default=0)
    water_curr_index = Column(Numeric(10, 2), default=0)
    water_usage = Column(Numeric(10, 2), default=0)
    water_amount = Column(Numeric(15, 2), default=0)

    # Fees
    shared_fee = Column(Numeric(15, 2), default=0)
    management_fee = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), default=0, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('employee_id', 'term_code', 'dorm_code', name='uq_bill_entry'),
        CheckConstraint('elec_curr_index >= elec_last_index', name='chk_elec_index'),
        CheckConstraint('water_curr_index >= water_last_index', name='chk_water_index'),
        CheckConstraint('total_amount >= 0 AND elec_amount >= 0 AND water_amount >= 0 AND shared_fee >= 0 AND management_fee >= 0', name='chk_amounts'),
        Index('idx_dormitory_bills_sort', 'term_code', 'created_at', postgresql_using='btree', postgresql_ops={'term_code': 'DESC', 'created_at': 'DESC'}),
    )
