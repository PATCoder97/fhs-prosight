"""
Unit tests for HRS data service layer.

Tests for:
- calculate_trend() function with various scenarios
- get_employee_salary() with success and error cases
- get_salary_history() with success and error cases
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from fastapi import HTTPException

from app.services.hrs_data_service import (
    calculate_trend,
    get_employee_salary,
    get_salary_history
)


class TestCalculateTrend:
    """Test calculate_trend function with various data scenarios"""

    def test_single_month_no_trend(self):
        """Test trend calculation with single month (no trend analysis possible)"""
        monthly_data = [
            {
                "month": 1,
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            }
        ]
        trend = calculate_trend(monthly_data)

        assert trend["average_net"] == 12000000
        assert trend["average_income"] == 15000000
        assert trend["average_deductions"] == 3000000
        assert trend["highest_month"]["month"] == 1
        assert trend["lowest_month"]["month"] == 1
        assert len(trend["significant_changes"]) == 0

    def test_multiple_months_consistent_salary(self):
        """Test trend with consistent salary across multiple months (no significant changes)"""
        monthly_data = [
            {
                "month": i,
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            }
            for i in range(1, 13)
        ]
        trend = calculate_trend(monthly_data)

        assert trend["average_net"] == 12000000
        assert trend["average_income"] == 15000000
        assert trend["average_deductions"] == 3000000
        assert len(trend["significant_changes"]) == 0

        # All months have same salary, so highest and lowest are just first and last in sort
        assert trend["highest_month"]["summary"]["thuc_linh"] == 12000000
        assert trend["lowest_month"]["summary"]["thuc_linh"] == 12000000

    def test_multiple_months_with_significant_percentage_change(self):
        """Test trend calculation with >10% salary increase"""
        monthly_data = [
            {
                "month": 1,
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            },
            {
                "month": 2,
                "summary": {
                    "tong_tien_cong": 20000000,
                    "tong_tien_tru": 4000000,
                    "thuc_linh": 16000000
                },
                "income": {},
                "deductions": {}
            }
        ]
        trend = calculate_trend(monthly_data)

        assert trend["average_net"] == 14000000
        assert trend["highest_month"]["month"] == 2
        assert trend["lowest_month"]["month"] == 1
        assert len(trend["significant_changes"]) == 1

        change = trend["significant_changes"][0]
        assert change["from_month"] == 1
        assert change["to_month"] == 2
        assert change["field"] == "thuc_linh"
        assert change["change"] == 4000000
        assert change["percentage"] == pytest.approx(33.33, rel=0.01)
        assert change["direction"] == "increase"

    def test_multiple_months_with_significant_absolute_change(self):
        """Test 600K change (>500K threshold) but <10% still triggers significant change"""
        monthly_data = [
            {
                "month": 1,
                "summary": {
                    "tong_tien_cong": 10000000,
                    "tong_tien_tru": 2000000,
                    "thuc_linh": 8000000
                },
                "income": {},
                "deductions": {}
            },
            {
                "month": 2,
                "summary": {
                    "tong_tien_cong": 10600000,
                    "tong_tien_tru": 2000000,
                    "thuc_linh": 8600000
                },
                "income": {},
                "deductions": {}
            }
        ]
        trend = calculate_trend(monthly_data)

        # 600K change is 7.5% (< 10%) but > 500K threshold
        assert len(trend["significant_changes"]) == 1

        change = trend["significant_changes"][0]
        assert change["change"] == 600000
        assert change["percentage"] == pytest.approx(7.5, rel=0.01)
        assert change["direction"] == "increase"

    def test_significant_decrease_detection(self):
        """Test detection of significant salary decrease"""
        monthly_data = [
            {
                "month": 1,
                "summary": {
                    "tong_tien_cong": 20000000,
                    "tong_tien_tru": 4000000,
                    "thuc_linh": 16000000
                },
                "income": {},
                "deductions": {}
            },
            {
                "month": 2,
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            }
        ]
        trend = calculate_trend(monthly_data)

        assert len(trend["significant_changes"]) == 1

        change = trend["significant_changes"][0]
        assert change["from_month"] == 1
        assert change["to_month"] == 2
        assert change["change"] == -4000000
        assert change["percentage"] == pytest.approx(-25.0, rel=0.01)
        assert change["direction"] == "decrease"

    def test_empty_data_returns_none(self):
        """Test trend calculation with no data returns None"""
        trend = calculate_trend([])
        assert trend is None

    def test_identical_salary_no_significant_changes(self):
        """Test multiple months with identical values produces no significant changes"""
        monthly_data = [
            {
                "month": i,
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            }
            for i in range(1, 13)
        ]
        trend = calculate_trend(monthly_data)

        assert trend["average_net"] == 12000000
        assert len(trend["significant_changes"]) == 0

    def test_edge_case_just_below_thresholds(self):
        """Test change just below both thresholds (9.9% and 499K) is not significant"""
        monthly_data = [
            {
                "month": 1,
                "summary": {
                    "tong_tien_cong": 10000000,
                    "tong_tien_tru": 2000000,
                    "thuc_linh": 8000000
                },
                "income": {},
                "deductions": {}
            },
            {
                "month": 2,
                "summary": {
                    "tong_tien_cong": 10490000,
                    "tong_tien_tru": 2000000,
                    "thuc_linh": 8490000
                },
                "income": {},
                "deductions": {}
            }
        ]
        trend = calculate_trend(monthly_data)

        # 490K change is 6.125% (both below thresholds)
        assert len(trend["significant_changes"]) == 0


@pytest.mark.asyncio
class TestGetEmployeeSalary:
    """Test get_employee_salary function"""

    async def test_successful_salary_fetch_with_employee_name(self):
        """Test successful salary retrieval with employee name from database"""
        # Mock database session
        mock_db = AsyncMock()

        # Mock employee lookup
        mock_employee = Mock()
        mock_employee.name_en = "PHAN ANH TUẤN"
        mock_db.get = AsyncMock(return_value=mock_employee)

        # Mock HRS client
        with patch('app.services.hrs_data_service.FHSHRSClient') as MockHRSClient:
            mock_hrs_client = AsyncMock()
            mock_hrs_client.get_salary_data = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {"luong_co_ban": 10000000},
                "deductions": {"bhxh": 1500000}
            })
            MockHRSClient.return_value = mock_hrs_client

            # Call service
            result = await get_employee_salary(mock_db, "VNW0006204", 2024, 12)

            assert result["employee_id"] == "VNW0006204"
            assert result["employee_name"] == "PHAN ANH TUẤN"
            assert result["period"]["year"] == 2024
            assert result["period"]["month"] == 12
            assert result["summary"]["thuc_linh"] == 12000000
            assert result["income"]["luong_co_ban"] == 10000000
            assert result["deductions"]["bhxh"] == 1500000

    async def test_employee_not_in_database_returns_unknown(self):
        """Test salary fetch when employee not found in database returns 'Unknown' name"""
        # Mock database session
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)  # Employee not found

        # Mock HRS client
        with patch('app.services.hrs_data_service.FHSHRSClient') as MockHRSClient:
            mock_hrs_client = AsyncMock()
            mock_hrs_client.get_salary_data = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            })
            MockHRSClient.return_value = mock_hrs_client

            result = await get_employee_salary(mock_db, "VNW0099999", 2024, 12)

            assert result["employee_name"] == "Unknown"

    async def test_hrs_api_returns_none_raises_404(self):
        """Test error when HRS API returns None (salary not found)"""
        mock_db = AsyncMock()

        # Mock HRS client to return None
        with patch('app.services.hrs_data_service.FHSHRSClient') as MockHRSClient:
            mock_hrs_client = AsyncMock()
            mock_hrs_client.get_salary_data = AsyncMock(return_value=None)
            MockHRSClient.return_value = mock_hrs_client

            with pytest.raises(HTTPException) as exc_info:
                await get_employee_salary(mock_db, "VNW0006204", 1990, 1)

            assert exc_info.value.status_code == 404
            assert "not found" in exc_info.value.detail.lower()

    async def test_invalid_employee_id_format_raises_400(self):
        """Test invalid employee ID format raises 400 error"""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_employee_salary(mock_db, "INVALID123", 2024, 12)

        assert exc_info.value.status_code == 400
        assert "Invalid employee ID format" in exc_info.value.detail

    async def test_hrs_api_exception_raises_503(self):
        """Test HRS API exception raises 503 error"""
        mock_db = AsyncMock()

        # Mock HRS client to raise exception
        with patch('app.services.hrs_data_service.FHSHRSClient') as MockHRSClient:
            mock_hrs_client = AsyncMock()
            mock_hrs_client.get_salary_data = AsyncMock(
                side_effect=Exception("HRS API connection failed")
            )
            MockHRSClient.return_value = mock_hrs_client

            with pytest.raises(HTTPException) as exc_info:
                await get_employee_salary(mock_db, "VNW0006204", 2024, 12)

            assert exc_info.value.status_code == 503
            assert "unavailable" in exc_info.value.detail.lower()


@pytest.mark.asyncio
class TestGetSalaryHistory:
    """Test get_salary_history function"""

    async def test_successful_history_fetch_full_year(self):
        """Test successful salary history fetch for full year"""
        # Mock database session
        mock_db = AsyncMock()

        # Mock employee lookup
        mock_employee = Mock()
        mock_employee.name_en = "PHAN ANH TUẤN"
        mock_db.get = AsyncMock(return_value=mock_employee)

        # Mock HRS client to return 12 months of data
        with patch('app.services.hrs_data_service.FHSHRSClient') as MockHRSClient:
            mock_hrs_client = AsyncMock()

            # Create salary data for 12 months
            async def mock_get_salary(emp_num, year, month):
                return {
                    "summary": {
                        "tong_tien_cong": 15000000 + (month * 100000),
                        "tong_tien_tru": 3000000,
                        "thuc_linh": 12000000 + (month * 100000)
                    },
                    "income": {},
                    "deductions": {}
                }

            mock_hrs_client.get_salary_data = AsyncMock(side_effect=mock_get_salary)
            MockHRSClient.return_value = mock_hrs_client

            result = await get_salary_history(mock_db, "VNW0006204", 2024, 1, 12)

            assert result["employee_id"] == "VNW0006204"
            assert result["employee_name"] == "PHAN ANH TUẤN"
            assert result["period"]["year"] == 2024
            assert result["period"]["month"] == "1-12"
            assert len(result["months"]) == 12
            assert result["trend"] is not None
            assert result["trend"]["average_net"] == pytest.approx(12650000, rel=0.01)

    async def test_invalid_month_range_raises_422(self):
        """Test invalid month range (from_month > to_month) raises 422"""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_salary_history(mock_db, "VNW0006204", 2024, 6, 3)

        assert exc_info.value.status_code == 422
        assert "Invalid month range" in exc_info.value.detail

    async def test_month_out_of_range_raises_422(self):
        """Test month values outside 1-12 range raises 422"""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_salary_history(mock_db, "VNW0006204", 2024, 0, 13)

        assert exc_info.value.status_code == 422
        assert "Month must be between 1-12" in exc_info.value.detail

    async def test_no_salary_data_found_raises_404(self):
        """Test no salary data found for any month raises 404"""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        # Mock HRS client to return None for all months
        with patch('app.services.hrs_data_service.FHSHRSClient') as MockHRSClient:
            mock_hrs_client = AsyncMock()
            mock_hrs_client.get_salary_data = AsyncMock(return_value=None)
            MockHRSClient.return_value = mock_hrs_client

            with pytest.raises(HTTPException) as exc_info:
                await get_salary_history(mock_db, "VNW0006204", 1990, 1, 12)

            assert exc_info.value.status_code == 404
            assert "No salary data found" in exc_info.value.detail

    async def test_partial_month_data_success(self):
        """Test history with partial data (some months missing) still succeeds"""
        mock_db = AsyncMock()

        # Mock employee lookup
        mock_employee = Mock()
        mock_employee.name_en = "TEST USER"
        mock_db.get = AsyncMock(return_value=mock_employee)

        # Mock HRS client to return data for only some months
        with patch('app.services.hrs_data_service.FHSHRSClient') as MockHRSClient:
            mock_hrs_client = AsyncMock()

            async def mock_get_salary(emp_num, year, month):
                # Return data only for months 1, 3, 5 (odd months)
                if month % 2 == 1:
                    return {
                        "summary": {
                            "tong_tien_cong": 15000000,
                            "tong_tien_tru": 3000000,
                            "thuc_linh": 12000000
                        },
                        "income": {},
                        "deductions": {}
                    }
                return None

            mock_hrs_client.get_salary_data = AsyncMock(side_effect=mock_get_salary)
            MockHRSClient.return_value = mock_hrs_client

            result = await get_salary_history(mock_db, "VNW0006204", 2024, 1, 6)

            # Should have 3 months (1, 3, 5)
            assert len(result["months"]) == 3
            assert result["trend"] is not None

    async def test_invalid_employee_id_format_raises_400(self):
        """Test invalid employee ID format raises 400"""
        mock_db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await get_salary_history(mock_db, "BADFORMAT", 2024, 1, 12)

        assert exc_info.value.status_code == 400
        assert "Invalid employee ID format" in exc_info.value.detail

    async def test_hrs_api_critical_error_raises_503(self):
        """Test critical HRS API error during parallel fetch raises 503"""
        mock_db = AsyncMock()
        mock_db.get = AsyncMock(return_value=None)

        # Mock HRS client to raise exception during gather
        with patch('app.services.hrs_data_service.asyncio.gather') as mock_gather:
            mock_gather.side_effect = Exception("Critical API failure")

            with pytest.raises(HTTPException) as exc_info:
                await get_salary_history(mock_db, "VNW0006204", 2024, 1, 12)

            assert exc_info.value.status_code == 503
            assert "unavailable" in exc_info.value.detail.lower()
