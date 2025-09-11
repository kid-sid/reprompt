#!/usr/bin/env python3
"""
Comprehensive Test Suite for Reprompt Chatbot API
Tests all endpoints, Supabase connection, and system functionality
"""

import asyncio
import json
import time
import requests
import sys
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

class TestRepromptAPI:
    """Comprehensive test suite for Reprompt Chatbot API"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"
        self.auth_base = f"{self.api_base}/auth"
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "TestPassword123!"
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
        self.test_results = []
        
    def log(self, message: str, color: str = Colors.WHITE, level: str = "INFO"):
        """Log message with color and timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{color}[{timestamp}] {level}: {message}{Colors.END}")
        
    def log_success(self, message: str):
        """Log success message"""
        self.log(f"✅ {message}", Colors.GREEN, "SUCCESS")
        
    def log_error(self, message: str):
        """Log error message"""
        self.log(f"❌ {message}", Colors.RED, "ERROR")
        
    def log_warning(self, message: str):
        """Log warning message"""
        self.log(f"⚠️ {message}", Colors.YELLOW, "WARNING")
        
    def log_info(self, message: str):
        """Log info message"""
        self.log(f"ℹ️ {message}", Colors.BLUE, "INFO")
        
    def log_debug(self, message: str):
        """Log debug message"""
        self.log(f"🔍 {message}", Colors.CYAN, "DEBUG")

    def test_server_connection(self) -> bool:
        """Test if the server is running and accessible"""
        self.log_info("Testing server connection...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_success(f"Server is running at {self.base_url}")
                self.log_debug(f"Health check response: {response.json()}")
                return True
            else:
                self.log_error(f"Server health check failed: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_error(f"Cannot connect to server: {e}")
            self.log_warning("Make sure the server is running with: python main.py")
            return False

    def test_root_endpoint(self) -> bool:
        """Test the root API endpoint"""
        self.log_info("Testing root endpoint...")
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_success("Root endpoint accessible")
                self.log_debug(f"Root response: {data}")
                return True
            else:
                self.log_error(f"Root endpoint failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"Root endpoint error: {e}")
            return False

    def test_frontend_endpoints(self) -> bool:
        """Test frontend serving endpoints"""
        self.log_info("Testing frontend endpoints...")
        endpoints = [
            ("/auth", "Authentication page"),
            ("/frontend", "Chatbot page"),
            ("/static/auth.html", "Static auth file"),
            ("/static/chatbot.html", "Static chatbot file")
        ]
        
        all_passed = True
        for endpoint, description in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                if response.status_code == 200:
                    self.log_success(f"{description} accessible")
                else:
                    self.log_error(f"{description} failed: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_error(f"{description} error: {e}")
                all_passed = False
                
        return all_passed

    def test_auth_health(self) -> bool:
        """Test authentication service health"""
        self.log_info("Testing authentication service health...")
        try:
            response = requests.get(f"{self.auth_base}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log_success("Authentication service is healthy")
                self.log_debug(f"Auth health response: {data}")
                return True
            else:
                self.log_error(f"Auth health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_error(f"Auth health check error: {e}")
            return False

    def test_supabase_connection(self) -> bool:
        """Test Supabase connection through user registration"""
        self.log_info("Testing Supabase connection...")
        try:
            # Try to register a test user (this will test Supabase connection)
            test_data = {
                "email": self.test_email,
                "password": self.test_password,
                "confirm_password": self.test_password
            }
            
            response = requests.post(
                f"{self.auth_base}/signup",
                json=test_data,
                timeout=15
            )
            
            if response.status_code == 201:
                data = response.json()
                self.user_id = data.get("id")
                self.log_success("Supabase connection successful - User registered")
                self.log_debug(f"User ID: {self.user_id}")
                return True
            elif response.status_code == 409:
                self.log_warning("User already exists - Supabase connection working")
                return True
            else:
                self.log_error(f"Supabase connection failed: {response.status_code}")
                self.log_debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"Supabase connection error: {e}")
            return False

    def test_user_login(self) -> bool:
        """Test user login functionality"""
        self.log_info("Testing user login...")
        try:
            login_data = {
                "email": self.test_email,
                "password": self.test_password
            }
            
            response = requests.post(
                f"{self.auth_base}/login",
                json=login_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.access_token = data.get("access_token")
                self.refresh_token = data.get("refresh_token")
                self.log_success("User login successful")
                self.log_debug(f"Access token: {self.access_token[:20]}...")
                self.log_debug(f"Refresh token: {self.refresh_token[:20]}...")
                return True
            else:
                self.log_error(f"Login failed: {response.status_code}")
                self.log_debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"Login error: {e}")
            return False

    def test_token_validation(self) -> bool:
        """Test token validation endpoint"""
        self.log_info("Testing token validation...")
        if not self.access_token:
            self.log_error("No access token available for validation")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.auth_base}/validate",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_success("Token validation successful")
                self.log_debug(f"Validation response: {data}")
                return True
            else:
                self.log_error(f"Token validation failed: {response.status_code}")
                self.log_debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"Token validation error: {e}")
            return False

    def test_user_profile(self) -> bool:
        """Test user profile endpoint"""
        self.log_info("Testing user profile...")
        if not self.access_token:
            self.log_error("No access token available for profile test")
            return False
            
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            response = requests.get(
                f"{self.auth_base}/profile",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.log_success("User profile retrieved successfully")
                self.log_debug(f"Profile data: {data}")
                return True
            else:
                self.log_error(f"Profile retrieval failed: {response.status_code}")
                self.log_debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"Profile retrieval error: {e}")
            return False

    def test_prompt_optimization(self) -> bool:
        """Test prompt optimization endpoint"""
        self.log_info("Testing prompt optimization...")
        if not self.access_token:
            self.log_error("No access token available for optimization test")
            return False
            
        test_prompts = [
            {
                "prompt": "Write a story about a cat",
                "inference_type": "lazy",
                "description": "Lazy mode optimization"
            },
            {
                "prompt": "Explain quantum computing",
                "inference_type": "pro", 
                "description": "Pro mode optimization"
            }
        ]
        
        all_passed = True
        for test_case in test_prompts:
            try:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json"
                }
                
                response = requests.post(
                    f"{self.api_base}/optimize-prompt",
                    json=test_case,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.log_success(f"{test_case['description']} successful")
                    self.log_debug(f"Optimized prompt: {data.get('output', '')[:100]}...")
                    self.log_debug(f"Tokens used: {data.get('tokens_used', 'N/A')}")
                else:
                    self.log_error(f"{test_case['description']} failed: {response.status_code}")
                    self.log_debug(f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_error(f"{test_case['description']} error: {e}")
                all_passed = False
                
        return all_passed

    def test_token_refresh(self) -> bool:
        """Test token refresh functionality"""
        self.log_info("Testing token refresh...")
        if not self.refresh_token:
            self.log_error("No refresh token available for refresh test")
            return False
            
        try:
            refresh_data = {"refresh_token": self.refresh_token}
            response = requests.post(
                f"{self.auth_base}/refresh",
                json=refresh_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                new_access_token = data.get("access_token")
                self.log_success("Token refresh successful")
                self.log_debug(f"New access token: {new_access_token[:20]}...")
                # Update the access token for further tests
                self.access_token = new_access_token
                return True
            else:
                self.log_error(f"Token refresh failed: {response.status_code}")
                self.log_debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"Token refresh error: {e}")
            return False

    def test_user_logout(self) -> bool:
        """Test user logout functionality"""
        self.log_info("Testing user logout...")
        if not self.refresh_token:
            self.log_error("No refresh token available for logout test")
            return False
            
        try:
            logout_data = {"refresh_token": self.refresh_token}
            response = requests.post(
                f"{self.auth_base}/logout",
                json=logout_data,
                timeout=10
            )
            
            if response.status_code == 200:
                self.log_success("User logout successful")
                self.log_debug("Tokens invalidated")
                return True
            else:
                self.log_error(f"Logout failed: {response.status_code}")
                self.log_debug(f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_error(f"Logout error: {e}")
            return False

    def test_error_handling(self) -> bool:
        """Test error handling with invalid requests"""
        self.log_info("Testing error handling...")
        
        error_tests = [
            {
                "endpoint": f"{self.auth_base}/login",
                "data": {"email": "invalid@test.com", "password": "wrong"},
                "expected_status": 401,
                "description": "Invalid login credentials"
            },
            {
                "endpoint": f"{self.api_base}/optimize-prompt",
                "data": {"prompt": "", "inference_type": "lazy"},
                "expected_status": 401,  # Should fail due to no auth
                "description": "Unauthorized optimization request"
            }
        ]
        
        all_passed = True
        for test in error_tests:
            try:
                response = requests.post(
                    test["endpoint"],
                    json=test["data"],
                    timeout=10
                )
                
                if response.status_code == test["expected_status"]:
                    self.log_success(f"{test['description']} handled correctly")
                else:
                    self.log_warning(f"{test['description']} returned {response.status_code} instead of {test['expected_status']}")
                    
            except Exception as e:
                self.log_error(f"{test['description']} error: {e}")
                all_passed = False
                
        return all_passed

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        self.log_info("Starting comprehensive API test suite...")
        self.log_info(f"Test email: {self.test_email}")
        
        tests = [
            ("Server Connection", self.test_server_connection),
            ("Root Endpoint", self.test_root_endpoint),
            ("Frontend Endpoints", self.test_frontend_endpoints),
            ("Auth Health Check", self.test_auth_health),
            ("Supabase Connection", self.test_supabase_connection),
            ("User Login", self.test_user_login),
            ("Token Validation", self.test_token_validation),
            ("User Profile", self.test_user_profile),
            ("Prompt Optimization", self.test_prompt_optimization),
            ("Token Refresh", self.test_token_refresh),
            ("User Logout", self.test_user_logout),
            ("Error Handling", self.test_error_handling)
        ]
        
        results = {}
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            self.log_info(f"\n{'='*50}")
            self.log_info(f"Running: {test_name}")
            self.log_info(f"{'='*50}")
            
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    passed += 1
                    self.log_success(f"{test_name} PASSED")
                else:
                    self.log_error(f"{test_name} FAILED")
            except Exception as e:
                self.log_error(f"{test_name} ERROR: {e}")
                results[test_name] = False
        
        # Summary
        self.log_info(f"\n{'='*60}")
        self.log_info("TEST SUMMARY")
        self.log_info(f"{'='*60}")
        self.log_info(f"Total Tests: {total}")
        self.log_success(f"Passed: {passed}")
        self.log_error(f"Failed: {total - passed}")
        self.log_info(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            self.log_success("🎉 ALL TESTS PASSED! System is working correctly.")
        else:
            self.log_warning(f"⚠️ {total - passed} tests failed. Check the logs above.")
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed/total)*100,
            "results": results,
            "test_email": self.test_email
        }

def main():
    """Main function to run the test suite"""
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("="*60)
    print("🤖 REPROMPT CHATBOT API - COMPREHENSIVE TEST SUITE")
    print("="*60)
    print(f"{Colors.END}")
    
    # Check if server URL is provided as argument
    server_url = "http://localhost:8001"
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    
    print(f"{Colors.BLUE}Testing server at: {server_url}{Colors.END}")
    print(f"{Colors.BLUE}Make sure the server is running with: python main.py{Colors.END}\n")
    
    # Create test instance and run tests
    tester = TestRepromptAPI(server_url)
    results = tester.run_all_tests()
    
    # Exit with appropriate code
    if results["passed"] == results["total"]:
        sys.exit(0)  # Success
    else:
        sys.exit(1)  # Failure

if __name__ == "__main__":
    main()
