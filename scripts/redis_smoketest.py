#!/usr/bin/env python3
"""
Enhanced Redis Smoke Test

Includes both normal Redis operations and chaos testing with latency injection.

Usage: 
    python scripts/redis_smoketest.py          # Normal smoke test
    python scripts/redis_smoketest.py --chaos  # Include chaos testing
    
Exit codes: 0 = success, 1 = error
"""

import asyncio
import sys
import argparse

# Add backend to Python path
sys.path.append('backend')

from app.redis_client import (
    get_redis, ping_ms, cache_setex, cache_get, with_lock, 
    stream_xadd, stream_readgroup, stream_ack
)


async def run_normal_tests():
    """Run the standard Redis smoke tests"""
    print("🔍 Redis Standard Smoke Test")
    print("=" * 40)
    
    status, rtt = await ping_ms()
    print("PING", status, rtt)
    
    await cache_setex("cache:hello", 30, "world")
    print("GET", await cache_get("cache:hello"))
    
    async with (await with_lock("demo", 5)) as acquired:
        print("LOCK", acquired)
    
    sid = await stream_xadd("queue:scrape", {"demo": True})
    print("XADD", bool(sid))
    
    msgs = await stream_readgroup("queue:scrape", "scrapegrp", "tester-1", count=1, block_ms=1000)
    if msgs:
        _, items = msgs[0]
        ids = [i[0] for i in items]
        await stream_ack("queue:scrape", "scrapegrp", *ids)
        print("XACK", len(ids))
    else:
        print("XACK", 0)
    
    print("✅ Standard tests completed")
    print()


async def run_chaos_tests():
    """Import and run chaos tests"""
    try:
        # Import chaos test functionality
        from redis_chaos_smoketest import run_chaos_tests
        return await run_chaos_tests()
    except ImportError as e:
        print(f"❌ Could not import chaos tests: {e}")
        return False


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Redis Smoke Test Suite')
    parser.add_argument('--chaos', action='store_true', 
                       help='Include chaos testing with latency injection')
    args = parser.parse_args()
    
    success = True
    
    # Always run normal tests
    try:
        await run_normal_tests()
    except Exception as e:
        print(f"❌ Standard tests failed: {e}")
        success = False
    
    # Run chaos tests if requested
    if args.chaos:
        try:
            chaos_success = await run_chaos_tests()
            success = success and chaos_success
        except Exception as e:
            print(f"❌ Chaos tests failed: {e}")
            success = False
    
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Some tests failed!")
    
    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)