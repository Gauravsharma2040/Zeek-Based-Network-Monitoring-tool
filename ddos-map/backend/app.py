"""HTTP and WebSocket receiver for network events.

Run locally with: ``uvicorn app:app --host 0.0.0.0 --port 8000``.
Senders use /ws/ingest; browser dashboards use /ws/events.
"""
import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager, suppress

from fastapi import Body, FastAPI, Header, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

from processor import processor_loop
from state import ingest_queue
from ui import add_client, remove_client

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

API_KEY = os.getenv("RTNSVP_API_KEY")
demo_task: asyncio.Task | None = None
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("RTNSVP_ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if origin.strip()
]


def is_authorized(ws: WebSocket) -> bool:
    """Allow local development without a key; require a key when configured."""
    return not API_KEY or ws.query_params.get("token") == API_KEY or ws.headers.get("x-api-key") == API_KEY


@asynccontextmanager
async def lifespan(_: FastAPI):
    task = asyncio.create_task(processor_loop(), name="event-processor")
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


app = FastAPI(title="RtNSVP receiver", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "queue_depth": ingest_queue.qsize(), "auth_enabled": bool(API_KEY)}


@app.get("/metrics")
async def metrics(token: str | None = Query(default=None), x_api_key: str | None = Header(default=None)):
    if API_KEY and token != API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    from metrics import stream_metrics
    return await stream_metrics.snapshot()


@app.get("/model")
async def model_status(token: str | None = Query(default=None), x_api_key: str | None = Header(default=None)):
    if API_KEY and token != API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    from usage_model import usage_model
    return usage_model.snapshot()


@app.post("/demo/start")
async def start_demo(token: str | None = Query(default=None), x_api_key: str | None = Header(default=None)):
    global demo_task
    if API_KEY and token != API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    if demo_task and not demo_task.done():
        return {"started": False, "message": "demo is already running"}
    from demo import run_demo
    demo_task = asyncio.create_task(run_demo(), name="showcase-demo")
    return {"started": True, "message": "baseline, anomaly, and DDoS scenario started"}


@app.post("/explain")
async def explain(event: dict = Body(...), token: str | None = Query(default=None), x_api_key: str | None = Header(default=None)):
    if API_KEY and token != API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")
    from ai_explainer import explain_event
    try:
        return {"explanation": await asyncio.to_thread(explain_event, event)}
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.websocket("/ws/ingest")
async def ingest(ws: WebSocket):
    if not is_authorized(ws):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await ws.accept()
    logger.info("Sender connected: %s", ws.client)
    try:
        while True:
            message = await ws.receive()
            payload = message.get("bytes")
            if payload is None and message.get("text") is not None:
                try:
                    decoded = json.loads(message["text"])
                    payload = json.dumps(decoded).encode("utf-8")
                except json.JSONDecodeError:
                    await ws.send_json({"ok": False, "error": "invalid JSON"})
                    continue
            if not payload or len(payload) > 64 * 1024:
                await ws.send_json({"ok": False, "error": "event batch must be 1-65536 bytes"})
                continue
            try:
                ingest_queue.put_nowait(payload)
            except asyncio.QueueFull:
                await ws.send_json({"ok": False, "error": "receiver is busy; retry shortly"})
                continue
            await ws.send_json({"ok": True, "queued": ingest_queue.qsize()})
    except WebSocketDisconnect:
        logger.info("Sender disconnected: %s", ws.client)


@app.websocket("/ws/events")
async def events(ws: WebSocket):
    origin = ws.headers.get("origin")
    if origin and origin not in ALLOWED_ORIGINS:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    if not is_authorized(ws):
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await ws.accept()
    await add_client(ws)
    try:
        # Keep the connection alive and detect a browser close. The dashboard
        # does not need to send commands today.
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await remove_client(ws)
