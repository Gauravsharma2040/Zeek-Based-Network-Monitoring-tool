"""Deterministic synthetic traffic for product demonstrations only."""
import asyncio
import json
import time

from state import ingest_queue


async def _send(event: dict) -> None:
    await ingest_queue.put(json.dumps(event).encode("utf-8"))


async def run_demo() -> None:
    """Create a normal baseline, then novel usage and a visible rate burst."""
    now = time.time()
    normal = {"ts": now, "src": "192.168.1.24", "dst": "8.8.8.8", "port": 443, "proto": "tcp", "service": "ssl", "bytes": 1400}
    for _ in range(100):
        await _send(normal)
        await asyncio.sleep(0.01)
    await _send({"ts": now, "src": "192.168.1.24", "dst": "198.51.100.42", "port": 31337, "proto": "udp", "service": None, "bytes": 30_000_000})
    await asyncio.sleep(1)
    for _ in range(260):
        await _send({"ts": now, "src": "192.168.1.88", "dst": "203.0.113.80", "port": 80, "proto": "tcp", "service": "http", "bytes": 120})
        await asyncio.sleep(0.01)
