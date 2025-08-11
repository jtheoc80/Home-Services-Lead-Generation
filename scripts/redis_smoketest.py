import asyncio
import json
import os
import sys

# Add backend to Python path
sys.path.append('backend')

from app.redis_client import (
    get_redis, ping_ms, cache_setex, cache_get, with_lock, 
    stream_xadd, stream_readgroup, stream_ack
)


async def main():
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


if __name__ == "__main__":
    asyncio.run(main())