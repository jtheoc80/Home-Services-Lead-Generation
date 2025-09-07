import os
import asyncio
import json
import time
import uuid
from typing import Any, Optional
from redis.asyncio import Redis

REDIS_URL = os.getenv("REDIS_URL")
_redis: Optional[Redis] = None


def get_redis() -> Optional[Redis]:
    global _redis
    if not REDIS_URL:
        return None
    if _redis is None:
        _redis = Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_timeout=0.3,
            socket_connect_timeout=0.3,
            health_check_interval=30,
            ssl=REDIS_URL.startswith("rediss://"),
        )
    return _redis


async def ping_ms() -> tuple[str, Optional[float]]:
    r = get_redis()
    if not r:
        return ("disabled", None)
    t0 = time.perf_counter()
    try:
        await asyncio.wait_for(r.ping(), timeout=0.3)
        return ("connected", (time.perf_counter() - t0) * 1000.0)
    except Exception:
        return ("down", None)


async def cache_get(key: str) -> Any:
    r = get_redis()
    return None if not r else await r.get(key)


async def cache_setex(key: str, ttl_s: int, value: str) -> None:
    r = get_redis()
    None if not r else await r.setex(key, ttl_s, value)


async def cache_setex(key: str, ttl_s: int, value: str) -> bool:
    r = get_redis()
    if not r:
        return False
    try:
        await r.setex(key, ttl_s, value)
        return True
    except Exception:
        return False


async def rate_limit(key: str, limit: int, window_s: int) -> bool:
    r = get_redis()
    if not r:
        return True
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, window_s)
    cnt, _ = await pipe.execute()
    return int(cnt) <= int(limit)


async def with_lock(name: str, ttl_s: int = 300):
    r = get_redis()
    if not r:

        class _NL:
            async def __aenter__(self):
                return True

            async def __aexit__(self, *a):
                return False

        return _NL()

    token = str(uuid.uuid4())
    key = f"lock:{name}"

    async def acquire():
        return await r.set(key, token, ex=ttl_s, nx=True)

    async def release():
        lua = "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end"
        try:
            await r.eval(lua, 1, key, token)
        except Exception:
            pass

    class _L:
        async def __aenter__(self):
            return await acquire()

        async def __aexit__(self, exc_type, exc, tb):
            await release()

    return _L()


async def dedupe_sadd(set_name: str, member: str, ttl_days: int = 90) -> bool:
    r = get_redis()
    if not r:
        return True
    added = await r.sadd(set_name, member)
    if added:
        await r.expire(set_name, ttl_days * 24 * 3600)
    return added == 1


async def stream_xadd(stream: str, payload: dict, maxlen: int = 10000) -> str:
    r = get_redis()
    return (
        ""
        if not r
        else await r.xadd(
            stream, {"payload": json.dumps(payload)}, maxlen=maxlen, approximate=True
        )
    )


async def stream_readgroup(
    stream: str, group: str, consumer: str, count: int = 10, block_ms: int = 5000
):
    r = get_redis()
    if not r:
        return []
    try:
        return await r.xreadgroup(
            groupname=group,
            consumername=consumer,
            streams={stream: ">"},
            count=count,
            block=block_ms,
        )
    except Exception:
        return []


async def stream_ack(stream: str, group: str, *ids: str) -> int:
    r = get_redis()
    return 0 if not r else await r.xack(stream, group, *ids)
