"""
This middleware automatically applies rate limiting to all API endpoints using the centralized rate limiting service.
"""

import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger
from services.rate_limiter.rate_limiting_service import rate_limiter, RateLimitExceeded


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic rate limiting
    
    Features:
    - Automatic endpoint detection
    - User-based and IP-based limiting
    - Configurable bypass for certain endpoints
    - Proper HTTP headers and error responses
    """
    
    def __init__(
        self,
        app: ASGIApp,
        bypass_endpoints: Optional[list] = None,
        bypass_patterns: Optional[list] = None
    ):
        super().__init__(app)
        self.bypass_endpoints = bypass_endpoints or [
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static"
        ]
        self.bypass_patterns = bypass_patterns or [
            "/static/",
            "/docs/",
            "/redoc/"
        ]
        
        # Endpoint mapping for rate limiting categories
        self.endpoint_mapping = {
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
    
    def _should_bypass(self, path: str) -> bool:
        """Check if the endpoint should bypass rate limiting"""
        # Check exact matches
        if path in self.bypass_endpoints:
            return True
        
        # Check pattern matches
        for pattern in self.bypass_patterns:
            if path.startswith(pattern):
                return True
        
        return False
    
    def _get_endpoint_category(self, path: str) -> str:
        """Get the rate limiting category for an endpoint"""
        # Check exact matches first
        if path in self.endpoint_mapping:
            return self.endpoint_mapping[path]
        
        # Check prefix matches
        for endpoint, category in self.endpoint_mapping.items():
            if path.startswith(endpoint):
                return category
        
        # Default to inference for unknown endpoints
        return "inference"
    
    def _get_identifier(self, request: Request) -> str:
        """Get identifier for rate limiting (IP address or user ID)"""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, 'user_id', None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        # Get real IP address (considering proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        return f"ip:{ip}"
    
    def _add_rate_limit_headers(self, response: Response, rate_limit_info: dict):
        """Add rate limiting headers to response"""
        counts = rate_limit_info.get("counts", {})
        limits = counts.get("limits", {})
        
        # Standard rate limiting headers
        response.headers["X-RateLimit-Limit-Minute"] = str(limits.get("minute", 0))
        response.headers["X-RateLimit-Limit-Hour"] = str(limits.get("hour", 0))
        response.headers["X-RateLimit-Limit-Day"] = str(limits.get("day", 0))
        
        response.headers["X-RateLimit-Remaining-Minute"] = str(
            max(0, limits.get("minute", 0) - counts.get("minute", 0))
        )
        response.headers["X-RateLimit-Remaining-Hour"] = str(
            max(0, limits.get("hour", 0) - counts.get("hour", 0))
        )
        response.headers["X-RateLimit-Remaining-Day"] = str(
            max(0, limits.get("day", 0) - counts.get("day", 0))
        )
        
        response.headers["X-RateLimit-Reset-Minute"] = str(
            int(time.time() // 60 + 1) * 60
        )
        response.headers["X-RateLimit-Reset-Hour"] = str(
            int(time.time() // 3600 + 1) * 3600
        )
        response.headers["X-RateLimit-Reset-Day"] = str(
            int(time.time() // 86400 + 1) * 86400
        )
        
        # User tier information
        response.headers["X-RateLimit-Tier"] = rate_limit_info.get("tier", "free")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through rate limiting middleware"""
        
        # Skip rate limiting for bypassed endpoints
        if self._should_bypass(request.url.path):
            return await call_next(request)
        
        # Skip if rate limiter is not available
        if not rate_limiter:
            logger.warning("Rate limiter not available, skipping rate limiting")
            return await call_next(request)
        
        try:
            # Get identifier and endpoint category
            identifier = self._get_identifier(request)
            endpoint_category = self._get_endpoint_category(request.url.path)
            
            # Get user ID if available
            user_id = getattr(request.state, 'user_id', None)
            
            # Check rate limit
            rate_limit_info = rate_limiter.check_rate_limit(
                identifier=identifier,
                endpoint=endpoint_category,
                user_id=user_id
            )
            
            # Process the request
            response = await call_next(request)
            
            # Add rate limiting headers to successful responses
            if response.status_code < 400:
                self._add_rate_limit_headers(response, rate_limit_info)
            
            return response
            
        except RateLimitExceeded as e:
            logger.warning(f"Rate limit exceeded: {e.message}")
            
            # Create error response
            error_response = JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": e.message,
                    "retry_after": e.retry_after,
                    "limit_type": e.limit_type,
                    "endpoint": endpoint_category,
                    "identifier": identifier
                }
            )
            
            # Add rate limiting headers to error response
            if 'rate_limit_info' in locals():
                self._add_rate_limit_headers(error_response, rate_limit_info)
            
            # Add Retry-After header
            error_response.headers["Retry-After"] = str(e.retry_after)
            
            return error_response
            
        except Exception as e:
            logger.error(f"Rate limiting middleware error: {e}")
            # In case of error, allow the request to proceed
            return await call_next(request)


def create_rate_limiting_middleware(
    bypass_endpoints: Optional[list] = None,
    bypass_patterns: Optional[list] = None
) -> RateLimitingMiddleware:
    """
    Factory function to create rate limiting middleware with custom configuration
    
    Args:
        bypass_endpoints: List of endpoints to bypass rate limiting
        bypass_patterns: List of URL patterns to bypass rate limiting
        
    Returns:
        Configured RateLimitingMiddleware instance
    """
    def middleware_factory(app: ASGIApp) -> RateLimitingMiddleware:
        return RateLimitingMiddleware(
            app=app,
            bypass_endpoints=bypass_endpoints,
            bypass_patterns=bypass_patterns
        )
    
    return middleware_factory
