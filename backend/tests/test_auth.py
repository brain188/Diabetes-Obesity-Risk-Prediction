"""
Authentication endpoint tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.healthcare_worker import HealthcareWorker
from app.core.security import verify_password
from tests.conftest import TestingSessionLocal


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_success(self, test_client: TestClient, test_register_data: dict):
        """Test successful user registration."""
        response = test_client.post("/api/v1/auth/register", json=test_register_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["full_name"] == test_register_data["full_name"]
        assert data["email"] == test_register_data["email"]
        assert data["clinic_name"] == test_register_data["clinic_name"]
        assert "worker_id" in data
        assert data["is_active"] is True
    
    def test_register_duplicate_email(
        self,
        test_client: TestClient,
        test_register_data: dict,
        test_user: HealthcareWorker
    ):
        """Test registration with duplicate email."""
        test_register_data["email"] = test_user.email
        response = test_client.post("/api/v1/auth/register", json=test_register_data)
        assert response.status_code == 409
        assert "DUPLICATE_RESOURCE" in response.json()["error"]
    
    def test_register_invalid_password(self, test_client: TestClient):
        """Test registration with invalid password."""
        data = {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "123",  # Too short
            "clinic_name": "Test Clinic",
        }
        response = test_client.post("/api/v1/auth/register", json=data)
        assert response.status_code == 422
    
    def test_login_success(
        self,
        test_client: TestClient,
        test_login_data: dict,
        test_user: HealthcareWorker
    ):
        """Test successful login."""
        response = test_client.post("/api/v1/auth/login", json=test_login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["email"] == test_user.email
        assert data["user"]["full_name"] == test_user.full_name
    
    def test_login_invalid_credentials(
        self,
        test_client: TestClient,
        test_invalid_login_data: dict
    ):
        """Test login with invalid credentials."""
        response = test_client.post("/api/v1/auth/login", json=test_invalid_login_data)
        assert response.status_code == 401
        assert "AUTHENTICATION_ERROR" in response.json()["error"]
    
    @pytest.mark.asyncio
    async def test_login_inactive_user(
        self,
        test_client: TestClient,
        test_login_data: dict,
        test_session: AsyncSession,
        test_user: HealthcareWorker
    ):
        """Test login with inactive user account."""
        # Deactivate user
        test_user.is_active = False
        await test_session.commit()
        
        response = test_client.post("/api/v1/auth/login", json=test_login_data)
        assert response.status_code == 401
        assert "AUTHENTICATION_ERROR" in response.json()["error"]
    
    def test_get_profile(
        self,
        test_client: TestClient,
        test_user: HealthcareWorker,
        test_auth_headers: dict
    ):
        """Test getting user profile."""
        response = test_client.get(
            "/api/v1/auth/profile",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == test_user.email
        assert data["full_name"] == test_user.full_name
        assert data["worker_id"] == test_user.worker_id
        assert data["clinic_name"] == test_user.clinic_name
    
    def test_get_profile_unauthenticated(self, test_client: TestClient):
        """Test getting profile without authentication."""
        response = test_client.get("/api/v1/auth/profile")
        assert response.status_code == 401
    
    def test_logout(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_user: HealthcareWorker
    ):
        """Test logout."""
        response = test_client.post(
            "/api/v1/auth/logout",
            headers=test_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    @pytest.mark.asyncio
    async def test_change_password(
        self,
        test_client: TestClient,
        test_auth_headers: dict,
        test_user: HealthcareWorker,
        test_session: AsyncSession
    ):
        """Test changing password."""
        data = {
            "current_password": "TestPassword123!",
            "new_password": "NewSecurePass456!",
        }
        response = test_client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=test_auth_headers
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        
        # Verify password was changed using a fresh session
        async with TestingSessionLocal() as fresh_session:
            from sqlalchemy import select
            from app.models.healthcare_worker import HealthcareWorker as HW
            result = await fresh_session.execute(
                select(HW).where(HW.worker_id == test_user.worker_id)
            )
            updated_worker = result.scalar_one()
        assert verify_password("NewSecurePass456!", updated_worker.password_hash) is True
    
    def test_change_password_wrong_current(
        self,
        test_client: TestClient,
        test_auth_headers: dict
    ):
        """Test changing password with wrong current password."""
        data = {
            "current_password": "WrongPassword!",
            "new_password": "NewSecurePass456!",
        }
        response = test_client.post(
            "/api/v1/auth/change-password",
            json=data,
            headers=test_auth_headers
        )
        assert response.status_code == 401
        assert "AUTHENTICATION_ERROR" in response.json()["error"]
    
    def test_request_password_reset(
        self,
        test_client: TestClient,
        test_user: HealthcareWorker
    ):
        """Test requesting password reset."""
        data = {"email": test_user.email}
        response = test_client.post(
            "/api/v1/auth/password-reset/request",
            json=data
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
    
    def test_request_password_reset_nonexistent_email(
        self,
        test_client: TestClient
    ):
        """Test password reset request for nonexistent email."""
        data = {"email": "nonexistent@example.com"}
        response = test_client.post(
            "/api/v1/auth/password-reset/request",
            json=data
        )
        # Should return success for security (don't reveal if email exists)
        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_health_check(self, test_client: TestClient):
        """Test health check endpoint."""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "environment" in data

    def test_refresh_token_success(
        self,
        test_client: TestClient,
        test_login_data: dict,
        test_user: HealthcareWorker
    ):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = test_client.post("/api/v1/auth/login", json=test_login_data)
        assert login_response.status_code == 200
        refresh_token = login_response.json()["refresh_token"]
        
        # Then refresh
        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
    
    def test_refresh_token_invalid(
        self,
        test_client: TestClient
    ):
        """Test token refresh with invalid token."""
        response = test_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_token"}
        )
        assert response.status_code == 401
        assert "AUTHENTICATION_ERROR" in response.json()["error"]