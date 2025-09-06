#!/usr/bin/env python3
"""
Test complete authentication flow
"""

import asyncio
import time
from services.auth_service import auth_service
from schemas.auth_schema import UserRegisterRequest, UserLoginRequest

async def test_complete_auth_flow():
    """Test the complete authentication flow"""
    print("🚀 Testing Complete Authentication Flow\n")
    
    # Create unique email using timestamp
    timestamp = int(time.time())
    unique_email = f"user{timestamp}@example.com"
    
    # Test 1: User Registration
    print("1️⃣ Testing User Registration...")
    user_data = UserRegisterRequest(
        email=unique_email,
        password="TestPass123",
        confirm_password="TestPass123"
    )
    
    try:
        registration = await auth_service.register_user(user_data)
        print(f"✅ Registration successful: {registration.id}")
        user_id = registration.id
        user_email = registration.email
    except Exception as e:
        print(f"❌ Registration failed: {e}")
        return
    
    print()
    
    # Test 2: User Login
    print("2️⃣ Testing User Login...")
    login_data = UserLoginRequest(
        email=user_email,
        password="TestPass123"
    )
    
    try:
        login = await auth_service.login_user(login_data)
        print(f"✅ Login successful")
        print(f"   Access Token: {login.access_token[:20]}...")
        print(f"   Refresh Token: {login.refresh_token[:20]}...")
        print(f"   User: {login.user.id}")
        
        access_token = login.access_token
        refresh_token = login.refresh_token
        
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    print()
    
    # Test 3: Get Current User (Protected Route)
    print("3️⃣ Testing Protected Route - Get Current User...")
    try:
        current_user = await auth_service.get_current_user(access_token)
        print(f"✅ Current user retrieved: {current_user.id}")
        print(f"   Email: {current_user.email}")
        print(f"   Created: {current_user.created_at}")
        
    except Exception as e:
        print(f"❌ Get current user failed: {e}")
        return
    
    print()
    
    # Test 4: Token Validation
    print("4️⃣ Testing Token Validation...")
    try:
        is_valid = await auth_service.validate_token(access_token)
        print(f"✅ Token validation: {is_valid}")
        
    except Exception as e:
        print(f"❌ Token validation failed: {e}")
        return
    
    print()
    
    # Test 5: Token Refresh
    print("5️⃣ Testing Token Refresh...")
    try:
        refresh_result = await auth_service.refresh_token(refresh_token)
        print(f"✅ Token refreshed successfully")
        print(f"   New Access Token: {refresh_result.access_token[:20]}...")
        
    except Exception as e:
        print(f"❌ Token refresh failed: {e}")
        return
    
    print()
    
    # Test 6: Logout
    print("6️⃣ Testing User Logout...")
    try:
        logout = await auth_service.logout_user(refresh_token)
        print(f"✅ Logout successful: {logout.message}")
        
    except Exception as e:
        print(f"❌ Logout failed: {e}")
        return
    
    print()
    print("🎉 Complete Authentication Flow Test Finished Successfully!")
    print(f"✅ User ID: {user_id}")
    print(f"✅ User Email: {user_email}")

async def main():
    """Main function"""
    print("🔧 Complete Authentication Flow Tester")
    print("=" * 50)
    await test_complete_auth_flow()

if __name__ == "__main__":
    asyncio.run(main())
