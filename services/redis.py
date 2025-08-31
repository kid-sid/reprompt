import redis
import json
import hashlib
import time
from typing import Optional, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        """Initialize Redis connection with configuration from settings."""
        try:
            self.redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None

    def _generate_cache_key(self, prompt: str, inference_type: str) -> str:
        """Generate a unique cache key for a prompt and inference type combination."""
        # Create a hash of the prompt and inference type
        content = f"{prompt}:{inference_type}"
        return f"prompt_optimization:{hashlib.md5(content.encode()).hexdigest()}"

    def cache_optimized_prompt(self, prompt: str, optimized_prompt: str, inference_type: str, 
                              model_used: str, tokens_used: int, ttl: int = 3600) -> bool:
        """
        Cache an optimized prompt result.
        
        Args:
            prompt: Original prompt
            optimized_prompt: Optimized prompt result
            inference_type: Type of inference used (lazy/pro)
            model_used: Model used for optimization
            tokens_used: Number of tokens used
            ttl: Time to live in seconds (default: 1 hour)
        
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._generate_cache_key(prompt, inference_type)
            cache_data = {
                "original_prompt": prompt,
                "optimized_prompt": optimized_prompt,
                "inference_type": inference_type,
                "model_used": model_used,
                "tokens_used": tokens_used,
                "timestamp": int(time.time())
            }
            
            self.redis_client.setex(
                cache_key, 
                ttl, 
                json.dumps(cache_data)
            )
            logger.info(f"Cached optimized prompt with key: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching optimized prompt: {e}")
            return False

    def get_cached_optimization(self, prompt: str, inference_type: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached optimization result.
        
        Args:
            prompt: Original prompt
            inference_type: Type of inference used (lazy/pro)
        
        Returns:
            Dict containing cached data or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._generate_cache_key(prompt, inference_type)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                logger.info(f"Cache hit for key: {cache_key}")
                return data
            else:
                logger.info(f"Cache miss for key: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving cached optimization: {e}")
            return None

    def cache_user_session(self, session_id: str, data: Dict[str, Any], ttl: int = 86400) -> bool:
        """
        Cache user session data.
        
        Args:
            session_id: Unique session identifier
            data: Session data to cache
            ttl: Time to live in seconds (default: 24 hours)
        
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = f"user_session:{session_id}"
            self.redis_client.setex(
                cache_key,
                ttl,
                json.dumps(data)
            )
            return True
            
        except Exception as e:
            logger.error(f"Error caching user session: {e}")
            return False

    def get_user_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached user session data.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Dict containing session data or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"user_session:{session_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving user session: {e}")
            return None

    def cache_prompt_history(self, user_id: str, history_entry: Dict[str, Any], max_entries: int = 50) -> bool:
        """
        Cache user's prompt optimization history.
        
        Args:
            user_id: User identifier
            history_entry: History entry to add
            max_entries: Maximum number of entries to keep
        
        Returns:
            bool: True if cached successfully, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = f"prompt_history:{user_id}"
            
            # Get existing history
            existing_history = self.get_prompt_history(user_id) or []
            
            # Add new entry at the beginning
            existing_history.insert(0, history_entry)
            
            # Keep only the latest entries
            if len(existing_history) > max_entries:
                existing_history = existing_history[:max_entries]
            
            # Cache the updated history
            self.redis_client.setex(
                cache_key,
                86400 * 7,  # 7 days TTL
                json.dumps(existing_history)
            )
            return True
            
        except Exception as e:
            logger.error(f"Error caching prompt history: {e}")
            return False

    def get_prompt_history(self, user_id: str) -> Optional[list]:
        """
        Retrieve user's prompt optimization history.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of history entries or None if not found
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = f"prompt_history:{user_id}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving prompt history: {e}")
            return None

    def clear_cache(self, pattern: str = "prompt_optimization:*") -> bool:
        """
        Clear cache entries matching a pattern.
        
        Args:
            pattern: Redis pattern to match (default: all prompt optimizations)
        
        Returns:
            bool: True if cleared successfully, False otherwise
        """
        if not self.redis_client:
            return False
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
                logger.info(f"Cleared {len(keys)} cache entries matching pattern: {pattern}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict containing cache statistics
        """
        if not self.redis_client:
            return {"error": "Redis not connected"}
        
        try:
            info = self.redis_client.info()
            return {
                "connected": True,
                "total_keys": info.get("db0", {}).get("keys", 0),
                "memory_usage": info.get("used_memory_human", "N/A"),
                "uptime": info.get("uptime_in_seconds", 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"error": str(e)}

# Create a global Redis service instance
redis_service = RedisService()
