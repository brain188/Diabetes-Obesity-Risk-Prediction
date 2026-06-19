"""
Authentication endpoints.
"""

from fastapi import APIRouter, Depends, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_session
from app.core.dependencies import get_current_user_id, get_client_ip, get_request_metadata
from app.core.exceptions import AuthenticationError, DuplicateError
from app.core.logging import get_logger
from app.schemas.auth import (
    PasswordChangeRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    TokenRefreshRequest,
    TokenRefreshResponse,
    UserLoginRequest,
    UserLoginResponse,
    UserProfileResponse,
    UserRegisterRequest,
    UserRegisterResponse,
)
from app.schemas.common import SuccessResponse
from app.services.auth_service import AuthService

logger = get_logger(__name__)
router  = APIRouter()          # Creates a route group for authentication endpoints
security = HTTPBearer()        # Security scheme for Bearer token authentication


@router.post("/register", response_model=UserRegisterResponse,
             status_code=status.HTTP_201_CREATED)
async def register(
    request : UserRegisterRequest,                                      # User registration data from request body
    db      : AsyncSession = Depends(get_db_session),                  # Database session dependency
    client_ip: str         = Depends(get_client_ip),                   # Client IP address for audit logging
    metadata: dict         = Depends(get_request_metadata),            # Request metadata for logging
) -> UserRegisterResponse:
    """
    Register a new healthcare worker.
    
    Creates a new user account with email/password.
    All audit logging is handled inside the service layer.
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate registration logic to service layer
    result  = await service.register(
        full_name   = request.full_name,                               # User's full name
        email       = request.email,                                   # Unique email address
        password    = request.password,                                # Plain text password (will be hashed)
        clinic_name = request.clinic_name,                             # Optional clinic/facility name
        ip_address  = client_ip,                                       # Client IP for audit trail
        user_agent  = metadata.get("user_agent"),                      # User agent string for audit trail
    )
    
    logger.info("User registered: %s", request.email)                  # Log successful registration
    return UserRegisterResponse(**result)                              # Return response matching schema


@router.post("/login", response_model=UserLoginResponse)
async def login(
    request : UserLoginRequest,                                        # Login credentials from request body
    db      : AsyncSession = Depends(get_db_session),                  # Database session dependency
    client_ip: str         = Depends(get_client_ip),                   # Client IP address for audit logging
    metadata: dict         = Depends(get_request_metadata),            # Request metadata for logging
) -> UserLoginResponse:
    """
    Authenticate a healthcare worker.
    
    Validates credentials and returns access/refresh tokens.
    Audit logging is handled inside AuthService.login() — do NOT
    call audit_repo.log_login() here as well or every login gets logged twice.
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate login logic to service layer (includes audit logging)
    result  = await service.login(
        email      = request.email,                                    # User's email address
        password   = request.password,                                 # User's password
        ip_address = client_ip,                                        # Client IP for audit trail
        user_agent = metadata.get("user_agent"),                       # User agent string for audit trail
        request_id = metadata.get("request_id"),                       # Request correlation ID for tracing
    )
    
    logger.info("User logged in: %s", request.email)                   # Log successful login
    return UserLoginResponse(**result)                                 # Return token response


