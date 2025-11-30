"""Pydantic schemas for prompt collaboration features."""

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from schemas.prompt_history_schema import PromptHistoryResponse


class CollaborationPermission(str, Enum):
    VIEW = "view"
    COMMENT = "comment"
    EDIT = "edit"


class CollaborationMemberStatus(str, Enum):
    INVITED = "invited"
    ACTIVE = "active"


class CollaborationShareRequest(BaseModel):
    """Request payload for creating/updating a share link."""

    base_permission: CollaborationPermission = Field(
        default=CollaborationPermission.VIEW,
        description="Default permission granted via the share link.",
    )
    expires_in_hours: Optional[int] = Field(
        default=None,
        ge=1,
        le=720,
        description="Optional expiry offset (in hours) from now.",
    )


class CollaborationShareResponse(BaseModel):
    """Response payload containing share link metadata."""

    collaboration_id: str = Field(..., description="Created collaboration identifier.")
    share_url: str = Field(..., description="Direct URL consumers can open to join.")
    base_permission: CollaborationPermission
    expires_at: Optional[datetime] = None


class CollaborationMembershipResponse(BaseModel):
    """Response describing a collaboration membership entry."""

    id: str
    collaboration_id: str
    user_id: Optional[str] = None
    email: Optional[str] = None
    permission: CollaborationPermission
    status: CollaborationMemberStatus
    created_at: datetime
    updated_at: datetime


class CollaborationDetailsResponse(BaseModel):
    """Complete collaboration detail payload."""

    id: str
    prompt_history_id: str
    owner_id: str
    base_permission: CollaborationPermission
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    members: List[CollaborationMembershipResponse] = Field(default_factory=list)
    requester_permission: CollaborationPermission = Field(
        ..., description="Effective permission for the requesting user."
    )
    share_url: Optional[str] = Field(
        default=None,
        description="Direct share URL (only populated for owners).",
    )


class CommentTarget(str, Enum):
    ORIGINAL = "original"
    OPTIMIZED = "optimized"


class CommentCreate(BaseModel):
    """Request payload to create a new inline comment."""

    target_type: CommentTarget = Field(..., description="Which text the comment anchors to.")
    body: str = Field(..., min_length=1, max_length=5000)
    anchor_start: Optional[int] = Field(None, ge=0)
    anchor_end: Optional[int] = Field(None, ge=0)

    @validator("anchor_end")
    def validate_anchor_range(cls, v, values):
        start = values.get("anchor_start")
        if v is not None and start is not None and v < start:
            raise ValueError("anchor_end must be greater than or equal to anchor_start")
        return v


class CommentUpdate(BaseModel):
    """Request payload to update an existing inline comment."""

    body: Optional[str] = Field(None, min_length=1, max_length=5000)
    resolved: Optional[bool] = None


class CommentResponse(BaseModel):
    """Serialized inline comment."""

    id: str
    collaboration_id: str
    author_id: str
    target_type: CommentTarget
    anchor_start: Optional[int]
    anchor_end: Optional[int]
    body: str
    resolved: bool
    created_at: datetime
    updated_at: datetime


class CollaborationPromptResponse(BaseModel):
    """Resolved prompt payload when accessing via share link."""

    collaboration_id: str
    permission: CollaborationPermission
    prompt: PromptHistoryResponse


class HandoffNotesUpdate(BaseModel):
    """Payload for updating handoff notes."""

    handoff_notes: Optional[str] = Field(
        None,
        description="New handoff notes content. Provide null to clear.",
        max_length=20000,
    )


