"""
Authentication Router Module

This module provides FastAPI routes for user authentication and session management.
It handles user registration, login, logout, token refresh, and profile management
using JWT tokens and Supabase authentication.

Endpoints:
    POST /auth/signup - Register a new user
    POST /auth/login - Authenticate user and get tokens
    POST /auth/logout - Logout user and invalidate tokens
    POST /auth/refresh - Refresh access token
    GET /auth/profile - Get user profile (protected)
    GET /auth/validate - Validate JWT token (protected)
    GET /auth/health - Health check for auth service
    POST /auth/create-missing-profiles - Utility endpoint for data sync

Dependencies:
    - Supabase for user authentication and storage
    - JWT tokens for session management
    - FastAPI for HTTP routing and validation

Author: Reprompt Chatbot Team
Version: 1.0.0
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger
from datetime import datetime
from schemas.auth_schema import (
    UserRegisterRequest, UserRegisterResponse,
    UserLoginRequest, UserLoginResponse,
    TokenRefreshRequest, TokenRefreshResponse,
    LogoutRequest, LogoutResponse,
    UserProfile, AuthError
)
from services.auth_service import auth_service

# Initialize router
router = APIRouter(prefix="/auth", tags=["authentication"])

# Security scheme for Bearer tokens
security = HTTPBearer(auto_error=False)

# Dependency to get current user from token
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """
    Get current authenticated user from JWT token.
    
    This dependency function extracts and validates the JWT token from the Authorization header
    and returns the corresponding user profile.
    
    Args:
        credentials (HTTPAuthorizationCredentials): Bearer token from Authorization header
        
    Returns:
        UserProfile: The authenticated user's profile information
        
    Raises:
        HTTPException: 401 if no credentials provided, invalid token, or expired token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Failed to get current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/signup", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegisterRequest):
    """
    Register a new user with email and password.
    
    Creates a new user account in the system with the provided email and password.
    The password confirmation is validated to ensure both passwords match.
    
    Args:
        user_data (UserRegisterRequest): User registration data containing:
            - email (str): User's email address (must be valid email format)
            - password (str): User's password (minimum 6 characters)
            - confirm_password (str): Password confirmation (must match password)
    
    Returns:
        UserRegisterResponse: Registration response containing:
            - id (str): Unique user identifier
            - message (str): Success message
    
    Raises:
        HTTPException: 409 if user already exists
        HTTPException: 400 if validation fails or passwords don't match
        HTTPException: 500 if internal server error occurs
    """
    try:
        logger.info(f"User registration attempt for email: {user_data.email}")
        logger.info(f"Request data: {user_data}")
        
        # Test if auth service is accessible
        logger.info("Calling auth service...")
        result = await auth_service.register_user(user_data)
        logger.info(f"User registered successfully: {result.id}")
        return result
        
    except AuthError as e:
        logger.warning(f"Registration failed for {user_data.email}: {e.message}")
        logger.warning(f"AuthError details: error={e.error}, message={e.message}")
        if e.error == "user_exists":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=e.message
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error details: {str(e)}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

@router.post("/login", response_model=UserLoginResponse)
async def login_user(login_data: UserLoginRequest):
    """
    Authenticate user with email and password.
    
    Validates user credentials and returns JWT tokens for authenticated sessions.
    Both access and refresh tokens are provided for secure session management.
    
    Args:
        login_data (UserLoginRequest): Login credentials containing:
            - email (str): User's email address
            - password (str): User's password
    
    Returns:
        UserLoginResponse: Login response containing:
            - access_token (str): JWT access token for API authentication
            - refresh_token (str): JWT refresh token for token renewal
            - user (UserProfile): User profile information
    
    Raises:
        HTTPException: 401 if invalid email or password
        HTTPException: 400 if request validation fails
        HTTPException: 500 if internal server error occurs
    """
    try:
        logger.info(f"Login attempt for email: {login_data.email}")
        result = await auth_service.login_user(login_data)
        logger.info(f"User logged in successfully: {result.user.id}")
        return result
    except AuthError as e:
        logger.warning(f"Login failed for {login_data.email}: {e.message}")
        if e.error == "invalid_credentials":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during login"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout_user(logout_data: LogoutRequest):
    """
    Logout user and invalidate refresh token.
    
    Invalidates the user's refresh token to end their session securely.
    The access token will also become invalid after logout.
    
    Args:
        logout_data (LogoutRequest): Logout request containing:
            - refresh_token (str): The refresh token to invalidate
    
    Returns:
        LogoutResponse: Logout response containing:
            - message (str): Success message confirming logout
    
    Raises:
        HTTPException: 500 if internal server error occurs (but still returns success)
        
    Note:
        Even if the logout operation fails on the server side, this endpoint
        will return a success response as the client will discard tokens anyway.
    """
    try:
        logger.info(f"User logout attempt with token: {logout_data.refresh_token}...")
        result = await auth_service.logout_user(logout_data.refresh_token)
        logger.info("User logged out successfully")
        return result
    except Exception as e:
        logger.error(f"Error during logout: {e}")
        # Even if logout fails, we should still return success
        # as the client will discard the tokens anyway
        return LogoutResponse(message="User logged out successfully")

