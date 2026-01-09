"""
Pydantic schemas for HRS salary data responses.

This module defines 9 schemas to structure salary information from FHS HRS API:
- SalarySummary: 3-field summary (total income, deductions, net)
- SalaryIncome: 32 income fields
- SalaryDeductions: 10 deduction fields
- SalaryPeriod: year and month
- SalaryResponse: Main response for single month query
- MonthlySalary: Salary data for one month in history
- SalaryChange: Month-over-month change details
- SalaryTrend: Trend analysis across multiple months
- SalaryHistoryResponse: Multi-month history with trend

Field Mapping Reference (HRS API fields[index]):
=====================================================
Summary Fields:
- fields[32]: tong_tien_cong (total income)
- fields[43]: thuc_linh (net salary)
- calculated: tong_tien_tru (sum of all deductions)

Income Fields (32 fields):
- fields[44]: luong_co_ban
- fields[2]: thuong_nang_suat
- fields[3]: phu_cap_chuc_vu
- fields[4]: phu_cap_trach_nhiem
- fields[5]: phu_cap_sinh_hoat
- fields[6]: phu_cap_di_lai
- fields[7]: phu_cap_nha_o
- fields[8]: phu_cap_dien_thoai
- fields[9]: phu_cap_an_trua
- fields[10]: phu_cap_xang_xe
- fields[11]: phu_cap_doc_hai
- fields[12]: phu_cap_lam_dem
- fields[13]: phu_cap_tieng_anh
- fields[14]: phu_cap_khac
- fields[15]: luong_lam_them_150
- fields[16]: luong_lam_them_200
- fields[17]: luong_lam_them_300
- fields[18]: luong_ngay_le
- fields[19]: luong_ngay_thuong
- fields[20]: thuong_hieu_qua
- fields[21]: thuong_khac
- fields[22]: tro_cap_khac
- fields[23]: bu_luong_thang_truoc
- fields[24]: luong_nghi_phep
- fields[25]: luong_nghi_om
- fields[26]: luong_con_nho
- fields[27]: thu_nhap_khac_1
- fields[28]: thu_nhap_khac_2
- fields[29]: thu_nhap_khac_3
- fields[30]: thu_nhap_khac_4
- fields[31]: thu_nhap_khac_5

Deduction Fields (10 fields):
- fields[33]: bhxh (social insurance)
- fields[34]: bhtn (unemployment insurance)
- fields[35]: bhyt (health insurance)
- fields[36]: thue_tncn (personal income tax)
- fields[37]: tam_ung (advance payment)
- fields[38]: phi_cong_doan (union fee)
- fields[39]: phat (penalty)
- fields[40]: khau_tru_khac_1 (other deduction 1)
- fields[41]: khau_tru_khac_2 (other deduction 2)
- fields[42]: khau_tru_khac_3 (other deduction 3)
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

    32 income fields from HRS salary response.
    All fields default to 0.0 if not provided.
    """
    luong_co_ban: float = Field(
        0.0,
        description="Lương cơ bản / Basic salary (VND)"
    )
    thuong_nang_suat: float = Field(
        0.0,
        description="Thưởng năng suất / Performance bonus (VND)"
    )
    phu_cap_chuc_vu: float = Field(
        0.0,
        description="Phụ cấp chức vụ / Position allowance (VND)"
    )
    phu_cap_trach_nhiem: float = Field(
        0.0,
        description="Phụ cấp trách nhiệm / Responsibility allowance (VND)"
    )
    phu_cap_sinh_hoat: float = Field(
        0.0,
        description="Phụ cấp sinh hoạt / Living allowance (VND)"
    )
    phu_cap_di_lai: float = Field(
        0.0,
        description="Phụ cấp đi lại / Transportation allowance (VND)"
    )
    phu_cap_nha_o: float = Field(
        0.0,
        description="Phụ cấp nhà ở / Housing allowance (VND)"
    )
    phu_cap_dien_thoai: float = Field(
        0.0,
        description="Phụ cấp điện thoại / Phone allowance (VND)"
    )
    phu_cap_an_trua: float = Field(
        0.0,
        description="Phụ cấp ăn trưa / Lunch allowance (VND)"
    )
    phu_cap_xang_xe: float = Field(
        0.0,
        description="Phụ cấp xăng xe / Fuel allowance (VND)"
    )
    phu_cap_doc_hai: float = Field(
        0.0,
        description="Phụ cấp độc hại / Hazard allowance (VND)"
    )
    phu_cap_lam_dem: float = Field(
        0.0,
        description="Phụ cấp làm đêm / Night shift allowance (VND)"
    )
    phu_cap_tieng_anh: float = Field(
        0.0,
        description="Phụ cấp tiếng Anh / English proficiency allowance (VND)"
    )
    phu_cap_khac: float = Field(
        0.0,
        description="Phụ cấp khác / Other allowances (VND)"
    )
    luong_lam_them_150: float = Field(
        0.0,
        description="Lương làm thêm 150% / Overtime 150% (VND)"
    )
    luong_lam_them_200: float = Field(
        0.0,
        description="Lương làm thêm 200% / Overtime 200% (VND)"
    )
    luong_lam_them_300: float = Field(
        0.0,
        description="Lương làm thêm 300% / Overtime 300% (VND)"
    )
    luong_ngay_le: float = Field(
        0.0,
        description="Lương ngày lễ / Holiday pay (VND)"
    )
    luong_ngay_thuong: float = Field(
        0.0,
        description="Lương ngày thường / Regular day pay (VND)"
    )
    thuong_hieu_qua: float = Field(
        0.0,
        description="Thưởng hiệu quả / Efficiency bonus (VND)"
    )
    thuong_khac: float = Field(
        0.0,
        description="Thưởng khác / Other bonuses (VND)"
    )
    tro_cap_khac: float = Field(
        0.0,
        description="Trợ cấp khác / Other subsidies (VND)"
    )
    bu_luong_thang_truoc: float = Field(
        0.0,
        description="Bù lương tháng trước / Previous month compensation (VND)"
    )
    luong_nghi_phep: float = Field(
        0.0,
        description="Lương nghỉ phép / Paid leave (VND)"
    )
    luong_nghi_om: float = Field(
        0.0,
        description="Lương nghỉ ốm / Sick leave pay (VND)"
    )
    luong_con_nho: float = Field(
        0.0,
        description="Lương con nhỏ / Child care allowance (VND)"
    )
    thu_nhap_khac_1: float = Field(
        0.0,
        description="Thu nhập khác 1 / Other income 1 (VND)"
    )
    thu_nhap_khac_2: float = Field(
        0.0,
        description="Thu nhập khác 2 / Other income 2 (VND)"
    )
    thu_nhap_khac_3: float = Field(
        0.0,
        description="Thu nhập khác 3 / Other income 3 (VND)"
    )
    thu_nhap_khac_4: float = Field(
        0.0,
        description="Thu nhập khác 4 / Other income 4 (VND)"
    )
    thu_nhap_khac_5: float = Field(
        0.0,
        description="Thu nhập khác 5 / Other income 5 (VND)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "luong_co_ban": 7205600.0,
                "thuong_nang_suat": 2000000.0,
                "phu_cap_chuc_vu": 1500000.0,
                "phu_cap_an_trua": 660000.0,
                "luong_lam_them_150": 850000.0,
                "phu_cap_di_lai": 500000.0,
                "phu_cap_dien_thoai": 200000.0,
                "thuong_hieu_qua": 1084400.0,
                "luong_nghi_phep": 1000000.0
            }
        }


