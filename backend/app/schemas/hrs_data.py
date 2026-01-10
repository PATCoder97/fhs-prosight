"""
Pydantic schemas for HRS salary data API responses.

Field Mapping Documentation (HRS API → Schema):

Summary Fields:
- fields[32]: tong_tien_cong (total income from API)
- fields[43]: thuc_linh (net salary from API)
- tong_tien_tru: calculated as sum of all deduction fields

Income Fields (32 fields):
- fields[44]: luong_co_ban
- fields[2]: thuong_nang_suat
- fields[3]: thuong_tet
- fields[4]: tro_cap_com
- fields[5]: tro_cap_di_lai
- fields[6]: thuong_chuyen_can
- fields[7]: phu_cap_truc_ban
- fields[8]: phu_cap_ngon_ngu
- fields[9]: phu_cap_dac_biet
- fields[10]: phu_cap_chuyen_nganh
- fields[11]: phu_cap_tac_nghiep
- fields[12]: phu_cap_khu_vuc
- fields[13]: phu_cap_tc_dot_xuat
- fields[14]: phu_cap_ngay_nghi
- fields[15]: phu_cap_tc_khan_cap
- fields[16]: phu_cap_chuc_vu
- fields[17]: tro_cap_phong
- fields[18]: phat_bu
- fields[19]: thuong_cong_viec
- fields[20]: phi_khac
- fields[21]: cong
- fields[22]: tien_dong_phuc
- fields[23]: tro_cap_com2
- fields[24]: tro_cap_dt
- fields[25]: tro_cap_nghi
- fields[26]: phu_cap_tc_le
- fields[27]: phu_cap_ca
- fields[28]: phu_cap_tc2
- fields[29]: phu_cap_nghi2
- fields[30]: phu_cap_tc_kc
- fields[31]: phu_cap_tc_dem

Deduction Fields (10 fields):
- fields[33]: bhxh
- fields[34]: bh_that_nghiep
- fields[35]: bhyt
- fields[36]: ky_tuc_xa
- fields[37]: tien_com
- fields[38]: dong_phuc
- fields[39]: cong_doan
- fields[40]: khac
- fields[41]: nghi_phep
- fields[42]: thue_thu_nhap
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List


# ============================================================================
# Core Salary Data Schemas
# ============================================================================

class SalarySummary(BaseModel):
    """
    Tóm tắt lương (Salary Summary).

    3-field summary of salary calculation.
    """
    tong_tien_cong: float = Field(
        ...,
        description="Tổng tiền cộng / Total income (VND)"
    )
    tong_tien_tru: float = Field(
        ...,
        description="Tổng tiền trừ / Total deductions (VND)"
    )
    thuc_linh: float = Field(
        ...,
        description="Thực lĩnh / Net salary (VND)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "tong_tien_cong": 15000000.0,
                "tong_tien_tru": 3331510.0,
                "thuc_linh": 11668490.0
            }
        }


class SalaryIncome(BaseModel):
    """
    Thu nhập (Income).

    32 income fields from HRS salary response - CORRECTED MAPPING.
    All fields default to 0.0 if not provided.
    """
    luong_co_ban: float = Field(0.0, description="Lương cơ bản / Basic salary (VND)")
    thuong_nang_suat: float = Field(0.0, description="Thưởng năng suất / Performance bonus (VND)")
    thuong_tet: float = Field(0.0, description="Thưởng Tết / Tet bonus (VND)")
    tro_cap_com: float = Field(0.0, description="Trợ cấp cơm / Meal allowance (VND)")
    tro_cap_di_lai: float = Field(0.0, description="Trợ cấp đi lại / Transportation allowance (VND)")
    thuong_chuyen_can: float = Field(0.0, description="Thưởng chuyên cần / Attendance bonus (VND)")
    phu_cap_truc_ban: float = Field(0.0, description="Phụ cấp trực ban / Duty allowance (VND)")
    phu_cap_ngon_ngu: float = Field(0.0, description="Phụ cấp ngôn ngữ / Language allowance (VND)")
    phu_cap_dac_biet: float = Field(0.0, description="Phụ cấp đặc biệt / Special allowance (VND)")
    phu_cap_chuyen_nganh: float = Field(0.0, description="Phụ cấp chuyên ngành / Professional allowance (VND)")
    phu_cap_tac_nghiep: float = Field(0.0, description="Phụ cấp tác nghiệp / Operational allowance (VND)")
    phu_cap_khu_vuc: float = Field(0.0, description="Phụ cấp khu vực / Regional allowance (VND)")
    phu_cap_tc_dot_xuat: float = Field(0.0, description="Phụ cấp TC đột xuất / Ad-hoc allowance (VND)")
    phu_cap_ngay_nghi: float = Field(0.0, description="Phụ cấp ngày nghỉ / Holiday allowance (VND)")
    phu_cap_tc_khan_cap: float = Field(0.0, description="Phụ cấp TC khẩn cấp / Emergency allowance (VND)")
    phu_cap_chuc_vu: float = Field(0.0, description="Phụ cấp chức vụ / Position allowance (VND)")
    tro_cap_phong: float = Field(0.0, description="Trợ cấp phòng / Room allowance (VND)")
    phat_bu: float = Field(0.0, description="Phạt bù / Compensation fine (VND)")
    thuong_cong_viec: float = Field(0.0, description="Thưởng công việc / Work bonus (VND)")
    phi_khac: float = Field(0.0, description="Phí khác / Other fees (VND)")
    cong: float = Field(0.0, description="Công / Work hours (VND)")
    tien_dong_phuc: float = Field(0.0, description="Tiền đồng phục / Uniform allowance (VND)")
    tro_cap_com2: float = Field(0.0, description="Trợ cấp cơm 2 / Meal allowance 2 (VND)")
    tro_cap_dt: float = Field(0.0, description="Trợ cấp điện thoại / Phone allowance (VND)")
    tro_cap_nghi: float = Field(0.0, description="Trợ cấp nghỉ / Leave allowance (VND)")
    phu_cap_tc_le: float = Field(0.0, description="Phụ cấp TC lễ / Festival allowance (VND)")
    phu_cap_ca: float = Field(0.0, description="Phụ cấp ca / Shift allowance (VND)")
    phu_cap_tc2: float = Field(0.0, description="Phụ cấp TC 2 / Allowance 2 (VND)")
    phu_cap_nghi2: float = Field(0.0, description="Phụ cấp nghỉ 2 / Leave allowance 2 (VND)")
    phu_cap_tc_kc: float = Field(0.0, description="Phụ cấp TC KC / Distance allowance (VND)")
    phu_cap_tc_dem: float = Field(0.0, description="Phụ cấp TC đêm / Night allowance (VND)")

    class Config:
        json_schema_extra = {
            "example": {
                "luong_co_ban": 7205600.0,
                "thuong_nang_suat": 2000000.0,
                "thuong_tet": 1500000.0,
                "tro_cap_com": 660000.0
            }
        }


class SalaryDeductions(BaseModel):
    """
    Các khoản khấu trừ (Deductions).

    10 deduction fields from HRS salary response - CORRECTED MAPPING.
    All fields default to 0.0 if not provided.
    """
    bhxh: float = Field(0.0, description="BHXH / Social insurance (VND)")
    bh_that_nghiep: float = Field(0.0, description="BH thất nghiệp / Unemployment insurance (VND)")
    bhyt: float = Field(0.0, description="BHYT / Health insurance (VND)")
    ky_tuc_xa: float = Field(0.0, description="Ký túc xá / Dormitory fee (VND)")
    tien_com: float = Field(0.0, description="Tiền cơm / Meal deduction (VND)")
    dong_phuc: float = Field(0.0, description="Đồng phục / Uniform deduction (VND)")
    cong_doan: float = Field(0.0, description="Công đoàn / Union fee (VND)")
    khac: float = Field(0.0, description="Khác / Other deduction (VND)")
    nghi_phep: float = Field(0.0, description="Nghỉ phép / Leave deduction (VND)")
    thue_thu_nhap: float = Field(0.0, description="Thuế thu nhập / Income tax (VND)")

    class Config:
        json_schema_extra = {
            "example": {
                "bhxh": 1080840.0,
                "bh_that_nghiep": 72056.0,
                "bhyt": 144112.0,
                "thue_thu_nhap": 2034502.0
            }
        }


class SalaryPeriod(BaseModel):
    """
    Kỳ lương (Salary Period).

    Year and month specification for salary query.
    """
    year: int = Field(..., ge=2020, le=2100, description="Năm / Year")
    month: int = Field(..., description="Tháng / Month (1-12)")

    @field_validator('month')
    @classmethod
    def validate_month(cls, v):
        if not 1 <= v <= 12:
            raise ValueError('Month must be between 1 and 12')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "year": 2024,
                "month": 12
            }
        }


# ============================================================================
# Response Schemas
# ============================================================================

class SalaryResponse(BaseModel):
    """
    Phản hồi lương (Salary Response).

    Complete response for single month salary query.
    """
    employee_id: str = Field(..., description="Mã nhân viên / Employee ID (e.g., VNW0006204)")
    employee_name: Optional[str] = Field(None, description="Tên nhân viên / Employee name")
    period: SalaryPeriod
    summary: SalarySummary
    income: SalaryIncome
    deductions: SalaryDeductions

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "VNW0006204",
                "employee_name": "PHAN ANH TUẤN",
                "period": {"year": 2024, "month": 12},
                "summary": {
                    "tong_tien_cong": 15000000.0,
                    "tong_tien_tru": 3331510.0,
                    "thuc_linh": 11668490.0
                },
                "income": {
                    "luong_co_ban": 7205600.0,
                    "thuong_nang_suat": 2000000.0
                },
                "deductions": {
                    "bhxh": 1080840.0,
                    "bhyt": 144112.0
                }
            }
        }


class MonthlySalary(BaseModel):
    """
    Lương theo tháng (Monthly Salary).

    Salary data for a single month in history query.
    """
    month: int = Field(..., ge=1, le=12, description="Tháng / Month")
    summary: SalarySummary
    income: SalaryIncome
    deductions: SalaryDeductions

    class Config:
        json_schema_extra = {
            "example": {
                "month": 12,
                "summary": {
                    "tong_tien_cong": 15000000.0,
                    "tong_tien_tru": 3331510.0,
                    "thuc_linh": 11668490.0
                },
                "income": {"luong_co_ban": 7205600.0},
                "deductions": {"bhxh": 1080840.0}
            }
        }


# ============================================================================
# Trend Analysis Schemas
# ============================================================================

class SalaryChange(BaseModel):
    """
    Thay đổi lương (Salary Change).

    Significant salary change detected between two months.
    """
    from_month: int = Field(..., ge=1, le=12, description="Từ tháng / From month")
    to_month: int = Field(..., ge=1, le=12, description="Đến tháng / To month")
    field: str = Field(..., description="Trường thay đổi / Changed field (e.g., 'thuc_linh')")
    change: float = Field(..., description="Số tiền thay đổi / Change amount (VND)")
    percentage: float = Field(..., description="Phần trăm thay đổi / Percentage change (%)")
    direction: str = Field(..., description="Chiều hướng / Direction ('increase' or 'decrease')")

    class Config:
        json_schema_extra = {
            "example": {
                "from_month": 3,
                "to_month": 4,
                "field": "thuc_linh",
                "change": 2000000.0,
                "percentage": 16.67,
                "direction": "increase"
            }
        }


class SalaryTrend(BaseModel):
    """
    Xu hướng lương (Salary Trend).

    Trend analysis for multi-month salary history.
    """
    average_income: float = Field(..., description="Thu nhập trung bình / Average monthly income (VND)")
    average_deductions: float = Field(..., description="Khấu trừ trung bình / Average monthly deductions (VND)")
    average_net: float = Field(..., description="Thực lĩnh trung bình / Average monthly net salary (VND)")
    highest_month: Optional[MonthlySalary] = Field(None, description="Tháng lương cao nhất / Highest salary month")
    lowest_month: Optional[MonthlySalary] = Field(None, description="Tháng lương thấp nhất / Lowest salary month")
    significant_changes: List[SalaryChange] = Field(
        default_factory=list,
        description="Các thay đổi đáng kể / Significant changes (>10% or >500K VND)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "average_income": 15500000.0,
                "average_deductions": 3100000.0,
                "average_net": 12400000.0,
                "highest_month": {"month": 12, "summary": {"thuc_linh": 13000000.0}},
                "lowest_month": {"month": 1, "summary": {"thuc_linh": 11000000.0}},
                "significant_changes": [
                    {
                        "from_month": 3,
                        "to_month": 4,
                        "field": "thuc_linh",
                        "change": 2000000.0,
                        "percentage": 16.67,
                        "direction": "increase"
                    }
                ]
            }
        }


class SalaryHistoryResponse(BaseModel):
    """
    Phản hồi lịch sử lương (Salary History Response).

    Complete response for multi-month salary history with trend analysis.
    """
    employee_id: str = Field(..., description="Mã nhân viên / Employee ID")
    employee_name: Optional[str] = Field(None, description="Tên nhân viên / Employee name")
    period: dict = Field(..., description="Kỳ truy vấn / Query period (year, month range)")
    months: List[MonthlySalary] = Field(
        default_factory=list,
        description="Dữ liệu theo tháng / Monthly salary data"
    )
    trend: Optional[SalaryTrend] = Field(None, description="Phân tích xu hướng / Trend analysis")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "VNW0006204",
                "employee_name": "PHAN ANH TUẤN",
                "period": {"year": 2024, "month": "1-12"},
                "months": [
                    {
                        "month": 1,
                        "summary": {"tong_tien_cong": 15000000.0, "tong_tien_tru": 3000000.0, "thuc_linh": 12000000.0}
                    }
                ],
                "trend": {
                    "average_income": 15500000.0,
                    "average_deductions": 3100000.0,
                    "average_net": 12400000.0
                }
            }
        }


# Achievement/Evaluation Schemas

class Achievement(BaseModel):
    """Single achievement/evaluation record."""
    year: str = Field(..., description="Evaluation year (Năm đánh giá)")
    score: str = Field(..., description="Achievement score (Điểm đánh giá): 甲, 優, etc.")

    class Config:
        json_schema_extra = {
            "example": {
                "year": "2024",
                "score": "甲"
            }
        }


class AchievementResponse(BaseModel):
    """Response model for achievement queries."""
    employee_id: str = Field(..., description="Employee ID (Mã nhân viên)")
    employee_name: str = Field(..., description="Employee name (Tên nhân viên)")
    achievements: List[Achievement] = Field(..., description="List of achievements across years")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "VNW0006204",
                "employee_name": "PHAN ANH TUẤN",
                "achievements": [
                    {"year": "2024", "score": "甲"},
                    {"year": "2023", "score": "甲"},
                    {"year": "2022", "score": "優"}
                ]
            }
        }


# Year Bonus Schemas

class YearBonusData(BaseModel):
    """Year bonus data fields."""
    mnv: Optional[str] = Field(None, description="Mã nhân viên")
    tlcb: Optional[str] = Field(None, description="Tổng lương cơ bản")
    stdltbtn: Optional[str] = Field(None, description="Số tháng đóng BHTN")
    capbac: Optional[str] = Field(None, description="Cấp bậc")
    tile: Optional[str] = Field(None, description="Tỷ lệ")
    stienthuong: Optional[str] = Field(None, description="Số tiền thưởng")
    tpnttt: Optional[str] = Field(None, description="Thưởng phần NT trước Tết")
    tpntst: Optional[str] = Field(None, description="Thưởng phần NT sau Tết")

    class Config:
        json_schema_extra = {
            "example": {
                "mnv": "VNW0006204",
                "tlcb": "15000000",
                "stdltbtn": "12",
                "capbac": "Senior",
                "tile": "100",
                "stienthuong": "5000000",
                "tpnttt": "2500000",
                "tpntst": "2500000"
            }
        }


class YearBonusResponse(BaseModel):
    """Response model for year bonus queries."""
    employee_id: str = Field(..., description="Employee ID (Mã nhân viên)")
    employee_name: str = Field(..., description="Employee name (Tên nhân viên)")
    year: int = Field(..., description="Bonus year (Năm thưởng)")
    bonus_data: YearBonusData = Field(..., description="Year bonus details")

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "VNW0006204",
                "employee_name": "PHAN ANH TUẤN",
                "year": 2024,
                "bonus_data": {
                    "mnv": "VNW0006204",
                    "tlcb": "15000000",
                    "stdltbtn": "12",
                    "capbac": "Senior",
                    "tile": "100",
                    "stienthuong": "5000000",
                    "tpnttt": "2500000",
                    "tpntst": "2500000"
                }
            }
        }
