from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class FeedbackType(str, Enum):
    """Enum for feedback types"""
    LIKE = "like"
    DISLIKE = "dislike"


class FeedbackCreateRequest(BaseModel):
    """Schema for feedback request (without user_id)"""
    prompt_history_id: str = Field(..., description="ID of the prompt history entry")
    feedback_type: FeedbackType = Field(..., description="Type of feedback (like/dislike)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_history_id": "123e4567-e89b-12d3-a456-426614174000",
                "feedback_type": "like"
            }
        }


class FeedbackCreate(BaseModel):
    """Schema for creating feedback (with user_id)"""
    prompt_history_id: str = Field(..., description="ID of the prompt history entry")
    feedback_type: FeedbackType = Field(..., description="Type of feedback (like/dislike)")
    user_id: str = Field(..., description="ID of the user giving feedback")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_history_id": "123e4567-e89b-12d3-a456-426614174000",
                "feedback_type": "like",
                "user_id": "123e4567-e89b-12d3-a456-426614174001"
            }
        }


class FeedbackResponse(BaseModel):
    """Schema for feedback response"""
    id: str = Field(..., description="Unique feedback ID")
    prompt_history_id: str = Field(..., description="ID of the prompt history entry")
    feedback_type: FeedbackType = Field(..., description="Type of feedback")
    user_id: str = Field(..., description="ID of the user who gave feedback")
    created_at: datetime = Field(..., description="When the feedback was created")
    updated_at: Optional[datetime] = Field(None, description="When the feedback was last updated")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "prompt_history_id": "123e4567-e89b-12d3-a456-426614174000",
                "feedback_type": "like",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }


class FeedbackUpdate(BaseModel):
    """Schema for updating feedback"""
    feedback_type: FeedbackType = Field(..., description="New feedback type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feedback_type": "dislike"
            }
        }


class FeedbackStats(BaseModel):
    """Schema for feedback statistics"""
    prompt_history_id: str = Field(..., description="ID of the prompt history entry")
    total_feedback: int = Field(..., description="Total number of feedback entries")
    likes: int = Field(..., description="Number of likes")
    dislikes: int = Field(..., description="Number of dislikes")
    like_percentage: float = Field(..., description="Percentage of likes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "prompt_history_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_feedback": 25,
                "likes": 20,
                "dislikes": 5,
                "like_percentage": 80.0
            }
        }


class UserFeedbackSummary(BaseModel):
    """Schema for user's feedback summary"""
    user_id: str = Field(..., description="ID of the user")
    total_feedback_given: int = Field(..., description="Total feedback given by user")
    total_likes_given: int = Field(..., description="Total likes given by user")
    total_dislikes_given: int = Field(..., description="Total dislikes given by user")
    recent_feedback: list[FeedbackResponse] = Field(..., description="Recent feedback entries")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "total_feedback_given": 15,
                "total_likes_given": 12,
                "total_dislikes_given": 3,
                "recent_feedback": []
            }
        }
