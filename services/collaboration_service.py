"""Service layer for prompt collaboration workflows."""
import secrets
import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from loguru import logger
from supabase import Client, create_client

from config import settings
from schemas.collaboration_schema import (
    CollaborationDetailsResponse,
    CollaborationMemberStatus,
    CollaborationMembershipResponse,
    CollaborationPermission,
    CollaborationPromptResponse,
    CollaborationShareRequest,
    CollaborationShareResponse,
    CommentCreate,
    CommentResponse,
    CommentUpdate,
)
from schemas.prompt_history_schema import InferenceType, PromptHistoryResponse


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        logger.warning(f"Failed to parse timestamp value: {value}")
        return None


class CollaborationService:
    """Service orchestrating collaboration state with Supabase."""

    _PERMISSION_ORDER = {
        CollaborationPermission.VIEW: 0,
        CollaborationPermission.COMMENT: 1,
        CollaborationPermission.EDIT: 2,
    }

    def __init__(self):
        self._validate_environment()
        self.supabase: Client = self._initialize_supabase()
        self.share_base_url: str = self._resolve_share_base_url()
        logger.info("CollaborationService initialized successfully")

    def _validate_environment(self):
        required_vars = ["SUPABASE_URL", "SUPABASE_ANON_KEY"]
        missing = [var for var in required_vars if not getattr(settings, var, None)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    def _initialize_supabase(self) -> Client:
        try:
            service_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
            if service_key:
                client = create_client(settings.SUPABASE_URL, service_key)
                logger.info("Supabase client created for collaboration service with service role key")
            else:
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                logger.warning("Supabase service role key missing; collaboration endpoints may be rate-limited")
            return client
        except Exception as exc:
            logger.error(f"Failed to initialize Supabase client for collaboration service: {exc}")
            raise RuntimeError(f"Supabase collaboration client initialization failed: {exc}") from exc

    def _resolve_share_base_url(self) -> str:
        for candidate in [
            getattr(settings, "COLLABORATION_SHARE_BASE_URL", None),
            getattr(settings, "FRONTEND_BASE_URL", None),
            getattr(settings, "APP_BASE_URL", None),
        ]:
            if candidate:
                return candidate.rstrip("/")
        return "http://localhost:8001"

    def _build_share_url(self, token: str) -> str:
        return f"{self.share_base_url}/chatbot?share={token}"

    @asynccontextmanager
    async def _operation_context(self, operation: str, **context):
        start_time = time.time()
        operation_id = secrets.token_hex(8)
        logger.info(f"Starting {operation}", extra={"operation_id": operation_id, **context})
        try:
            yield operation_id
        except Exception as exc:
            duration = time.time() - start_time
            logger.error(
                f"{operation} failed after {duration:.2f}s",
                extra={"operation_id": operation_id, "duration": duration, "error": str(exc), **context},
            )
            raise
        else:
            duration = time.time() - start_time
            logger.info(
                f"{operation} completed successfully in {duration:.2f}s",
                extra={"operation_id": operation_id, "duration": duration, **context},
            )

    def _generate_share_token(self) -> str:
        return secrets.token_urlsafe(16)

    def _validate_prompt_ownership(self, history_id: str, owner_id: str) -> Dict[str, Any]:
        response = self.supabase.table("prompt_history").select("*").eq("id", history_id).limit(1).execute()
        if not response.data:
            raise ValueError("Prompt history entry not found")
        record = response.data[0]
        if record.get("user_id") != owner_id:
            raise PermissionError("Only the prompt owner can manage collaboration links")
        return record

    def _fetch_collaboration_for_history(self, history_id: str) -> Optional[Dict[str, Any]]:
        response = (
            self.supabase.table("prompt_collaborations")
            .select("*")
            .eq("prompt_history_id", history_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def _fetch_collaboration_by_token(self, share_token: str) -> Optional[Dict[str, Any]]:
        response = (
            self.supabase.table("prompt_collaborations")
            .select("*")
            .eq("share_token", share_token)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def _fetch_collaboration_by_id(self, collaboration_id: str) -> Optional[Dict[str, Any]]:
        response = (
            self.supabase.table("prompt_collaborations")
            .select("*")
            .eq("id", collaboration_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def _fetch_memberships(self, collaboration_id: str) -> List[Dict[str, Any]]:
        response = (
            self.supabase.table("prompt_collaboration_members")
            .select("*")
            .eq("collaboration_id", collaboration_id)
            .execute()
        )
        return response.data or []

    def _effective_permission(
        self,
        base_permission: CollaborationPermission,
        member_permission: Optional[CollaborationPermission],
    ) -> CollaborationPermission:
        perms = [base_permission]
        if member_permission:
            perms.append(member_permission)
        return max(perms, key=lambda perm: self._PERMISSION_ORDER[perm])

    def _serialize_members(self, entries: List[Dict[str, Any]]) -> List[CollaborationMembershipResponse]:
        result = []
        for entry in entries:
            result.append(
                CollaborationMembershipResponse(
                    id=entry["id"],
                    collaboration_id=entry["collaboration_id"],
                    user_id=entry.get("user_id"),
                    email=entry.get("email"),
                    permission=CollaborationPermission(entry.get("permission", "view")),
                    status=CollaborationMemberStatus(entry.get("status", "invited")),
                    created_at=_parse_timestamp(entry.get("created_at")),
                    updated_at=_parse_timestamp(entry.get("updated_at")),
                )
            )
        return result

    def _serialize_prompt(self, record: Dict[str, Any]) -> PromptHistoryResponse:
        return PromptHistoryResponse(
            id=record["id"],
            user_id=record["user_id"],
            original_prompt=record["original_prompt"],
            optimized_prompt=record["optimized_prompt"],
            inference_type=InferenceType(record["inference_type"]),
            model_used=record["model_used"],
            tokens_used=record["tokens_used"],
            processing_time_ms=record["processing_time_ms"],
            handoff_notes=record.get("handoff_notes"),
            created_at=_parse_timestamp(record.get("created_at")),
            updated_at=_parse_timestamp(record.get("updated_at")),
        )

    async def create_or_update_share(
        self,
        owner_id: str,
        history_id: str,
        share_request: CollaborationShareRequest,
    ) -> CollaborationShareResponse:
        async with self._operation_context(
            "create_or_update_share",
            owner_id=owner_id,
            history_id=history_id,
        ):
            self._validate_prompt_ownership(history_id, owner_id)
            existing = self._fetch_collaboration_for_history(history_id)

            expires_at = None
            if share_request.expires_in_hours:
                expires_at = datetime.now(timezone.utc) + timedelta(hours=share_request.expires_in_hours)

            if existing:
                updates: Dict[str, Any] = {
                    "base_permission": share_request.base_permission.value,
                }
                updates["expires_at"] = expires_at.isoformat() if expires_at else None
                response = (
                    self.supabase.table("prompt_collaborations")
                    .update(updates)
                    .eq("id", existing["id"])
                    .execute()
                )
                data = response.data[0]
            else:
                share_token = self._generate_share_token()
                insert_payload: Dict[str, Any] = {
                    "prompt_history_id": history_id,
                    "owner_id": owner_id,
                    "share_token": share_token,
                    "base_permission": share_request.base_permission.value,
                }
                if expires_at:
                    insert_payload["expires_at"] = expires_at.isoformat()
                response = self.supabase.table("prompt_collaborations").insert(insert_payload).execute()
                if not response.data:
                    raise RuntimeError("Failed to create collaboration link")
                data = response.data[0]

            share_url = self._build_share_url(data["share_token"])
            return CollaborationShareResponse(
                collaboration_id=data["id"],
                share_url=share_url,
                base_permission=CollaborationPermission(data["base_permission"]),
                expires_at=_parse_timestamp(data.get("expires_at")),
            )

    def _guard_not_expired(self, collaboration: Dict[str, Any]):
        expires_at = _parse_timestamp(collaboration.get("expires_at"))
        if expires_at:
            current_time = datetime.now(timezone.utc)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at < current_time:
                raise PermissionError("Share link has expired")

    def _fetch_prompt(self, history_id: str) -> Dict[str, Any]:
        response = self.supabase.table("prompt_history").select("*").eq("id", history_id).limit(1).execute()
        if not response.data:
            raise ValueError("Prompt history entry not found")
        return response.data[0]

    async def resolve_share_token(self, share_token: str) -> CollaborationPromptResponse:
        async with self._operation_context("resolve_share_token"):
            collaboration = self._fetch_collaboration_by_token(share_token)
            if not collaboration:
                raise ValueError("Invalid share token")
            self._guard_not_expired(collaboration)

            prompt_record = self._fetch_prompt(collaboration["prompt_history_id"])
            prompt = self._serialize_prompt(prompt_record)

            return CollaborationPromptResponse(
                collaboration_id=collaboration["id"],
                permission=CollaborationPermission(collaboration["base_permission"]),
                prompt=prompt,
            )

    def _find_membership(self, collaboration_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        response = (
            self.supabase.table("prompt_collaboration_members")
            .select("*")
            .eq("collaboration_id", collaboration_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    async def accept_share_token(self, user_id: str, email: str, share_token: str) -> CollaborationPromptResponse:
        async with self._operation_context("accept_share_token", user_id=user_id):
            collaboration = self._fetch_collaboration_by_token(share_token)
            if not collaboration:
                raise ValueError("Invalid share token")
            self._guard_not_expired(collaboration)

            membership = self._find_membership(collaboration["id"], user_id)

            desired_permission = CollaborationPermission(collaboration["base_permission"])
            if membership:
                current_permission = CollaborationPermission(membership["permission"])
                effective_permission = self._effective_permission(desired_permission, current_permission)
                update_payload = {
                    "permission": effective_permission.value,
                    "status": CollaborationMemberStatus.ACTIVE.value,
                }
                (
                    self.supabase.table("prompt_collaboration_members")
                    .update(update_payload)
                    .eq("id", membership["id"])
                    .execute()
                )
            else:
                effective_permission = desired_permission
                insert_payload = {
                    "collaboration_id": collaboration["id"],
                    "user_id": user_id,
                    "email": email,
                    "permission": effective_permission.value,
                    "status": CollaborationMemberStatus.ACTIVE.value,
                }
                self.supabase.table("prompt_collaboration_members").insert(insert_payload).execute()

            prompt_record = self._fetch_prompt(collaboration["prompt_history_id"])
            prompt = self._serialize_prompt(prompt_record)

            return CollaborationPromptResponse(
                collaboration_id=collaboration["id"],
                permission=effective_permission,
                prompt=prompt,
            )

    async def get_collaboration_details(
        self,
        collaboration_id: str,
        requester_id: str,
    ) -> CollaborationDetailsResponse:
        async with self._operation_context("get_collaboration_details", collaboration_id=collaboration_id):
            collaboration = self._fetch_collaboration_by_id(collaboration_id)
            if not collaboration:
                raise ValueError("Collaboration not found")
            self._guard_not_expired(collaboration)

            requester_permission = self._user_permission(collaboration, requester_id)
            members = self._serialize_members(self._fetch_memberships(collaboration_id))
            share_url = None
            if collaboration["owner_id"] == requester_id:
                share_url = self._build_share_url(collaboration["share_token"])
            return CollaborationDetailsResponse(
                id=collaboration["id"],
                prompt_history_id=collaboration["prompt_history_id"],
                owner_id=collaboration["owner_id"],
                base_permission=CollaborationPermission(collaboration["base_permission"]),
                expires_at=_parse_timestamp(collaboration.get("expires_at")),
                created_at=_parse_timestamp(collaboration.get("created_at")),
                updated_at=_parse_timestamp(collaboration.get("updated_at")),
                members=members,
                requester_permission=requester_permission,
                share_url=share_url,
            )

    async def get_collaboration_for_history(
        self,
        history_id: str,
        requester_id: str,
    ) -> Optional[CollaborationDetailsResponse]:
        async with self._operation_context(
            "get_collaboration_for_history",
            history_id=history_id,
            requester_id=requester_id,
        ):
            collaboration = self._fetch_collaboration_for_history(history_id)
            if not collaboration:
                return None
            return await self.get_collaboration_details(collaboration["id"], requester_id)

    def _user_permission(
        self,
        collaboration: Dict[str, Any],
        requester_id: str,
    ) -> CollaborationPermission:
        if collaboration["owner_id"] == requester_id:
            return CollaborationPermission.EDIT
        membership = self._find_membership(collaboration["id"], requester_id)
        if not membership or membership.get("status") != CollaborationMemberStatus.ACTIVE.value:
            raise PermissionError("You do not have access to this collaboration")
        base_permission = CollaborationPermission(collaboration["base_permission"])
        member_permission = CollaborationPermission(membership["permission"])
        return self._effective_permission(base_permission, member_permission)

    async def get_comments(self, collaboration_id: str, requester_id: str) -> List[CommentResponse]:
        async with self._operation_context("get_comments", collaboration_id=collaboration_id):
            collaboration = self._fetch_collaboration_by_id(collaboration_id)
            if not collaboration:
                raise ValueError("Collaboration not found")
            self._guard_not_expired(collaboration)

            self._user_permission(collaboration, requester_id)  # ensures access

            response = (
                self.supabase.table("prompt_comments")
                .select("*")
                .eq("collaboration_id", collaboration_id)
                .order("created_at")
                .execute()
            )

            comments = []
            for entry in response.data or []:
                comments.append(
                    CommentResponse(
                        id=entry["id"],
                        collaboration_id=entry["collaboration_id"],
                        author_id=entry["author_id"],
                        target_type=entry["target_type"],
                        anchor_start=entry.get("anchor_start"),
                        anchor_end=entry.get("anchor_end"),
                        body=entry["body"],
                        resolved=entry.get("resolved", False),
                        created_at=_parse_timestamp(entry.get("created_at")),
                        updated_at=_parse_timestamp(entry.get("updated_at")),
                    )
                )
            return comments

    async def add_comment(
        self,
        collaboration_id: str,
        author_id: str,
        payload: CommentCreate,
    ) -> CommentResponse:
        async with self._operation_context("add_comment", collaboration_id=collaboration_id):
            collaboration = self._fetch_collaboration_by_id(collaboration_id)
            if not collaboration:
                raise ValueError("Collaboration not found")
            self._guard_not_expired(collaboration)

            permission = self._user_permission(collaboration, author_id)
            if self._PERMISSION_ORDER[permission] < self._PERMISSION_ORDER[CollaborationPermission.COMMENT]:
                raise PermissionError("Comment permission required")

            insert_payload = {
                "collaboration_id": collaboration_id,
                "author_id": author_id,
                "target_type": payload.target_type.value,
                "anchor_start": payload.anchor_start,
                "anchor_end": payload.anchor_end,
                "body": payload.body,
            }
            response = self.supabase.table("prompt_comments").insert(insert_payload).execute()
            if not response.data:
                raise RuntimeError("Failed to create comment")
            entry = response.data[0]
            return CommentResponse(
                id=entry["id"],
                collaboration_id=entry["collaboration_id"],
                author_id=entry["author_id"],
                target_type=entry["target_type"],
                anchor_start=entry.get("anchor_start"),
                anchor_end=entry.get("anchor_end"),
                body=entry["body"],
                resolved=entry.get("resolved", False),
                created_at=_parse_timestamp(entry.get("created_at")),
                updated_at=_parse_timestamp(entry.get("updated_at")),
            )

    def _fetch_comment(self, comment_id: str) -> Optional[Dict[str, Any]]:
        response = self.supabase.table("prompt_comments").select("*").eq("id", comment_id).limit(1).execute()
        return response.data[0] if response.data else None

    async def update_comment(
        self,
        comment_id: str,
        requester_id: str,
        payload: CommentUpdate,
    ) -> CommentResponse:
        async with self._operation_context("update_comment", comment_id=comment_id):
            comment = self._fetch_comment(comment_id)
            if not comment:
                raise ValueError("Comment not found")

            collaboration = self._fetch_collaboration_by_id(comment["collaboration_id"])
            if not collaboration:
                raise ValueError("Collaboration not found")
            self._guard_not_expired(collaboration)

            permission = self._user_permission(collaboration, requester_id)
            if requester_id != comment["author_id"] and permission != CollaborationPermission.EDIT:
                raise PermissionError("Only authors or editors can update comments")

            update_payload: Dict[str, Any] = {}
            if payload.body is not None:
                update_payload["body"] = payload.body
            if payload.resolved is not None:
                update_payload["resolved"] = payload.resolved

            if not update_payload:
                return CommentResponse(
                    id=comment["id"],
                    collaboration_id=comment["collaboration_id"],
                    author_id=comment["author_id"],
                    target_type=comment["target_type"],
                    anchor_start=comment.get("anchor_start"),
                    anchor_end=comment.get("anchor_end"),
                    body=comment["body"],
                    resolved=comment.get("resolved", False),
                    created_at=_parse_timestamp(comment.get("created_at")),
                    updated_at=_parse_timestamp(comment.get("updated_at")),
                )

            response = (
                self.supabase.table("prompt_comments")
                .update(update_payload)
                .eq("id", comment_id)
                .execute()
            )
            entry = response.data[0]
            return CommentResponse(
                id=entry["id"],
                collaboration_id=entry["collaboration_id"],
                author_id=entry["author_id"],
                target_type=entry["target_type"],
                anchor_start=entry.get("anchor_start"),
                anchor_end=entry.get("anchor_end"),
                body=entry["body"],
                resolved=entry.get("resolved", False),
                created_at=_parse_timestamp(entry.get("created_at")),
                updated_at=_parse_timestamp(entry.get("updated_at")),
            )

    async def delete_comment(self, comment_id: str, requester_id: str) -> None:
        async with self._operation_context("delete_comment", comment_id=comment_id):
            comment = self._fetch_comment(comment_id)
            if not comment:
                raise ValueError("Comment not found")

            collaboration = self._fetch_collaboration_by_id(comment["collaboration_id"])
            if not collaboration:
                raise ValueError("Collaboration not found")
            self._guard_not_expired(collaboration)

            permission = self._user_permission(collaboration, requester_id)
            if requester_id != comment["author_id"] and permission != CollaborationPermission.EDIT:
                raise PermissionError("Only authors or editors can delete comments")

            self.supabase.table("prompt_comments").delete().eq("id", comment_id).execute()

    async def update_handoff_notes(
        self,
        collaboration_id: str,
        requester_id: str,
        notes: Optional[str],
    ) -> PromptHistoryResponse:
        async with self._operation_context("update_handoff_notes", collaboration_id=collaboration_id):
            collaboration = self._fetch_collaboration_by_id(collaboration_id)
            if not collaboration:
                raise ValueError("Collaboration not found")
            self._guard_not_expired(collaboration)

            permission = self._user_permission(collaboration, requester_id)
            if permission != CollaborationPermission.EDIT:
                raise PermissionError("Edit permission required to update handoff notes")

            history_id = collaboration["prompt_history_id"]
            response = (
                self.supabase.table("prompt_history")
                .update({"handoff_notes": notes})
                .eq("id", history_id)
                .execute()
            )
            if not response.data:
                raise RuntimeError("Failed to update handoff notes")
            prompt_record = response.data[0]
            return self._serialize_prompt(prompt_record)


# Singleton instance
try:
    collaboration_service = CollaborationService()
except Exception as exc:
    logger.critical(f"Failed to initialize CollaborationService: {exc}")
    raise


