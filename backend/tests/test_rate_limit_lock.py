#!/usr/bin/env python3
"""
Tests for Redis rate limiting and distributed locks functionality.
"""

import os
import pytest
from unittest.mock import Mock, patch, AsyncMock

# Set required environment variables for testing
os.environ['SUPABASE_JWT_SECRET'] = 'test_secret'
os.environ['SUPABASE_URL'] = 'https://test.supabase.co'
os.environ['SUPABASE_SERVICE_ROLE'] = 'test_service_role'

# Import after setting environment variables
from app.redis_client import rate_limit, with_lock, ping_ms, cache_get, cache_setex, dedupe_sadd


class TestRedisRateLimit:
    """Test cases for Redis rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_within_limit(self):
        """Test that rate limiting allows requests within the limit."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            # Mock Redis pipeline
            mock_pipeline = Mock()
            mock_pipeline.execute = AsyncMock(return_value=[1, True])  # First request
            
            mock_redis = Mock()  # Use Mock instead of AsyncMock for the main object
            mock_redis.pipeline.return_value = mock_pipeline
            mock_get_redis.return_value = mock_redis
            
            # Should allow first request
            result = await rate_limit("test_key", limit=5, window_s=60)
            assert result is True
            
            # Verify pipeline operations
            mock_pipeline.incr.assert_called_once_with("test_key")
            mock_pipeline.expire.assert_called_once_with("test_key", 60)
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocks_over_limit(self):
        """Test that rate limiting blocks requests over the limit."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            # Mock Redis pipeline
            mock_pipeline = Mock()
            mock_pipeline.execute = AsyncMock(return_value=[6, True])  # Over limit
            
            mock_redis = Mock()  # Use Mock instead of AsyncMock for the main object
            mock_redis.pipeline.return_value = mock_pipeline
            mock_get_redis.return_value = mock_redis
            
            # Should block request over limit
            result = await rate_limit("test_key", limit=5, window_s=60)
            assert result is False
    
    @pytest.mark.asyncio
    async def test_rate_limit_allows_when_redis_unavailable(self):
        """Test that rate limiting allows all requests when Redis is unavailable."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_get_redis.return_value = None
            
            # Should allow all requests when Redis is unavailable
            result = await rate_limit("test_key", limit=5, window_s=60)
            assert result is True


class TestRedisLocks:
    """Test cases for Redis distributed locks functionality."""
    
    @pytest.mark.asyncio
    async def test_lock_acquire_and_release(self):
        """Test successful lock acquisition and release."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.set.return_value = True  # Lock acquired
            mock_redis.eval.return_value = 1    # Lock released
            mock_get_redis.return_value = mock_redis
            
            async with await with_lock("test_lock", ttl_s=10) as acquired:
                assert acquired is True
                
            # Verify lock operations
            mock_redis.set.assert_called_once()
            mock_redis.eval.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_lock_acquisition_failure(self):
        """Test lock acquisition failure when already held."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.set.return_value = False  # Lock not acquired
            mock_get_redis.return_value = mock_redis
            
            async with await with_lock("test_lock", ttl_s=10) as acquired:
                assert acquired is False
    
    @pytest.mark.asyncio
    async def test_lock_always_succeeds_when_redis_unavailable(self):
        """Test that locks always succeed when Redis is unavailable."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_get_redis.return_value = None
            
            async with await with_lock("test_lock", ttl_s=10) as acquired:
                assert acquired is True


class TestRedisCache:
    """Test cases for Redis caching functionality."""
    
    @pytest.mark.asyncio
    async def test_cache_get_returns_none_when_redis_unavailable(self):
        """Test cache get returns None when Redis is unavailable."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_get_redis.return_value = None
            
            result = await cache_get("test_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_setex_does_nothing_when_redis_unavailable(self):
        """Test cache setex does nothing when Redis is unavailable."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_get_redis.return_value = None
            
            # Should not raise an exception
            await cache_setex("test_key", 30, "test_value")


class TestRedisPing:
    """Test cases for Redis connectivity checks."""
    
    @pytest.mark.asyncio
    async def test_ping_returns_disabled_when_redis_unavailable(self):
        """Test ping returns disabled status when Redis is unavailable."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_get_redis.return_value = None
            
            status, rtt = await ping_ms()
            assert status == "disabled"
            assert rtt is None
    
    @pytest.mark.asyncio
    async def test_ping_returns_connected_when_redis_available(self):
        """Test ping returns connected status when Redis is available."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_get_redis.return_value = mock_redis
            
            status, rtt = await ping_ms()
            assert status == "connected"
            assert isinstance(rtt, float)
            assert rtt > 0
    
    @pytest.mark.asyncio
    async def test_ping_returns_down_on_exception(self):
        """Test ping returns down status when Redis raises exception."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_get_redis.return_value = mock_redis
            
            status, rtt = await ping_ms()
            assert status == "down"
            assert rtt is None


class TestRedisDeduplication:
    """Test cases for Redis deduplication functionality."""
    
    @pytest.mark.asyncio
    async def test_dedupe_sadd_returns_true_when_redis_unavailable(self):
        """Test deduplication allows all when Redis is unavailable."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_get_redis.return_value = None
            
            result = await dedupe_sadd("test_set", "test_member")
            assert result is True
    
    @pytest.mark.asyncio
    async def test_dedupe_sadd_returns_true_for_new_member(self):
        """Test deduplication returns True for new set member."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.sadd.return_value = 1  # New member added
            mock_get_redis.return_value = mock_redis
            
            result = await dedupe_sadd("test_set", "test_member", ttl_days=90)
            assert result is True
            
            # Verify operations
            mock_redis.sadd.assert_called_once_with("test_set", "test_member")
            mock_redis.expire.assert_called_once_with("test_set", 90 * 24 * 3600)
    
    @pytest.mark.asyncio
    async def test_dedupe_sadd_returns_false_for_existing_member(self):
        """Test deduplication returns False for existing set member."""
        with patch('app.redis_client.get_redis') as mock_get_redis:
            mock_redis = AsyncMock()
            mock_redis.sadd.return_value = 0  # Member already exists
            mock_get_redis.return_value = mock_redis
            
            result = await dedupe_sadd("test_set", "test_member")
            assert result is False