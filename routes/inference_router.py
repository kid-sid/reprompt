from fastapi import APIRouter, HTTPException
from schemas.inference_schema import InferenceRequest, InferenceResponse
from models.inference import optimize_prompt
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/optimize-prompt", response_model=InferenceResponse)
async def optimize_prompt_endpoint(request: InferenceRequest):
    """Optimize a user prompt using AI to make it more efficient and effective."""

    try:
        logger.info(f"Received prompt optimization request: {request.prompt[:50]}...")
        
        optimized_prompt = optimize_prompt(request.prompt)

        return InferenceResponse(
            output=optimized_prompt,
            tokens_used=0  # You can implement token counting if needed
        )
    
    except Exception as e:
        logger.error(f"Error in prompt optimization: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/health")
async def inference_health():
    """Health check for the inference service."""
    
    return {"status": "inference service is healthy"}
