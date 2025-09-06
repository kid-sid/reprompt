from fastapi import APIRouter, HTTPException
from schemas.inference_schema import InferenceRequest, InferenceResponse, InferenceType
from models.lazy_inference import optimize_prompt as lazy_optimize_prompt
from models.pro_inference import optimize_prompt as pro_optimize_prompt
from services.redis import RedisService
from config import settings
import logging
import hashlib

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Redis service
redis_service = RedisService()

@router.post("/optimize-prompt", response_model=InferenceResponse)
async def optimize_prompt_endpoint(request: InferenceRequest):
    """Optimize a user prompt using AI to make it more efficient and effective."""

    try:
        logger.info(f"Received {request.inference_type} prompt optimization request: {request.prompt[:50]}...")
        
        # Check cache first
        cached_result = redis_service.get_cached_optimization(request.prompt, request.inference_type.value)
        if cached_result:
            logger.info("Returning cached result")
            return InferenceResponse(
                output=cached_result["optimized_prompt"],
                tokens_used=cached_result["tokens_used"],
                inference_type=request.inference_type.value,
                model_used=cached_result["model_used"],
                cached=True
            )
        
        # Route to appropriate inference based on type
        if request.inference_type == InferenceType.LAZY:
            optimized_prompt = lazy_optimize_prompt(request.prompt)
            model_used = settings.LAZY_MODEL
        elif request.inference_type == InferenceType.PRO:
            optimized_prompt = pro_optimize_prompt(request.prompt)
            model_used = settings.PRO_MODEL
        else:
            raise HTTPException(status_code=400, detail="Invalid inference type")

        # Cache the result
        redis_service.cache_optimized_prompt(
            prompt=request.prompt,
            optimized_prompt=optimized_prompt,
            inference_type=request.inference_type.value,
            model_used=model_used,
            tokens_used=0  # You can implement token counting if needed
        )

        return InferenceResponse(
            output=optimized_prompt,
            tokens_used=0,  # You can implement token counting if needed
            inference_type=request.inference_type.value,
            model_used=model_used,
            cached=False
        )
    
    except Exception as e:
        logger.error(f"Error in {request.inference_type} prompt optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def inference_health():
    """Health check for the inference service."""
    
    return {"status": "inference service is healthy"}

@router.get("/models")
async def get_available_models():
    """Get information about available models and inference types."""
    
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
    """Get cache statistics and information."""
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
    """Clear all cached prompt optimizations."""
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
