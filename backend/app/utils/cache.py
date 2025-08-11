#!/usr/bin/env python3
"""
Redis cache utility for caching lead data and session storage.

This module provides Redis-based caching functionality for improving
performance of lead processing and API responses.
"""

import os
import json
import logging
from typing import Optional, Any, Dict, List, Union
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Configuration for Redis cache."""
    redis_url: Optional[str] = None
    default_ttl: int = 3600  # 1 hour default TTL
    
    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Create configuration from environment variables."""
        return cls(
            redis_url=os.getenv('REDIS_URL'),
            default_ttl=int(os.getenv('CACHE_TTL', '3600'))
        )


class RedisCache:
    """Redis cache service for lead data and session storage."""
    
    def __init__(self, config: Optional[CacheConfig] = None):
        self.config = config or CacheConfig.from_env()
        self._client = None
        
    def _get_client(self):
        """Lazy load Redis client."""
        if self._client is None and self.config.redis_url:
            try:
                import redis
                self._client = redis.from_url(self.config.redis_url, decode_responses=True)
                # Test connection
                self._client.ping()
                logger.info("Redis connection established")
            except ImportError:
                logger.warning("Redis library not installed. Caching disabled.")
                return None
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {str(e)}. Caching disabled.")
                return None
        return self._client
    
    def is_enabled(self) -> bool:
        """Check if Redis caching is enabled and available."""
        return bool(self.config.redis_url and self._get_client())
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache (will be JSON serialized)
            ttl: Time to live in seconds (uses default if None)
            
        Returns:
            True if value was cached successfully, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            client = self._get_client()
            serialized_value = json.dumps(value, default=str)
            ttl = ttl or self.config.default_ttl
            
            result = client.setex(key, ttl, serialized_value)
            logger.debug(f"Cached value for key: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {str(e)}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        if not self.is_enabled():
            return None
            
        try:
            client = self._get_client()
            value = client.get(key)
            
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            else:
                logger.debug(f"Cache miss for key: {key}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {str(e)}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key was deleted, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            client = self._get_client()
            result = client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return bool(result)
            
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.is_enabled():
            return False
            
        try:
            client = self._get_client()
            return bool(client.exists(key))
            
        except Exception as e:
            logger.error(f"Error checking cache key existence {key}: {str(e)}")
            return False
    
    def cache_lead_scores(self, lead_id: int, scores: Dict[str, Any], ttl: int = 1800) -> bool:
        """
        Cache lead scoring results.
        
        Args:
            lead_id: Lead ID
            scores: Scoring results dictionary
            ttl: Time to live in seconds (default 30 minutes)
            
        Returns:
            True if cached successfully
        """
        key = f"lead_scores:{lead_id}"
        scores['cached_at'] = datetime.now(timezone.utc).isoformat()
        return self.set(key, scores, ttl)
    
    def get_cached_lead_scores(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """
        Get cached lead scoring results.
        
        Args:
            lead_id: Lead ID
            
        Returns:
            Cached scores if found, None otherwise
        """
        key = f"lead_scores:{lead_id}"
        return self.get(key)
    
    def cache_export_result(self, export_id: str, result: Dict[str, Any], ttl: int = 7200) -> bool:
        """
        Cache export operation results.
        
        Args:
            export_id: Unique export operation ID
            result: Export result metadata
            ttl: Time to live in seconds (default 2 hours)
            
        Returns:
            True if cached successfully
        """
        key = f"export_result:{export_id}"
        result['cached_at'] = datetime.now(timezone.utc).isoformat()
        return self.set(key, result, ttl)
    
    def get_cached_export_result(self, export_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached export operation results.
        
        Args:
            export_id: Export operation ID
            
        Returns:
            Cached export result if found, None otherwise
        """
        key = f"export_result:{export_id}"
        return self.get(key)
    
    def increment_rate_limit(self, identifier: str, window_seconds: int = 900) -> int:
        """
        Increment rate limit counter for an identifier.
        
        Args:
            identifier: Rate limit identifier (e.g., IP address, user ID)
            window_seconds: Rate limit window in seconds (default 15 minutes)
            
        Returns:
            Current count for the identifier
        """
        if not self.is_enabled():
            return 0
            
        try:
            client = self._get_client()
            key = f"rate_limit:{identifier}"
            
            # Use pipeline for atomic increment and expire
            pipe = client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            results = pipe.execute()
            
            return results[0] if results else 0
            
        except Exception as e:
            logger.error(f"Error incrementing rate limit for {identifier}: {str(e)}")
            return 0
    
    def get_rate_limit_count(self, identifier: str) -> int:
        """
        Get current rate limit count for an identifier.
        
        Args:
            identifier: Rate limit identifier
            
        Returns:
            Current count for the identifier
        """
        if not self.is_enabled():
            return 0
            
        try:
            client = self._get_client()
            key = f"rate_limit:{identifier}"
            count = client.get(key)
            return int(count) if count else 0
            
        except Exception as e:
            logger.error(f"Error getting rate limit count for {identifier}: {str(e)}")
            return 0
    
    def clear_cache_pattern(self, pattern: str) -> int:
        """
        Clear cache keys matching a pattern.
        
        Args:
            pattern: Redis key pattern (e.g., "lead_scores:*")
            
        Returns:
            Number of keys deleted
        """
        if not self.is_enabled():
            return 0
            
        try:
            client = self._get_client()
            keys = client.keys(pattern)
            if keys:
                deleted = client.delete(*keys)
                logger.info(f"Cleared {deleted} cache keys matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error clearing cache pattern {pattern}: {str(e)}")
            return 0


# Global cache instance
_cache_service = None

def get_cache_service() -> RedisCache:
    """Get the global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = RedisCache()
    return _cache_service