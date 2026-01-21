🌐 Real-Time Network Stream Monitor

A personal, real-time network monitoring system that streams live network events from a self-owned network to a central backend for processing and visualization.

Built around event streaming, not log files.

True real-time pipeline — events flow as they occur, not in batches

Stream-first design — one event = one message (WebSocket)

Passive & safe — observes traffic, never modifies it

Auth-ready transport — Cloudflare tunnel + Access support

Async by default — non-blocking ingestion and processing

Visualization-driven — designed for live maps and dashboards

🏗️ Architecture
Zeek (sensor)
   → WebSocket sender
      → Cloudflare Tunnel
         → FastAPI backend
            → metrics / enrichment / UI


No inbound ports.
No polling.
No file uploads.

🔍 What It Does Today

Streams live Zeek connection events

Processes events asynchronously

Maintains rolling traffic metrics

Enriches events with metadata (e.g. geo)

Prepares data for real-time UI consumption

🔐 Security Model

Dev mode for rapid iteration (temporary tunnels)

Production-ready Cloudflare Access JWT verification

Backend never stores sender secrets

Each client authenticates independently

🧭 Where This Is Going

Designed to evolve naturally into a network security monitoring system by adding:

traffic spike detection

anomaly detection models

multi-source event ingestion

Kafka-backed buffering & replay

real-time geographic visualizations

No redesign required.

⚖️ Scope

Passive monitoring only

Intended for networks you own or are authorized to observe

Focuses on metadata, not payload inspection
