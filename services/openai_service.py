"""
Production-ready OpenAI Service

This service handles OpenAI API operations with rate limiting,
proper error handling, and logging while maintaining original functionality.
"""

import openai
import time
from typing import Dict, Any, List
from loguru import logger
from config import settings

# Production configuration constants
MAX_REQUESTS_PER_MINUTE = 60  # OpenAI's default rate limit
RATE_LIMIT_WINDOW = 60  # 1 minute

class RateLimiter:
    """Simple rate limiting implementation for OpenAI API calls"""
    
    def __init__(self):
        self.requests: List[float] = []
    
    def is_rate_limited(self) -> bool:
        """Check if request is rate limited"""
        now = time.time()
        
        # Clean old requests
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < RATE_LIMIT_WINDOW]
        
        if len(self.requests) >= MAX_REQUESTS_PER_MINUTE:
            return True
        
        self.requests.append(now)
        return False

class OpenAIService:
    """OpenAI service with rate limiting and error handling"""
    
    def __init__(self):
        """Initialize OpenAI service with validation"""
        self._validate_environment()
        self.client = self._initialize_client()
        self.rate_limiter = RateLimiter()
        self._health_check()
        logger.info("OpenAI service initialized successfully")
    
    def _validate_environment(self):
        """Validate required environment variables"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable or create a .env file with your API key.")
        
        # Validate API key format (OpenAI keys start with 'sk-')
        if not settings.OPENAI_API_KEY.startswith('sk-'):
            logger.warning("OpenAI API key format appears invalid (should start with 'sk-')")
    
    def _initialize_client(self) -> openai.OpenAI:
        """Initialize and validate OpenAI client"""
        try:
            client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client created successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to create OpenAI client: {e}")
            raise RuntimeError(f"OpenAI client initialization failed: {e}")
    
    def _health_check(self):
        """Verify OpenAI API connection is working"""
        try:
            # Simple health check - try to access API
            # Just verify the client can make a basic request
            self.client.models.list()
            logger.info("OpenAI API health check passed")
        except Exception as e:
            logger.error(f"OpenAI API health check failed: {e}")
            raise RuntimeError(f"OpenAI service unavailable: {e}")
    
    def _check_rate_limit(self):
        """Check if request is rate limited"""
        if self.rate_limiter.is_rate_limited():
            raise RuntimeError("Rate limit exceeded. Please try again later.")
    
    def create_openai_client(self):
        """
        Create and return an OpenAI client with configured settings.
        
        Returns:
            openai.OpenAI: Configured OpenAI client instance
        """
        # Check rate limit before creating client
        self._check_rate_limit()
        
        if not settings.OPENAI_API_KEY:
            raise ValueError("OpenAI API key is not configured. Please set OPENAI_API_KEY environment variable or create a .env file with your API key.")
        
        return self.client
    
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        model: str = None,  # Allow override, otherwise use config
        max_tokens: int = None,  # Allow override, otherwise use config
        temperature: float = None,  # Allow override, otherwise use config
        mode: str = "lazy"  # "lazy" or "pro"
    ) -> Dict[str, Any]:
        """Create chat completion with rate limiting and error handling"""
        try:
            # Check rate limit
            self._check_rate_limit()
            
            # Validate mode parameter
            if mode not in ["lazy", "pro"]:
                raise ValueError(f"Invalid mode '{mode}'. Mode must be 'lazy' or 'pro'")
            
            # Use config values if not provided
            if model is None:
                model = settings.LAZY_MODEL if mode == "lazy" else settings.PRO_MODEL
            
            if max_tokens is None:
                max_tokens = settings.LAZY_MAX_TOKENS if mode == "lazy" else settings.PRO_MAX_TOKENS
            
            if temperature is None:
                temperature = settings.LAZY_TEMPERATURE if mode == "lazy" else settings.PRO_TEMPERATURE
            
            # Validate inputs
            if not messages or not isinstance(messages, list):
                raise ValueError("Messages must be a non-empty list")
            
            if not isinstance(model, str) or not model:
                raise ValueError("Model must be a non-empty string")
            
            if not (0 <= temperature <= 2):
                raise ValueError("Temperature must be between 0 and 2")
            
            if max_tokens < 1 or max_tokens > 4000:
                raise ValueError("Max tokens must be between 1 and 4000")
            
            # Perform chat completion
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            logger.info(f"Chat completion successful with model {model} (mode: {mode})")
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "mode": mode,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }
            
        except ValueError as e:
            logger.error(f"Validation error in chat completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise RuntimeError(f"Chat completion failed: {e}")
    
    def text_completion(
        self, 
        prompt: str, 
        model: str = None,  # Allow override, otherwise use config
        max_tokens: int = None,  # Allow override, otherwise use config
        temperature: float = None,  # Allow override, otherwise use config
        mode: str = "lazy"  # "lazy" or "pro"
    ) -> Dict[str, Any]:
        """Create text completion using chat completion API (compatible with modern models)"""
        try:
            # Check rate limit
            self._check_rate_limit()
            
            # Validate mode parameter
            if mode not in ["lazy", "pro"]:
                raise ValueError(f"Invalid mode '{mode}'. Mode must be 'lazy' or 'pro'")
            
            # Use config values if not provided
            if model is None:
                model = settings.LAZY_MODEL if mode == "lazy" else settings.PRO_MODEL
            
            if max_tokens is None:
                max_tokens = settings.LAZY_MAX_TOKENS if mode == "lazy" else settings.PRO_MAX_TOKENS
            
            if temperature is None:
                temperature = settings.LAZY_TEMPERATURE if mode == "lazy" else settings.PRO_TEMPERATURE
            
            # Validate inputs
            if not prompt or not isinstance(prompt, str):
                raise ValueError("Prompt must be a non-empty string")
            
            if not isinstance(model, str) or not model:
                raise ValueError("Model must be a non-empty string")
            
            if not (0 <= temperature <= 2):
                raise ValueError("Temperature must be between 0 and 2")
            
            if max_tokens < 1 or max_tokens > 4000:
                raise ValueError("Max tokens must be between 1 and 4000")
            
            # Convert prompt to chat format for compatibility with modern models
            messages = [{"role": "user", "content": prompt}]
            
            # Use chat completion instead of text completion
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            logger.info(f"Text completion successful with model {model} (mode: {mode}) using chat API")
            
            return {
                "content": response.choices[0].message.content if response.choices else "",
                "model": response.model,
                "mode": mode,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                },
                "finish_reason": response.choices[0].finish_reason if response.choices else None
            }
            
        except ValueError as e:
            logger.error(f"Validation error in text completion: {e}")
            raise
        except Exception as e:
            logger.error(f"Text completion failed: {e}")
            raise RuntimeError(f"Text completion failed: {e}")
    
    def list_models(self) -> List[Dict[str, Any]]:
        """List available OpenAI models"""
        try:
            # Check rate limit
            self._check_rate_limit()
            
            response = self.client.models.list()
            
            models = []
            for model in response.data:
                # Only include safe, basic attributes
                models.append({
                    "id": model.id,
                    "object": getattr(model, 'object', 'unknown'),
                    "created": getattr(model, 'created', None),
                    "owned_by": getattr(model, 'owned_by', 'unknown')
                })
            
            logger.info(f"Retrieved {len(models)} models successfully")
            return models
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            # Return empty list instead of crashing
            return []
    
    def health_check(self) -> Dict[str, Any]:
        """Check OpenAI service health"""
        try:
            # Check API connectivity
            self.client.models.list()
            
            # Check rate limiting status
            is_rate_limited = self.rate_limiter.is_rate_limited()
            
            return {
                "status": "healthy",
                "service": "openai",
                "timestamp": time.time(),
                "api_connected": True,
                "rate_limited": is_rate_limited,
                "requests_in_window": len(self.rate_limiter.requests)
            }
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "openai",
                "timestamp": time.time(),
                "error": str(e)
            }
    
    def get_usage_info(self) -> Dict[str, Any]:
        """Get current usage information"""
        return {
            "requests_in_window": len(self.rate_limiter.requests),
            "rate_limited": self.rate_limiter.is_rate_limited(),
            "max_requests_per_minute": MAX_REQUESTS_PER_MINUTE
        }

# Create singleton instance with proper error handling
try:
    openai_service = OpenAIService()
    logger.info("OpenAI service singleton created successfully")
except Exception as e:
    logger.critical(f"Failed to initialize OpenAI service: {e}")
    openai_service = None

# Keep the original function for backward compatibility
def create_openai_client():
    """
    Create and return an OpenAI client with configured settings.
    
    Returns:
        openai.OpenAI: Configured OpenAI client instance
    """
    if openai_service is None:
        raise RuntimeError("OpenAI service is not available")
    
    return openai_service.create_openai_client()

# Export openai_client for backward compatibility with inference files
openai_client = create_openai_client()
