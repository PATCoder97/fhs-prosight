from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# Reusable Components

class EvaluationLevel(BaseModel):
    """Single evaluation level (init/review/final)."""
    score: Optional[str] = Field(None, description="評核成績 (甲/優/etc.)")
    comment: Optional[str] = Field(None, description="評語")
    reviewer: Optional[str] = Field(None, description="主管工號")

    class Config:
        json_schema_extra = {
            "example": {
                "score": "甲",
                "comment": "本月完成審核共1305個力學試驗數據，及時率100%",
                "reviewer": "VNW0004677"
            }
        }


class EvaluationGroup(BaseModel):
    """Evaluation group (dept or mgr)."""
    init: EvaluationLevel = Field(..., description="初核")
    review: EvaluationLevel = Field(..., description="複核")
    final: EvaluationLevel = Field(..., description="核定")

    class Config:
        json_schema_extra = {
            "example": {
                "init": {"score": "優", "comment": "工作表現優秀", "reviewer": "VNW0004635"},
                "review": {"score": "優", "comment": "確認評核結果", "reviewer": "VNW0013364"},
                "final": {"score": "優", "comment": "核定通過", "reviewer": "VNW0003380"}
            }
        }


# Response Models

class EvaluationResponse(BaseModel):
    """Response model for evaluation record."""
    id: int = Field(..., description="Evaluation record ID")
    term_code: str = Field(..., description="評核年月 (e.g., 25B)")
    employee_id: str = Field(..., description="工號 (e.g., VNW0018983)")
    employee_name: Optional[str] = Field(None, description="姓名")
    job_level: Optional[str] = Field(None, description="職等")
    nation: Optional[str] = Field(None, description="國籍 (TW/VN)")
    dept_code: Optional[str] = Field(None, description="部門代碼")
    dept_name: Optional[str] = Field(None, description="部門名稱")
    grade_code: Optional[str] = Field(None, description="職等六碼")
    grade_name: Optional[str] = Field(None, description="職等名稱")
    dept_evaluation: EvaluationGroup = Field(..., description="部門評核 (初核/複核/核定)")
    mgr_evaluation: EvaluationGroup = Field(..., description="經理室評核 (初核/複核/核定)")
    leave_days: Optional[float] = Field(None, description="請假總日數")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: Optional[datetime] = Field(None, description="更新時間")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "term_code": "25B",
                "employee_id": "VNW0018983",
                "employee_name": "阮氏幸",
                "job_level": "基層人員",
                "nation": "VN",
                "dept_code": "7800",
                "dept_name": "冶金技術部物理試驗處處務室",
                "grade_code": "MZD01P",
                "grade_name": "助理管理師",
                "dept_evaluation": {
                    "init": {"score": "甲", "comment": "", "reviewer": "VNW0004635"},
                    "review": {"score": "甲", "comment": "", "reviewer": None},
                    "final": {"score": "甲", "comment": "", "reviewer": "VNW0003380"}
                },
                "mgr_evaluation": {
                    "init": {"score": "甲", "comment": "", "reviewer": "VNW0013364"},
                    "review": {"score": "甲", "comment": "", "reviewer": "VNW0004740"},
                    "final": {"score": "甲", "comment": "", "reviewer": "VNW0001140"}
                },
                "leave_days": 0.125,
                "created_at": "2026-01-10T09:00:00Z",
                "updated_at": "2026-01-10T09:00:00Z"
            }
        }


class SearchResponse(BaseModel):
    """Paginated search response."""
    total: int = Field(..., description="Total matching records", ge=0)
    page: int = Field(..., description="Current page number", ge=1)
    page_size: int = Field(..., description="Items per page", ge=1, le=100)
    results: List[EvaluationResponse] = Field(..., description="Evaluation records")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 250,
                "page": 1,
                "page_size": 50,
                "results": [
                    {
                        "id": 1,
                        "term_code": "25B",
                        "employee_id": "VNW0018983",
                        "employee_name": "阮氏幸",
                        "job_level": "基層人員",
                        "nation": "VN",
                        "dept_code": "7800",
                        "dept_name": "冶金技術部物理試驗處處務室",
                        "grade_code": "MZD01P",
                        "grade_name": "助理管理師",
                        "dept_evaluation": {
                            "init": {"score": "甲", "comment": "", "reviewer": "VNW0004635"},
                            "review": {"score": "甲", "comment": "", "reviewer": None},
                            "final": {"score": "甲", "comment": "", "reviewer": "VNW0003380"}
                        },
                        "mgr_evaluation": {
                            "init": {"score": "甲", "comment": "", "reviewer": "VNW0013364"},
                            "review": {"score": "甲", "comment": "", "reviewer": "VNW0004740"},
                            "final": {"score": "甲", "comment": "", "reviewer": "VNW0001140"}
                        },
                        "leave_days": 0.125,
                        "created_at": "2026-01-10T09:00:00Z",
                        "updated_at": "2026-01-10T09:00:00Z"
                    }
                ]
            }
        }


class UploadSummary(BaseModel):
    """Upload result summary."""
    success: bool = Field(..., description="Whether upload succeeded")
    summary: dict = Field(..., description="Counts: total_rows, created, updated, errors")
    error_details: List[dict] = Field(default_factory=list, description="Error details per row")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "summary": {
                    "total_rows": 150,
                    "created": 120,
                    "updated": 30,
                    "errors": 0
                },
                "error_details": []
            }
        }