class SalaryDeductions(BaseModel):
    """
    Các khoản trừ (Deductions).

    10 deduction fields from HRS salary response.
    All fields default to 0.0 if not provided.
    """
    bhxh: float = Field(
        0.0,
        description="Bảo hiểm xã hội / Social insurance (VND)"
    )
    bhtn: float = Field(
        0.0,
        description="Bảo hiểm thất nghiệp / Unemployment insurance (VND)"
    )
    bhyt: float = Field(
        0.0,
        description="Bảo hiểm y tế / Health insurance (VND)"
    )
    thue_tncn: float = Field(
        0.0,
        description="Thuế thu nhập cá nhân / Personal income tax (VND)"
    )
    tam_ung: float = Field(
        0.0,
        description="Tạm ứng / Advance payment (VND)"
    )
    phi_cong_doan: float = Field(
        0.0,
        description="Phí công đoàn / Union fee (VND)"
    )
    phat: float = Field(
        0.0,
        description="Phạt / Penalty (VND)"
    )
    khau_tru_khac_1: float = Field(
        0.0,
        description="Khấu trừ khác 1 / Other deduction 1 (VND)"
    )
    khau_tru_khac_2: float = Field(
        0.0,
        description="Khấu trừ khác 2 / Other deduction 2 (VND)"
    )
    khau_tru_khac_3: float = Field(
        0.0,
        description="Khấu trừ khác 3 / Other deduction 3 (VND)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "bhxh": 1080840.0,
                "bhtn": 144112.0,
                "bhyt": 180140.0,
                "thue_tncn": 1850000.0,
                "phi_cong_doan": 76418.0
            }
        }


