"""Tests for authentication endpoints."""
import pytest
from unittest.mock import MagicMock, patch


class TestAuthEndpoints:
    """Test authentication API endpoints."""

    def test_register_success(self, client, mock_supabase):
        """Test successful user registration."""
        # Mock no existing user
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        # Mock user creation
        mock_supabase.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new-user-id", "email": "new@example.com", "name": "New User"}]
        )
        
        response = client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "SecurePass123!",
            "name": "New User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_duplicate_email(self, client, mock_supabase):
        """Test registration with existing email."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "existing-id"}]
        )
        
        response = client.post("/api/v1/auth/register", json={
            "email": "existing@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_login_success(self, client, mock_supabase):
        """Test successful login."""
        from app.core.security import get_password_hash
        
        password_hash = get_password_hash("CorrectPassword123!")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "user-id",
                "email": "test@example.com",
                "password_hash": password_hash,
                "status": "active"
            }]
        )
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "CorrectPassword123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self, client, mock_supabase):
        """Test login with wrong password."""
        from app.core.security import get_password_hash
        
        password_hash = get_password_hash("CorrectPassword")
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{
                "id": "user-id",
                "email": "test@example.com",
                "password_hash": password_hash,
                "status": "active"
            }]
        )
        
        response = client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "WrongPassword"
        })
        
        assert response.status_code == 401

    def test_login_user_not_found(self, client, mock_supabase):
        """Test login with non-existent user."""
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        
        response = client.post("/api/v1/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "AnyPassword123!"
        })
        
        assert response.status_code == 401

    def test_refresh_token_success(self, client, mock_supabase, mock_user):
        """Test token refresh."""
        from app.core.security import create_refresh_token
        
        refresh_token = create_refresh_token({"sub": mock_user["id"], "email": mock_user["email"]})
        mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[mock_user]
        )
        
        response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_logout(self, client):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
