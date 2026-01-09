"""
Workflow integration tests for employee management.
Tests complete user workflows and realistic scenarios.
"""
import pytest
from fastapi import status
from unittest.mock import patch


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_employee_lifecycle(client, admin_token, mock_hrs_client_success):
    """Test complete workflow: sync → get → update → search → delete"""

    # 1. Sync employee from HRS
    with patch('app.services.employee_service.hrs_client.get_employee_info') as mock_get:
        mock_get.return_value = mock_hrs_client_success

        sync_resp = await client.post(
            "/api/employees/sync",
            json={"emp_id": 6204, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert sync_resp.status_code == status.HTTP_200_OK
        assert sync_resp.json()["id"] == "VNW0006204"

    # 2. Get employee by ID
    get_resp = await client.get(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_resp.status_code == status.HTTP_200_OK
    employee_data = get_resp.json()
    assert employee_data["name_tw"] == "陳玉俊"

    # 3. Update employee
    update_resp = await client.put(
        "/api/employees/VNW0006204",
        json={"job_title": "Lead Engineer", "salary": 9000000},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_resp.status_code == status.HTTP_200_OK
    updated_data = update_resp.json()
    assert updated_data["job_title"] == "Lead Engineer"
    assert updated_data["salary"] == 9000000

    # 4. Search finds updated employee
    search_resp = await client.get(
        "/api/employees/search",
        params={"name": "陳玉"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert search_resp.status_code == status.HTTP_200_OK
    search_data = search_resp.json()
    assert len(search_data["items"]) >= 1
    found_emp = next((e for e in search_data["items"] if e["id"] == "VNW0006204"), None)
    assert found_emp is not None
    assert found_emp["job_title"] == "Lead Engineer"

    # 5. Delete employee
    delete_resp = await client.delete(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert delete_resp.status_code == status.HTTP_200_OK
    assert delete_resp.json()["success"] is True

    # 6. Verify employee is deleted
    get_after_delete = await client.get(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_after_delete.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
@pytest.mark.integration
async def test_bulk_sync_then_search_all(client, admin_token, mock_hrs_client_success):
    """Test bulk sync → search shows all synced employees"""

    with patch('app.services.employee_service.hrs_client.bulk_get_employees') as mock_bulk:
        # Mock 3 employees
        mock_bulk.return_value = [
            {**mock_hrs_client_success, "employee_id": "VNW0006200"},
            {**mock_hrs_client_success, "employee_id": "VNW0006201"},
            {**mock_hrs_client_success, "employee_id": "VNW0006202"}
        ]

        # Bulk sync
        sync_resp = await client.post(
            "/api/employees/bulk-sync",
            json={"from_id": 6200, "to_id": 6202, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert sync_resp.status_code == status.HTTP_200_OK
        sync_data = sync_resp.json()
        assert sync_data["total"] == 3
        assert sync_data["success"] >= 2  # At least 2 should succeed

    # Search by department (all should have same dept)
    search_resp = await client.get(
        "/api/employees/search",
        params={"department_code": "7410"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert search_resp.status_code == status.HTTP_200_OK
    search_data = search_resp.json()
    assert len(search_data["items"]) >= 2  # At least the synced ones


@pytest.mark.asyncio
@pytest.mark.integration
async def test_update_then_get_shows_updated_data(client, admin_token, sample_employee):
    """Test update employee → get shows updated data"""

    # Update employee
    update_resp = await client.put(
        "/api/employees/VNW0006204",
        json={
            "job_title": "Senior Software Engineer",
            "salary": 10000000,
            "phone1": "0987654321"
        },
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert update_resp.status_code == status.HTTP_200_OK

    # Get employee and verify updates
    get_resp = await client.get(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_resp.status_code == status.HTTP_200_OK
    employee = get_resp.json()
    assert employee["job_title"] == "Senior Software Engineer"
    assert employee["salary"] == 10000000
    assert employee["phone1"] == "0987654321"
    # Original fields should remain
    assert employee["name_tw"] == "陳玉俊"
    assert employee["department_code"] == "7410"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_sync_existing_employee_updates_not_duplicates(client, admin_token, sample_employee, mock_hrs_client_success):
    """Test syncing existing employee updates data, doesn't create duplicate"""

    # Count employees before
    search_before = await client.get(
        "/api/employees/search",
        params={"department_code": "7410"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    count_before = len(search_before.json()["items"])

    # Sync same employee with updated data
    updated_hrs_data = {
        **mock_hrs_client_success,
        "job_title": "Updated Title",
        "salary": "8,500,000"
    }

    with patch('app.services.employee_service.hrs_client.get_employee_info') as mock_get:
        mock_get.return_value = updated_hrs_data

        sync_resp = await client.post(
            "/api/employees/sync",
            json={"emp_id": 6204, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert sync_resp.status_code == status.HTTP_200_OK
        synced_emp = sync_resp.json()
        assert synced_emp["id"] == "VNW0006204"
        assert synced_emp["job_title"] == "Updated Title"
        assert synced_emp["salary"] == 8500000

    # Count employees after - should be same (no duplicate)
    search_after = await client.get(
        "/api/employees/search",
        params={"department_code": "7410"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    count_after = len(search_after.json()["items"])
    assert count_after == count_before  # No new employee created


@pytest.mark.asyncio
@pytest.mark.integration
async def test_multiple_syncs_from_different_sources(client, admin_token, mock_hrs_client_success, mock_covid_client_success):
    """Test sync from HRS then COVID merges data correctly"""

    # 1. Sync from HRS first
    with patch('app.services.employee_service.hrs_client.get_employee_info') as mock_hrs:
        mock_hrs.return_value = mock_hrs_client_success

        hrs_resp = await client.post(
            "/api/employees/sync",
            json={"emp_id": 6204, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert hrs_resp.status_code == status.HTTP_200_OK
        hrs_data = hrs_resp.json()
        assert hrs_data["dept"] == "冶金技術部"  # From HRS
        assert hrs_data.get("identity_number") is None  # Not in HRS

    # 2. Sync from COVID (adds identity_number, nationality)
    with patch('app.services.employee_service.covid_client.get_user_info') as mock_covid:
        mock_covid.return_value = mock_covid_client_success

        covid_resp = await client.post(
            "/api/employees/sync",
            json={"emp_id": 6204, "source": "covid", "token": "test_token"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert covid_resp.status_code == status.HTTP_200_OK
        covid_data = covid_resp.json()
        assert covid_data["identity_number"] == "044090004970"  # From COVID
        assert covid_data["nationality"] == "VN"  # From COVID
        assert covid_data["dept"] == "冶金技術部"  # Still from HRS (not overwritten)

    # 3. Get final merged employee
    get_resp = await client.get(
        "/api/employees/VNW0006204",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert get_resp.status_code == status.HTTP_200_OK
    final_emp = get_resp.json()

    # Should have data from both sources
    assert final_emp["dept"] == "冶金技術部"  # From HRS
    assert final_emp["job_title"] == "工程師"  # From HRS
    assert final_emp["identity_number"] == "044090004970"  # From COVID
    assert final_emp["nationality"] == "VN"  # From COVID


@pytest.mark.asyncio
@pytest.mark.integration
async def test_search_pagination_workflow(client, admin_token, mock_hrs_client_success):
    """Test search pagination with multiple employees"""

    # Bulk sync to create multiple employees
    with patch('app.services.employee_service.hrs_client.bulk_get_employees') as mock_bulk:
        # Create 5 employees
        mock_bulk.return_value = [
            {**mock_hrs_client_success, "employee_id": f"VNW000620{i}"}
            for i in range(5)
        ]

        sync_resp = await client.post(
            "/api/employees/bulk-sync",
            json={"from_id": 6200, "to_id": 6204, "source": "hrs"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert sync_resp.status_code == status.HTTP_200_OK

    # Search page 1 (limit 2)
    page1_resp = await client.get(
        "/api/employees/search",
        params={"skip": 0, "limit": 2, "department_code": "7410"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert page1_resp.status_code == status.HTTP_200_OK
    page1_data = page1_resp.json()
    assert len(page1_data["items"]) <= 2
    assert page1_data["skip"] == 0
    assert page1_data["limit"] == 2

    # Search page 2 (skip 2, limit 2)
    page2_resp = await client.get(
        "/api/employees/search",
        params={"skip": 2, "limit": 2, "department_code": "7410"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert page2_resp.status_code == status.HTTP_200_OK
    page2_data = page2_resp.json()
    assert page2_data["skip"] == 2
    assert page2_data["limit"] == 2

    # Ensure different employees on different pages
    if len(page1_data["items"]) > 0 and len(page2_data["items"]) > 0:
        page1_ids = {emp["id"] for emp in page1_data["items"]}
        page2_ids = {emp["id"] for emp in page2_data["items"]}
        assert len(page1_ids & page2_ids) == 0  # No overlap
