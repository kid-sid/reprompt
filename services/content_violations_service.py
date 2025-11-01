"""
Content Violations Service
Tracks toxic content and jailbreak attempts in Supabase.
"""
import logging
from typing import Optional, Dict, Any, List
from supabase import Client
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentViolationsService:
    """Service for logging content violations to Supabase"""
    
    def __init__(self, supabase_client: Client):
        """
        Initialize the content violations service.
        
        Args:
            supabase_client: Authenticated Supabase client
        """
        self.supabase = supabase_client
        logger.info("ContentViolationsService initialized")
    
    async def log_violation(
        self,
        user_id: Optional[str],
        content_preview: str,
        violation_type: str,
        flagged_categories: Optional[Dict[str, bool]] = None,
        category_scores: Optional[Dict[str, float]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Log a content violation to the database.
        
        Args:
            user_id: User ID (None if unauthenticated)
            content_preview: First 500 chars of the content (sanitized)
            violation_type: Type of violation ('toxic', 'jailbreak', 'prompt_injection', etc.)
            flagged_categories: Categories flagged by moderation API
            category_scores: Scores for each category
            ip_address: IP address of the request (optional)
            user_agent: User agent string (optional)
            
        Returns:
            True if logging was successful, False otherwise
        """
        try:
            # Sanitize content preview (max 500 chars)
            sanitized_preview = content_preview[:500] if content_preview else ""
            
            # Prepare violation data
            violation_data = {
                "user_id": user_id,
                "content_preview": sanitized_preview,
                "violation_type": violation_type,
                "flagged_categories": flagged_categories,
                "category_scores": category_scores,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.info(
                f"Logging violation: type={violation_type}, user_id={user_id}, "
                f"preview={sanitized_preview[:50]}..."
            )
            
            # Insert into database
            response = self.supabase.table("content_violations").insert(violation_data).execute()
            
            if response.data:
                logger.info(f"Successfully logged violation: {response.data[0].get('id')}")
                return True
            else:
                logger.warning(f"Violation logged but no data returned: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging content violation: {e}")
            # Don't raise - logging failures shouldn't break the request
            return False
    
    async def get_user_violations(
        self,
        user_id: str,
        limit: int = 100,
        violation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get violations for a specific user.
        
        Args:
            user_id: User ID
            limit: Maximum number of violations to return
            violation_type: Filter by violation type (optional)
            
        Returns:
            List of violation records
        """
        try:
            query = self.supabase.table("content_violations").select("*").eq("user_id", user_id)
            
            if violation_type:
                query = query.eq("violation_type", violation_type)
            
            query = query.order("created_at", desc=True).limit(limit)
            
            response = query.execute()
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching user violations: {e}")
            return []
    
    async def get_user_violation_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get violation statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with violation statistics
        """
        try:
            response = self.supabase.table("user_violation_stats").select("*").eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]
            
            # Return empty stats if no violations
            return {
                "user_id": user_id,
                "total_violations": 0,
                "toxic_count": 0,
                "jailbreak_count": 0,
                "injection_count": 0,
                "first_violation": None,
                "last_violation": None
            }
            
        except Exception as e:
            logger.error(f"Error fetching violation stats: {e}")
            return {
                "user_id": user_id,
                "total_violations": 0,
                "toxic_count": 0,
                "jailbreak_count": 0,
                "injection_count": 0
            }
    
    async def get_recent_violations(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent violations across all users (for admin/monitoring).
        
        Args:
            limit: Maximum number of violations to return
            
        Returns:
            List of recent violation records
        """
        try:
            response = (
                self.supabase.table("content_violations")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Error fetching recent violations: {e}")
            return []

# Global instance (will be initialized with Supabase client)
content_violations_service: Optional[ContentViolationsService] = None

def initialize_violations_service(supabase_client: Client):
    """Initialize the global content violations service"""
    global content_violations_service
    content_violations_service = ContentViolationsService(supabase_client)
    logger.info("Global content violations service initialized")

