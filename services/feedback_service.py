from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from supabase import create_client, Client
from schemas.feedback_schema import (
    FeedbackCreate, 
    FeedbackResponse, 
    FeedbackUpdate, 
    FeedbackStats,
    UserFeedbackSummary,
    FeedbackType
)
from config import settings

# Get logger
logger = logging.getLogger(__name__)

class FeedbackService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Use service role client only if the key is available, otherwise use the regular client
        if settings.SUPABASE_SERVICE_ROLE_KEY:
            self.supabase_service = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
        else:
            logger.warning("SUPABASE_SERVICE_ROLE_KEY not set, using regular client for feedback operations")
            self.supabase_service = supabase_client
    
    def set_authenticated_client(self, authenticated_client: Client):
        """Set the authenticated client for RLS operations"""
        self.supabase = authenticated_client
    
    def create_feedback(self, feedback_data: FeedbackCreate) -> FeedbackResponse:
        """Create a new feedback entry"""
        try:
            logger.info(f"Creating feedback for user {feedback_data.user_id}, prompt {feedback_data.prompt_history_id}, type {feedback_data.feedback_type}")
            
            # Check if feedback already exists for this user and prompt
            existing = self.get_user_feedback_for_prompt(
                feedback_data.user_id, 
                feedback_data.prompt_history_id
            )
            
            if existing:
                logger.info(f"Feedback already exists, updating existing feedback {existing.id}")
                # Update existing feedback
                return self.update_feedback(existing.id, FeedbackUpdate(feedback_type=feedback_data.feedback_type))
            
            # Create new feedback using authenticated client
            insert_data = {
                'prompt_history_id': feedback_data.prompt_history_id,
                'user_id': feedback_data.user_id,
                'feedback_type': feedback_data.feedback_type.value
            }
            logger.info(f"Inserting feedback data: {insert_data}")
            
            result = self.supabase.table('feedback').insert(insert_data).execute()
            
            logger.info(f"Supabase insert result: {result}")
            
            if result.data and len(result.data) > 0:
                feedback = result.data[0]
                logger.info(f"Created feedback {feedback['id']} for user {feedback_data.user_id}")
                return FeedbackResponse(**feedback)
            else:
                logger.error(f"Failed to create feedback: {result}")
                raise Exception("Failed to create feedback - no data returned")
                
        except Exception as e:
            logger.error(f"Error creating feedback: {str(e)}")
            raise
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[FeedbackResponse]:
        """Get feedback by ID"""
        try:
            result = self.supabase_service.table('feedback').select('*').eq('id', feedback_id).execute()
            
            if result.data:
                return FeedbackResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting feedback by ID {feedback_id}: {str(e)}")
            raise
    
    def update_feedback(self, feedback_id: str, feedback_update: FeedbackUpdate) -> Optional[FeedbackResponse]:
        """Update existing feedback"""
        try:
            result = self.supabase.table('feedback').update({
                'feedback_type': feedback_update.feedback_type.value,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('id', feedback_id).execute()
            
            if result.data and len(result.data) > 0:
                feedback = result.data[0]
                logger.info(f"Updated feedback {feedback_id}")
                return FeedbackResponse(**feedback)
            else:
                logger.error(f"Failed to update feedback {feedback_id}: {result}")
                return None
            
        except Exception as e:
            logger.error(f"Error updating feedback {feedback_id}: {str(e)}")
            raise
    
    def delete_feedback(self, feedback_id: str) -> bool:
        """Delete feedback"""
        try:
            result = self.supabase.table('feedback').delete().eq('id', feedback_id).execute()
            
            if result.data:
                logger.info(f"Deleted feedback {feedback_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting feedback {feedback_id}: {str(e)}")
            raise
    
    def get_user_feedback_for_prompt(self, user_id: str, prompt_history_id: str) -> Optional[FeedbackResponse]:
        """Get user's feedback for a specific prompt"""
        try:
            result = self.supabase.table('feedback').select('*').eq('user_id', user_id).eq('prompt_history_id', prompt_history_id).execute()
            
            if result.data:
                return FeedbackResponse(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting user feedback for prompt: {str(e)}")
            raise
    
    def get_feedback_stats_for_prompt(self, prompt_history_id: str) -> FeedbackStats:
        """Get feedback statistics for a specific prompt"""
        try:
            # Get all feedback for this prompt
            result = self.supabase_service.table('feedback').select('feedback_type').eq('prompt_history_id', prompt_history_id).execute()
            
            total_feedback = len(result.data) if result.data else 0
            likes = sum(1 for f in result.data if f['feedback_type'] == 'like') if result.data else 0
            dislikes = total_feedback - likes
            like_percentage = (likes / total_feedback * 100) if total_feedback > 0 else 0.0
            
            return FeedbackStats(
                prompt_history_id=prompt_history_id,
                total_feedback=total_feedback,
                likes=likes,
                dislikes=dislikes,
                like_percentage=round(like_percentage, 2)
            )
            
        except Exception as e:
            logger.error(f"Error getting feedback stats for prompt {prompt_history_id}: {str(e)}")
            raise
    
    def get_user_feedback_summary(self, user_id: str, limit: int = 10) -> UserFeedbackSummary:
        """Get user's feedback summary"""
        try:
            # Get user's feedback
            result = self.supabase_service.table('feedback').select('*').eq('user_id', user_id).order('created_at', desc=True).limit(limit).execute()
            
            feedback_list = [FeedbackResponse(**f) for f in result.data] if result.data else []
            
            total_feedback = len(feedback_list)
            total_likes = sum(1 for f in feedback_list if f.feedback_type == FeedbackType.LIKE)
            total_dislikes = total_feedback - total_likes
            
            return UserFeedbackSummary(
                user_id=user_id,
                total_feedback_given=total_feedback,
                total_likes_given=total_likes,
                total_dislikes_given=total_dislikes,
                recent_feedback=feedback_list
            )
            
        except Exception as e:
            logger.error(f"Error getting user feedback summary for {user_id}: {str(e)}")
            raise
    
    def get_recent_feedback(self, limit: int = 50) -> List[FeedbackResponse]:
        """Get recent feedback across all users"""
        try:
            result = self.supabase_service.table('feedback').select('*').order('created_at', desc=True).limit(limit).execute()
            
            return [FeedbackResponse(**f) for f in result.data] if result.data else []
            
        except Exception as e:
            logger.error(f"Error getting recent feedback: {str(e)}")
            raise
