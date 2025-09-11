#!/usr/bin/env python3
"""
Minimal test to isolate authentication issue
"""

import asyncio
from services.auth_service import auth_service
from schemas.auth_schema import UserRegisterRequest, UserLoginRequest

async def test_auth_service_directly():
    """Test auth service methods directly"""
    print("🔧 Testing Auth Service Directly\n")
    
    try:
        # Test 1: Basic service initialization
        print("1️⃣ Testing service initialization...")
        print(f"✅ Auth service initialized: {type(auth_service)}")
        
        # Test 2: Try to register a user
        print("\n2️⃣ Testing user registration...")
        user_data = UserRegisterRequest(
            email="newuser@example.com",
            password="TestPass123",
            confirm_password="TestPass123"
        )
        
        print(f"📝 Attempting to register: {user_data.email}")
        result = await auth_service.register_user(user_data)
        print(f"✅ Registration result: {result}")
        
    except Exception as e:
        print(f"❌ Error during registration: {e}")
        print(f"   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        
        # Try to get more details about the error
        import traceback
        print(f"\n🔍 Full traceback:")
        traceback.print_exc()

async def main():
    """Main test function"""
    print("🚀 Starting Direct Auth Service Test\n")
    await test_auth_service_directly()

if __name__ == "__main__":
    asyncio.run(main())
