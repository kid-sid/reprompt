import logging
from typing import Dict, Any, Optional, Union
from fastapi import HTTPException
import json

# Configuration constants
DEFAULT_PROMPT_MIN_LENGTH = 3
DEFAULT_PROMPT_MAX_LENGTH = 10000  # 10KB

def format_api_response(
    success: bool = True,
    data: Optional[Dict[str, Any]] = None,
    message: str = "",
    error_code: Optional[str] = None,
    status_code: int = 200
) -> Dict[str, Any]:
    """
    Format consistent API responses.
    
    Args:
        success: Whether the operation was successful
        data: Response data payload
        message: Human-readable message
        error_code: Machine-readable error code
        status_code: HTTP status code
    
    Returns:
        Formatted API response dictionary
    """
    response = {
        "success": success,
        "message": message,
        "status_code": status_code
    }
    
    if data is not None:
        response["data"] = data
    
    if error_code:
        response["error_code"] = error_code
    
    return response

def handle_openai_error(error: Exception) -> HTTPException:
    """
    Handle OpenAI API errors and return appropriate HTTP exceptions.
    
    Args:
        error: The exception that occurred
    
    Returns:
        HTTPException with appropriate status code and detail
    """
    error_message = str(error).lower()
    
    # Rate limiting
    if any(term in error_message for term in ["rate limit", "too many requests"]):
        return HTTPException(
            status_code=429, 
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Authentication issues
    elif any(term in error_message for term in ["authentication", "invalid api key", "unauthorized"]):
        return HTTPException(
            status_code=401, 
            detail="Authentication failed. Please check your API key."
        )
    
    # Quota exceeded
    elif any(term in error_message for term in ["quota", "billing", "payment"]):
        return HTTPException(
            status_code=402, 
            detail="Quota exceeded. Please check your billing status."
        )
    
    # Model not found
    elif any(term in error_message for term in ["model not found", "does not exist"]):
        return HTTPException(
            status_code=400, 
            detail="Invalid model specified."
        )
    
    # Content filtering
    elif any(term in error_message for term in ["content filter", "policy violation"]):
        return HTTPException(
            status_code=400, 
            detail="Content violates usage policies."
        )
    
    # Default error
    else:
        return HTTPException(
            status_code=500, 
            detail=f"OpenAI service error: {str(error)}"
        )

def validate_prompt(
    prompt: Any, 
    min_length: int = DEFAULT_PROMPT_MIN_LENGTH,
    max_length: int = DEFAULT_PROMPT_MAX_LENGTH
) -> bool:
    """
    Validate prompt input.
    
    Args:
        prompt: The prompt to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
    
    Returns:
        True if valid, False otherwise
    """
    try:
        # Type validation
        if not isinstance(prompt, str):
            return False
        
        # Content validation
        if not prompt or not prompt.strip():
            return False
        
        stripped_prompt = prompt.strip()
        
        # Length validation
        if len(stripped_prompt) < min_length:
            return False
        
        if len(stripped_prompt) > max_length:
            return False
        
        return True
        
    except Exception:
        # If any validation fails, return False
        return False

def sanitize_prompt(
    prompt: Any, 
    max_length: int = DEFAULT_PROMPT_MAX_LENGTH
) -> str:
    """
    Sanitize prompt input.
    
    Args:
        prompt: The prompt to sanitize
        max_length: Maximum allowed length
    
    Returns:
        Sanitized prompt string
    """
    try:
        # Convert to string if needed
        if not isinstance(prompt, str):
            prompt = str(prompt) if prompt is not None else ""
        
        # Strip whitespace and limit length
        sanitized = prompt.strip()[:max_length]
        
        return sanitized
        
    except Exception:
        return ""

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with error handling.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
    
    Returns:
        Parsed JSON object or default value
    """
    try:
        if not isinstance(json_str, str):
            return default
        
        return json.loads(json_str)
        
    except (json.JSONDecodeError, TypeError):
        return default

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to specified length with suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
    
    Returns:
        Truncated text
    """
    try:
        if not isinstance(text, str):
            return str(text)[:max_length]
        
        if len(text) <= max_length:
            return text
        
        return text[:max_length - len(suffix)] + suffix
        
    except Exception:
        return str(text)[:max_length] if text else ""
