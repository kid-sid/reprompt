from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from schemas.inference_schema import InferenceRequest, InferenceResponse, InferenceType
from schemas.prompt_history_schema import PromptHistoryCreate, InferenceType as HistoryInferenceType
from models.lazy_inference import optimize_prompt as lazy_optimize_prompt
from models.pro_inference import optimize_prompt as pro_optimize_prompt
from services.redis import RedisService
from services.prompt_history_service import prompt_history_service
from services.auth_service import auth_service
from schemas.auth_schema import UserProfile
from config import settings
from utils.helpers import handle_openai_error
import logging
import hashlib
import time

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Redis service
redis_service = RedisService()

# Security scheme
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """Get current authenticated user"""
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

@router.post("/optimize-prompt", response_model=InferenceResponse)
async def optimize_prompt_endpoint(
    request: InferenceRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Optimize a user prompt using AI to make it more efficient and effective.
    
    This endpoint takes a user's prompt and optimizes it using either Lazy or Pro mode
    AI inference. It first checks the Redis cache for existing optimizations before
    calling the AI service. Results are cached for future requests.
    
    Args:
        request (InferenceRequest): Optimization request containing:
            - prompt (str): The user's original prompt to optimize
            - inference_type (InferenceType): Either "lazy" or "pro" mode
            - max_tokens (int, optional): Maximum tokens for the response
    
    Returns:
        InferenceResponse: Optimization response containing:
            - output (str): The optimized prompt
            - tokens_used (int): Number of tokens consumed (currently 0)
            - inference_type (str): The mode used ("lazy" or "pro")
            - model_used (str): The AI model used for optimization
            - cached (bool): Whether the result was served from cache
    
    Raises:
        HTTPException: 400 if invalid inference type is provided
        HTTPException: 500 if internal server error occurs during optimization
        
    Note:
        - Lazy mode uses GPT-3.5 for simple, efficient optimization
        - Pro mode uses GPT-4 for advanced optimization techniques
        - Results are cached in Redis for improved performance
        - Token counting is not yet implemented (returns 0)
    """

    try:
        start_time = time.time()
        logger.info(f"Received {request.inference_type} prompt optimization request from user {current_user.id}: {request.prompt[:50]}...")
        
        # Check cache first
        cached_result = redis_service.get_cached_optimization(request.prompt, request.inference_type.value)
        if cached_result:
            logger.info("Returning cached result")
            
            # Save to history even for cached results
            prompt_history_id = None
            try:
                history_data = PromptHistoryCreate(
                    original_prompt=request.prompt,
                    optimized_prompt=cached_result["optimized_prompt"],
                    inference_type=HistoryInferenceType(request.inference_type.value),
                    model_used=cached_result["model_used"],
                    tokens_used=cached_result["tokens_used"],
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )
                history_response = await prompt_history_service.create_prompt_history(
                    user_id=current_user.id,
                    prompt_data=history_data
                )
                prompt_history_id = history_response.id
            except Exception as e:
                logger.warning(f"Failed to save cached result to history: {e}")
            
            return InferenceResponse(
                output=cached_result["optimized_prompt"],
                tokens_used=cached_result["tokens_used"],
                inference_type=request.inference_type.value,
                model_used=cached_result["model_used"],
                cached=True,
                prompt_history_id=prompt_history_id
            )
        
        # Route to appropriate inference based on type
        if request.inference_type == InferenceType.LAZY:
            optimized_prompt, tokens_used = lazy_optimize_prompt(request.prompt)
            model_used = settings.LAZY_MODEL
        elif request.inference_type == InferenceType.PRO:
            optimized_prompt, tokens_used = pro_optimize_prompt(request.prompt)
            model_used = settings.PRO_MODEL
        else:
            raise HTTPException(status_code=400, detail="Invalid inference type")

        processing_time_ms = int((time.time() - start_time) * 1000)

        # Cache the result
        redis_service.cache_optimized_prompt(
            prompt=request.prompt,
            optimized_prompt=optimized_prompt,
            inference_type=request.inference_type.value,
            model_used=model_used,
            tokens_used=tokens_used
        )

        # Save to prompt history
        prompt_history_id = None
        try:
            history_data = PromptHistoryCreate(
                original_prompt=request.prompt,
                optimized_prompt=optimized_prompt,
                inference_type=HistoryInferenceType(request.inference_type.value),
                model_used=model_used,
                tokens_used=tokens_used,
                processing_time_ms=processing_time_ms
            )
            history_response = await prompt_history_service.create_prompt_history(
                user_id=current_user.id,
                prompt_data=history_data
            )
            prompt_history_id = history_response.id
            logger.info(f"Saved prompt history for user {current_user.id}")
        except Exception as e:
            logger.error(f"Failed to save prompt history: {e}")
            # Don't fail the request if history saving fails

        return InferenceResponse(
            output=optimized_prompt,
            tokens_used=tokens_used,
            inference_type=request.inference_type.value,
            model_used=model_used,
            cached=False,
            prompt_history_id=prompt_history_id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in {request.inference_type} prompt optimization: {str(e)}")
        raise handle_openai_error(e)

@router.get("/health")
async def inference_health():
    """
    Health check for the inference service.
    Provides a simple health check endpoint for the inference service.
    
    Returns:
        dict: Health status containing:
            - status (str): "inference service is healthy"
    
    Raises:
        None: This endpoint does not raise exceptions
    """
    
    return {"status": "inference service is healthy"}

@router.get("/models")
async def get_available_models():
    """
    Get information about available AI models and inference types.
    
    Returns detailed configuration information about the available inference modes,
    including model specifications, parameters, and optimization techniques used
    for each mode.
    
    Returns:
        dict: Model information containing:
            - lazy (dict): Lazy mode configuration:
                - model (str): AI model name (e.g., "gpt-3.5-turbo")
                - description (str): Brief description of the mode
                - technique (str): Optimization technique used
                - max_tokens (int): Maximum tokens for responses
                - temperature (float): AI model temperature setting
            - pro (dict): Pro mode configuration:
                - model (str): AI model name (e.g., "gpt-4")
                - description (str): Brief description of the mode
                - technique (str): Advanced optimization techniques
                - max_tokens (int): Maximum tokens for responses
                - temperature (float): AI model temperature setting
    
    Raises:
        None: This endpoint does not raise exceptions
        
    Note:
        Configuration values are read from the application settings.
        This endpoint is useful for frontend applications to display
        available options and their characteristics to users.
    """
    
    return {
        "lazy": {
            "model": settings.LAZY_MODEL,
            "description": "Simple and efficient prompt optimization",
            "technique": "Straightforward improvement with basic clarity and specificity",
            "max_tokens": settings.LAZY_MAX_TOKENS,
            "temperature": settings.LAZY_TEMPERATURE
        },
        "pro": {
            "model": settings.PRO_MODEL,
            "description": "Advanced prompt optimization with sophisticated techniques",
            "technique": "Chain-of-thought, role-based prompting, and advanced strategies",
            "max_tokens": settings.PRO_MAX_TOKENS,
            "temperature": settings.PRO_TEMPERATURE
        }
    }

@router.get("/cache/stats")
async def get_cache_stats():
    """
    Get Redis cache statistics and information.
    
    Retrieves comprehensive statistics about the Redis cache service,
    including connection status, memory usage, and performance metrics.
    This endpoint is useful for monitoring cache performance and health.
    
    Returns:
        dict: Cache statistics containing:
            - status (str): Cache service status ("available", "unavailable", "error")
            - cache_enabled (bool): Whether caching is enabled
            - redis_version (str): Version of Redis server
            - connected_clients (int): Number of connected Redis clients
            - used_memory_human (str): Human-readable memory usage
            - total_commands_processed (int): Total Redis commands processed
            - message (str): Additional status message (on error/unavailable)
    
    Raises:
        None: This endpoint handles errors gracefully and returns status information
        
    Note:
        - Returns "unavailable" status if Redis is not configured
        - Returns "error" status if Redis connection fails
        - Memory usage is returned in human-readable format (e.g., "1.2M")
        - This endpoint is useful for system monitoring and debugging
    """
    try:
        if not redis_service.redis_client:
            return {
                "status": "unavailable",
                "message": "Redis service not configured",
                "cache_enabled": False
            }
        
        # Get basic Redis info
        info = redis_service.redis_client.info()
        
        return {
            "status": "available",
            "cache_enabled": True,
            "redis_version": info.get("redis_version", "unknown"),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "total_commands_processed": info.get("total_commands_processed", 0)
        }
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return {
            "status": "error",
            "message": str(e),
            "cache_enabled": False
        }

@router.delete("/cache/clear")
async def clear_cache():
    """
    Clear all cached prompt optimizations from Redis.
    
    Removes all cached optimization results from the Redis cache. This operation
    is useful for cache maintenance, testing, or when you need to force fresh
    AI responses for all prompts.
    
    Returns:
        dict: Clear operation result containing:
            - message (str): Success or status message
            - deleted_count (int): Number of cache entries deleted
    
    Raises:
        HTTPException: 503 if Redis service is not available
        HTTPException: 500 if cache clearing operation fails
        
    Note:
        - Only clears keys matching the pattern "prompt_optimization:*"
        - Returns count of 0 if cache is already empty
        - This operation is irreversible - all cached optimizations will be lost
        - Use with caution in production environments as it will impact performance
        - Consider using this endpoint for maintenance windows or testing
    """
    try:
        if not redis_service.redis_client:
            raise HTTPException(status_code=503, detail="Redis service not available")
        
        # Get all keys matching the pattern
        pattern = "prompt_optimization:*"
        keys = redis_service.redis_client.keys(pattern)
        
        if keys:
            deleted = redis_service.redis_client.delete(*keys)
            logger.info(f"Cleared {deleted} cached items")
            return {
                "message": f"Cache cleared successfully. Deleted {deleted} items.",
                "deleted_count": deleted
            }
        else:
            return {
                "message": "Cache is already empty.",
                "deleted_count": 0
            }
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")
