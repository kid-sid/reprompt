#!/usr/bin/env python3
"""
Direct test of auth_service.py methods
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.auth_service import AuthService
from schemas.auth_schema import UserRegisterRequest, UserLoginRequest

async def test_auth_service():
    """Test auth service methods directly"""
    print("🔧 Testing AuthService Directly")
    print("=" * 50)
    
    # Initialize auth service
    auth_service = AuthService()
    print("✅ AuthService initialized")
    
    # Test data
    timestamp = int(asyncio.get_event_loop().time())
    email = f"directtest{timestamp}@example.com"
    password = "TestPass123"
    
    print(f"\n📝 Testing with email: {email}")
    
    try:
        # Test 1: User Registration
        print("\n1️⃣ Testing User Registration...")
        register_data = UserRegisterRequest(
            email=email,
            password=password,
            confirm_password=password
        )
        
        register_result = await auth_service.register_user(register_data)
        print(f"✅ Registration successful: {register_result.id}")
        
        # Test 2: User Login
        print("\n2️⃣ Testing User Login...")
        login_data = UserLoginRequest(
            email=email,
            password=password
        )
        
        login_result = await auth_service.login_user(login_data)
        print(f"✅ Login successful: {login_result.user.id}")
        print(f"   Access Token: {login_result.access_token[:20]}...")
        print(f"   Refresh Token: {login_result.refresh_token}")
        
        # Test 3: Get Current User
        print("\n3️⃣ Testing Get Current User...")
        current_user = await auth_service.get_current_user(login_result.access_token)
        print(f"✅ Current user: {current_user.id}")
        
        # Test 4: Validate Token
        print("\n4️⃣ Testing Token Validation...")
        validation_result = await auth_service.validate_token(login_result.access_token)
        print(f"✅ Token validation: {validation_result}")
        
        # Test 5: Token Refresh
        print("\n5️⃣ Testing Token Refresh...")
        refresh_result = await auth_service.refresh_token(login_result.refresh_token)
        print(f"✅ Token refreshed: {refresh_result.access_token[:20]}...")
        
        # Test 6: User Logout
        print("\n6️⃣ Testing User Logout...")
        logout_result = await auth_service.logout_user(login_result.refresh_token)
        print(f"✅ Logout successful: {logout_result.message}")
        
        print("\n🎉 All auth service tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main function"""
    print("🚀 Starting AuthService Direct Test")
    print("Note: This tests the service methods directly, not through HTTP endpoints")
    print()
    
    # Run async test
    asyncio.run(test_auth_service())

if __name__ == "__main__":
    main()
