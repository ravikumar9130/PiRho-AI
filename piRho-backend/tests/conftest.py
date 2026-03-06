"""Pytest configuration and fixtures."""
import os
import pytest
from unittest.mock import MagicMock, patch

# Set test environment
os.environ["APP_ENV"] = "test"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_KEY"] = "test-key"
os.environ["SUPABASE_SERVICE_KEY"] = "test-service-key"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-minimum-32-characters"
# Valid Fernet key (generated with Fernet.generate_key())
os.environ["ENCRYPTION_KEY"] = "qnDf2zvZZmJ-rT9yc836RX5pO_oB0Tws6tsukSfE2Vs="

from fastapi.testclient import TestClient


@pytest.fixture
def mock_supabase():
    """Mock Supabase client."""
    mock = MagicMock()
    return mock


@pytest.fixture
def mock_user():
    """Sample user data."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "name": "Test User",
        "status": "active",
        "email_verified": True,
        "created_at": "2025-01-01T00:00:00Z"
    }


@pytest.fixture
def mock_tenant():
    """Sample tenant data."""
    return {
        "id": "test-tenant-id",
        "user_id": "test-user-id",
        "name": "Test Tenant",
        "plan": "free",
        "promo_code_used": None,
        "promo_applied_at": None,
        "created_at": "2025-01-01T00:00:00Z",
        "settings": {}
    }


@pytest.fixture
def client(mock_supabase):
    """Test client with mocked dependencies."""
    with patch("app.core.database.get_supabase_client", return_value=mock_supabase):
        from app.main import app
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def authenticated_client(mock_supabase, mock_user, mock_tenant):
    """Test client with auth already setup."""
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[mock_user]
    )
    mock_supabase.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
        data=mock_tenant
    )
    mock_supabase.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(data=[{}])
    
    with patch("app.core.database.get_supabase_client", return_value=mock_supabase):
        from app.main import app
        with TestClient(app) as test_client:
            yield test_client


@pytest.fixture
def auth_headers():
    """Generate valid auth headers for testing."""
    from app.core.security import create_access_token
    token = create_access_token({"sub": "test-user-id", "email": "test@example.com"})
    return {"Authorization": f"Bearer {token}"}
