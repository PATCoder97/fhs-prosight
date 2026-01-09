"""
Integration tests for salary API endpoints.

Tests all 3 endpoints with authentication, authorization, and error cases:
1. GET /api/hrs-data/salary - View own salary
2. GET /api/hrs-data/salary/history - View salary history with trend
3. GET /api/hrs-data/salary/{employee_id} - Admin view any employee's salary
"""

import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
@pytest.mark.integration
class TestGetOwnSalaryEndpoint:
    """Test GET /api/hrs-data/salary endpoint"""

    async def test_get_own_salary_current_month_success(self, client, user_token, sample_employee):
        """Test GET /salary returns own salary for current month"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {
                    "luong_co_ban": 10000000,
                    "thuong_nang_suat": 2000000
                },
                "deductions": {
                    "bhxh": 1500000,
                    "bhyt": 200000
                }
            })()

            response = await client.get(
                "/api/hrs-data/salary?year=2024&month=12",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["employee_id"] == "VNW002"
            assert data["period"]["year"] == 2024
            assert data["period"]["month"] == 12
            assert data["summary"]["thuc_linh"] == 12000000
            assert data["income"]["luong_co_ban"] == 10000000
            assert data["deductions"]["bhxh"] == 1500000

    async def test_get_own_salary_default_current_month(self, client, user_token, sample_employee):
        """Test GET /salary without parameters defaults to current month"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            })()

            response = await client.get(
                "/api/hrs-data/salary",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "period" in data
            # Year and month should default to current date

    async def test_get_salary_unauthenticated_returns_401(self, client):
        """Test GET /salary without authentication returns 401"""
        response = await client.get("/api/hrs-data/salary")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_salary_not_found_returns_404(self, client, user_token):
        """Test GET /salary returns 404 when salary not found"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value=None)()

            response = await client.get(
                "/api/hrs-data/salary?year=1990&month=1",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"].lower()

    async def test_get_salary_specific_month_success(self, client, user_token, sample_employee):
        """Test GET /salary with specific month returns correct data"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 16000000,
                    "tong_tien_tru": 3200000,
                    "thuc_linh": 12800000
                },
                "income": {},
                "deductions": {}
            })()

            response = await client.get(
                "/api/hrs-data/salary?year=2024&month=6",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["period"]["year"] == 2024
            assert data["period"]["month"] == 6
            assert data["summary"]["thuc_linh"] == 12800000


@pytest.mark.asyncio
@pytest.mark.integration
class TestGetSalaryHistoryEndpoint:
    """Test GET /api/hrs-data/salary/history endpoint"""

    async def test_get_salary_history_full_year_success(self, client, user_token, sample_employee):
        """Test GET /salary/history returns full year history with trend"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            # Mock returns different salary for each month
            async def mock_salary_data(emp_num, year, month):
                return {
                    "summary": {
                        "tong_tien_cong": 15000000 + (month * 100000),
                        "tong_tien_tru": 3000000,
                        "thuc_linh": 12000000 + (month * 100000)
                    },
                    "income": {},
                    "deductions": {}
                }

            mock_get.side_effect = mock_salary_data

            response = await client.get(
                "/api/hrs-data/salary/history?year=2024&from_month=1&to_month=12",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["employee_id"] == "VNW002"
            assert data["period"]["year"] == 2024
            assert data["period"]["month"] == "1-12"
            assert len(data["months"]) == 12
            assert "trend" in data
            assert "average_net" in data["trend"]
            assert "highest_month" in data["trend"]
            assert "lowest_month" in data["trend"]
            assert "significant_changes" in data["trend"]

    async def test_get_salary_history_partial_year_success(self, client, user_token, sample_employee):
        """Test GET /salary/history returns partial year (Q1)"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            })()

            response = await client.get(
                "/api/hrs-data/salary/history?year=2024&from_month=1&to_month=3",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["period"]["month"] == "1-3"
            assert len(data["months"]) == 3

    async def test_get_salary_history_invalid_month_range_returns_422(self, client, user_token):
        """Test GET /salary/history with invalid month range returns 422"""
        response = await client.get(
            "/api/hrs-data/salary/history?year=2024&from_month=6&to_month=3",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "Invalid month range" in response.json()["detail"]

    async def test_get_salary_history_unauthenticated_returns_401(self, client):
        """Test GET /salary/history without authentication returns 401"""
        response = await client.get("/api/hrs-data/salary/history?year=2024")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_salary_history_no_data_returns_404(self, client, user_token):
        """Test GET /salary/history with no data returns 404"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value=None)()

            response = await client.get(
                "/api/hrs-data/salary/history?year=1990&from_month=1&to_month=12",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "No salary data found" in response.json()["detail"]

    async def test_get_salary_history_default_month_range(self, client, user_token, sample_employee):
        """Test GET /salary/history defaults to full year (1-12)"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 15000000,
                    "tong_tien_tru": 3000000,
                    "thuc_linh": 12000000
                },
                "income": {},
                "deductions": {}
            })()

            response = await client.get(
                "/api/hrs-data/salary/history?year=2024",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["period"]["month"] == "1-12"


@pytest.mark.asyncio
@pytest.mark.integration
class TestGetEmployeeSalaryAdminEndpoint:
    """Test GET /api/hrs-data/salary/{employee_id} endpoint (admin only)"""

    async def test_get_employee_salary_admin_success(self, client, admin_token, sample_employee):
        """Test GET /salary/{employee_id} as admin returns employee salary"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value={
                "summary": {
                    "tong_tien_cong": 20000000,
                    "tong_tien_tru": 4000000,
                    "thuc_linh": 16000000
                },
                "income": {
                    "luong_co_ban": 15000000
                },
                "deductions": {
                    "bhxh": 2000000
                }
            })()

            response = await client.get(
                "/api/hrs-data/salary/VNW0006204?year=2024&month=12",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["employee_id"] == "VNW0006204"
            assert data["summary"]["thuc_linh"] == 16000000

    async def test_get_employee_salary_non_admin_forbidden(self, client, user_token):
        """Test GET /salary/{employee_id} as non-admin returns 403"""
        response = await client.get(
            "/api/hrs-data/salary/VNW0009999?year=2024&month=12",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "admin" in response.json()["detail"].lower() or "forbidden" in response.json()["detail"].lower()

    async def test_get_employee_salary_invalid_id_returns_400(self, client, admin_token):
        """Test GET /salary/{employee_id} with invalid ID format returns 400"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            # The service should raise 400 before calling HRS API
            response = await client.get(
                "/api/hrs-data/salary/INVALID123?year=2024&month=12",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert "Invalid employee ID" in response.json()["detail"]

    async def test_get_employee_salary_unauthenticated_returns_401(self, client):
        """Test GET /salary/{employee_id} without authentication returns 401"""
        response = await client.get("/api/hrs-data/salary/VNW0006204?year=2024&month=12")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_get_employee_salary_not_found_returns_404(self, client, admin_token):
        """Test GET /salary/{employee_id} with non-existent salary returns 404"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.return_value = AsyncMock(return_value=None)()

            response = await client.get(
                "/api/hrs-data/salary/VNW0099999?year=1990&month=1",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            assert "not found" in response.json()["detail"].lower()

    async def test_get_employee_salary_missing_year_returns_422(self, client, admin_token):
        """Test GET /salary/{employee_id} without required year parameter returns 422"""
        response = await client.get(
            "/api/hrs-data/salary/VNW0006204?month=12",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # FastAPI validation error for missing required field
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_get_employee_salary_missing_month_returns_422(self, client, admin_token):
        """Test GET /salary/{employee_id} without required month parameter returns 422"""
        response = await client.get(
            "/api/hrs-data/salary/VNW0006204?year=2024",
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        # FastAPI validation error for missing required field
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
@pytest.mark.integration
class TestSalaryEndpointsErrorHandling:
    """Test error handling across all salary endpoints"""

    async def test_hrs_api_unavailable_returns_503(self, client, user_token):
        """Test HRS API unavailable returns 503"""
        with patch('app.integrations.fhs_hrs_client.FHSHRSClient.get_salary_data') as mock_get:
            mock_get.side_effect = Exception("HRS API connection failed")

            response = await client.get(
                "/api/hrs-data/salary?year=2024&month=12",
                headers={"Authorization": f"Bearer {user_token}"}
            )

            assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

    async def test_invalid_year_validation(self, client, user_token):
        """Test year validation (must be 2000-2100)"""
        response = await client.get(
            "/api/hrs-data/salary?year=1900&month=12",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_invalid_month_validation(self, client, user_token):
        """Test month validation (must be 1-12)"""
        response = await client.get(
            "/api/hrs-data/salary?year=2024&month=13",
            headers={"Authorization": f"Bearer {user_token}"}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
