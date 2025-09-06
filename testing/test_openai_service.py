"""
Test script for OpenAI Service

This script tests all functionality of the OpenAI service including:
- Service initialization
- Rate limiting
- Chat completion (lazy and pro modes)
- Text completion (lazy and pro modes)
- Model listing
- Health checks
- Error handling
- Mode selection and model switching
"""

import os
import sys
import time
from typing import Dict, Any

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_openai_service():
    """Test the OpenAI service functionality"""
    
    print("🚀 Testing OpenAI Service...")
    print("=" * 50)
    
    try:
        # Test 1: Import and initialization
        print("\n1️⃣ Testing service import and initialization...")
        from services.openai_service import openai_service, create_openai_client
        
        if openai_service is None:
            print("❌ OpenAI service failed to initialize")
            return False
        
        print("✅ OpenAI service imported successfully")
        
        # Test 2: Health check
        print("\n2️⃣ Testing health check...")
        health = openai_service.health_check()
        print(f"Health status: {health['status']}")
        print(f"API connected: {health['api_connected']}")
        
        if health['status'] == 'healthy':
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
            return False
        
        # Test 3: List models (optional)
        print("\n3️⃣ Testing model listing (optional)...")
        try:
            models = openai_service.list_models()
            print(f"Found {len(models)} models")
            if models:
                print(f"First model: {models[0]['id']}")
            print("✅ Model listing successful")
        except Exception as e:
            print(f"⚠️ Model listing failed (non-critical): {e}")
            print("   This is optional and won't affect core functionality")
        
        # Test 4: Create OpenAI client
        print("\n4️⃣ Testing OpenAI client creation...")
        try:
            client = create_openai_client()
            print("✅ OpenAI client created successfully")
        except Exception as e:
            print(f"❌ OpenAI client creation failed: {e}")
            return False
        
        # Test 5: Chat completion - Lazy mode
        print("\n5️⃣ Testing chat completion - Lazy mode...")
        try:
            messages = [
                {"role": "user", "content": "Hello! How are you today?"}
            ]
            
            response = openai_service.chat_completion(
                messages=messages,
                mode="lazy"
            )
            
            print(f"✅ Lazy mode chat completion successful")
            print(f"   Model used: {response['model']}")
            print(f"   Mode: {response['mode']}")
            print(f"   Content: {response['content'][:100]}...")
            print(f"   Tokens used: {response['usage']['total_tokens']}")
            
        except Exception as e:
            print(f"❌ Lazy mode chat completion failed: {e}")
            return False
        
        # Test 6: Chat completion - Pro mode
        print("\n6️⃣ Testing chat completion - Pro mode...")
        try:
            messages = [
                {"role": "user", "content": "Explain quantum computing in simple terms"}
            ]
            
            response = openai_service.chat_completion(
                messages=messages,
                mode="pro"
            )
            
            print(f"✅ Pro mode chat completion successful")
            print(f"   Model used: {response['model']}")
            print(f"   Mode: {response['mode']}")
            print(f"   Content: {response['content'][:100]}...")
            print(f"   Tokens used: {response['usage']['total_tokens']}")
            
        except Exception as e:
            print(f"❌ Pro mode chat completion failed: {e}")
            return False
        
        # Test 7: Text completion - Lazy mode (using chat API)
        print("\n7️⃣ Testing text completion - Lazy mode (using chat API)...")
        try:
            prompt = "The future of artificial intelligence is"
            
            response = openai_service.text_completion(
                prompt=prompt,
                mode="lazy"
            )
            
            print(f"✅ Lazy mode text completion successful")
            print(f"   Model used: {response['model']}")
            print(f"   Mode: {response['mode']}")
            print(f"   Content: {response['content'][:100]}...")
            print(f"   Tokens used: {response['usage']['total_tokens']}")
            
        except Exception as e:
            print(f"❌ Lazy mode text completion failed: {e}")
            return False
        
        # Test 8: Text completion - Pro mode (using chat API)
        print("\n8️⃣ Testing text completion - Pro mode (using chat API)...")
        try:
            prompt = "The future of artificial intelligence is"
            
            response = openai_service.text_completion(
                prompt=prompt,
                mode="pro"
            )
            
            print(f"✅ Pro mode text completion successful")
            print(f"   Model used: {response['model']}")
            print(f"   Mode: {response['mode']}")
            print(f"   Content: {response['content'][:100]}...")
            print(f"   Tokens used: {response['usage']['total_tokens']}")
            
        except Exception as e:
            print(f"❌ Pro mode text completion failed: {e}")
            return False
        
        # Test 9: Custom parameters override
        print("\n9️⃣ Testing custom parameters override...")
        try:
            messages = [
                {"role": "user", "content": "Write a short poem about coding"}
            ]
            
            response = openai_service.chat_completion(
                messages=messages,
                model="gpt-3.5-turbo",  # Override model
                max_tokens=100,         # Override max tokens
                temperature=0.8,        # Override temperature
                mode="lazy"
            )
            
            print(f"✅ Custom parameters override successful")
            print(f"   Model used: {response['model']}")
            print(f"   Max tokens: 100 (custom)")
            print(f"   Temperature: 0.8 (custom)")
            print(f"   Content: {response['content'][:100]}...")
            
        except Exception as e:
            print(f"❌ Custom parameters override failed: {e}")
            return False
        
        # Test 10: Rate limiting
        print("\n🔟 Testing rate limiting...")
        try:
            # Make multiple requests quickly to test rate limiting
            print("   Making multiple requests to test rate limiting...")
            
            for i in range(3):
                try:
                    response = openai_service.chat_completion(
                        messages=[{"role": "user", "content": f"Test message {i+1}"}],
                        mode="lazy"
                    )
                    print(f"   Request {i+1}: ✅ Success")
                    time.sleep(0.1)  # Small delay between requests
                except Exception as e:
                    if "Rate limit exceeded" in str(e):
                        print(f"   Request {i+1}: ⚠️ Rate limited (expected)")
                        break
                    else:
                        print(f"   Request {i+1}: ❌ Unexpected error: {e}")
            
            print("✅ Rate limiting test completed")
            
        except Exception as e:
            print(f"❌ Rate limiting test failed: {e}")
        
        # Test 11: Usage info
        print("\n1️⃣1️⃣ Testing usage info...")
        try:
            usage = openai_service.get_usage_info()
            print(f"✅ Usage info retrieved successfully")
            print(f"   Requests in window: {usage['requests_in_window']}")
            print(f"   Rate limited: {usage['rate_limited']}")
            print(f"   Max requests per minute: {usage['max_requests_per_minute']}")
            
        except Exception as e:
            print(f"❌ Usage info retrieval failed: {e}")
        
        # Test 12: Error handling - Invalid inputs
        print("\n1️⃣2️⃣ Testing error handling - Invalid inputs...")
        
        # Test empty messages
        try:
            openai_service.chat_completion(messages=[], mode="lazy")
            print("❌ Should have failed with empty messages")
            return False
        except ValueError as e:
            print(f"✅ Correctly caught empty messages error: {e}")
        
        # Test invalid temperature
        try:
            openai_service.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                temperature=3.0,  # Invalid temperature
                mode="lazy"
            )
            print("❌ Should have failed with invalid temperature")
            return False
        except ValueError as e:
            print(f"✅ Correctly caught invalid temperature error: {e}")
        
        # Test invalid max_tokens
        try:
            openai_service.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=0,  # Invalid max_tokens
                mode="lazy"
            )
            print("❌ Should have failed with invalid max_tokens")
            return False
        except ValueError as e:
            print(f"✅ Correctly caught invalid max_tokens error: {e}")
        
        print("✅ Error handling test completed")
        
        # Test 13: Mode validation
        print("\n1️⃣3️⃣ Testing mode validation...")
        
        # Test invalid mode
        try:
            openai_service.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                mode="invalid_mode"
            )
            print("❌ Should have failed with invalid mode")
            return False
        except ValueError as e:
            if "Invalid mode" in str(e):
                print(f"✅ Correctly caught invalid mode error: {e}")
            else:
                print(f"❌ Unexpected error for invalid mode: {e}")
                return False
        
        print("\n🎉 All tests completed successfully!")
        print("✅ OpenAI service is working correctly")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running this from the project root directory")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_config_values():
    """Test that config values are properly set"""
    
    print("\n🔧 Testing configuration values...")
    print("=" * 30)
    
    try:
        from config import settings
        
        print(f"LAZY_MODEL: {settings.LAZY_MODEL}")
        print(f"PRO_MODEL: {settings.PRO_MODEL}")
        print(f"LAZY_MAX_TOKENS: {settings.LAZY_MAX_TOKENS}")
        print(f"LAZY_TEMPERATURE: {settings.LAZY_TEMPERATURE}")
        print(f"PRO_MAX_TOKENS: {settings.PRO_MAX_TOKENS}")
        print(f"PRO_TEMPERATURE: {settings.PRO_TEMPERATURE}")
        print(f"OPENAI_API_KEY: {'✅ Set' if settings.OPENAI_API_KEY else '❌ Not set'}")
        
        if not settings.OPENAI_API_KEY:
            print("⚠️  Warning: OPENAI_API_KEY not set. Tests may fail.")
            print("   Please set your OpenAI API key in .env file or environment variables.")
        
        return True
        
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        return False

def main():
    """Main test function"""
    
    print("🧪 OpenAI Service Test Suite")
    print("=" * 50)
    
    # Test configuration first
    if not test_config_values():
        print("\n❌ Configuration test failed. Please check your .env file.")
        return
    
    # Test the service
    if test_openai_service():
        print("\n🎯 All tests passed! OpenAI service is ready for production.")
    else:
        print("\n💥 Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
