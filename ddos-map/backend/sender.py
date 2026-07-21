"""Tail Zeek conn.log and stream normalized events to an RtNSVP receiver.

Example: python sender.py --zeek-log /opt/zeek/logs/current/conn.log --receiver ws://receiver:8000/ws/ingest
"""
import argparse
import asyncio
import json
import os
from pathlib import Path

import websockets


def parse_zeek_line(fields: list[str], line: str) -> dict | None:
    values = line.rstrip("\n").split("\t")
    record = dict(zip(fields, values))
    if record.get("id.orig_h") in (None, "-") or record.get("id.resp_h") in (None, "-"):
        return None
    return {
        "ts": record.get("ts", 0), "src": record["id.orig_h"], "dst": record["id.resp_h"],
        "port": record.get("id.resp_p", 0), "proto": record.get("proto", "unknown"),
        "service": record.get("service") if record.get("service") != "-" else None,
        "bytes": record.get("orig_bytes", 0),
    }


def read_new_zeek_records(path: Path, position: int, fields: list[str]) -> tuple[list[dict], int, list[str]]:
    """Read only records appended since ``position``; reset cleanly on rotation."""
    if path.stat().st_size < position:
        position, fields = 0, []
    events: list[dict] = []
    with path.open("r", encoding="utf-8", errors="replace") as log:
        log.seek(position)
        for line in log:
            if line.startswith("#fields"):
                fields = line.rstrip("\n").split("\t")[1:]
            elif fields and not line.startswith("#"):
                event = parse_zeek_line(fields, line)
                if event:
                    events.append(event)
        position = log.tell()
    return events, position, fields


async def stream(path: Path, receiver: str, api_key: str | None):
    headers = {"x-api-key": api_key} if api_key else None
    position, fields = 0, []
    while True:
        try:
            async with websockets.connect(receiver, additional_headers=headers, ping_interval=20) as ws:
                while True:
                    events, position, fields = read_new_zeek_records(path, position, fields)
                    for event in events:
                        await ws.send(json.dumps(event))
                        await ws.recv()
                    await asyncio.sleep(1)
        except (OSError, websockets.WebSocketException) as error:
            print(f"Receiver unavailable ({error}); retrying in 3 seconds")
            await asyncio.sleep(3)
        await asyncio.sleep(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Stream a Zeek conn.log to RtNSVP")
    parser.add_argument("--zeek-log", type=Path, required=True)
    parser.add_argument("--receiver", default="ws://127.0.0.1:8000/ws/ingest")
    parser.add_argument("--api-key", default=os.getenv("RTNSVP_API_KEY"))
    args = parser.parse_args()
    asyncio.run(stream(args.zeek_log, args.receiver, args.api_key))
