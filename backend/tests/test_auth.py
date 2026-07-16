import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.modules.auth.models import User, RefreshToken, EmailVerificationToken, PasswordResetToken
from src.modules.auth.services import AuthService


@pytest.mark.asyncio
async def test_auth_signup_flow(client: TestClient, db_session: AsyncSession):
    """
    Test user signup and verify database insertion.
    """
    signup_data = {
        "email": "tester@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    # 1. API Call
    response = client.post("/api/v1/auth/signup", json=signup_data)
    assert response.status_code == 201
    
    # 2. Database validation
    query = select(User).where(User.email == "tester@datasense.ai")
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.first_name == "Test"
    assert user.is_verified is False  # Email starts unverified


@pytest.mark.asyncio
async def test_auth_login_flow(client: TestClient, db_session: AsyncSession):
    """
    Test user login with valid credentials, verifying JWT token response and HttpOnly cookie payload.
    """
    # Create user first
    signup_data = {
        "email": "login_tester@datasense.ai",
        "password": "SecurePassword123",
        "first_name": "Login",
        "last_name": "User"
    }
    client.post("/api/v1/auth/signup", json=signup_data)

    # Attempt login
    login_data = {
        "email": "login_tester@datasense.ai",
        "password": "SecurePassword123"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login_tester@datasense.ai"

    # Verify HTTPOnly refresh token cookie exists
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_auth_login_invalid_credentials(client: TestClient, db_session: AsyncSession):
    """
    Test login rejection on incorrect password.
    """
    login_data = {
        "email": "login_tester@datasense.ai",
        "password": "WrongPassword!!!"
    }
    response = client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 401
    assert "access_token" not in response.json()


@pytest.mark.asyncio
async def test_email_verification_flow(client: TestClient, db_session: AsyncSession):
    """
    Test complete email verification workflow using generated token values.
    """
    # Create user
    query = select(User).where(User.email == "tester@datasense.ai")
    result = await db_session.execute(query)
    user = result.scalar_one()

    # Generate verification token
    token = await AuthService.generate_email_verification(db_session, user.id)

    # API call to verify
    response = client.get(f"/api/v1/auth/verify-email?token={token}")
    assert response.status_code == 200
    assert response.json()["message"] == "Email verified successfully."

    # Validate db state
    await db_session.refresh(user)
    assert user.is_verified is True


@pytest.mark.asyncio
async def test_password_reset_flow(client: TestClient, db_session: AsyncSession):
    """
    Test forgot password trigger and reset execution.
    """
    # Trigger forgot password
    forgot_data = {"email": "tester@datasense.ai"}
    response = client.post("/api/v1/auth/forgot-password", json=forgot_data)
    assert response.status_code == 200

    # Get reset token directly from database (simulating reading the email link)
    query = select(User).where(User.email == "tester@datasense.ai")
    result = await db_session.execute(query)
    user = result.scalar_one()
    
    token_query = select(PasswordResetToken).where(PasswordResetToken.user_id == user.id)
    token_result = await db_session.execute(token_query)
    reset_token = token_result.scalar_one().token

    # Reset password
    reset_data = {
        "token": reset_token,
        "new_password": "NewSecurePassword123"
    }
    response = client.post("/api/v1/auth/reset-password", json=reset_data)
    assert response.status_code == 200

    # Verify user can log in with new password
    login_data = {
        "email": "tester@datasense.ai",
        "password": "NewSecurePassword123"
    }
    login_response = client.post("/api/v1/auth/login", json=login_data)
    assert login_response.status_code == 200
