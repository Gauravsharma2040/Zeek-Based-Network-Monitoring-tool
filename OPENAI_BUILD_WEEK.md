# RtNSVP — OpenAI Build Week Submission

## One-line pitch

RtNSVP turns raw Zeek network telemetry into an explainable, real-time view of normal behavior, unusual usage, and possible traffic bursts—without requiring a full security operations center.

## The problem

Small teams and home-lab operators can collect network logs, but raw connection data is difficult to interpret in the moment. Existing security tools can be expensive, noisy, or designed for specialists. I wanted to make the first layer of network visibility understandable: what is normal, what changed, and what should I investigate next?

## The solution

RtNSVP is a passive monitoring tool for networks the user owns or is authorized to observe. It streams Zeek `conn.log` metadata from a sensor to a FastAPI receiver, maintains live metrics, and displays activity in a browser dashboard.

The application learns a lightweight baseline from time of day, destination port, byte volume, and protocol. It combines that score with transparent rules for unseen source/port combinations and traffic-rate bursts. Instead of presenting an opaque security verdict, RtNSVP shows why an event was flagged and suggests the next investigation step.

## What the demo shows

1. The dashboard begins with no traffic.
2. **Run showcase demo** creates normal HTTPS traffic so the online baseline can learn.
3. The simulated traffic introduces an unusual high-volume UDP connection; the dashboard labels it as a usage anomaly.
4. A short high-rate stream follows; the receiver labels it as a possible DDoS burst.
5. Selecting **Explain with AI** sends the selected event's metadata to the server-side OpenAI integration and returns a concise, plain-English investigation summary.

This deterministic demo mode makes the project easy to evaluate without access to a live Zeek sensor.

## Architecture

```text
Zeek sensor
  -> Python sender (tails conn.log)
  -> WebSocket ingestion endpoint
  -> bounded async queue
  -> parser + GeoIP enrichment + online usage model
  -> live metrics / event broadcast / dashboard
  -> optional OpenAI explanation endpoint
```

### Technical highlights

- FastAPI WebSocket receiver with separate sender and dashboard routes.
- Bounded ingestion queue and asynchronous processing.
- Zeek sender that tracks file position and handles log rotation.
- Dependency-light online Gaussian baseline using incremental running statistics.
- Explainable anomaly fields: model score, confidence, burst/novelty reason, and normal-versus-suspicious label.
- Optional GeoIP map, reconnecting frontend, and a deterministic showcase scenario.
- API-key gate, origin allowlist, and server-side secret handling.

## How Codex and GPT-5.6 helped me build it

I used Codex with GPT-5.6 as a development collaborator throughout the project. It helped me move from a partially connected prototype to a testable product story while keeping the core security purpose intact.

### 1. Turning an idea into an end-to-end system

Codex reviewed the original code paths and identified the missing links between the Zeek sender, WebSocket receiver, processor, metrics, and frontend. It helped implement a clear separation between event ingestion and UI broadcasting, then verified the flow with compilation, smoke tests, and production frontend builds.

### 2. Designing a lightweight ML approach

Rather than adding a large opaque model, GPT-5.6 helped shape an incremental baseline that is practical for a live demo and explainable to users. The result learns a normal-use profile from five event features and returns a transparent anomaly score. The model does not train on obvious traffic bursts, helping avoid normalizing the behavior it should flag.

### 3. Making the product demonstrable

Codex helped turn the dashboard from a raw map into a narrative: learn normal behavior, identify a deviation, detect a burst, and explain the next step. It added the synthetic demo scenario, live incident panel, model-readiness status, and resilient reconnect behavior so the project can be shown reliably in a short video.

### 4. Adding a responsible AI layer

The optional OpenAI explanation feature is designed as an investigation aid, not an automatic enforcement tool. GPT-5.6 helped create a constrained prompt that asks for a concise explanation and one safe next step, explicitly avoids certainty, and does not recommend automatically blocking traffic. The receiver sends only the selected event's metadata—not packet payloads—to the API.

### 5. Improving delivery quality

Codex also assisted with dependency checks, build validation, documentation, configuration templates, and security cleanup. This let me spend more time on the product experience and less time on repetitive integration work.

## OpenAI usage

When configured with `OPENAI_API_KEY`, RtNSVP uses the server-side OpenAI SDK and the Responses API to turn selected network-event metadata into a short incident explanation. The integration uses `store=False` and keeps the API key on the receiver; it is never sent to the browser.

The project defaults the optional explanation feature to `gpt-5.6-terra`, while allowing operators to set `OPENAI_MODEL` for their own deployment. Gemini and Groq are retained as operational fallbacks when explicitly configured; OpenAI is tried first. See the [OpenAI models documentation](https://developers.openai.com/api/docs/models) and [Responses API guide](https://developers.openai.com/api/docs/guides/responses) for current model and API details.

## Responsible-use commitments

- RtNSVP is for passive monitoring of networks the user owns or is authorized to monitor.
- It works with connection metadata and does not inspect or alter packet payloads.
- Alerts are signals for investigation, not claims of compromise.
- The initial usage model is in-memory and resets on restart; it is not presented as a trained intrusion-detection system.
- OpenAI-generated explanations are advisory and always require human review.

## What is next

- Persist separate baseline profiles per monitored network.
- Evaluate detection quality against labeled Zeek/CICIDS-style data.
- Add alert routing, historical investigation views, and role-based identity controls.
- Add model evaluation reports so threshold changes are evidence-driven.

## Run it

Follow the local setup in [README.md](README.md). For the full demo, start the backend and frontend, open the dashboard, then select **Run showcase demo**.
