from datetime import datetime
from sqlalchemy import Column, String, Integer, Date, DateTime
from sqlalchemy.sql import func
from app.models.user import Base


class Employee(Base):
    __tablename__ = "employees"

    # Primary Key
    id = Column(String(10), primary_key=True, index=True)  # VNW0006204

    # Names
    name_tw = Column(String(100), nullable=True)  # Chinese name (陳玉俊)
    name_en = Column(String(100), nullable=True)  # Vietnamese name (PHAN ANH TUẤN)

    # Dates
    dob = Column(Date, nullable=True)  # Date of birth
    start_date = Column(Date, nullable=True)  # Date of joining

    # Job Info
    dept = Column(String(100), nullable=True)  # Department name (冶金技術部)
    department_code = Column(String(8), index=True, nullable=True)  # Code (7410)
    job_title = Column(String(100), nullable=True)  # Position (工程師)
    job_type = Column(String(100), nullable=True)  # Job type

    # Salary & Personal
    salary = Column(Integer, default=0, nullable=True)
    address1 = Column(String(200), nullable=True)  # Current address
    address2 = Column(String(200), nullable=True)  # Household registration
    phone1 = Column(String(20), nullable=True)
    phone2 = Column(String(20), nullable=True)

    # Family & Legal
    spouse_name = Column(String(100), nullable=True)
    nationality = Column(String(20), nullable=True)
    identity_number = Column(String(32), unique=True, index=True, nullable=True)  # CMND/CCCD
    sex = Column(String(8), nullable=True)  # Male/Female or 男/女

    # Dormitory (placeholder for future dorms feature)
    dorm_id = Column(String(20), nullable=True)

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Employee(id={self.id}, name_tw={self.name_tw}, name_en={self.name_en})>"
