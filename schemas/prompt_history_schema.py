"""Pydantic schemas for prompt history operations"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class InferenceType(str, Enum):
    LAZY = "lazy"
    PRO = "pro"

class PromptHistoryCreate(BaseModel):
    """Schema for creating a new prompt history entry"""
    original_prompt: str = Field(..., min_length=1, max_length=10000, description="Original user prompt")
    optimized_prompt: str = Field(..., min_length=1, max_length=10000, description="AI-optimized prompt")
    inference_type: InferenceType = Field(..., description="Type of inference used (lazy or pro)")
    model_used: str = Field(..., description="AI model used for optimization")
    tokens_used: int = Field(default=0, ge=0, description="Number of tokens used")
    processing_time_ms: int = Field(default=0, ge=0, description="Processing time in milliseconds")
    
    @validator('original_prompt', 'optimized_prompt')
    def validate_prompt_content(cls, v):
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty or just whitespace')
        return v.strip()
    
    @validator('model_used')
    def validate_model_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Model name cannot be empty')
        return v.strip()

class PromptHistoryResponse(BaseModel):
    """Schema for prompt history response"""
    id: str = Field(..., description="Unique identifier for the prompt history entry")
    user_id: str = Field(..., description="User ID who created this entry")
    original_prompt: str = Field(..., description="Original user prompt")
    optimized_prompt: str = Field(..., description="AI-optimized prompt")
    inference_type: InferenceType = Field(..., description="Type of inference used")
    model_used: str = Field(..., description="AI model used for optimization")
    tokens_used: int = Field(..., description="Number of tokens used")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    created_at: datetime = Field(..., description="When this entry was created")
    updated_at: datetime = Field(..., description="When this entry was last updated")
    
    class Config:
        from_attributes = True

class PromptHistoryListResponse(BaseModel):
    """Schema for paginated prompt history list response"""
    items: List[PromptHistoryResponse] = Field(..., description="List of prompt history entries")
    total_count: int = Field(..., description="Total number of entries")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")
    has_previous: bool = Field(..., description="Whether there are previous pages")

class PromptHistoryUpdate(BaseModel):
    """Schema for updating a prompt history entry"""
    original_prompt: Optional[str] = Field(None, min_length=1, max_length=10000)
    optimized_prompt: Optional[str] = Field(None, min_length=1, max_length=10000)
    inference_type: Optional[InferenceType] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = Field(None, ge=0)
    processing_time_ms: Optional[int] = Field(None, ge=0)
    
    @validator('original_prompt', 'optimized_prompt')
    def validate_prompt_content(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Prompt cannot be empty or just whitespace')
        return v.strip() if v else v
    
    @validator('model_used')
    def validate_model_name(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('Model name cannot be empty')
        return v.strip() if v else v


class PromptHistorySearch(BaseModel):
    """Schema for searching prompt history"""
    query: Optional[str] = Field(None, description="Search query for prompts")
    inference_type: Optional[InferenceType] = Field(None, description="Filter by inference type")
    model_used: Optional[str] = Field(None, description="Filter by model used")
    date_from: Optional[datetime] = Field(None, description="Filter from date")
    date_to: Optional[datetime] = Field(None, description="Filter to date")
    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")
    
    @validator('query')
    def validate_query(cls, v):
        if v is not None and len(v.strip()) < 2:
            raise ValueError('Search query must be at least 2 characters long')
        return v.strip() if v else v
