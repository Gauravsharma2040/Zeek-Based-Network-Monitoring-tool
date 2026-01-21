import asyncio
import websockets
from state import ingest_queue
CLOUDFLARE_WS = "wss://covers-known-virginia-brandon.trycloudflare.com/ws"
async def cloudflare_listener():
    while True:
        try:
            async with websockets.connect(
                CLOUDFLARE_WS,
                ping_interval=20,
            ) as ws:
                async for msg in ws:
                    if not isinstance(msg, (bytes, bytearray)):
                        continue
                    if len(msg) > 64 * 1024:
                        continue
                    await ingest_queue.put(msg)

        except Exception as e:
            print("Tunnel disconnected, retrying:", e)
            await asyncio.sleep(3)
