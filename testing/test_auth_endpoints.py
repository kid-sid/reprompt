#!/usr/bin/env python3
"""
Test script for authentication endpoints
Run this to test your complete authentication flow
"""

import requests
import json
from typing import Optional

class HTTPAuthTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_prefix = "/api/v1/auth"
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        
    def _make_request(self, method: str, endpoint: str, data: dict = None, headers: dict = None) -> dict:
        """Make HTTP request to endpoint"""
        url = f"{self.base_url}{self.api_prefix}{endpoint}"
        
        if headers is None:
            headers = {}
        
        if data:
            headers["Content-Type"] = "application/json"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Status code: {e.response.status_code}")
                    print(f"   Response text: {e.response.text}")
            return {}
    
    def test_health_check(self):
        """Test health check endpoint"""
        print("🔍 Testing health check...")
        result = self._make_request("GET", "/health")
        if result:
            print(f"✅ Health check: {result}")
        return result
    
    def test_register(self, email: str, password: str):
        """Test user registration"""
        print(f"📝 Testing user registration for {email}...")
        
        data = {
            "email": email,
            "password": password,
            "confirm_password": password
        }
        
        result = self._make_request("POST", "/register", data)
        if result:
            print(f"✅ Registration successful: {result}")
            return result
        return None
    
    def test_login(self, email: str, password: str):
        """Test user login"""
        print(f"🔐 Testing login for {email}...")
        
        data = {
            "email": email,
            "password": password
        }
        
        result = self._make_request("POST", "/login", data)
        if result:
            print(f"✅ Login successful: {result}")
            # Store tokens for later use
            self.access_token = result.get("access_token")
            self.refresh_token = result.get("refresh_token")
            return result
        return None
    
    def test_profile(self):
        """Test getting user profile (protected route)"""
        if not self.access_token:
            print("❌ No access token available. Login first.")
            return None
        
        print("👤 Testing profile retrieval...")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        result = self._make_request("GET", "/profile", headers=headers)
        if result:
            print(f"✅ Profile retrieved: {result}")
            return result
        return None
    
    def test_validate_token(self):
        """Test token validation (protected route)"""
        if not self.access_token:
            print("❌ No access token available. Login first.")
            return None
        
        print("🔍 Testing token validation...")
        
        headers = {
            "Authorization": f"Bearer {self.access_token}"
        }
        
        result = self._make_request("GET", "/validate", headers=headers)
        if result:
            print(f"✅ Token validation: {result}")
            return result
        return None
    
    def test_refresh_token(self):
        """Test token refresh"""
        if not self.refresh_token:
            print("❌ No refresh token available. Login first.")
            return None
        
        print("🔄 Testing token refresh...")
        
        data = {
            "refresh_token": self.refresh_token
        }
        
        result = self._make_request("POST", "/refresh", data)
        if result:
            print(f"✅ Token refreshed: {result}")
            # Update access token
            self.access_token = result.get("access_token")
            return result
        return None
    
    def test_logout(self):
        """Test user logout"""
        if not self.refresh_token:
            print("❌ No refresh token available. Login first.")
            return None
        
        print("🚪 Testing logout...")
        
        data = {
            "refresh_token": self.refresh_token
        }
        
        result = self._make_request("POST", "/logout", data)
        if result:
            print(f"✅ Logout successful: {result}")
            # Clear tokens
            self.access_token = None
            self.refresh_token = None
            return result
        return None
    
    def run_complete_test(self):
        """Run complete authentication flow test"""
        print("🚀 Starting Complete Authentication Flow Test\n")
        
        # Test health check
        self.test_health_check()
        print()
        
        # Test registration
        test_email = "testuser@example.com"
        test_password = "TestPass123"
        
        registration = self.test_register(test_email, test_password)
        if not registration:
            print("⚠️ Registration failed, trying login with existing user...")
        
        print()
        
        # Test login
        login = self.test_login(test_email, test_password)
        if not login:
            print("❌ Login failed. Cannot continue with protected routes.")
            return
        
        print()
        
        # Test protected routes
        self.test_profile()
        print()
        
        self.test_validate_token()
        print()
        
        # Test token refresh
        self.test_refresh_token()
        print()
        
        # Test logout
        self.test_logout()
        print()
        
        print("🎉 Complete authentication flow test finished!")

def main():
    """Main function to run tests"""
    print("🔧 Authentication Endpoints Tester")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8001/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running on http://localhost:8001")
        else:
            print("⚠️ Server responded but with unexpected status")
    except requests.exceptions.RequestException:
        print("❌ Server is not running. Please start your FastAPI server first:")
        print("   python main.py")
        return
    
    print()
    
    # Create tester and run tests
    tester = HTTPAuthTester()
    tester.run_complete_test()

if __name__ == "__main__":
    main()




"Test the end points"