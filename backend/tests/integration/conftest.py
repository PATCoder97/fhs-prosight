import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.database.session import get_db
from tests.conftest import test_db_session, admin_token, user_token, sample_employee


@pytest_asyncio.fixture
async def client(test_db_session):
    """Create test client with overridden database dependency"""
    
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_hrs_client_success():
    """Mock HRS client with successful response"""
    mock_data = {
        "employee_id": "VNW0006204",
        "name_tw": "陳玉俊",
        "name_en": "PHAN ANH TUẤN",
        "dob": "19970420",
        "start_date": "20190805",
        "dept": "冶金技術部",
        "department_code": "7410",
        "job_title": "工程師",
        "job_type": "正式",
        "salary": "7,205,600",
        "address1": "台灣",
        "phone1": "0123456789"
    }
    return mock_data


@pytest.fixture
def mock_covid_client_success():
    """Mock COVID client with successful response"""
    mock_data = {
        "employee_id": "VNW0006204",
        "name_tw": "陳玉俊",
        "department_code": "7410",
        "phone1": "0123456789",
        "sex": "M",
        "identity_number": "044090004970",
        "dob": "1997-04-20",
        "nationality": "VN"
    }
    return mock_data
