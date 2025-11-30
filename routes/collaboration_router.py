"""
FastAPI routes for prompt collaboration workflows.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger

from schemas.auth_schema import UserProfile
from schemas.collaboration_schema import (
    CollaborationDetailsResponse,
    CollaborationPromptResponse,
    CollaborationShareRequest,
    CollaborationShareResponse,
    CommentCreate,
    CommentResponse,
    CommentUpdate,
    HandoffNotesUpdate,
)
from schemas.prompt_history_schema import PromptHistoryResponse
from services.auth_service import auth_service
from services.collaboration_service import collaboration_service

security = HTTPBearer()
router = APIRouter()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UserProfile:
    """Resolve and validate the current authenticated user."""
    try:
        user = await auth_service.get_current_user(credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception as exc:
        logger.error(f"Authentication failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/collaboration/{history_id}/share",
    response_model=CollaborationShareResponse,
    status_code=status.HTTP_200_OK,
)
async def create_share_link(
    history_id: str,
    share_request: CollaborationShareRequest,
    current_user: UserProfile = Depends(get_current_user),
):
    """Create or update a collaboration share link for a prompt history entry."""
    try:
        return await collaboration_service.create_or_update_share(
            owner_id=current_user.id,
            history_id=history_id,
            share_request=share_request,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to create share link: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create share link",
        )


@router.get(
    "/collaboration/history/{history_id}",
    response_model=Optional[CollaborationDetailsResponse],
)
async def get_collaboration_by_history(
    history_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Return collaboration metadata for a prompt history entry, if available."""
    try:
        return await collaboration_service.get_collaboration_for_history(history_id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to fetch collaboration by history: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch collaboration",
        )


@router.get(
    "/collaboration/share/{share_token}",
    response_model=CollaborationPromptResponse,
)
async def resolve_share_token(share_token: str):
    """Resolve a share token and return prompt details without requiring auth."""
    try:
        return await collaboration_service.resolve_share_token(share_token)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to resolve share token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve share token",
        )


@router.post(
    "/collaboration/share/{share_token}/accept",
    response_model=CollaborationPromptResponse,
    status_code=status.HTTP_200_OK,
)
async def accept_share_token(
    share_token: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Accept a share token and join the collaboration as the current user."""
    try:
        return await collaboration_service.accept_share_token(
            user_id=current_user.id,
            email=current_user.email,
            share_token=share_token,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to accept share token: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept share token",
        )


@router.get(
    "/collaboration/{collaboration_id}",
    response_model=CollaborationDetailsResponse,
)
async def get_collaboration_details(
    collaboration_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Return collaboration metadata and member list."""
    try:
        return await collaboration_service.get_collaboration_details(collaboration_id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to fetch collaboration details: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch collaboration details",
        )


@router.get(
    "/collaboration/{collaboration_id}/comments",
    response_model=list[CommentResponse],
)
async def get_collaboration_comments(
    collaboration_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """List comments for the collaboration."""
    try:
        return await collaboration_service.get_comments(collaboration_id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to fetch comments: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch comments",
        )


@router.post(
    "/collaboration/{collaboration_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_collaboration_comment(
    collaboration_id: str,
    comment: CommentCreate,
    current_user: UserProfile = Depends(get_current_user),
):
    """Add a new inline comment to the collaboration."""
    try:
        return await collaboration_service.add_comment(collaboration_id, current_user.id, comment)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to add comment: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add comment",
        )


@router.patch(
    "/collaboration/{collaboration_id}/comments/{comment_id}",
    response_model=CommentResponse,
)
async def update_collaboration_comment(
    collaboration_id: str,
    comment_id: str,
    updates: CommentUpdate,
    current_user: UserProfile = Depends(get_current_user),
):
    """Update a comment body or resolution status."""
    try:
        return await collaboration_service.update_comment(comment_id, current_user.id, updates)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to update comment: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update comment",
        )


@router.delete(
    "/collaboration/{collaboration_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_collaboration_comment(
    collaboration_id: str,
    comment_id: str,
    current_user: UserProfile = Depends(get_current_user),
):
    """Delete a comment."""
    try:
        await collaboration_service.delete_comment(comment_id, current_user.id)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to delete comment: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment",
        )


@router.put(
    "/collaboration/{collaboration_id}/handoff",
    response_model=PromptHistoryResponse,
)
async def update_handoff_notes(
    collaboration_id: str,
    payload: HandoffNotesUpdate,
    current_user: UserProfile = Depends(get_current_user),
):
    """Update collaboration handoff notes for a prompt."""
    try:
        return await collaboration_service.update_handoff_notes(
            collaboration_id=collaboration_id,
            requester_id=current_user.id,
            notes=payload.handoff_notes,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        logger.error(f"Failed to update handoff notes: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update handoff notes",
        )


