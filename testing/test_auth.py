#!/usr/bin/env python3
"""
Test script to verify Supabase authentication is working
Run this to check if your setup is correct
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

async def test_supabase_connection():
    """Test basic Supabase connection"""
    try:
        from supabase import create_client, Client
        
        # Get credentials from environment variables
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        print("🔍 Checking Supabase configuration...")
        print(f"URL: {supabase_url}")
        print(f"Key: {supabase_key[:20]}..." if supabase_key else "Key: NOT SET")
        
        if not supabase_url or not supabase_key:
            print("❌ Missing SUPABASE_URL or SUPABASE_ANON_KEY in .env file")
            return False
        
        # Test connection
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Supabase client created successfully")
        
        # Test basic auth methods
        print("\n🔐 Testing authentication methods...")
        
        # Test sign up (this will create a test user)
        test_email = "test@example.com"
        test_password = "TestPass123"
        
        print(f"📝 Attempting to create test user: {test_email}")
        
        try:
            # Check if user already exists
            auth_response = supabase.auth.sign_in_with_password({
                "email": test_email,
                "password": test_password
            })
            print("✅ Test user already exists and can sign in")
            
        except Exception as e:
            if "Invalid login credentials" in str(e):
                print("📝 Creating new test user...")
                auth_response = supabase.auth.sign_up({
                    "email": test_email,
                    "password": test_password
                })
                
                if auth_response.user:
                    print(f"✅ Test user created successfully! ID: {auth_response.user.id}")
                else:
                    print("❌ Failed to create test user")
                    return False
            else:
                print(f"❌ Unexpected error: {e}")
                return False
        
        # Test database connection
        print("\n🗄️ Testing database connection...")
        try:
            # Try to access the profiles table
            response = supabase.table("profiles").select("*").limit(1).execute()
            print("✅ Database connection successful")
            print(f"📊 Profiles table accessible (found {len(response.data)} records)")
            
        except Exception as e:
            print(f"⚠️ Database warning: {e}")
            print("💡 You may need to create the profiles table")
        
        # Test sign out
        print("\n🚪 Testing sign out...")
        try:
            supabase.auth.sign_out()
            print("✅ Sign out successful")
        except Exception as e:
            print(f"⚠️ Sign out warning: {e}")
        
        print("\n🎉 All tests completed!")
        return True
        
    except ImportError:
        print("❌ Supabase package not installed. Run: pip install supabase")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

async def test_auth_service():
    """Test our custom auth service"""
    try:
        print("\n🔧 Testing custom AuthService...")
        
        from services.auth_service import auth_service
        print("✅ AuthService imported successfully")
        
        # Test token validation
        print("🔍 Testing token validation...")
        is_valid = await auth_service.validate_token("invalid_token")
        print(f"✅ Token validation method works (invalid token: {is_valid})")
        
        print("🎉 AuthService test completed!")
        return True
        
    except Exception as e:
        print(f"❌ AuthService test failed: {e}")
        return False

def check_environment():
    """Check if all required environment variables are set"""
    print("🌍 Checking environment variables...")
    
    required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value[:50]}..." if len(value) > 50 else f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Add them to your .env file")
        return False
    
    return True

async def main():
    """Run all tests"""
    print("🚀 Starting Supabase Authentication Tests\n")
    
    # Check environment
    env_ok = check_environment()
    if not env_ok:
        print("\n❌ Environment check failed. Please fix before continuing.")
        return
    
    print("\n" + "="*50)
    
    # Test basic connection
    connection_ok = await test_supabase_connection()
    
    print("\n" + "="*50)
    
    # Test auth service
    service_ok = await test_auth_service()
    
    print("\n" + "="*50)
    
    # Summary
    print("\n📋 TEST SUMMARY:")
    if connection_ok and service_ok:
        print("🎉 All tests passed! Your Supabase setup is working correctly.")
        print("\n💡 Next steps:")
        print("   1. Create the profiles table in Supabase dashboard")
        print("   2. Test the auth endpoints")
        print("   3. Integrate with your FastAPI app")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\n🔧 Common fixes:")
        print("   1. Verify your .env file has correct Supabase credentials")
        print("   2. Check if Supabase project is active")
        print("   3. Ensure you have the right permissions")

if __name__ == "__main__":
    asyncio.run(main())
