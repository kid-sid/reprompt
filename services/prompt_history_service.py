"""
Service for managing user prompt history with Supabase integration
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
import secrets
from supabase import create_client, Client
from loguru import logger
from config import settings

from schemas.prompt_history_schema import (
    PromptHistoryCreate, PromptHistoryResponse, PromptHistoryListResponse,
    PromptHistoryUpdate, PromptHistorySearch
)

class PromptHistoryService:
    """Service for managing user prompt history"""
    
    def __init__(self):
        """Initialize Supabase client for prompt history operations"""
        self._validate_environment()
        self.supabase: Client = self._initialize_supabase()
        logger.info("PromptHistoryService initialized successfully")
    
    def _validate_environment(self):
        """Validate required environment variables"""
        required_vars = ['SUPABASE_URL', 'SUPABASE_ANON_KEY']
        missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    def _initialize_supabase(self) -> Client:
        """Initialize and validate Supabase client"""
        try:
            # Use service role key for prompt history operations to bypass RLS
            service_key = getattr(settings, 'SUPABASE_SERVICE_ROLE_KEY', None)
            if service_key:
                client = create_client(settings.SUPABASE_URL, service_key)
                logger.info("Supabase client created for prompt history service with service role key")
            else:
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)
                logger.info("Supabase client created for prompt history service with anon key")
            return client
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise RuntimeError(f"Supabase client initialization failed: {e}")
    
    @asynccontextmanager
    async def _operation_context(self, operation: str, **context):
        """Context manager for operation logging and timing"""
        start_time = time.time()
        operation_id = secrets.token_hex(8)
        
        logger.info(f"Starting {operation}", extra={
            "operation_id": operation_id,
            "operation": operation,
            **context
        })
        
        try:
            yield operation_id
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{operation} failed after {duration:.2f}s", extra={
                "operation_id": operation_id,
                "operation": operation,
                "duration": duration,
                "error": str(e),
                **context
            })
            raise
        else:
            duration = time.time() - start_time
            logger.info(f"{operation} completed successfully in {duration:.2f}s", extra={
                "operation_id": operation_id,
                "operation": operation,
                "duration": duration,
                **context
            })
    
    async def create_prompt_history(
        self, 
        user_id: str, 
        prompt_data: PromptHistoryCreate
    ) -> PromptHistoryResponse:
        """Create a new prompt history entry"""
        async with self._operation_context("create_prompt_history", user_id=user_id) as op_id:
            try:
                # Prepare data for insertion
                history_data = {
                    "user_id": user_id,
                    "original_prompt": prompt_data.original_prompt,
                    "optimized_prompt": prompt_data.optimized_prompt,
                    "inference_type": prompt_data.inference_type.value,
                    "model_used": prompt_data.model_used,
                    "tokens_used": prompt_data.tokens_used,
                    "processing_time_ms": prompt_data.processing_time_ms
                }
                
                # Insert into database
                response = self.supabase.table("prompt_history").insert(history_data).execute()
                
                if not response.data:
                    raise Exception("Failed to create prompt history entry")
                
                history_entry = response.data[0]
                logger.info(f"Created prompt history entry: {history_entry['id']}")
                
                return PromptHistoryResponse(
                    id=history_entry["id"],
                    user_id=history_entry["user_id"],
                    original_prompt=history_entry["original_prompt"],
                    optimized_prompt=history_entry["optimized_prompt"],
                    inference_type=history_entry["inference_type"],
                    model_used=history_entry["model_used"],
                    tokens_used=history_entry["tokens_used"],
                    processing_time_ms=history_entry["processing_time_ms"],
                    created_at=datetime.fromisoformat(history_entry["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(history_entry["updated_at"].replace('Z', '+00:00'))
                )
                
            except Exception as e:
                logger.error(f"Failed to create prompt history for user {user_id}: {e}")
                raise
    
    async def get_user_prompt_history(
        self, 
        user_id: str, 
        search_params: PromptHistorySearch
    ) -> PromptHistoryListResponse:
        """Get paginated prompt history for a user"""
        async with self._operation_context("get_user_prompt_history", user_id=user_id) as op_id:
            try:
                # Build query
                query = self.supabase.table("prompt_history").select("*", count="exact")
                query = query.eq("user_id", user_id)
                
                # Apply filters
                if search_params.inference_type:
                    query = query.eq("inference_type", search_params.inference_type.value)
                
                if search_params.model_used:
                    query = query.eq("model_used", search_params.model_used)
                
                if search_params.date_from:
                    query = query.gte("created_at", search_params.date_from.isoformat())
                
                if search_params.date_to:
                    query = query.lte("created_at", search_params.date_to.isoformat())
                
                if search_params.query:
                    # Search in both original and optimized prompts
                    query = query.or_(f"original_prompt.ilike.%{search_params.query}%,optimized_prompt.ilike.%{search_params.query}%")
                
                # Apply pagination
                offset = (search_params.page - 1) * search_params.page_size
                query = query.order("created_at", desc=True)
                query = query.range(offset, offset + search_params.page_size - 1)
                
                # Execute query
                response = query.execute()
                
                # Process results
                items = []
                for item in response.data:
                    items.append(PromptHistoryResponse(
                        id=item["id"],
                        user_id=item["user_id"],
                        original_prompt=item["original_prompt"],
                        optimized_prompt=item["optimized_prompt"],
                        inference_type=item["inference_type"],
                        model_used=item["model_used"],
                        tokens_used=item["tokens_used"],
                        processing_time_ms=item["processing_time_ms"],
                        created_at=datetime.fromisoformat(item["created_at"].replace('Z', '+00:00')),
                        updated_at=datetime.fromisoformat(item["updated_at"].replace('Z', '+00:00'))
                    ))
                
                total_count = response.count or 0
                has_next = offset + search_params.page_size < total_count
                has_previous = search_params.page > 1
                
                logger.info(f"Retrieved {len(items)} prompt history entries for user {user_id}")
                
                return PromptHistoryListResponse(
                    items=items,
                    total_count=total_count,
                    page=search_params.page,
                    page_size=search_params.page_size,
                    has_next=has_next,
                    has_previous=has_previous
                )
                
            except Exception as e:
                logger.error(f"Failed to get prompt history for user {user_id}: {e}")
                raise
    
    async def get_prompt_history_by_id(
        self, 
        user_id: str, 
        history_id: str
    ) -> Optional[PromptHistoryResponse]:
        """Get a specific prompt history entry by ID"""
        async with self._operation_context("get_prompt_history_by_id", user_id=user_id, history_id=history_id) as op_id:
            try:
                response = self.supabase.table("prompt_history").select("*").eq("id", history_id).eq("user_id", user_id).execute()
                
                if not response.data:
                    return None
                
                item = response.data[0]
                return PromptHistoryResponse(
                    id=item["id"],
                    user_id=item["user_id"],
                    original_prompt=item["original_prompt"],
                    optimized_prompt=item["optimized_prompt"],
                    inference_type=item["inference_type"],
                    model_used=item["model_used"],
                    tokens_used=item["tokens_used"],
                    processing_time_ms=item["processing_time_ms"],
                    created_at=datetime.fromisoformat(item["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(item["updated_at"].replace('Z', '+00:00'))
                )
                
            except Exception as e:
                logger.error(f"Failed to get prompt history {history_id} for user {user_id}: {e}")
                raise
    
    async def update_prompt_history(
        self, 
        user_id: str, 
        history_id: str, 
        update_data: PromptHistoryUpdate
    ) -> Optional[PromptHistoryResponse]:
        """Update a prompt history entry"""
        async with self._operation_context("update_prompt_history", user_id=user_id, history_id=history_id) as op_id:
            try:
                # Prepare update data (only include non-None values)
                update_dict = {}
                for field, value in update_data.dict(exclude_unset=True).items():
                    if value is not None:
                        update_dict[field] = value
                
                if not update_dict:
                    # No updates to make
                    return await self.get_prompt_history_by_id(user_id, history_id)
                
                # Update in database
                response = self.supabase.table("prompt_history").update(update_dict).eq("id", history_id).eq("user_id", user_id).execute()
                
                if not response.data:
                    return None
                
                item = response.data[0]
                logger.info(f"Updated prompt history entry: {history_id}")
                
                return PromptHistoryResponse(
                    id=item["id"],
                    user_id=item["user_id"],
                    original_prompt=item["original_prompt"],
                    optimized_prompt=item["optimized_prompt"],
                    inference_type=item["inference_type"],
                    model_used=item["model_used"],
                    tokens_used=item["tokens_used"],
                    processing_time_ms=item["processing_time_ms"],
                    created_at=datetime.fromisoformat(item["created_at"].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(item["updated_at"].replace('Z', '+00:00'))
                )
                
            except Exception as e:
                logger.error(f"Failed to update prompt history {history_id} for user {user_id}: {e}")
                raise
    
    async def delete_prompt_history(
        self, 
        user_id: str, 
        history_id: str
    ) -> bool:
        """Delete a prompt history entry"""
        async with self._operation_context("delete_prompt_history", user_id=user_id, history_id=history_id) as op_id:
            try:
                response = self.supabase.table("prompt_history").delete().eq("id", history_id).eq("user_id", user_id).execute()
                
                success = len(response.data) > 0
                if success:
                    logger.info(f"Deleted prompt history entry: {history_id}")
                else:
                    logger.warning(f"Prompt history entry not found or already deleted: {history_id}")
                
                return success
                
            except Exception as e:
                logger.error(f"Failed to delete prompt history {history_id} for user {user_id}: {e}")
                raise
    
    
    async def delete_user_history(self, user_id: str) -> int:
        """Delete all prompt history for a user (for account deletion)"""
        async with self._operation_context("delete_user_history", user_id=user_id) as op_id:
            try:
                # First get count
                count_response = self.supabase.table("prompt_history").select("id", count="exact").eq("user_id", user_id).execute()
                total_count = count_response.count or 0
                
                # Delete all entries
                response = self.supabase.table("prompt_history").delete().eq("user_id", user_id).execute()
                
                logger.info(f"Deleted {total_count} prompt history entries for user {user_id}")
                return total_count
                
            except Exception as e:
                logger.error(f"Failed to delete all prompt history for user {user_id}: {e}")
                raise
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for prompt history service"""
        try:
            # Test database connectivity
            self.supabase.table("prompt_history").select("count").limit(1).execute()
            
            return {
                "status": "healthy",
                "service": "prompt_history",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "accessible"
            }
        except Exception as e:
            logger.error(f"Prompt history service health check failed: {e}")
            return {
                "status": "unhealthy",
                "service": "prompt_history",
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

# Create singleton instance
try:
    prompt_history_service = PromptHistoryService()
except Exception as e:
    logger.critical(f"Failed to initialize PromptHistoryService: {e}")
    raise
