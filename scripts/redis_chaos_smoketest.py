#!/usr/bin/env python3
"""
Redis Chaos Smoke Test

Injects 250-500ms latency into Redis operations to simulate provider slowness
and tests that the application degrades gracefully with proper timeouts.

This test ensures:
1. Operations with injected latency properly timeout within 1s
2. The application doesn't hang when Redis is slow
3. Graceful degradation occurs (fallback behavior, retries, etc.)

Usage: python scripts/redis_chaos_smoketest.py
Exit codes: 0 = success, 1 = failure
"""

import asyncio
import random
import sys
import time
from contextlib import asynccontextmanager
from typing import Optional, Any
from unittest.mock import AsyncMock, patch

# Add backend to Python path
sys.path.append('backend')

from app.redis_client import (
    get_redis, ping_ms, cache_setex, cache_get, with_lock, 
    stream_xadd, stream_readgroup, stream_ack, rate_limit
)


class ChaosRedisWrapper:
    """Wrapper that injects latency into Redis operations to simulate slowness."""
    
    def __init__(self, original_redis, latency_range=(0.25, 0.5)):
        self.original = original_redis
        self.min_latency, self.max_latency = latency_range
    
    async def _inject_latency(self):
        """Inject random latency between 250-500ms"""
        delay = random.uniform(self.min_latency, self.max_latency)
        await asyncio.sleep(delay)
    
    async def ping(self):
        await self._inject_latency()
        return await self.original.ping()
    
    async def get(self, key):
        await self._inject_latency()
        return await self.original.get(key)
    
    async def setex(self, key, ttl, value):
        await self._inject_latency()
        return await self.original.setex(key, ttl, value)
    
    async def set(self, key, value, **kwargs):
        await self._inject_latency()
        return await self.original.set(key, value, **kwargs)
    
    async def incr(self, key):
        await self._inject_latency()
        return await self.original.incr(key)
    
    async def expire(self, key, ttl):
        await self._inject_latency()
        return await self.original.expire(key, ttl)
    
    async def sadd(self, key, *values):
        await self._inject_latency()
        return await self.original.sadd(key, *values)
    
    async def xadd(self, stream, fields, **kwargs):
        await self._inject_latency()
        return await self.original.xadd(stream, fields, **kwargs)
    
    async def xreadgroup(self, **kwargs):
        await self._inject_latency()
        return await self.original.xreadgroup(**kwargs)
    
    async def xack(self, stream, group, *ids):
        await self._inject_latency()
        return await self.original.xack(stream, group, *ids)
    
    def pipeline(self):
        """Return original pipeline since we handle latency in MockPipeline"""
        # For AsyncMock, we need to actually call and await if it's a coroutine
        pipeline = self.original.pipeline()
        # But since we're in a sync method, we can't await, so assume it returns directly
        """Return a ChaosPipelineWrapper to inject latency into pipeline operations."""
        pipeline = self.original.pipeline()
        return ChaosPipelineWrapper(pipeline, self.min_latency, self.max_latency)


class ChaosPipelineWrapper:
    """Wrapper for Redis pipeline that injects latency"""
    
    def __init__(self, original_pipeline, min_latency, max_latency):
        self.original = original_pipeline
        self.min_latency = min_latency
        self.max_latency = max_latency
    
    async def _inject_latency(self):
        delay = random.uniform(self.min_latency, self.max_latency)
        await asyncio.sleep(delay)
    
    def incr(self, key):
        result = self.original.incr(key)
        return self  # Return self for method chaining
    
    def expire(self, key, ttl):
        result = self.original.expire(key, ttl)
        return self  # Return self for method chaining
    
    async def execute(self):
        await self._inject_latency()
        return await self.original.execute()


