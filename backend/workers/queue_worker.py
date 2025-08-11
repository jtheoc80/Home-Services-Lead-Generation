import os
import asyncio
import json
from app.redis_client import get_redis, stream_readgroup, stream_ack

STREAM = "queue:scrape"
GROUP = "scrapegrp" 
CONSUMER = os.getenv("HOSTNAME", "worker-1")


async def ensure_group():
    r = get_redis()
    if r:
        try:
            await r.xgroup_create(STREAM, GROUP, id="$", mkstream=True)
        except Exception:
        except Exception as e:
            logger.exception("Failed to create Redis group '%s' for stream '%s'", GROUP, STREAM)


async def handle(msg):
    payload = json.loads(msg["payload"])
    # TODO: call normalize/ingest with payload
    print(f"Processing message: {payload}")


async def run():
    await ensure_group()
    while True:
        batches = await stream_readgroup(STREAM, GROUP, CONSUMER)
        for stream, entries in batches or []:
            ids = []
            for _id, kv in entries:
                try:
                    await handle({k: v for k, v in kv.items()})
                    ids.append(_id)
                except Exception:
                    logging.exception("Exception occurred while handling message")
            if ids:
                await stream_ack(STREAM, GROUP, *ids)


if __name__ == "__main__":
    asyncio.run(run())