class SalaryPeriod(BaseModel):
    """
    Kỳ lương (Salary Period).

    Represents a specific month in a year.
    """
    year: int = Field(..., ge=2020, le=2100, description="Năm / Year")
    month: int = Field(..., ge=1, le=12, description="Tháng / Month (1-12)")

    @field_validator('month')
    @classmethod
    def validate_month_range(cls, v: int) -> int:
        """Validate month is between 1 and 12"""
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

    Main response schema for single month salary query.
    Includes employee info, period, and structured salary data.
    """
    employee_id: str = Field(
        ...,
        description="Mã nhân viên / Employee ID (e.g., VNW0006204)"
    )
    employee_name: Optional[str] = Field(
        None,
        description="Tên nhân viên / Employee name"
    )
    period: SalaryPeriod = Field(
        ...,
        description="Kỳ lương / Salary period"
    )
    summary: SalarySummary = Field(
        ...,
        description="Tóm tắt lương / Salary summary"
    )
    income: SalaryIncome = Field(
        ...,
        description="Thu nhập / Income details"
    )
    deductions: SalaryDeductions = Field(
        ...,
        description="Các khoản trừ / Deduction details"
    )

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
                    "thuong_nang_suat": 2000000.0,
                    "phu_cap_chuc_vu": 1500000.0,
                    "phu_cap_an_trua": 660000.0
                },
                "deductions": {
                    "bhxh": 1080840.0,
                    "bhtn": 144112.0,
                    "bhyt": 180140.0,
                    "thue_tncn": 1850000.0
                }
            }
        }


class MonthlySalary(BaseModel):
    """
    Lương tháng (Monthly Salary).

    Salary data for one month in a multi-month history query.
    """
    month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Tháng / Month (1-12)"
    )
    summary: SalarySummary = Field(
        ...,
        description="Tóm tắt lương / Salary summary"
    )
    income: SalaryIncome = Field(
        ...,
        description="Thu nhập / Income details"
    )
    deductions: SalaryDeductions = Field(
        ...,
        description="Các khoản trừ / Deduction details"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "month": 12,
                "summary": {
                    "tong_tien_cong": 15000000.0,
                    "tong_tien_tru": 3331510.0,
                    "thuc_linh": 11668490.0
                },
                "income": {"luong_co_ban": 7205600.0, "thuong_nang_suat": 2000000.0},
                "deductions": {"bhxh": 1080840.0, "thue_tncn": 1850000.0}
            }
        }


class SalaryChange(BaseModel):
    """
    Thay đổi lương (Salary Change).

    Represents a significant month-over-month change in salary.
    Detected when change > 10% or > 500,000 VND.
    """
    from_month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Từ tháng / From month"
    )
    to_month: int = Field(
        ...,
        ge=1,
        le=12,
        description="Đến tháng / To month"
    )
    field: str = Field(
        ...,
        description="Trường thay đổi / Field that changed (e.g., 'thuc_linh', 'luong_co_ban')"
    )
    change: float = Field(
        ...,
        description="Giá trị thay đổi / Absolute change amount (VND)"
    )
    percentage: float = Field(
        ...,
        description="Phần trăm thay đổi / Percentage change (%)"
    )
    direction: str = Field(
        ...,
        pattern="^(increase|decrease)$",
        description="Hướng thay đổi / Direction: 'increase' or 'decrease'"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "from_month": 11,
                "to_month": 12,
                "field": "thuc_linh",
                "change": 1500000.0,
                "percentage": 14.75,
                "direction": "increase"
            }
        }


class SalaryTrend(BaseModel):
    """
    Xu hướng lương (Salary Trend).

    Trend analysis across multiple months.
    Includes averages, extremes, and significant changes.
    """
    average_income: float = Field(
        ...,
        description="Thu nhập trung bình / Average monthly income (VND)"
    )
    average_deductions: float = Field(
        ...,
        description="Khấu trừ trung bình / Average monthly deductions (VND)"
    )
    average_net: float = Field(
        ...,
        description="Thực lĩnh trung bình / Average monthly net salary (VND)"
    )
    highest_month: Optional[MonthlySalary] = Field(
        None,
        description="Tháng cao nhất / Month with highest net salary"
    )
    lowest_month: Optional[MonthlySalary] = Field(
        None,
        description="Tháng thấp nhất / Month with lowest net salary"
    )
    significant_changes: List[SalaryChange] = Field(
        default_factory=list,
        description="Thay đổi đáng kể / Significant month-over-month changes (>10% or >500K VND)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "average_income": 14500000.0,
                "average_deductions": 3200000.0,
                "average_net": 11300000.0,
                "highest_month": {
                    "month": 12,
                    "summary": {
                        "tong_tien_cong": 15000000.0,
                        "tong_tien_tru": 3331510.0,
                        "thuc_linh": 11668490.0
                    },
                    "income": {"luong_co_ban": 7205600.0},
                    "deductions": {"bhxh": 1080840.0}
                },
                "lowest_month": {
                    "month": 1,
                    "summary": {
                        "tong_tien_cong": 13000000.0,
                        "tong_tien_tru": 3100000.0,
                        "thuc_linh": 9900000.0
                    },
                    "income": {"luong_co_ban": 7205600.0},
                    "deductions": {"bhxh": 1080840.0}
                },
                "significant_changes": [
                    {
                        "from_month": 6,
                        "to_month": 7,
                        "field": "thuong_nang_suat",
                        "change": 1000000.0,
                        "percentage": 100.0,
                        "direction": "increase"
                    }
                ]
            }
        }


class SalaryHistoryResponse(BaseModel):
    """
    Lịch sử lương (Salary History Response).

    Response schema for multi-month salary history query.
    Includes monthly data and trend analysis.
    """
    employee_id: str = Field(
        ...,
        description="Mã nhân viên / Employee ID (e.g., VNW0006204)"
    )
    employee_name: Optional[str] = Field(
        None,
        description="Tên nhân viên / Employee name"
    )
    period: SalaryPeriod = Field(
        ...,
        description="Kỳ truy vấn / Query period (year, month range)"
    )
    months: List[MonthlySalary] = Field(
        default_factory=list,
        description="Dữ liệu từng tháng / Monthly salary data"
    )
    trend: Optional[SalaryTrend] = Field(
        None,
        description="Phân tích xu hướng / Trend analysis"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "employee_id": "VNW0006204",
                "employee_name": "PHAN ANH TUẤN",
                "period": {"year": 2024, "month": 12},
                "months": [
                    {
                        "month": 10,
                        "summary": {
                            "tong_tien_cong": 14000000.0,
                            "tong_tien_tru": 3200000.0,
                            "thuc_linh": 10800000.0
                        },
                        "income": {"luong_co_ban": 7205600.0},
                        "deductions": {"bhxh": 1080840.0}
                    },
                    {
                        "month": 11,
                        "summary": {
                            "tong_tien_cong": 14500000.0,
                            "tong_tien_tru": 3300000.0,
                            "thuc_linh": 11200000.0
                        },
                        "income": {"luong_co_ban": 7205600.0},
                        "deductions": {"bhxh": 1080840.0}
                    },
                    {
                        "month": 12,
                        "summary": {
                            "tong_tien_cong": 15000000.0,
                            "tong_tien_tru": 3331510.0,
                            "thuc_linh": 11668490.0
                        },
                        "income": {"luong_co_ban": 7205600.0},
                        "deductions": {"bhxh": 1080840.0}
                    }
                ],
                "trend": {
                    "average_income": 14500000.0,
                    "average_deductions": 3277170.0,
                    "average_net": 11222830.0,
                    "highest_month": None,
                    "lowest_month": None,
                    "significant_changes": []
                }
            }
        }
