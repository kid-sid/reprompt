from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
import logging
from services.feedback_service import FeedbackService
from routes.auth_router import get_current_user
from schemas.feedback_schema import (
    FeedbackCreateRequest,
    FeedbackCreate, 
    FeedbackResponse, 
    FeedbackUpdate, 
    FeedbackStats,
    UserFeedbackSummary
)
from schemas.auth_schema import UserProfile
from utils.helpers import format_api_response

# Get logger
logger = logging.getLogger(__name__)

router = APIRouter()

def get_feedback_service() -> FeedbackService:
    """Dependency to get feedback service"""
    from main import get_supabase_client
    supabase_client = get_supabase_client()
    return FeedbackService(supabase_client)

def get_authenticated_feedback_service(current_user: UserProfile) -> FeedbackService:
    """Dependency to get feedback service with authenticated client"""
    from main import get_supabase_client
    from supabase import create_client
    from config import settings
    
    # Create authenticated client with user's JWT token
    # For now, we'll use the service role client to bypass RLS
    if settings.SUPABASE_SERVICE_ROLE_KEY:
        authenticated_client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    else:
        # Fallback to regular client
        authenticated_client = get_supabase_client()
    
    feedback_service = FeedbackService(authenticated_client)
    return feedback_service

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_request: FeedbackCreateRequest,
    current_user: UserProfile = Depends(get_current_user)
):
    """Create or update feedback for a prompt"""
    try:
        # Get authenticated feedback service
        feedback_service = get_authenticated_feedback_service(current_user)
        
        # Create FeedbackCreate object with user_id from authenticated user
        feedback_data = FeedbackCreate(
            prompt_history_id=feedback_request.prompt_history_id,
            feedback_type=feedback_request.feedback_type,
            user_id=current_user.id
        )
        
        feedback = feedback_service.create_feedback(feedback_data)
        logger.info(f"Created feedback {feedback.id} for user {current_user.id}")
        return feedback
        
    except Exception as e:
        logger.error(f"Error creating feedback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create feedback"
        )

@router.get("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def get_feedback(
    feedback_id: str,
    current_user: UserProfile = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get feedback by ID"""
    try:
        feedback = feedback_service.get_feedback_by_id(feedback_id)
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        # Ensure user can only access their own feedback
        if feedback.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own feedback"
            )
        
        return feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback {feedback_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feedback"
        )

@router.put("/feedback/{feedback_id}", response_model=FeedbackResponse)
async def update_feedback(
    feedback_id: str,
    feedback_update: FeedbackUpdate,
    current_user: UserProfile = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Update existing feedback"""
    try:
        # First check if feedback exists and belongs to user
        existing_feedback = feedback_service.get_feedback_by_id(feedback_id)
        
        if not existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        if existing_feedback.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own feedback"
            )
        
        updated_feedback = feedback_service.update_feedback(feedback_id, feedback_update)
        
        if not updated_feedback:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update feedback"
            )
        
        logger.info(f"Updated feedback {feedback_id} for user {current_user.id}")
        return updated_feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback {feedback_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update feedback"
        )

@router.delete("/feedback/{feedback_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feedback(
    feedback_id: str,
    current_user: UserProfile = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Delete feedback"""
    try:
        # First check if feedback exists and belongs to user
        existing_feedback = feedback_service.get_feedback_by_id(feedback_id)
        
        if not existing_feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        if existing_feedback.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own feedback"
            )
        
        success = feedback_service.delete_feedback(feedback_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete feedback"
            )
        
        logger.info(f"Deleted feedback {feedback_id} for user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting feedback {feedback_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete feedback"
        )

@router.get("/feedback/stats/{prompt_history_id}", response_model=FeedbackStats)
async def get_feedback_stats(
    prompt_history_id: str,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get feedback statistics for a specific prompt"""
    try:
        stats = feedback_service.get_feedback_stats_for_prompt(prompt_history_id)
        return stats
        
    except Exception as e:
        logger.error(f"Error getting feedback stats for {prompt_history_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get feedback statistics"
        )

@router.get("/feedback/user/summary", response_model=UserFeedbackSummary)
async def get_user_feedback_summary(
    current_user: UserProfile = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get current user's feedback summary"""
    try:
        summary = feedback_service.get_user_feedback_summary(current_user.id)
        return summary
        
    except Exception as e:
        logger.error(f"Error getting user feedback summary for {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user feedback summary"
        )

@router.get("/feedback/user/{prompt_history_id}", response_model=FeedbackResponse)
async def get_user_feedback_for_prompt(
    prompt_history_id: str,
    current_user: UserProfile = Depends(get_current_user),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """Get current user's feedback for a specific prompt"""
    try:
        feedback = feedback_service.get_user_feedback_for_prompt(current_user.id, prompt_history_id)
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No feedback found for this prompt"
            )
        
        return feedback
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user feedback for prompt {prompt_history_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user feedback"
        )
