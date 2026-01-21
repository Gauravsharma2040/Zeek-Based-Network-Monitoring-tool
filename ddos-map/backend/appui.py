from state import ingest_queue

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
    print("[host] sender connected")

    try:
        while True:
            msg = await ws.receive_text()
            await ingest_queue.put(msg.encode())
    except WebSocketDisconnect:
        print("[host] sender disconnected")