@router.post("/logout", response_model=SuccessResponse)
async def logout(
    db          : AsyncSession = Depends(get_db_session),              # Database session dependency
    current_user: str          = Depends(get_current_user_id),         # Currently authenticated user ID
    client_ip   : str          = Depends(get_client_ip),               # Client IP address for audit logging
    metadata    : dict         = Depends(get_request_metadata),        # Request metadata for logging
) -> SuccessResponse:
    """
    Log out the current user.
    
    Revokes the user's refresh token and logs the logout event.
    Client should discard the access token after logout.
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate logout logic to service layer (includes token revocation and audit logging)
    await service.logout(
        worker_id  = current_user,                                     # Authenticated user's worker ID
        ip_address = client_ip,                                        # Client IP for audit trail
        request_id = metadata.get("request_id"),                       # Request correlation ID for tracing
    )
    
    return SuccessResponse(success=True, message="Logout successful")   # Return success response


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request  : TokenRefreshRequest,                                    # Refresh token from request body
    db       : AsyncSession = Depends(get_db_session),                 # Database session dependency
    client_ip: str          = Depends(get_client_ip),                  # Client IP address for audit logging
) -> TokenRefreshResponse:
    """
    Refresh the access token using a refresh token.
    
    Implements refresh token rotation for security:
    - Validates the refresh token against stored hash
    - Issues a new access token
    - Issues a new refresh token (rotation)
    - Revokes the old refresh token
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate token refresh logic to service layer
    result  = await service.refresh_token(
        refresh_token = request.refresh_token,                         # Refresh token to validate
        ip_address    = client_ip,                                     # Client IP for audit trail
    )
    
    return TokenRefreshResponse(**result)                              # Return new token pair


@router.post("/password-reset/request", response_model=SuccessResponse)
async def request_password_reset(
    request  : PasswordResetRequest,                                   # Email address for password reset
    db       : AsyncSession = Depends(get_db_session),                 # Database session dependency
    client_ip: str          = Depends(get_client_ip),                  # Client IP address for audit logging
) -> SuccessResponse:
    """
    Request a password reset.
    
    Sends a password reset email with a reset token.
    Always returns success for security (doesn't reveal if email exists).
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate password reset request logic to service layer
    await service.request_password_reset(email=request.email, ip_address=client_ip)
    
    return SuccessResponse(
        success=True,
        message="Password reset instructions sent if account exists",  # Generic message for security
    )


@router.post("/password-reset/confirm", response_model=SuccessResponse)
async def confirm_password_reset(
    request  : PasswordResetConfirmRequest,                            # Reset token and new password
    db       : AsyncSession = Depends(get_db_session),                 # Database session dependency
    client_ip: str          = Depends(get_client_ip),                  # Client IP address for audit logging
) -> SuccessResponse:
    """
    Confirm password reset with token.
    
    Validates the reset token and updates the password.
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate password reset confirmation logic to service layer
    success = await service.reset_password(
        token        = request.token,                                  # Reset token from email
        new_password = request.new_password,                           # New password to set
        ip_address   = client_ip,                                      # Client IP for audit trail
    )
    
    if not success:
        raise AuthenticationError("Password reset failed.")            # Raise error if reset fails
    
    return SuccessResponse(success=True, message="Password reset successful")


@router.post("/change-password", response_model=SuccessResponse)
async def change_password(
    request     : PasswordChangeRequest,                                # Current and new password
    db          : AsyncSession = Depends(get_db_session),               # Database session dependency
    current_user: str          = Depends(get_current_user_id),          # Currently authenticated user ID
    client_ip   : str          = Depends(get_client_ip),                # Client IP address for audit logging
) -> SuccessResponse:
    """
    Change password for authenticated user.
    
    Requires current password verification before updating to new password.
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate password change logic to service layer
    await service.change_password(
        worker_id        = current_user,                               # Authenticated user's worker ID
        current_password = request.current_password,                   # Current password for verification
        new_password     = request.new_password,                       # New password to set
        ip_address       = client_ip,                                  # Client IP for audit trail
    )
    
    return SuccessResponse(success=True, message="Password changed successfully")


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    db          : AsyncSession = Depends(get_db_session),              # Database session dependency
    current_user: str          = Depends(get_current_user_id),         # Currently authenticated user ID
) -> UserProfileResponse:
    """
    Get the current user's profile information.
    
    Returns user details including name, email, clinic, and account status.
    Requires authentication.
    """
    service = AuthService(db)                                           # Initialize auth service with database session
    
    # Delegate profile retrieval logic to service layer
    profile = await service.get_user_profile(current_user)             # Get user profile data
    
    return UserProfileResponse(**profile)                              # Return profile response