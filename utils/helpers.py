import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException
import json

def setup_logging(level: str = "INFO") -> logging.Logger:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def format_api_response(
    success: bool = True,
    data: Optional[Dict[str, Any]] = None,
    message: str = "",
    error_code: Optional[str] = None
) -> Dict[str, Any]:
    """Format consistent API responses."""
    response = {
        "success": success,
        "message": message
    }
    
    if data is not None:
        response["data"] = data
    
    if error_code:
        response["error_code"] = error_code
    
    return response

def handle_openai_error(error: Exception) -> HTTPException:
    """Handle OpenAI API errors and return appropriate HTTP exceptions."""
    error_message = str(error)
    
    if "rate limit" in error_message.lower():
        return HTTPException(status_code=429, detail="Rate limit exceeded")
    elif "authentication" in error_message.lower():
        return HTTPException(status_code=401, detail="Authentication failed")
    elif "quota" in error_message.lower():
        return HTTPException(status_code=402, detail="Quota exceeded")
    else:
        return HTTPException(status_code=500, detail="OpenAI service error")

def validate_prompt(prompt: str) -> bool:
    """Validate prompt input."""
    if not prompt or not prompt.strip():
        return False
    
    if len(prompt.strip()) < 3:
        return False
    
    if len(prompt) > 10000:  # 10KB limit
        return False
    
    return True

def sanitize_prompt(prompt: str) -> str:
    """Sanitize prompt input."""
    return prompt.strip()[:10000]  # Limit to 10KB
