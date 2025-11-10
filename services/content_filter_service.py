"""
Content Filtering Service
Uses OpenAI Moderation API to detect toxic, harmful, or inappropriate content.
Also detects jailbreak and prompt injection attempts.
"""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from fastapi import HTTPException
from openai import OpenAI
from config import settings

logger = logging.getLogger(__name__)

# Jailbreak and prompt injection patterns
JAILBREAK_PATTERNS = [
    r"ignore\s+(previous|all)\s+instructions?",
    r"forget\s+(previous|all|everything)",
    r"disregard\s+(your|all|previous)",
    r"you\s+are\s+now",
    r"pretend\s+you\s+are",
    r"act\s+as\s+if",
    r"system\s*:\s*you",
    r"new\s+instructions?\s*:",
    r"override\s+previous",
    r"bypass\s+(your|the)\s+(safety|guardrails?|restrictions?)",
    r"jailbreak",
    r"developer\s+mode",
    r"do\s+anything\s+now",
    r"your\s+new\s+instructions?",
    r"as\s+a\s+(developer|admin|hacker)",
]

class ContentFilterService:
    """Service for filtering toxic and inappropriate content using OpenAI Moderation API"""
    
    def __init__(self):
        """Initialize the content filter service with OpenAI client"""
        self.client = None
        if settings.OPENAI_API_KEY:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("Content filter service initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client for content filtering: {e}")
                self.client = None
        else:
            logger.warning("OPENAI_API_KEY not set - content filtering disabled")
    
    def detect_jailbreak(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Detect jailbreak or prompt injection attempts.
        
        Args:
            text: The text to check for jailbreak patterns
            
        Returns:
            Tuple of (is_jailbreak: bool, matched_pattern: Optional[str])
        """
        if not text or not isinstance(text, str):
            return False, None
        
        text_lower = text.lower()
        
        for pattern in JAILBREAK_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                logger.warning(f"Jailbreak detected. Pattern: {pattern}, Text preview: {text[:50]}...")
                return True, pattern
        
        return False, None
    
    def is_toxic(self, text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """
        Check if text contains toxic or harmful content.
        
        Args:
            text: The text to check for toxicity
            
        Returns:
            Tuple of (is_toxic: bool, moderation_result: Optional[Dict])
            - is_toxic: True if content is flagged, False otherwise
            - moderation_result: Full moderation API response if available
        """
        if not self.client:
            logger.warning("Content filter not available - allowing content through")
            return False, None
        
        if not text or not isinstance(text, str) or not text.strip():
            return False, None
        
        try:
            # Call OpenAI Moderation API
            response = self.client.moderations.create(input=text)
            
            # Check if content is flagged
            is_flagged = response.results[0].flagged
            
            # Get categories that were flagged
            categories = response.results[0].categories
            category_scores = response.results[0].category_scores
            
            # Build detailed result
            moderation_result = {
                "flagged": is_flagged,
                "categories": {
                    k: bool(v) for k, v in categories.model_dump().items()
                },
                "category_scores": {
                    k: float(v) for k, v in category_scores.model_dump().items()
                }
            }
            
            if is_flagged:
                flagged_categories = [k for k, v in moderation_result["categories"].items() if v]
                logger.warning(
                    f"Toxic content detected. Categories: {flagged_categories}. "
                    f"Text preview: {text[:50]}..."
                )
            
            return is_flagged, moderation_result
            
        except Exception as e:
            logger.error(f"Error checking content toxicity: {e}")
            # On error, allow content through (fail open)
            # In production, you might want to fail closed for stricter security
            return False, None
    
    def get_toxicity_reason(self, moderation_result: Dict[str, Any]) -> str:
        """
        Get human-readable reason why content was flagged.
        
        Args:
            moderation_result: The moderation result from is_toxic()
            
        Returns:
            Human-readable reason string
        """
        if not moderation_result or not moderation_result.get("flagged"):
            return "Content is safe"
        
        flagged_categories = [
            category for category, flagged in moderation_result["categories"].items()
            if flagged
        ]
        
        # Map categories to user-friendly messages
        category_messages = {
            "hate": "hate speech or discriminatory content",
            "hate/threatening": "threatening hate speech",
            "self-harm": "self-harm or suicide-related content",
            "sexual": "sexual or adult content",
            "sexual/minors": "sexual content involving minors",
            "violence": "violent content",
            "violence/graphic": "graphic violent content"
        }
        
        reasons = []
        for category in flagged_categories:
            if category in category_messages:
                reasons.append(category_messages[category])
            else:
                reasons.append(category.replace("_", " "))
        
        if reasons:
            return f"Content contains: {', '.join(reasons)}"
        
        return "Content violates our usage policies"

# Global instance
content_filter_service = ContentFilterService()

# TODO: Add ip_address and user_agent parameters when implementing IP tracking
def check_content_toxicity(
    text: str,
    user_id: Optional[str] = None
) -> None:
    """
    Check if content is toxic or contains jailbreak attempts.
    Logs violations to Supabase if detected.
    
    Args:
        text: Text to check for toxicity
        user_id: Optional user ID for logging violations
        # TODO: ip_address: Optional IP address for logging
        # TODO: user_agent: Optional user agent for logging
        
    Raises:
        HTTPException: 400 if content is flagged as toxic or jailbreak
    """
    # First check for jailbreak attempts
    is_jailbreak, matched_pattern = content_filter_service.detect_jailbreak(text)
    
    if is_jailbreak:
        # Log jailbreak attempt
        # TODO: Pass ip_address and user_agent when implementing IP tracking
        _log_violation_async(
            user_id=user_id,
            content_preview=text,
            violation_type="jailbreak"
            # TODO: ip_address=ip_address,
            # TODO: user_agent=user_agent
        )
        raise HTTPException(
            status_code=400,
            detail="Content cannot be processed. This request appears to be an attempt to manipulate the system. Please rephrase your request in a safe and appropriate manner."
        )
    
    # Check for toxic content using OpenAI Moderation API
    is_toxic, moderation_result = content_filter_service.is_toxic(text)
    
    if is_toxic:
        # Log toxic content violation
        flagged_categories = moderation_result.get("categories", {}) if moderation_result else {}
        category_scores = moderation_result.get("category_scores", {}) if moderation_result else {}
        
        # TODO: Pass ip_address and user_agent when implementing IP tracking
        _log_violation_async(
            user_id=user_id,
            content_preview=text,
            violation_type="toxic",
            flagged_categories=flagged_categories,
            category_scores=category_scores
            # TODO: ip_address=ip_address,
            # TODO: user_agent=user_agent
        )
        
        reason = content_filter_service.get_toxicity_reason(moderation_result)
        raise HTTPException(
            status_code=400,
            detail=f"Content cannot be processed. {reason}. Please rephrase your request in a safe and appropriate manner."
        )

# TODO: Add ip_address and user_agent parameters when implementing IP tracking
def _log_violation_async(
    user_id: Optional[str],
    content_preview: str,
    violation_type: str,
    flagged_categories: Optional[Dict[str, bool]] = None,
    category_scores: Optional[Dict[str, float]] = None
):
    """
    Asynchronously log a violation to Supabase.
    Non-blocking - doesn't wait for completion.
    """
    try:
        from services.content_violations_service import content_violations_service
        import asyncio
        import threading
        
        if content_violations_service:
            # Run in background thread to avoid blocking
            def log_in_background():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(
                        content_violations_service.log_violation(
                            user_id=user_id,
                            content_preview=content_preview,
                            violation_type=violation_type,
                            flagged_categories=flagged_categories,
                            category_scores=category_scores
                            # TODO: Add ip_address and user_agent when implementing IP tracking
                            # ip_address=ip_address,
                            # user_agent=user_agent
                        )
                    )
                    loop.close()
                except Exception as e:
                    logger.warning(f"Failed to log violation in background: {e}")
            
            thread = threading.Thread(target=log_in_background, daemon=True)
            thread.start()
    except Exception as e:
        # Don't fail the request if logging fails
        logger.warning(f"Failed to log violation asynchronously: {e}")

