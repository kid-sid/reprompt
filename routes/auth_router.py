from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

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
    """Get current authenticated user from JWT token"""
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

@router.post("/register", response_model=UserRegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserRegisterRequest):
    """Register a new user with email and password"""
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
    """Authenticate user with email and password"""
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
    """Logout user and invalidate refresh token"""
    try:
        logger.info("User logout attempt")
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
    """Refresh access token using refresh token"""
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
    """Get current user's profile (protected route)"""
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
    """Validate if the current token is valid (protected route)"""
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
    """Health check endpoint for authentication service"""
    try:
        # Test basic Supabase connection
        # This is a simple health check that doesn't require authentication
        return {
            "status": "healthy",
            "service": "authentication",
            "timestamp": "2024-01-01T00:00:00Z"  # You can make this dynamic
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service is not healthy"
        )
