# RtNSVP — Real-Time Network Stream Monitor

RtNSVP is a passive, real-time network monitor for networks you own or are authorized to observe. A Zeek sensor streams connection metadata to a central FastAPI receiver, which enriches events, maintains rolling metrics, builds a transparent online usage baseline, and drives a live dashboard.

```
Zeek sensor → Python WebSocket sender → secure tunnel/VPN → FastAPI receiver → metrics, enrichment, dashboard
```

The design is stream-first (one event per WebSocket message), asynchronous, and does not inspect or modify packet payloads.

## What works now

- A sender tails and normalizes Zeek `conn.log`, tracking its position and handling log rotation.
- The receiver separates authenticated ingestion (`/ws/ingest`) from dashboard events (`/ws/events`).
- It accepts normalized JSON events and the original compact binary packet format.
- Live metrics, protocol counts, optional GeoIP locations, traffic-rate DDoS labels, and unseen source/port anomaly labels are available on the dashboard.
- A lightweight online Gaussian model learns normal time, port, byte-volume, and protocol patterns after 100 events. It adds an explainable score to each event and exposes its status at `/model`.
- Use **Run showcase demo** to demonstrate the complete normal-baseline → anomaly → DDoS sequence without a Zeek sensor.
- With `OPENAI_API_KEY` set on the receiver, the investigation panel sends only the selected event's metadata to the server-side OpenAI Responses API and returns a concise next-step explanation.
- The core codebase, UI components, and documentation were iteratively generated and refined using OpenAI's GPT and Codex models, accelerating development and ensuring high‑quality, AI‑assisted code.

## Run locally

In one terminal:

```powershell
cd ddos-map/backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
$env:RTNSVP_API_KEY = "replace-with-a-long-secret" # optional locally; required remotely
uvicorn app:app --host 0.0.0.0 --port 8000
```

In another terminal:

```powershell
cd ddos-map/frontend
npm install
npm run dev
```

When receiver authentication is enabled, create `ddos-map/frontend/.env.local` with `VITE_API_TOKEN` equal to `RTNSVP_API_KEY`. For a remote receiver, also set `VITE_API_URL=wss://receiver.example.com`.

Then stream Zeek connections (replace the log path):

```powershell
cd ddos-map/backend
python sender.py --zeek-log C:\path\to\conn.log --api-key $env:RTNSVP_API_KEY
```

For map locations, obtain MaxMind GeoLite2-City and place `GeoLite2-City.mmdb` in `ddos-map/backend/`. The receiver works without it; it simply omits map coordinates.

## Security and roadmap

Use TLS (`wss://`) through a reverse proxy, Cloudflare Access, or VPN before traffic leaves your local network. Configure `RTNSVP_API_KEY` and `RTNSVP_ALLOWED_ORIGINS`; never commit secrets—use `ddos-map/backend/env.example` as a template.

The in-memory online model is a baseline, not a security verdict. It resets on restart and should be trained separately per network before any persistent-profile feature is added. Planned extensions include saved profiles, labeled-model evaluation, multi-source ingestion, durable buffering/replay, alerting, and stronger production identity controls.