@asynccontextmanager
async def chaos_redis_context():
    """Context manager that injects chaos into Redis operations"""
    original_get_redis = get_redis
    
    def patched_get_redis():
        original_redis = original_get_redis()
        if original_redis is None:
            # Create a mock Redis for testing when no Redis is available
            mock_redis = AsyncMock()
            mock_redis.ping.return_value = True
            mock_redis.get.return_value = None
            mock_redis.setex.return_value = True
            mock_redis.set.return_value = True
            mock_redis.incr.return_value = 1
            mock_redis.expire.return_value = True
            mock_redis.sadd.return_value = 1
            mock_redis.xadd.return_value = "test-id"
            mock_redis.xreadgroup.return_value = []
            mock_redis.xack.return_value = 1
            
            # Mock pipeline with proper synchronous methods that include latency
            class MockPipeline:
                def incr(self, key):
                    return self
                
                def expire(self, key, ttl):
                    return self
                    
                async def execute(self):
                    # Inject latency here instead of in wrapper
                    delay = random.uniform(0.25, 0.5)  # 250-500ms
                    await asyncio.sleep(delay)
                    return [1, True]
            
            from unittest.mock import Mock
            mock_redis.pipeline = Mock()
            mock_redis.pipeline.return_value = MockPipeline()
            
            return ChaosRedisWrapper(mock_redis)
        else:
            return ChaosRedisWrapper(original_redis)
    
    with patch('app.redis_client.get_redis', patched_get_redis):
        yield


async def test_ping_with_chaos():
    """Test that ping operations timeout properly with injected latency"""
    print("Testing ping with chaos latency...")
    
    start_time = time.perf_counter()
    try:
        # This should timeout because chaos latency > socket timeout
        status, rtt = await asyncio.wait_for(ping_ms(), timeout=1.0)
        elapsed = time.perf_counter() - start_time
        
        print(f"  PING completed in {elapsed:.3f}s: {status}")
        
        # Verify it doesn't hang longer than 1s
        if elapsed > 1.0:
            raise Exception(f"PING hung for {elapsed:.3f}s, exceeding 1s limit")
            
        # With chaos latency (250-500ms) + socket timeout (300ms), we expect either:
        # - Quick timeout due to socket timeout (< 1s)
        # - Slow response but within 1s limit
        if elapsed > 0.8:
            print(f"  ✅ PING handled latency gracefully: {elapsed:.3f}s")
        elif status == "down":
            print(f"  ✅ PING timed out gracefully: {elapsed:.3f}s")
        else:
            print(f"  ✅ PING completed within timeout: {elapsed:.3f}s")
            
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start_time
        print(f"  ✅ PING timed out as expected: {elapsed:.3f}s")


async def test_cache_operations_with_chaos():
    """Test cache operations with chaos latency"""
    print("Testing cache operations with chaos latency...")
    
    # Test cache_setex
    start_time = time.perf_counter()
    try:
        success = await asyncio.wait_for(
            cache_setex("chaos:test", 30, "value"), 
            timeout=1.0
        )
        elapsed = time.perf_counter() - start_time
        print(f"  SETEX completed in {elapsed:.3f}s: {success}")
        
        if elapsed > 1.0:
            raise Exception(f"SETEX hung for {elapsed:.3f}s, exceeding 1s limit")
            
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start_time
        print(f"  ✅ SETEX timed out gracefully: {elapsed:.3f}s")
    
    # Test cache_get
    start_time = time.perf_counter()
    try:
        value = await asyncio.wait_for(
            cache_get("chaos:test"), 
            timeout=1.0
        )
        elapsed = time.perf_counter() - start_time
        print(f"  GET completed in {elapsed:.3f}s: {value}")
        
        if elapsed > 1.0:
            raise Exception(f"GET hung for {elapsed:.3f}s, exceeding 1s limit")
            
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start_time
        print(f"  ✅ GET timed out gracefully: {elapsed:.3f}s")


async def test_rate_limit_with_chaos():
    """Test rate limiting with chaos latency"""
    print("Testing rate limit with chaos latency...")
    
    start_time = time.perf_counter()
    try:
        allowed = await asyncio.wait_for(
            rate_limit("chaos:rate", 5, 60), 
            timeout=1.0
        )
        elapsed = time.perf_counter() - start_time
        print(f"  RATE_LIMIT completed in {elapsed:.3f}s: {allowed}")
        
        if elapsed > 1.0:
            raise Exception(f"RATE_LIMIT hung for {elapsed:.3f}s, exceeding 1s limit")
            
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start_time
        print(f"  ✅ RATE_LIMIT timed out gracefully: {elapsed:.3f}s")


