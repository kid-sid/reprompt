#!/usr/bin/env python3
"""
Test if all imports in auth_router are working
"""

def test_imports():
    print("🔍 Testing imports...")
    
    try:
        print("📦 Testing FastAPI imports...")
        from fastapi import APIRouter, HTTPException, Depends, status
        from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
        print("✅ FastAPI imports successful")
    except Exception as e:
        print(f"❌ FastAPI imports failed: {e}")
        return False
    
    try:
        print("📦 Testing loguru import...")
        from loguru import logger
        print("✅ Loguru import successful")
    except Exception as e:
        print(f"❌ Loguru import failed: {e}")
        return False
    
    try:
        print("📦 Testing auth schema imports...")
        from schemas.auth_schema import (
            UserRegisterRequest, UserRegisterResponse,
            UserLoginRequest, UserLoginResponse,
            TokenRefreshRequest, TokenRefreshResponse,
            LogoutRequest, LogoutResponse,
            UserProfile, AuthError
        )
        print("✅ Auth schema imports successful")
    except Exception as e:
        print(f"❌ Auth schema imports failed: {e}")
        return False
    
    try:
        print("📦 Testing auth service import...")
        from services.auth_service import auth_service
        print("✅ Auth service import successful")
    except Exception as e:
        print(f"❌ Auth service import failed: {e}")
        return False
    
    print("\n🎉 All imports successful!")
    return True

if __name__ == "__main__":
    test_imports()