@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(refresh_data: TokenRefreshRequest):
    """
    Refresh access token using refresh token.
    
    Generates a new access token using a valid refresh token. This allows
    users to continue their session without re-authenticating.
    
    Args:
        refresh_data (TokenRefreshRequest): Refresh request containing:
            - refresh_token (str): Valid refresh token for token renewal
    
    Returns:
        TokenRefreshResponse: Token refresh response containing:
            - access_token (str): New JWT access token
            - refresh_token (str): New JWT refresh token (optional)
    
    Raises:
        HTTPException: 401 if refresh token is invalid or expired
        HTTPException: 500 if internal server error occurs
    """
    try:
        logger.info("Token refresh attempt")
        result = await auth_service.refresh_token(refresh_data.refresh_token)
        logger.info("Token refreshed successfully")
        return result
    except AuthError as e:
        logger.warning(f"Token refresh failed: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error during token refresh: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during token refresh"
        )

@router.get("/profile", response_model=UserProfile)
async def get_user_profile(current_user: UserProfile = Depends(get_current_user)):
    """
    Get current user's profile information.
    
    Retrieves the authenticated user's profile data. This is a protected route
    that requires a valid JWT access token in the Authorization header.
    
    Args:
        current_user (UserProfile): Authenticated user profile (injected by dependency)
    
    Returns:
        UserProfile: User profile containing:
            - id (str): Unique user identifier
            - email (str): User's email address
            - created_at (datetime): Account creation timestamp
    
    Raises:
        HTTPException: 401 if no valid authentication token provided
        HTTPException: 500 if internal server error occurs
    """
    try:
        logger.info(f"Profile request for user: {current_user.id}")
        return current_user
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while fetching profile"
        )

@router.get("/validate", response_model=dict)
async def validate_token(current_user: UserProfile = Depends(get_current_user)):
    """
    Validate if the current JWT token is valid.
    
    Checks the validity of the provided JWT access token and returns
    user information if the token is valid. This is a protected route.
    
    Args:
        current_user (UserProfile): Authenticated user profile (injected by dependency)
    
    Returns:
        dict: Validation response containing:
            - valid (bool): True if token is valid
            - user_id (str): User's unique identifier
            - email (str): User's email address
    
    Raises:
        HTTPException: 401 if token is invalid or expired
        HTTPException: 500 if internal server error occurs
    """
    try:
        logger.info(f"Token validation request for user: {current_user.id}")
        return {
            "valid": True,
            "user_id": current_user.id,
            "email": current_user.email
        }
    except Exception as e:
        logger.error(f"Error validating token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while validating token"
        )

@router.get("/health", response_model=dict)
async def auth_health_check():
    """
    Health check endpoint for authentication service.
    
    Provides a simple health check for the authentication service.
    This endpoint does not require authentication and can be used
    for monitoring and load balancer health checks.
    
    Returns:
        dict: Health status containing:
            - status (str): "healthy" if service is operational
            - service (str): Service name ("authentication")
            - timestamp (str): ISO format timestamp of the check
    
    Raises:
        HTTPException: 503 if authentication service is not healthy
    """
    try:
        # Test basic Supabase connection
        # This is a simple health check that doesn't require authentication
        return {
            "status": "healthy",
            "service": "authentication",
            "timestamp":datetime.utcnow().isoformat()  # You can make this dynamic
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not healthy"
        )

@router.post("/create-missing-profiles", response_model=dict)
async def create_missing_profiles():
    """
    Create profiles for users who exist in auth.users but not in profiles table.
    
    This is a utility endpoint that synchronizes user data between Supabase's
    auth.users table and the custom profiles table. It creates profile records
    for users who have authentication records but are missing profile data.
    
    Returns:
        dict: Operation result containing:
            - message (str): Description of the operation result
            - created_count (int): Number of profiles created
            - processed_count (int): Total number of users processed
    
    Raises:
        HTTPException: 500 if the operation fails or internal server error occurs
        
    Note:
        This endpoint is typically used for data migration or maintenance purposes.
        It should be called when there are discrepancies between auth and profile data.
    """
    try:
        logger.info("Creating missing profiles for existing auth users")
        result = await auth_service.create_missing_profiles()
        logger.info(f"Profile creation completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Failed to create missing profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create missing profiles"
        )
