import asyncio
# Raw events from sender → host
ingest_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=10_000)
# Connected frontend clients