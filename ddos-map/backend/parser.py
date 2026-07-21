"""Parse either legacy binary packets or JSON events from Zeek senders."""
import ipaddress
import json
import socket
import struct
from collections.abc import Iterator

STRUCT_FMT = "!QIIHB"
STRUCT_SIZE = struct.calcsize(STRUCT_FMT)


def _normalise(event: dict) -> dict:
    src = str(event.get("src") or event.get("id.orig_h") or "")
    dst = str(event.get("dst") or event.get("id.resp_h") or "")
    if not src or not dst:
        raise ValueError("event requires src/dst (or Zeek id.orig_h/id.resp_h)")
    ipaddress.ip_address(src)
    ipaddress.ip_address(dst)
    return {
        "ts": float(event.get("ts", 0)),
        "src": src,
        "dst": dst,
        "port": int(event.get("port", event.get("id.resp_p", 0)) or 0),
        "proto": str(event.get("proto", "unknown")).lower(),
        "service": event.get("service"),
        "bytes": int(event.get("bytes", event.get("orig_bytes", 0)) or 0),
    }


def parse_batch(data: bytes) -> Iterator[dict]:
    """Yield valid events. A malformed JSON item never stops the stream."""
    try:
        decoded = json.loads(data.decode("utf-8"))
        records = decoded if isinstance(decoded, list) else [decoded]
        for record in records:
            if isinstance(record, dict):
                try:
                    yield _normalise(record)
                except (TypeError, ValueError):
                    continue
        return
    except (UnicodeDecodeError, json.JSONDecodeError):
        pass

    for index in range(0, len(data) - STRUCT_SIZE + 1, STRUCT_SIZE):
        ts, src, dst, port, proto = struct.unpack(STRUCT_FMT, data[index:index + STRUCT_SIZE])
        yield {
            "ts": ts,
            "src": socket.inet_ntoa(struct.pack("!I", src)),
            "dst": socket.inet_ntoa(struct.pack("!I", dst)),
            "port": port,
            "proto": {6: "tcp", 17: "udp"}.get(proto, str(proto)),
            "service": None,
            "bytes": 0,
        }
