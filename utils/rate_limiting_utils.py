"""
Rate Limiting Utilities

Helper functions for integrating rate limiting into existing routers
and providing rate limit information to frontend applications.
"""

from typing import Dict, Any, Optional
from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from services.rate_limiting_service import rate_limiter, RateLimitExceeded
from services.auth_service import auth_service
from schemas.auth_schema import UserProfile


def get_rate_limit_info(request: Request, endpoint: str, user: Optional[UserProfile] = None) -> Dict[str, Any]:
    """
    Get rate limit information for an endpoint
    
    Args:
        request: FastAPI request object
        endpoint: Endpoint category (inference, auth, etc.)
        user: Optional authenticated user
        
    Returns:
        Dict with rate limit status and information
    """
    if not rate_limiter:
        return {
            "allowed": True,
            "message": "Rate limiting not available",
            "tier": "free",
            "counts": {"minute": 0, "hour": 0, "day": 0},
            "limits": {"minute": 0, "hour": 0, "day": 0}
        }
    
    try:
        # Get identifier
        user_id = user.id if user else None
        identifier = f"user:{user_id}" if user_id else f"ip:{request.client.host}"
        
        # Get rate limit status
        status = rate_limiter.get_rate_limit_status(
            identifier=identifier,
            endpoint=endpoint,
            user_id=user_id
        )
        
        return {
            "allowed": True,
            "message": "Rate limit check successful",
            "tier": status.get("tier", "free"),
            "counts": status.get("counts", {}),
            "limits": status.get("limits", {}),
            "usage_percentages": status.get("usage_percentages", {})
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit info: {e}")
        return {
            "allowed": True,
            "message": f"Rate limit check failed: {str(e)}",
            "tier": "free",
            "counts": {"minute": 0, "hour": 0, "day": 0},
            "limits": {"minute": 0, "hour": 0, "day": 0}
        }


def check_rate_limit_for_user(request: Request, endpoint: str, user: UserProfile) -> None:
    """
    Check rate limit for authenticated user and raise exception if exceeded
    
    Args:
        request: FastAPI request object
        endpoint: Endpoint category
        user: Authenticated user
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    if not rate_limiter:
        return
    
    try:
        identifier = f"user:{user.id}"
        
        rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            user_id=user.id
        )
        
    except RateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for user {user.id}: {e.message}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": e.message,
                "retry_after": e.retry_after,
                "limit_type": e.limit_type
            },
            headers={"Retry-After": str(e.retry_after)}
        )
    except Exception as e:
        logger.error(f"Rate limit check failed for user {user.id}: {e}")
        # Don't block the request if rate limiting fails


def check_rate_limit_for_ip(request: Request, endpoint: str) -> None:
    """
    Check rate limit for IP address and raise exception if exceeded
    
    Args:
        request: FastAPI request object
        endpoint: Endpoint category
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    if not rate_limiter:
        return
    
    try:
        # Get real IP address
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"
        
        identifier = f"ip:{ip}"
        
        rate_limiter.check_rate_limit(
            identifier=identifier,
            endpoint=endpoint,
            user_id=None
        )
        
    except RateLimitExceeded as e:
        logger.warning(f"Rate limit exceeded for IP {ip}: {e.message}")
        raise HTTPException(
            status_code=429,
            detail={
                "error": "rate_limit_exceeded",
                "message": e.message,
                "retry_after": e.retry_after,
                "limit_type": e.limit_type
            },
            headers={"Retry-After": str(e.retry_after)}
        )
    except Exception as e:
        logger.error(f"Rate limit check failed for IP: {e}")
        # Don't block the request if rate limiting fails


def get_user_rate_limit_status(user: UserProfile, endpoint: str) -> Dict[str, Any]:
    """
    Get detailed rate limit status for a user
    
    Args:
        user: Authenticated user
        endpoint: Endpoint category
        
    Returns:
        Dict with detailed rate limit information
    """
    if not rate_limiter:
        return {
            "tier": "free",
            "endpoint": endpoint,
            "counts": {"minute": 0, "hour": 0, "day": 0},
            "limits": {"minute": 0, "hour": 0, "day": 0},
            "usage_percentages": {"minute": 0, "hour": 0, "day": 0},
            "message": "Rate limiting not available"
        }
    
    try:
        identifier = f"user:{user.id}"
        
        status = rate_limiter.get_rate_limit_status(
            identifier=identifier,
            endpoint=endpoint,
            user_id=user.id
        )
        
        return {
            **status,
            "message": "Rate limit status retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit status for user {user.id}: {e}")
        return {
            "tier": "free",
            "endpoint": endpoint,
            "counts": {"minute": 0, "hour": 0, "day": 0},
            "limits": {"minute": 0, "hour": 0, "day": 0},
            "usage_percentages": {"minute": 0, "hour": 0, "day": 0},
            "error": str(e)
        }


def reset_user_rate_limits(user: UserProfile, endpoint: str) -> bool:
    """
    Reset rate limits for a user (admin function)
    
    Args:
        user: User to reset limits for
        endpoint: Endpoint category
        
    Returns:
        True if successful, False otherwise
    """
    if not rate_limiter:
        return False
    
    try:
        identifier = f"user:{user.id}"
        return rate_limiter.reset_rate_limit(identifier, endpoint)
        
    except Exception as e:
        logger.error(f"Failed to reset rate limits for user {user.id}: {e}")
        return False


def format_rate_limit_message(rate_limit_info: Dict[str, Any]) -> str:
    """
    Format rate limit information into a user-friendly message
    
    Args:
        rate_limit_info: Rate limit information dict
        
    Returns:
        Formatted message string
    """
    tier = rate_limit_info.get("tier", "free")
    counts = rate_limit_info.get("counts", {})
    limits = rate_limit_info.get("limits", {})
    
    message = f"Rate limit status for {tier} tier:\n"
    
    for period in ["minute", "hour", "day"]:
        count = counts.get(period, 0)
        limit = limits.get(period, 0)
        percentage = (count / limit * 100) if limit > 0 else 0
        
        message += f"- {period.capitalize()}: {count}/{limit} ({percentage:.1f}%)\n"
    
    return message.strip()


# Dependency for getting current user with rate limiting
security = HTTPBearer()

async def get_current_user_with_rate_limit(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserProfile:
    """
    Get current authenticated user with rate limiting check
    
    This can be used as a dependency in FastAPI routes
    """
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
