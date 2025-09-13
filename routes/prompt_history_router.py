"""
FastAPI router for prompt history endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import time
from loguru import logger
from utils.helpers import format_api_response
from services.prompt_history_service import prompt_history_service
from services.auth_service import auth_service
from schemas.prompt_history_schema import (
    PromptHistoryCreate, PromptHistoryResponse, PromptHistoryListResponse,
    PromptHistoryUpdate, PromptHistorySearch
)
from schemas.auth_schema import UserProfile

# Security scheme
security = HTTPBearer()

router = APIRouter()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """Get current authenticated user"""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/prompt-history", response_model=PromptHistoryResponse, status_code=status.HTTP_201_CREATED)
async def create_prompt_history(
    prompt_data: PromptHistoryCreate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Create a new prompt history entry"""
    try:
        start_time = time.time()
        
        # Create the prompt history entry
        history_entry = await prompt_history_service.create_prompt_history(
            user_id=current_user.id,
            prompt_data=prompt_data
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"Created prompt history entry for user {current_user.id} in {processing_time}ms")
        
        return history_entry
        
    except Exception as e:
        logger.error(f"Failed to create prompt history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create prompt history entry"
        )

@router.get("/prompt-history", response_model=PromptHistoryListResponse)
async def get_prompt_history(
    page: int = 1,
    page_size: int = 20,
    query: Optional[str] = None,
    inference_type: Optional[str] = None,
    model_used: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get paginated prompt history for the current user"""
    try:
        # Parse date parameters
        from datetime import datetime
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_from format. Use ISO format (e.g., 2024-01-01T00:00:00Z)"
                )
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid date_to format. Use ISO format (e.g., 2024-01-01T00:00:00Z)"
                )
        
        # Validate inference_type
        if inference_type and inference_type not in ["lazy", "pro"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="inference_type must be 'lazy' or 'pro'"
            )
        
        # Create search parameters
        search_params = PromptHistorySearch(
            query=query,
            inference_type=inference_type,
            model_used=model_used,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            page=page,
            page_size=page_size
        )
        
        # Get prompt history
        history_list = await prompt_history_service.get_user_prompt_history(
            user_id=current_user.id,
            search_params=search_params
        )
        
        logger.info(f"Retrieved {len(history_list.items)} prompt history entries for user {current_user.id}")
        return history_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt history"
        )

@router.get("/prompt-history/{history_id}", response_model=PromptHistoryResponse)
async def get_prompt_history_by_id(
    history_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get a specific prompt history entry by ID"""
    try:
        history_entry = await prompt_history_service.get_prompt_history_by_id(
            user_id=current_user.id,
            history_id=history_id
        )
        
        if not history_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt history entry not found"
            )
        
        return history_entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prompt history by ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve prompt history entry"
        )

@router.put("/prompt-history/{history_id}", response_model=PromptHistoryResponse)
async def update_prompt_history(
    history_id: str,
    update_data: PromptHistoryUpdate,
    current_user: UserProfile = Depends(get_current_user)
):
    """Update a prompt history entry"""
    try:
        updated_entry = await prompt_history_service.update_prompt_history(
            user_id=current_user.id,
            history_id=history_id,
            update_data=update_data
        )
        
        if not updated_entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt history entry not found"
            )
        
        logger.info(f"Updated prompt history entry {history_id} for user {current_user.id}")
        return updated_entry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update prompt history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update prompt history entry"
        )

@router.delete("/prompt-history/{history_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prompt_history(
    history_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Delete a prompt history entry"""
    try:
        success = await prompt_history_service.delete_prompt_history(
            user_id=current_user.id,
            history_id=history_id
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prompt history entry not found"
            )
        
        logger.info(f"Deleted prompt history entry {history_id} for user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete prompt history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete prompt history entry"
        )


@router.delete("/prompt-history", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_prompt_history(
    current_user: UserProfile = Depends(get_current_user)
):
    """Delete all prompt history for the current user"""
    try:
        deleted_count = await prompt_history_service.delete_user_history(
            user_id=current_user.id
        )
        
        logger.info(f"Deleted {deleted_count} prompt history entries for user {current_user.id}")
        
    except Exception as e:
        logger.error(f"Failed to delete all prompt history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete prompt history"
        )

@router.get("/prompt-history/health")
async def prompt_history_health_check():
    """Health check for prompt history service"""
    try:
        health_status = await prompt_history_service.health_check()
        return format_api_response(
            success=True,
            data=health_status,
            message="Prompt history service is healthy"
        )
    except Exception as e:
        logger.error(f"Prompt history health check failed: {e}")
        return format_api_response(
            success=False,
            data={
                "status": "unhealthy",
                "service": "prompt_history",
                "error": str(e)
            },
            message="Prompt history service health check failed"
        )
