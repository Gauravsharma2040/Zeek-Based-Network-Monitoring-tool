import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from ui import ui_clients
from tunnel_client import cloudflare_listener
from processor import processor_loop
from metrics import stream_metrics
import auth
import os
app = FastAPI()
ENABLE_AUTH = os.getenv("ENABLE_CF_AUTH", "0") == "1"
@app.websocket("/ws")
async def ws(ws: WebSocket):
    if ENABLE_AUTH:
        token = ws.headers.get("cf-access-jwt-assertion")
        if not token:
            await ws.close(code=4401)
            return
        try:
            auth.verify_jwt(token)
        except Exception:
            await ws.close(code=4403)
            return

    await ws.accept()
    ui_clients.add(ws)
    print("[host] WebSocket connected")

    try:
        while True:
            msg = await ws.receive_text()
            print("[host] received:", msg[:200])

    except WebSocketDisconnect:
        print("[host] WebSocket disconnected")
    finally:
        ui_clients.discard(ws)
@app.get("/metrics")
def metrics():
    return stream_metrics.snapshot()
@app.on_event("startup")
async def startup():
    asyncio.create_task(cloudflare_listener())
    asyncio.create_task(processor_loop())
