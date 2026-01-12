from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Index, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class Evaluation(Base):
    __tablename__ = "evaluations"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Evaluation Period (Required)
    term_code = Column(String(10), nullable=False, index=True)  # 25, 251, 252, 25A, 25B, 25C
    employee_id = Column(String(20), nullable=False, index=True)  # VNW0006204

    # Employee Info (Optional - can sync from user table)
    employee_name = Column(String(100), nullable=True)  # 阮氏幸
    job_level = Column(String(50), nullable=True)  # 基層人員
    nation = Column(String(10), nullable=True)  # TW, VN
    dept_code = Column(String(20), nullable=True, index=True)  # 7800
    dept_name = Column(String(200), nullable=True)  # 冶金技術部物理試驗處處務室
    grade_code = Column(String(20), nullable=True)  # MZD01P
    grade_name = Column(String(100), nullable=True)  # 助理管理師

    # Department Evaluation (部門 - 初核/複核/核定)
    init_score = Column(String(20), nullable=True)  # 甲, 優, etc.
    init_comment = Column(Text, nullable=True)  # 初核評語
    init_reviewer = Column(String(20), nullable=True)  # 初核主管 - employee_id

    review_score = Column(String(20), nullable=True)  # 複核成績
    review_comment = Column(Text, nullable=True)  # 複核評語
    review_reviewer = Column(String(20), nullable=True)  # 複核主管

    final_score = Column(String(20), nullable=True)  # 核定成績
    final_comment = Column(Text, nullable=True)  # 核定評語
    final_reviewer = Column(String(20), nullable=True)  # 核定主管

    # Management Office Evaluation (經理室 - 初核/複核/核定)
    mgr_init_score = Column(String(20), nullable=True)  # 經理室初核成績
    mgr_init_comment = Column(Text, nullable=True)  # 經理室初核評語
    mgr_init_reviewer = Column(String(20), nullable=True)  # 經理室初核主管

    mgr_review_score = Column(String(20), nullable=True)  # 經理室複核成績
    mgr_review_comment = Column(Text, nullable=True)  # 經理室複核評語
    mgr_review_reviewer = Column(String(20), nullable=True)  # 經理室複核主管

    mgr_final_score = Column(String(20), nullable=True)  # 經理室核定成績
    mgr_final_comment = Column(Text, nullable=True)  # 經理室核定評語
    mgr_final_reviewer = Column(String(20), nullable=True)  # 經理室核定主管

    # Additional Info
    leave_days = Column(Float, nullable=True)  # 請假總日數

    # Audit timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Constraints
    __table_args__ = (
        UniqueConstraint('term_code', 'employee_id', name='uq_evaluations_term_employee'),
        Index('ix_evaluations_term_code', 'term_code'),
        Index('ix_evaluations_employee_id', 'employee_id'),
        Index('ix_evaluations_dept_code', 'dept_code'),
    )

    def __repr__(self):
        return f"<Evaluation(id={self.id}, term_code={self.term_code}, employee_id={self.employee_id})>"
