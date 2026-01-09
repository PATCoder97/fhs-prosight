"""
Integration tests for employee API endpoints.
Tests the full request/response cycle including auth, validation, and database operations.
"""
import pytest
from fastapi import status
from unittest.mock import patch, AsyncMock


# =============================================================================
# POST /api/employees/sync
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_employee_from_hrs_success(client, admin_token, mock_hrs_client_success):
    """Test syncing employee from HRS API as admin"""
    with patch('app.services.employee_service.hrs_client.get_employee_info') as mock_get:
        mock_get.return_value = mock_hrs_client_success

        response = await client.post(
            "/api/employees/sync",
            json={"emp_id": 6204, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "VNW0006204"
        assert data["name_tw"] == "陳玉俊"
        assert data["name_en"] == "Phan Anh Tuấn"  # Normalized


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_employee_from_covid_success(client, admin_token, mock_covid_client_success):
    """Test syncing employee from COVID API with token"""
    with patch('app.services.employee_service.covid_client.get_user_info') as mock_get:
        mock_get.return_value = mock_covid_client_success

        response = await client.post(
            "/api/employees/sync",
            json={"emp_id": 6204, "source": "covid", "token": "valid_token_123"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == "VNW0006204"
        assert data["identity_number"] == "044090004970"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_employee_covid_without_token(client, admin_token):
    """Test sync from COVID without token returns 400"""
    response = await client.post(
        "/api/employees/sync",
        json={"emp_id": 6204, "source": "covid"},  # No token
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "token" in response.json()["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_employee_as_non_admin(client, user_token):
    """Test non-admin user cannot sync employees"""
    response = await client.post(
        "/api/employees/sync",
        json={"emp_id": 6204, "source": "hrs"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_employee_not_found(client, admin_token):
    """Test sync with invalid employee ID returns 404"""
    with patch('app.services.employee_service.hrs_client.get_employee_info') as mock_get:
        mock_get.return_value = None  # Not found

        response = await client.post(
            "/api/employees/sync",
            json={"emp_id": 9999, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_employee_invalid_source(client, admin_token):
    """Test sync with invalid source returns 400"""
    response = await client.post(
        "/api/employees/sync",
        json={"emp_id": 6204, "source": "invalid"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# POST /api/employees/bulk-sync
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_sync_from_hrs_success(client, admin_token, mock_hrs_client_success):
    """Test bulk sync from HRS returns correct summary"""
    with patch('app.services.employee_service.hrs_client.bulk_get_employees') as mock_bulk:
        # Mock: 3 employees, 2 success, 1 None (skipped)
        mock_bulk.return_value = [
            mock_hrs_client_success,
            None,  # Skipped
            {**mock_hrs_client_success, "employee_id": "VNW0006205"}
        ]

        response = await client.post(
            "/api/employees/bulk-sync",
            json={"from_id": 6204, "to_id": 6206, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert data["success"] == 2
        assert data["skipped"] == 1
        assert "errors" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_sync_from_covid_with_token(client, admin_token, mock_covid_client_success):
    """Test bulk sync from COVID with token"""
    with patch('app.services.employee_service.covid_client.bulk_get_users') as mock_bulk:
        mock_bulk.return_value = [mock_covid_client_success]

        response = await client.post(
            "/api/employees/bulk-sync",
            json={"from_id": 6204, "to_id": 6204, "source": "covid", "token": "valid_token"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 1
        assert data["success"] >= 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_sync_invalid_range(client, admin_token):
    """Test bulk sync with to_id < from_id returns 422"""
    response = await client.post(
        "/api/employees/bulk-sync",
        json={"from_id": 6210, "to_id": 6200, "source": "hrs"},  # Invalid range
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_sync_as_non_admin(client, user_token):
    """Test non-admin cannot bulk sync"""
    response = await client.post(
        "/api/employees/bulk-sync",
        json={"from_id": 6200, "to_id": 6210, "source": "hrs"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# GET /api/employees/search
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_employees_by_name(client, admin_token, sample_employee):
    """Test search employees by name (ILIKE match)"""
    response = await client.get(
        "/api/employees/search",
        params={"name": "陳玉"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert len(data["items"]) >= 1
    assert data["items"][0]["id"] == "VNW0006204"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_employees_by_department(client, admin_token, sample_employee):
    """Test search by department_code"""
    response = await client.get(
        "/api/employees/search",
        params={"department_code": "7410"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["items"]) >= 1
    assert all(emp["department_code"] == "7410" for emp in data["items"])


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_employees_pagination(client, admin_token, sample_employee):
    """Test search with pagination"""
    response = await client.get(
        "/api/employees/search",
        params={"skip": 0, "limit": 10},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "skip" in data
    assert "limit" in data
    assert data["skip"] == 0
    assert data["limit"] == 10


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_as_non_admin(client, user_token):
    """Test non-admin cannot search employees"""
    response = await client.get(
        "/api/employees/search",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# GET /api/employees/{emp_id}
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_employee_by_id_success(client, admin_token, sample_employee):
    """Test get employee by ID returns employee"""
    response = await client.get(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == "VNW0006204"
    assert data["name_tw"] == "陳玉俊"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_employee_not_found(client, admin_token):
    """Test get non-existent employee returns 404"""
    response = await client.get(
        "/api/employees/VNW9999999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_employee_as_non_admin(client, user_token):
    """Test non-admin cannot get employee details"""
    response = await client.get(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# PUT /api/employees/{emp_id}
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_employee_success(client, admin_token, sample_employee):
    """Test update employee updates fields"""
    response = await client.put(
        "/api/employees/VNW0006204",
        json={"job_title": "Senior Engineer", "salary": 8000000},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["job_title"] == "Senior Engineer"
    assert data["salary"] == 8000000


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_employee_not_found(client, admin_token):
    """Test update non-existent employee returns 404"""
    response = await client.put(
        "/api/employees/VNW9999999",
        json={"job_title": "Test"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_employee_as_non_admin(client, user_token, sample_employee):
    """Test non-admin cannot update employee"""
    response = await client.put(
        "/api/employees/VNW0006204",
        json={"job_title": "Test"},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# DELETE /api/employees/{emp_id}
# =============================================================================

@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_employee_success(client, admin_token, sample_employee):
    """Test delete employee returns success"""
    response = await client.delete(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True

    # Verify deleted
    get_response = await client.get(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_employee_not_found(client, admin_token):
    """Test delete non-existent employee returns false"""
    response = await client.delete(
        "/api/employees/VNW9999999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is False


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_employee_as_non_admin(client, user_token, sample_employee):
    """Test non-admin cannot delete employee"""
    response = await client.delete(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
