#!/usr/bin/env python3
"""
Test script for the authentication UI
This script tests the basic functionality of the authentication system
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8001"
API_BASE = f"{BASE_URL}/api/v1"

def test_auth_endpoints():
    """Test all authentication endpoints"""
    print("🧪 Testing Authentication Endpoints")
    print("=" * 50)
    
    # Test health check
    print("\n1. Testing health check...")
    try:
        response = requests.get(f"{API_BASE}/auth/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    # Test registration
    print("\n2. Testing user registration...")
    test_email = f"test_{int(time.time())}@example.com"
    test_password = "testpassword123"
    
    registration_data = {
        "email": test_email,
        "password": test_password,
        "confirm_password": test_password
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/register",
            json=registration_data
        )
        
        if response.status_code == 201:
            print("✅ Registration successful")
            print(f"   User ID: {response.json().get('id')}")
            print(f"   Email: {response.json().get('email')}")
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Registration error: {e}")
    
    # Test login
    print("\n3. Testing user login...")
    login_data = {
        "email": test_email,
        "password": test_password
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=login_data
        )
        
        if response.status_code == 200:
            print("✅ Login successful")
            login_response = response.json()
            access_token = login_response.get('access_token')
            refresh_token = login_response.get('refresh_token')
            print(f"   Access token: {access_token[:20]}...")
            print(f"   Refresh token: {refresh_token[:20]}...")
            print(f"   User email: {login_response.get('user', {}).get('email')}")
            
            # Test token validation
            print("\n4. Testing token validation...")
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(f"{API_BASE}/auth/validate", headers=headers)
            
            if response.status_code == 200:
                print("✅ Token validation successful")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Token validation failed: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Test user profile
            print("\n5. Testing user profile...")
            response = requests.get(f"{API_BASE}/auth/profile", headers=headers)
            
            if response.status_code == 200:
                print("✅ Profile retrieval successful")
                print(f"   Profile: {response.json()}")
            else:
                print(f"❌ Profile retrieval failed: {response.status_code}")
                print(f"   Response: {response.text}")
            
            # Test logout
            print("\n6. Testing logout...")
            logout_data = {"refresh_token": refresh_token}
            response = requests.post(f"{API_BASE}/auth/logout", json=logout_data)
            
            if response.status_code == 200:
                print("✅ Logout successful")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Logout failed: {response.status_code}")
                print(f"   Response: {response.text}")
                
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"❌ Login error: {e}")
    
    # Test invalid login
    print("\n7. Testing invalid login...")
    invalid_login_data = {
        "email": test_email,
        "password": "wrongpassword"
    }
    
    try:
        response = requests.post(
            f"{API_BASE}/auth/login",
            json=invalid_login_data
        )
        
        if response.status_code == 401:
            print("✅ Invalid login correctly rejected")
        else:
            print(f"❌ Invalid login should have been rejected: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid login test error: {e}")

def test_frontend_routes():
    """Test frontend routes"""
    print("\n🌐 Testing Frontend Routes")
    print("=" * 50)
    
    routes = [
        ("/", "Root endpoint"),
        ("/frontend", "Main application"),
        ("/auth", "Authentication page"),
        ("/health", "Health check")
    ]
    
    for route, description in routes:
        print(f"\nTesting {description} ({route})...")
        try:
            response = requests.get(f"{BASE_URL}{route}")
            if response.status_code == 200:
                print(f"✅ {description} accessible")
                if route == "/auth":
                    print("   Authentication page loaded successfully")
            else:
                print(f"❌ {description} failed: {response.status_code}")
        except Exception as e:
            print(f"❌ {description} error: {e}")

def main():
    """Main test function"""
    print("🚀 Starting Authentication System Tests")
    print("Make sure the server is running on http://localhost:8001")
    print("=" * 60)
    
    try:
        # Test frontend routes first
        test_frontend_routes()
        
        # Test authentication endpoints
        test_auth_endpoints()
        
        print("\n" + "=" * 60)
        print("🎉 All tests completed!")
        print("\nTo test the UI manually:")
        print("1. Open http://localhost:8001/auth in your browser")
        print("2. Try creating an account and logging in")
        print("3. Test the main application at http://localhost:8001/frontend")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Test suite error: {e}")

if __name__ == "__main__":
    main()
