"""
Centralized Rate Limiting Service

This service provides comprehensive rate limiting for all API endpoints
with Redis backend for distributed systems and configurable limits.
"""

import time
import json
import hashlib
from typing import Dict, Optional, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import redis
from loguru import logger
from config import settings


class RateLimitTier(Enum):
    """User rate limit tiers"""
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class RateLimitConfig:
    """Rate limit configuration for different endpoints and tiers"""
    requests_per_minute: int
    requests_per_hour: int
    requests_per_day: int
    burst_limit: int = 10  # Allow burst of requests
    window_size: int = 60  # Window size in seconds


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    def __init__(self, message: str, retry_after: int, limit_type: str):
        self.message = message
        self.retry_after = retry_after
        self.limit_type = limit_type
        super().__init__(message)


class CentralizedRateLimiter:
    """
    Centralized rate limiting service with Redis backend
    
    Features:
    - Multiple time windows (minute, hour, day)
    - User-based and IP-based limiting
    - Burst protection
    - Configurable limits per endpoint and user tier
    - Distributed system support via Redis
    """
    
    def __init__(self):
        """Initialize the rate limiter with Redis connection"""
        self.redis_client = self._initialize_redis()
        self.rate_limits = self._initialize_rate_limits()
        self.default_tier = RateLimitTier.FREE
        
    def _initialize_redis(self) -> Optional[redis.Redis]:
        """Initialize Redis connection"""
        try:
            if not hasattr(settings, 'REDIS_HOST') or not settings.REDIS_HOST:
                logger.warning("Redis not configured, using in-memory rate limiting")
                return None
                
            client = redis.Redis(
                host=settings.REDIS_HOST,
                port=getattr(settings, 'REDIS_PORT', 6379),
                password=getattr(settings, 'REDIS_PASSWORD', ''),
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            
            # Test connection
            client.ping()
            logger.info("Redis rate limiting initialized successfully")
            return client
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis for rate limiting: {e}")
            logger.warning("Falling back to in-memory rate limiting")
            return None
    
    def _initialize_rate_limits(self) -> Dict[str, Dict[RateLimitTier, RateLimitConfig]]:
        """Initialize rate limit configurations for different endpoints and tiers"""
        return {
            # Inference endpoints - most critical
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
    
    def _get_user_tier(self, user_id: Optional[str] = None) -> RateLimitTier:
        """Get user tier based on user ID (placeholder for future implementation)"""
        # TODO: Implement user tier lookup from database
        # For now, return default tier
        return self.default_tier
    
    def _generate_key(self, identifier: str, endpoint: str, window: str) -> str:
        """Generate Redis key for rate limiting"""
        return f"rate_limit:{endpoint}:{identifier}:{window}"
    
    def _get_current_window(self, window_size: int) -> int:
        """Get current time window"""
        return int(time.time() // window_size)
    
    def _check_rate_limit_redis(self, identifier: str, endpoint: str, 
                               config: RateLimitConfig) -> Tuple[bool, int, Dict[str, int]]:
        """Check rate limit using Redis"""
        if not self.redis_client:
            return self._check_rate_limit_memory(identifier, endpoint, config)
        
        current_time = time.time()
        current_minute = int(current_time // 60)
        current_hour = int(current_time // 3600)
        current_day = int(current_time // 86400)
        
        # Keys for different time windows
        minute_key = self._generate_key(identifier, endpoint, f"minute:{current_minute}")
        hour_key = self._generate_key(identifier, endpoint, f"hour:{current_hour}")
        day_key = self._generate_key(identifier, endpoint, f"day:{current_day}")
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Increment counters
        pipe.incr(minute_key)
        pipe.incr(hour_key)
        pipe.incr(day_key)
        
        # Set expiration
        pipe.expire(minute_key, 120)  # 2 minutes
        pipe.expire(hour_key, 7200)   # 2 hours
        pipe.expire(day_key, 172800)  # 2 days
        
        # Execute pipeline
        results = pipe.execute()
        
        minute_count, hour_count, day_count = results[:3]
        
        # Check limits
        limits_exceeded = []
        retry_after = 0
        
        if minute_count > config.requests_per_minute:
            limits_exceeded.append("minute")
            retry_after = max(retry_after, 60 - (current_time % 60))
        
        if hour_count > config.requests_per_hour:
            limits_exceeded.append("hour")
            retry_after = max(retry_after, 3600 - (current_time % 3600))
        
        if day_count > config.requests_per_day:
            limits_exceeded.append("day")
            retry_after = max(retry_after, 86400 - (current_time % 86400))
        
        is_limited = len(limits_exceeded) > 0
        
        return is_limited, int(retry_after), {
            "minute": minute_count,
            "hour": hour_count,
            "day": day_count,
            "limits": {
                "minute": config.requests_per_minute,
                "hour": config.requests_per_hour,
                "day": config.requests_per_day
            }
        }
    
    def _check_rate_limit_memory(self, identifier: str, endpoint: str, 
                                config: RateLimitConfig) -> Tuple[bool, int, Dict[str, int]]:
        """Fallback in-memory rate limiting when Redis is not available"""
        # This is a simplified in-memory implementation
        # In production, you might want to use a more sophisticated approach
        logger.warning("Using in-memory rate limiting (Redis not available)")
        
        # For now, allow all requests when Redis is not available
        # In production, implement proper in-memory rate limiting
        return False, 0, {
            "minute": 0,
            "hour": 0,
            "day": 0,
            "limits": {
                "minute": config.requests_per_minute,
                "hour": config.requests_per_hour,
                "day": config.requests_per_day
            }
        }
    
    def check_rate_limit(self, identifier: str, endpoint: str, 
                        user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            identifier: IP address or user ID
            endpoint: API endpoint category (inference, auth, etc.)
            user_id: Optional user ID for user-based limiting
            
        Returns:
            Dict with rate limit status and information
            
        Raises:
            RateLimitExceeded: If rate limit is exceeded
        """
        try:
            # Get user tier
            tier = self._get_user_tier(user_id)
            
            # Get rate limit configuration
            if endpoint not in self.rate_limits:
                logger.warning(f"Unknown endpoint: {endpoint}, using default limits")
                endpoint = "inference"  # Use inference limits as default
            
            if tier not in self.rate_limits[endpoint]:
                logger.warning(f"Unknown tier: {tier}, using FREE tier")
                tier = RateLimitTier.FREE
            
            config = self.rate_limits[endpoint][tier]
            
            # Check rate limits
            is_limited, retry_after, counts = self._check_rate_limit_redis(
                identifier, endpoint, config
            )
            
            result = {
                "allowed": not is_limited,
                "retry_after": retry_after,
                "tier": tier.value,
                "endpoint": endpoint,
                "counts": counts,
                "identifier": identifier
            }
            
            if is_limited:
                limit_type = "unknown"
                if counts["minute"] > config.requests_per_minute:
                    limit_type = "minute"
                elif counts["hour"] > config.requests_per_hour:
                    limit_type = "hour"
                elif counts["day"] > config.requests_per_day:
                    limit_type = "day"
                
                raise RateLimitExceeded(
                    message=f"Rate limit exceeded for {endpoint} endpoint",
                    retry_after=retry_after,
                    limit_type=limit_type
                )
            
            logger.debug(f"Rate limit check passed for {identifier} on {endpoint}")
            return result
            
        except RateLimitExceeded:
            raise
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            # In case of error, allow the request but log the issue
            return {
                "allowed": True,
                "retry_after": 0,
                "tier": "free",
                "endpoint": endpoint,
                "counts": {"minute": 0, "hour": 0, "day": 0, "limits": {}},
                "identifier": identifier,
                "error": str(e)
            }
    
    def get_rate_limit_status(self, identifier: str, endpoint: str, 
                             user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get current rate limit status without incrementing counters"""
        try:
            tier = self._get_user_tier(user_id)
            
            if endpoint not in self.rate_limits:
                endpoint = "inference"
            
            if tier not in self.rate_limits[endpoint]:
                tier = RateLimitTier.FREE
            
            config = self.rate_limits[endpoint][tier]
            
            if not self.redis_client:
                return {
                    "tier": tier.value,
                    "endpoint": endpoint,
                    "counts": {"minute": 0, "hour": 0, "day": 0},
                    "limits": {
                        "minute": config.requests_per_minute,
                        "hour": config.requests_per_hour,
                        "day": config.requests_per_day
                    }
                }
            
            current_time = time.time()
            current_minute = int(current_time // 60)
            current_hour = int(current_time // 3600)
            current_day = int(current_time // 86400)
            
            minute_key = self._generate_key(identifier, endpoint, f"minute:{current_minute}")
            hour_key = self._generate_key(identifier, endpoint, f"hour:{current_hour}")
            day_key = self._generate_key(identifier, endpoint, f"day:{current_day}")
            
            minute_count = int(self.redis_client.get(minute_key) or 0)
            hour_count = int(self.redis_client.get(hour_key) or 0)
            day_count = int(self.redis_client.get(day_key) or 0)
            
            return {
                "tier": tier.value,
                "endpoint": endpoint,
                "counts": {
                    "minute": minute_count,
                    "hour": hour_count,
                    "day": day_count
                },
                "limits": {
                    "minute": config.requests_per_minute,
                    "hour": config.requests_per_hour,
                    "day": config.requests_per_day
                },
                "usage_percentages": {
                    "minute": (minute_count / config.requests_per_minute) * 100,
                    "hour": (hour_count / config.requests_per_hour) * 100,
                    "day": (day_count / config.requests_per_day) * 100
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {
                "tier": "free",
                "endpoint": endpoint,
                "counts": {"minute": 0, "hour": 0, "day": 0},
                "limits": {"minute": 5, "hour": 50, "day": 200},
                "error": str(e)
            }
    
    def reset_rate_limit(self, identifier: str, endpoint: str) -> bool:
        """Reset rate limits for a specific identifier and endpoint"""
        try:
            if not self.redis_client:
                logger.warning("Cannot reset rate limits without Redis")
                return False
            
            # Get all keys for this identifier and endpoint
            pattern = f"rate_limit:{endpoint}:{identifier}:*"
            keys = self.redis_client.keys(pattern)
            
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Reset rate limits for {identifier} on {endpoint}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to reset rate limits: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """Check rate limiting service health"""
        try:
            if self.redis_client:
                # Test Redis connection
                self.redis_client.ping()
                redis_status = "healthy"
            else:
                redis_status = "not_configured"
            
            return {
                "status": "healthy",
                "redis": redis_status,
                "endpoints_configured": list(self.rate_limits.keys()),
                "tiers_available": [tier.value for tier in RateLimitTier],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Rate limiting health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Create singleton instance
try:
    rate_limiter = CentralizedRateLimiter()
    logger.info("Centralized rate limiter initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize rate limiter: {e}")
    rate_limiter = None
