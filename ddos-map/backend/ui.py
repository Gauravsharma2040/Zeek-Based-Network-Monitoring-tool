import json
ui_clients = set()
async def broadcast(event):
    msg = json.dumps(event)
    for ws in list(ui_clients):
        try:
            await ws.send_text(msg)
        except:
            ui_clients.discard(ws)
