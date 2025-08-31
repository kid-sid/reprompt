from fastapi import APIRouter, HTTPException
from schemas.inference_schema import InferenceRequest, InferenceResponse, InferenceType
from models.lazy_inference import optimize_prompt as lazy_optimize_prompt
from models.pro_inference import optimize_prompt as pro_optimize_prompt
from config import settings
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/optimize-prompt", response_model=InferenceResponse)
async def optimize_prompt_endpoint(request: InferenceRequest):
    """Optimize a user prompt using AI to make it more efficient and effective."""

    try:
        logger.info(f"Received {request.inference_type} prompt optimization request: {request.prompt[:50]}...")
        
        # Route to appropriate inference based on type
        if request.inference_type == InferenceType.LAZY:
            optimized_prompt = lazy_optimize_prompt(request.prompt)
            model_used = settings.LAZY_MODEL
        elif request.inference_type == InferenceType.PRO:
            optimized_prompt = pro_optimize_prompt(request.prompt)
            model_used = settings.PRO_MODEL
        else:
            raise HTTPException(status_code=400, detail="Invalid inference type")

        return InferenceResponse(
            output=optimized_prompt,
            tokens_used=0,  # You can implement token counting if needed
            inference_type=request.inference_type.value,
            model_used=model_used
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
            "technique": "Straightforward improvement with basic clarity and specificity"
        },
        "pro": {
            "model": settings.PRO_MODEL,
            "description": "Advanced prompt optimization with sophisticated techniques",
            "technique": "Chain-of-thought, role-based prompting, and advanced strategies"
        }
    }
