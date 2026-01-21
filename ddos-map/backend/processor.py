import asyncio
from state import ingest_queue
from parser import parse_batch
from geoip import enrich
from metrics import stream_metrics
from ui import broadcast
async def processor_loop():
    while True:
        raw = await ingest_queue.get()
        print("[processor] event:", event)  
        for event in parse_batch(raw):
            enrich(event)
            await stream_metrics.update(event)
            await broadcast(event)