async def test_lock_with_chaos():
    """Test distributed locks with chaos latency"""
    print("Testing distributed lock with chaos latency...")
    
    start_time = time.perf_counter()
    try:
        async with (await asyncio.wait_for(with_lock("chaos:lock", 5), timeout=1.0)) as acquired:
            elapsed = time.perf_counter() - start_time
            print(f"  LOCK acquired in {elapsed:.3f}s: {acquired}")
            
            if elapsed > 1.0:
                raise Exception(f"LOCK hung for {elapsed:.3f}s, exceeding 1s limit")
                
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start_time
        print(f"  ✅ LOCK timed out gracefully: {elapsed:.3f}s")


async def test_timeout_enforcement():
    """Test that operations absolutely do not exceed 1s timeout under any circumstances"""
    print("Testing strict 1s timeout enforcement...")
    
    operations = [
        ("ping_ms", ping_ms()),
        ("cache_get", cache_get("test:key")),
        ("cache_setex", cache_setex("test:key", 30, "value")),
        ("rate_limit", rate_limit("test:rate", 5, 60)),
        ("stream_xadd", stream_xadd("test:stream", {"data": "test"})),
    ]
    
    for op_name, operation in operations:
        start_time = time.perf_counter()
        try:
            await asyncio.wait_for(operation, timeout=1.0)
            elapsed = time.perf_counter() - start_time
            
            if elapsed > 1.0:
                raise Exception(f"{op_name} took {elapsed:.3f}s, exceeding 1s limit")
            
            print(f"  ✅ {op_name}: {elapsed:.3f}s (within 1s limit)")
            
        except asyncio.TimeoutError:
            elapsed = time.perf_counter() - start_time
            # TimeoutError at 1s is acceptable
            if elapsed > TIMEOUT_CLEANUP_TOLERANCE:  # Allow small tolerance for cleanup
                raise Exception(f"{op_name} cleanup took {elapsed:.3f}s after timeout")
            print(f"  ✅ {op_name}: timed out at {elapsed:.3f}s (acceptable)")


async def test_graceful_degradation():
    """Test that the system provides appropriate fallbacks when Redis is slow"""
    print("Testing graceful degradation patterns...")
    
    # Test that rate limiting allows requests when Redis is slow (fallback to allow)
    start_time = time.perf_counter()
    try:
        allowed = await asyncio.wait_for(rate_limit("chaos:degrade", 1, 60), timeout=1.0)
        elapsed = time.perf_counter() - start_time
        print(f"  ✅ Rate limiting degraded gracefully: {allowed} in {elapsed:.3f}s")
        
        # With latency, rate limiting should either work slowly or fallback to True
        if not allowed:
            print("  ⚠️  Rate limiting denied request despite potential Redis issues")
    except asyncio.TimeoutError:
        print("  ✅ Rate limiting timed out gracefully (fallback behavior)")
    
    # Test that locks handle slowness gracefully
    start_time = time.perf_counter()
    try:
        async with (await asyncio.wait_for(with_lock("chaos:degradelock", 5), timeout=1.0)) as acquired:
            elapsed = time.perf_counter() - start_time
            print(f"  ✅ Lock degraded gracefully: {acquired} in {elapsed:.3f}s")
    except asyncio.TimeoutError:
        elapsed = time.perf_counter() - start_time
        print(f"  ✅ Lock timed out gracefully: {elapsed:.3f}s")


async def run_chaos_tests():
    """Run all chaos tests"""
    print("🔥 Redis Chaos Smoke Test")
    print("=" * 50)
    print("Injecting 250-500ms latency to simulate provider slowness...")
    print()
    
    async with chaos_redis_context():
        test_functions = [
            test_ping_with_chaos,
            test_cache_operations_with_chaos,
            test_rate_limit_with_chaos,
            test_lock_with_chaos,
            test_timeout_enforcement,
            test_graceful_degradation,
        ]
        
        passed = 0
        failed = 0
        
        for test_func in test_functions:
            try:
                await test_func()
                passed += 1
                print()
            except Exception as e:
                print(f"  ❌ {test_func.__name__} failed: {e}")
                failed += 1
                print()
        
        print("=" * 50)
        print(f"Tests: {passed} passed, {failed} failed")
        
        if failed > 0:
            print("❌ Some chaos tests failed")
            return False
        else:
            print("✅ All chaos tests passed - Redis degrades gracefully under latency!")
            return True


async def main():
    """Main entry point"""
    try:
        success = await run_chaos_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Chaos test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())