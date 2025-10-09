"""
Rate Limiting Configuration

This file contains all rate limiting configurations for different endpoints
and user tiers. Modify these values to adjust rate limits without changing code.
"""

from typing import Dict
from services.rate_limiter.rate_limiting_service import RateLimitTier, RateLimitConfig


# Rate limit configurations for different endpoints and user tiers
RATE_LIMIT_CONFIGS: Dict[str, Dict[RateLimitTier, RateLimitConfig]] = {
    # Inference endpoints - most critical for cost control
    "inference": {
        RateLimitTier.FREE: RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=50,
            requests_per_day=200,
            burst_limit=3
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests_per_minute=15,
            requests_per_hour=200,
            requests_per_day=1000,
            burst_limit=5
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=1000,
            requests_per_day=5000,
            burst_limit=10
        ),
        RateLimitTier.ENTERPRISE: RateLimitConfig(
            requests_per_minute=200,
            requests_per_hour=5000,
            requests_per_day=25000,
            burst_limit=20
        )
    },
    
    # Authentication endpoints
    "auth": {
        RateLimitTier.FREE: RateLimitConfig(
            requests_per_minute=5,
            requests_per_hour=20,
            requests_per_day=100,
            burst_limit=3
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=50,
            requests_per_day=200,
            burst_limit=5
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests_per_minute=20,
            requests_per_hour=100,
            requests_per_day=500,
            burst_limit=10
        ),
        RateLimitTier.ENTERPRISE: RateLimitConfig(
            requests_per_minute=50,
            requests_per_hour=300,
            requests_per_day=1000,
            burst_limit=20
        )
    },
    
    # Prompt history endpoints
    "prompt_history": {
        RateLimitTier.FREE: RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=500,
            burst_limit=5
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=300,
            requests_per_day=1500,
            burst_limit=10
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=5000,
            burst_limit=20
        ),
        RateLimitTier.ENTERPRISE: RateLimitConfig(
            requests_per_minute=300,
            requests_per_hour=3000,
            requests_per_day=15000,
            burst_limit=50
        )
    },
    
    # Feedback endpoints
    "feedback": {
        RateLimitTier.FREE: RateLimitConfig(
            requests_per_minute=20,
            requests_per_hour=200,
            requests_per_day=1000,
            burst_limit=10
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=600,
            requests_per_day=3000,
            burst_limit=20
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests_per_minute=200,
            requests_per_hour=2000,
            requests_per_day=10000,
            burst_limit=50
        ),
        RateLimitTier.ENTERPRISE: RateLimitConfig(
            requests_per_minute=500,
            requests_per_hour=5000,
            requests_per_day=25000,
            burst_limit=100
        )
    },
    
    # Cache endpoints
    "cache": {
        RateLimitTier.FREE: RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=500,
            burst_limit=5
        ),
        RateLimitTier.BASIC: RateLimitConfig(
            requests_per_minute=30,
            requests_per_hour=300,
            requests_per_day=1500,
            burst_limit=10
        ),
        RateLimitTier.PREMIUM: RateLimitConfig(
            requests_per_minute=100,
            requests_per_hour=1000,
            requests_per_day=5000,
            burst_limit=20
        ),
        RateLimitTier.ENTERPRISE: RateLimitConfig(
            requests_per_minute=300,
            requests_per_hour=3000,
            requests_per_day=15000,
            burst_limit=50
        )
    }
}

# Endpoint mapping for automatic categorization
ENDPOINT_MAPPING = {
    "/api/v1/optimize-prompt": "inference",
    "/api/v1/auth/signup": "auth",
    "/api/v1/auth/login": "auth",
    "/api/v1/auth/logout": "auth",
    "/api/v1/auth/refresh": "auth",
    "/api/v1/auth/profile": "auth",
    "/api/v1/auth/validate": "auth",
    "/api/v1/prompt-history": "prompt_history",
    "/api/v1/feedback": "feedback",
    "/api/v1/cache/stats": "cache",
    "/api/v1/cache/clear": "cache"
}

# Endpoints to bypass rate limiting
BYPASS_ENDPOINTS = [
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/static"
]

# URL patterns to bypass rate limiting
BYPASS_PATTERNS = [
    "/static/",
    "/docs/",
    "/redoc/"
]

# Default user tier (when user tier lookup is not implemented)
DEFAULT_USER_TIER = RateLimitTier.FREE

# Redis configuration for rate limiting
REDIS_CONFIG = {
    "key_prefix": "rate_limit",
    "key_separator": ":",
    "expiration_buffer": 2,  # Multiplier for expiration times (2x window size)
    "connection_timeout": 5,
    "socket_timeout": 5,
    "retry_on_timeout": True
}

# Rate limiting behavior configuration
BEHAVIOR_CONFIG = {
    "allow_on_redis_failure": True,  # Allow requests if Redis is down
    "log_rate_limit_violations": True,
    "log_rate_limit_checks": False,  # Set to True for debugging
    "include_headers": True,  # Include rate limit headers in responses
    "strict_mode": False,  # If True, block requests when rate limiter is unavailable
}

# Cost control settings for inference endpoints
COST_CONTROL_CONFIG = {
    "max_tokens_per_request": 4000,
    "max_requests_per_minute_cost_threshold": 100,  # Alert if exceeded
    "daily_cost_limit_per_user": 10.0,  # USD
    "enable_cost_tracking": True,
    "cost_alert_threshold": 0.8  # Alert when 80% of daily limit reached
}
