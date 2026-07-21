import asyncio
import json
from fastapi import WebSocket

ui_clients: set[WebSocket] = set()
_lock = asyncio.Lock()


async def add_client(ws: WebSocket):
    async with _lock:
        ui_clients.add(ws)


async def remove_client(ws: WebSocket):
    async with _lock:
        ui_clients.discard(ws)


async def broadcast(event: dict):
    message = json.dumps(event, separators=(",", ":"))
    clients = list(ui_clients)
    results = await asyncio.gather(*(client.send_text(message) for client in clients), return_exceptions=True)
    for client, result in zip(clients, results):
        if isinstance(result, Exception):
            await remove_client(client)
