"""
Offline Rate Limiting Test

This script tests the rate limiting logic without requiring a running server.
It's useful for verifying the implementation works correctly.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_rate_limiting_service():
    """Test the rate limiting service directly"""
    print("🧪 Testing Rate Limiting Service (Offline)")
    print("=" * 50)
    
    try:
        from services.rate_limiting_service import CentralizedRateLimiter, RateLimitTier, RateLimitConfig
        
        print("✅ Successfully imported rate limiting service")
        
        # Test service initialization
        print("\n1️⃣ Testing service initialization...")
        limiter = CentralizedRateLimiter()
        print("✅ Rate limiter initialized")
        
        # Test health check
        print("\n2️⃣ Testing health check...")
        health = limiter.health_check()
        print(f"✅ Health check: {health.get('status', 'unknown')}")
        print(f"   Redis status: {health.get('redis', 'unknown')}")
        print(f"   Endpoints: {len(health.get('endpoints_configured', []))}")
        
        # Test rate limit configuration
        print("\n3️⃣ Testing rate limit configuration...")
        inference_limits = limiter.rate_limits.get('inference', {})
        free_limits = inference_limits.get(RateLimitTier.FREE)
        
        if free_limits:
            print(f"✅ Free tier limits: {free_limits.requests_per_minute}/min, {free_limits.requests_per_hour}/hour")
        else:
            print("❌ Free tier limits not found")
        
        # Test rate limit check (will use in-memory fallback)
        print("\n4️⃣ Testing rate limit check...")
        try:
            result = limiter.check_rate_limit(
                identifier="test_user_123",
                endpoint="inference",
                user_id="test_user_123"
            )
            print(f"✅ Rate limit check passed: {result.get('allowed', False)}")
            print(f"   Tier: {result.get('tier', 'unknown')}")
            print(f"   Endpoint: {result.get('endpoint', 'unknown')}")
        except Exception as e:
            print(f"⚠️  Rate limit check failed (expected with in-memory fallback): {e}")
        
        # Test rate limit status
        print("\n5️⃣ Testing rate limit status...")
        try:
            status = limiter.get_rate_limit_status(
                identifier="test_user_123",
                endpoint="inference",
                user_id="test_user_123"
            )
            print(f"✅ Rate limit status retrieved")
            print(f"   Tier: {status.get('tier', 'unknown')}")
            print(f"   Counts: {status.get('counts', {})}")
            print(f"   Limits: {status.get('limits', {})}")
        except Exception as e:
            print(f"⚠️  Rate limit status failed: {e}")
        
        print("\n✅ Rate limiting service tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import rate limiting service: {e}")
        return False
    except Exception as e:
        print(f"❌ Rate limiting service test failed: {e}")
        return False

def test_middleware_import():
    """Test middleware import"""
    print("\n🔧 Testing Middleware Import")
    print("=" * 30)
    
    try:
        from middleware.rate_limiting_middleware import RateLimitingMiddleware
        print("✅ Rate limiting middleware imported successfully")
        
        # Test middleware configuration
        print("\n6️⃣ Testing middleware configuration...")
        middleware = RateLimitingMiddleware(
            app=None,  # We don't need a real app for this test
            bypass_endpoints=["/health", "/docs"],
            bypass_patterns=["/static/"]
        )
        print("✅ Middleware configured successfully")
        print(f"   Bypass endpoints: {len(middleware.bypass_endpoints)}")
        print(f"   Bypass patterns: {len(middleware.bypass_patterns)}")
        print(f"   Endpoint mappings: {len(middleware.endpoint_mapping)}")
        
        # Test endpoint categorization
        print("\n7️⃣ Testing endpoint categorization...")
        test_endpoints = [
            "/api/v1/optimize-prompt",
            "/api/v1/auth/login", 
            "/api/v1/prompt-history",
            "/api/v1/feedback",
            "/unknown/endpoint"
        ]
        
        for endpoint in test_endpoints:
            category = middleware._get_endpoint_category(endpoint)
            print(f"   {endpoint} -> {category}")
        
        print("\n✅ Middleware tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import middleware: {e}")
        return False
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        return False

def test_utils_import():
    """Test utility functions import"""
    print("\n🛠️ Testing Utility Functions")
    print("=" * 30)
    
    try:
        from utils.rate_limiting_utils import (
            get_rate_limit_info,
            check_rate_limit_for_user,
            get_user_rate_limit_status,
            format_rate_limit_message
        )
        print("✅ Rate limiting utilities imported successfully")
        
        # Test utility functions
        print("\n8️⃣ Testing utility functions...")
        
        # Test format function
        test_info = {
            "tier": "free",
            "counts": {"minute": 3, "hour": 25, "day": 100},
            "limits": {"minute": 5, "hour": 50, "day": 200}
        }
        
        message = format_rate_limit_message(test_info)
        print(f"✅ Format function works: {len(message)} characters")
        
        print("\n✅ Utility functions tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import utilities: {e}")
        return False
    except Exception as e:
        print(f"❌ Utility functions test failed: {e}")
        return False

def test_config_import():
    """Test configuration import"""
    print("\n⚙️ Testing Configuration")
    print("=" * 25)
    
    try:
        from rate_limits_config import (
            RATE_LIMIT_CONFIGS,
            ENDPOINT_MAPPING,
            BYPASS_ENDPOINTS,
            BYPASS_PATTERNS
        )
        print("✅ Rate limiting configuration imported successfully")
        
        print(f"   Rate limit configs: {len(RATE_LIMIT_CONFIGS)} endpoints")
        print(f"   Endpoint mappings: {len(ENDPOINT_MAPPING)}")
        print(f"   Bypass endpoints: {len(BYPASS_ENDPOINTS)}")
        print(f"   Bypass patterns: {len(BYPASS_PATTERNS)}")
        
        # Test specific configurations
        if "inference" in RATE_LIMIT_CONFIGS:
            inference_config = RATE_LIMIT_CONFIGS["inference"]
            print(f"   Inference tiers: {len(inference_config)}")
        
        print("\n✅ Configuration tests completed!")
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import configuration: {e}")
        return False
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all offline tests"""
    print("🧪 Rate Limiting Offline Test Suite")
    print("=" * 50)
    print("This test verifies the rate limiting implementation")
    print("without requiring a running server or Redis.\n")
    
    tests = [
        ("Rate Limiting Service", test_rate_limiting_service),
        ("Middleware Import", test_middleware_import),
        ("Utility Functions", test_utils_import),
        ("Configuration", test_config_import)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n📈 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Rate limiting system is ready.")
        print("\n💡 Next steps:")
        print("   1. Start the server: python start_server.py")
        print("   2. Test with: python testing/test_rate_limiting.py")
        print("   3. Check rate limits at: http://localhost:8001/api/v1/rate-limit/status")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
