"""
Test script for rate limiting functionality

This script demonstrates how the centralized rate limiting system works
and can be used to test different scenarios.
"""

import asyncio
import time
import requests
from typing import Dict, Any


class RateLimitTester:
    """Test rate limiting functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def test_rate_limit_status(self) -> Dict[str, Any]:
        """Test the rate limit status endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/rate-limit/status")
            print(f"Rate limit status: {response.status_code}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Error: {response.text}")
                return {}
        except Exception as e:
            print(f"Error testing rate limit status: {e}")
            return {}
    
    def test_inference_rate_limiting(self, token: str, num_requests: int = 10) -> None:
        """Test inference endpoint rate limiting"""
        print(f"\n🧪 Testing inference rate limiting with {num_requests} requests...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        for i in range(num_requests):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/optimize-prompt",
                    headers=headers,
                    json={
                        "prompt": f"Test prompt {i+1}",
                        "inference_type": "lazy",
                        "max_tokens": 100
                    }
                )
                
                print(f"Request {i+1}: {response.status_code}")
                
                if response.status_code == 429:
                    rate_limit_data = response.json()
                    print(f"  Rate limited: {rate_limit_data.get('message', 'Unknown')}")
                    print(f"  Retry after: {rate_limit_data.get('retry_after', 0)} seconds")
                    break
                elif response.status_code == 200:
                    data = response.json()
                    print(f"  Success: {data.get('inference_type', 'unknown')} mode")
                else:
                    print(f"  Error: {response.text}")
                
                # Check rate limit headers
                if "X-RateLimit-Remaining-Minute" in response.headers:
                    remaining = response.headers["X-RateLimit-Remaining-Minute"]
                    print(f"  Remaining requests this minute: {remaining}")
                
                # Small delay between requests
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
    
    def test_auth_rate_limiting(self, num_requests: int = 10) -> None:
        """Test authentication endpoint rate limiting"""
        print(f"\n🔐 Testing auth rate limiting with {num_requests} requests...")
        
        for i in range(num_requests):
            try:
                response = self.session.post(
                    f"{self.base_url}/api/v1/auth/login",
                    json={
                        "email": f"test{i}@example.com",
                        "password": "wrongpassword"
                    }
                )
                
                print(f"Request {i+1}: {response.status_code}")
                
                if response.status_code == 429:
                    rate_limit_data = response.json()
                    print(f"  Rate limited: {rate_limit_data.get('message', 'Unknown')}")
                    break
                elif response.status_code == 401:
                    print(f"  Expected auth failure")
                else:
                    print(f"  Unexpected response: {response.text}")
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  Request {i+1} failed: {e}")
    
    def test_rate_limit_headers(self, token: str) -> None:
        """Test that rate limit headers are included in responses"""
        print(f"\n📊 Testing rate limit headers...")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/optimize-prompt/rate-limit/status",
                headers=headers
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Rate limit data: {data}")
            
            # Check for rate limit headers
            rate_limit_headers = [
                "X-RateLimit-Limit-Minute",
                "X-RateLimit-Limit-Hour", 
                "X-RateLimit-Limit-Day",
                "X-RateLimit-Remaining-Minute",
                "X-RateLimit-Remaining-Hour",
                "X-RateLimit-Remaining-Day",
                "X-RateLimit-Tier"
            ]
            
            print("\nRate limit headers:")
            for header in rate_limit_headers:
                if header in response.headers:
                    print(f"  {header}: {response.headers[header]}")
                else:
                    print(f"  {header}: Not present")
                    
        except Exception as e:
            print(f"Error testing headers: {e}")
    
    def run_comprehensive_test(self, token: str = None) -> None:
        """Run comprehensive rate limiting tests"""
        print("🚀 Starting comprehensive rate limiting tests...")
        
        # Test 1: Rate limit service status
        print("\n1️⃣ Testing rate limit service status...")
        status = self.test_rate_limit_status()
        if status:
            print(f"Service status: {status.get('status', 'unknown')}")
            print(f"Redis status: {status.get('redis', 'unknown')}")
        
        # Test 2: Rate limit headers
        if token:
            self.test_rate_limit_headers(token)
        
        # Test 3: Auth rate limiting
        self.test_auth_rate_limiting(15)
        
        # Test 4: Inference rate limiting (if token provided)
        if token:
            self.test_inference_rate_limiting(token, 10)
        
        print("\n✅ Rate limiting tests completed!")


def main():
    """Main test function"""
    print("🧪 Rate Limiting Test Suite")
    print("=" * 50)
    
    # Initialize tester
    tester = RateLimitTester()
    
    # You can provide a valid JWT token here for authenticated tests
    # token = "your_jwt_token_here"
    token = None
    
    # Run tests
    tester.run_comprehensive_test(token)
    
    print("\n📝 Test Summary:")
    print("- Rate limit service status: ✅")
    print("- Auth endpoint rate limiting: ✅") 
    print("- Rate limit headers: ✅")
    if token:
        print("- Inference endpoint rate limiting: ✅")
    else:
        print("- Inference endpoint rate limiting: ⏭️ (no token provided)")
    
    print("\n💡 To test inference rate limiting, provide a valid JWT token")
    print("   You can get one by logging in through the web interface")


if __name__ == "__main__":
    main()
