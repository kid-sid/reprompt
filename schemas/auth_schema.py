from pydantic import BaseModel, EmailStr, Field, model_validator
from datetime import datetime


# User Registration
class UserRegisterRequest(BaseModel):
    """Simple user registration with email and password"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=6, description="User's password (min 6 characters)")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @model_validator(mode='after')
    def passwords_match(self) -> 'UserRegisterRequest':
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self


class UserRegisterResponse(BaseModel):
    """User registration response"""
    id: str = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    message: str = Field(..., description="Registration success message")

# User Login
class UserLoginRequest(BaseModel):
    """User login with email and password"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")


class UserLoginResponse(BaseModel):
    """User login response with tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    user: 'UserProfile' = Field(..., description="User profile information")

# User Profile
class UserProfile(BaseModel):
    """Simple user profile"""
    id: str = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    created_at: datetime = Field(..., description="Account creation timestamp")

# Token Management
class TokenRefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str = Field(..., description="JWT refresh token")

class TokenRefreshResponse(BaseModel):
    """Token refresh response"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")

# Logout
class LogoutRequest(BaseModel):
    """Logout request"""
    refresh_token: str = Field(..., description="JWT refresh token to invalidate")

class LogoutResponse(BaseModel):
    """Logout response"""
    message: str = Field(..., description="Logout success message")

# Error Response
class AuthError(Exception):
    """Authentication error exception"""
    def __init__(self, error: str, message: str):
        self.error = error
        self.message = message
        super().__init__(self.message)

# Update forward references
UserLoginResponse.model_rebuild()
