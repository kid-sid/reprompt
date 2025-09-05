#!/usr/bin/env python3
"""
Test HTTP endpoints for authentication
"""

import requests
import time
import json

class HTTPAuthTester:
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_prefix = "/api/v1/auth"
        self.access_token = None
        self.refresh_token = None
        
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
    
    def test_register(self):
        """Test user registration"""
        timestamp = int(time.time())
        email = f"httptest{timestamp}@example.com"
        password = "TestPass123"
        
        print(f"📝 Testing user registration for {email}...")
        
        data = {
            "email": email,
            "password": password,
            "confirm_password": password
        }
        
        result = self._make_request("POST", "/register", data)
        if result:
            print(f"✅ Registration successful: {result}")
            return email, password
        return None, None
    
    def test_login(self, email: str, password: str):
        """Test user login"""
        print(f"🔐 Testing login for {email}...")
        
        data = {
            "email": email,
            "password": password
        }
        
        result = self._make_request("POST", "/login", data)
        if result:
            print(f"✅ Login successful")
            print(f"   Access Token: {result.get('access_token', '')[:20]}...")
            print(f"   Refresh Token: {result.get('refresh_token', '')}...")
            
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
            self.refresh_token = result.get("refresh_token")
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
        """Run complete HTTP endpoint test"""
        print("🚀 Starting HTTP Endpoints Test\n")
        
        # Test health check
        self.test_health_check()
        print()
        
        # Test registration
        email, password = self.test_register()
        if not email:
            print("❌ Registration failed. Cannot continue.")
            return
        
        print()
        
        # Test login
        login = self.test_login(email, password)
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
        
        print("🎉 HTTP endpoints test completed successfully!")

def main():
    """Main function"""
    print("🔧 HTTP Authentication Endpoints Tester")
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
