import pytest
import pytest_asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.jwt_handler import create_access_token
from app.models.user import User, Base
from app.models.employee import Employee


# Test Database Configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine with in-memory SQLite"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_db_engine):
    """Create test database session"""
    async_session = sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


# User Fixtures

@pytest.fixture
def new_user_data():
    """Sample data for creating a new user"""
    return {
        "social_id": "new_user_123",
        "provider": "google",
        "email": "newuser@example.com",
        "full_name": "New User",
        "avatar": "https://example.com/avatar.jpg"
    }


@pytest.fixture
def existing_user_data():
    """Sample data for an existing user"""
    return {
        "id": 1,
        "social_id": "existing_user_456",
        "provider": "github",
        "email": "existing@example.com",
        "full_name": "Existing User",
        "avatar": "https://example.com/avatar2.jpg",
        "role": "user",
        "localId": "VNW001",
        "is_active": True,
        "is_verified": False,
        "created_at": datetime.utcnow(),
        "last_login": datetime.utcnow()
    }


@pytest_asyncio.fixture
async def admin_user(test_db_session):
    """Create an admin user in test database"""
    admin = User(
        social_id="admin_123",
        provider="google",
        email="admin@example.com",
        full_name="Admin User",
        avatar="https://example.com/admin.jpg",
        role="admin",
        localId="ADM001",
        is_active=True,
        is_verified=True
    )

    test_db_session.add(admin)
    await test_db_session.commit()
    await test_db_session.refresh(admin)

    return admin


@pytest_asyncio.fixture
async def regular_user(test_db_session):
    """Create a regular user in test database"""
    user = User(
        social_id="user_456",
        provider="github",
        email="user@example.com",
        full_name="Regular User",
        avatar="https://example.com/user.jpg",
        role="user",
        localId="VNW002",
        is_active=True,
        is_verified=False
    )

    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)

    return user


@pytest_asyncio.fixture
async def guest_user(test_db_session):
    """Create a guest user (no localId) in test database"""
    guest = User(
        social_id="guest_789",
        provider="google",
        email="guest@example.com",
        full_name="Guest User",
        avatar="https://example.com/guest.jpg",
        role="guest",
        localId=None,
        is_active=True,
        is_verified=False
    )

    test_db_session.add(guest)
    await test_db_session.commit()
    await test_db_session.refresh(guest)

    return guest


# JWT Token Fixtures

@pytest.fixture
def admin_token(admin_user):
    """Generate JWT token for admin user"""
    return create_access_token(
        user_id=str(admin_user.id),
        full_name=admin_user.full_name,
        role=admin_user.role,
        localId=admin_user.localId,
        provider=admin_user.provider,
        scope="access"
    )


@pytest.fixture
def user_token(regular_user):
    """Generate JWT token for regular user"""
    return create_access_token(
        user_id=str(regular_user.id),
        full_name=regular_user.full_name,
        role=regular_user.role,
        localId=regular_user.localId,
        provider=regular_user.provider,
        scope="access"
    )


@pytest.fixture
def guest_token(guest_user):
    """Generate JWT token for guest user"""
    return create_access_token(
        user_id=str(guest_user.id),
        full_name=guest_user.full_name,
        role=guest_user.role,
        localId=guest_user.localId,
        provider=guest_user.provider,
        scope="access"
    )


# Employee Fixtures

@pytest_asyncio.fixture
async def sample_employee(test_db_session):
    """Create a sample employee in test database"""
    employee = Employee(
        id="VNW0006204",
        name_tw="陳玉俊",
        name_en="Phan Anh Tuấn",
        department_code="7410",
        dept="冶金技術部",
        job_title="工程師",
        identity_number="044090004970"
    )

    test_db_session.add(employee)
    await test_db_session.commit()
    await test_db_session.refresh(employee)

    return employee


# Mock Fixtures

@pytest.fixture
def mock_db_session():
    """Mock database session for unit tests"""
    session = AsyncMock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    return session
